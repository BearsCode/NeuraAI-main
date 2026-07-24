from __future__ import annotations

from functools import lru_cache
import re
from typing import ClassVar, Literal

from pydantic import SecretStr, field_validator, model_validator

from backend.app.core.configs.base import load_section_settings
from backend.app.core.configs.sections.bot_platform import BotPlatformConfig
from backend.app.core.configs.normalizers import ensure_leading_slash


class TelegramConfig(BotPlatformConfig):
    """Telegram bot delivery settings."""

    TELEGRAM_TOKEN_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"^\d+:[A-Za-z0-9_-]+$")

    bot_type: Literal["long_polling", "webhook"] = "long_polling"
    webhook_path: str = "/webhook/telegram"

    @field_validator("bot_type", mode="before")
    @classmethod
    def normalize_bot_type(cls, value: object) -> object:
        if isinstance(value, str) and value.strip().lower() == "long":
            return "long_polling"
        return value

    @field_validator("webhook_path", mode="before")
    @classmethod
    def normalize_webhook_path(cls, value: object) -> object:
        return ensure_leading_slash(value)

    @field_validator("bot_token")
    @classmethod
    def validate_bot_token(cls, value: SecretStr | None) -> SecretStr | None:
        if value is None:
            return value
        secret = value.get_secret_value()
        if secret and not cls.TELEGRAM_TOKEN_PATTERN.fullmatch(secret):
            raise ValueError("bot_token must match Telegram token format '<bot_id>:<token>'")
        return value

    @model_validator(mode="after")
    def validate_webhook_mode(self) -> "TelegramConfig":
        if self.bot_type == "webhook" and not self.webhook_url:
            raise ValueError("webhook_url is required when telegram bot_type is 'webhook'")
        return self


@lru_cache(maxsize=1)
def get_telegram_config() -> TelegramConfig:
    return load_section_settings("telegram", TelegramConfig)
