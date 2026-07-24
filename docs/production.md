# Production Deployment

## Build

```bash
docker build -t neura-backend:latest .
```

## Required Environment

- `APP__ENV=production`
- `WEB__DOMAIN=example.com`
- `WEB__PUBLIC_BASE_URL=https://example.com`
- `LETSENCRYPT_EMAIL=ops@example.com`
- `DB__DSN=postgresql+asyncpg://...`
- `REDIS__DSN=redis://...`
- `S3__ENDPOINT_URL=https://...`
- `S3__ACCESS_KEY_ID=...`
- `S3__SECRET_ACCESS_KEY=...`
- `S3__BUCKET=...`
- `SECURITY__JWT_SECRET_KEY=...`
- `SECURITY__TOKEN_ENCRYPTION_KEY=...`
- `AI__PROVIDER=mock|openai|claude|gemini`

## Reverse Proxy And TLS

The production compose profile includes:

- `nginx` on ports `80` and `443`
- `certbot-init` to request the first Let's Encrypt certificate
- `certbot-renew` to renew certificates on a loop

`nginx` serves:

- `/` -> `frontend`
- `/api/*` -> `api`
- `/.well-known/acme-challenge/*` -> certbot webroot

Startup flow:

1. Point `WEB__DOMAIN` at the host with DNS.
2. Set `WEB__DOMAIN`, `WEB__PUBLIC_BASE_URL=https://<domain>`, and `LETSENCRYPT_EMAIL` in `.env`.
3. Start the stack:

```bash
docker compose --profile production up --build -d
```

On first boot `nginx` starts in HTTP mode so the ACME challenge can pass, `certbot-init` requests the certificate, and `nginx` reloads itself into HTTPS mode as soon as the cert files appear.

## Deploy Order

1. Apply migrations:

```bash
alembic upgrade head
```

2. Seed plans and bootstrap admin if needed:

```bash
BOOTSTRAP_ADMIN_EMAIL=admin@example.com \
BOOTSTRAP_ADMIN_PASSWORD='ChangeMe12345' \
python scripts/bootstrap_db.py
```

3. Start API:

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --proxy-headers
```

4. Start workers:

```bash
python -m arq backend.app.workers.llm_worker.WorkerSettings
python -m arq backend.app.workers.publisher_worker.WorkerSettings
python -m arq backend.app.workers.analytics_worker.WorkerSettings
python -m arq backend.app.workers.outbox_worker.WorkerSettings
```

## Healthchecks

- Liveness: `/api/v1/health/live`
- Readiness: `/api/v1/health/ready`
- Prometheus: `/metrics`

## Migration Strategy

- Use expand/contract migrations.
- Add nullable columns and dual-write first.
- Backfill in background.
- Switch reads.
- Remove legacy columns only in a later release.

## Scaling

- Scale API separately from workers.
- Scale `publisher_worker` horizontally only if platform rate limits are respected.
- Keep Redis persistence enabled for streams and rate-limit counters.
- Monitor `outbox_events`, `ai_jobs`, and `publication_attempts` tables for backlog growth.
