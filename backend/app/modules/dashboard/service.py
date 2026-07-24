from __future__ import annotations

from datetime import UTC, datetime, time

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.analytics_snapshot import AnalyticsSnapshot
from backend.app.db.approval_policy import ApprovalPolicy
from backend.app.db.content_item import ContentItem
from backend.app.db.enums import ApprovalMode
from backend.app.db.project_strategy import ProjectStrategy
from backend.app.db.publication import Publication
from backend.app.db.social_integration import SocialIntegration
from backend.app.db.user import User
from backend.app.modules.access import ensure_project_access
from backend.app.modules.dashboard.schemas import (
    DashboardKPIResponse,
    DashboardResponse,
    DashboardScheduleItemResponse,
)


class DashboardService:
    async def get_dashboard(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        project_id: str,
    ) -> DashboardResponse:
        project = await ensure_project_access(session, current_user, tenant_id, project_id)
        strategy = await session.scalar(
            select(ProjectStrategy).where(
                ProjectStrategy.tenant_id == tenant_id,
                ProjectStrategy.project_id == project_id,
            )
        )
        policy = await session.scalar(
            select(ApprovalPolicy).where(
                ApprovalPolicy.tenant_id == tenant_id,
                ApprovalPolicy.project_id == project_id,
            )
        )
        snapshot = await session.scalar(
            select(AnalyticsSnapshot)
            .where(AnalyticsSnapshot.tenant_id == tenant_id, AnalyticsSnapshot.project_id == project_id)
            .order_by(AnalyticsSnapshot.collected_at.desc())
        )
        connected_integrations = (
            await session.scalars(
                select(SocialIntegration)
                .where(
                    SocialIntegration.tenant_id == tenant_id,
                    SocialIntegration.project_id == project_id,
                )
                .order_by(SocialIntegration.created_at.desc())
            )
        ).all()
        upcoming_items = (
            await session.scalars(
                select(ContentItem)
                .where(ContentItem.tenant_id == tenant_id, ContentItem.project_id == project_id)
                .order_by(ContentItem.publish_date, ContentItem.publish_time)
                .limit(7)
            )
        ).all()
        publications_total = await session.scalar(
            select(func.count(Publication.id)).where(
                Publication.tenant_id == tenant_id,
                Publication.project_id == project_id,
            )
        )

        return DashboardResponse(
            tenant_id=tenant_id,
            project_id=project_id,
            strategy_status=project.strategy_status.value,
            connected_platforms=[item.platform.value for item in connected_integrations if item.status.value == "connected"],
            approval_mode=(policy.mode.value if policy else ApprovalMode.MANUAL.value),
            kpis=[
                DashboardKPIResponse(code="publications_total", value=int(publications_total or 0), label="Publications"),
                DashboardKPIResponse(code="followers", value=snapshot.followers if snapshot else 0, label="Followers"),
                DashboardKPIResponse(code="reach", value=snapshot.reach if snapshot else 0, label="Reach"),
                DashboardKPIResponse(code="er", value=snapshot.er if snapshot else 0.0, label="Engagement Rate"),
            ],
            ai_recommendations=strategy.recommendations if strategy else [
                f"Start with Telegram and VK for {project.company_name}.",
                "Use case-based posts and educational posts as the core mix.",
            ],
            upcoming_schedule=[
                DashboardScheduleItemResponse(
                    content_item_id=item.id,
                    platform=item.platform.value,
                    content_type=item.content_type.value,
                    publish_at=datetime.combine(item.publish_date, item.publish_time or time(hour=10), tzinfo=UTC),
                    status=item.status.value,
                )
                for item in upcoming_items
            ],
        )
