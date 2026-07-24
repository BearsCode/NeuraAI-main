from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class WorkflowStep(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "workflow_steps"

    workflow_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    step_order: Mapped[int] = mapped_column(nullable=False)
    step_type: Mapped[str] = mapped_column(String(64), nullable=False)
    agent_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    input_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    output_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retry_count: Mapped[int] = mapped_column(nullable=False, default=0)
    async_job_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
