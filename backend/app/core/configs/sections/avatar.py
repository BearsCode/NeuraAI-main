from __future__ import annotations

from functools import lru_cache

from pydantic import Field, SecretStr, field_validator

from backend.app.core.configs.base import ConfigSection, load_section_settings
from backend.app.core.configs.normalizers import normalize_optional_string


class HeygenConfig(ConfigSection):
    api_key: SecretStr | None = None
    base_url: str = "https://api.heygen.com"
    webhook_secret: SecretStr | None = None

    @field_validator("api_key", "webhook_secret", mode="before")
    @classmethod
    def normalize_secrets(cls, value: object) -> object:
        return normalize_optional_string(value)


class ReplicateConfig(ConfigSection):
    api_key: SecretStr | None = None
    base_url: str = "https://api.replicate.com/v1"
    webhook_secret: SecretStr | None = None
    flower_trigger_word: str = "TOK"
    lora_model_owner: str = "ostris"
    lora_model_name: str = "flux-dev-lora-trainer"

    @field_validator("api_key", "webhook_secret", mode="before")
    @classmethod
    def normalize_secrets(cls, value: object) -> object:
        return normalize_optional_string(value)


class AvatarConfig(ConfigSection):
    heygen: HeygenConfig = Field(default_factory=HeygenConfig)
    replicate: ReplicateConfig = Field(default_factory=ReplicateConfig)

    @property
    def heygen_configured(self) -> bool:
        return self.heygen.api_key is not None

    @property
    def replicate_configured(self) -> bool:
        return self.replicate.api_key is not None


@lru_cache(maxsize=1)
def get_avatar_config() -> AvatarConfig:
    return load_section_settings("avatar", AvatarConfig)
