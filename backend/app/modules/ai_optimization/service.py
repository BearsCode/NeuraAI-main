from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.ai_job import AIJob
from backend.app.db.enums import AIJobStatus, OptimizationStatus
from backend.app.db.optimization_recommendation import OptimizationRecommendation
from backend.app.db.user import User
from backend.app.events.schemas import EventEnvelope, OptimizationSuggestedEvent
from backend.app.infra.outbox import OutboxService
from backend.app.modules.access import ensure_project_access
from backend.app.modules.ai_optimization.schemas import OptimizationRecommendationResponse


class AIOptimizationService:
    async def trigger(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        project_id: str,
        reason: str | None,
    ) -> OptimizationRecommendationResponse:
        project = await ensure_project_access(session, current_user, tenant_id, project_id)
        recommendation = OptimizationRecommendation(
            tenant_id=tenant_id,
            project_id=project_id,
            status=OptimizationStatus.PENDING,
            summary=f"Optimization run requested for {project.company_name}",
            details={
                "reason": reason or "weekly_review",
                "suggested_publish_time": "10:30",
                "suggested_frequency": "5 posts per week",
            },
            suggested_publish_time="10:30",
            suggested_frequency="5 posts per week",
        )
        session.add(recommendation)
        await session.flush()
        session.add(
            AIJob(
                tenant_id=tenant_id,
                project_id=project_id,
                job_type="optimization",
                provider="queued",
                model="queued",
                status=AIJobStatus.PENDING,
                input_payload={"recommendation_id": recommendation.id},
            )
        )
        await OutboxService().enqueue(
            session,
            EventEnvelope(
                event_type="optimization.suggested",
                topic="optimization.suggested.v1",
                tenant_id=tenant_id,
                aggregate_id=recommendation.id,
                payload=OptimizationSuggestedEvent(
                    tenant_id=tenant_id,
                    recommendation_id=recommendation.id,
                ).model_dump(mode="json"),
            ),
        )
        await session.commit()
        return self._to_response(recommendation)

    async def list_recommendations(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        project_id: str,
    ) -> list[OptimizationRecommendationResponse]:
        await ensure_project_access(session, current_user, tenant_id, project_id)
        items = (
            await session.scalars(
                select(OptimizationRecommendation)
                .where(
                    OptimizationRecommendation.tenant_id == tenant_id,
                    OptimizationRecommendation.project_id == project_id,
                )
                .order_by(OptimizationRecommendation.created_at.desc())
            )
        ).all()
        return [self._to_response(item) for item in items]

    def _to_response(self, item: OptimizationRecommendation) -> OptimizationRecommendationResponse:
        return OptimizationRecommendationResponse(
            recommendation_id=item.id,
            tenant_id=item.tenant_id,
            project_id=item.project_id,
            status=item.status.value,
            summary=item.summary,
            details=item.details,
            created_at=item.created_at,
        )
