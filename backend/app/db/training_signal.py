from __future__ import annotations

from sqlalchemy import Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TrainingSignal(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "training_signals"

    tenant_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    project_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    content_item_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    signal_weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    context: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    training_round: Mapped[int] = mapped_column(nullable=False, default=0)
    applied: Mapped[bool] = mapped_column(default=False)
