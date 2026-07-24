from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.configs import settings
from backend.app.core.security import generate_referral_code
from backend.app.db.enums import CommissionStatus, PaymentStatus, PlanCode, SubscriptionStatus
from backend.app.db.tenant_membership import TenantMembership
from backend.app.db.partner_commission import PartnerCommission
from backend.app.db.partner_profile import PartnerProfile
from backend.app.db.payment import Payment
from backend.app.db.promo_code_redemption import PromoCodeRedemption
from backend.app.db.subscription import Subscription
from backend.app.db.subscription_plan import SubscriptionPlan
from backend.app.db.tenant import Tenant
from backend.app.db.user import User
from backend.app.modules.access import ensure_tenant_access
from backend.app.modules.billing.schemas import (
    CommissionResponse,
    PaymentResponse,
    SubscriptionPlanResponse,
    SubscriptionResponse,
)
from backend.app.schemas.promocode import PromocodePreviewResponse
from backend.app.services.promocode_service import PromoCodeService
from backend.app.modules.billing.yookassa import YooKassaClient
from backend.app.observability.logging import get_logger

logger = get_logger(__name__)


class BillingService:
    def __init__(self) -> None:
        self.promocodes = PromoCodeService()

    async def list_plans(self, session: AsyncSession) -> list[SubscriptionPlanResponse]:
        plans = (
            await session.scalars(
                select(SubscriptionPlan)
                .where(SubscriptionPlan.is_active.is_(True))
                .order_by(SubscriptionPlan.price_amount.asc(), SubscriptionPlan.created_at.asc())
            )
        ).all()
        return [
            SubscriptionPlanResponse(
                plan_id=plan.id,
                code=plan.code,
                name=plan.name,
                price_amount=plan.price_amount,
                currency=plan.currency,
                requests_per_minute=plan.requests_per_minute,
                content_generations_per_hour=plan.content_generations_per_hour,
                publications_per_hour=plan.publications_per_hour,
                features=plan.features,
            )
            for plan in plans
        ]

    async def preview_promocode(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        code: str,
        plan_code: str,
    ) -> PromocodePreviewResponse:
        await ensure_tenant_access(session, current_user, tenant_id)
        plan = await self._get_plan(session, plan_code)
        return await self.promocodes.preview_promocode(session, tenant_id, code, plan)

    async def get_subscription(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
    ) -> SubscriptionResponse:
        await ensure_tenant_access(session, current_user, tenant_id)
        subscription = await self._get_subscription_record(session, tenant_id)
        if not subscription:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
        return self._to_subscription_response(subscription)

    async def change_plan(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        plan_code: str,
        promo_code: str | None = None,
    ) -> SubscriptionResponse:
        await ensure_tenant_access(session, current_user, tenant_id)
        plan = await self._get_plan(session, plan_code)
        subscription = await self._get_subscription_record(session, tenant_id)
        now = datetime.now(UTC)

        if not subscription:
            subscription = Subscription(
                tenant_id=tenant_id,
                plan_id=plan.id,
                status=SubscriptionStatus.ACTIVE,
                starts_at=now,
                next_charge_at=now + timedelta(days=30),
            )
            session.add(subscription)
        else:
            subscription.plan_id = plan.id
            subscription.status = SubscriptionStatus.ACTIVE
            subscription.next_charge_at = now + timedelta(days=30)

        subscription.active_promo_code_redemption = None
        subscription.active_promo_code_redemption_id = None
        await session.flush()

        if promo_code:
            redemption = await self.promocodes.redeem_promocode(
                session=session,
                current_user=current_user,
                tenant_id=tenant_id,
                subscription=subscription,
                plan=plan,
                code=promo_code,
            )
            subscription.active_promo_code_redemption = redemption

        await session.commit()
        return await self.get_subscription(session, current_user, tenant_id)

    async def is_creator_plan(
        self,
        session: AsyncSession,
        tenant_id: str,
    ) -> bool:
        subscription = await self._get_subscription_record(session, tenant_id)
        if not subscription or not subscription.plan:
            return False
        return subscription.plan.code == PlanCode.CREATOR.value

    async def list_payments(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
    ) -> list[PaymentResponse]:
        subscription = await self.get_subscription(session, current_user, tenant_id)
        db_subscription = await session.scalar(
            select(Subscription)
            .options(selectinload(Subscription.payments))
            .where(Subscription.id == subscription.subscription_id)
        )
        assert db_subscription is not None
        return [
            PaymentResponse(
                payment_id=payment.id,
                amount=payment.amount,
                currency=payment.currency,
                status=payment.status.value,
                provider=payment.provider,
                paid_at=payment.paid_at,
            )
            for payment in db_subscription.payments
        ]

    async def list_commissions(
        self,
        session: AsyncSession,
        current_user: User,
    ) -> list[CommissionResponse]:
        commissions = (
            await session.scalars(
                select(PartnerCommission)
                .where(PartnerCommission.partner_user_id == current_user.id)
                .order_by(PartnerCommission.created_at.desc())
            )
        ).all()
        return [
            CommissionResponse(
                commission_id=item.id,
                tenant_id=item.tenant_id,
                amount=item.amount,
                status=item.status.value,
                paid_out_at=item.paid_out_at,
            )
            for item in commissions
        ]

    async def record_successful_payment(
        self,
        session: AsyncSession,
        *,
        subscription_id: str | None,
        external_payment_id: str | None,
        amount: float,
        currency: str,
        provider: str,
        metadata: dict,
    ) -> Payment:
        """Persist a successful payment and atomically accrue referral commission."""

        now = datetime.now(UTC)
        async with session.begin():
            subscription = await self._resolve_subscription_for_payment(session, subscription_id)
            payment = None
            if external_payment_id:
                payment = await session.scalar(
                    select(Payment).where(Payment.external_payment_id == external_payment_id)
                )

            if payment is None:
                payment = Payment(
                    tenant_id=subscription.tenant_id,
                    subscription_id=subscription.id,
                    external_payment_id=external_payment_id,
                    provider=provider,
                )
                session.add(payment)

            payment.amount = amount
            payment.currency = currency
            payment.status = PaymentStatus.SUCCEEDED
            payment.paid_at = now
            payment.metadata_json = metadata
            subscription.status = SubscriptionStatus.ACTIVE
            subscription.next_charge_at = now + timedelta(days=30)
            await session.flush()

            existing_commission_id = await session.scalar(
                select(PartnerCommission.id).where(PartnerCommission.payment_id == payment.id).limit(1)
            )
            if existing_commission_id is None:
                await self._accrue_partner_commission(session, subscription, payment)

        return payment

    async def initiate_payment(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        plan_code: str,
        promo_code: str | None = None,
    ) -> dict:
        """Initiate a payment for a plan change. Returns payment details for frontend to process."""
        await ensure_tenant_access(session, current_user, tenant_id)
        plan = await self._get_plan(session, plan_code)
        
        if plan.price_amount == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot initiate payment for free plan")
        
        subscription = await self._get_subscription_record(session, tenant_id)
        if not subscription:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
        
        amount_to_pay = plan.price_amount
        if promo_code:
            redemption = await self.promocodes.redeem_promocode(
                session=session,
                current_user=current_user,
                tenant_id=tenant_id,
                subscription=subscription,
                plan=plan,
                code=promo_code,
            )
            subscription.active_promo_code_redemption = redemption
            amount_to_pay = redemption.final_price_amount
            
        payment = Payment(
            tenant_id=tenant_id,
            subscription_id=subscription.id,
            provider="yookassa",
            amount=amount_to_pay,
            currency=plan.currency,
            status=PaymentStatus.PENDING,
        )
        session.add(payment)
        await session.flush()
        
        subscription.status = SubscriptionStatus.PENDING_PAYMENT
        subscription.plan_id = plan.id
        subscription.plan_name = plan.code
        subscription.amount = int(amount_to_pay)
        
        await session.commit()
        
        # Initiate YooKassa payment
        try:
            client = YooKassaClient()
            return_url = f"{settings.server.cors_origins[0]}/billing" if settings.server.cors_origins else "https://neuraai.com/billing"
            yk_payment = await client.create_payment(
                amount=float(amount_to_pay),
                currency=plan.currency,
                description=f"Оплата тарифа {plan.name}",
                return_url=return_url,
                customer_email=current_user.email,
                metadata={"payment_id": str(payment.id), "tenant_id": tenant_id, "subscription_id": str(subscription.id)}
            )
            
            # Update external payment id
            payment.external_payment_id = yk_payment["id"]
            await session.commit()
            
            return {
                "payment_id": str(payment.id),
                "external_payment_id": yk_payment["id"],
                "confirmation_url": yk_payment["confirmation"]["confirmation_url"],
                "amount": payment.amount,
                "currency": payment.currency,
                "subscription_id": str(subscription.id),
            }
        except Exception as e:
            logger.error(f"Failed to initiate YooKassa payment: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Payment gateway error")

    async def handle_webhook(self, session: AsyncSession, payload: dict) -> dict:
        event = payload.get("event")
        obj = payload.get("object", {})
        
        metadata = obj.get("metadata", {})
        payment_id_str = metadata.get("payment_id")
        subscription_id_str = metadata.get("subscription_id")
        external_payment_id = obj.get("id")
        
        if event == "payment.succeeded":
            amount = float(obj.get("amount", {}).get("value", 0))
            currency = obj.get("amount", {}).get("currency", "RUB")
            await self.record_successful_payment(
                session=session,
                subscription_id=subscription_id_str,
                external_payment_id=external_payment_id,
                amount=amount,
                currency=currency,
                provider="yookassa",
                metadata=obj,
            )
        elif event == "payment.canceled":
            if external_payment_id:
                async with session.begin():
                    payment = await session.scalar(select(Payment).where(Payment.external_payment_id == external_payment_id))
                    if payment and payment.status == PaymentStatus.PENDING:
                        payment.status = PaymentStatus.FAILED
                        subscription = await session.get(Subscription, payment.subscription_id)
                        if subscription and subscription.status == SubscriptionStatus.PENDING_PAYMENT:
                            subscription.status = SubscriptionStatus.CANCELED
        
        return {"status": "ok"}

    async def refund_payment(self, session: AsyncSession, payment_id: str) -> dict:
        async with session.begin():
            payment = await session.get(Payment, payment_id)
            if not payment or payment.status != PaymentStatus.SUCCEEDED or not payment.external_payment_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment cannot be refunded")
            
            try:
                client = YooKassaClient()
                refund = await client.refund_payment(
                    payment_id=payment.external_payment_id,
                    amount=float(payment.amount),
                    currency=payment.currency,
                    description="Возврат средств по запросу",
                )
                payment.status = PaymentStatus.REFUNDED
                return refund
            except Exception as e:
                logger.error(f"Failed to refund payment {payment_id}: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Refund failed")

    async def _get_plan(self, session: AsyncSession, plan_code: str) -> SubscriptionPlan:
        plan = await session.scalar(
            select(SubscriptionPlan).where(
                SubscriptionPlan.code == plan_code,
                SubscriptionPlan.is_active.is_(True),
            )
        )
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        return plan

    async def _resolve_subscription_for_payment(
        self,
        session: AsyncSession,
        subscription_id: str | None,
    ) -> Subscription:
        query = select(Subscription).options(selectinload(Subscription.tenant))
        if subscription_id:
            query = query.where(Subscription.id == subscription_id)
        else:
            query = query.order_by(Subscription.created_at.desc())

        subscription = await session.scalar(query)
        if not subscription:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
        return subscription

    async def _accrue_partner_commission(
        self,
        session: AsyncSession,
        subscription: Subscription,
        payment: Payment,
    ) -> None:
        tenant = subscription.tenant or await session.get(Tenant, subscription.tenant_id)
        if tenant is None:
            return

        owner = await session.get(User, tenant.owner_user_id)
        if owner is None or not owner.referred_by_user_id:
            return

        referrer_subscription = await session.scalar(
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .join(TenantMembership, TenantMembership.tenant_id == Subscription.tenant_id)
            .where(
                TenantMembership.user_id == owner.referred_by_user_id,
                TenantMembership.is_primary.is_(True),
                Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]),
            )
            .order_by(Subscription.created_at.desc())
        )
        if not referrer_subscription or not referrer_subscription.plan:
            return
        if referrer_subscription.plan.code != PlanCode.CREATOR.value:
            return

        partner_profile = await session.scalar(
            select(PartnerProfile).where(PartnerProfile.user_id == owner.referred_by_user_id)
        )
        if partner_profile is None:
            referrer = await session.get(User, owner.referred_by_user_id)
            if referrer is None:
                return
            partner_profile = PartnerProfile(
                user_id=referrer.id,
                referral_code=generate_referral_code(referrer.full_name),
                commission_rate=settings.billing.partner_commission_rate,
            )
            session.add(partner_profile)
            await session.flush()

        commission_amount = round(payment.amount * partner_profile.commission_rate, 2)
        if commission_amount <= 0:
            return

        session.add(
            PartnerCommission(
                tenant_id=subscription.tenant_id,
                partner_user_id=partner_profile.user_id,
                payment_id=payment.id,
                amount=commission_amount,
                status=CommissionStatus.PENDING,
            )
        )
        partner_profile.total_income = round(partner_profile.total_income + commission_amount, 2)
        partner_profile.pending_payout = round(partner_profile.pending_payout + commission_amount, 2)

    async def _get_subscription_record(self, session: AsyncSession, tenant_id: str) -> Subscription | None:
        return await session.scalar(
            select(Subscription)
            .options(
                selectinload(Subscription.plan),
                selectinload(Subscription.active_promo_code_redemption).selectinload(PromoCodeRedemption.promo_code),
            )
            .where(Subscription.tenant_id == tenant_id)
            .order_by(Subscription.created_at.desc())
        )

    def _to_subscription_response(self, subscription: Subscription) -> SubscriptionResponse:
        applied_promocode = self.promocodes.serialize_redemption(subscription.active_promo_code_redemption)
        plan_price_amount = float(subscription.plan.price_amount)
        next_charge_amount = (
            applied_promocode.final_price_amount if applied_promocode is not None else plan_price_amount
        )
        return SubscriptionResponse(
            subscription_id=subscription.id,
            tenant_id=subscription.tenant_id,
            plan_code=subscription.plan.code,
            price_amount=plan_price_amount,
            currency=subscription.plan.currency,
            next_charge_amount=next_charge_amount,
            status=subscription.status.value,
            next_charge_at=subscription.next_charge_at,
            trial_ends_at=subscription.trial_ends_at,
            applied_promocode=applied_promocode,
        )
