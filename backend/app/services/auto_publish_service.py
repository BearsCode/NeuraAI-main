from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.db.approval_policy import ApprovalPolicy
from backend.app.db.enums import PublicationStatus
from backend.app.db.publication import Publication
from backend.app.db.publication_history import PublicationHistory
from backend.app.db.tenant import Tenant


class AutoPublishService:
    """Select publications eligible for daily auto publishing."""

    async def enqueue_daily_approved_publications(
        self,
        session: AsyncSession,
        *,
        now_utc: datetime | None = None,
    ) -> list[str]:
        """Move approved publications into the processing queue at 09:00 tenant local time."""

        current_time = now_utc or datetime.now(UTC)
        rows = (
            await session.execute(
                select(Publication, ApprovalPolicy, Tenant)
                .join(ApprovalPolicy, ApprovalPolicy.project_id == Publication.project_id)
                .join(Tenant, Tenant.id == Publication.tenant_id)
                .options(selectinload(Publication.targets))
                .where(
                    Publication.status == PublicationStatus.APPROVED,
                    ApprovalPolicy.auto_publish_enabled.is_(True),
                )
            )
        ).all()

        queued_ids: list[str] = []
        for publication, policy, tenant in rows:
            if not self._is_autopublish_window(publication, tenant.default_timezone, current_time):
                continue
            if policy.auto_publish_platforms:
                target_platforms = {target.platform.value for target in publication.targets}
                if not target_platforms.issubset(set(policy.auto_publish_platforms)):
                    continue

            publication.status = PublicationStatus.QUEUED
            if publication.scheduled_at > current_time:
                publication.scheduled_at = current_time
            session.add(
                PublicationHistory(
                    tenant_id=publication.tenant_id,
                    publication_id=publication.id,
                    platform="batch",
                    status="queued",
                    message="Publication queued by auto-publish scheduler",
                    payload={
                        "project_timezone": tenant.default_timezone,
                        "scheduled_at": publication.scheduled_at.isoformat(),
                    },
                )
            )
            queued_ids.append(publication.id)

        if queued_ids:
            await session.commit()
        return queued_ids

    def _is_autopublish_window(
        self,
        publication: Publication,
        timezone_name: str,
        now_utc: datetime,
    ) -> bool:
        tzinfo = self._timezone(timezone_name)
        local_now = now_utc.astimezone(tzinfo)
        scheduled_local = publication.scheduled_at.astimezone(tzinfo)
        if local_now.hour != 9 or local_now.minute >= 5:
            return False
        return scheduled_local.date() <= local_now.date()

    def _timezone(self, timezone_name: str) -> ZoneInfo:
        try:
            return ZoneInfo(timezone_name or "UTC")
        except ZoneInfoNotFoundError:
            return ZoneInfo("UTC")
