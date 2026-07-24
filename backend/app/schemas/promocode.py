from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.db.enums import PromoCodeKind

TypePromoCode = PromoCodeKind


class CreatePromocode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    description: str = ""
    type_promo: TypePromoCode
    value: float = Field(ge=0)
    max_uses: int | None = Field(default=None, ge=1)
    start_time: datetime | None = None
    expire_time: datetime | None = None
    is_active: bool = True

    @model_validator(mode="after")
    def validate_payload(self) -> "CreatePromocode":
        if self.expire_time and self.start_time and self.expire_time <= self.start_time:
            raise ValueError("expire_time must be later than start_time")
        if self.type_promo == TypePromoCode.PERCENT and not 0 < self.value <= 100:
            raise ValueError("percent promo value must be between 0 and 100")
        if self.type_promo == TypePromoCode.GIFT_PLAN and self.value < 0:
            raise ValueError("gift_plan value cannot be negative")
        if self.type_promo != TypePromoCode.GIFT_PLAN and self.value <= 0:
            raise ValueError("promo value must be greater than 0")
        return self


class ChangePromocode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str | None = None
    type_promo: TypePromoCode | None = None
    value: float | None = Field(default=None, ge=0)
    max_uses: int | None = Field(default=None, ge=1)
    start_time: datetime | None = None
    expire_time: datetime | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_payload(self) -> "ChangePromocode":
        if self.expire_time and self.start_time and self.expire_time <= self.start_time:
            raise ValueError("expire_time must be later than start_time")
        if self.type_promo == TypePromoCode.PERCENT and self.value is not None and not 0 < self.value <= 100:
            raise ValueError("percent promo value must be between 0 and 100")
        if self.type_promo == TypePromoCode.GIFT_PLAN and self.value is not None and self.value < 0:
            raise ValueError("gift_plan value cannot be negative")
        return self


class DeletePromocode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=3, max_length=64)


class PromocodeResponse(BaseModel):
    promo_code_id: str
    code: str
    description: str
    type_promo: TypePromoCode
    value: float
    max_uses: int | None
    uses_total: int
    remaining_uses: int | None
    start_time: datetime | None
    expire_time: datetime | None
    is_active: bool
    created_by_user_id: str | None
    created_at: datetime
    updated_at: datetime


class PromocodePreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=3, max_length=64)
    plan_code: str = Field(min_length=1, max_length=64)


class AppliedPromocodeResponse(BaseModel):
    code: str
    type_promo: TypePromoCode
    original_price_amount: float
    discount_amount: float
    final_price_amount: float
    redeemed_at: datetime


class PromocodePreviewResponse(BaseModel):
    code: str
    type_promo: TypePromoCode
    plan_code: str
    original_price_amount: float
    discount_amount: float
    final_price_amount: float
    remaining_uses: int | None
    is_valid: bool = True
    message: str | None = None
