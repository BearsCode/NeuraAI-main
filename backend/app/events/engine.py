from __future__ import annotations

import json
import logging
from typing import Any, Callable, Coroutine

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db_session
from backend.app.events.schemas import EventEnvelope

logger = logging.getLogger(__name__)

EventHandler = Callable[[EventEnvelope, AsyncSession], Coroutine[Any, Any, None]]


class EventEngine:
    def __init__(self, redis: Redis | None = None):
        self.redis = redis
        self._handlers: dict[str, list[EventHandler]] = {}

    def on(self, event_type: str):
        def decorator(handler: EventHandler) -> EventHandler:
            self._handlers.setdefault(event_type, []).append(handler)
            return handler
        return decorator

    async def publish(self, envelope: EventEnvelope) -> None:
        if self.redis:
            data = envelope.model_dump(mode="json")
            await self.redis.xadd(
                envelope.topic,
                data,
                maxlen=10000,
                approximate=True,
            )
            await self.redis.publish(envelope.topic, json.dumps(data, default=str))

        await self._process_locally(envelope)

    DLQ_TOPIC = "dead_letter:v1"

    async def _publish_to_dlq(self, envelope: EventEnvelope, error: str) -> None:
        if not self.redis:
            return
        try:
            dlq_data = envelope.model_dump(mode="json")
            dlq_data["_error"] = error
            dlq_data["_failed_at"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
            await self.redis.xadd(self.DLQ_TOPIC, dlq_data, maxlen=10000, approximate=True)
        except Exception:
            logger.exception("Failed to publish to dead letter queue")

    async def _process_locally(self, envelope: EventEnvelope) -> None:
        handlers = self._handlers.get(envelope.event_type, [])
        if not handlers:
            return

        async for session in get_db_session():
            try:
                for handler in handlers:
                    await handler(envelope, session)
            except Exception as e:
                logger.error("Event handler failed for %s: %s", envelope.event_type, e)
                await self._publish_to_dlq(envelope, str(e))
            finally:
                await session.close()

    async def listen_loop(self, topics: list[str]) -> None:
        if not self.redis:
            return

        max_retries = 5
        retry_delay = 1.0
        pubsub = None

        async def _heartbeat() -> None:
            while True:
                try:
                    await self.redis.set("event_engine:heartbeat", "1", ex=60)
                    await __import__("asyncio").sleep(30)
                except Exception:
                    logger.warning("Heartbeat failed")

        import asyncio as _asyncio
        _asyncio.ensure_future(_heartbeat())

        for attempt in range(max_retries):
            try:
                if pubsub is not None:
                    await pubsub.unsubscribe(*topics)
                    await pubsub.close()
                pubsub = self.redis.pubsub()
                await pubsub.subscribe(*topics)

                try:
                    async for message in pubsub.listen():
                        if message["type"] != "message":
                            continue
                        try:
                            data = json.loads(message["data"])
                            envelope = EventEnvelope(**data)
                            await self._process_locally(envelope)
                        except Exception as e:
                            logger.error("Failed to process pubsub message: %s", e)
                finally:
                    await pubsub.unsubscribe(*topics)
                    await pubsub.close()
                    pubsub = None
            except Exception as e:
                logger.error("Redis pubsub connection lost (attempt %d/%d): %s", attempt + 1, max_retries, e)
                if attempt < max_retries - 1:
                    await _asyncio.sleep(retry_delay * (2 ** attempt))
                else:
                    logger.critical("Redis pubsub connection exhausted all retries")


event_engine = EventEngine()
