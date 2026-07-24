from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db_session
from backend.app.db.user import User
from backend.app.modules.analytics.schemas import AnalyticsDashboardResponse, AnalyticsOverviewResponse
from backend.app.modules.analytics.service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])
service = AnalyticsService()


@router.get("/dashboard", response_model=AnalyticsDashboardResponse)
async def get_dashboard(
    project_id: str = Query(..., min_length=1),
    days: int = Query(default=7, ge=1, le=30),
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> AnalyticsDashboardResponse:
    return await service.get_dashboard(session, current_user, x_tenant_id, project_id, days=days)


@router.get("/projects/{project_id}", response_model=AnalyticsOverviewResponse)
async def get_analytics(
    project_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> AnalyticsOverviewResponse:
    return await service.get_overview(session, current_user, x_tenant_id, project_id)
