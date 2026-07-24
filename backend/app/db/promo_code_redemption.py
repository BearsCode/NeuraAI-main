from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from backend.app.db.promo_code import PromoCode
    from backend.app.db.subscription import Subscription
    from backend.app.db.user import User


class PromoCodeRedemption(UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin, Base):
    __tablename__ = "promo_code_redemptions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "promo_code_id", name="uq_promo_code_redemptions_tenant_code"),
        Index("ix_promo_code_redemptions_tenant_created", "tenant_id", "created_at"),
    )

    promo_code_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("promo_codes.id", ondelete="CASCADE"),
        index=True,
    )
    subscription_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    applied_by_user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    plan_code: Mapped[str] = mapped_column(String(64), index=True)
    original_price_amount: Mapped[float] = mapped_column(Float, default=0)
    discount_amount: Mapped[float] = mapped_column(Float, default=0)
    final_price_amount: Mapped[float] = mapped_column(Float, default=0)

    promo_code: Mapped["PromoCode"] = relationship(back_populates="redemptions")
    subscription: Mapped["Subscription | None"] = relationship(
        back_populates="promo_code_redemptions",
        foreign_keys=[subscription_id],
    )
    applied_by: Mapped["User | None"] = relationship()
