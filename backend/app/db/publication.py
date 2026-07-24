from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin
from backend.app.db.enums import ContentType, IntegrationPlatform, PublicationStatus, enum_kwargs

if TYPE_CHECKING:
    from backend.app.db.content_item import ContentItem
    from backend.app.db.project import Project
    from backend.app.db.publication_target import PublicationTarget


class Publication(UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin, Base):
    __tablename__ = "publications"
    __table_args__ = (
        Index("ix_publications_status_scheduled", "tenant_id", "status", "scheduled_at"),
    )

    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    content_item_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("content_items.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    )
    platform: Mapped[IntegrationPlatform] = mapped_column(
        Enum(IntegrationPlatform, **enum_kwargs),
        default=IntegrationPlatform.TELEGRAM,
    )
    status: Mapped[PublicationStatus] = mapped_column(
        Enum(PublicationStatus, **enum_kwargs),
        default=PublicationStatus.PENDING_APPROVAL,
        index=True,
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC) + timedelta(days=1),
    )
    all_or_nothing: Mapped[bool] = mapped_column(Boolean, default=True)
    approval_required: Mapped[bool] = mapped_column(Boolean, default=True)
    content_type: Mapped[ContentType | None] = mapped_column(
        Enum(ContentType, **enum_kwargs),
        nullable=True,
        default=ContentType.POST,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    external_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    external_post_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    saga_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    project: Mapped["Project"] = relationship(back_populates="publications")
    content_item: Mapped["ContentItem | None"] = relationship(back_populates="publication")
    targets: Mapped[list["PublicationTarget"]] = relationship(
        back_populates="publication",
        cascade="all, delete-orphan",
    )
