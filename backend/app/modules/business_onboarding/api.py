from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import execute_idempotent, get_current_user, require_idempotency_header
from backend.app.core.database import get_db_session
from backend.app.db.user import User
from backend.app.modules.business_onboarding.schemas import (
    AIAnalysisJobResponse,
    AIAnalysisRequest,
    BusinessResponse,
    CreateBusinessRequest,
)
from backend.app.modules.business_onboarding.service import BusinessOnboardingService

router = APIRouter(prefix="/onboarding", tags=["business_onboarding"])
service = BusinessOnboardingService()


@router.post("/businesses", response_model=BusinessResponse)
async def create_business(
    payload: CreateBusinessRequest,
    request: Request,
    idempotency_key: str = Depends(require_idempotency_header),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> BusinessResponse:
    return await execute_idempotent(
        request=request,
        session=session,
        current_user=current_user,
        tenant_id=current_user.id,
        idempotency_key=idempotency_key,
        payload=payload,
        response_model=BusinessResponse,
        operation=lambda: service.create_business(session, current_user, payload),
    )


@router.post("/projects/{project_id}/ai-analysis", response_model=AIAnalysisJobResponse)
async def request_ai_analysis(
    project_id: str,
    payload: AIAnalysisRequest,
    request: Request,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
    idempotency_key: str = Depends(require_idempotency_header),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> AIAnalysisJobResponse:
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-ID header is required")
    return await execute_idempotent(
        request=request,
        session=session,
        current_user=current_user,
        tenant_id=x_tenant_id,
        idempotency_key=idempotency_key,
        payload=payload,
        response_model=AIAnalysisJobResponse,
        operation=lambda: service.request_ai_analysis(
            session,
            current_user,
            tenant_id=x_tenant_id,
            project_id=project_id,
            task_type=payload.task_type,
        ),
    )
