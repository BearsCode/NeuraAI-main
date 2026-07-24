import re

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.enums import MembershipRole, StrategyStatus
from backend.app.db.project import Project
from backend.app.db.tenant import Tenant
from backend.app.db.tenant_membership import TenantMembership
from backend.app.db.user import User
from backend.app.events.schemas import BusinessOnboardedEvent, EventEnvelope
from backend.app.infra.outbox import OutboxService
from backend.app.modules.business_onboarding.repository import BusinessOnboardingRepository
from backend.app.repositories.project import ProjectRepository
from backend.app.schemas.projects import (
    BusinessOnboardingRequest,
    ProjectResponse,
    ProjectSummaryResponse,
)


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    normalized = normalized.strip("-")
    return normalized or "business"


async def _unique_tenant_slug(session: AsyncSession, company_name: str) -> str:
    base = _slugify(company_name)
    candidate = base
    suffix = 1
    while await session.scalar(select(Tenant).where(Tenant.slug == candidate)):
        suffix += 1
        candidate = f"{base}-{suffix}"
    return candidate


async def ensure_project_access(
    session: AsyncSession,
    project_id: str,
    current_user: User,
) -> Project:
    project = await ProjectRepository(session).get_accessible_project(project_id, current_user)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


class ProjectService:
    async def list_projects(
        self,
        session: AsyncSession,
        current_user: User,
    ) -> list[ProjectSummaryResponse]:
        projects = await ProjectRepository(session).list_for_user(current_user)
        return [
            ProjectSummaryResponse(
                project_id=project.id,
                company_name=project.company_name,
                industry=project.industry,
                city=project.city,
                strategy_status=project.strategy_status.value,
            )
            for project in projects
        ]

    async def create_project(
        self,
        session: AsyncSession,
        current_user: User,
        payload: BusinessOnboardingRequest,
    ) -> ProjectResponse:
        repository = BusinessOnboardingRepository(session)
        tenant = await repository.create_tenant(
            Tenant(
                slug=await _unique_tenant_slug(session, payload.company_name),
                name=payload.company_name,
                owner_user_id=current_user.id,
                default_timezone="UTC",
                industry=payload.industry,
                city=payload.city,
                search_document=" ".join(
                    filter(
                        None,
                        [
                            payload.company_name,
                            payload.business_description,
                            payload.target_audience,
                        ],
                    )
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
                    filter(
                        None,
                        [
                            payload.company_name,
                            payload.business_description,
                            payload.industry,
                            payload.target_audience,
                        ],
                    )
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
        await session.refresh(project)
        return self._to_response(project)

    async def get_project(
        self,
        session: AsyncSession,
        current_user: User,
        project_id: str,
    ) -> ProjectResponse:
        project = await ensure_project_access(session, project_id, current_user)
        return self._to_response(project)

    def _to_response(self, project: Project) -> ProjectResponse:
        return ProjectResponse(
            project_id=project.id,
            owner_user_id=project.owner_user_id,
            company_name=project.company_name,
            business_description=project.business_description,
            city=project.city,
            industry=project.industry,
            services=project.services,
            website=project.website,
            phone=project.phone,
            email=project.email,
            social_links=project.social_links,
            target_audience=project.target_audience,
            competitors=project.competitors,
            business_features=project.business_features,
            strategy_status=project.strategy_status.value,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
