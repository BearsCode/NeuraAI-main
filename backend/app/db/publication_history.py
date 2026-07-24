from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.app.db.publication import Publication
    from backend.app.db.publication_target import PublicationTarget


class PublicationHistory(UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin, Base):
    """History log for publication queue execution."""

    __tablename__ = "publication_histories"
    __table_args__ = (
        Index("ix_publication_histories_publication_created", "publication_id", "created_at"),
        Index("ix_publication_histories_tenant_status", "tenant_id", "status"),
    )

    publication_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("publications.id", ondelete="CASCADE"),
        index=True,
    )
    publication_target_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("publication_targets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    platform: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), index=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)

    publication: Mapped["Publication"] = relationship()
    target: Mapped["PublicationTarget | None"] = relationship()
