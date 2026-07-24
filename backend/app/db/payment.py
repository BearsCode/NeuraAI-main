from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin
from backend.app.db.enums import PaymentStatus, enum_kwargs

if TYPE_CHECKING:
    from backend.app.db.partner_commission import PartnerCommission
    from backend.app.db.subscription import Subscription


class Payment(UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin, Base):
    __tablename__ = "payments"
    __table_args__ = (
        Index("ix_payments_tenant_status_created", "tenant_id", "status", "created_at"),
        UniqueConstraint("external_payment_id", name="uq_payments_external_payment_id"),
    )

    subscription_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
        index=True,
    )
    external_payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount: Mapped[float] = mapped_column(Float, default=0)
    currency: Mapped[str] = mapped_column(String(8), default="RUB")
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, **enum_kwargs),
        default=PaymentStatus.PENDING,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(64), default="manual")
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    subscription: Mapped["Subscription"] = relationship(back_populates="payments")
    commissions: Mapped[list["PartnerCommission"]] = relationship(
        back_populates="payment",
        cascade="all, delete-orphan",
    )
