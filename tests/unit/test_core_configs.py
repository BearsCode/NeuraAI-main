from __future__ import annotations

import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.app.core.configs import Settings, load_section_settings
from backend.app.core.configs.sections import TelegramConfig
from backend.app.utils.env_file import EnvFilesResolver

NESTED_PREFIXES = (
    "APP__",
    "WEB__",
    "DB__",
    "REDIS__",
    "S3__",
    "SECURITY__",
    "OBSERVABILITY__",
    "WORKERS__",
    "AI__",
    "BILLING__",
    "TELEGRAM__",
    "MAX__",
    "SOCIAL__",
)

LEGACY_KEYS = {
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "AI_API_KEY",
    "AI_BASE_URL",
    "AI_MODEL",
    "AI_PROVIDER",
    "ALLOWED_ORIGINS",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_MODEL",
    "APP_DEBUG",
    "APP_ENV",
    "APP_HOST",
    "APP_NAME",
    "APP_PORT",
    "APP_VERSION",
    "DATABASE_URL",
    "DB_AUTO_CREATE_SCHEMA",
    "DB_ECHO",
    "DB_MAX_OVERFLOW",
    "DB_POOL_RECYCLE_SECONDS",
    "DB_POOL_SIZE",
    "DB_POOL_TIMEOUT_SECONDS",
    "DB_STATEMENT_TIMEOUT_MS",
    "DOCS_ENABLED",
    "DALLE_IMAGE_SIZE",
    "DALLE_MODEL",
    "LOCAL_STORAGE_PATH",
    "LOG_LEVEL",
    "MAX_ADMIN_IDS",
    "MAX_BOT_TOKEN",
    "MAX_UPLOAD_SIZE_MB",
    "MAX_WEBHOOK_URL",
    "OPENAPI_ENABLED",
    "OPENAI_API_KEY",
    "OPENAI_MODEL",
    "POSTGRES_DB",
    "POSTGRES_HOST",
    "POSTGRES_PASSWORD",
    "POSTGRES_PORT",
    "POSTGRES_USER",
    "POSTGRES_USERNAME",
    "PUBLIC_BASE_URL",
    "REDIS_HOST",
    "REDIS_PORT",
    "REDIS_URL",
    "REFRESH_TOKEN_EXPIRE_DAYS",
    "REQUEST_ID_HEADER",
    "S3_ACCESS_KEY",
    "S3_BUCKET_NAME",
    "S3_ENDPOINT_URL",
    "S3_PUBLIC_BASE_URL",
    "S3_REGION",
    "S3_SECRET_KEY",
    "SEED_ADMIN_ON_STARTUP",
    "STORAGE_BACKEND",
    "TELEGRAM_ADMIN_IDS",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_TYPE",
    "TELEGRAM_WEBHOOK_PATH",
    "TELEGRAM_WEBHOOK_URL",
    "TOKEN_ENCRYPTION_KEY",
    "WEB_DOMAIN",
    "WEB_LOGIN_ADMIN",
    "WEB_PASSWORD_ADMIN",
}


def _clear_config_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in list(os.environ):
        if key.startswith(NESTED_PREFIXES) or key in LEGACY_KEYS:
            monkeypatch.delenv(key, raising=False)


def test_settings_ignore_repo_dotenv_when_env_file_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_config_env(monkeypatch)

    settings = Settings(_env_file=None)

    assert settings.app.name == "Neura Backend"
    assert settings.db.dsn is None
    assert settings.database_url == "sqlite+aiosqlite:///./neuaraai.db"
    assert settings.database_uses_sqlite is True


