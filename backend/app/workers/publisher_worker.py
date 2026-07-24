from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from arq import cron
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.core.configs import settings
from backend.app.db.enums import (
    ContentStatus,
    PublicationStatus,
    PublicationTargetStatus,
)
from backend.app.db.publication import Publication
from backend.app.db.publication_attempt import PublicationAttempt
from backend.app.db.publication_history import PublicationHistory
from backend.app.db.publication_target import PublicationTarget
from backend.app.integrations.social_adapters import PublishPayload
from backend.app.modules.publishing.service import PublishingService
from backend.app.services.auto_publish_service import AutoPublishService
from backend.app.services.notification_service import NotificationService
from backend.app.workers.common import WorkerContext, build_redis_settings, shutdown, startup


async def process_due_publications(ctx: WorkerContext) -> int:
    session_factory = ctx["session_factory"]
    async with session_factory() as session:
        await AutoPublishService().enqueue_daily_approved_publications(session)

    async with session_factory() as session:
        publication_ids = (
            await session.scalars(
                select(Publication.id)
                .where(
                    Publication.status.in_(
                        [
                            PublicationStatus.QUEUED,
                            PublicationStatus.IN_PROGRESS,
                        ]
                    ),
                    Publication.scheduled_at <= datetime.now(UTC),
                )
                .order_by(Publication.scheduled_at)
                .limit(20)
            )
        ).all()

    concurrency_limit = asyncio.Semaphore(5)

    async def _run(publication_id: str) -> str:
        async with concurrency_limit:
            return await process_publication(ctx, publication_id)

    if not publication_ids:
        return 0
    results = await asyncio.gather(*[_run(publication_id) for publication_id in publication_ids], return_exceptions=True)
    return sum(1 for item in results if not isinstance(item, Exception))


async def process_publication(ctx: WorkerContext, publication_id: str) -> str:
    session_factory = ctx["session_factory"]
    social_registry = ctx["social_registry"]
    platform_semaphores = ctx["platform_semaphores"]
    async with session_factory() as session:
        publication = await session.scalar(
            select(Publication)
            .options(
                selectinload(Publication.content_item),
                selectinload(Publication.targets).selectinload(PublicationTarget.integration),
                selectinload(Publication.targets).selectinload(PublicationTarget.attempts),
            )
            .where(Publication.id == publication_id)
        )
        if publication is None or publication.content_item is None:
            return "skipped"

        publication.status = PublicationStatus.IN_PROGRESS
        service = PublishingService()
        now = datetime.now(UTC)

        for target in publication.targets:
            attempt = _current_attempt(target, publication)
            if target.status not in {
                PublicationTargetStatus.QUEUED,
                PublicationTargetStatus.FAILED,
                PublicationTargetStatus.IN_PROGRESS,
            }:
                continue
            if attempt.next_retry_at and attempt.next_retry_at > now:
                continue

            adapter = social_registry.adapter_for(target.platform.value)
            attempt.status = PublicationTargetStatus.IN_PROGRESS

            try:
                semaphore = platform_semaphores.get(target.platform.value, asyncio.Semaphore(1))
                async with semaphore:
                    result = await adapter.publish(
                        target.integration,
                        PublishPayload(
                            text=publication.content_item.text,
                            media_urls=[
                                media_url
                                for media_url in [
                                    publication.content_item.image_url,
                                    publication.content_item.video_url,
                                ]
                                if media_url
                            ],
                            scheduled_at=publication.scheduled_at,
                            metadata={
                                "tenant_id": publication.tenant_id,
                                "project_id": publication.project_id,
                                "publication_id": publication.id,
                            },
                        ),
                    )
                target.external_post_id = result.external_post_id
                target.published_at = result.published_at
                target.compensate_required = publication.all_or_nothing
                attempt.status = PublicationTargetStatus.PUBLISHED
                attempt.error_message = None
                attempt.response_payload = result.metadata
                attempt.next_retry_at = None
                session.add(
                    PublicationHistory(
                        tenant_id=publication.tenant_id,
                        publication_id=publication.id,
                        publication_target_id=target.id,
                        platform=target.platform.value,
                        status="published",
                        message="Publication target sent successfully",
                        payload=result.metadata,
                    )
                )
                await service.mark_target_result(
                    session,
                    publication,
                    target,
                    True,
                    message="published",
                )
            except Exception as exc:  # noqa: BLE001
                await _handle_failure(
                    session=session,
                    publication=publication,
                    target=target,
                    attempt=attempt,
                    error_message=str(exc),
                    registry=social_registry,
                )

        if publication.status == PublicationStatus.PUBLISHED:
            publication.content_item.status = ContentStatus.PUBLISHED
        await session.commit()
        return publication.status.value


