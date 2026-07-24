from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AdminSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "admin_sessions"
    __table_args__ = (
        Index("ix_admin_sessions_user_expires", "user_id", "expires_at"),
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    admin_role: Mapped[str] = mapped_column(String(16))
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    device_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    impersonating_user_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True
    )
    impersonation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
