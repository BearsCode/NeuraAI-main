from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.app.db.user import User


class Notification(UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin, Base):
    """In-app notification stored for a user."""

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_read_created", "user_id", "is_read", "created_at"),
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    project_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    channel: Mapped[str] = mapped_column(String(32), default="in_app")
    severity: Mapped[str] = mapped_column(String(32), default="info")
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    user: Mapped["User"] = relationship()
