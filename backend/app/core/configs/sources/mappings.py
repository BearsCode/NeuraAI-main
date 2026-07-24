from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LegacyEnvMapping:
    path: tuple[str, ...]
    keys: tuple[str, ...]


APP_ENV_MAPPINGS = (
    LegacyEnvMapping(("app", "env"), ("APP_ENV",)),
    LegacyEnvMapping(("app", "debug"), ("APP_DEBUG",)),
    LegacyEnvMapping(("app", "host"), ("APP_HOST",)),
    LegacyEnvMapping(("app", "name"), ("APP_NAME",)),
    LegacyEnvMapping(("app", "port"), ("APP_PORT",)),
    LegacyEnvMapping(("app", "version"), ("APP_VERSION",)),
    LegacyEnvMapping(("app", "default_timezone"), ("APP_DEFAULT_TIMEZONE",)),
)

WEB_ENV_MAPPINGS = (
    LegacyEnvMapping(("web", "api_v1_prefix"), ("API_V1_PREFIX", "APP__API_V1_PREFIX")),
    LegacyEnvMapping(("web", "api_v2_prefix"), ("API_V2_PREFIX", "APP__API_V2_PREFIX")),
    LegacyEnvMapping(("web", "cors_origins"), ("ALLOWED_ORIGINS", "APP__CORS_ORIGINS")),
    LegacyEnvMapping(("web", "public_base_url"), ("PUBLIC_BASE_URL", "APP__PUBLIC_BASE_URL")),
    LegacyEnvMapping(("web", "docs_enabled"), ("DOCS_ENABLED", "APP__DOCS_ENABLED")),
    LegacyEnvMapping(("web", "openapi_enabled"), ("OPENAPI_ENABLED", "APP__OPENAPI_ENABLED")),
    LegacyEnvMapping(("web", "request_id_header"), ("REQUEST_ID_HEADER", "APP__REQUEST_ID_HEADER")),
    LegacyEnvMapping(("web", "domain"), ("WEB_DOMAIN",)),
    LegacyEnvMapping(("web", "admin_login"), ("WEB_LOGIN_ADMIN",)),
    LegacyEnvMapping(("web", "admin_password"), ("WEB_PASSWORD_ADMIN",)),
)

DATABASE_ENV_MAPPINGS = (
    LegacyEnvMapping(("db", "dsn"), ("DATABASE_URL",)),
    LegacyEnvMapping(("db", "echo"), ("DB_ECHO",)),
    LegacyEnvMapping(("db", "run_migrations_on_startup"), ("DB_AUTO_CREATE_SCHEMA",)),
    LegacyEnvMapping(("db", "pool_size"), ("DB_POOL_SIZE",)),
    LegacyEnvMapping(("db", "max_overflow"), ("DB_MAX_OVERFLOW",)),
    LegacyEnvMapping(("db", "pool_timeout_seconds"), ("DB_POOL_TIMEOUT_SECONDS",)),
    LegacyEnvMapping(("db", "pool_recycle_seconds"), ("DB_POOL_RECYCLE_SECONDS",)),
    LegacyEnvMapping(("db", "statement_timeout_ms"), ("DB_STATEMENT_TIMEOUT_MS",)),
    LegacyEnvMapping(("db", "host"), ("POSTGRES_HOST",)),
    LegacyEnvMapping(("db", "port"), ("POSTGRES_PORT",)),
    LegacyEnvMapping(("db", "database"), ("POSTGRES_DB",)),
    LegacyEnvMapping(("db", "username"), ("POSTGRES_USERNAME", "POSTGRES_USER")),
    LegacyEnvMapping(("db", "password"), ("POSTGRES_PASSWORD",)),
)

REDIS_ENV_MAPPINGS = (
    LegacyEnvMapping(("redis", "dsn"), ("REDIS_URL",)),
    LegacyEnvMapping(("redis", "host"), ("REDIS_HOST",)),
    LegacyEnvMapping(("redis", "port"), ("REDIS_PORT",)),
)

S3_ENV_MAPPINGS = (
    LegacyEnvMapping(("s3", "backend"), ("STORAGE_BACKEND",)),
    LegacyEnvMapping(("s3", "local_root"), ("LOCAL_STORAGE_PATH",)),
    LegacyEnvMapping(("s3", "max_upload_size_mb"), ("MAX_UPLOAD_SIZE_MB",)),
    LegacyEnvMapping(("s3", "allowed_upload_content_types"), ("ALLOWED_UPLOAD_CONTENT_TYPES",)),
    LegacyEnvMapping(("s3", "endpoint_url"), ("S3_ENDPOINT_URL",)),
    LegacyEnvMapping(("s3", "access_key_id"), ("S3_ACCESS_KEY",)),
    LegacyEnvMapping(("s3", "secret_access_key"), ("S3_SECRET_KEY",)),
    LegacyEnvMapping(("s3", "bucket"), ("S3_BUCKET_NAME",)),
    LegacyEnvMapping(("s3", "region"), ("S3_REGION",)),
    LegacyEnvMapping(("s3", "public_base_url"), ("S3_PUBLIC_BASE_URL",)),
)

