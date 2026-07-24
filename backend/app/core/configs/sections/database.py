from __future__ import annotations

from functools import lru_cache
from typing import ClassVar
from urllib.parse import quote_plus, urlsplit

from pydantic import Field, SecretStr, computed_field, field_validator, model_validator

from backend.app.core.configs.base import ConfigSection, load_section_settings
from backend.app.core.configs.normalizers import (
    normalize_database_dsn,
    normalize_optional_string,
    normalize_string,
    validate_database_name,
    validate_hostname_or_ip,
)


class DatabaseConfig(ConfigSection):
    """Primary database connectivity and pooling settings."""

    SUPPORTED_SCHEMES: ClassVar[tuple[str, ...]] = (
        "postgres",
        "postgresql",
        "postgresql+asyncpg",
        "sqlite",
        "sqlite+aiosqlite",
    )

    dsn: str | None = None
    host: str = "localhost"
    port: int = Field(default=5432, ge=1, le=65535)
    database: str = "neura"
    username: str = "postgres"
    password: SecretStr = SecretStr("postgres")
    echo: bool = False
    run_migrations_on_startup: bool = False
    pool_size: int = Field(default=20, ge=1)
    max_overflow: int = Field(default=40, ge=0)
    pool_timeout_seconds: int = Field(default=30, ge=1)
    pool_recycle_seconds: int = Field(default=1800, ge=1)
    statement_timeout_ms: int = Field(default=5000, ge=1)
    sqlite_path: str = "./neuaraai.db"

    @field_validator("dsn", mode="before")
    @classmethod
    def normalize_dsn(cls, value: object) -> object:
        return normalize_database_dsn(value)

    @field_validator("host", "database", "username", "sqlite_path", mode="before")
    @classmethod
    def normalize_strings(cls, value: object) -> object:
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

        scheme = urlsplit(value).scheme or value.split("://", maxsplit=1)[0]
        if scheme not in cls.SUPPORTED_SCHEMES:
            supported = ", ".join(cls.SUPPORTED_SCHEMES)
            raise ValueError(f"dsn must use one of the supported schemes: {supported}")
        return value

    @field_validator("host")
    @classmethod
    def validate_host(cls, value: str) -> str:
        return validate_hostname_or_ip(value, field_name="host")

    @field_validator("database")
    @classmethod
    def validate_database(cls, value: str) -> str:
        return validate_database_name(value)

    @model_validator(mode="after")
    def validate_connection_parts(self) -> "DatabaseConfig":
        if self.dsn:
            return self

        if not self.host:
            raise ValueError("host must be configured when dsn is not provided")
        if not self.database:
            raise ValueError("database must be configured when dsn is not provided")
        if not self.username:
            raise ValueError("username must be configured when dsn is not provided")
        if not self.password or not self.password.get_secret_value():
            raise ValueError("password must be configured when dsn is not provided")
        return self

    @computed_field(return_type=str)
    @property
    def resolved_dsn(self) -> str:
        if self.dsn:
            return self.dsn
        username = quote_plus(self.username)
        password = quote_plus(self.password.get_secret_value())
        return f"postgresql+asyncpg://{username}:{password}@{self.host}:{self.port}/{self.database}"

    @computed_field(return_type=bool)
    @property
    def uses_sqlite(self) -> bool:
        return self.resolved_dsn.startswith("sqlite")

    @computed_field(return_type=str)
    @property
    def sync_dsn(self) -> str:
        return (
            self.resolved_dsn.replace("+asyncpg", "+psycopg")
            .replace("+aiosqlite", "")
            .replace("+psycopg2", "+psycopg")
        )

    @computed_field(return_type=str)
    @property
    def driver_name(self) -> str:
        scheme = urlsplit(self.resolved_dsn).scheme or self.resolved_dsn.split("://", maxsplit=1)[0]
        return scheme.split("+", maxsplit=1)[0]

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
def get_database_config() -> DatabaseConfig:
    return load_section_settings("db", DatabaseConfig)
