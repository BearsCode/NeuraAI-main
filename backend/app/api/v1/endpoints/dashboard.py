from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db_session
from backend.app.db.user import User
from backend.app.schemas.dashboard import DashboardResponse
from backend.app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
dashboard_service = DashboardService()


@router.get("/{project_id}", response_model=DashboardResponse)
async def get_dashboard(
    project_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> DashboardResponse:
    return await dashboard_service.get_dashboard(session, current_user, project_id)
