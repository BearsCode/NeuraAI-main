from __future__ import annotations

import asyncio
from typing import Any

import httpx
from celery import Task
from redis.asyncio import Redis
from sqlalchemy import select

from backend.app.celery_app import celery_app
from backend.app.core.database import get_session_factory
from backend.app.core.configs import settings
from backend.app.db.ai_job import AIJob
from backend.app.db.enums import AIJobStatus, StrategyStatus
from backend.app.db.project import Project
from backend.app.events.bus import RedisEventBus
from backend.app.integrations.ai_adapters import build_ai_adapter
from backend.app.integrations.social_adapters import SocialAdapterRegistry
from backend.app.workers.analytics_worker import collect_due_analytics
from backend.app.workers.llm_worker import process_ai_job, process_pending_ai_jobs, scan_pending_anthropic_batches
from backend.app.workers.outbox_worker import flush_outbox
from backend.app.workers.publisher_worker import process_due_publications, process_publication


def _run_worker_operation(operation: Any) -> Any:
    return asyncio.run(_run_with_context(operation))


async def _run_with_context(operation: Any) -> Any:
    redis = Redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )
    ctx = _worker_context(redis)
    try:
        return await operation(ctx)
    finally:
        await redis.aclose()


def _worker_context(redis: Redis) -> dict[str, Any]:
    return {
        "redis": redis,
        "session_factory": get_session_factory(),
        "event_bus": RedisEventBus(redis),
        "ai_adapter": build_ai_adapter(),
        "social_registry": SocialAdapterRegistry(),
        "platform_semaphores": {
            "telegram": asyncio.Semaphore(max(1, settings.social.telegram.rate_limit_per_minute // 30)),
            "vk": asyncio.Semaphore(max(1, settings.social.vk.rate_limit_per_minute // 30)),
        },
    }


class ResilientTask(Task):
    autoretry_for = (httpx.TimeoutException, httpx.HTTPStatusError, RuntimeError, TimeoutError)
    retry_backoff = True
    retry_backoff_max = 60
    retry_jitter = True
    retry_kwargs = {"max_retries": 3}


@celery_app.task(name="backend.app.celery_tasks.process_ai_job", bind=True, base=ResilientTask)
def process_ai_job_task(self: ResilientTask, job_id: str) -> str:
    del self
    return _run_worker_operation(
        lambda ctx: process_ai_job(
            {
                **ctx,
                "propagate_retryable_errors": True,
            },
            job_id,
        )
    )


@celery_app.task(name="backend.app.celery_tasks.scan_pending_ai_jobs")
def scan_pending_ai_jobs() -> int:
    return int(_run_worker_operation(process_pending_ai_jobs))


@celery_app.task(name="backend.app.celery_tasks.scan_anthropic_batches")
def scan_anthropic_batches() -> int:
    return int(_run_worker_operation(scan_pending_anthropic_batches))


@celery_app.task(name="backend.app.celery_tasks.process_publication", bind=True, base=ResilientTask)
def process_publication_task(self: ResilientTask, publication_id: str) -> str:
    del self
    return _run_worker_operation(lambda ctx: process_publication(ctx, publication_id))


@celery_app.task(name="backend.app.celery_tasks.scan_due_publications")
def scan_due_publications() -> int:
    return int(_run_worker_operation(process_due_publications))


@celery_app.task(name="backend.app.celery_tasks.publish_outbox")
def publish_outbox() -> int:
    return int(_run_worker_operation(flush_outbox))


@celery_app.task(name="backend.app.celery_tasks.collect_analytics")
def collect_analytics() -> int:
    return int(_run_worker_operation(collect_due_analytics))


@celery_app.task(name="backend.app.celery_tasks.process_video_subtitles", bind=True, base=ResilientTask)
def process_video_subtitles(
    self: ResilientTask,
    video_url: str,
    project_id: str,
) -> str:
    del self
    from backend.app.services.video_processing_service import video_processing
    result = asyncio.run(_async_generate_subtitles(video_processing, video_url, project_id))
    return result


_CEO_SYSTEM_PROMPT = (
    "Ты — CEO Agent платформы Нейра.\n"
    "Сделай анализ для владельца бизнеса и сформулируй стратегические рекомендации."
)

_CEO_DAILY_USER_PROMPT = (
    "Сформируй ежедневный брифинг на основе текущих метрик и активностей.\n"
    "Метрики: {metrics}\n"
    "Активные публикации: {publications}\n"
    "Сформулируй краткую выжимку (что хорошо, что плохо) и стратегический совет."
)

_CEO_WEEKLY_USER_PROMPT = (
    "Сформируй еженедельный отчёт на основе метрик за неделю и выполненных активностей.\n"
    "Метрики: {metrics}\n"
    "Выполненный контент-план: {publications}\n"
    "Сформулируй развёрнутый анализ, инсайты и стратегические рекомендации на следующую неделю."
)

_CEO_RESPONSE_SCHEMA = {
    "briefing": "string",
    "insights": ["string"],
    "strategy_recommendation": "string",
}


async def _queue_ceo_jobs(job_type: str, user_prompt_template: str) -> int:
    session_factory = get_session_factory()
    async with session_factory() as session:
        projects = (
            await session.scalars(
                select(Project).where(
                    Project.strategy_status == StrategyStatus.ACTIVE,
                )
            )
        ).all()

        queued = 0
        for project in projects:
            analytics = _gather_project_metrics(session, project.id)
            input_payload = {
                "system_prompt": _CEO_SYSTEM_PROMPT,
                "user_prompt": user_prompt_template.format(
                    metrics=analytics.get("metrics", "{}"),
                    publications=analytics.get("publications", "[]"),
                ),
                "response_schema": _CEO_RESPONSE_SCHEMA,
            }
            session.add(
                AIJob(
                    tenant_id=project.tenant_id,
                    project_id=project.id,
                    job_type=job_type,
                    provider="queued",
                    model="queued",
                    status=AIJobStatus.PENDING,
                    input_payload=input_payload,
                )
            )
            queued += 1

        await session.commit()
    return queued


def _gather_project_metrics(session, project_id: str) -> dict:
    return {
        "metrics": f"project_id={project_id}",
        "publications": "[]",
    }


@celery_app.task(name="backend.app.celery_tasks.queue_ceo_daily_briefings")
def queue_ceo_daily_briefings() -> int:
    return int(
        asyncio.run(_queue_ceo_jobs("ceo_daily_briefing", _CEO_DAILY_USER_PROMPT))
    )


@celery_app.task(name="backend.app.celery_tasks.queue_ceo_weekly_reports")
def queue_ceo_weekly_reports() -> int:
    return int(
        asyncio.run(_queue_ceo_jobs("ceo_weekly_report", _CEO_WEEKLY_USER_PROMPT))
    )


async def _async_generate_subtitles(
    vp: Any, video_url: str, project_id: str
) -> str:
    subtitles = await vp.generate_subtitles(video_url)
    if not subtitles:
        return video_url
    processed_url = await vp.burn_subtitles(video_url, subtitles)
    if processed_url != video_url:
        from backend.app.integrations.storage_client import StorageClient
        sc = StorageClient()
        _, result_url = await sc.store_bytes(
            project_id=project_id,
            file_name=f"videos/subtitled/{video_url.rsplit('/', 1)[-1] or 'output.mp4'}",
            content_type="video/mp4",
            data=b"",
        )
        return result_url or processed_url
    return processed_url
