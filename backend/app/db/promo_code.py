from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from backend.app.db.enums import PromoCodeKind, enum_kwargs

if TYPE_CHECKING:
    from backend.app.db.promo_code_redemption import PromoCodeRedemption
    from backend.app.db.user import User


class PromoCode(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "promo_codes"
    __table_args__ = (
        UniqueConstraint("code", name="uq_promo_codes_code"),
        CheckConstraint("value >= 0", name="promo_codes_value_positive"),
        CheckConstraint("max_uses IS NULL OR max_uses > 0", name="promo_codes_max_uses_positive"),
        CheckConstraint("uses_total >= 0", name="promo_codes_uses_total_positive"),
        Index("ix_promo_codes_active_window", "is_active", "starts_at", "expires_at"),
    )

    code: Mapped[str] = mapped_column(String(64), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    kind: Mapped[PromoCodeKind] = mapped_column(Enum(PromoCodeKind, **enum_kwargs), index=True)
    value: Mapped[float] = mapped_column(Float, default=0)
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    uses_total: Mapped[int] = mapped_column(Integer, default=0)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_by_user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_by: Mapped["User | None"] = relationship()
    redemptions: Mapped[list["PromoCodeRedemption"]] = relationship(
        back_populates="promo_code",
        cascade="all, delete-orphan",
    )