def _current_attempt(target: PublicationTarget, publication: Publication) -> PublicationAttempt:
    if target.attempts:
        return max(target.attempts, key=lambda item: item.attempt_number)

    attempt = PublicationAttempt(
        tenant_id=publication.tenant_id,
        publication_target_id=target.id,
        attempt_number=1,
        status=PublicationTargetStatus.QUEUED,
        next_retry_at=publication.scheduled_at,
    )
    target.attempts.append(attempt)
    return attempt


async def _handle_failure(
    *,
    session,
    publication: Publication,
    target: PublicationTarget,
    attempt: PublicationAttempt,
    error_message: str,
    registry,
) -> None:
    service = PublishingService()
    session.add(
        PublicationHistory(
            tenant_id=publication.tenant_id,
            publication_id=publication.id,
            publication_target_id=target.id,
            platform=target.platform.value,
            status="failed",
            message=error_message,
            payload={"attempt_number": attempt.attempt_number},
        )
    )
    if attempt.attempt_number < settings.workers.max_retries:
        attempt.status = PublicationTargetStatus.FAILED
        attempt.error_message = error_message
        next_retry_at = datetime.now(UTC) + timedelta(minutes=min(2 ** attempt.attempt_number, 60))
        attempt.next_retry_at = next_retry_at
        session.add(
            PublicationAttempt(
                tenant_id=publication.tenant_id,
                publication_target_id=target.id,
                attempt_number=attempt.attempt_number + 1,
                status=PublicationTargetStatus.QUEUED,
                next_retry_at=next_retry_at,
            )
        )
        target.status = PublicationTargetStatus.QUEUED
        publication.status = PublicationStatus.QUEUED
        return

    publication.last_error_message = error_message
    await service.mark_target_result(
        session,
        publication,
        target,
        False,
        message=error_message,
        all_or_nothing=publication.all_or_nothing,
    )
    await NotificationService().notify_publication_failure(
        session,
        tenant_id=publication.tenant_id,
        project_id=publication.project_id,
        title=f"{target.platform.value.upper()} publication failed",
        message=error_message,
        metadata={
            "publication_id": publication.id,
            "platform": target.platform.value,
            "attempt_number": attempt.attempt_number,
        },
        alert_telegram_admins=target.platform.value == "vk",
    )
    attempt.status = PublicationTargetStatus.FAILED
    attempt.error_message = error_message
    attempt.next_retry_at = None
    if publication.all_or_nothing:
        for candidate in publication.targets:
            if candidate.id == target.id or not candidate.external_post_id or not candidate.compensate_required:
                continue
            adapter = registry.adapter_for(candidate.platform.value)
            await adapter.delete(candidate.integration, candidate.external_post_id)
            candidate.status = PublicationTargetStatus.COMPENSATED
            candidate.compensate_required = False


class WorkerSettings:
    functions = [process_publication]
    cron_jobs = [cron(process_due_publications, second={5, 20, 35, 50}, run_at_startup=True)]
    on_startup = startup
    on_shutdown = shutdown
    queue_name = settings.workers.publisher_queue_name
    redis_settings = build_redis_settings()
    health_check_key = f"{settings.workers.publisher_queue_name}:health"
    job_timeout = 300
