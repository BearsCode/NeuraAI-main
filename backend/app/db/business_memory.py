from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class BusinessMemory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "business_memory"

    tenant_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    project_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)

    memory_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    title: Mapped[str] = mapped_column(String(256), nullable=False)
    content: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confidence: Mapped[float | None] = mapped_column(nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
