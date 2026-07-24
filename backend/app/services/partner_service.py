from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.configs import settings
from backend.app.core.security import generate_referral_code
from backend.app.db.enums import PlanCode, SubscriptionStatus
from backend.app.db.partner_profile import PartnerProfile
from backend.app.db.subscription import Subscription
from backend.app.db.tenant_membership import TenantMembership
from backend.app.db.user import User
from backend.app.schemas.partners import PartnerDashboardResponse


class PartnerService:
    async def get_dashboard(
        self,
        session: AsyncSession,
        current_user: User,
    ) -> PartnerDashboardResponse:
        profile = await session.scalar(
            select(PartnerProfile).where(PartnerProfile.user_id == current_user.id)
        )
        if not profile:
            profile = PartnerProfile(
                user_id=current_user.id,
                referral_code=generate_referral_code(current_user.full_name),
                commission_rate=settings.billing.partner_commission_rate,
            )
            session.add(profile)
            await session.commit()
            await session.refresh(profile)

        invited_users = await session.scalar(
            select(func.count(User.id)).where(User.referred_by_user_id == current_user.id)
        )
        active_subscriptions = await session.scalar(
            select(func.count(Subscription.id))
            .join(User, User.id == Subscription.user_id)
            .where(
                User.referred_by_user_id == current_user.id,
                Subscription.status == SubscriptionStatus.ACTIVE,
            )
        )
        revenue = await session.scalar(
            select(func.coalesce(func.sum(Subscription.amount), 0))
            .join(User, User.id == Subscription.user_id)
            .where(
                User.referred_by_user_id == current_user.id,
                Subscription.status == SubscriptionStatus.ACTIVE,
            )
        )

        total_income = round(float(revenue or 0) * profile.commission_rate, 2)
        pending_payout = round(total_income * 0.5, 2)

        return PartnerDashboardResponse(
            referral_link=f"{settings.web.public_base_url.rstrip('/')}/ref/{profile.referral_code}",
            referral_code=profile.referral_code,
            total_referrals=int(invited_users or 0),
            successful_payments_count=int(active_subscriptions or 0),
            total_commission=total_income,
            available_balance=pending_payout,
            commission_rate=profile.commission_rate,
        )

    async def _check_creator_plan(
        self,
        session: AsyncSession,
        user: User,
    ) -> bool:
        membership = await session.scalar(
            select(TenantMembership).where(
                TenantMembership.user_id == user.id,
                TenantMembership.is_primary.is_(True),
            )
        )
        if not membership:
            return False

        subscription = await session.scalar(
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(
                Subscription.tenant_id == membership.tenant_id,
                Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]),
            )
            .order_by(Subscription.created_at.desc())
        )
        if not subscription or not subscription.plan:
            return False

        return subscription.plan.code == PlanCode.CREATOR.value
