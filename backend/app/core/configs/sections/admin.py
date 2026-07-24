from __future__ import annotations

from functools import lru_cache

from pydantic import Field, SecretStr, field_validator

from backend.app.core.configs.base import ConfigSection, load_section_settings


class AdminConfig(ConfigSection):
    super_admin_emails: list[str] = Field(default_factory=lambda: ["admin@example.com"])

    admin_secret_key: SecretStr = SecretStr("  ")
    admin_salt: str = ""
    admin_path_rotation_hours: int = Field(default=24, ge=1)
    admin_path_grace_hours: int = Field(default=24, ge=0)

    master_encryption_key: SecretStr = SecretStr("  ")

    @field_validator("admin_secret_key")
    @classmethod
    def validate_admin_secret_key(cls, value: SecretStr) -> SecretStr:
        raw = value.get_secret_value().strip()
        if not raw or raw in ("change-me", "changeme-admin-secret-key"):
            return value
        if len(raw) < 16:
            raise ValueError("admin_secret_key must be at least 16 characters long")
        return value

    @field_validator("master_encryption_key")
    @classmethod
    def validate_master_encryption_key(cls, value: SecretStr) -> SecretStr:
        raw = value.get_secret_value().strip()
        if not raw or raw in ("change-me", "change-me-master-encryption-key-32bytes!"):
            return value
        if len(raw) < 16:
            raise ValueError("master_encryption_key must be at least 16 characters long")
        return value

    two_factor_enabled: bool = True
    two_factor_code_ttl_seconds: int = Field(default=300, ge=60)
    two_factor_max_attempts: int = Field(default=3, ge=1)
    two_factor_block_minutes: int = Field(default=15, ge=1)
    two_factor_resend_limit: int = Field(default=3, ge=1)
    two_factor_resend_window_seconds: int = Field(default=300, ge=60)

    device_fingerprint_enabled: bool = True
    device_fingerprint_confirmation_email: bool = True

    anomaly_learning_days: int = Field(default=30, ge=1)
    anomaly_max_actions_per_minute: int = Field(default=60, ge=1)
    anomaly_suspicious_hours_start: int = Field(default=2, ge=0, le=23)
    anomaly_suspicious_hours_end: int = Field(default=6, ge=0, le=23)

    brute_force_max_attempts: int = Field(default=5, ge=1)
    brute_force_block_minutes: int = Field(default=15, ge=1)
    brute_force_3_blocks_hours: int = Field(default=1, ge=1)

    session_ttl_minutes: int = Field(default=15, ge=1)
    admin_session_ttl_minutes: int = Field(default=480, ge=60)
    max_admin_sessions_per_user: int = Field(default=3, ge=1)

    rate_limit_read_per_minute: int = Field(default=60, ge=1)
    rate_limit_write_per_minute: int = Field(default=15, ge=1)

    ip_allowlist: list[str] = Field(default_factory=list)


@lru_cache(maxsize=1)
def get_admin_config() -> AdminConfig:
    return load_section_settings("admin", AdminConfig)
