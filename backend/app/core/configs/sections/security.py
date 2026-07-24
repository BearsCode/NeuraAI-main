from __future__ import annotations

from functools import lru_cache
import hashlib

from pydantic import Field, SecretStr, computed_field, field_validator

from backend.app.core.configs.base import ConfigSection, load_section_settings
from backend.app.core.configs.normalizers import normalize_optional_string, normalize_string


class SecurityConfig(ConfigSection):
    """Authentication, token lifetime, and secret-management settings."""

    jwt_secret_key: SecretStr = SecretStr("  ")  # MUST be set via env in production
    jwt_issuer: str = "neura"
    jwt_audience: str = "neura-clients"
    access_token_ttl_minutes: int = Field(default=30, ge=1)
    refresh_token_ttl_days: int = Field(default=30, ge=1)
    email_verification_ttl_seconds: int = Field(default=300, ge=60)
    email_verification_max_attempts: int = Field(default=5, ge=1)
    token_encryption_key: SecretStr = SecretStr("  ")  # MUST be set via env in production
    otp_signing_key: SecretStr = SecretStr("  ")  # MUST be set via env in production
    password_min_length: int = Field(default=10, ge=8)
    seed_admin_on_startup: bool = False

    @field_validator("jwt_secret_key", "token_encryption_key", "otp_signing_key", mode="before")
    @classmethod
    def normalize_secret_values(cls, value: object) -> object:
        normalized = normalize_optional_string(value)
        return value if normalized is None else normalized

    @field_validator("jwt_issuer", "jwt_audience", mode="before")
    @classmethod
    def normalize_strings(cls, value: object) -> object:
        return normalize_string(value)

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret_key(cls, value: SecretStr) -> SecretStr:
        raw = value.get_secret_value().strip()
        if not raw or raw in ("change-me", "changeme"):
            return value
        if len(raw) < 12:
            raise ValueError("jwt_secret_key must be at least 12 characters long")
        return value

    @field_validator("token_encryption_key")
    @classmethod
    def validate_token_encryption_key(cls, value: SecretStr) -> SecretStr:
        raw = value.get_secret_value().strip()
        if not raw or raw in ("change-me", "changeme"):
            return value
        if len(raw) < 16:
            raise ValueError("token_encryption_key must be at least 16 characters long")
        return value

    @computed_field(return_type=str)
    @property
    def token_encryption_fingerprint(self) -> str:
        digest = hashlib.sha256(self.token_encryption_key.get_secret_value().encode("utf-8")).hexdigest()
        return digest[:12]


JwtConfig = SecurityConfig


@lru_cache(maxsize=1)
def get_security_config() -> SecurityConfig:
    return load_section_settings("security", SecurityConfig)
