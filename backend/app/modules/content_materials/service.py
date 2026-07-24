from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.content_item import ContentItem
from backend.app.db.enums import ContentStatus, ContentType, IntegrationPlatform
from backend.app.db.project import Project
from backend.app.db.tenant import Tenant
from backend.app.db.tenant_membership import TenantMembership
from backend.app.db.user import User
from backend.app.observability.logging import get_logger
from backend.app.services.ai_text_service import AITextService
from backend.app.modules.content_materials.schemas import (
    ContentGenerateRequest,
    ContentItemResponse,
    ContentSaveRequest,
)

logger = get_logger(__name__)


class ContentMaterialsService:
    async def _get_primary_context(
        self,
        session: AsyncSession,
        current_user: User,
        required: bool = True,
    ) -> tuple[Tenant, Project] | None:
        query = (
            select(Tenant, Project)
            .join(TenantMembership, TenantMembership.tenant_id == Tenant.id)
            .join(Project, Project.tenant_id == Tenant.id)
            .where(TenantMembership.user_id == current_user.id)
            .order_by(TenantMembership.is_primary.desc(), Project.created_at.desc())
        )
        row = (await session.execute(query)).first()
        if row is None:
            if required:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Business profile not found. Создайте компанию в настройках."
                )
            return None
        return row[0], row[1]

    async def generate_content(
        self,
        session: AsyncSession,
        current_user: User,
        payload: ContentGenerateRequest,
    ) -> dict[str, str]:
        tenant, project = await self._get_primary_context(session, current_user)

        system_prompt = (
            "Ты — профессиональный копирайтер для соцсетей. "
            "Напиши текст публикации по запросу пользователя. "
            "Учитывай платформу и формат контента. "
            "Ответ дай на русском языке, без лишних пояснений."
        )

        user_prompt = payload.prompt
        if payload.platform:
            user_prompt += f"\nПлатформа: {payload.platform}"
        if payload.content_type:
            user_prompt += f"\nФормат: {payload.content_type}"
        if payload.tone:
            user_prompt += f"\nТон: {payload.tone}"
        if payload.topic:
            user_prompt += f"\nТема: {payload.topic}"
        if payload.keywords:
            user_prompt += f"\nКлючевые слова: {payload.keywords}"

        svc = AITextService()
        text = await svc.generate_text(system_prompt, user_prompt)

        item = ContentItem(
            tenant_id=tenant.id,
            project_id=project.id,
            platform=IntegrationPlatform(payload.platform) if payload.platform else IntegrationPlatform.TELEGRAM,
            content_type=ContentType(payload.content_type) if payload.content_type else ContentType.POST,
            status=ContentStatus.GENERATED,
            text=text,
            title=payload.prompt[:80],
        )
        session.add(item)
        await session.flush()

        return {"text": text, "content_item_id": str(item.id)}

    async def list_materials(
        self,
        session: AsyncSession,
        current_user: User,
    ) -> list[ContentItemResponse]:
        tenant, project = await self._get_primary_context(session, current_user)
        items = (
            await session.scalars(
                select(ContentItem)
                .where(
                    ContentItem.tenant_id == tenant.id,
                    ContentItem.project_id == project.id,
                )
                .order_by(ContentItem.created_at.desc())
            )
        ).all()
        return [
            ContentItemResponse(
                content_item_id=str(item.id),
                platform=item.platform.value if item.platform else None,
                content_type=item.content_type.value if item.content_type else "post",
                title=item.title or "",
                text=item.text or "",
                status=item.status.value if item.status else "draft",
                created_at=item.created_at,
            )
            for item in items
        ]

    async def create_material(
        self,
        session: AsyncSession,
        current_user: User,
        payload: ContentSaveRequest,
    ) -> ContentItemResponse:
        tenant, project = await self._get_primary_context(session, current_user)
        item = ContentItem(
            tenant_id=tenant.id,
            project_id=project.id,
            platform=IntegrationPlatform(payload.platform) if payload.platform else IntegrationPlatform.TELEGRAM,
            content_type=ContentType(payload.content_type) if payload.content_type else ContentType.POST,
            status=ContentStatus.DRAFT,
            text=payload.text,
            title=payload.title or payload.text[:80],
        )
        session.add(item)
        await session.flush()
        return ContentItemResponse(
            content_item_id=str(item.id),
            platform=item.platform.value if item.platform else None,
            content_type=item.content_type.value if item.content_type else "post",
            title=item.title or "",
            text=item.text or "",
            status=item.status.value if item.status else "draft",
            created_at=item.created_at,
        )