SECURITY_ENV_MAPPINGS = (
    LegacyEnvMapping(("security", "jwt_secret_key"), ("JWT_SECRET_KEY",)),
    LegacyEnvMapping(("security", "jwt_issuer"), ("JWT_ISSUER",)),
    LegacyEnvMapping(("security", "jwt_audience"), ("JWT_AUDIENCE",)),
    LegacyEnvMapping(("security", "access_token_ttl_minutes"), ("ACCESS_TOKEN_EXPIRE_MINUTES",)),
    LegacyEnvMapping(("security", "refresh_token_ttl_days"), ("REFRESH_TOKEN_EXPIRE_DAYS",)),
    LegacyEnvMapping(("security", "token_encryption_key"), ("TOKEN_ENCRYPTION_KEY",)),
    LegacyEnvMapping(("security", "seed_admin_on_startup"), ("SEED_ADMIN_ON_STARTUP",)),
)

OBSERVABILITY_ENV_MAPPINGS = (
    LegacyEnvMapping(("observability", "log_level"), ("LOG_LEVEL",)),
    LegacyEnvMapping(("observability", "log_json"), ("LOG_JSON",)),
    LegacyEnvMapping(("observability", "service_name"), ("SERVICE_NAME",)),
    LegacyEnvMapping(("observability", "otlp_endpoint"), ("OTLP_ENDPOINT",)),
    LegacyEnvMapping(("observability", "metrics_enabled"), ("METRICS_ENABLED",)),
    LegacyEnvMapping(("observability", "traces_enabled"), ("TRACES_ENABLED",)),
)

AI_ENV_MAPPINGS = (
    LegacyEnvMapping(("ai", "openai", "api_key"), ("OPENAI_API_KEY",)),
    LegacyEnvMapping(("ai", "openai", "model"), ("OPENAI_MODEL",)),
    LegacyEnvMapping(("ai", "claude", "api_key"), ("ANTHROPIC_API_KEY",)),
    LegacyEnvMapping(("ai", "claude", "model"), ("ANTHROPIC_MODEL",)),
    LegacyEnvMapping(("ai", "dalle_model"), ("DALLE_MODEL",)),
    LegacyEnvMapping(("ai", "dalle_image_size"), ("DALLE_IMAGE_SIZE",)),
)

TELEGRAM_ENV_MAPPINGS = (
    LegacyEnvMapping(("telegram", "bot_token"), ("TELEGRAM_BOT_TOKEN",)),
    LegacyEnvMapping(("telegram", "admin_ids"), ("TELEGRAM_ADMIN_IDS",)),
    LegacyEnvMapping(("telegram", "webhook_url"), ("TELEGRAM_WEBHOOK_URL",)),
    LegacyEnvMapping(("telegram", "bot_type"), ("TELEGRAM_TYPE",)),
    LegacyEnvMapping(("telegram", "webhook_path"), ("TELEGRAM_WEBHOOK_PATH",)),
)

MAX_ENV_MAPPINGS = (
    LegacyEnvMapping(("max", "bot_token"), ("MAX_BOT_TOKEN",)),
    LegacyEnvMapping(("max", "admin_ids"), ("MAX_ADMIN_IDS",)),
    LegacyEnvMapping(("max", "webhook_url"), ("MAX_WEBHOOK_URL",)),
)

LEGACY_ENV_MAPPINGS = (
    *APP_ENV_MAPPINGS,
    *WEB_ENV_MAPPINGS,
    *DATABASE_ENV_MAPPINGS,
    *REDIS_ENV_MAPPINGS,
    *S3_ENV_MAPPINGS,
    *SECURITY_ENV_MAPPINGS,
    *OBSERVABILITY_ENV_MAPPINGS,
    *AI_ENV_MAPPINGS,
    *TELEGRAM_ENV_MAPPINGS,
    *MAX_ENV_MAPPINGS,
)


def ai_provider_env_mappings(provider: str) -> tuple[LegacyEnvMapping, ...]:
    if provider not in {"openai", "claude", "gemini"}:
        return ()
    return (
        LegacyEnvMapping(("ai", provider, "api_key"), ("AI_API_KEY",)),
        LegacyEnvMapping(("ai", provider, "model"), ("AI_MODEL",)),
        LegacyEnvMapping(("ai", provider, "base_url"), ("AI_BASE_URL",)),
    )
