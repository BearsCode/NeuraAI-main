from __future__ import annotations

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db_session
from backend.app.db.user import User
from backend.app.modules.ai_retail.service import RetailService

router = APIRouter(prefix="/retail", tags=["ai_retail"])
service = RetailService()


class ConnectSystemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_system: str
    credentials: dict = {}


@router.post("/projects/{project_id}/connect")
async def connect_retail_system(
    project_id: str,
    payload: ConnectSystemRequest,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await service.connect_system(session, x_tenant_id, project_id, payload.source_system, payload.credentials)


@router.post("/projects/{project_id}/sync")
async def sync_catalog(
    project_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await service.sync_catalog(session, x_tenant_id, project_id)


@router.get("/projects/{project_id}/products")
async def list_products(
    project_id: str,
    category: str | None = None,
    on_sale: bool | None = None,
    in_stock: bool | None = None,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await service.list_products(session, x_tenant_id, project_id, category, on_sale, in_stock)


@router.get("/projects/{project_id}/dashboard")
async def retail_dashboard(
    project_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await service.get_dashboard(session, x_tenant_id, project_id)


@router.get("/projects/{project_id}/sync-history")
async def sync_history(
    project_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await service.get_sync_history(session, x_tenant_id, project_id)
