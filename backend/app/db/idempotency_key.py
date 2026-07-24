from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin
from backend.app.db.enums import IdempotencyStatus, enum_kwargs


class IdempotencyKey(UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin, Base):
    __tablename__ = "idempotency_keys"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "endpoint", "idempotency_key", name="uq_idempotency_identity"),
        Index("ix_idempotency_keys_tenant_status", "tenant_id", "status"),
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    endpoint: Mapped[str] = mapped_column(String(255))
    idempotency_key: Mapped[str] = mapped_column(String(255))
    request_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[IdempotencyStatus] = mapped_column(
        Enum(IdempotencyStatus, **enum_kwargs),
        default=IdempotencyStatus.IN_PROGRESS,
    )
    response_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
