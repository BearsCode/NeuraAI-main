from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.app.db.user import User


class PartnerProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "partner_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_partner_profiles_user"),
        UniqueConstraint("referral_code", name="uq_partner_profiles_referral_code"),
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    referral_code: Mapped[str] = mapped_column(String(64), index=True)
    commission_rate: Mapped[float] = mapped_column(Float, default=0.2)
    total_income: Mapped[float] = mapped_column(Float, default=0)
    pending_payout: Mapped[float] = mapped_column(Float, default=0)

    user: Mapped["User"] = relationship(back_populates="partner_profile")
