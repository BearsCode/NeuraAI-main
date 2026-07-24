from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, Float, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SubscriptionPlan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "subscription_plans"
    __table_args__ = (
        UniqueConstraint("code", name="uq_subscription_plans_code"),
        CheckConstraint("price_amount >= 0", name="price_amount_positive"),
    )

    code: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")
    price_amount: Mapped[float] = mapped_column(Float, default=0)
    currency: Mapped[str] = mapped_column(String(8), default="RUB")
    requests_per_minute: Mapped[int] = mapped_column(Integer, default=120)
    content_generations_per_hour: Mapped[int] = mapped_column(Integer, default=100)
    publications_per_hour: Mapped[int] = mapped_column(Integer, default=50)
    features: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
