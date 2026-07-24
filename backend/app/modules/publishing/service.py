from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.approval_policy import ApprovalPolicy
from backend.app.db.enums import (
    ApprovalMode,
    ContentStatus,
    PublicationStatus,
    PublicationTargetStatus,
)
from backend.app.db.publication import Publication
from backend.app.db.publication_attempt import PublicationAttempt
from backend.app.db.publication_target import PublicationTarget
from backend.app.db.user import User
from backend.app.events.schemas import EventEnvelope, PublicationApprovedEvent, PublicationResultEvent
from backend.app.infra.outbox import OutboxService
from backend.app.modules.access import ensure_project_access
from backend.app.modules.publishing.repository import PublishingRepository
from backend.app.modules.publishing.saga import PublishingSagaCoordinator
from backend.app.modules.publishing.schemas import (
    CreatePublicationRequest,
    PublicationResponse,
    PublicationTargetResponse,
)


class PublishingService:
    async def create_publication(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        project_id: str,
        payload: CreatePublicationRequest,
    ) -> PublicationResponse:
        await ensure_project_access(session, current_user, tenant_id, project_id)
        repository = PublishingRepository(session)
        content_item = await repository.get_content_item(tenant_id, payload.content_item_id)
        if not content_item or content_item.project_id != project_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content item not found")

        integrations = await repository.list_integrations_for_ids(
            tenant_id,
            project_id,
            payload.integration_ids,
        )
        if not integrations:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active integrations selected")

        approval_policy = await session.scalar(
            select(ApprovalPolicy).where(
                ApprovalPolicy.tenant_id == tenant_id,
                ApprovalPolicy.project_id == project_id,
            )
        )
        auto_mode_enabled = bool(
            approval_policy
            and approval_policy.mode == ApprovalMode.AUTO
            and approval_policy.auto_publish_enabled
        )

        publication = await repository.create_publication(
            Publication(
                tenant_id=tenant_id,
                project_id=project_id,
                content_item_id=content_item.id,
                status=PublicationStatus.APPROVED if auto_mode_enabled else PublicationStatus.PENDING_APPROVAL,
                scheduled_at=payload.scheduled_at or (datetime.now(UTC) + timedelta(hours=1)),
                all_or_nothing=payload.all_or_nothing,
                approval_required=not auto_mode_enabled,
            )
        )
        targets: list[PublicationTarget] = []
        for integration in integrations:
            target = await repository.create_target(
                PublicationTarget(
                    tenant_id=tenant_id,
                    publication_id=publication.id,
                    integration_id=integration.id,
                    platform=integration.platform,
                    status=PublicationTargetStatus.QUEUED,
                )
            )
            await repository.create_attempt(
                PublicationAttempt(
                    tenant_id=tenant_id,
                    publication_target_id=target.id,
                    attempt_number=1,
                    status=PublicationTargetStatus.QUEUED,
                    next_retry_at=publication.scheduled_at,
                )
            )
            targets.append(target)

        saga_id = PublishingSagaCoordinator().start(publication, targets)
        publication.status = PublicationStatus.APPROVED if auto_mode_enabled else PublicationStatus.PENDING_APPROVAL
        publication.saga_id = saga_id
        content_item.status = ContentStatus.READY
        await session.commit()
        return await self.get_publication(session, current_user, tenant_id, publication.id)

    async def get_publication(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        publication_id: str,
    ) -> PublicationResponse:
        publication = await PublishingRepository(session).get_publication(tenant_id, publication_id)
        if not publication:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Publication not found")
        await ensure_project_access(session, current_user, tenant_id, publication.project_id)
        return self._to_response(publication)

    async def list_publications(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        project_id: str,
    ) -> list[PublicationResponse]:
        await ensure_project_access(session, current_user, tenant_id, project_id)
        publications = await PublishingRepository(session).list_publications(tenant_id, project_id)
        return [self._to_response(item) for item in publications]

    async def mark_approved(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        publication_id: str,
    ) -> PublicationResponse:
        publication = await PublishingRepository(session).get_publication(tenant_id, publication_id)
        if not publication:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Publication not found")
        await ensure_project_access(session, current_user, tenant_id, publication.project_id)
        publication.status = PublicationStatus.APPROVED
        await OutboxService().enqueue(
            session,
            EventEnvelope(
                event_type="publication.approved",
                topic="publication.approved.v1",
                tenant_id=tenant_id,
                aggregate_id=publication.id,
                payload=PublicationApprovedEvent(
                    tenant_id=tenant_id,
                    publication_id=publication.id,
                    approved_by_user_id=current_user.id,
                ).model_dump(mode="json"),
            ),
        )
        await session.commit()
        return self._to_response(publication)

    async def mark_target_result(
        self,
        session: AsyncSession,
        publication: Publication,
        target: PublicationTarget,
        success: bool,
        *,
        message: str | None = None,
        all_or_nothing: bool = True,
    ) -> None:
        saga = PublishingSagaCoordinator()
        if success:
            saga.handle_target_success(publication, target)
        else:
            saga.handle_target_failure(publication, target, all_or_nothing)

        await OutboxService().enqueue(
            session,
            EventEnvelope(
                event_type="publication.target.result",
                topic="publication.target.result.v1",
                tenant_id=publication.tenant_id,
                aggregate_id=target.id,
                payload=PublicationResultEvent(
                    tenant_id=publication.tenant_id,
                    publication_id=publication.id,
                    platform=target.platform.value,
                    status=target.status.value,
                    message=message,
                ).model_dump(mode="json"),
            ),
        )

    def _to_response(self, publication: Publication) -> PublicationResponse:
        return PublicationResponse(
            publication_id=publication.id,
            tenant_id=publication.tenant_id,
            project_id=publication.project_id,
            content_item_id=publication.content_item_id,
            status=publication.status.value,
            scheduled_at=publication.scheduled_at,
            all_or_nothing=publication.all_or_nothing,
            approval_required=publication.approval_required,
            saga_id=publication.saga_id,
            targets=[
                PublicationTargetResponse(
                    publication_target_id=target.id,
                    integration_id=target.integration_id,
                    platform=target.platform.value,
                    status=target.status.value,
                    external_post_id=target.external_post_id,
                    published_at=target.published_at,
                )
                for target in publication.targets
            ],
        )
