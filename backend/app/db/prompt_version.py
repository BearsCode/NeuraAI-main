from __future__ import annotations

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PromptVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "prompt_versions"

    prompt_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ai_expert_prompts.id", ondelete="CASCADE"),
        index=True,
    )
    content: Mapped[str] = mapped_column(Text)
    diff: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    author_id: Mapped[str] = mapped_column(String(36))
