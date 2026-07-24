from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.db.content_item import ContentItem
from backend.app.db.enums import UserRole
from backend.app.db.project import Project
from backend.app.db.publication import Publication
from backend.app.db.tenant_membership import TenantMembership
from backend.app.db.user import User
from backend.app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    async def list_for_user(self, current_user: User) -> list[Project]:
        query = select(Project).order_by(Project.created_at.desc())
        if current_user.role != UserRole.ADMIN:
            query = query.join(
                TenantMembership,
                TenantMembership.tenant_id == Project.tenant_id,
            ).where(TenantMembership.user_id == current_user.id)
        return list((await self.session.scalars(query)).unique().all())

    async def get_accessible_project(
        self,
        project_id: str,
        current_user: User,
    ) -> Project | None:
        query = (
            select(Project)
            .options(
                selectinload(Project.assets),
                selectinload(Project.integrations),
                selectinload(Project.strategy),
                selectinload(Project.content_plans),
                selectinload(Project.content_items).selectinload(ContentItem.publication),
                selectinload(Project.publications).selectinload(Publication.content_item),
                selectinload(Project.analytics_snapshots),
            )
            .where(Project.id == project_id)
        )
        if current_user.role != UserRole.ADMIN:
            query = query.join(
                TenantMembership,
                TenantMembership.tenant_id == Project.tenant_id,
            ).where(TenantMembership.user_id == current_user.id)
        return await self.session.scalar(query)

    async def create(self, project: Project) -> Project:
        self.session.add(project)
        await self.session.flush()
        return project
