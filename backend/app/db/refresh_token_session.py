from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.app.db.user import User


class RefreshTokenSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "refresh_token_sessions"
    __table_args__ = (
        UniqueConstraint("token_id_hash", name="uq_refresh_token_sessions_token_id_hash"),
        Index("ix_refresh_token_sessions_user_expires_at", "user_id", "expires_at"),
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    token_id_hash: Mapped[str] = mapped_column(String(64), index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    session_family_id: Mapped[str] = mapped_column(String(36), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    replaced_by_token_id_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    user: Mapped["User"] = relationship(back_populates="refresh_sessions")
