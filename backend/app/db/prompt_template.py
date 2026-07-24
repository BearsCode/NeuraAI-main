from __future__ import annotations

from sqlalchemy import Boolean, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PromptTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Editable prompt templates stored in the database."""

    __tablename__ = "prompt_templates"
    __table_args__ = (
        UniqueConstraint("tenant_id", "task_type", "version", name="uq_prompt_templates_scope_version"),
        Index("ix_prompt_templates_task_active", "task_type", "is_active"),
    )

    tenant_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    task_type: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    system_prompt: Mapped[str] = mapped_column(Text)
    user_prompt_template: Mapped[str] = mapped_column(Text)
    response_schema: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
