from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class InternshipState(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "internship_states"

    tenant_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    project_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    stage: Mapped[str] = mapped_column(String(32), nullable=False, default="initialization")
    day_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    total_days: Mapped[int] = mapped_column(Integer, nullable=False, default=14)
    approval_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    signals_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    generated_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    approved_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    preference_model: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    recommended_mode: Mapped[str | None] = mapped_column(String(32), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_extended: Mapped[bool] = mapped_column(default=False)
