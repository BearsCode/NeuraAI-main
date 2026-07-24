from datetime import datetime

from typing import Literal

from pydantic import BaseModel, ConfigDict

PLAN_NAMES = Literal["trial", "starter", "growth", "enterprise"]


class SubscriptionResponse(BaseModel):
    plan_name: PLAN_NAMES
    status: str
    amount: float
    billing_period: str
    next_charge_at: datetime | None = None


class UpdateSubscriptionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_name: PLAN_NAMES
    billing_period: str = "monthly"
