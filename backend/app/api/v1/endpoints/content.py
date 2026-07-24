from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db_session
from backend.app.db.user import User
from backend.app.schemas.content import (
    ContentPlanGenerateRequest,
    ContentPlanResponse,
    GeneratePostRequest,
    GeneratedContentResponse,
    PublicationResponse,
)
from backend.app.services.content_service import ContentService

router = APIRouter(prefix="/content", tags=["content"])
content_service = ContentService()


@router.get("/{project_id}/plan", response_model=ContentPlanResponse)
async def get_content_plan(
    project_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ContentPlanResponse:
    return await content_service.get_plan(session, current_user, project_id)


@router.post("/{project_id}/plan/generate", response_model=ContentPlanResponse, status_code=status.HTTP_201_CREATED)
async def generate_content_plan(
    project_id: str,
    payload: ContentPlanGenerateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ContentPlanResponse:
    return await content_service.generate_plan(session, current_user, project_id, payload)


@router.get("/{project_id}/generated", response_model=list[GeneratedContentResponse])
async def list_generated_content(
    project_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[GeneratedContentResponse]:
    return await content_service.list_generated_content(session, current_user, project_id)


@router.post("/{project_id}/generated", response_model=GeneratedContentResponse, status_code=status.HTTP_201_CREATED)
async def generate_post(
    project_id: str,
    payload: GeneratePostRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> GeneratedContentResponse:
    return await content_service.generate_post(session, current_user, project_id, payload)


@router.get("/{project_id}/publications", response_model=list[PublicationResponse])
async def list_publications(
    project_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[PublicationResponse]:
    return await content_service.list_publications(session, current_user, project_id)
