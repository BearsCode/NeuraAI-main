from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import computed_field, field_validator, model_validator

from backend.app.core.configs.base import ConfigSection, load_section_settings
from backend.app.core.configs.normalizers import normalize_log_level, normalize_optional_url, normalize_string


class ObservabilityConfig(ConfigSection):
    """Logging, metrics, and tracing configuration."""

    log_level: Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"] = "INFO"
    log_json: bool = True
    service_name: str = "neura-backend"
    otlp_endpoint: str | None = None
    metrics_enabled: bool = True
    traces_enabled: bool = False

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level_value(cls, value: object) -> object:
        return normalize_log_level(value)

    @field_validator("service_name", mode="before")
    @classmethod
    def normalize_service_name(cls, value: object) -> object:
        return normalize_string(value)

    @field_validator("otlp_endpoint", mode="before")
    @classmethod
    def normalize_otlp_endpoint(cls, value: object) -> object:
        return normalize_optional_url(value)

    @model_validator(mode="after")
    def validate_tracing_configuration(self) -> "ObservabilityConfig":
        if self.traces_enabled and not self.otlp_endpoint:
            raise ValueError("otlp_endpoint must be configured when traces_enabled is true")
        return self

    @computed_field(return_type=bool)
    @property
    def otlp_enabled(self) -> bool:
        return self.traces_enabled and bool(self.otlp_endpoint)


@lru_cache(maxsize=1)
def get_observability_config() -> ObservabilityConfig:
    return load_section_settings("observability", ObservabilityConfig)
