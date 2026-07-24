from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DeviceFingerprint(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "device_fingerprints"
    __table_args__ = (
        Index("ix_device_fingerprints_user_hash", "user_id", "fingerprint_hash"),
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    fingerprint_hash: Mapped[str] = mapped_column(String(128), index=True)
    device_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_trusted: Mapped[bool] = mapped_column(Boolean, default=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
