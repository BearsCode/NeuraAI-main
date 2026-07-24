#!/usr/bin/env bash
# Generate production .env with secure random keys
set -euo pipefail

cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)"

JWT_SECRET=$(openssl rand -hex 64)
TOKEN_ENCRYPTION_KEY=$(openssl rand -hex 32)
ENCRYPT_KEY=$(openssl rand -hex 32)
DB_PASS=$(openssl rand -hex 16)
REDIS_PASS=$(openssl rand -hex 16)
MINIO_PASS=$(openssl rand -hex 16)
ADMIN_SECRET=$(openssl rand -hex 32)
ADMIN_MASTER_KEY=$(openssl rand -hex 32)
ADMIN_SALT=$(openssl rand -hex 16)
AI_API_KEY=$(openssl rand -hex 32)

cat > .env << ENVEOF
# =============================================================================
# NeuraAI Production Configuration
# Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)
# =============================================================================

# --- App ---------------------------------------------------------------------
APP__ENV=production
NEURA_ENV_PROFILE=production

# --- Web ---------------------------------------------------------------------
WEB__DOMAIN=neuara.ru
WEB__PUBLIC_BASE_URL=https://neuara.ru
WEB__DOCS_ENABLED=false

# --- Database ----------------------------------------------------------------
POSTGRES_DB=neuaraai
POSTGRES_USER=neura
POSTGRES_PASSWORD=${DB_PASS}
DB__DSN=postgresql+asyncpg://neura:${DB_PASS}@postgres:5432/neuaraai
DB__POOL_SIZE=20
DB__MAX_OVERFLOW=40
DB__POOL_TIMEOUT=30
DB__STATEMENT_TIMEOUT=30000
DB__RUN_MIGRATIONS_ON_STARTUP=true

# --- Redis -------------------------------------------------------------------
REDIS_PASSWORD=${REDIS_PASS}
REDIS__DSN=redis://:${REDIS_PASS}@redis:6379/0

# --- Storage (S3/Minio) ------------------------------------------------------
S3__BACKEND=s3
S3__ENDPOINT_URL=http://minio:9000
S3__ACCESS_KEY_ID=neura-minio
S3__SECRET_ACCESS_KEY=${MINIO_PASS}
S3__BUCKET=neuaraai-media
S3__PUBLIC_BASE_URL=https://neuara.ru/media
S3__USE_PATH_STYLE=true
S3__SIGNED_URL_TTL_SECONDS=3600
S3__MAX_FILE_SIZE_MB=50
MINIO_ROOT_USER=neura-minio
MINIO_ROOT_PASSWORD=${MINIO_PASS}
MINIO_API_PORT=9000
MINIO_CONSOLE_PORT=9001

# --- Security / JWT ----------------------------------------------------------
SECURITY__JWT_SECRET_KEY=${JWT_SECRET}
SECURITY__ACCESS_TOKEN_TTL_SECONDS=900
SECURITY__REFRESH_TOKEN_TTL_SECONDS=2592000
SECURITY__JWT_ALGORITHM=HS256
SECURITY__SEED_ADMIN_ON_STARTUP=false
SECURITY__TOKEN_ENCRYPTION_KEY=${TOKEN_ENCRYPTION_KEY}
ENCRYPTION__KEY=${ENCRYPT_KEY}
PASSWORD__MIN_LENGTH=8
PASSWORD__REQUIRE_UPPERCASE=true
PASSWORD__REQUIRE_DIGIT=true

# --- Admin -------------------------------------------------------------------
ADMIN__SUPER_ADMIN_EMAILS='["admin@neuara.ru"]'
ADMIN__ADMIN_SECRET_KEY=${ADMIN_SECRET}
ADMIN__ADMIN_SALT=${ADMIN_SALT}
ADMIN__MASTER_ENCRYPTION_KEY=${ADMIN_MASTER_KEY}

# --- Rate Limit --------------------------------------------------------------
RATE_LIMIT__ENABLED=true
RATE_LIMIT__DEFAULT_RATE=100/minute
RATE_LIMIT__STRICT_RATE=10/minute

# --- Observability -----------------------------------------------------------
OBSERVABILITY__METRICS_ENABLED=true
OBSERVABILITY__TRACES_ENABLED=false
OBSERVABILITY__LOG_LEVEL=INFO

# --- Workers -----------------------------------------------------------------
WORKER__CONCURRENCY=2
WORKER__MAX_BURST=10
WORKER__TIMEOUT_SECONDS=300

# --- AI ----------------------------------------------------------------------
AI__PROVIDER=openai
AI__OPENAI__API_KEY=${AI_API_KEY}
AI__OPENAI__BASE_URL=https://api.openai.com/v1
AI__OPENAI__MODEL=gpt-4o-mini

# --- Social ------------------------------------------------------------------
SOCIAL__MODE=live

# --- Billing -----------------------------------------------------------------
BILLING__PROVIDER=manual
BILLING__DEFAULT_CURRENCY=RUB

# --- Telegram ----------------------------------------------------------------
TELEGRAM__BOT_TOKEN=

# --- Social / OAuth ----------------------------------------------------------
OAUTH__VK__CLIENT_ID=
OAUTH__VK__CLIENT_SECRET=
OAUTH__YANDEX__CLIENT_ID=
OAUTH__YANDEX__CLIENT_SECRET=
OAUTH__MAILRU__CLIENT_ID=
OAUTH__MAILRU__CLIENT_SECRET=

# --- Email -------------------------------------------------------------------
EMAIL__PROVIDER=console
EMAIL__FROM=noreply@neuara.ru
EMAIL__SMTP__HOST=
EMAIL__SMTP__PORT=587
EMAIL__SMTP__USER=
EMAIL__SMTP__PASSWORD=

# --- Retail ------------------------------------------------------------------
RETAIL__PROVIDER=manual

# --- SSL / Certbot -----------------------------------------------------------
LETSENCRYPT_EMAIL=admin@neuara.ru
NGINX_HTTP_PORT=80
NGINX_HTTPS_PORT=443
CERTBOT_RENEW_INTERVAL_SECONDS=43200
ENVEOF

echo "=== .env generated ==="
echo "  JWT_SECRET=${JWT_SECRET:0:16}..."
echo "  DB_PASS=${DB_PASS:0:8}..."
echo "  MINIO_PASS=${MINIO_PASS:0:8}..."
