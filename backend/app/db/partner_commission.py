from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin
from backend.app.db.enums import CommissionStatus, enum_kwargs

if TYPE_CHECKING:
    from backend.app.db.payment import Payment
    from backend.app.db.user import User


class PartnerCommission(UUIDPrimaryKeyMixin, TimestampMixin, TenantScopedMixin, Base):
    __tablename__ = "partner_commissions"
    __table_args__ = (
        Index("ix_partner_commissions_partner_status", "partner_user_id", "status"),
    )

    partner_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
    )
    payment_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("payments.id", ondelete="CASCADE"),
        index=True,
    )
    amount: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[CommissionStatus] = mapped_column(
        Enum(CommissionStatus, **enum_kwargs),
        default=CommissionStatus.PENDING,
    )
    paid_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    partner_user: Mapped["User"] = relationship(back_populates="commissions")
    payment: Mapped["Payment"] = relationship(back_populates="commissions")
