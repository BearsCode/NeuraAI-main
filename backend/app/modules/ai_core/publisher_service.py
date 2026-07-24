from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.content_item import ContentItem
from backend.app.db.enums import IntegrationPlatform, PublicationStatus, PublicationTargetStatus
from backend.app.db.publication import Publication
from backend.app.db.publication_attempt import PublicationAttempt
from backend.app.db.publication_target import PublicationTarget
from backend.app.db.social_integration import SocialIntegration
from backend.app.integrations.social_adapters import PublishPayload, SocialAdapterRegistry


class PublisherService:
    def __init__(self):
        from backend.app.core.configs import settings
        self.adapter_registry = SocialAdapterRegistry(app_settings=settings)

    async def queue_publication(
        self,
        session: AsyncSession,
        tenant_id: str,
        project_id: str,
        content_item_id: str,
        platform: str,
        scheduled_at: datetime | None = None,
        content_type: str = "post",
    ) -> Publication:
        integration = await session.scalar(
            select(SocialIntegration).where(
                SocialIntegration.tenant_id == tenant_id,
                SocialIntegration.platform == IntegrationPlatform(platform),
                SocialIntegration.status == "connected",
            )
        )
        if not integration:
            integration = await session.scalar(
                select(SocialIntegration).where(
                    SocialIntegration.tenant_id == tenant_id,
                    SocialIntegration.platform == IntegrationPlatform(platform),
                )
            )
            if not integration:
                raise ValueError(f"No social integration for platform {platform}")

        publication = Publication(
            tenant_id=tenant_id,
            project_id=project_id,
            content_item_id=content_item_id,
            platform=IntegrationPlatform(platform),
            status=PublicationStatus.QUEUED,
            scheduled_at=scheduled_at or datetime.now(UTC),
        )
        session.add(publication)
        await session.flush()

        target = PublicationTarget(
            publication_id=publication.id,
            integration_id=integration.id,
            platform=IntegrationPlatform(platform),
            status=PublicationTargetStatus.QUEUED,
        )
        session.add(target)
        await session.flush()

        return publication

    async def publish(
        self, session: AsyncSession, publication_id: str
    ) -> dict:
        publication = await session.scalar(
            select(Publication).where(Publication.id == publication_id)
        )
        if not publication:
            raise ValueError(f"Publication {publication_id} not found")

        content_item = await session.scalar(
            select(ContentItem).where(ContentItem.id == publication.content_item_id)
        )
        if not content_item:
            content_text = ""
            media_urls: list[str] = []
        else:
            content_text = content_item.text
            media_urls = []
            if content_item.image_url:
                media_urls.append(content_item.image_url)
            if content_item.video_url:
                media_urls.append(content_item.video_url)

        target = await session.scalar(
            select(PublicationTarget).where(
                PublicationTarget.publication_id == publication.id
            )
        )

        attempt = PublicationAttempt(
            publication_target_id=target.id if target else None,
            attempt_number=1,
            status=PublicationTargetStatus.IN_PROGRESS,
        )
        session.add(attempt)
        await session.flush()

        try:
            social = await session.scalar(
                select(SocialIntegration).where(
                    SocialIntegration.tenant_id == publication.tenant_id,
                    SocialIntegration.platform == publication.platform,
                    SocialIntegration.status == "connected",
                )
            )

            adapter = self.adapter_registry.adapter_for(publication.platform)

            pub_payload = PublishPayload(
                text=content_text,
                media_urls=media_urls,
                scheduled_at=publication.scheduled_at,
                metadata={"publication_id": publication.id, "tenant_id": publication.tenant_id},
            )

            if social:
                result = await adapter.publish(social, pub_payload)
            else:
                from types import SimpleNamespace
                from backend.app.integrations.social_adapters import MockSocialAdapter
                mock = MockSocialAdapter(platform=publication.platform, limit_per_minute=30)
                fake_integration = SimpleNamespace(
                    account_handle=f"mock_{publication.tenant_id[:8]}",
                    platform=publication.platform,
                )
                result = await mock.publish(fake_integration, pub_payload)

            publication.status = PublicationStatus.PUBLISHED
            publication.published_at = datetime.now(UTC)

            if target:
                target.status = PublicationTargetStatus.PUBLISHED
                target.published_at = datetime.now(UTC)
                if result:
                    target.external_post_id = result.external_post_id

            attempt.status = PublicationTargetStatus.PUBLISHED
            attempt.response_payload = {"external_post_id": result.external_post_id} if result else {}
            await session.flush()

            return {
                "publication_id": publication.id,
                "status": "published",
                "url": None,
                "external_id": result.external_post_id if result else None,
            }
        except Exception as e:
            publication.status = PublicationStatus.FAILED
            attempt.status = PublicationTargetStatus.FAILED
            attempt.error_message = str(e)
            await session.flush()
            raise

    async def retry_publication(
        self, session: AsyncSession, publication_id: str
    ) -> dict:
        publication = await session.scalar(
            select(Publication).where(Publication.id == publication_id)
        )
        if not publication:
            raise ValueError(f"Publication {publication_id} not found")

        target = await session.scalar(
            select(PublicationTarget).where(
                PublicationTarget.publication_id == publication_id
            )
        )

        previous_attempts = (
            await session.scalars(
                select(PublicationAttempt)
                .where(
                    PublicationAttempt.publication_target_id == target.id,
                    PublicationAttempt.status == PublicationTargetStatus.FAILED,
                )
                .order_by(desc(PublicationAttempt.attempt_number))
            )
        ).all() if target else []

        attempt_number = (previous_attempts[0].attempt_number if previous_attempts else 0) + 1
        if attempt_number > 3:
            raise ValueError(f"Publication {publication_id} has exceeded max retries (3)")

        publication.status = PublicationStatus.QUEUED
        await session.flush()

        return await self.publish(session, publication_id)

    async def get_publication_status(
        self, session: AsyncSession, publication_id: str
    ) -> dict | None:
        publication = await session.scalar(
            select(Publication).where(Publication.id == publication_id)
        )
        if not publication:
            return None

        target = await session.scalar(
            select(PublicationTarget).where(
                PublicationTarget.publication_id == publication_id
            )
        )

        attempts = (
            await session.scalars(
                select(PublicationAttempt)
                .where(
                    PublicationAttempt.publication_target_id == target.id,
                )
                .order_by(PublicationAttempt.attempt_number)
            )
        ).all() if target else []

        return {
            "id": publication.id,
            "tenant_id": publication.tenant_id,
            "project_id": publication.project_id,
            "platform": publication.platform,
            "status": publication.status,
            "content_type": publication.content_type.value if publication.content_type else None,
            "scheduled_at": publication.scheduled_at.isoformat() if publication.scheduled_at else None,
            "published_at": publication.published_at.isoformat() if publication.published_at else None,
            "external_url": publication.external_url,
            "external_post_id": publication.external_post_id or (target.external_post_id if target else None),
            "attempts": [
                {
                    "number": a.attempt_number,
                    "status": a.status,
                    "error": a.error_message,
                }
                for a in attempts
            ],
        }
