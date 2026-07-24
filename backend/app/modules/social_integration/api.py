from __future__ import annotations
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.core.configs import settings
from backend.app.core.database import get_db_session
from backend.app.db.user import User
from backend.app.modules.social_integration.schemas import (
    SocialAuthorizeResponse,
    SocialConnectRequest,
    SocialConnectionResponse,
    SocialOAuthCallbackRequest,
    SocialUpdateRequest,
)
from backend.app.modules.social_integration.service import SocialIntegrationService

router = APIRouter(prefix="/social", tags=["social_integration"])
service = SocialIntegrationService()


def validate_redirect_uri(uri: str) -> str:
    allowed_origins = [settings.web.public_base_url]
    try:
        parsed = urlparse(uri)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError
        normalized = f"{parsed.scheme}://{parsed.netloc}"
        if parsed.scheme != "https" and not settings.app.is_local:
            raise ValueError
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid redirect_uri")
    if normalized not in allowed_origins:
        raise HTTPException(status_code=400, detail="Invalid redirect_uri")
    return uri


@router.get("/projects/{project_id}/connections", response_model=list[SocialConnectionResponse])
async def list_connections(
    project_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[SocialConnectionResponse]:
    return await service.list_connections(session, current_user, x_tenant_id, project_id)


@router.get("/projects/{project_id}/oauth/{platform}/authorize", response_model=SocialAuthorizeResponse)
async def authorize(
    project_id: str,
    platform: str,
    redirect_uri: str = Query(...),
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SocialAuthorizeResponse:
    validated_redirect_uri = validate_redirect_uri(redirect_uri)
    return await service.begin_authorization(
        session,
        current_user,
        x_tenant_id,
        project_id,
        platform,
        validated_redirect_uri,
    )


@router.post("/projects/{project_id}/oauth/{platform}/callback", response_model=SocialConnectionResponse)
async def oauth_callback(
    project_id: str,
    platform: str,
    payload: SocialOAuthCallbackRequest,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SocialConnectionResponse:
    return await service.complete_authorization(
        session,
        current_user,
        x_tenant_id,
        project_id,
        platform,
        payload,
    )


@router.post("/projects/{project_id}/connections", response_model=SocialConnectionResponse)
async def connect(
    project_id: str,
    payload: SocialConnectRequest,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SocialConnectionResponse:
    return await service.connect(session, current_user, x_tenant_id, project_id, payload)


@router.patch("/projects/{project_id}/connections/{platform}", response_model=SocialConnectionResponse)
async def update(
    project_id: str,
    platform: str,
    payload: SocialUpdateRequest,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SocialConnectionResponse:
    return await service.update(session, current_user, x_tenant_id, project_id, platform, payload)


@router.delete("/projects/{project_id}/connections/{platform}", response_model=SocialConnectionResponse)
async def disconnect(
    project_id: str,
    platform: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SocialConnectionResponse:
    return await service.disconnect(session, current_user, x_tenant_id, project_id, platform)
