from datetime import UTC, datetime, time, timedelta
import asyncio
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.configs import settings
from backend.app.integrations.ai_client import AIClient
from backend.app.integrations.storage_client import StorageClient
from backend.app.db.asset import Asset
from backend.app.db.content_item import ContentItem
from backend.app.db.content_plan import ContentPlan
from backend.app.db.enums import (
    AssetType,
    ContentSourceMode,
    ContentStatus,
    ContentType,
    IntegrationPlatform,
    PublicationStatus,
)
from backend.app.db.project_strategy import ProjectStrategy
from backend.app.db.publication import Publication
from backend.app.db.user import User

ai_client = AIClient()
storage_client = StorageClient()
from backend.app.observability.logging import get_logger
from backend.app.schemas.content import (
    ContentPlanGenerateRequest,
    ContentPlanResponse,
    GeneratePostRequest,
    GeneratedContentResponse,
    PlannedContentItem,
    PublicationResponse,
)
from backend.app.services.project_service import ensure_project_access

logger = get_logger(__name__)


class ContentService:
    async def generate_plan(
        self,
        session: AsyncSession,
        current_user: User,
        project_id: str,
        payload: ContentPlanGenerateRequest,
    ) -> ContentPlanResponse:
        project = await ensure_project_access(session, project_id, current_user)
        strategy = await session.scalar(
            select(ProjectStrategy).where(ProjectStrategy.project_id == project.id)
        )

        platforms = payload.platforms or (strategy.channels if strategy and strategy.channels else ["telegram", "vk"])
        content_types = payload.content_types or ["post", "carousel", "story"]

        plan = ContentPlan(
            tenant_id=project.tenant_id,
            project_id=project.id,
            period_days=payload.period_days,
            source_mode=ContentSourceMode(payload.source_mode),
            status="generated",
        )
        session.add(plan)
        await session.flush()

        items: list[ContentItem] = []
        tasks = []
        for index in range(payload.period_days):
            platform_name = platforms[index % len(platforms)]
            content_type_name = content_types[index % len(content_types)]
            topic = f"Content idea {index + 1} for {platform_name} focusing on {content_type_name}."
            tasks.append(ai_client.generate_post_text(project, topic, platform_name))

        generated_texts = await asyncio.gather(*tasks, return_exceptions=True)

        for index in range(payload.period_days):
            platform_name = platforms[index % len(platforms)]
            content_type_name = content_types[index % len(content_types)]
            publish_date = (datetime.now(UTC) + timedelta(days=index + 1)).date()
            publish_time = time(hour=10 + (index % 5), minute=0)

            text_result = generated_texts[index]
            if isinstance(text_result, Exception) or not text_result:
                post_text = (
                    f"{project.company_name}: content idea #{index + 1} for "
                    f"{platform_name} focused on {project.target_audience}."
                )
            else:
                post_text = str(text_result)

            item = ContentItem(
                tenant_id=project.tenant_id,
                project_id=project.id,
                plan_id=plan.id,
                platform=IntegrationPlatform(platform_name),
                content_type=ContentType(content_type_name),
                publish_date=publish_date,
                publish_time=publish_time,
                status=ContentStatus.DRAFT,
                text=post_text,
            )
            session.add(item)
            await session.flush()

            publication = Publication(
                tenant_id=project.tenant_id,
                project_id=project.id,
                content_item_id=item.id,
                platform=item.platform,
                scheduled_at=datetime.combine(publish_date, publish_time, UTC),
                status=PublicationStatus.PENDING_APPROVAL,
            )
            session.add(publication)
            items.append(item)

        await session.commit()
        return await self.get_plan(session, current_user, project_id)

    async def get_plan(
        self,
        session: AsyncSession,
        current_user: User,
        project_id: str,
    ) -> ContentPlanResponse:
        project = await ensure_project_access(session, project_id, current_user)
        latest_plan = await session.scalar(
            select(ContentPlan)
            .where(ContentPlan.project_id == project.id)
            .order_by(ContentPlan.created_at.desc())
        )
        if not latest_plan:
            return ContentPlanResponse(
                plan_id="",
                project_id=project.id,
                period_days=0,
                source_mode=ContentSourceMode.MIXED.value,
                status="empty",
                items=[],
            )

        plan_items = (
            await session.scalars(
                select(ContentItem)
                .where(ContentItem.plan_id == latest_plan.id)
                .order_by(ContentItem.publish_date, ContentItem.publish_time)
            )
        ).all()
        items = [
            self._to_planned_item(item)
            for item in plan_items
        ]

        return ContentPlanResponse(
            plan_id=latest_plan.id,
            project_id=project.id,
            period_days=latest_plan.period_days,
            source_mode=latest_plan.source_mode.value,
            status=latest_plan.status,
            items=items,
        )

    async def generate_post(
        self,
        session: AsyncSession,
        current_user: User,
        project_id: str,
        payload: GeneratePostRequest,
    ) -> GeneratedContentResponse:
        project = await ensure_project_access(session, project_id, current_user)
        
        post_text = await ai_client.generate_post_text(
            project,
            payload.topic_hint or "AI marketing update",
            payload.platform
        )

        content_item = ContentItem(
            tenant_id=project.tenant_id,
            project_id=project.id,
            platform=IntegrationPlatform(payload.platform),
            content_type=ContentType(payload.content_type),
            status=ContentStatus.READY,
            text=post_text,
            publish_date=(payload.scheduled_at or datetime.now(UTC)).date(),
            publish_time=(payload.scheduled_at or datetime.now(UTC)).time().replace(second=0, microsecond=0),
        )
        session.add(content_item)
        await session.flush()

        if settings.openai_api_key:
            try:
                image_prompt = (
                    f"Modern clean B2B marketing graphic for {project.company_name} in the {project.industry} industry. "
                    f"Visual style matches the topic: {payload.topic_hint or 'Business and marketing success'}."
                )
                image_bytes = await ai_client.generate_image(image_prompt)
                file_name = f"ai_gen_{uuid4().hex[:10]}.png"
                storage_uri, public_url = await storage_client.store_bytes(
                    project.id,
                    file_name,
                    "image/png",
                    image_bytes,
                )
                content_item.image_url = public_url

                asset = Asset(
                    project_id=project.id,
                    asset_type=AssetType.PHOTO,
                    file_name=file_name,
                    content_type="image/png",
                    storage_uri=storage_uri,
                    public_url=public_url,
                )
                session.add(asset)
            except Exception as exc:
                logger.warning("image_generation_failed", extra={"error": str(exc), "project_id": project.id})

        publication = Publication(
            tenant_id=project.tenant_id,
            project_id=project.id,
            content_item_id=content_item.id,
            platform=content_item.platform,
            scheduled_at=payload.scheduled_at or datetime.now(UTC) + timedelta(days=1),
            status=PublicationStatus.PENDING_APPROVAL,
        )
        session.add(publication)
        await session.commit()
        await session.refresh(content_item)
        await session.refresh(publication)

        return GeneratedContentResponse(
            content_id=content_item.id,
            project_id=project.id,
            platform=content_item.platform.value,
            content_type=content_item.content_type.value,
            caption=content_item.text,
            status=content_item.status.value,
            created_at=content_item.created_at,
            publication_id=publication.id,
        )

    async def list_generated_content(
        self,
        session: AsyncSession,
        current_user: User,
        project_id: str,
    ) -> list[GeneratedContentResponse]:
        project = await ensure_project_access(session, project_id, current_user)
        items = (
            await session.scalars(
                select(ContentItem)
                .options(selectinload(ContentItem.publication))
                .where(ContentItem.project_id == project.id)
                .order_by(ContentItem.created_at.desc())
            )
        ).all()
        return [
            GeneratedContentResponse(
                content_id=item.id,
                project_id=project.id,
                platform=item.platform.value,
                content_type=item.content_type.value,
                caption=item.text,
                status=item.status.value,
                created_at=item.created_at,
                publication_id=item.publication.id if item.publication else None,
            )
            for item in items
        ]

    async def list_publications(
        self,
        session: AsyncSession,
        current_user: User,
        project_id: str,
    ) -> list[PublicationResponse]:
        project = await ensure_project_access(session, project_id, current_user)
        publications = (
            await session.scalars(
                select(Publication)
                .where(Publication.project_id == project.id)
                .order_by(Publication.scheduled_at)
            )
        ).all()
        return [
            PublicationResponse(
                publication_id=publication.id,
                project_id=project.id,
                content_item_id=publication.content_item_id,
                platform=publication.platform.value,
                scheduled_at=publication.scheduled_at,
                status=publication.status.value,
                retry_count=publication.retry_count,
                error_message=publication.last_error_message,
            )
            for publication in publications
        ]

    def _to_planned_item(self, item: ContentItem) -> PlannedContentItem:
        return PlannedContentItem(
            content_item_id=item.id,
            date=item.publish_date,
            time=item.publish_time.strftime("%H:%M"),
            platform=item.platform.value,
            content_type=item.content_type.value,
            status=item.status.value,
            text=item.text,
            image_url=item.image_url,
            video_url=item.video_url,
        )
