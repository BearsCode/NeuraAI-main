from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, computed_field, field_validator, model_validator

from backend.app.core.configs.base import ConfigSection, load_section_settings
from backend.app.core.configs.normalizers import normalize_optional_string


class SocialProviderConfig(ConfigSection):
    """OAuth and webhook controls for a single social platform adapter."""

    webhook_secret: SecretStr | None = None
    client_id: str | None = None
    client_secret: SecretStr | None = None
    rate_limit_per_minute: int = Field(default=60, ge=1)

    @field_validator("webhook_secret", "client_secret", mode="before")
    @classmethod
    def normalize_optional_secrets(cls, value: object) -> object:
        return normalize_optional_string(value)

    @field_validator("client_id", mode="before")
    @classmethod
    def normalize_client_id(cls, value: object) -> object:
        return normalize_optional_string(value)

    @model_validator(mode="after")
    def validate_oauth_pair(self) -> "SocialProviderConfig":
        if bool(self.client_id) != bool(self.client_secret):
            raise ValueError("client_id and client_secret must be configured together")
        return self

    @computed_field(return_type=bool)
    @property
    def oauth_configured(self) -> bool:
        return self.client_id is not None and self.client_secret is not None


class SocialConfig(ConfigSection):
    """Per-platform integration settings for outbound publishing adapters."""

    mode: Literal["mock", "live"] = "mock"
    telegram: SocialProviderConfig = Field(default_factory=SocialProviderConfig)
    vk: SocialProviderConfig = Field(default_factory=SocialProviderConfig)
    instagram: SocialProviderConfig = Field(default_factory=SocialProviderConfig)
    threads: SocialProviderConfig = Field(default_factory=SocialProviderConfig)
    tiktok: SocialProviderConfig = Field(default_factory=SocialProviderConfig)
    youtube: SocialProviderConfig = Field(default_factory=SocialProviderConfig)
    whatsapp_business: SocialProviderConfig = Field(default_factory=SocialProviderConfig)
    max: SocialProviderConfig = Field(default_factory=SocialProviderConfig)


@lru_cache(maxsize=1)
def get_social_config() -> SocialConfig:
    return load_section_settings("social", SocialConfig)
