from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.project import Project
from backend.app.db.tenant import Tenant
from backend.app.db.tenant_membership import TenantMembership
from backend.app.db.user import User
from backend.app.repositories.user import PartnerProfileRepository
from backend.app.schemas.users import ProfileResponse, UpdateProfileRequest


class UserService:
    async def get_profile(self, session: AsyncSession, current_user: User) -> ProfileResponse:
        partner_profile = await PartnerProfileRepository(session).get_by_user_id(current_user.id)
        company_name = await self._get_company_name(session, current_user)
        return ProfileResponse(
            user_id=current_user.id,
            email=current_user.email,
            full_name=current_user.full_name,
            phone=current_user.phone,
            company_name=company_name,
            role=current_user.role.value,
            admin_role=current_user.admin_role.value if current_user.admin_role else None,
            is_active=current_user.is_active,
            referral_code=partner_profile.referral_code if partner_profile else None,
        )

    async def update_profile(
        self,
        session: AsyncSession,
        current_user: User,
        payload: UpdateProfileRequest,
    ) -> ProfileResponse:
        persistent_user = await session.get(User, current_user.id)
        if persistent_user is None:
            return await self.get_profile(session, current_user)

        updates = payload.model_dump(exclude_none=True)
        for field, value in updates.items():
            if field in {"full_name", "phone"}:
                setattr(persistent_user, field, value)

        if payload.company_name is not None:
            persistent_user.company_name = payload.company_name
            context = await self._get_primary_context(session, persistent_user)
            if context is not None:
                tenant, project = context
                tenant.name = payload.company_name
                project.company_name = payload.company_name
                project.search_document = " ".join(
                    filter(
                        None,
                        [
                            payload.company_name,
                            project.business_description,
                            project.industry,
                            project.target_audience,
                        ],
                    )
                )

        await session.commit()
        return await self.get_profile(session, persistent_user)

    async def _get_company_name(self, session: AsyncSession, current_user: User) -> str | None:
        context = await self._get_primary_context(session, current_user)
        if context is not None:
            tenant, project = context
            return project.company_name or tenant.name

        return await session.scalar(
            select(Tenant.name)
            .join(TenantMembership, TenantMembership.tenant_id == Tenant.id)
            .where(TenantMembership.user_id == current_user.id)
            .order_by(TenantMembership.is_primary.desc(), Tenant.created_at.desc())
        )

    async def _get_primary_context(
        self,
        session: AsyncSession,
        current_user: User,
    ) -> tuple[Tenant, Project] | None:
        row = (
            await session.execute(
                select(Tenant, Project)
                .join(TenantMembership, TenantMembership.tenant_id == Tenant.id)
                .join(Project, Project.tenant_id == Tenant.id)
                .where(TenantMembership.user_id == current_user.id)
                .order_by(TenantMembership.is_primary.desc(), Project.created_at.desc())
            )
        ).first()
        if row is None:
            return None
        return row[0], row[1]
