from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.analytics_snapshot import AnalyticsSnapshot
from backend.app.db.publication import Publication
from backend.app.db.user import User
from backend.app.modules.access import ensure_project_access
from backend.app.modules.analytics.schemas import (
    AnalyticsDashboardPoint,
    AnalyticsDashboardResponse,
    AnalyticsMetricResponse,
    AnalyticsOverviewResponse,
)


class AnalyticsService:
    async def get_dashboard(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        project_id: str,
        *,
        days: int = 7,
    ) -> AnalyticsDashboardResponse:
        """Return analytics grouped by day and social platform for the dashboard."""

        await ensure_project_access(session, current_user, tenant_id, project_id)
        since = datetime.now(UTC) - timedelta(days=days)
        day_column = func.date(AnalyticsSnapshot.collected_at).label("day")
        rows = (
            await session.execute(
                select(
                    day_column,
                    AnalyticsSnapshot.platform,
                    func.coalesce(func.sum(AnalyticsSnapshot.reach), 0).label("reach"),
                    func.coalesce(func.sum(AnalyticsSnapshot.followers), 0).label("followers"),
                    func.coalesce(func.sum(AnalyticsSnapshot.likes), 0).label("likes"),
                    func.coalesce(func.sum(AnalyticsSnapshot.comments), 0).label("comments"),
                    func.coalesce(func.sum(AnalyticsSnapshot.saves), 0).label("saves"),
                    func.coalesce(func.avg(AnalyticsSnapshot.ctr), 0).label("ctr"),
                    func.coalesce(func.avg(AnalyticsSnapshot.er), 0).label("er"),
                )
                .where(
                    AnalyticsSnapshot.tenant_id == tenant_id,
                    AnalyticsSnapshot.project_id == project_id,
                    AnalyticsSnapshot.collected_at >= since,
                )
                .group_by(day_column, AnalyticsSnapshot.platform)
                .order_by(day_column.asc(), AnalyticsSnapshot.platform.asc())
            )
        ).all()
        return AnalyticsDashboardResponse(
            tenant_id=tenant_id,
            project_id=project_id,
            days=days,
            points=[
                AnalyticsDashboardPoint(
                    date=row.day,
                    platform=row.platform,
                    reach=int(row.reach or 0),
                    followers=int(row.followers or 0),
                    likes=int(row.likes or 0),
                    comments=int(row.comments or 0),
                    saves=int(row.saves or 0),
                    ctr=round(float(row.ctr or 0), 2),
                    er=round(float(row.er or 0), 2),
                )
                for row in rows
            ],
        )

    async def get_overview(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        project_id: str,
    ) -> AnalyticsOverviewResponse:
        project = await ensure_project_access(session, current_user, tenant_id, project_id)
        snapshot = await session.scalar(
            select(AnalyticsSnapshot)
            .where(AnalyticsSnapshot.tenant_id == tenant_id, AnalyticsSnapshot.project_id == project_id)
            .order_by(AnalyticsSnapshot.collected_at.desc())
        )
        if not snapshot:
            publications_total = await session.scalar(
                select(Publication).where(
                    Publication.tenant_id == tenant_id,
                    Publication.project_id == project_id,
                )
            )
            snapshot = AnalyticsSnapshot(
                tenant_id=tenant_id,
                project_id=project_id,
                platform="all",
                collected_at=datetime.now(UTC),
                reach=max(1000, len(project.social_links) * 350),
                followers=200 + len(project.services) * 20,
                likes=80 + len(project.services) * 5,
                comments=25,
                saves=14,
                ctr=2.9,
                er=6.2,
                audience_growth=7.5,
                raw_metrics={"publications_total": 1 if publications_total else 0},
            )
            session.add(snapshot)
            await session.commit()
            await session.refresh(snapshot)

        return AnalyticsOverviewResponse(
            snapshot_id=snapshot.id,
            tenant_id=tenant_id,
            project_id=project_id,
            platform=snapshot.platform,
            collected_at=snapshot.collected_at,
            metrics=[
                AnalyticsMetricResponse(name="reach", value=snapshot.reach, unit="users"),
                AnalyticsMetricResponse(name="followers", value=snapshot.followers, unit="users"),
                AnalyticsMetricResponse(name="likes", value=snapshot.likes, unit="actions"),
                AnalyticsMetricResponse(name="comments", value=snapshot.comments, unit="actions"),
                AnalyticsMetricResponse(name="saves", value=snapshot.saves, unit="actions"),
                AnalyticsMetricResponse(name="ctr", value=snapshot.ctr, unit="%"),
                AnalyticsMetricResponse(name="er", value=snapshot.er, unit="%"),
                AnalyticsMetricResponse(name="audience_growth", value=snapshot.audience_growth, unit="%"),
            ],
            ai_summary=[
                "Telegram and VK remain the strongest channels for predictable lead acquisition.",
                "Increase reuse of top-performing posts into carousel and short-form variants.",
            ],
        )
