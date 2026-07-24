from __future__ import annotations

from sqlalchemy import Boolean, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AIExpertPrompt(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_expert_prompts"
    __table_args__ = (
        UniqueConstraint("niche", name="uq_ai_expert_prompts_niche"),
        Index("ix_ai_expert_prompts_active", "niche", "is_active"),
    )

    niche: Mapped[str] = mapped_column(String(120), index=True)
    role_description: Mapped[str] = mapped_column(Text)
    tone: Mapped[str] = mapped_column(String(120), default="expert, practical, concise")
    additional_instructions: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
