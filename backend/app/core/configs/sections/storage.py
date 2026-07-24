from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, computed_field, field_validator, model_validator

from backend.app.core.configs.base import ConfigSection, load_section_settings
from backend.app.core.configs.normalizers import (
    normalize_optional_url,
    normalize_optional_string,
    normalize_string,
    normalize_string_list,
    validate_absolute_url,
    validate_s3_bucket_name,
)


class S3Config(ConfigSection):
    """Object-storage configuration for local and S3-compatible backends."""

    backend: Literal["local", "s3"] = "local"
    local_root: str = "./storage/uploads"
    max_upload_size_mb: int = Field(default=25, ge=1)
    allowed_upload_content_types: list[str] = Field(
        default_factory=lambda: [
            "image/jpeg",
            "image/png",
            "image/webp",
            "video/mp4",
            "application/pdf",
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "application/zip",
        ]
    )
    endpoint_url: str = ""
    access_key_id: SecretStr | None = None
    secret_access_key: SecretStr | None = None
    bucket: str = "neura-media"
    region: str = "us-east-1"
    public_base_url: str = ""
    use_path_style: bool = True
    signed_url_ttl_seconds: int = Field(default=900, ge=1)

    @field_validator("backend", mode="before")
    @classmethod
    def normalize_backend(cls, value: object) -> object:
        normalized = normalize_optional_string(value)
        return normalized.lower() if normalized else value

    @field_validator("local_root", mode="before")
    @classmethod
    def normalize_local_root(cls, value: object) -> object:
        return normalize_string(value)

    @field_validator("bucket", "region", mode="before")
    @classmethod
    def normalize_bucket_and_region(cls, value: object) -> object:
        normalized = normalize_string(value)
        return normalized.lower() if isinstance(normalized, str) else normalized

    @field_validator("endpoint_url", "public_base_url", mode="before")
    @classmethod
    def normalize_urls(cls, value: object) -> object:
        return normalize_optional_url(value) or ""

    @field_validator("access_key_id", "secret_access_key", mode="before")
    @classmethod
    def normalize_optional_secrets(cls, value: object) -> object:
        return normalize_optional_string(value)

    @field_validator("allowed_upload_content_types", mode="before")
    @classmethod
    def normalize_content_types(cls, value: object) -> object:
        normalized = normalize_string_list(value)
        if not isinstance(normalized, list):
            return normalized
        return [item.lower() for item in normalized]

    @field_validator("bucket")
    @classmethod
    def validate_bucket(cls, value: str) -> str:
        return validate_s3_bucket_name(value)

    @field_validator("endpoint_url")
    @classmethod
    def validate_endpoint_url(cls, value: str) -> str:
        if not value:
            return value
        return validate_absolute_url(value, field_name="endpoint_url", allowed_schemes=("http", "https"))

    @field_validator("public_base_url")
    @classmethod
    def validate_public_base_url(cls, value: str) -> str:
        if not value:
            return value
        return validate_absolute_url(value, field_name="public_base_url", allowed_schemes=("http", "https"))

    @model_validator(mode="after")
    def validate_backend_specific_settings(self) -> "S3Config":
        if self.backend == "s3" and bool(self.access_key_id) != bool(self.secret_access_key):
            raise ValueError("access_key_id and secret_access_key must be configured together for S3 backend")
        return self

    @computed_field(return_type=bool)
    @property
    def is_remote(self) -> bool:
        return self.backend == "s3" or bool(self.endpoint_url)

    @computed_field(return_type=int)
    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache(maxsize=1)
def get_s3_config() -> S3Config:
    return load_section_settings("s3", S3Config)
