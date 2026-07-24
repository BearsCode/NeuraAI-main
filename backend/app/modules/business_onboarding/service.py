from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.configs import settings
from backend.app.db.ai_job import AIJob
from backend.app.db.enums import AIJobStatus, MembershipRole, StrategyStatus
from backend.app.db.project import Project
from backend.app.db.tenant import Tenant
from backend.app.db.tenant_membership import TenantMembership
from backend.app.db.user import User
from backend.app.events.schemas import AIRequestedEvent, BusinessOnboardedEvent, EventEnvelope
from backend.app.infra.outbox import OutboxService
from backend.app.modules.access import ensure_project_access
from backend.app.modules.business_onboarding.repository import BusinessOnboardingRepository
from backend.app.modules.business_onboarding.schemas import (
    AIAnalysisJobResponse,
    CreateBusinessRequest,
    BusinessResponse,
)


class BusinessOnboardingService:
    async def create_business(
        self,
        session: AsyncSession,
        current_user: User,
        payload: CreateBusinessRequest,
    ) -> BusinessResponse:
        repository = BusinessOnboardingRepository(session)
        if await repository.get_tenant_by_slug(payload.tenant_slug):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tenant slug already exists")

        tenant = await repository.create_tenant(
            Tenant(
                slug=payload.tenant_slug,
                name=payload.tenant_name,
                owner_user_id=current_user.id,
                default_timezone=payload.timezone,
                industry=payload.industry,
                city=payload.city,
                search_document=" ".join(
                    [
                        payload.tenant_name,
                        payload.company_name,
                        payload.business_description,
                        payload.target_audience,
                    ]
                ),
            )
        )
        await repository.create_membership(
            TenantMembership(
                tenant_id=tenant.id,
                user_id=current_user.id,
                role=MembershipRole.OWNER,
                is_primary=True,
            )
        )
        project = await repository.create_project(
            Project(
                tenant_id=tenant.id,
                owner_user_id=current_user.id,
                company_name=payload.company_name,
                business_description=payload.business_description,
                city=payload.city,
                industry=payload.industry,
                services=payload.services,
                website=str(payload.website) if payload.website else None,
                phone=payload.phone,
                email=str(payload.email) if payload.email else None,
                social_links=payload.social_links,
                target_audience=payload.target_audience,
                competitors=payload.competitors,
                business_features=payload.business_features,
                strategy_status=StrategyStatus.DRAFT,
                search_document=" ".join(
                    [
                        payload.company_name,
                        payload.business_description,
                        payload.industry,
                        payload.target_audience,
                    ]
                ),
            )
        )
        await repository.create_default_policy(tenant.id, project.id)
        await OutboxService().enqueue(
            session,
            EventEnvelope(
                event_type="business.onboarded",
                topic="business.onboarded.v1",
                tenant_id=tenant.id,
                aggregate_id=project.id,
                payload=BusinessOnboardedEvent(
                    tenant_id=tenant.id,
                    project_id=project.id,
                    owner_user_id=current_user.id,
                ).model_dump(mode="json"),
            ),
        )
        await session.commit()
        return BusinessResponse(
            tenant_id=tenant.id,
            project_id=project.id,
            tenant_name=tenant.name,
            tenant_slug=tenant.slug,
            company_name=project.company_name,
            city=project.city,
            industry=project.industry,
            strategy_status=project.strategy_status.value,
            created_at=project.created_at,
        )

    async def request_ai_analysis(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        project_id: str,
        task_type: str,
    ) -> AIAnalysisJobResponse:
        repository = BusinessOnboardingRepository(session)
        await ensure_project_access(session, current_user, tenant_id, project_id)
        job = await repository.create_ai_job(
            AIJob(
                tenant_id=tenant_id,
                project_id=project_id,
                job_type=task_type,
                provider=settings.ai.provider,
                model=settings.ai_model or settings.ai.provider,
                status=AIJobStatus.PENDING,
                input_payload={"requested_by_user_id": current_user.id},
            )
        )
        await OutboxService().enqueue(
            session,
            EventEnvelope(
                event_type="ai.requested",
                topic="ai.requested.v1",
                tenant_id=tenant_id,
                aggregate_id=job.id,
                payload=AIRequestedEvent(
                    tenant_id=tenant_id,
                    project_id=project_id,
                    job_id=job.id,
                    task_type=task_type,
                ).model_dump(mode="json"),
            ),
        )
        await session.commit()
        return AIAnalysisJobResponse(
            job_id=job.id,
            tenant_id=tenant_id,
            project_id=project_id,
            status=job.status.value,
            task_type=job.job_type,
        )
