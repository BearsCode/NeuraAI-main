from __future__ import annotations

from datetime import UTC, datetime

import httpx
from arq import cron
from sqlalchemy import select

from backend.app.core.configs import settings
from backend.app.db.ai_expert_prompt import AIExpertPrompt
from backend.app.db.ai_job import AIJob
from backend.app.db.enums import AIJobStatus, StrategyStatus
from backend.app.db.optimization_recommendation import OptimizationRecommendation
from backend.app.db.project import Project
from backend.app.db.project_strategy import ProjectStrategy
from backend.app.integrations.ai_adapters import AIGenerateRequest
from backend.app.infra.retry import async_retry
from backend.app.services.ai_orchestration_service import AIOrchestrationService
from backend.app.workers.common import WorkerContext, build_redis_settings, shutdown, startup


async def process_pending_ai_jobs(ctx: WorkerContext) -> int:
    session_factory = ctx["session_factory"]
    async with session_factory() as session:
        jobs = (
            await session.scalars(
                select(AIJob)
                .where(
                    AIJob.status == AIJobStatus.PENDING,
                    (AIJob.scheduled_for.is_(None) | (AIJob.scheduled_for <= datetime.now(UTC))),
                )
                .order_by(AIJob.created_at)
                .limit(25)
            )
        ).all()

    processed = 0
    for job in jobs:
        await process_ai_job(ctx, job.id)
        processed += 1
    return processed


async def process_ai_job(ctx: WorkerContext, job_id: str) -> str:
    session_factory = ctx["session_factory"]
    adapter = ctx["ai_adapter"]
    orchestration = AIOrchestrationService()
    propagate_retryable_errors = bool(ctx.get("propagate_retryable_errors"))
    async with session_factory() as session:
        job = await session.get(AIJob, job_id)
        if not job or job.status not in {AIJobStatus.PENDING, AIJobStatus.RUNNING}:
            return "skipped"

        job.status = AIJobStatus.RUNNING
        await session.commit()

        try:
            project = await session.get(Project, job.project_id) if job.project_id else None
            if job.job_type == "strategy_generation" and project is not None:
                strategy = await async_retry(
                    lambda: orchestration.generate_strategy(session, project),
                    retries=3,
                    base_delay_seconds=1.0,
                    max_delay_seconds=8.0,
                )
                project.strategy_status = StrategyStatus.ACTIVE
                job.output_payload = {
                    "project_id": project.id,
                    "strategy_id": strategy.id,
                    "status": "generated",
                }
                job.status = AIJobStatus.SUCCEEDED
                job.error_message = None
                await session.commit()
                return "processed"

            expert_prompt = await _load_expert_prompt(session, project)
            result = await adapter.generate(
                AIGenerateRequest(
                    task_type=job.job_type,
                    context={
                        "tenant_id": job.tenant_id,
                        "project_id": job.project_id,
                        "company_name": project.company_name if project else None,
                        "industry": project.industry if project else None,
                        "target_audience": project.target_audience if project else None,
                        "channels": project.social_links if project else [],
                        "system_prompt": expert_prompt,
                        **job.input_payload,
                    },
                )
            )
            await _apply_ai_result(session, job, project, result)
            job.status = AIJobStatus.SUCCEEDED
            job.output_payload = result
            job.error_message = None
            await session.commit()
            return "processed"
        except Exception as exc:  # noqa: BLE001
            if propagate_retryable_errors and _is_retryable_ai_error(exc):
                job.status = AIJobStatus.RUNNING
                job.error_message = str(exc)
                await session.commit()
                raise
            job.status = AIJobStatus.FAILED
            job.error_message = str(exc)
            await session.commit()
            return "failed"


async def _load_expert_prompt(session, project: Project | None) -> dict | None:
    if project is None or not project.industry:
        return None

    prompt = await session.scalar(
        select(AIExpertPrompt).where(
            AIExpertPrompt.niche == project.industry.lower(),
            AIExpertPrompt.is_active.is_(True),
        )
    )
    if prompt is None:
        return None
    return {
        "niche": prompt.niche,
        "role_description": prompt.role_description,
        "tone": prompt.tone,
        "additional_instructions": prompt.additional_instructions,
    }


