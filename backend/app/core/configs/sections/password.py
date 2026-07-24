from __future__ import annotations

from functools import lru_cache

from pydantic import Field

from backend.app.core.configs.base import ConfigSection, load_section_settings


class PasswordConfig(ConfigSection):
    """Password policy settings."""

    min_length: int = Field(default=10, ge=8)
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digit: bool = True
    require_special: bool = False


@lru_cache(maxsize=1)
def get_password_config() -> PasswordConfig:
    return load_section_settings("password", PasswordConfig)
