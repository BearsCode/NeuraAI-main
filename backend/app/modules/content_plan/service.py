from __future__ import annotations


from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.configs import settings
from backend.app.db.ai_job import AIJob
from backend.app.db.content_version import ContentVersion
from backend.app.db.enums import (
    AIJobStatus,
    ContentStatus,
)
from backend.app.db.user import User
from backend.app.events.schemas import ContentPlanGeneratedEvent, EventEnvelope
from backend.app.infra.outbox import OutboxService
from backend.app.modules.access import ensure_project_access
from backend.app.modules.content_plan.repository import ContentPlanRepository
from backend.app.modules.content_plan.schemas import (
    ContentPlanItemResponse,
    ContentPlanResponse,
    ContentVersionResponse,
    GenerateContentPlanRequest,
    GenerateContentVersionRequest,
)
from backend.app.services.ai_orchestration_service import AIOrchestrationService
from backend.app.services.ai_text_service import AITextService


class ContentPlanService:
    def __init__(self) -> None:
        self.orchestration = AIOrchestrationService()

    async def generate_plan(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        project_id: str,
        payload: GenerateContentPlanRequest,
    ) -> ContentPlanResponse:
        project = await ensure_project_access(session, current_user, tenant_id, project_id)
        repository = ContentPlanRepository(session)

        latest = await repository.get_latest_plan(tenant_id, project_id)
        version = (latest.version + 1) if latest else 1
        plan, items = await self.orchestration.generate_content_plan(
            session,
            project,
            period_days=payload.period_days,
            source_mode=payload.source_mode,
            platforms=payload.platforms or ["telegram", "vk"],
            content_types=payload.content_types or ["post", "carousel"],
            version=version,
        )

        for item in items:
            await repository.create_version(
                ContentVersion(
                    tenant_id=tenant_id,
                    content_item_id=item.id,
                    version_number=1,
                    text=item.text,
                    prompt_snapshot=item.metadata_json,
                    ai_provider="orchestrated",
                    ai_model=settings.ai.provider,
                )
            )

        session.add(
            AIJob(
                tenant_id=tenant_id,
                project_id=project_id,
                job_type="content_plan_generation",
                provider=settings.ai.provider,
                model=settings.ai_model or settings.ai.provider,
                status=AIJobStatus.SUCCEEDED,
                input_payload=payload.model_dump(mode="json"),
                output_payload={"plan_id": plan.id, "items_count": len(items)},
            )
        )
        await OutboxService().enqueue(
            session,
            EventEnvelope(
                event_type="content.plan.generated",
                topic="content.plan.generated.v1",
                tenant_id=tenant_id,
                aggregate_id=plan.id,
                payload=ContentPlanGeneratedEvent(
                    tenant_id=tenant_id,
                    plan_id=plan.id,
                    project_id=project_id,
                    items_count=len(items),
                ).model_dump(mode="json"),
            ),
        )
        await session.commit()
        return await self.get_latest_plan(session, current_user, tenant_id, project_id)

    async def generate_version(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        project_id: str,
        content_item_id: str,
        payload: GenerateContentVersionRequest,
    ) -> ContentVersionResponse:
        await ensure_project_access(session, current_user, tenant_id, project_id)
        repository = ContentPlanRepository(session)
        content_item = await repository.get_content_item(tenant_id, content_item_id)
        if not content_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content item not found")

        version_number = content_item.current_version_number + 1
        system_prompt = (
            "Ты — профессиональный копирайтер для соцсетей. "
            "Напиши текст публикации по заданной теме. "
            "Используй русский язык. Без лишних пояснений."
        )
        user_prompt = (
            f"Тема: {payload.topic}\n"
            f"Платформа: {payload.platform}\n"
            f"Тип контента: {content_item.content_type.value if hasattr(content_item, 'content_type') else 'post'}\n"
        )
        if payload.prompt_context:
            user_prompt += f"Контекст: {payload.prompt_context}\n"

        svc = AITextService()
        try:
            generated_text = await svc.generate_text(system_prompt, user_prompt, temperature=0.8)
        except Exception:
            generated_text = (
                f"{payload.topic}\n\n"
                f"Platform: {payload.platform}\n"
                f"AI-маркетинг — ваш ключ к росту.\n"
                f"Попробуйте Нейру уже сегодня."
            )

        version = await repository.create_version(
            ContentVersion(
                tenant_id=tenant_id,
                content_item_id=content_item.id,
                version_number=version_number,
                text=generated_text,
                prompt_snapshot=payload.prompt_context,
                ai_provider=settings.ai.provider,
                ai_model=settings.ai.openai.model or "gpt-4o-mini",
            )
        )
        content_item.text = generated_text
        content_item.current_version_number = version_number
        content_item.status = ContentStatus.READY
        await session.commit()
        return ContentVersionResponse(
            version_id=version.id,
            tenant_id=tenant_id,
            project_id=project_id,
            content_item_id=content_item.id,
            version_number=version.version_number,
            text=version.text,
            ai_provider=version.ai_provider,
            ai_model=version.ai_model,
            created_at=version.created_at,
        )

    async def get_latest_plan(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        project_id: str,
    ) -> ContentPlanResponse:
        await ensure_project_access(session, current_user, tenant_id, project_id)
        repository = ContentPlanRepository(session)
        plan = await repository.get_latest_plan(tenant_id, project_id)
        if not plan:
            return ContentPlanResponse(
                plan_id="",
                tenant_id=tenant_id,
                project_id=project_id,
                version=0,
                period_days=0,
                source_mode="mixed",
                status="empty",
                items=[],
            )
        items = await repository.list_plan_items(plan.id)
        return ContentPlanResponse(
            plan_id=plan.id,
            tenant_id=tenant_id,
            project_id=project_id,
            version=plan.version,
            period_days=plan.period_days,
            source_mode=plan.source_mode.value,
            status=plan.status,
            items=[
                ContentPlanItemResponse(
                    content_item_id=item.id,
                    platform=item.platform.value,
                    content_type=item.content_type.value,
                    publish_at=f"{item.publish_date.isoformat()}T{item.publish_time.strftime('%H:%M')}:00",
                    status=item.status.value,
                    text=item.text,
                )
                for item in items
            ],
        )
