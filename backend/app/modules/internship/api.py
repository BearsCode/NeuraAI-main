from __future__ import annotations

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db_session
from backend.app.db.user import User
from backend.app.modules.internship.service import InternshipService

router = APIRouter(prefix="/internship", tags=["internship"])
service = InternshipService()


class EvaluatePostRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content_item_id: str
    action: str
    comment: str | None = None
    context: dict = {}


class SetModeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: str


@router.post("/projects/{project_id}/start")
async def start_internship(
    project_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await service.start_internship(session, x_tenant_id, project_id)


@router.get("/projects/{project_id}/status")
async def get_internship_status(
    project_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await service.get_status(session, x_tenant_id, project_id)


@router.post("/projects/{project_id}/evaluate")
async def evaluate_post(
    project_id: str,
    payload: EvaluatePostRequest,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await service.evaluate_post(session, x_tenant_id, project_id, payload)


@router.post("/projects/{project_id}/set-mode")
async def set_operation_mode(
    project_id: str,
    payload: SetModeRequest,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await service.set_mode(session, x_tenant_id, project_id, payload.mode)


@router.get("/projects/{project_id}/report")
async def get_internship_report(
    project_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await service.get_report(session, x_tenant_id, project_id)


@router.post("/projects/{project_id}/advance-day")
async def advance_day(
    project_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await service.advance_day(session, x_tenant_id, project_id)
