from __future__ import annotations

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db_session
from backend.app.db.user import User
from backend.app.modules.ai_avatar.service import AvatarService

router = APIRouter(prefix="/avatar", tags=["ai_avatar"])
service = AvatarService()


class CreatePhotoAvatarRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    photo_urls: list[str] = []


class CreateVideoAvatarRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    video_url: str


@router.post("/photo/create")
async def create_photo_avatar(
    payload: CreatePhotoAvatarRequest,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await service.create_photo_avatar(session, x_tenant_id, payload.photo_urls)


@router.post("/video/create")
async def create_video_avatar(
    payload: CreateVideoAvatarRequest,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await service.create_video_avatar(session, x_tenant_id, payload.video_url)


@router.get("/{avatar_id}")
async def get_avatar(
    avatar_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await service.get_avatar(session, x_tenant_id, avatar_id)


@router.get("")
async def list_avatars(
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await service.list_avatars(session, x_tenant_id)


@router.delete("/{avatar_id}")
async def delete_avatar(
    avatar_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await service.delete_avatar(session, x_tenant_id, avatar_id)


@router.get("/{avatar_id}/status")
async def get_avatar_status(
    avatar_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await service.get_training_status(session, x_tenant_id, avatar_id)
