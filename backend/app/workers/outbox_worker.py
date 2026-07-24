from __future__ import annotations

from arq import cron

from backend.app.core.configs import settings
from backend.app.infra.outbox import OutboxProcessor
from backend.app.workers.common import WorkerContext, build_redis_settings, shutdown, startup


async def flush_outbox(ctx: WorkerContext) -> int:
    processor = OutboxProcessor(
        session_factory=ctx["session_factory"],
        event_bus=ctx["event_bus"],
    )
    return await processor.process_pending()


class WorkerSettings:
    functions = [flush_outbox]
    cron_jobs = [cron(flush_outbox, second={0, 10, 20, 30, 40, 50}, run_at_startup=True)]
    on_startup = startup
    on_shutdown = shutdown
    queue_name = settings.workers.outbox_queue_name
    redis_settings = build_redis_settings()
    health_check_key = f"{settings.workers.outbox_queue_name}:health"
    job_timeout = 120
