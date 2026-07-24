# Нейра Backend API

Backend-only карта API для SaaS-платформы «Нейра». Фронтенда здесь нет: только FastAPI, PostgreSQL/SQLite для локалки, Redis, S3/local storage, AI workers и интеграции.

## Версионирование

Активный контракт MVP: `/api/v1`.

`/api/v2` не включён в локальной конфигурации. Он нужен только тогда, когда появится новый несовместимый контракт API. Пока v2 нет, дублировать все ручки в Swagger непрофессионально: это создаёт шум и риск, что клиент случайно начнёт использовать несуществующую версию продукта.

Включить v2 можно явно:

```env
WEB__API_V2_PREFIX=/api/v2
```

## Основной Product Flow

Эти endpoints проще всего использовать для первого клиентского сценария из ТЗ.

| Раздел | Endpoint |
| --- | --- |
| Проверка рефералки | `GET /api/v1/registration/referral?code=...` |
| Запрос email-кода | `POST /api/v1/registration/email/request-code` |
| Подтверждение email | `POST /api/v1/registration/email/confirm` |
| Завершение регистрации | `POST /api/v1/registration/complete` |
| Статус регистрации | `GET /api/v1/registration/status` |
| Тарифы | `GET /api/v1/tariffs` |
| Dashboard клиента | `GET /api/v1/dashboard/user` |
| Запуск анализа бренда | `POST /api/v1/dashboard/brand-analysis` |
| Подключение соцсети | `POST /api/v1/social/connect` |
| Анализ соцсетей | `POST /api/v1/social/analyze` |
| Результат анализа соцсетей | `GET /api/v1/social/analysis` |
| Генерация контент-плана | `POST /api/v1/content/plan/generate` |
| Очередь Approval Center | `GET /api/v1/approval/posts` |
| Подтверждение поста | `POST /api/v1/approval/posts/{post_id}/approve` |
| Публикация | `POST /api/v1/publishing/trigger` |
| Аналитика | `GET /api/v1/analytics/summary` |

## Доменные API

Для production-логики используем модульные bounded-context endpoints.

| Модуль | Prefix | Назначение |
| --- | --- | --- |
| Identity | `/api/v1/identity` | регистрация, login, refresh, profile, password |
| Onboarding | `/api/v1/onboarding` | анкета бизнеса, tenant/project, AI analysis job |
| Dashboard | `/api/v1/dashboard` | агрегированное состояние проекта |
| Social Integration | `/api/v1/social` | подключения Telegram, VK, Instagram, Threads, TikTok, YouTube, WhatsApp Business, MAX |
| Content Plan | `/api/v1/content-plans` | контент-планы, посты, версии |
| Approval Center | `/api/v1/approval` | ручной/авто режим, approve/reject/reschedule |
| Publishing | `/api/v1/publishing` | очередь публикаций, saga, retry, история |
| Analytics | `/api/v1/analytics` | охваты, ER, CTR, рост аудитории |
| AI Optimization | `/api/v1/ai-optimization` | недельная оптимизация стратегии |
| Billing | `/api/v1/billing` | тарифы, подписки, платежи, комиссии |
| Files | `/api/v1/files` | S3/local файлы и подписанные URL |
| Admin | `/api/v1/admin` | пользователи, тарифы, подписки, партнёры, статистика |

## AI контур

AI в backend разделён на понятные задачи:

- `business_analysis`: анализ компании, рынка, конкурентов и позиционирования.
- `strategy_generation`: стратегия, рубрики, каналы, частота публикаций.
- `content_plan_generation`: план публикаций на период.
- `post_generation`: текст/медиа-черновики для конкретной площадки.
- `social_channel_analysis`: анализ подключённых соцсетей.
- `weekly_optimization`: корректировка рубрик, времени, частоты и типов контента.

Запросы к LLM не должны выполняться внутри HTTP request долго и блокирующе. HTTP создаёт `AIJob` и outbox event, дальше задачу забирает worker.

## Swagger Authorize

Локальный Swagger: `http://127.0.0.1:8000/docs`.

Для кнопки `Authorize`:

```text
username: admin@neuaraai.dev
password: LocalAdmin12345
```

`client_id`, `client_secret`, `scopes` оставить пустыми.
