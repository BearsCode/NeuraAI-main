from __future__ import annotations

from functools import lru_cache

from pydantic import Field, SecretStr, field_validator

from backend.app.core.configs.base import ConfigSection, load_section_settings
from backend.app.core.configs.normalizers import normalize_optional_string


class VKOAuthConfig(ConfigSection):
    client_id: str | None = None
    client_secret: SecretStr | None = None

    @field_validator("client_id", mode="before")
    @classmethod
    def normalize_client_id(cls, value: object) -> object:
        return normalize_optional_string(value)

    @field_validator("client_secret", mode="before")
    @classmethod
    def normalize_client_secret(cls, value: object) -> object:
        return normalize_optional_string(value)

    @property
    def configured(self) -> bool:
        return bool(self.client_id) and bool(self.client_secret)


class YandexOAuthConfig(ConfigSection):
    client_id: str | None = None
    client_secret: SecretStr | None = None

    @field_validator("client_id", mode="before")
    @classmethod
    def normalize_client_id(cls, value: object) -> object:
        return normalize_optional_string(value)

    @field_validator("client_secret", mode="before")
    @classmethod
    def normalize_client_secret(cls, value: object) -> object:
        return normalize_optional_string(value)

    @property
    def configured(self) -> bool:
        return bool(self.client_id) and bool(self.client_secret)


class MailruOAuthConfig(ConfigSection):
    client_id: str | None = None
    client_secret: SecretStr | None = None

    @field_validator("client_id", mode="before")
    @classmethod
    def normalize_client_id(cls, value: object) -> object:
        return normalize_optional_string(value)

    @field_validator("client_secret", mode="before")
    @classmethod
    def normalize_client_secret(cls, value: object) -> object:
        return normalize_optional_string(value)

    @property
    def configured(self) -> bool:
        return bool(self.client_id) and bool(self.client_secret)


class TelegramLoginConfig(ConfigSection):
    bot_token: SecretStr | None = None

    @field_validator("bot_token", mode="before")
    @classmethod
    def normalize_bot_token(cls, value: object) -> object:
        return normalize_optional_string(value)

    @property
    def configured(self) -> bool:
        return bool(self.bot_token)


class OAuthConfig(ConfigSection):
    vk: VKOAuthConfig = Field(default_factory=VKOAuthConfig)
    yandex: YandexOAuthConfig = Field(default_factory=YandexOAuthConfig)
    mailru: MailruOAuthConfig = Field(default_factory=MailruOAuthConfig)
    telegram_login: TelegramLoginConfig = Field(default_factory=TelegramLoginConfig)


@lru_cache(maxsize=1)
def get_oauth_config() -> OAuthConfig:
    return load_section_settings("oauth", OAuthConfig)
