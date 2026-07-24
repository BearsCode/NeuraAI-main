from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.enums import WorkflowStatus
from backend.app.db.publication import Publication
from backend.app.db.retail_catalog_sync import RetailCatalogSync
from backend.app.db.workflow_instance import WorkflowInstance


class SchedulerService:
    async def check_publication_queue(self, session: AsyncSession) -> list[dict]:
        now = datetime.now(UTC)
        due_pubs = (
            await session.scalars(
                select(Publication)
                .where(
                    Publication.status == "queued",
                    Publication.scheduled_at <= now,
                    Publication.scheduled_at >= now - timedelta(hours=1),
                )
                .order_by(Publication.scheduled_at)
                .limit(50)
            )
        ).all()

        from sqlalchemy import text

        results = []
        for pub in due_pubs:
            from backend.app.core.configs import settings
            if settings.database_uses_sqlite:
                existing = await session.scalar(
                    select(WorkflowInstance).where(
                        text("json_extract(context, '$.publication_id') = :pid"),
                        WorkflowInstance.status.in_(["running", "pending"]),
                    )
                )
            else:
                existing = await session.scalar(
                    select(WorkflowInstance).where(
                        WorkflowInstance.context["publication_id"].as_string() == pub.id,
                        WorkflowInstance.status.in_(["running", "pending"]),
                    )
                )
            if existing:
                continue

            pub.status = "in_progress"
            results.append(
                {
                    "publication_id": pub.id,
                    "project_id": pub.project_id,
                    "tenant_id": pub.tenant_id,
                    "platform": pub.platform,
                    "scheduled_at": pub.scheduled_at.isoformat() if pub.scheduled_at else None,
                }
            )

        await session.flush()
        return results

    async def check_content_queue(
        self, session: AsyncSession, tenant_id: str, project_id: str
    ) -> dict:
        now = datetime.now(UTC)
        upcoming = (
            await session.scalars(
                select(Publication)
                .where(
                    Publication.tenant_id == tenant_id,
                    Publication.project_id == project_id,
                    Publication.status.in_(["queued", "pending_approval"]),
                    Publication.scheduled_at >= now,
                )
                .order_by(Publication.scheduled_at)
            )
        ).all()

        next_7_days_pubs = [p for p in upcoming if p.scheduled_at and p.scheduled_at <= now + timedelta(days=7)]
        total_queued = len(upcoming)
        next_7_days_count = len(next_7_days_pubs)

        return {
            "total_queued": total_queued,
            "next_7_days_count": next_7_days_count,
            "needs_content": next_7_days_count < 7,
            "empty_slots": max(0, 7 - next_7_days_count),
            "upcoming_publications": [
                {
                    "id": p.id,
                    "platform": p.platform,
                    "content_type": p.content_type.value if p.content_type else None,
                    "scheduled_at": p.scheduled_at.isoformat() if p.scheduled_at else None,
                    "status": p.status,
                }
                for p in upcoming[:20]
            ],
        }

    async def schedule_content_generation(
        self,
        session: AsyncSession,
        tenant_id: str,
        project_id: str,
        workflow_type: str = "content_generation",
    ) -> str | None:
        queue = await self.check_content_queue(session, tenant_id, project_id)
        if not queue["needs_content"]:
            return None

        workflow = WorkflowInstance(
            tenant_id=tenant_id,
            project_id=project_id,
            workflow_type=workflow_type,
            status=WorkflowStatus.PENDING.value,
            trigger="scheduler_content_gap",
            current_step=0,
            total_steps=3,
            context={"reason": "content_queue_low", "empty_slots": queue["empty_slots"]},
        )
        session.add(workflow)
        await session.flush()
        await session.commit()
        return workflow.id

    async def run_retail_sync(
        self, session: AsyncSession, tenant_id: str, project_id: str
    ) -> dict:
        last_sync = (
            await session.scalars(
                select(RetailCatalogSync)
                .where(
                    RetailCatalogSync.tenant_id == tenant_id,
                    RetailCatalogSync.project_id == project_id,
                    RetailCatalogSync.status == "completed",
                )
                .order_by(desc(RetailCatalogSync.created_at))
                .limit(1)
            )
        ).first()

        now = datetime.now(UTC)
        if last_sync and last_sync.created_at:
            hours_since = (now - last_sync.created_at).total_seconds() / 3600
            if hours_since < 6:
                return {"status": "skipped", "reason": f"Last sync was {hours_since:.1f}h ago, need 6h gap"}

        sync = RetailCatalogSync(
            tenant_id=tenant_id,
            project_id=project_id,
            source_system="scheduled",
            status="syncing",
            started_at=now,
        )
        session.add(sync)
        await session.flush()
        sync.status = "completed"
        sync.completed_at = datetime.now(UTC)
        await session.commit()

        return {"status": "completed", "sync_id": sync.id}

    async def check_async_jobs(self, session: AsyncSession) -> list[dict]:
        stale = (
            await session.scalars(
                select(WorkflowInstance)
                .where(
                    WorkflowInstance.status.in_(["running", "waiting_async"]),
                    WorkflowInstance.started_at <= datetime.now(UTC) - timedelta(hours=6),
                )
                .limit(20)
            )
        ).all()

        results = []
        for wf in stale:
            wf.status = WorkflowStatus.FAILED.value
            wf.error = "Timed out after 6 hours"
            wf.completed_at = datetime.now(UTC)
            results.append(
                {
                    "workflow_id": wf.id,
                    "status": "timed_out",
                }
            )

        await session.flush()
        return results
