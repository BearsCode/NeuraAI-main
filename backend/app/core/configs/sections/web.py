from __future__ import annotations

from functools import lru_cache

from pydantic import Field, SecretStr, computed_field, field_validator, model_validator

from backend.app.core.configs.base import ConfigSection, load_section_settings
from backend.app.core.configs.normalizers import (
    ensure_leading_slash,
    normalize_optional_url,
    normalize_optional_string,
    normalize_string_list,
    validate_absolute_url,
    validate_request_header_name,
)


class WebConfig(ConfigSection):
    """HTTP surface configuration: URLs, docs, CORS, and request metadata."""

    api_v1_prefix: str = "/api/v1"
    api_v2_prefix: str = "/api/v2"
    cors_origins: list[str] = Field(default_factory=list)
    public_base_url: str = "http://127.0.0.1:8000"
    docs_enabled: bool = False
    openapi_enabled: bool = False
    request_id_header: str = "X-Request-ID"
    domain: str | None = None
    admin_login: str | None = None
    admin_password: SecretStr | None = None

    @field_validator("api_v1_prefix", "api_v2_prefix", mode="before")
    @classmethod
    def normalize_api_prefix(cls, value: object) -> object:
        return ensure_leading_slash(value)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def normalize_cors_origins(cls, value: object) -> object:
        result = normalize_string_list(value)
        if result == ["*"]:
            raise ValueError('CORS allow_origins=["*"] is forbidden when allow_credentials=True. Specify explicit origins.')
        return result

    @field_validator("public_base_url", mode="before")
    @classmethod
    def normalize_public_base_url(cls, value: object) -> object:
        normalized = normalize_optional_url(value)
        return normalized or value

    @field_validator("request_id_header", mode="before")
    @classmethod
    def normalize_request_id_header(cls, value: object) -> object:
        normalized = normalize_optional_string(value)
        return normalized or value

    @field_validator("domain", "admin_login", "admin_password", mode="before")
    @classmethod
    def normalize_optional_values(cls, value: object) -> object:
        return normalize_optional_string(value)

    @field_validator("public_base_url")
    @classmethod
    def validate_public_base_url(cls, value: str) -> str:
        return validate_absolute_url(value, field_name="public_base_url", allowed_schemes=("http", "https"))

    @field_validator("request_id_header")
    @classmethod
    def validate_request_header(cls, value: str) -> str:
        return validate_request_header_name(value)

    @model_validator(mode="after")
    def validate_admin_credentials(self) -> "WebConfig":
        if bool(self.admin_login) != bool(self.admin_password):
            raise ValueError("admin_login and admin_password must be configured together")
        return self

    @computed_field(return_type=str)
    @property
    def normalized_public_base_url(self) -> str:
        return self.public_base_url.rstrip("/")


@lru_cache(maxsize=1)
def get_web_config() -> WebConfig:
    return load_section_settings("web", WebConfig)
