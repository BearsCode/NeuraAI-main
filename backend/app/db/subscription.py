from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin
from backend.app.db.enums import SubscriptionStatus, enum_kwargs

if TYPE_CHECKING:
    from backend.app.db.payment import Payment
    from backend.app.db.promo_code_redemption import PromoCodeRedemption
    from backend.app.db.subscription_plan import SubscriptionPlan
    from backend.app.db.tenant import Tenant


class Subscription(UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin, Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        Index("ix_subscriptions_tenant_status", "tenant_id", "status"),
    )

    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        index=True,
    )
    plan_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("subscription_plans.id", ondelete="RESTRICT"),
        index=True,
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, **enum_kwargs),
        default=SubscriptionStatus.TRIAL,
        index=True,
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_charge_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    seats: Mapped[int] = mapped_column(Integer, default=1)
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    active_promo_code_redemption_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("promo_code_redemptions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    tenant: Mapped["Tenant"] = relationship(back_populates="subscriptions")
    plan: Mapped["SubscriptionPlan"] = relationship()
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="subscription",
        cascade="all, delete-orphan",
    )
    active_promo_code_redemption: Mapped["PromoCodeRedemption | None"] = relationship(
        foreign_keys=[active_promo_code_redemption_id],
        post_update=True,
    )
    promo_code_redemptions: Mapped[list["PromoCodeRedemption"]] = relationship(
        back_populates="subscription",
        cascade="all, delete-orphan",
        foreign_keys="PromoCodeRedemption.subscription_id",
    )
