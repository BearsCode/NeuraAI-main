from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator

from backend.app.core.configs.base import ConfigSection, load_section_settings
from backend.app.core.configs.normalizers import normalize_optional_string


class EmailConfig(ConfigSection):
    provider: Literal["smtp", "console", "disabled"] = "console"
    smtp_host: str = "localhost"
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_user: str | None = None
    smtp_password: SecretStr | None = None
    smtp_use_tls: bool = True
    default_from: str = "noreply@neuara.ai"
    default_from_name: str = "NeuaraAI"

    @field_validator("smtp_user", mode="before")
    @classmethod
    def normalize_smtp_user(cls, value: object) -> object:
        return normalize_optional_string(value)

    @field_validator("smtp_password", mode="before")
    @classmethod
    def normalize_smtp_password(cls, value: object) -> object:
        return normalize_optional_string(value)


@lru_cache(maxsize=1)
def get_email_config() -> EmailConfig:
    return load_section_settings("email", EmailConfig)
