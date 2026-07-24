from __future__ import annotations

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db_session
from backend.app.db.user import User
from backend.app.services_internal.business_memory import BusinessMemoryService

router = APIRouter(prefix="/business-memory", tags=["business_memory"])
service = BusinessMemoryService()


@router.get("/projects/{project_id}/full-context")
async def get_full_context(
    project_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await service.get_full_context(session, x_tenant_id, project_id)


@router.get("/projects/{project_id}/company-profile")
async def get_company_profile(
    project_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await service.get_company_profile(session, x_tenant_id, project_id)


@router.get("/projects/{project_id}/preferences")
async def get_preferences(
    project_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await service.get_preference_model(session, x_tenant_id, project_id)


@router.get("/projects/{project_id}/analytics")
async def get_analytics(
    project_id: str,
    days: int = 30,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await service.get_analytics(session, x_tenant_id, project_id, days)


@router.get("/projects/{project_id}/topics")
async def get_topic_model(
    project_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await service.get_topic_model(session, x_tenant_id, project_id)


@router.get("/projects/{project_id}/publication-history")
async def get_publication_history(
    project_id: str,
    limit: int = 50,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await service.get_publication_history(session, x_tenant_id, project_id, limit)


@router.get("/projects/{project_id}/retail-catalog")
async def get_retail_catalog(
    project_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await service.get_retail_catalog(session, x_tenant_id, project_id)


class StoreMemoryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    memory_type: str
    title: str
    content: dict = {}
    source: str | None = None
    confidence: float | None = None


@router.post("/projects/{project_id}/store")
async def store_memory(
    project_id: str,
    payload: StoreMemoryRequest,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    memory = await service.store_memory(
        session, x_tenant_id, project_id,
        payload.memory_type, payload.title, payload.content,
        payload.source, payload.confidence,
    )
    return {
        "id": memory.id,
        "memory_type": memory.memory_type,
        "title": memory.title,
        "created_at": memory.created_at.isoformat(),
    }
