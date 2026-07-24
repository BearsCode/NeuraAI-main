from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class EmailVerificationCode(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "email_verification_codes"
    __table_args__ = (
        Index("ix_email_verification_codes_email_expires", "email", "expires_at"),
    )

    email: Mapped[str] = mapped_column(String(255), index=True)
    code_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
