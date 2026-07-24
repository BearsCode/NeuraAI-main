from __future__ import annotations

from urllib.parse import urlsplit

from pydantic import Field, SecretStr, computed_field, field_validator, model_validator

from backend.app.core.configs.base import ConfigSection
from backend.app.core.configs.normalizers import normalize_int_list, normalize_optional_string, normalize_url


class BotPlatformConfig(ConfigSection):
    """Shared configuration contract for bot-based platform integrations."""

    bot_token: SecretStr | None = None
    admin_ids: list[int] = Field(default_factory=list)
    webhook_url: str = ""

    @field_validator("bot_token", mode="before")
    @classmethod
    def normalize_bot_token(cls, value: object) -> object:
        return normalize_optional_string(value)

    @field_validator("admin_ids", mode="before")
    @classmethod
    def normalize_admin_ids(cls, value: object) -> object:
        return normalize_int_list(value)

    @field_validator("webhook_url", mode="before")
    @classmethod
    def normalize_webhook_url(cls, value: object) -> object:
        return normalize_url(value)

    @field_validator("webhook_url")
    @classmethod
    def validate_webhook_url(cls, value: str) -> str:
        if not value:
            return value
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("webhook_url must be an absolute http/https URL")
        return value

    @model_validator(mode="after")
    def validate_admin_ids(self) -> "BotPlatformConfig":
        if any(admin_id <= 0 for admin_id in self.admin_ids):
            raise ValueError("admin_ids must contain only positive integer identifiers")
        return self

    @computed_field(return_type=bool)
    @property
    def enabled(self) -> bool:
        return self.bot_token is not None and bool(self.bot_token.get_secret_value())
