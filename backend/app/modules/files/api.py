from __future__ import annotations

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db_session
from backend.app.db.user import User
from backend.app.modules.files.schemas import (
    CompleteUploadRequest,
    CreateUploadUrlRequest,
    FileAssetResponse,
    UploadUrlResponse,
)
from backend.app.modules.files.service import FileService

router = APIRouter(prefix="/files", tags=["files"])
service = FileService()


@router.post("/projects/{project_id}/upload-url", response_model=UploadUrlResponse)
async def create_upload_url(
    project_id: str,
    payload: CreateUploadUrlRequest,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> UploadUrlResponse:
    return await service.create_upload_url(
        session=session,
        current_user=current_user,
        tenant_id=x_tenant_id,
        project_id=project_id,
        file_name=payload.file_name,
        content_type=payload.content_type,
    )


@router.post("/projects/{project_id}/complete", response_model=FileAssetResponse)
async def complete_upload(
    project_id: str,
    payload: CompleteUploadRequest,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> FileAssetResponse:
    return await service.complete_upload(session, current_user, x_tenant_id, project_id, payload)


@router.get("/projects/{project_id}", response_model=list[FileAssetResponse])
async def list_assets(
    project_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[FileAssetResponse]:
    return await service.list_assets(session, current_user, x_tenant_id, project_id)
