from __future__ import annotations

from celery import Celery

from backend.app.core.configs import settings

celery_app = Celery(
    "neura",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["backend.app.celery_tasks"],
)

celery_app.conf.update(
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    broker_transport_options={"visibility_timeout": 3600},
    result_expires=3600,
    timezone="UTC",
    beat_schedule={
        "ai-jobs-scan": {
            "task": "backend.app.celery_tasks.scan_pending_ai_jobs",
            "schedule": 60.0,
        },
        "anthropic-batch-scan": {
            "task": "backend.app.celery_tasks.scan_anthropic_batches",
            "schedule": 300.0,
        },
        "publication-scan": {
            "task": "backend.app.celery_tasks.scan_due_publications",
            "schedule": 300.0,
        },
        "outbox-flush": {
            "task": "backend.app.celery_tasks.publish_outbox",
            "schedule": 10.0,
        },
        "analytics-scan": {
            "task": "backend.app.celery_tasks.collect_analytics",
            "schedule": 3600.0,
        },
        "ceo-daily-briefing": {
            "task": "backend.app.celery_tasks.queue_ceo_daily_briefings",
            "schedule": 28800.0,
            "options": {"expires": 3600},
        },
        "ceo-weekly-report": {
            "task": "backend.app.celery_tasks.queue_ceo_weekly_reports",
            "schedule": 604800.0,
            "options": {"expires": 7200},
        },
    },
)
