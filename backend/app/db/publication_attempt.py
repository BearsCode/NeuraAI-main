from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin
from backend.app.db.enums import PublicationTargetStatus, enum_kwargs

if TYPE_CHECKING:
    from backend.app.db.publication_target import PublicationTarget


class PublicationAttempt(UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin, Base):
    __tablename__ = "publication_attempts"
    __table_args__ = (
        UniqueConstraint("publication_target_id", "attempt_number", name="uq_publication_attempt_number"),
        Index("ix_publication_attempts_retry", "tenant_id", "next_retry_at"),
    )

    publication_target_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("publication_targets.id", ondelete="CASCADE"),
        index=True,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[PublicationTargetStatus] = mapped_column(
        Enum(PublicationTargetStatus, **enum_kwargs),
        default=PublicationTargetStatus.QUEUED,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    target: Mapped["PublicationTarget"] = relationship(back_populates="attempts")
