from __future__ import annotations

from functools import lru_cache

from backend.app.core.configs.base import load_section_settings
from backend.app.core.configs.sections.bot_platform import BotPlatformConfig


class MaxConfig(BotPlatformConfig):
    """MAX platform bot configuration."""


@lru_cache(maxsize=1)
def get_max_config() -> MaxConfig:
    return load_section_settings("max", MaxConfig)