async def _apply_ai_result(
    session,
    job: AIJob,
    project: Project | None,
    result: dict,
) -> None:
    if job.job_type in ("ceo_daily_briefing", "ceo_weekly_report"):
        job.output_payload = result
        return

    if "optimization" in job.job_type:
        recommendation_id = job.input_payload.get("recommendation_id")
        if recommendation_id:
            recommendation = await session.get(OptimizationRecommendation, recommendation_id)
            if recommendation is not None:
                recommendation.summary = str(result.get("summary", recommendation.summary))
                recommendation.details = result.get("details", recommendation.details)
                recommendation.suggested_publish_time = result.get("suggested_publish_time")
                recommendation.suggested_frequency = result.get("suggested_frequency")
        return

    if project is None:
        return

    strategy = await session.scalar(select(ProjectStrategy).where(ProjectStrategy.project_id == project.id))
    if strategy is None:
        strategy = ProjectStrategy(
            tenant_id=project.tenant_id,
            project_id=project.id,
        )
        session.add(strategy)

    strategy.business_analysis = list(result.get("business_analysis", strategy.business_analysis))
    strategy.market_analysis = list(result.get("market_analysis", strategy.market_analysis))
    strategy.competitor_analysis = list(result.get("competitor_analysis", strategy.competitor_analysis))
    strategy.positioning = str(result.get("positioning", strategy.positioning))
    strategy.content_pillars = list(result.get("content_pillars", strategy.content_pillars))
    strategy.channels = list(result.get("channels", strategy.channels))
    strategy.publishing_frequency = str(result.get("publishing_frequency", strategy.publishing_frequency))
    strategy.recommendations = list(result.get("recommendations", strategy.recommendations))
    strategy.optimization_mode = str(result.get("optimization_mode", strategy.optimization_mode))
    project.strategy_status = StrategyStatus.ACTIVE


def _is_retryable_ai_error(exc: Exception) -> bool:
    """Return True when Celery should retry an external LLM failure."""

    if isinstance(exc, (httpx.TimeoutException, TimeoutError)):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code
        return status_code == 429 or 500 <= status_code < 600
    return isinstance(exc, RuntimeError) and "Circuit breaker is open" in str(exc)


class WorkerSettings:
    functions = [process_ai_job]
    cron_jobs = [cron(process_pending_ai_jobs, second={0, 15, 30, 45}, run_at_startup=True)]
    on_startup = startup
    on_shutdown = shutdown
    queue_name = settings.workers.llm_queue_name
    redis_settings = build_redis_settings()
    health_check_key = f"{settings.workers.llm_queue_name}:health"
    job_timeout = settings.ai.request_timeout_seconds + 30

import json

async def scan_pending_anthropic_batches(ctx: WorkerContext) -> int:
    session_factory = ctx["session_factory"]
    api_key = getattr(settings, "anthropic_api_key", None)
    
    if not api_key and hasattr(settings, "ai") and hasattr(settings.ai, "claude"):
        claude = getattr(settings.ai, "claude")
        if getattr(claude, "api_key", None):
            api_key = claude.api_key.get_secret_value()
            
    if not api_key:
        return 0

    async with session_factory() as session:
        jobs = (
            await session.scalars(
                select(AIJob)
                .where(
                    AIJob.status == AIJobStatus.RUNNING,
                    AIJob.job_type == "anthropic_batch",
                )
                .limit(25)
            )
        ).all()

    if not jobs:
        return 0

    processed = 0
    async with httpx.AsyncClient(timeout=30.0) as client:
        for job in jobs:
            batch_id = job.input_payload.get("batch_id")
            if not batch_id:
                async with session_factory() as session:
                    j = await session.get(AIJob, job.id)
                    if j:
                        j.status = AIJobStatus.FAILED
                        j.error_message = "No batch_id in input_payload"
                        await session.commit()
                continue
            
            try:
                resp = await client.get(
                    f"https://api.anthropic.com/v1/messages/batches/{batch_id}",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01"
                    }
                )
                resp.raise_for_status()
                data = resp.json()
                status = data.get("processing_status")
                
                if status == "ended":
                    results_url = data.get("results_url")
                    async with session_factory() as session:
                        j = await session.get(AIJob, job.id)
                        if not j:
                            continue
                            
                        if results_url:
                            res_resp = await client.get(
                                results_url,
                                headers={
                                    "x-api-key": api_key,
                                    "anthropic-version": "2023-06-01"
                                }
                            )
                            res_resp.raise_for_status()
                            
                            results = []
                            for line in res_resp.text.strip().split("\n"):
                                if line.strip():
                                    results.append(json.loads(line))
                            
                            j.output_payload = {"results": results}
                            j.status = AIJobStatus.SUCCEEDED
                        else:
                            j.status = AIJobStatus.FAILED
                            j.error_message = "Batch ended but no results_url found"
                            
                        await session.commit()
                    processed += 1
                elif status in ["canceling", "expired"]:
                    async with session_factory() as session:
                        j = await session.get(AIJob, job.id)
                        if j:
                            j.status = AIJobStatus.FAILED
                            j.error_message = f"Batch finished with status: {status}"
                            await session.commit()
                    processed += 1
                        
            except Exception as e:
                pass

    return processed
