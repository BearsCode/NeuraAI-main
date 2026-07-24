from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.configs import settings
from backend.app.db.enums import OutboxStatus
from backend.app.db.outbox_event import OutboxEvent
from backend.app.events.bus import RedisEventBus
from backend.app.events.schemas import EventEnvelope


class OutboxService:
    async def enqueue(
        self,
        session: AsyncSession,
        envelope: EventEnvelope,
    ) -> OutboxEvent:
        event = OutboxEvent(
            tenant_id=envelope.tenant_id,
            aggregate_id=envelope.aggregate_id,
            event_type=envelope.event_type,
            topic=envelope.topic,
            payload=envelope.model_dump(mode="json"),
        )
        session.add(event)
        await session.flush()
        return event


class OutboxProcessor:
    def __init__(self, session_factory, event_bus: RedisEventBus) -> None:
        self.session_factory = session_factory
        self.event_bus = event_bus

    async def process_pending(self, batch_size: int = 100) -> int:
        processed = 0
        async with self.session_factory() as session:
            events = (
                await session.scalars(
                    select(OutboxEvent)
                    .where(OutboxEvent.status == OutboxStatus.PENDING)
                    .order_by(OutboxEvent.created_at)
                    .limit(batch_size)
                )
            ).all()

            for event in events:
                try:
                    envelope = EventEnvelope(
                        event_id=event.id,
                        event_type=event.event_type,
                        topic=event.topic,
                        tenant_id=event.tenant_id,
                        aggregate_id=event.aggregate_id,
                        payload=event.payload,
                        occurred_at=event.created_at,
                    )
                    await self.event_bus.publish(envelope)
                    event.status = OutboxStatus.PUBLISHED
                    event.last_error = None
                    processed += 1
                except Exception as exc:  # noqa: BLE001
                    event.retry_count += 1
                    event.last_error = str(exc)
                    if event.retry_count >= settings.workers.max_retries:
                        event.status = OutboxStatus.FAILED

            await session.commit()
        return processed
