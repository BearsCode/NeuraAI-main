from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.analytics_snapshot import AnalyticsSnapshot
from backend.app.db.content_plan import ContentPlan
from backend.app.db.publication import Publication
from backend.app.db.publication_target import PublicationTarget
from backend.app.services_internal.business_memory import BusinessMemoryService
from backend.app.integrations import ai_client


class AIPlanner:
    def __init__(self):
        self.memory = BusinessMemoryService()

    async def analyze_content_need(
        self, session: AsyncSession, tenant_id: str, project_id: str
    ) -> dict:
        context = await self.memory.get_full_context(session, tenant_id, project_id)
        upcoming_pubs = (
            await session.scalars(
                select(Publication)
                .where(
                    Publication.tenant_id == tenant_id,
                    Publication.project_id == project_id,
                    Publication.status.in_(["queued", "pending_approval"]),
                    Publication.scheduled_at >= datetime.now(UTC),
                )
                .order_by(Publication.scheduled_at)
            )
        ).all()

        queue_count = len(upcoming_pubs)
        next_7_days = sum(
            1 for p in upcoming_pubs if p.scheduled_at and p.scheduled_at <= datetime.now(UTC) + timedelta(days=7)
        )
        recommended_min = 7

        needs_content = next_7_days < recommended_min

        prompt = (
            f"Analyze this business and determine if new content is needed.\n"
            f"Company: {context.get('company_profile', {}).get('company_name', 'Unknown')}\n"
            f"Niche: {context.get('company_profile', {}).get('company_niche', 'Unknown')}\n"
            f"Queue status: {queue_count} upcoming, {next_7_days} in next 7 days\n"
            f"Analytics: {context.get('analytics', {})}\n"
            f"Topics: {context.get('topic_model', {})}\n"
            f"Products on sale: {len(context.get('retail_catalog', {}).get('on_sale', []))}\n"
            f"Preferences: {context.get('preferences', {})}\n"
            f"Return JSON with: needs_content (bool), reason (str), suggested_topics (list), suggested_formats (list)"
        )

        result = await ai_client.generate(prompt=prompt, response_format={"type": "json_object"})

        return {
            "needs_content": needs_content,
            "queue_count": queue_count,
            "next_7_days_count": next_7_days,
            "recommended_min": recommended_min,
            "analysis": result,
            "context_summary": {
                "total_products": context.get("retail_catalog", {}).get("total_products", 0),
                "on_sale_products": len(context.get("retail_catalog", {}).get("on_sale", [])),
                "avg_engagement": context.get("analytics", {}).get("avg_engagement_rate", 0),
                "successful_topics": context.get("topic_model", {}).get("successful_topics", []),
            },
        }

    async def create_content_plan(
        self, session: AsyncSession, tenant_id: str, project_id: str, days: int = 30, priority_note: str | None = None
    ) -> dict:
        need = await self.analyze_content_need(session, tenant_id, project_id)
        context = await self.memory.get_full_context(session, tenant_id, project_id)

        prompt = (
            f"Create a {days}-day content plan for this business.\n"
            f"Company: {context.get('company_profile', {})}\n"
            f"Preferences: {context.get('preferences', {})}\n"
            f"Analytics: {context.get('analytics', {})}\n"
            f"Topics: {context.get('topic_model', {})}\n"
            f"Retail catalog: {context.get('retail_catalog', {})}\n"
            f"Priority Note / Manager Note: {priority_note if priority_note else 'None'}\n"
            f"Create exactly {days//2} posts (one every 2 days).\n"
            f"If there is a Priority Note, prioritize those items from the catalog or themes.\n"
            f"For each post specify: topic, format, platform, scheduled_time (ISO), use_avatar (bool), product_id (if applicable)\n"
            f"Return JSON with: posts (array of objects)"
        )

        plan_result = await ai_client.generate(prompt=prompt, response_format={"type": "json_object"})

        posts = plan_result.get("posts", []) if isinstance(plan_result, dict) else []
        content_plan = ContentPlan(
            tenant_id=tenant_id,
            project_id=project_id,
            plan_data={
                "days": days,
                "posts": posts,
                "analysis": need,
                "generated_at": datetime.now(UTC).isoformat(),
            },
            status="active",
        )
        session.add(content_plan)
        await session.flush()

        return {
            "plan_id": content_plan.id,
            "posts": posts,
            "analysis": need,
        }

    async def determine_optimal_time(
        self, session: AsyncSession, tenant_id: str, project_id: str
    ) -> dict:
        targets = (
            await session.scalars(
                select(PublicationTarget)
                .where(
                    PublicationTarget.tenant_id == tenant_id,
                    PublicationTarget.published_at.isnot(None),
                )
                .join(Publication, Publication.id == PublicationTarget.publication_id)
                .where(Publication.project_id == project_id)
                .order_by(desc(PublicationTarget.published_at))
                .limit(100)
            )
        ).all()

        hour_engagement: dict[int, list[float]] = {}
        day_engagement: dict[int, list[float]] = {}
        for target in targets:
            if not target.published_at:
                continue
            hour = target.published_at.hour
            day = target.published_at.weekday()
            er = 0.0
            hour_engagement.setdefault(hour, []).append(er)
            day_engagement.setdefault(day, []).append(er)

        snapshots = (
            await session.scalars(
                select(AnalyticsSnapshot)
                .where(
                    AnalyticsSnapshot.tenant_id == tenant_id,
                    AnalyticsSnapshot.project_id == project_id,
                )
                .order_by(desc(AnalyticsSnapshot.collected_at))
                .limit(90)
            )
        ).all()

        for snap in snapshots:
            hour = snap.collected_at.hour
            day = snap.collected_at.weekday()
            er = 0.0
            if snap.reach and snap.reach > 0:
                er = ((snap.likes or 0) + (snap.comments or 0)) / snap.reach * 100
            hour_engagement.setdefault(hour, []).append(er)
            day_engagement.setdefault(day, []).append(er)

        def avg(lst: list[float]) -> float:
            return sum(lst) / len(lst) if lst else 0.0

        best_hour = max(hour_engagement, key=lambda h: avg(hour_engagement[h])) if hour_engagement else 10
        best_day = max(day_engagement, key=lambda d: avg(day_engagement[d])) if day_engagement else 2

        return {
            "best_hour": best_hour,
            "best_day": best_day,
            "hourly_breakdown": {str(h): round(avg(v), 2) for h, v in hour_engagement.items()},
            "daily_breakdown": {str(d): round(avg(v), 2) for d, v in day_engagement.items()},
        }

    async def adjust_strategy(
        self, session: AsyncSession, tenant_id: str, project_id: str
    ) -> dict:
        context = await self.memory.get_full_context(session, tenant_id, project_id)
        analytics = context.get("analytics", {})
        preferences = context.get("preferences", {})

        prompt = (
            f"Review content strategy performance and suggest adjustments.\n"
            f"Analytics: {analytics}\n"
            f"Preferences: {preferences}\n"
            f"Topic model: {context.get('topic_model', {})}\n"
            f"Identify what's working, what's not, and what should change.\n"
            f"Return JSON with: adjustments (array of objects with field, current_value, suggested_value, reason)"
        )

        result = await ai_client.generate(prompt=prompt, response_format={"type": "json_object"})

        return result if isinstance(result, dict) else {}
