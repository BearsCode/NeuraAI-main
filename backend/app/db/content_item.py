from __future__ import annotations

from datetime import UTC, date, datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin
from backend.app.db.enums import ContentStatus, ContentType, IntegrationPlatform, enum_kwargs

if TYPE_CHECKING:
    from backend.app.db.content_plan import ContentPlan
    from backend.app.db.content_version import ContentVersion
    from backend.app.db.project import Project
    from backend.app.db.publication import Publication


class ContentItem(UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin, Base):
    __tablename__ = "content_items"
    __table_args__ = (
        Index("ix_content_items_publish_at", "tenant_id", "publish_date", "publish_time"),
    )

    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    plan_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("content_plans.id", ondelete="SET NULL"),
        nullable=True,
    )
    platform: Mapped[IntegrationPlatform] = mapped_column(Enum(IntegrationPlatform, **enum_kwargs), index=True)
    content_type: Mapped[ContentType] = mapped_column(Enum(ContentType, **enum_kwargs))
    publish_date: Mapped[date] = mapped_column(Date, default=lambda: datetime.now(UTC).date())
    publish_time: Mapped[time] = mapped_column(default=lambda: time(hour=10, minute=0))
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus, **enum_kwargs),
        default=ContentStatus.DRAFT,
        index=True,
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    text: Mapped[str] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    current_version_number: Mapped[int] = mapped_column(Integer, default=1)

    project: Mapped["Project"] = relationship(back_populates="content_items")
    plan: Mapped["ContentPlan | None"] = relationship(back_populates="items")
    publication: Mapped["Publication | None"] = relationship(
        back_populates="content_item",
        cascade="all, delete-orphan",
        uselist=False,
    )
    versions: Mapped[list["ContentVersion"]] = relationship(
        back_populates="content_item",
        cascade="all, delete-orphan",
    )
