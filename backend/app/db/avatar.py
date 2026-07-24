from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Avatar(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "avatars"

    tenant_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    avatar_type: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    source_urls: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    model_weights_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    preview_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provider_model_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(default=True)
