from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from backend.app.schemas.promocode import AppliedPromocodeResponse


class SubscriptionPlanResponse(BaseModel):
    plan_id: str
    code: str
    name: str
    price_amount: float
    currency: str
    requests_per_minute: int
    content_generations_per_hour: int
    publications_per_hour: int
    features: dict


class SubscriptionResponse(BaseModel):
    subscription_id: str
    tenant_id: str
    plan_code: str
    price_amount: float | None
    currency: str | None
    next_charge_amount: float | None
    status: str
    next_charge_at: datetime | None
    trial_ends_at: datetime | None
    applied_promocode: AppliedPromocodeResponse | None = None


class ChangePlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_code: str
    promo_code: str | None = None


class PaymentResponse(BaseModel):
    payment_id: str
    amount: float
    currency: str
    status: str
    provider: str
    paid_at: datetime | None


class CommissionResponse(BaseModel):
    commission_id: str
    tenant_id: str
    amount: float
    status: str
    paid_out_at: datetime | None
