from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, computed_field, field_validator

from backend.app.core.configs.base import ConfigSection, load_section_settings
from backend.app.core.configs.normalizers import normalize_ai_provider, normalize_optional_string, normalize_optional_url


class AIProviderConfig(ConfigSection):
    """Provider-specific credentials and endpoint overrides for LLM vendors."""

    api_key: SecretStr | None = None
    base_url: str | None = None
    model: str | None = None

    @field_validator("api_key", mode="before")
    @classmethod
    def normalize_api_key(cls, value: object) -> object:
        return normalize_optional_string(value)

    @field_validator("base_url", mode="before")
    @classmethod
    def normalize_base_url(cls, value: object) -> object:
        return normalize_optional_url(value)

    @field_validator("model", mode="before")
    @classmethod
    def normalize_model(cls, value: object) -> object:
        return normalize_optional_string(value)


class AIConfig(ConfigSection):
    """Global AI routing, timeout, and circuit-breaker configuration."""

    provider: Literal["openai", "claude", "gemini", "mock"] = "mock"
    request_timeout_seconds: int = Field(default=60, ge=1)
    circuit_breaker_failures: int = Field(default=5, ge=1)
    circuit_breaker_reset_seconds: int = Field(default=60, ge=1)
    dalle_model: str = "dall-e-3"
    dalle_image_size: str = "1024x1024"
    openai: AIProviderConfig = Field(default_factory=AIProviderConfig)
    claude: AIProviderConfig = Field(default_factory=AIProviderConfig)
    gemini: AIProviderConfig = Field(default_factory=AIProviderConfig)
    heygen: AIProviderConfig = Field(default_factory=AIProviderConfig)

    @field_validator("provider", mode="before")
    @classmethod
    def normalize_provider(cls, value: object) -> object:
        return normalize_ai_provider(value)

    @computed_field(return_type=bool)
    @property
    def has_active_credentials(self) -> bool:
        if self.provider == "mock":
            return True
        provider_settings = getattr(self, self.provider)
        return provider_settings.api_key is not None


@lru_cache(maxsize=1)
def get_ai_config() -> AIConfig:
    return load_section_settings("ai", AIConfig)
