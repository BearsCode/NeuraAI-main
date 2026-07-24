from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.analytics_snapshot import AnalyticsSnapshot
from backend.app.db.publication import Publication
from backend.app.db.training_signal import TrainingSignal
from backend.app.integrations import ai_client
from backend.app.modules.agents.base import BaseAgent
from backend.app.services_internal.business_memory import BusinessMemoryService


class CEOAgent(BaseAgent):
    name = "ceo"
    description = "Еженедельные CEO-отчёты, анализ, утренние брифинги"

    def __init__(self):
        self.memory = BusinessMemoryService()

    async def execute(
        self,
        session: AsyncSession,
        input_data: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        project_id = input_data.get("project_id", (context or {}).get("project_id"))
        tenant_id = input_data.get("tenant_id", (context or {}).get("tenant_id"))
        report_type = input_data.get("report_type", "weekly")

        now = datetime.now(UTC)
        days = 7 if report_type == "daily" else 30 if report_type == "monthly" else 7
        cutoff = now - timedelta(days=days)

        recent_pubs = (
            await session.scalars(
                select(Publication)
                .where(
                    Publication.tenant_id == tenant_id,
                    Publication.project_id == project_id,
                    Publication.published_at >= cutoff,
                )
                .order_by(desc(Publication.published_at))
            )
        ).all()

        snapshots = (
            await session.scalars(
                select(AnalyticsSnapshot)
                .where(
                    AnalyticsSnapshot.tenant_id == tenant_id,
                    AnalyticsSnapshot.project_id == project_id,
                    AnalyticsSnapshot.collected_at >= cutoff,
                )
            )
        ).all()

        signals = (
            await session.scalars(
                select(TrainingSignal)
                .where(
                    TrainingSignal.tenant_id == tenant_id,
                    TrainingSignal.project_id == project_id,
                    TrainingSignal.created_at >= cutoff,
                )
                .order_by(desc(TrainingSignal.created_at))
            )
        ).all()

        total_reach = sum(s.reach or 0 for s in snapshots)
        total_likes = sum(s.likes or 0 for s in snapshots)
        total_comments = sum(s.comments or 0 for s in snapshots)
        total_clicks = sum(s.saves or 0 for s in snapshots)
        published_count = len(recent_pubs)
        approved_signals = sum(1 for s in signals if s.action in ("approved", "approved_with_edits", "marked_as_best"))
        rejected_signals = sum(1 for s in signals if s.action in ("rejected", "deleted_after_publish"))

        profile = await self.memory.get_company_profile(session, tenant_id, project_id)

        prompt = (
            f"Generate a {report_type} CEO report for this business.\n"
            f"Company: {profile.get('company_name')}\n"
            f"Period: last {days} days\n"
            f"Published: {published_count} posts\n"
            f"Total reach: {total_reach}\n"
            f"Total likes: {total_likes}\n"
            f"Total comments: {total_comments}\n"
            f"Total clicks: {total_clicks}\n"
            f"Approved signals: {approved_signals}\n"
            f"Rejected signals: {rejected_signals}\n"
            f"Return JSON with: executive_summary (str), key_metrics (dict), "
            f"top_performing_content (list), areas_for_improvement (list), "
            f"recommendations (list of str), next_steps (str)"
        )

        result = await ai_client.generate(prompt=prompt, response_format={"type": "json_object"})

        return {
            "report_type": report_type,
            "period_days": days,
            "generated_at": now.isoformat(),
            "metrics": {
                "published_count": published_count,
                "total_reach": total_reach,
                "total_likes": total_likes,
                "total_comments": total_comments,
                "total_clicks": total_clicks,
                "approved_signals": approved_signals,
                "rejected_signals": rejected_signals,
            },
            "analysis": result if isinstance(result, dict) else {"report": str(result)},
        }
