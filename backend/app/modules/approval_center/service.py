from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.db.approval_policy import ApprovalPolicy
from backend.app.db.enums import ApprovalMode, PublicationStatus
from backend.app.db.publication import Publication
from backend.app.db.user import User
from backend.app.modules.access import ensure_project_access
from backend.app.modules.approval_center.schemas import (
    ApprovalPolicyResponse,
    ApprovalPolicyUpdateRequest,
    ApprovalQueueItemResponse,
)
from backend.app.modules.publishing.service import PublishingService


class ApprovalCenterService:
    async def get_policy(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        project_id: str,
    ) -> ApprovalPolicyResponse:
        await ensure_project_access(session, current_user, tenant_id, project_id)
        policy = await session.scalar(
            select(ApprovalPolicy).where(
                ApprovalPolicy.tenant_id == tenant_id,
                ApprovalPolicy.project_id == project_id,
            )
        )
        if not policy:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval policy not found")
        return self._to_policy_response(policy)

    async def update_policy(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        project_id: str,
        payload: ApprovalPolicyUpdateRequest,
    ) -> ApprovalPolicyResponse:
        await ensure_project_access(session, current_user, tenant_id, project_id)
        policy = await session.scalar(
            select(ApprovalPolicy).where(
                ApprovalPolicy.tenant_id == tenant_id,
                ApprovalPolicy.project_id == project_id,
            )
        )
        if not policy:
            policy = ApprovalPolicy(tenant_id=tenant_id, project_id=project_id)
            session.add(policy)
        policy.mode = ApprovalMode(payload.mode)
        policy.auto_publish_enabled = payload.auto_publish_enabled
        policy.auto_publish_platforms = payload.auto_publish_platforms
        await session.commit()
        return self._to_policy_response(policy)

    async def get_queue(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        project_id: str,
    ) -> list[ApprovalQueueItemResponse]:
        await ensure_project_access(session, current_user, tenant_id, project_id)
        publications = (
            await session.scalars(
                select(Publication)
                .options(selectinload(Publication.targets))
                .where(
                    Publication.tenant_id == tenant_id,
                    Publication.project_id == project_id,
                    Publication.status.in_(
                        [
                            PublicationStatus.PENDING_APPROVAL,
                            PublicationStatus.APPROVED,
                        ]
                    ),
                )
                .order_by(Publication.scheduled_at)
            )
        ).all()
        return [
            ApprovalQueueItemResponse(
                publication_id=item.id,
                content_item_id=item.content_item_id,
                status=item.status.value,
                scheduled_at=item.scheduled_at,
                target_platforms=[target.platform.value for target in item.targets],
            )
            for item in publications
        ]

    async def approve(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        publication_id: str,
    ):
        return await PublishingService().mark_approved(session, current_user, tenant_id, publication_id)

    async def reject(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        publication_id: str,
        comment: str | None,
    ):
        await PublishingService().get_publication(session, current_user, tenant_id, publication_id)
        db_publication = await session.get(Publication, publication_id)
        assert db_publication is not None
        db_publication.status = PublicationStatus.FAILED
        db_publication.last_error_message = comment
        await session.commit()
        return await PublishingService().get_publication(session, current_user, tenant_id, publication_id)

    async def postpone(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        publication_id: str,
        scheduled_at,
    ):
        await PublishingService().get_publication(session, current_user, tenant_id, publication_id)
        db_publication = await session.get(Publication, publication_id)
        assert db_publication is not None
        db_publication.scheduled_at = scheduled_at
        db_publication.status = PublicationStatus.PENDING_APPROVAL
        await session.commit()
        return await PublishingService().get_publication(session, current_user, tenant_id, publication_id)

    def _to_policy_response(self, policy: ApprovalPolicy) -> ApprovalPolicyResponse:
        return ApprovalPolicyResponse(
            policy_id=policy.id,
            tenant_id=policy.tenant_id,
            project_id=policy.project_id,
            mode=policy.mode.value,
            auto_publish_enabled=policy.auto_publish_enabled,
            auto_publish_platforms=policy.auto_publish_platforms,
        )
