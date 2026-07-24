from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.enums import SubscriptionStatus
from backend.app.db.partner_profile import PartnerProfile
from backend.app.db.project import Project
from backend.app.db.subscription import Subscription
from backend.app.db.user import User
from backend.app.schemas.admin import AdminOverviewResponse, AdminProjectResponse, AdminUserResponse


class AdminService:
    async def get_overview(self, session: AsyncSession) -> AdminOverviewResponse:
        users_total = await session.scalar(select(func.count(User.id)))
        projects_total = await session.scalar(select(func.count(Project.id)))
        active_subscriptions = await session.scalar(
            select(func.count(Subscription.id)).where(Subscription.status == SubscriptionStatus.ACTIVE)
        )
        partners_total = await session.scalar(select(func.count(PartnerProfile.id)))
        monthly_revenue = await session.scalar(
            select(func.coalesce(func.sum(Subscription.amount), 0)).where(
                Subscription.status == SubscriptionStatus.ACTIVE
            )
        )
        return AdminOverviewResponse(
            users_total=int(users_total or 0),
            projects_total=int(projects_total or 0),
            active_subscriptions=int(active_subscriptions or 0),
            partners_total=int(partners_total or 0),
            monthly_revenue=float(monthly_revenue or 0),
        )

    async def list_users(self, session: AsyncSession) -> list[AdminUserResponse]:
        query = (
            select(User, func.count(Project.id).label("projects_total"))
            .outerjoin(Project, Project.owner_user_id == User.id)
            .group_by(User.id)
            .order_by(User.created_at.desc())
        )
        rows = (await session.execute(query)).all()
        return [
            AdminUserResponse(
                user_id=user.id,
                email=user.email,
                full_name=user.full_name,
                role=user.role.value,
                is_active=user.is_active,
                projects_total=int(projects_total or 0),
            )
            for user, projects_total in rows
        ]

    async def list_projects(self, session: AsyncSession) -> list[AdminProjectResponse]:
        rows = (
            await session.execute(
                select(Project, User.email)
                .join(User, User.id == Project.owner_user_id)
                .order_by(Project.created_at.desc())
            )
        ).all()
        return [
            AdminProjectResponse(
                project_id=project.id,
                company_name=project.company_name,
                owner_email=owner_email,
                industry=project.industry,
                strategy_status=project.strategy_status.value,
            )
            for project, owner_email in rows
        ]
