from __future__ import annotations

from sqlalchemy import Enum, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin
from backend.app.db.enums import OptimizationStatus, enum_kwargs


class OptimizationRecommendation(UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin, Base):
    __tablename__ = "optimization_recommendations"
    __table_args__ = (
        Index("ix_optimization_recommendations_tenant_status", "tenant_id", "status"),
    )

    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    status: Mapped[OptimizationStatus] = mapped_column(
        Enum(OptimizationStatus, **enum_kwargs),
        default=OptimizationStatus.PENDING,
        index=True,
    )
    summary: Mapped[str] = mapped_column(Text)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    suggested_publish_time: Mapped[str | None] = mapped_column(String(16), nullable=True)
    suggested_frequency: Mapped[str | None] = mapped_column(String(120), nullable=True)
