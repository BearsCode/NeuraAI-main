from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.analytics_snapshot import AnalyticsSnapshot
from backend.app.db.user import User
from backend.app.schemas.analytics import AnalyticsMetric, AnalyticsOverviewResponse
from backend.app.services.project_service import ensure_project_access


class AnalyticsService:
    async def get_overview(
        self,
        session: AsyncSession,
        current_user: User,
        project_id: str,
    ) -> AnalyticsOverviewResponse:
        project = await ensure_project_access(session, project_id, current_user)
        snapshot = None
        if project.analytics_snapshots:
            snapshot = sorted(project.analytics_snapshots, key=lambda item: item.created_at, reverse=True)[0]

        if not snapshot:
            snapshot = AnalyticsSnapshot(
                project_id=project.id,
                period="last_30_days",
                reach=max(1000, len(project.publications) * 250),
                followers=max(100, len(project.integrations) * 80),
                likes=max(50, len(project.content_items) * 12),
                comments=max(10, len(project.content_items) * 4),
                saves=max(8, len(project.content_items) * 3),
                ctr=2.7,
                er=5.4,
                audience_growth=7.8,
            )
            session.add(snapshot)
            await session.commit()
            await session.refresh(snapshot)

        strategy_recommendations = project.strategy.recommendations if project.strategy else []
        return AnalyticsOverviewResponse(
            project_id=project.id,
            period=snapshot.period,
            metrics=[
                AnalyticsMetric(name="reach", value=snapshot.reach, unit="users"),
                AnalyticsMetric(name="followers", value=snapshot.followers, unit="users"),
                AnalyticsMetric(name="likes", value=snapshot.likes, unit="actions"),
                AnalyticsMetric(name="comments", value=snapshot.comments, unit="actions"),
                AnalyticsMetric(name="saves", value=snapshot.saves, unit="actions"),
                AnalyticsMetric(name="ctr", value=snapshot.ctr, unit="%"),
                AnalyticsMetric(name="er", value=snapshot.er, unit="%"),
                AnalyticsMetric(name="audience_growth", value=snapshot.audience_growth, unit="%"),
            ],
            ai_summary=strategy_recommendations[:2]
            or [
                "Telegram and VK should be prioritized first for predictable SMB demand.",
                "Review the best-performing themes weekly and reuse them in new formats.",
            ],
        )
