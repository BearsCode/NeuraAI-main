from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.enums import StrategyStatus
from backend.app.db.project_strategy import ProjectStrategy
from backend.app.db.user import User
from backend.app.schemas.ai import AIAnalysisResponse, AIRecommendationResponse, StrategyResponse
from backend.app.services.ai_orchestration_service import AIOrchestrationService
from backend.app.services.project_service import ensure_project_access


class AIService:
    """Facade over AI orchestration for strategy-related endpoints."""

    def __init__(self) -> None:
        self.orchestration = AIOrchestrationService()

    async def generate(
        self,
        session: AsyncSession,
        current_user: User,
        project_id: str,
    ) -> ProjectStrategy:
        """Generate and persist project strategy."""

        project = await ensure_project_access(session, project_id, current_user)
        strategy = await self.orchestration.generate_strategy(session, project)
        project.strategy_status = StrategyStatus.ACTIVE
        await session.commit()
        await session.refresh(strategy)
        return strategy

    async def get_analysis(
        self,
        session: AsyncSession,
        current_user: User,
        project_id: str,
    ) -> AIAnalysisResponse:
        """Return the business, market, and competitor analysis blocks."""

        strategy = await self._get_or_generate(session, current_user, project_id)
        return AIAnalysisResponse(
            project_id=project_id,
            business_analysis=strategy.business_analysis,
            market_analysis=strategy.market_analysis,
            competitor_analysis=strategy.competitor_analysis,
        )

    async def get_strategy(
        self,
        session: AsyncSession,
        current_user: User,
        project_id: str,
    ) -> StrategyResponse:
        """Return the strategy summary."""

        strategy = await self._get_or_generate(session, current_user, project_id)
        return StrategyResponse(
            project_id=project_id,
            positioning=strategy.positioning,
            content_pillars=strategy.content_pillars,
            channels=strategy.channels,
            publishing_frequency=strategy.publishing_frequency,
        )

    async def get_recommendations(
        self,
        session: AsyncSession,
        current_user: User,
        project_id: str,
    ) -> AIRecommendationResponse:
        """Return optimization recommendations."""

        strategy = await self._get_or_generate(session, current_user, project_id)
        return AIRecommendationResponse(
            project_id=project_id,
            recommendations=strategy.recommendations,
            optimization_mode=strategy.optimization_mode,
        )

    async def _get_or_generate(
        self,
        session: AsyncSession,
        current_user: User,
        project_id: str,
    ) -> ProjectStrategy:
        await ensure_project_access(session, project_id, current_user)
        strategy = await session.scalar(
            select(ProjectStrategy).where(ProjectStrategy.project_id == project_id)
        )
        if strategy is None:
            strategy = await self.generate(session, current_user, project_id)
        return strategy
