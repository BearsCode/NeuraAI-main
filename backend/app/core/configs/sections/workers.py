from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator, model_validator

from backend.app.core.configs.base import ConfigSection, load_section_settings
from backend.app.core.configs.normalizers import normalize_string, validate_queue_name


class WorkerConfig(ConfigSection):
    """Queue naming and lifecycle settings for background workers."""

    llm_queue_name: str = "neura:llm"
    publisher_queue_name: str = "neura:publisher"
    analytics_queue_name: str = "neura:analytics"
    outbox_queue_name: str = "neura:outbox"
    shutdown_grace_seconds: int = Field(default=30, ge=1)
    max_retries: int = Field(default=5, ge=0)

    @field_validator(
        "llm_queue_name",
        "publisher_queue_name",
        "analytics_queue_name",
        "outbox_queue_name",
        mode="before",
    )
    @classmethod
    def normalize_queue_names(cls, value: object) -> object:
        return normalize_string(value)

    @field_validator(
        "llm_queue_name",
        "publisher_queue_name",
        "analytics_queue_name",
        "outbox_queue_name",
    )
    @classmethod
    def validate_queue_names(cls, value: str) -> str:
        return validate_queue_name(value)

    @model_validator(mode="after")
    def validate_unique_queue_names(self) -> "WorkerConfig":
        queue_names = {
            self.llm_queue_name,
            self.publisher_queue_name,
            self.analytics_queue_name,
            self.outbox_queue_name,
        }
        if len(queue_names) != 4:
            raise ValueError("worker queue names must be unique")
        return self


@lru_cache(maxsize=1)
def get_worker_config() -> WorkerConfig:
    return load_section_settings("workers", WorkerConfig)
