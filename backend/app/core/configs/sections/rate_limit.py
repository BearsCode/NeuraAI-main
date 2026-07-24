from __future__ import annotations

from functools import lru_cache

from pydantic import Field, model_validator

from backend.app.core.configs.base import ConfigSection, load_section_settings


class RateLimitConfig(ConfigSection):
    """Default request and throughput limits applied by the API gateway layer."""

    anonymous_requests_per_minute: int = Field(default=30, ge=1)
    client_requests_per_minute: int = Field(default=120, ge=1)
    partner_requests_per_minute: int = Field(default=180, ge=1)
    admin_requests_per_minute: int = Field(default=300, ge=1)
    login_attempts_per_minute: int = Field(default=5, ge=1)
    publish_per_hour: int = Field(default=50, ge=1)
    generation_per_hour: int = Field(default=100, ge=1)

    @model_validator(mode="after")
    def validate_rate_hierarchy(self) -> "RateLimitConfig":
        if self.client_requests_per_minute < self.anonymous_requests_per_minute:
            raise ValueError("client_requests_per_minute cannot be lower than anonymous_requests_per_minute")
        if self.partner_requests_per_minute < self.client_requests_per_minute:
            raise ValueError("partner_requests_per_minute cannot be lower than client_requests_per_minute")
        if self.admin_requests_per_minute < self.partner_requests_per_minute:
            raise ValueError("admin_requests_per_minute cannot be lower than partner_requests_per_minute")
        return self


@lru_cache(maxsize=1)
def get_rate_limit_config() -> RateLimitConfig:
    return load_section_settings("rate_limit", RateLimitConfig)
