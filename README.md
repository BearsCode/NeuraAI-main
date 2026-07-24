# Neura Backend

Production-oriented backend scaffold for the Neura AI B2B marketing platform.

## Stack

- Python 3.12+
- FastAPI + Pydantic v2
- SQLAlchemy 2.0 async
- PostgreSQL 15+ with partitioned tables and full-text indexes
- Redis for cache, rate limiting, streams, and worker coordination
- MinIO/S3 for assets
- arq workers for AI jobs, publishing, analytics, and outbox delivery
- structlog + OpenTelemetry + Prometheus

## Configuration

- Canonical env layout is section-based: `APP__...`, `WEB__...`, `DB__...`, `REDIS__...`, `S3__...`, `SECURITY__...`, `AI__...`.
- Canonical env storage is split by category under `config/env/<profile>/*.env`.
- Local development defaults live in `config/env/local/*.env`.
- Template files live in `config/env/example/*.env.example`.
- Legacy flat keys from the old bootstrap layer are still accepted for backward compatibility in local/dev environments.

## Bounded Contexts

- `identity`
- `business_onboarding`
- `social_integration`
- `content_plan`
- `approval_center`
- `publishing`
- `analytics`
- `ai_optimization`
- `billing`
- `admin`
- `files`
- `dashboard`

## Local Run

### Direct app run

1. Use the committed local `.env` for SQLite, local storage and mock AI, or override it with `.env.local`.
2. Seed plans, AI prompts and the local admin:

```bash
python scripts/bootstrap_db.py
```

3. Run the API directly:

```bash
uvicorn backend.app.main:app --reload
```

### Docker Compose

`docker compose up --build` starts the full local stack on PostgreSQL, Redis and MinIO. This is the recommended containerized mode because the compose stack includes multiple backend processes and workers.

```bash
docker compose up --build
```

The frontend is included in the default stack and is published on `http://localhost:3000`. Inside Docker it talks to the backend over the internal compose network.

If you specifically want SQLite inside Docker, use the dedicated API-only profile together with the SQLite frontend:

```bash
APP_PORT=8010 FRONTEND_PORT=3010 docker compose --profile sqlite up --build frontend-sqlite api-sqlite redis minio create-bucket
```

The SQLite profile intentionally does not start the ARQ workers. Sharing one SQLite database file across several long-lived containers is fragile and not a good default.

For production ingress, the compose stack now includes an `nginx` + Let's Encrypt flow behind the `production` profile. Set `WEB__DOMAIN`, `WEB__PUBLIC_BASE_URL=https://<your-domain>`, and `LETSENCRYPT_EMAIL` in `.env`, point DNS at the host, then start with:

```bash
docker compose --profile production up --build -d
```

`nginx` serves the frontend at `/`, proxies the backend at `/api`, answers the ACME challenge on port 80, and switches itself to HTTPS once the first certificate is issued.

### Open

- Frontend: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`
- Liveness: `http://localhost:8000/api/v1/health/live`
- Readiness: `http://localhost:8000/api/v1/health/ready`
- MinIO console: `http://localhost:9001`
- Swagger login: `admin@neuaraai.dev` / `LocalAdmin12345`

## Manual Runtime

```bash
pip install -e .[test]
alembic upgrade head
python scripts/bootstrap_db.py
uvicorn backend.app.main:app --reload
python -m arq backend.app.workers.llm_worker.WorkerSettings
python -m arq backend.app.workers.publisher_worker.WorkerSettings
python -m arq backend.app.workers.analytics_worker.WorkerSettings
python -m arq backend.app.workers.outbox_worker.WorkerSettings
```

## Production Notes

- Use managed PostgreSQL and Redis.
- Keep `DB__RUN_MIGRATIONS_ON_STARTUP=false`; run Alembic explicitly in deploy pipeline.
- Replace `AI__PROVIDER=mock` with a gateway-backed provider config.
- Rotate `SECURITY__JWT_SECRET_KEY` and `SECURITY__TOKEN_ENCRYPTION_KEY`.
- Store `.env` in a secret manager, not in the image.
- Scale `api` and worker groups independently.

See [docs/backend-api-map.md](docs/backend-api-map.md) for the clean backend API map, [docs/production.md](docs/production.md) for deployment details, [docs/curl-examples.md](docs/curl-examples.md) for bounded-context API checks, and [docs/mvp-api.md](docs/mvp-api.md) for MVP-compatible product-flow routes.
