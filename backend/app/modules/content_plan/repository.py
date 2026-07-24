from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.content_item import ContentItem
from backend.app.db.content_plan import ContentPlan
from backend.app.db.content_version import ContentVersion


class ContentPlanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_plan(self, plan: ContentPlan) -> ContentPlan:
        self.session.add(plan)
        await self.session.flush()
        return plan

    async def create_item(self, item: ContentItem) -> ContentItem:
        self.session.add(item)
        await self.session.flush()
        return item

    async def create_version(self, version: ContentVersion) -> ContentVersion:
        self.session.add(version)
        await self.session.flush()
        return version

    async def list_plan_items(self, plan_id: str) -> list[ContentItem]:
        return list(
            (
                await self.session.scalars(
                    select(ContentItem)
                    .where(ContentItem.plan_id == plan_id)
                    .order_by(ContentItem.publish_date, ContentItem.publish_time)
                )
            ).all()
        )

    async def get_latest_plan(self, tenant_id: str, project_id: str) -> ContentPlan | None:
        return await self.session.scalar(
            select(ContentPlan)
            .where(ContentPlan.tenant_id == tenant_id, ContentPlan.project_id == project_id)
            .order_by(ContentPlan.created_at.desc())
        )

    async def get_content_item(self, tenant_id: str, content_item_id: str) -> ContentItem | None:
        return await self.session.scalar(
            select(ContentItem).where(
                ContentItem.tenant_id == tenant_id,
                ContentItem.id == content_item_id,
            )
        )
