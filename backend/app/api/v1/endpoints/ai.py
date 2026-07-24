from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db_session
from backend.app.db.user import User
from backend.app.schemas.ai import (
    AIAnalysisResponse,
    AIRecommendationResponse,
    StrategyResponse,
)
from backend.app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["ai"])
ai_service = AIService()


@router.post("/{project_id}/generate", response_model=StrategyResponse)
async def generate_strategy(
    project_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> StrategyResponse:
    await ai_service.generate(session, current_user, project_id)
    return await ai_service.get_strategy(session, current_user, project_id)


@router.get("/{project_id}/analysis", response_model=AIAnalysisResponse)
async def get_analysis(
    project_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> AIAnalysisResponse:
    return await ai_service.get_analysis(session, current_user, project_id)


@router.get("/{project_id}/strategy", response_model=StrategyResponse)
async def get_strategy(
    project_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> StrategyResponse:
    return await ai_service.get_strategy(session, current_user, project_id)


@router.get("/{project_id}/recommendations", response_model=AIRecommendationResponse)
async def get_recommendations(
    project_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> AIRecommendationResponse:
    return await ai_service.get_recommendations(session, current_user, project_id)
