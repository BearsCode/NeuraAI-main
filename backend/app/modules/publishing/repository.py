from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.db.content_item import ContentItem
from backend.app.db.publication import Publication
from backend.app.db.publication_attempt import PublicationAttempt
from backend.app.db.publication_target import PublicationTarget
from backend.app.db.social_integration import SocialIntegration


class PublishingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_content_item(self, tenant_id: str, content_item_id: str) -> ContentItem | None:
        return await self.session.scalar(
            select(ContentItem).where(
                ContentItem.tenant_id == tenant_id,
                ContentItem.id == content_item_id,
            )
        )

    async def list_integrations_for_ids(
        self,
        tenant_id: str,
        project_id: str,
        integration_ids: list[str],
    ) -> list[SocialIntegration]:
        query = select(SocialIntegration).where(
            SocialIntegration.tenant_id == tenant_id,
            SocialIntegration.project_id == project_id,
        )
        if integration_ids:
            query = query.where(SocialIntegration.id.in_(integration_ids))
        return list((await self.session.scalars(query)).all())

    async def create_publication(self, publication: Publication) -> Publication:
        self.session.add(publication)
        await self.session.flush()
        return publication

    async def create_target(self, target: PublicationTarget) -> PublicationTarget:
        self.session.add(target)
        await self.session.flush()
        return target

    async def create_attempt(self, attempt: PublicationAttempt) -> PublicationAttempt:
        self.session.add(attempt)
        await self.session.flush()
        return attempt

    async def list_publications(self, tenant_id: str, project_id: str) -> list[Publication]:
        return list(
            (
                await self.session.scalars(
                    select(Publication)
                    .options(selectinload(Publication.targets))
                    .where(Publication.tenant_id == tenant_id, Publication.project_id == project_id)
                    .order_by(Publication.created_at.desc())
                )
            ).all()
        )

    async def get_publication(self, tenant_id: str, publication_id: str) -> Publication | None:
        return await self.session.scalar(
            select(Publication)
            .options(selectinload(Publication.targets))
            .where(Publication.tenant_id == tenant_id, Publication.id == publication_id)
        )
