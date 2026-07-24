from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db_session
from backend.app.db.user import User
from backend.app.modules.content_materials.schemas import (
    ContentGenerateRequest,
    ContentItemResponse,
    ContentSaveRequest,
)
from backend.app.modules.content_materials.service import ContentMaterialsService

router = APIRouter(prefix="/content", tags=["content"])
content_materials_service = ContentMaterialsService()


@router.post("/generate")
async def generate_content(
    payload: ContentGenerateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    return await content_materials_service.generate_content(session, current_user, payload)


@router.get("/materials", response_model=list[ContentItemResponse])
async def list_materials(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    return await content_materials_service.list_materials(session, current_user)


@router.post("/materials", response_model=ContentItemResponse, status_code=status.HTTP_201_CREATED)
async def create_material(
    payload: ContentSaveRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    return await content_materials_service.create_material(session, current_user, payload)
