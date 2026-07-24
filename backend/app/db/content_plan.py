from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Index, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin
from backend.app.db.enums import ContentSourceMode, enum_kwargs

if TYPE_CHECKING:
    from backend.app.db.content_item import ContentItem
    from backend.app.db.project import Project


class ContentPlan(UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin, Base):
    __tablename__ = "content_plans"
    __table_args__ = (
        Index("ix_content_plans_project_created", "tenant_id", "project_id", "created_at"),
    )

    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    period_days: Mapped[int] = mapped_column(Integer, default=30)
    source_mode: Mapped[ContentSourceMode] = mapped_column(
        Enum(ContentSourceMode, **enum_kwargs),
        default=ContentSourceMode.MIXED,
    )
    plan_data: Mapped[dict | None] = mapped_column(JSON, default=dict, nullable=True)
    status: Mapped[str] = mapped_column(String(64), default="generated")
    version: Mapped[int] = mapped_column(Integer, default=1)

    project: Mapped["Project"] = relationship(back_populates="content_plans")
    items: Mapped[list["ContentItem"]] = relationship(back_populates="plan", cascade="all, delete-orphan")
