from __future__ import annotations

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db_session
from backend.app.db.user import User
from backend.app.modules.approval_center.schemas import (
    ApprovalDecisionRequest,
    ApprovalPolicyResponse,
    ApprovalPolicyUpdateRequest,
    ApprovalQueueItemResponse,
    PostponeRequest,
)
from backend.app.modules.approval_center.service import ApprovalCenterService
from backend.app.modules.publishing.schemas import PublicationResponse

router = APIRouter(prefix="/approval", tags=["approval_center"])
service = ApprovalCenterService()


@router.get("/projects/{project_id}/policy", response_model=ApprovalPolicyResponse)
async def get_policy(
    project_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApprovalPolicyResponse:
    return await service.get_policy(session, current_user, x_tenant_id, project_id)


@router.patch("/projects/{project_id}/policy", response_model=ApprovalPolicyResponse)
async def update_policy(
    project_id: str,
    payload: ApprovalPolicyUpdateRequest,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApprovalPolicyResponse:
    return await service.update_policy(session, current_user, x_tenant_id, project_id, payload)


@router.get("/projects/{project_id}/queue", response_model=list[ApprovalQueueItemResponse])
async def get_queue(
    project_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[ApprovalQueueItemResponse]:
    return await service.get_queue(session, current_user, x_tenant_id, project_id)


@router.post("/publications/{publication_id}/approve", response_model=PublicationResponse)
async def approve(
    publication_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> PublicationResponse:
    return await service.approve(session, current_user, x_tenant_id, publication_id)


@router.post("/publications/{publication_id}/reject", response_model=PublicationResponse)
async def reject(
    publication_id: str,
    payload: ApprovalDecisionRequest,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> PublicationResponse:
    return await service.reject(session, current_user, x_tenant_id, publication_id, payload.comment)


@router.post("/publications/{publication_id}/postpone", response_model=PublicationResponse)
async def postpone(
    publication_id: str,
    payload: PostponeRequest,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> PublicationResponse:
    return await service.postpone(session, current_user, x_tenant_id, publication_id, payload.scheduled_at)
