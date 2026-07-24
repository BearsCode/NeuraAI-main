from __future__ import annotations

from sqlalchemy import Enum, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TenantTimePartitionMixin, UUIDPrimaryKeyMixin
from backend.app.db.enums import OutboxStatus, enum_kwargs


class OutboxEvent(UUIDPrimaryKeyMixin, TenantTimePartitionMixin, Base):
    __tablename__ = "outbox_events"
    __table_args__ = (
        Index("ix_outbox_events_pending", "status", "created_at"),
        {"postgresql_partition_by": "RANGE (created_at)"},
    )

    aggregate_id: Mapped[str] = mapped_column(String(36), index=True)
    event_type: Mapped[str] = mapped_column(String(128), index=True)
    topic: Mapped[str] = mapped_column(String(128), index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[OutboxStatus] = mapped_column(
        Enum(OutboxStatus, **enum_kwargs),
        default=OutboxStatus.PENDING,
        index=True,
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
