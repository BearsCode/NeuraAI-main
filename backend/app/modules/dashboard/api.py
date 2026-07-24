from __future__ import annotations

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db_session
from backend.app.db.user import User
from backend.app.modules.dashboard.schemas import DashboardResponse
from backend.app.modules.dashboard.service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
service = DashboardService()


@router.get("/projects/{project_id}", response_model=DashboardResponse)
async def get_dashboard(
    project_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> DashboardResponse:
    return await service.get_dashboard(session, current_user, x_tenant_id, project_id)
