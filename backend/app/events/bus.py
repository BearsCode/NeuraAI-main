from __future__ import annotations

import json
import logging

from redis.asyncio import Redis

from backend.app.core.configs import settings
from backend.app.events.schemas import EventEnvelope

logger = logging.getLogger(__name__)


class RedisEventBus:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def publish(self, envelope: EventEnvelope) -> None:
        try:
            data = envelope.model_dump(mode="json")
            await self.redis.xadd(
                envelope.topic,
                data,
                maxlen=settings.redis.stream_max_len,
                approximate=True,
            )
            await self.redis.publish(envelope.topic, json.dumps(data, default=str))
        except Exception:
            logger.exception("Failed to publish event %s to topic %s", envelope.event_type, envelope.topic)


event_bus: RedisEventBus | None = None
