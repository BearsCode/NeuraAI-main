from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from backend.app.db.enums import ToolProviderType, ToolStatus, enum_kwargs


class Tool(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "tool_registry"

    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    provider_type: Mapped[ToolProviderType] = mapped_column(
        Enum(ToolProviderType, **enum_kwargs),
        nullable=False,
        index=True,
    )
    api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[ToolStatus] = mapped_column(
        Enum(ToolStatus, **enum_kwargs),
        default=ToolStatus.INACTIVE,
        nullable=False,
        index=True,
    )
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
