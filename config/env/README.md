# Environment Layout

The backend reads dotenv files by profile and category.

Resolution order:

1. `config/env/base/*.env`
2. `config/env/<profile>/*.env`
3. `.env`
4. `.env.local`

Profile resolution:

- `NEURA_ENV_PROFILE`
- `APP__ENV`
- `APP_ENV`
- fallback: `local`

Examples:

- Local runtime: `config/env/local/*.env`
- Production runtime: `config/env/production/*.env`
- Shared defaults: `config/env/base/*.env`

Notes:

- Files are split by backend concern: app, web, database, redis, storage, security, AI, workers, billing, and integrations.
- Legacy flat env names are still supported by the compatibility loader, but the canonical format is nested `SECTION__FIELD`.
- Deprecated legacy keys such as `QUEUE_BACKEND`, `OPENAI_API_TOKEN`, `CLAUDE_API_TOKEN`, `ADMIN_*`, and `TELEGRAM_BOT_PORT` are intentionally not part of the canonical backend config set.
