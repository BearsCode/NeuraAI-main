from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.app.db.project import Project


class ProjectStrategy(UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin, Base):
    __tablename__ = "project_strategies"
    __table_args__ = (
        UniqueConstraint("project_id", name="uq_project_strategies_project_id"),
    )

    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        unique=True,
    )
    business_analysis: Mapped[list[str]] = mapped_column(JSON, default=list)
    market_analysis: Mapped[list[str]] = mapped_column(JSON, default=list)
    competitor_analysis: Mapped[list[str]] = mapped_column(JSON, default=list)
    positioning: Mapped[str] = mapped_column(Text, default="")
    content_pillars: Mapped[list[str]] = mapped_column(JSON, default=list)
    channels: Mapped[list[str]] = mapped_column(JSON, default=list)
    publishing_frequency: Mapped[str] = mapped_column(String(120), default="3 posts per week")
    recommendations: Mapped[list[str]] = mapped_column(JSON, default=list)
    optimization_mode: Mapped[str] = mapped_column(String(64), default="manual_confirmation")

    project: Mapped["Project"] = relationship(back_populates="strategy")
