from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.enums import SubscriptionStatus
from backend.app.db.subscription import Subscription
from backend.app.db.user import User
from backend.app.schemas.subscriptions import SubscriptionResponse, UpdateSubscriptionRequest

PLAN_PRICING: dict[str, float] = {
    "trial": 0,
    "starter": 49,
    "growth": 199,
    "enterprise": 499,
}


class SubscriptionService:
    async def get_current(self, session: AsyncSession, current_user: User) -> SubscriptionResponse:
        subscription = await self._get_or_create(session, current_user)
        return self._to_response(subscription)

    async def update_current(
        self,
        session: AsyncSession,
        current_user: User,
        payload: UpdateSubscriptionRequest,
    ) -> SubscriptionResponse:
        subscription = await self._get_or_create(session, current_user)
        subscription.plan_name = payload.plan_name
        subscription.billing_period = payload.billing_period
        subscription.amount = float(PLAN_PRICING[payload.plan_name])
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.next_charge_at = datetime.now(UTC) + timedelta(days=30)
        await session.commit()
        await session.refresh(subscription)
        return self._to_response(subscription)

    async def _get_or_create(self, session: AsyncSession, current_user: User) -> Subscription:
        subscription = await session.scalar(
            select(Subscription).where(Subscription.user_id == current_user.id)
        )
        if subscription:
            return subscription

        subscription = Subscription(
            user_id=current_user.id,
            plan_name="trial",
            status=SubscriptionStatus.TRIAL,
            amount=0,
            billing_period="monthly",
            next_charge_at=datetime.now(UTC) + timedelta(days=14),
        )
        session.add(subscription)
        await session.commit()
        await session.refresh(subscription)
        return subscription

    def _to_response(self, subscription: Subscription) -> SubscriptionResponse:
        return SubscriptionResponse(
            plan_name=subscription.plan_name,
            status=subscription.status.value,
            amount=subscription.amount,
            billing_period=subscription.billing_period,
            next_charge_at=subscription.next_charge_at,
        )
