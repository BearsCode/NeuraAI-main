from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TenantTimePartitionMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.app.db.project import Project


class AnalyticsSnapshot(UUIDPrimaryKeyMixin, TenantTimePartitionMixin, Base):
    __tablename__ = "analytics_snapshots"
    __table_args__ = (
        Index("ix_analytics_snapshots_project_collected", "tenant_id", "project_id", "collected_at"),
        Index(
            "ix_analytics_snapshots_project_platform_collected",
            "tenant_id",
            "project_id",
            "platform",
            "collected_at",
        ),
        {"postgresql_partition_by": "RANGE (created_at)"},
    )

    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    platform: Mapped[str] = mapped_column(String(64), default="all")
    period: Mapped[str] = mapped_column(String(32), default="last_30_days")
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    reach: Mapped[int] = mapped_column(Integer, default=0)
    followers: Mapped[int] = mapped_column(Integer, default=0)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    saves: Mapped[int] = mapped_column(Integer, default=0)
    ctr: Mapped[float] = mapped_column(Float, default=0)
    er: Mapped[float] = mapped_column(Float, default=0)
    audience_growth: Mapped[float] = mapped_column(Float, default=0)
    raw_metrics: Mapped[dict] = mapped_column(JSON, default=dict)

    project: Mapped["Project"] = relationship(back_populates="analytics_snapshots")
