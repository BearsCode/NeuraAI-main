from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import execute_idempotent, get_current_user, require_idempotency_header
from backend.app.core.database import get_db_session
from backend.app.db.user import User
from backend.app.modules.content_plan.schemas import (
    ContentPlanResponse,
    ContentVersionResponse,
    GenerateContentPlanRequest,
    GenerateContentVersionRequest,
)
from backend.app.modules.content_plan.service import ContentPlanService

router = APIRouter(prefix="/content-plans", tags=["content_plan"])
service = ContentPlanService()


@router.post("/projects/{project_id}", response_model=ContentPlanResponse)
async def generate_content_plan(
    project_id: str,
    payload: GenerateContentPlanRequest,
    request: Request,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    idempotency_key: str = Depends(require_idempotency_header),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ContentPlanResponse:
    return await execute_idempotent(
        request=request,
        session=session,
        current_user=current_user,
        tenant_id=x_tenant_id,
        idempotency_key=idempotency_key,
        payload=payload,
        response_model=ContentPlanResponse,
        operation=lambda: service.generate_plan(session, current_user, x_tenant_id, project_id, payload),
    )


@router.get("/projects/{project_id}", response_model=ContentPlanResponse)
async def get_latest_plan(
    project_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ContentPlanResponse:
    return await service.get_latest_plan(session, current_user, x_tenant_id, project_id)


@router.post("/projects/{project_id}/items/{content_item_id}/versions", response_model=ContentVersionResponse)
async def generate_version(
    project_id: str,
    content_item_id: str,
    payload: GenerateContentVersionRequest,
    request: Request,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    idempotency_key: str = Depends(require_idempotency_header),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ContentVersionResponse:
    return await execute_idempotent(
        request=request,
        session=session,
        current_user=current_user,
        tenant_id=x_tenant_id,
        idempotency_key=idempotency_key,
        payload=payload,
        response_model=ContentVersionResponse,
        operation=lambda: service.generate_version(
            session,
            current_user,
            x_tenant_id,
            project_id,
            content_item_id,
            payload,
        ),
    )
