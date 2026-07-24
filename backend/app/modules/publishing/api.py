from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import execute_idempotent, get_current_user, require_idempotency_header
from backend.app.core.database import get_db_session
from backend.app.db.user import User
from backend.app.modules.publishing.schemas import CreatePublicationRequest, PublicationResponse
from backend.app.modules.publishing.service import PublishingService

router = APIRouter(prefix="/publishing", tags=["publishing"])
service = PublishingService()


@router.post("/projects/{project_id}/publications", response_model=PublicationResponse)
async def create_publication(
    project_id: str,
    payload: CreatePublicationRequest,
    request: Request,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    idempotency_key: str = Depends(require_idempotency_header),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> PublicationResponse:
    return await execute_idempotent(
        request=request,
        session=session,
        current_user=current_user,
        tenant_id=x_tenant_id,
        idempotency_key=idempotency_key,
        payload=payload,
        response_model=PublicationResponse,
        operation=lambda: service.create_publication(session, current_user, x_tenant_id, project_id, payload),
    )


@router.get("/projects/{project_id}/publications", response_model=list[PublicationResponse])
async def list_publications(
    project_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[PublicationResponse]:
    return await service.list_publications(session, current_user, x_tenant_id, project_id)


@router.get("/publications/{publication_id}", response_model=PublicationResponse)
async def get_publication(
    publication_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> PublicationResponse:
    return await service.get_publication(session, current_user, x_tenant_id, publication_id)
