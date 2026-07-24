from __future__ import annotations

from functools import lru_cache
import re
from typing import ClassVar, Literal

from pydantic import Field, SecretStr, computed_field, field_validator, model_validator

from backend.app.core.configs.base import ConfigSection, load_section_settings
from backend.app.core.configs.normalizers import normalize_optional_string


class YookassaConfig(ConfigSection):
    """Optional YooKassa provider credentials."""

    SECRET_KEY_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9_-]+$")

    shop_id: int | None = Field(default=None, ge=10_000, le=999_999_999)
    secret_key: SecretStr | None = None

    @field_validator("shop_id", mode="before")
    @classmethod
    def normalize_shop_id(cls, value: object) -> object:
        normalized = normalize_optional_string(value)
        if normalized is None:
            return None
        return normalized

    @field_validator("secret_key", mode="before")
    @classmethod
    def normalize_secret_key(cls, value: object) -> object:
        return normalize_optional_string(value)

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: SecretStr | None) -> SecretStr | None:
        if value is None:
            return value
        secret = value.get_secret_value()
        if len(secret) < 10:
            raise ValueError("yookassa.secret_key must be at least 10 characters long")
        if not cls.SECRET_KEY_PATTERN.fullmatch(secret):
            raise ValueError("yookassa.secret_key contains unsupported characters")
        return value

    @model_validator(mode="after")
    def validate_pair(self) -> "YookassaConfig":
        if bool(self.shop_id) != bool(self.secret_key):
            raise ValueError("yookassa.shop_id and yookassa.secret_key must be configured together")
        return self

    @computed_field(return_type=bool)
    @property
    def is_configured(self) -> bool:
        return self.shop_id is not None and self.secret_key is not None


class BillingConfig(ConfigSection):
    """Subscription and referral defaults shared across billing flows."""

    payments_provider: Literal["disabled", "yookassa"] = "disabled"
    partner_commission_rate: float = Field(default=0.2, ge=0, le=1)
    currency: str = "RUB"
    trial_days: int = Field(default=14, ge=0)
    webhook_secret: SecretStr | None = None
    yookassa: YookassaConfig = Field(default_factory=YookassaConfig)

    @field_validator("payments_provider", mode="before")
    @classmethod
    def normalize_payments_provider(cls, value: object) -> object:
        normalized = normalize_optional_string(value)
        return normalized.lower() if normalized else value

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: object) -> object:
        normalized = normalize_optional_string(value)
        return normalized.upper() if normalized else value

    @field_validator("webhook_secret", mode="before")
    @classmethod
    def normalize_webhook_secret(cls, value: object) -> object:
        return normalize_optional_string(value)

    @model_validator(mode="after")
    def validate_provider_configuration(self) -> "BillingConfig":
        if self.payments_provider == "yookassa" and not self.yookassa.is_configured:
            raise ValueError("yookassa credentials must be configured when payments_provider is 'yookassa'")
        return self

    @computed_field(return_type=float)
    @property
    def partner_commission_percent(self) -> float:
        return round(self.partner_commission_rate * 100, 2)


@lru_cache(maxsize=1)
def get_billing_config() -> BillingConfig:
    return load_section_settings("billing", BillingConfig)
