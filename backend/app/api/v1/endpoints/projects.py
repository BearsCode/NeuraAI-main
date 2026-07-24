from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db_session
from backend.app.db.user import User
from backend.app.schemas.projects import (
    BusinessOnboardingRequest,
    ProjectResponse,
    ProjectSummaryResponse,
)
from backend.app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])
project_service = ProjectService()


@router.get("", response_model=list[ProjectSummaryResponse])
async def list_projects(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[ProjectSummaryResponse]:
    return await project_service.list_projects(session, current_user)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: BusinessOnboardingRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ProjectResponse:
    return await project_service.create_project(session, current_user, payload)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ProjectResponse:
    return await project_service.get_project(session, current_user, project_id)
