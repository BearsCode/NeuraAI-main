from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.app.db.content_item import ContentItem


class ContentVersion(UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin, Base):
    __tablename__ = "content_versions"
    __table_args__ = (
        UniqueConstraint("content_item_id", "version_number", name="uq_content_versions_number"),
    )

    content_item_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("content_items.id", ondelete="CASCADE"),
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    prompt_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    ai_provider: Mapped[str] = mapped_column(String(64), default="mock")
    ai_model: Mapped[str] = mapped_column(String(120), default="mock")

    content_item: Mapped["ContentItem"] = relationship(back_populates="versions")