def test_nested_settings_are_normalized_by_field_validators(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_config_env(monkeypatch)
    settings = Settings(
        _env_file=None,
        web={
            "api_v1_prefix": "api/v1",
            "public_base_url": "https://api.example.com/",
            "cors_origins": "https://a.example.com, https://b.example.com",
        },
        db={"dsn": "postgres://svc:secret@db:5432/neura"},
        redis={"host": "cache", "port": 6380},
        s3={
            "backend": "s3",
            "public_base_url": "https://cdn.example.com/",
            "allowed_upload_content_types": "image/png, image/jpeg, image/png",
        },
    )

    assert settings.web.api_v1_prefix == "/api/v1"
    assert settings.web.public_base_url == "https://api.example.com"
    assert settings.web.cors_origins == ["https://a.example.com", "https://b.example.com"]
    assert settings.db.dsn == "postgresql+asyncpg://svc:secret@db:5432/neura"
    assert settings.redis.dsn is None
    assert settings.redis_url == "redis://cache:6380/0"
    assert settings.s3.public_base_url == "https://cdn.example.com"
    assert settings.s3.allowed_upload_content_types == ["image/png", "image/jpeg"]


def test_legacy_env_mapping_resolves_to_structured_sections(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_config_env(monkeypatch)
    monkeypatch.setenv("APP_NAME", "Legacy Neura")
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://legacy.example.com/")
    monkeypatch.setenv("ALLOWED_ORIGINS", "[\"https://one.example.com\", \"https://two.example.com\"]")
    monkeypatch.setenv("DATABASE_URL", "postgres://legacy:secret@db:5432/legacy")
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    monkeypatch.setenv("AI_API_KEY", "test-key")
    monkeypatch.setenv("AI_MODEL", "claude-3-7-sonnet")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-key")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    monkeypatch.setenv("DALLE_MODEL", "dall-e-3")
    monkeypatch.setenv("DALLE_IMAGE_SIZE", "1024x1024")

    settings = Settings(_env_file=None)

    assert settings.app.name == "Legacy Neura"
    assert settings.web.public_base_url == "https://legacy.example.com"
    assert settings.web.cors_origins == ["https://one.example.com", "https://two.example.com"]
    assert settings.db.dsn == "postgresql+asyncpg://legacy:secret@db:5432/legacy"
    assert settings.ai.provider == "claude"
    assert settings.ai.claude.model == "claude-3-7-sonnet"
    assert settings.ai.claude.api_key is not None
    assert settings.openai_api_key == "openai-key"
    assert settings.openai_model == "gpt-4o-mini"
    assert settings.anthropic_api_key == "test-key"
    assert settings.anthropic_model == "claude-3-7-sonnet"
    assert settings.dalle_model == "dall-e-3"
    assert settings.dalle_image_size == "1024x1024"


def test_bot_config_supports_csv_and_json_admin_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_config_env(monkeypatch)
    settings = Settings(
        _env_file=None,
        telegram={"admin_ids": "1, 2, 3", "webhook_path": "webhook/telegram"},
        max={"admin_ids": "[10, 11]"},
    )

    assert settings.telegram.admin_ids == [1, 2, 3]
    assert settings.telegram.webhook_path == "/webhook/telegram"
    assert settings.max.admin_ids == [10, 11]


def test_load_section_settings_reads_single_category_env_file(tmp_path: Path) -> None:
    telegram_env = tmp_path / "110-telegram.env"
    telegram_env.write_text(
        "\n".join(
            [
                "TELEGRAM__BOT_TOKEN=123456:abcDEF_123",
                "TELEGRAM__BOT_TYPE=webhook",
                "TELEGRAM__WEBHOOK_URL=https://bot.example.com/telegram",
                "TELEGRAM__ADMIN_IDS=[1,2,3]",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    config = load_section_settings("telegram", TelegramConfig, env_file=(telegram_env,))

    assert config.enabled is True
    assert config.bot_type == "webhook"
    assert config.webhook_url == "https://bot.example.com/telegram"
    assert config.admin_ids == [1, 2, 3]


def test_telegram_webhook_mode_requires_webhook_url(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_config_env(monkeypatch)

    with pytest.raises(ValidationError, match="webhook_url is required"):
        Settings(
            _env_file=None,
            telegram={"bot_token": "123456:abcDEF_123", "bot_type": "webhook"},
        )


def test_billing_yookassa_credentials_must_be_paired(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_config_env(monkeypatch)

    with pytest.raises(ValidationError, match="yookassa.shop_id and yookassa.secret_key"):
        Settings(
            _env_file=None,
            billing={"yookassa": {"shop_id": 12345}},
        )


def test_production_settings_reject_sqlite(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_config_env(monkeypatch)
    monkeypatch.setenv("APP__ENV", "production")
    monkeypatch.setenv("DB__DSN", "sqlite+aiosqlite:///./prod.db")
    monkeypatch.setenv("S3__BACKEND", "s3")
    monkeypatch.setenv("S3__ENDPOINT_URL", "https://s3.example.com")
    monkeypatch.setenv("WEB__PUBLIC_BASE_URL", "https://api.example.com")
    monkeypatch.setenv("SECURITY__JWT_SECRET_KEY", "super-secret")
    monkeypatch.setenv("SECURITY__TOKEN_ENCRYPTION_KEY", "prod-encryption-key")

    with pytest.raises(ValidationError, match="SQLite is not allowed in production"):
        Settings(_env_file=None)


def test_production_settings_reject_mock_ai_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_config_env(monkeypatch)
    monkeypatch.setenv("APP__ENV", "production")
    monkeypatch.setenv("DB__DSN", "postgresql+asyncpg://svc:secret@db:5432/neura")
    monkeypatch.setenv("S3__BACKEND", "s3")
    monkeypatch.setenv("S3__ENDPOINT_URL", "https://s3.example.com")
    monkeypatch.setenv("WEB__PUBLIC_BASE_URL", "https://api.example.com")
    monkeypatch.setenv("SECURITY__JWT_SECRET_KEY", "super-secret")
    monkeypatch.setenv("SECURITY__TOKEN_ENCRYPTION_KEY", "prod-encryption-key")
    monkeypatch.setenv("AI__PROVIDER", "mock")

    with pytest.raises(ValidationError, match="AI__PROVIDER=mock is not allowed"):
        Settings(_env_file=None)


def test_production_settings_reject_mock_social_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_config_env(monkeypatch)
    monkeypatch.setenv("APP__ENV", "production")
    monkeypatch.setenv("DB__DSN", "postgresql+asyncpg://svc:secret@db:5432/neura")
    monkeypatch.setenv("S3__BACKEND", "s3")
    monkeypatch.setenv("S3__ENDPOINT_URL", "https://s3.example.com")
    monkeypatch.setenv("WEB__PUBLIC_BASE_URL", "https://api.example.com")
    monkeypatch.setenv("SECURITY__JWT_SECRET_KEY", "super-secret")
    monkeypatch.setenv("SECURITY__TOKEN_ENCRYPTION_KEY", "prod-encryption-key")
    monkeypatch.setenv("AI__PROVIDER", "openai")
    monkeypatch.setenv("AI__OPENAI__API_KEY", "real-openai-key")
    monkeypatch.setenv("AI__OPENAI__MODEL", "gpt-4o-mini")
    monkeypatch.setenv("SOCIAL__MODE", "mock")

    with pytest.raises(ValidationError, match="SOCIAL__MODE=mock is not allowed"):
        Settings(_env_file=None)


def test_production_settings_reject_gateway_ai_without_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_config_env(monkeypatch)
    monkeypatch.setenv("APP__ENV", "production")
    monkeypatch.setenv("DB__DSN", "postgresql+asyncpg://svc:secret@db:5432/neura")
    monkeypatch.setenv("S3__BACKEND", "s3")
    monkeypatch.setenv("S3__ENDPOINT_URL", "https://s3.example.com")
    monkeypatch.setenv("WEB__PUBLIC_BASE_URL", "https://api.example.com")
    monkeypatch.setenv("SECURITY__JWT_SECRET_KEY", "super-secret")
    monkeypatch.setenv("SECURITY__TOKEN_ENCRYPTION_KEY", "prod-encryption-key")
    monkeypatch.setenv("AI__PROVIDER", "gemini")
    monkeypatch.setenv("AI__GEMINI__API_KEY", "real-gemini-key")
    monkeypatch.setenv("SOCIAL__MODE", "live")

    with pytest.raises(ValidationError, match="Gateway AI providers require a base_url"):
        Settings(_env_file=None)


def test_settings_sections_are_immutable(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_config_env(monkeypatch)
    settings = Settings(_env_file=None)

    with pytest.raises(ValidationError, match="frozen"):
        settings.app.name = "Changed"  # type: ignore[misc]

    with pytest.raises(ValidationError, match="frozen"):
        settings.db.host = "db"  # type: ignore[misc]


def test_resolved_urls_and_masks_do_not_mutate_source_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_config_env(monkeypatch)
    settings = Settings(
        _env_file=None,
        app={"env": "development"},
        db={"host": "db", "database": "neura", "username": "svc", "password": "secret"},
        redis={"host": "cache", "username": "worker", "password": "redis-secret"},
    )

    assert settings.db.dsn is None
    assert settings.database_url == "postgresql+asyncpg://svc:secret@db:5432/neura"
    assert settings.database_masked_url == "postgresql+asyncpg://***:***@db:5432/neura"
    assert settings.redis.dsn is None
    assert settings.redis_url == "redis://worker:redis-secret@cache:6379/0"
    assert settings.redis_masked_url == "redis://***:***@cache:6379/0"


def test_redis_tls_detection_uses_scheme_not_suffix(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_config_env(monkeypatch)

    plain = Settings(_env_file=None, redis={"dsn": "redis://cache:6379/0"})
    tls = Settings(_env_file=None, redis={"dsn": "rediss://cache:6379/0"})

    assert plain.redis_uses_tls is False
    assert tls.redis_uses_tls is True


def test_settings_load_from_split_env_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_config_env(monkeypatch)

    app_env = tmp_path / "00-app.env"
    web_env = tmp_path / "10-web.env"
    db_env = tmp_path / "20-database.env"

    app_env.write_text("APP__NAME=Split Neura\nAPP__ENV=local\n", encoding="utf-8")
    web_env.write_text("WEB__PUBLIC_BASE_URL=https://split.example.com/\n", encoding="utf-8")
    db_env.write_text("DB__DSN=postgres://split:secret@db:5432/neura\n", encoding="utf-8")

    settings = Settings(_env_file=(app_env, web_env, db_env))

    assert settings.app.name == "Split Neura"
    assert settings.web.public_base_url == "https://split.example.com"
    assert settings.db.dsn == "postgresql+asyncpg://split:secret@db:5432/neura"


def test_env_files_resolver_uses_profile_directories(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_dir = tmp_path / "config" / "env" / "local"
    config_dir.mkdir(parents=True)
    env_file = config_dir / "00-app.env"
    env_file.write_text("APP__NAME=Resolved Neura\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='neura'\n", encoding="utf-8")

    monkeypatch.delenv("NEURA_ENV_FILES", raising=False)
    monkeypatch.setenv("NEURA_ENV_PROFILE", "local")

    resolver = EnvFilesResolver(start_path=tmp_path / "backend")

    assert resolver.resolve() == (env_file.resolve(),)
