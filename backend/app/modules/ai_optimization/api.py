from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import execute_idempotent, get_current_user, require_idempotency_header
from backend.app.core.database import get_db_session
from backend.app.db.user import User
from backend.app.modules.ai_optimization.schemas import (
    OptimizationRecommendationResponse,
    TriggerOptimizationRequest,
)
from backend.app.modules.ai_optimization.service import AIOptimizationService

router = APIRouter(prefix="/ai-optimization", tags=["ai_optimization"])
service = AIOptimizationService()


@router.post("/projects/{project_id}/run", response_model=OptimizationRecommendationResponse)
async def trigger(
    project_id: str,
    payload: TriggerOptimizationRequest,
    request: Request,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    idempotency_key: str = Depends(require_idempotency_header),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> OptimizationRecommendationResponse:
    return await execute_idempotent(
        request=request,
        session=session,
        current_user=current_user,
        tenant_id=x_tenant_id,
        idempotency_key=idempotency_key,
        payload=payload,
        response_model=OptimizationRecommendationResponse,
        operation=lambda: service.trigger(session, current_user, x_tenant_id, project_id, payload.reason),
    )


@router.get("/projects/{project_id}", response_model=list[OptimizationRecommendationResponse])
async def list_recommendations(
    project_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[OptimizationRecommendationResponse]:
    return await service.list_recommendations(session, current_user, x_tenant_id, project_id)
