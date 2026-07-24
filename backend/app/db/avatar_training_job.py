from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AvatarTrainingJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "avatar_training_jobs"

    tenant_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    avatar_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    avatar_type: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_job_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    input_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    output_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
