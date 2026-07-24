from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin
from backend.app.db.enums import AIJobStatus, enum_kwargs


class AIJob(UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin, Base):
    __tablename__ = "ai_jobs"
    __table_args__ = (
        Index("ix_ai_jobs_status_created", "tenant_id", "status", "created_at"),
    )

    project_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
    )
    job_type: Mapped[str] = mapped_column(String(64), index=True)
    provider: Mapped[str] = mapped_column(String(64), default="mock")
    model: Mapped[str] = mapped_column(String(120), default="mock")
    status: Mapped[AIJobStatus] = mapped_column(
        Enum(AIJobStatus, **enum_kwargs),
        default=AIJobStatus.PENDING,
        index=True,
    )
    input_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    output_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
