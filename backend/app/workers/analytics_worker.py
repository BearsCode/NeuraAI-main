from __future__ import annotations

from datetime import UTC, datetime

from arq import cron
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.core.configs import settings
from backend.app.db.analytics_snapshot import AnalyticsSnapshot
from backend.app.db.project import Project
from backend.app.events.schemas import AnalyticsCollectedEvent, EventEnvelope
from backend.app.infra.outbox import OutboxService
from backend.app.services.subscription_lifecycle import SubscriptionLifecycleService
from backend.app.workers.common import WorkerContext, build_redis_settings, shutdown, startup


async def collect_due_analytics(ctx: WorkerContext) -> int:
    session_factory = ctx["session_factory"]
    async with session_factory() as session:
        project_ids = (
            await session.scalars(
                select(Project.id)
                .order_by(Project.created_at.desc())
                .limit(50)
            )
        ).all()

    processed = 0
    for project_id in project_ids:
        await collect_project_analytics(ctx, project_id)
        processed += 1
    return processed


async def collect_project_analytics(ctx: WorkerContext, project_id: str) -> str:
    session_factory = ctx["session_factory"]
    registry = ctx["social_registry"]
    async with session_factory() as session:
        project = await session.scalar(
            select(Project)
            .options(selectinload(Project.integrations))
            .where(Project.id == project_id)
        )
        if project is None:
            return "skipped"

        totals = {
            "reach": 0,
            "followers": 0,
            "likes": 0,
            "comments": 0,
            "saves": 0,
        }
        for integration in project.integrations:
            if integration.status.value != "connected":
                continue
            metrics = await registry.adapter_for(integration.platform.value).fetch_analytics(integration)
            totals["reach"] += metrics.reach
            totals["followers"] += metrics.followers
            totals["likes"] += metrics.likes
            totals["comments"] += metrics.comments
            totals["saves"] += metrics.saves

        followers = max(totals["followers"], 1)
        reach = max(totals["reach"], 1)
        ctr = round((totals["likes"] / reach) * 100, 2)
        er = round(((totals["likes"] + totals["comments"] + totals["saves"]) / followers) * 100, 2)
        snapshot = AnalyticsSnapshot(
            tenant_id=project.tenant_id,
            project_id=project.id,
            platform="all",
            collected_at=datetime.now(UTC),
            reach=totals["reach"],
            followers=totals["followers"],
            likes=totals["likes"],
            comments=totals["comments"],
            saves=totals["saves"],
            ctr=ctr,
            er=er,
            audience_growth=round(er / 3, 2),
            raw_metrics={"integrations": len(project.integrations)},
        )
        session.add(snapshot)
        await session.flush()
        await OutboxService().enqueue(
            session,
            EventEnvelope(
                event_type="analytics.collected",
                topic="analytics.collected.v1",
                tenant_id=project.tenant_id,
                aggregate_id=snapshot.id,
                payload=AnalyticsCollectedEvent(
                    tenant_id=project.tenant_id,
                    project_id=project.id,
                    snapshot_id=snapshot.id,
                ).model_dump(mode="json"),
            ),
        )
        await session.commit()
        return snapshot.id


async def process_subscription_lifecycle(ctx: WorkerContext) -> dict[str, int]:
    session_factory = ctx["session_factory"]
    svc = SubscriptionLifecycleService()
    async with session_factory() as session:
        return await svc.run_all(session)


class WorkerSettings:
    functions = [collect_project_analytics, process_subscription_lifecycle]
    cron_jobs = [
        cron(collect_due_analytics, minute={0}, run_at_startup=True),
        cron(process_subscription_lifecycle, minute={0}, run_at_startup=True),
    ]
    on_startup = startup
    on_shutdown = shutdown
    queue_name = settings.workers.analytics_queue_name
    redis_settings = build_redis_settings()
    health_check_key = f"{settings.workers.analytics_queue_name}:health"
    job_timeout = 600
