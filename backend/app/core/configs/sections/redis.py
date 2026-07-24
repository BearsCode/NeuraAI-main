from __future__ import annotations

from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import Field, SecretStr, computed_field, field_validator

from backend.app.core.configs.base import ConfigSection, load_section_settings
from backend.app.core.configs.normalizers import normalize_optional_string, normalize_string, validate_hostname_or_ip


class RedisConfig(ConfigSection):
    """Redis connectivity plus cache and stream retention defaults."""

    dsn: str | None = None
    host: str = "localhost"
    username: str | None = None
    password: SecretStr | None = None
    port: int = Field(default=6379, ge=1, le=65535)
    database: int = Field(default=0, ge=0)
    cache_ttl_seconds: int = Field(default=300, ge=1)
    rate_limit_ttl_seconds: int = Field(default=60, ge=1)
    stream_max_len: int = Field(default=10000, ge=1)

    @field_validator("dsn", "username", mode="before")
    @classmethod
    def normalize_optional_strings(cls, value: object) -> object:
        return normalize_optional_string(value)

    @field_validator("host", mode="before")
    @classmethod
    def normalize_host(cls, value: object) -> object:
        return normalize_string(value)

    @field_validator("password", mode="before")
    @classmethod
    def normalize_password(cls, value: object) -> object:
        normalized = normalize_optional_string(value)
        return value if normalized is None else normalized

    @field_validator("dsn")
    @classmethod
    def validate_dsn(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not value.startswith(("redis://", "rediss://")):
            raise ValueError("dsn must start with redis:// or rediss://")
        return value

    @field_validator("host")
    @classmethod
    def validate_host(cls, value: str) -> str:
        return validate_hostname_or_ip(value, field_name="host")

    @computed_field(return_type=str)
    @property
    def resolved_dsn(self) -> str:
        if self.dsn:
            return self.dsn
        auth = ""
        if self.username:
            auth = quote_plus(self.username)
            if self.password:
                auth = f"{auth}:{quote_plus(self.password.get_secret_value())}"
            auth = f"{auth}@"
        return f"redis://{auth}{self.host}:{self.port}/{self.database}"

    @computed_field(return_type=bool)
    @property
    def is_tls(self) -> bool:
        return self.resolved_dsn.startswith("rediss://")

    @computed_field(return_type=str)
    @property
    def masked_dsn(self) -> str:
        if "://" not in self.resolved_dsn:
            return self.resolved_dsn
        scheme, remainder = self.resolved_dsn.split("://", maxsplit=1)
        if "@" not in remainder:
            return self.resolved_dsn
        _, host_part = remainder.rsplit("@", maxsplit=1)
        return f"{scheme}://***:***@{host_part}"


@lru_cache(maxsize=1)
def get_redis_config() -> RedisConfig:
    return load_section_settings("redis", RedisConfig)
