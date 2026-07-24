from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.db.enums import ContentStatus, PublicationStatus, UserRole
from backend.app.db.project import Project
from backend.app.db.publication import Publication
from backend.app.db.tenant_membership import TenantMembership
from backend.app.db.user import User
from backend.app.integrations.queue_client import QueueClient
from backend.app.schemas.approval import (
    ApprovalDecisionRequest,
    ApprovalItemResponse,
    PostponePublicationRequest,
    PublicationActionResponse,
)

class ApprovalService:
    async def get_queue(
        self,
        session: AsyncSession,
        current_user: User,
        project_id: str,
    ) -> list[ApprovalItemResponse]:
        query = (
            select(Publication)
            .options(selectinload(Publication.content_item))
            .where(Publication.project_id == project_id)
        )
        if current_user.role != UserRole.ADMIN:
            query = query.join(Project, Project.id == Publication.project_id).join(
                TenantMembership,
                TenantMembership.tenant_id == Project.tenant_id,
            ).where(
                TenantMembership.user_id == current_user.id
            )

        accessible = (await session.scalars(query)).all()
        return [
            ApprovalItemResponse(
                publication_id=publication.id,
                content_item_id=publication.content_item_id,
                platform=publication.platform.value,
                scheduled_at=publication.scheduled_at,
                status=publication.status.value,
                preview_text=publication.content_item.text if publication.content_item else "",
                requires_changes=publication.status == PublicationStatus.REJECTED,
            )
            for publication in accessible
            if publication.status in {PublicationStatus.PENDING_APPROVAL, PublicationStatus.POSTPONED}
        ]

    async def approve(
        self,
        session: AsyncSession,
        current_user: User,
        publication_id: str,
        queue_client: QueueClient,
    ) -> PublicationActionResponse:
        publication = await self._get_accessible_publication(session, current_user, publication_id)
        publication.status = PublicationStatus.QUEUED
        if publication.content_item:
            publication.content_item.status = ContentStatus.APPROVED
        queue_reference = await queue_client.enqueue_publication(publication.id)
        await session.commit()
        return PublicationActionResponse(
            publication_id=publication.id,
            status=publication.status.value,
            message="Publication approved and queued",
            queue_reference=queue_reference,
        )

    async def reject(
        self,
        session: AsyncSession,
        current_user: User,
        publication_id: str,
        payload: ApprovalDecisionRequest,
    ) -> PublicationActionResponse:
        publication = await self._get_accessible_publication(session, current_user, publication_id)
        publication.status = PublicationStatus.REJECTED
        publication.last_error_message = payload.comment
        if publication.content_item:
            publication.content_item.status = ContentStatus.REJECTED
        await session.commit()
        return PublicationActionResponse(
            publication_id=publication.id,
            status=publication.status.value,
            message="Publication rejected",
        )

    async def postpone(
        self,
        session: AsyncSession,
        current_user: User,
        publication_id: str,
        payload: PostponePublicationRequest,
    ) -> PublicationActionResponse:
        publication = await self._get_accessible_publication(session, current_user, publication_id)
        publication.status = PublicationStatus.POSTPONED
        publication.scheduled_at = payload.scheduled_at
        await session.commit()
        return PublicationActionResponse(
            publication_id=publication.id,
            status=publication.status.value,
            message="Publication postponed",
        )

    async def _get_accessible_publication(
        self,
        session: AsyncSession,
        current_user: User,
        publication_id: str,
    ) -> Publication:
        query = (
            select(Publication)
            .options(selectinload(Publication.content_item))
            .where(Publication.id == publication_id)
        )
        if current_user.role != UserRole.ADMIN:
            query = query.join(Project, Project.id == Publication.project_id).join(
                TenantMembership,
                TenantMembership.tenant_id == Project.tenant_id,
            ).where(
                TenantMembership.user_id == current_user.id
            )

        publication = await session.scalar(query)
        if not publication:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Publication not found")
        return publication
