from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.enums import UserRole
from backend.app.db.project import Project
from backend.app.db.tenant import Tenant
from backend.app.db.tenant_membership import TenantMembership
from backend.app.db.user import User


async def ensure_tenant_access(
    session: AsyncSession,
    current_user: User,
    tenant_id: str,
) -> Tenant:
    tenant = await session.scalar(select(Tenant).where(Tenant.id == tenant_id))
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    if current_user.role == UserRole.ADMIN:
        return tenant

    membership = await session.scalar(
        select(TenantMembership).where(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.user_id == current_user.id,
        )
    )
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden for tenant")
    return tenant


async def ensure_project_access(
    session: AsyncSession,
    current_user: User,
    tenant_id: str,
    project_id: str,
) -> Project:
    await ensure_tenant_access(session, current_user, tenant_id)
    project = await session.scalar(
        select(Project).where(Project.id == project_id, Project.tenant_id == tenant_id)
    )
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project
