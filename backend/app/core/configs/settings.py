from __future__ import annotations

from functools import lru_cache
from urllib.parse import urlsplit

from pydantic import Field, computed_field, model_validator

from backend.app.core.configs.base import RootSettings
from backend.app.core.configs.sections import (
    AdminConfig,
    AIConfig,
    AIProviderConfig,
    AppConfig,
    AvatarConfig,
    BillingConfig,
    DatabaseConfig,
    EmailConfig,
    MaxConfig,
    OAuthConfig,
    ObservabilityConfig,
    PasswordConfig,
    RateLimitConfig,
    RedisConfig,
    RetailConfig,
    S3Config,
    SecurityConfig,
    SocialConfig,
    TelegramConfig,
    WebConfig,
    WorkerConfig,
)


class Settings(RootSettings):
    """Root application settings composed from bounded configuration sections."""

    app: AppConfig = Field(default_factory=AppConfig)
    admin: AdminConfig = Field(default_factory=AdminConfig)
    web: WebConfig = Field(default_factory=WebConfig)
    db: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    s3: S3Config = Field(default_factory=S3Config)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)
    workers: WorkerConfig = Field(default_factory=WorkerConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    social: SocialConfig = Field(default_factory=SocialConfig)
    billing: BillingConfig = Field(default_factory=BillingConfig)
    email: EmailConfig = Field(default_factory=EmailConfig)
    password: PasswordConfig = Field(default_factory=PasswordConfig)
    avatar: AvatarConfig = Field(default_factory=AvatarConfig)
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    oauth: OAuthConfig = Field(default_factory=OAuthConfig)
    max: MaxConfig = Field(default_factory=MaxConfig)
    retail: RetailConfig = Field(default_factory=RetailConfig)

    @computed_field(return_type=bool)
    @property
    def is_production(self) -> bool:
        return self.app.is_production

    @property
    def active_ai_provider(self) -> AIProviderConfig | None:
        if self.ai.provider not in {"openai", "claude", "gemini"}:
            return None
        return getattr(self.ai, self.ai.provider)

    @model_validator(mode="after")
    def validate_runtime(self) -> "Settings":
        if self.is_production:
            if self.database_uses_sqlite:
                raise ValueError("SQLite is not allowed in production")
            if not self.s3.is_remote:
                raise ValueError("Production requires S3-compatible object storage")
            if self.security.seed_admin_on_startup:
                raise ValueError("SECURITY__SEED_ADMIN_ON_STARTUP must be False in production")
            if _is_placeholder_secret(self.security.jwt_secret_key.get_secret_value()):
                raise ValueError("SECURITY__JWT_SECRET_KEY must be explicitly configured in production")
            if _is_placeholder_secret(self.admin.admin_secret_key.get_secret_value()):
                raise ValueError("ADMIN__ADMIN_SECRET_KEY must be explicitly configured in production")
            if not self.admin.admin_salt.strip():
                raise ValueError("ADMIN__ADMIN_SALT must be explicitly configured in production")
            if _is_placeholder_secret(self.admin.master_encryption_key.get_secret_value()):
                raise ValueError("ADMIN__MASTER_ENCRYPTION_KEY must be explicitly configured in production")
            if any(email == "admin@example.com" for email in self.admin.super_admin_emails):
                raise ValueError("ADMIN__SUPER_ADMIN_EMAILS must not use the default 'admin@example.com'")
            if self.ai.provider == "mock":
                raise ValueError("AI__PROVIDER=mock is not allowed in production")
            if self.social.mode == "mock":
                raise ValueError("SOCIAL__MODE=mock is not allowed in production")
            if not self.ai.has_active_credentials:
                raise ValueError("Active AI provider credentials must be configured in production")
            active_ai_provider = self.active_ai_provider
            if (
                active_ai_provider is None
                or active_ai_provider.api_key is None
                or _is_placeholder_secret(active_ai_provider.api_key.get_secret_value())
            ):
                raise ValueError("Active AI provider API key must be configured with a non-placeholder value")
            if self.ai.provider not in {"openai", "claude"} and not active_ai_provider.base_url:
                raise ValueError("Gateway AI providers require a base_url in production")
            if _is_placeholder_secret(self.security.token_encryption_key.get_secret_value()):
                raise ValueError("SECURITY__TOKEN_ENCRYPTION_KEY must be rotated in production")
            if self.web.public_base_url.startswith("http://"):
                raise ValueError("WEB__PUBLIC_BASE_URL must use HTTPS in production")

        return self

    @property
    def public_base_url(self) -> str:
        return self.web.public_base_url

    @property
    def request_id_header(self) -> str:
        return self.web.request_id_header

    @property
    def app_name(self) -> str:
        return self.app.name

    @property
    def app_env(self) -> str:
        return self.app.env

    @property
    def api_v1_prefix(self) -> str:
        return self.web.api_v1_prefix

    @property
    def api_v2_prefix(self) -> str:
        return self.web.api_v2_prefix

    @property
    def docs_enabled(self) -> bool:
        return self.web.docs_enabled

    @property
    def allowed_origins(self) -> list[str]:
        return self.web.cors_origins

    @property
    def database_url(self) -> str:
        if self.db.dsn:
            return self.db.dsn
        if self.app.env == "local":
            return f"sqlite+aiosqlite:///{self.db.sqlite_path}"
        return self.db.resolved_dsn

    @property
    def database_sync_url(self) -> str:
        return _sync_database_url(self.database_url)

    @property
    def database_uses_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def database_driver_name(self) -> str:
        return _database_driver_name(self.database_url)

    @property
    def database_masked_url(self) -> str:
        return _mask_url_credentials(self.database_url)

    @property
    def redis_url(self) -> str:
        return self.redis.resolved_dsn

    @property
    def redis_uses_tls(self) -> bool:
        return self.redis_url.startswith("rediss://")

    @property
    def redis_masked_url(self) -> str:
        return _mask_url_credentials(self.redis_url)

    @property
    def queue_backend(self) -> str:
        return "redis"

    @property
    def storage_backend(self) -> str:
        return "s3" if self.s3.is_remote else "local"

    @property
    def local_storage_path(self) -> str:
        return self.s3.local_root

    @property
    def max_upload_size_bytes(self) -> int:
        return self.s3.max_upload_size_bytes

    @property
    def max_upload_size_mb(self) -> int:
        return self.s3.max_upload_size_mb

    @property
    def allowed_upload_content_types(self) -> list[str]:
        return self.s3.allowed_upload_content_types

    @property
    def s3_endpoint_url(self) -> str:
        return self.s3.endpoint_url

    @property
    def s3_access_key(self) -> str:
        return self.s3.access_key_id.get_secret_value() if self.s3.access_key_id else ""

    @property
    def s3_secret_key(self) -> str:
        return self.s3.secret_access_key.get_secret_value() if self.s3.secret_access_key else ""

    @property
    def s3_bucket_name(self) -> str:
        return self.s3.bucket

    @property
    def s3_region(self) -> str:
        return self.s3.region

    @property
    def s3_public_base_url(self) -> str:
        return self.s3.public_base_url

    @property
    def ai_provider(self) -> str:
        return self.ai.provider

    def _rotate_key(self, key_str: str) -> str:
        if not key_str:
            return ""
        keys = [k.strip() for k in key_str.split(",") if k.strip()]
        if not keys:
            return ""
        import random
        return random.choice(keys)

    @property
    def ai_api_key(self) -> str:
        credentials = self.active_ai_provider
        val = credentials.api_key.get_secret_value() if credentials and credentials.api_key else ""
        return self._rotate_key(val)

    @property
    def ai_model(self) -> str:
        credentials = self.active_ai_provider
        return credentials.model or "" if credentials else ""

    @property
    def openai_api_key(self) -> str:
        val = self.ai.openai.api_key.get_secret_value() if self.ai.openai.api_key else ""
        return self._rotate_key(val)

    @property
    def openai_model(self) -> str:
        return self.ai.openai.model or ""

    @property
    def anthropic_api_key(self) -> str:
        val = self.ai.claude.api_key.get_secret_value() if self.ai.claude.api_key else ""
        return self._rotate_key(val)

    @property
    def anthropic_model(self) -> str:
        return self.ai.claude.model or "claude-3-5-sonnet-20241022"

    @property
    def dalle_model(self) -> str:
        return self.ai.dalle_model or "dall-e-3"

    @property
    def dalle_image_size(self) -> str:
        return self.ai.dalle_image_size or "1024x1024"

    @property
    def jwt_secret_key(self) -> str:
        return self.security.jwt_secret_key.get_secret_value()

    @property
    def jwt_issuer(self) -> str:
        return self.security.jwt_issuer

    @property
    def jwt_audience(self) -> str:
        return self.security.jwt_audience

    @property
    def access_token_expire_minutes(self) -> int:
        return self.security.access_token_ttl_minutes

    @property
    def refresh_token_expire_days(self) -> int:
        return self.security.refresh_token_ttl_days


def _sync_database_url(value: str) -> str:
    return (
        value.replace("+asyncpg", "+psycopg")
        .replace("+aiosqlite", "")
        .replace("+psycopg2", "+psycopg")
    )


def _database_driver_name(value: str) -> str:
    scheme = urlsplit(value).scheme or value.split("://", maxsplit=1)[0]
    return scheme.split("+", maxsplit=1)[0]


def _mask_url_credentials(value: str) -> str:
    if "://" not in value:
        return value
    scheme, remainder = value.split("://", maxsplit=1)
    if "@" not in remainder:
        return value
    _, host_part = remainder.rsplit("@", maxsplit=1)
    return f"{scheme}://***:***@{host_part}"


def _is_placeholder_secret(value: str) -> bool:
    normalized = value.strip().lower()
    if not normalized:
        return True
    placeholders = {
        "change-me",
        "changeme",
        "secret",
        "replace-me",
        "replace_me",
        "placeholder",
        "example",
        "test",
    }
    if normalized in placeholders:
        return True
    return normalized.startswith(("change-me", "replace-me", "replace-with", "local-dev"))


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
