from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.ai_job import AIJob
from backend.app.db.approval_policy import ApprovalPolicy
from backend.app.db.enums import ApprovalMode
from backend.app.db.project import Project
from backend.app.db.tenant import Tenant
from backend.app.db.tenant_membership import TenantMembership


class BusinessOnboardingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_tenant_by_slug(self, tenant_slug: str) -> Tenant | None:
        return await self.session.scalar(select(Tenant).where(Tenant.slug == tenant_slug))

    async def create_tenant(self, tenant: Tenant) -> Tenant:
        self.session.add(tenant)
        await self.session.flush()
        return tenant

    async def create_membership(self, membership: TenantMembership) -> TenantMembership:
        self.session.add(membership)
        await self.session.flush()
        return membership

    async def create_project(self, project: Project) -> Project:
        self.session.add(project)
        await self.session.flush()
        return project

    async def create_default_policy(self, tenant_id: str, project_id: str) -> ApprovalPolicy:
        policy = ApprovalPolicy(
            tenant_id=tenant_id,
            project_id=project_id,
            mode=ApprovalMode.MANUAL,
            auto_publish_enabled=False,
        )
        self.session.add(policy)
        await self.session.flush()
        return policy

    async def create_ai_job(self, job: AIJob) -> AIJob:
        self.session.add(job)
        await self.session.flush()
        return job
