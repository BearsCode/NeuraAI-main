from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field, field_validator

from backend.app.core.configs.base import ConfigSection, load_section_settings
from backend.app.core.configs.normalizers import normalize_optional_string, normalize_string, validate_hostname_or_ip


class AppConfig(ConfigSection):
    """Process-level application identity and runtime mode."""

    name: str = Field(default="Neura Backend", min_length=2, max_length=120)
    env: Literal["local", "development", "staging", "production"] = "local"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    version: str = Field(default="1.0.0", min_length=1, max_length=32)
    default_timezone: str = Field(default="UTC", min_length=2, max_length=64)

    @field_validator("env", mode="before")
    @classmethod
    def normalize_env(cls, value: object) -> object:
        normalized = normalize_optional_string(value)
        return normalized.lower() if normalized else value

    @field_validator("name", "host", "version", "default_timezone", mode="before")
    @classmethod
    def normalize_strings(cls, value: object) -> object:
        return normalize_string(value)

    @field_validator("host")
    @classmethod
    def validate_host(cls, value: str) -> str:
        return validate_hostname_or_ip(value, field_name="host")

    @computed_field(return_type=bool)
    @property
    def is_production(self) -> bool:
        return self.env == "production"


@lru_cache(maxsize=1)
def get_app_config() -> AppConfig:
    return load_section_settings("app", AppConfig)
