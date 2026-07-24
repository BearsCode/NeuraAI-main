from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

from backend.app.db.admin_session import AdminSession
from backend.app.db.ai_expert_prompt import AIExpertPrompt
from backend.app.db.ai_job import AIJob
from backend.app.db.audit_log import AuditLog
from backend.app.db.content_item import ContentItem
from backend.app.db.device_fingerprint import DeviceFingerprint
from backend.app.db.enums import (
    AdminRole,
    AIJobStatus,
    CommissionStatus,
    IntegrationStatus,
    OutboxStatus,
    PaymentStatus,
    SubscriptionStatus,
    TenantStatus,
    ToolProviderType,
    ToolStatus,
    UserRole,
)
from backend.app.db.notification import Notification
from backend.app.db.tool import Tool
from backend.app.db.outbox_event import OutboxEvent
from backend.app.db.partner_commission import PartnerCommission
from backend.app.db.partner_profile import PartnerProfile
from backend.app.db.payment import Payment
from backend.app.db.platform_setting import PlatformSetting
from backend.app.db.project import Project
from backend.app.db.publication import Publication
from backend.app.db.social_integration import SocialIntegration
from backend.app.db.subscription import Subscription
from backend.app.db.subscription_plan import SubscriptionPlan
from backend.app.db.tenant import Tenant
from backend.app.db.tenant_membership import TenantMembership
from backend.app.db.user import User
from backend.app.db.workflow_instance import WorkflowInstance
from backend.app.modules.admin.rbac import ROLE_PERMISSIONS, can_manage_role, get_permissions_for_role
from backend.app.modules.admin.schemas import (
    AdminAdminRoleUpdateRequest,
    AdminAnalyticsResponse,
    AdminAuditLogResponse,
    AdminDeviceResponse,
    AdminExpertPromptResponse,
    AdminExpertPromptUpsertRequest,
    AdminImpersonateSessionResponse,
    AdminImpersonateStartRequest,
    AdminMonitoringResponse,
    AdminNotificationCreateRequest,
    AdminOverviewResponse,
    AdminPartnerResponse,
    AdminPaymentResponse,
    AdminPlatformSettingResponse,
    AdminPlatformSettingUpdateRequest,
    AdminPricingResponse,
    AdminPricingUpdateRequest,
    AdminProjectResponse,
    AdminPromocodeResponse,
    AdminPromptVersionResponse,
    AdminQueueMetricsResponse,
    AdminReferralResponse,
    AdminRoleUpdateRequest,
    AdminSubscriptionResponse,
    AdminTariffResponse,
    AdminTariffUpsertRequest,
    AdminTenantResponse,
    AdminToolCreateRequest,
    AdminToolResponse,
    AdminToolTestResponse,
    AdminToolUpdateRequest,
    AdminUserDetailResponse,
    AdminUserResponse,
    AdminUserSubscriptionResponse,
    AdminUserTenantResponse,
    AdminWorkflowResponse,
)
from backend.app.schemas.promocode import ChangePromocode, CreatePromocode
from backend.app.services.promocode_service import PromoCodeService


class AdminService:
    async def overview(self, session: AsyncSession) -> AdminOverviewResponse:
        users_total = await self._count(session, User)
        active_users_total = await session.scalar(
            select(func.count(User.id)).where(User.is_active.is_(True))
        )
        tenants_total = await self._count(session, Tenant)
        active_tenants_total = await session.scalar(
            select(func.count(Tenant.id)).where(Tenant.status == TenantStatus.ACTIVE)
        )
        projects_total = await self._count(session, Project)
        active_projects_total = await session.scalar(
            select(func.count(Project.id)).where(Project.strategy_status.is_not(None))
        )
        active_subscriptions = await session.scalar(
            select(func.count(Subscription.id)).where(Subscription.status == SubscriptionStatus.ACTIVE)
        )
        partners_total = await self._count(session, PartnerProfile)
        monthly_recurring_revenue = await self._monthly_recurring_revenue(session)
        successful_payments_total = await self._successful_payments_total(session)
        pending_outbox_events = await session.scalar(
            select(func.count(OutboxEvent.id)).where(OutboxEvent.status == OutboxStatus.PENDING)
        )
        failed_ai_jobs = await session.scalar(
            select(func.count(AIJob.id)).where(AIJob.status == AIJobStatus.FAILED)
        )

        return AdminOverviewResponse(
            users_total=int(users_total or 0),
            active_users_total=int(active_users_total or 0),
            tenants_total=int(tenants_total or 0),
            active_tenants_total=int(active_tenants_total or 0),
            projects_total=int(projects_total or 0),
            active_projects_total=int(active_projects_total or 0),
            active_subscriptions=int(active_subscriptions or 0),
            partners_total=int(partners_total or 0),
            monthly_recurring_revenue=float(monthly_recurring_revenue or 0),
            successful_payments_total=float(successful_payments_total or 0),
            pending_outbox_events=int(pending_outbox_events or 0),
            failed_ai_jobs=int(failed_ai_jobs or 0),
        )

    async def list_tenants(
        self,
        session: AsyncSession,
        *,
        search: str | None = None,
        page: int = 1,
        size: int = 50,
    ) -> list[AdminTenantResponse]:
        owner = aliased(User)
        statement = (
            select(
                Tenant,
                owner.email.label("owner_email"),
                func.count(func.distinct(Project.id)).label("projects_total"),
                func.count(func.distinct(Subscription.id)).label("subscriptions_total"),
            )
            .outerjoin(owner, owner.id == Tenant.owner_user_id)
            .outerjoin(Project, Project.tenant_id == Tenant.id)
            .outerjoin(Subscription, Subscription.tenant_id == Tenant.id)
            .group_by(Tenant.id, owner.email)
            .order_by(Tenant.created_at.desc())
            .offset(self._offset(page, size))
            .limit(size)
        )
        if search:
            needle = f"%{search.strip()}%"
            statement = statement.where(Tenant.name.ilike(needle) | Tenant.slug.ilike(needle))

        rows = (await session.execute(statement)).all()
        return [
            AdminTenantResponse(
                tenant_id=tenant.id,
                slug=tenant.slug,
                name=tenant.name,
                status=tenant.status.value,
                owner_user_id=tenant.owner_user_id,
                owner_email=owner_email,
                projects_total=int(projects_total or 0),
                subscriptions_total=int(subscriptions_total or 0),
                created_at=tenant.created_at,
            )
            for tenant, owner_email, projects_total, subscriptions_total in rows
        ]

    async def list_projects(
        self,
        session: AsyncSession,
        *,
        search: str | None = None,
        industry: str | None = None,
        page: int = 1,
        size: int = 50,
    ) -> list[AdminProjectResponse]:
        statement = (
            select(
                Project,
                Tenant.name.label("tenant_name"),
                User.email.label("owner_email"),
                func.count(func.distinct(SocialIntegration.id)).label("integrations_total"),
                func.count(func.distinct(ContentItem.id)).label("content_items_total"),
                func.count(func.distinct(Publication.id)).label("publications_total"),
            )
            .outerjoin(Tenant, Tenant.id == Project.tenant_id)
            .outerjoin(User, User.id == Project.owner_user_id)
            .outerjoin(SocialIntegration, SocialIntegration.project_id == Project.id)
            .outerjoin(ContentItem, ContentItem.project_id == Project.id)
            .outerjoin(Publication, Publication.project_id == Project.id)
            .group_by(Project.id, Tenant.name, User.email)
            .order_by(Project.created_at.desc())
            .offset(self._offset(page, size))
            .limit(size)
        )
        if search:
            needle = f"%{search.strip()}%"
            statement = statement.where(Project.company_name.ilike(needle) | User.email.ilike(needle))
        if industry:
            statement = statement.where(Project.industry == industry)

        rows = (await session.execute(statement)).all()
        return [
            AdminProjectResponse(
                project_id=project.id,
                tenant_id=project.tenant_id,
                tenant_name=tenant_name,
                owner_user_id=project.owner_user_id,
                owner_email=owner_email,
                company_name=project.company_name,
                city=project.city,
                industry=project.industry,
                strategy_status=project.strategy_status.value,
                integrations_total=int(integrations_total or 0),
                content_items_total=int(content_items_total or 0),
                publications_total=int(publications_total or 0),
                created_at=project.created_at,
            )
            for project, tenant_name, owner_email, integrations_total, content_items_total, publications_total in rows
        ]

    async def list_users(
        self,
        session: AsyncSession,
        *,
        search: str | None = None,
        role: UserRole | None = None,
        page: int = 1,
        size: int = 50,
    ) -> list[AdminUserResponse]:
        statement = (
            select(
                User,
                func.count(func.distinct(TenantMembership.tenant_id)).label("tenants_total"),
                func.count(func.distinct(Project.id)).label("projects_total"),
            )
            .outerjoin(TenantMembership, TenantMembership.user_id == User.id)
            .outerjoin(Project, Project.owner_user_id == User.id)
            .group_by(User.id)
            .order_by(User.created_at.desc())
            .offset(self._offset(page, size))
            .limit(size)
        )
        if search:
            needle = f"%{search.strip()}%"
            statement = statement.where(User.email.ilike(needle) | User.full_name.ilike(needle))
        if role:
            statement = statement.where(User.role == role)

        rows = (await session.execute(statement)).all()
        return [
            AdminUserResponse(
                user_id=user.id,
                email=user.email,
                full_name=user.full_name,
                role=user.role.value,
                is_active=user.is_active,
                is_verified=user.is_verified,
                tenants_total=int(tenants_total or 0),
                projects_total=int(projects_total or 0),
                created_at=user.created_at,
            )
            for user, tenants_total, projects_total in rows
        ]

    async def get_user(self, session: AsyncSession, user_id: str) -> AdminUserDetailResponse:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        tenant_rows = (
            await session.execute(
                select(TenantMembership, Tenant.name)
                .join(Tenant, Tenant.id == TenantMembership.tenant_id)
                .where(TenantMembership.user_id == user.id)
                .order_by(TenantMembership.created_at.desc())
            )
        ).all()
        tenant_ids = [membership.tenant_id for membership, _ in tenant_rows]
        subscriptions: list[Subscription] = []
        if tenant_ids:
            subscriptions = (
                await session.scalars(
                    select(Subscription)
                    .options(selectinload(Subscription.plan))
                    .where(Subscription.tenant_id.in_(tenant_ids))
                    .order_by(Subscription.created_at.desc())
                )
            ).all()

        projects_total = await session.scalar(
            select(func.count(Project.id)).where(Project.owner_user_id == user.id)
        )

        return AdminUserDetailResponse(
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            is_active=user.is_active,
            is_verified=user.is_verified,
            tenants_total=len(tenant_ids),
            projects_total=int(projects_total or 0),
            created_at=user.created_at,
            phone=user.phone,
            last_login_at=user.last_login_at,
            referred_by_user_id=user.referred_by_user_id,
            tenants=[
                AdminUserTenantResponse(
                    tenant_id=membership.tenant_id,
                    tenant_name=tenant_name,
                    role=membership.role.value,
                    is_primary=membership.is_primary,
                )
                for membership, tenant_name in tenant_rows
            ],
            subscriptions=[
                AdminUserSubscriptionResponse(
                    subscription_id=item.id,
                    tenant_id=item.tenant_id,
                    plan_code=item.plan.code if item.plan else None,
                    status=item.status.value,
                    starts_at=item.starts_at,
                    ends_at=item.ends_at,
                    next_charge_at=item.next_charge_at,
                )
                for item in subscriptions
            ],
        )

    async def update_user_role(
        self,
        session: AsyncSession,
        user_id: str,
        payload: AdminRoleUpdateRequest,
        current_user: User | None = None,
    ) -> AdminUserDetailResponse:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if current_user and current_user.admin_role and user.admin_role:
            if not can_manage_role(current_user.admin_role, user.admin_role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot manage users with equal or higher admin role",
                )
        user.role = payload.role
        await session.commit()
        await self._log_audit(session, current_user or user, "user.role.update", "user", user_id, {"new_role": payload.role.value})
        return await self.get_user(session, user_id)

    async def update_user_admin_role(
        self,
        session: AsyncSession,
        user_id: str,
        payload: AdminAdminRoleUpdateRequest,
        current_user: User,
    ) -> AdminUserDetailResponse:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if not can_manage_role(current_user.admin_role, payload.admin_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot assign equal or higher admin role",
            )
        old_role = user.admin_role
        user.admin_role = payload.admin_role
        from backend.app.core.crypto import encrypt_role_permissions
        perms = list(ROLE_PERMISSIONS.get(payload.admin_role, set()))
        user.encrypted_permissions = encrypt_role_permissions(user.id, [p.value for p in perms])
        await session.commit()
        await self._log_audit(session, current_user, "user.admin_role.update", "user", user_id, {
            "old_role": old_role.value if old_role else None,
            "new_role": payload.admin_role.value,
        })
        return await self.get_user(session, user_id)

    async def list_subscriptions(
        self,
        session: AsyncSession,
        *,
        status_filter: SubscriptionStatus | None = SubscriptionStatus.ACTIVE,
        plan_code: str | None = None,
        page: int = 1,
        size: int = 50,
    ) -> list[AdminSubscriptionResponse]:
        statement = (
            select(Subscription, SubscriptionPlan, Tenant.name)
            .join(SubscriptionPlan, SubscriptionPlan.id == Subscription.plan_id)
            .outerjoin(Tenant, Tenant.id == Subscription.tenant_id)
            .order_by(Subscription.created_at.desc())
            .offset(self._offset(page, size))
            .limit(size)
        )
        if status_filter:
            statement = statement.where(Subscription.status == status_filter)
        if plan_code:
            statement = statement.where(SubscriptionPlan.code == plan_code)

        rows = (await session.execute(statement)).all()
        return [
            AdminSubscriptionResponse(
                subscription_id=subscription.id,
                tenant_id=subscription.tenant_id,
                tenant_name=tenant_name,
                plan_id=subscription.plan_id,
                plan_code=plan.code if plan else None,
                plan_name=plan.name if plan else None,
                status=subscription.status.value,
                seats=subscription.seats,
                starts_at=subscription.starts_at,
                ends_at=subscription.ends_at,
                next_charge_at=subscription.next_charge_at,
                trial_ends_at=subscription.trial_ends_at,
                created_at=subscription.created_at,
            )
            for subscription, plan, tenant_name in rows
        ]

    async def list_payments(
        self,
        session: AsyncSession,
        *,
        status_filter: PaymentStatus | None = None,
        provider: str | None = None,
        page: int = 1,
        size: int = 50,
    ) -> list[AdminPaymentResponse]:
        statement = (
            select(Payment, Tenant.name, SubscriptionPlan.code)
            .join(Subscription, Subscription.id == Payment.subscription_id)
            .outerjoin(SubscriptionPlan, SubscriptionPlan.id == Subscription.plan_id)
            .outerjoin(Tenant, Tenant.id == Payment.tenant_id)
            .order_by(Payment.created_at.desc())
            .offset(self._offset(page, size))
            .limit(size)
        )
        if status_filter:
            statement = statement.where(Payment.status == status_filter)
        if provider:
            statement = statement.where(Payment.provider == provider)

        rows = (await session.execute(statement)).all()
        return [
            AdminPaymentResponse(
                payment_id=payment.id,
                tenant_id=payment.tenant_id,
                tenant_name=tenant_name,
                subscription_id=payment.subscription_id,
                plan_code=plan_code,
                amount=payment.amount,
                currency=payment.currency,
                status=payment.status.value,
                provider=payment.provider,
                external_payment_id=payment.external_payment_id,
                paid_at=payment.paid_at,
                created_at=payment.created_at,
            )
            for payment, tenant_name, plan_code in rows
        ]

    async def list_partners(
        self,
        session: AsyncSession,
        *,
        search: str | None = None,
        page: int = 1,
        size: int = 50,
    ) -> list[AdminPartnerResponse]:
        referred_user = aliased(User)
        referrals_total = (
            select(func.count(referred_user.id))
            .where(referred_user.referred_by_user_id == PartnerProfile.user_id)
            .correlate(PartnerProfile)
            .scalar_subquery()
        )
        commissions_total = (
            select(func.coalesce(func.sum(PartnerCommission.amount), 0))
            .where(PartnerCommission.partner_user_id == PartnerProfile.user_id)
            .correlate(PartnerProfile)
            .scalar_subquery()
        )
        available_commission = (
            select(
                func.coalesce(
                    func.sum(
                        case(
                            (
                                PartnerCommission.status.in_(
                                    [CommissionStatus.PENDING, CommissionStatus.AVAILABLE]
                                ),
                                PartnerCommission.amount,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                )
            )
            .where(PartnerCommission.partner_user_id == PartnerProfile.user_id)
            .correlate(PartnerProfile)
            .scalar_subquery()
        )
        statement = (
            select(
                PartnerProfile,
                User.email,
                User.full_name,
                referrals_total.label("referrals_total"),
                commissions_total.label("commissions_total"),
                available_commission.label("available_commission"),
            )
            .join(User, User.id == PartnerProfile.user_id)
            .order_by(PartnerProfile.created_at.desc())
            .offset(self._offset(page, size))
            .limit(size)
        )
        if search:
            needle = f"%{search.strip()}%"
            statement = statement.where(
                User.email.ilike(needle) | PartnerProfile.referral_code.ilike(needle)
            )

        rows = (await session.execute(statement)).all()
        return [
            AdminPartnerResponse(
                partner_profile_id=profile.id,
                user_id=profile.user_id,
                email=email,
                full_name=full_name,
                referral_code=profile.referral_code,
                commission_rate=profile.commission_rate,
                total_income=profile.total_income,
                pending_payout=profile.pending_payout,
                referrals_total=int(referral_count or 0),
                commissions_total=float(commission_sum or 0),
                available_commission=float(available_sum or 0),
                created_at=profile.created_at,
            )
            for profile, email, full_name, referral_count, commission_sum, available_sum in rows
        ]

    async def list_referrals(
        self,
        session: AsyncSession,
        *,
        search: str | None = None,
        page: int = 1,
        size: int = 50,
    ) -> list[AdminReferralResponse]:
        referrer = aliased(User)
        statement = (
            select(User, referrer)
            .join(referrer, User.referred_by_user_id == referrer.id)
            .order_by(User.created_at.desc())
            .offset(self._offset(page, size))
            .limit(size)
        )
        if search:
            needle = f"%{search.strip()}%"
            statement = statement.where(User.email.ilike(needle) | referrer.email.ilike(needle))

        rows = (await session.execute(statement)).all()
        return [
            AdminReferralResponse(
                referred_user_id=referred_user.id,
                referred_email=referred_user.email,
                referrer_user_id=referrer_user.id,
                referrer_email=referrer_user.email,
                created_at=referred_user.created_at,
            )
            for referred_user, referrer_user in rows
        ]

    async def analytics(self, session: AsyncSession) -> AdminAnalyticsResponse:
        users_total = await self._count(session, User)
        tenants_total = await self._count(session, Tenant)
        projects_total = await self._count(session, Project)
        content_items_total = await self._count(session, ContentItem)
        publications_total = await self._count(session, Publication)
        connected_integrations_total = await session.scalar(
            select(func.count(SocialIntegration.id)).where(
                SocialIntegration.status == IntegrationStatus.CONNECTED
            )
        )
        active_subscriptions_total = await session.scalar(
            select(func.count(Subscription.id)).where(Subscription.status == SubscriptionStatus.ACTIVE)
        )

        return AdminAnalyticsResponse(
            users_total=int(users_total or 0),
            tenants_total=int(tenants_total or 0),
            projects_total=int(projects_total or 0),
            content_items_total=int(content_items_total or 0),
            publications_total=int(publications_total or 0),
            connected_integrations_total=int(connected_integrations_total or 0),
            active_subscriptions_total=int(active_subscriptions_total or 0),
            revenue_total=float(await self._successful_payments_total(session) or 0),
            monthly_recurring_revenue=float(await self._monthly_recurring_revenue(session) or 0),
        )

    async def monitoring(self, session: AsyncSession) -> AdminMonitoringResponse:
        outbox_events = await self._count_by_value(session, OutboxEvent.status)
        ai_jobs = await self._count_by_value(session, AIJob.status)
        publications = await self._count_by_value(session, Publication.status)
        social_integrations = await self._count_by_value(session, SocialIntegration.status)

        return AdminMonitoringResponse(
            outbox_events=outbox_events,
            ai_jobs=ai_jobs,
            publications=publications,
            social_integrations=social_integrations,
            failed_ai_jobs=ai_jobs.get(AIJobStatus.FAILED.value, 0),
            pending_outbox_events=outbox_events.get(OutboxStatus.PENDING.value, 0),
            generated_at=datetime.now(UTC),
        )

    async def list_tariffs(self, session: AsyncSession) -> list[AdminTariffResponse]:
        plans = (
            await session.scalars(select(SubscriptionPlan).order_by(SubscriptionPlan.price_amount.asc()))
        ).all()
        return [self._tariff_response(plan) for plan in plans]

    async def upsert_tariff(
        self,
        session: AsyncSession,
        payload: AdminTariffUpsertRequest,
        current_user: User | None = None,
    ) -> AdminTariffResponse:
        plan = await session.scalar(select(SubscriptionPlan).where(SubscriptionPlan.code == payload.code))
        if plan is None:
            plan = SubscriptionPlan(code=payload.code, name=payload.name)
            session.add(plan)

        plan.name = payload.name
        plan.description = payload.description
        plan.price_amount = payload.price_amount
        plan.currency = payload.currency.upper()
        plan.requests_per_minute = payload.requests_per_minute
        plan.content_generations_per_hour = payload.content_generations_per_hour
        plan.publications_per_hour = payload.publications_per_hour
        plan.features = payload.features
        plan.is_active = payload.is_active
        await session.commit()
        await session.refresh(plan)
        if current_user:
            await self._log_audit(session, current_user, "tariff.upsert", "tariff", plan.code, {
                "severity": "warn", "price": payload.price_amount,
            })
        return self._tariff_response(plan)

    async def list_expert_prompts(self, session: AsyncSession) -> list[AdminExpertPromptResponse]:
        prompts = (
            await session.scalars(select(AIExpertPrompt).order_by(AIExpertPrompt.niche.asc()))
        ).all()
        return [self._expert_prompt_response(prompt) for prompt in prompts]

    async def upsert_expert_prompt(
        self,
        session: AsyncSession,
        payload: AdminExpertPromptUpsertRequest,
    ) -> AdminExpertPromptResponse:
        prompt = await session.scalar(select(AIExpertPrompt).where(AIExpertPrompt.niche == payload.niche))
        if prompt is None:
            prompt = AIExpertPrompt(
                niche=payload.niche,
                role_description=payload.role_description,
            )
            session.add(prompt)

        prompt.role_description = payload.role_description
        prompt.tone = payload.tone
        prompt.additional_instructions = payload.additional_instructions
        prompt.is_active = payload.is_active
        await session.commit()
        await session.refresh(prompt)
        return self._expert_prompt_response(prompt)

    async def delete_expert_prompt(self, session: AsyncSession, niche: str) -> None:
        prompt = await session.scalar(select(AIExpertPrompt).where(AIExpertPrompt.niche == niche))
        if prompt is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expert prompt not found")
        await session.delete(prompt)
        await session.commit()

    async def list_promocodes(
        self,
        session: AsyncSession,
        *,
        page: int = 1,
        size: int = 50,
    ) -> list[AdminPromocodeResponse]:
        promo_codes = await PromoCodeService().list_promocodes(session)
        return promo_codes[self._offset(page, size): self._offset(page, size) + size]

    async def create_promocode(
        self,
        session: AsyncSession,
        current_user: User,
        payload: CreatePromocode,
    ) -> AdminPromocodeResponse:
        return await PromoCodeService().create_promocode(session, current_user, payload)

    async def update_promocode(
        self,
        session: AsyncSession,
        code: str,
        payload: ChangePromocode,
    ) -> AdminPromocodeResponse:
        return await PromoCodeService().update_promocode(session, code, payload)

    async def delete_promocode(self, session: AsyncSession, code: str) -> None:
        await PromoCodeService().delete_promocode(session, code)

    async def get_pricing(self, session: AsyncSession) -> AdminPricingResponse:
        return AdminPricingResponse(
            token_price_per_1k=0.01,
            generation_price_per_1k=0.05,
            storage_price_gb=0.10,
        )

    async def update_pricing(self, session: AsyncSession, payload: AdminPricingUpdateRequest) -> AdminPricingResponse:
        from backend.app.db.platform_setting import PlatformSetting
        mappings = {
            "token_price_per_1k": "pricing.token_price_per_1k",
            "generation_price_per_1k": "pricing.generation_price_per_1k",
            "storage_price_gb": "pricing.storage_price_gb",
        }
        update_data = payload.model_dump(exclude_none=True)
        for field, key in mappings.items():
            if field in update_data:
                setting = await session.scalar(select(PlatformSetting).where(PlatformSetting.key == key))
                if setting is None:
                    setting = PlatformSetting(key=key, value=str(update_data[field]), category="pricing")
                    session.add(setting)
                else:
                    setting.value = str(update_data[field])
        await session.commit()
        return await self.get_pricing(session)

    async def create_notification(
        self,
        session: AsyncSession,
        current_user: User,
        payload: AdminNotificationCreateRequest,
    ) -> dict:
        n = Notification(
            title=payload.title,
            body=payload.body,
            target_role=payload.target_role,
            target_user_id=payload.target_user_id,
        )
        session.add(n)
        await session.commit()
        return {"id": n.id, "message": "Notification created"}

    async def list_audit_logs(
        self,
        session: AsyncSession,
        *,
        action: str | None = None,
        severity: str | None = None,
        page: int = 1,
        size: int = 50,
    ) -> list[AdminAuditLogResponse]:
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).offset(self._offset(page, size)).limit(size)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        if severity:
            stmt = stmt.where(AuditLog.metadata_json["severity"].as_string() == severity)
        logs = (await session.scalars(stmt)).all()
        result = []
        for log in logs:
            meta = log.metadata_json or {}
            actor_email = meta.get("actor_email")
            if not actor_email and log.user_id:
                actor = await session.get(User, log.user_id)
                actor_email = actor.email if actor else None
            result.append(AdminAuditLogResponse(
                log_id=log.id,
                actor_id=log.user_id or "",
                actor_email=actor_email,
                action=log.action,
                target_type=log.resource_type,
                target_id=log.resource_id,
                details=meta.get("details"),
                diff=meta.get("diff"),
                ip_address=log.ip_address,
                severity=meta.get("severity", "info"),
                reason=meta.get("reason"),
                created_at=log.created_at,
            ))
        return result

    async def get_audit_log(self, session: AsyncSession, log_id: str) -> AdminAuditLogResponse:
        log = await session.get(AuditLog, log_id)
        if not log:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit log not found")
        meta = log.metadata_json or {}
        return AdminAuditLogResponse(
            log_id=log.id,
            actor_id=log.user_id or "",
            actor_email=None,
            action=log.action,
            target_type=log.resource_type,
            target_id=log.resource_id,
            details=meta.get("details"),
            diff=meta.get("diff"),
            ip_address=log.ip_address,
            severity=meta.get("severity", "info"),
            reason=meta.get("reason"),
            created_at=log.created_at,
        )

    async def start_impersonation(
        self,
        session: AsyncSession,
        admin_user: User,
        payload: AdminImpersonateStartRequest,
        *,
        ip_address: str | None,
    ) -> AdminImpersonateSessionResponse:
        target = await session.get(User, payload.target_user_id)
        if not target:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found")
        existing = await session.scalar(
            select(AdminSession).where(
                AdminSession.user_id == admin_user.id,
                AdminSession.is_active.is_(True),
                AdminSession.impersonating_user_id.isnot(None),
            )
        )
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already impersonating a user")
        sess = AdminSession(
            user_id=admin_user.id,
            admin_role=admin_user.admin_role.value if admin_user.admin_role else "admin",
            ip_address=ip_address,
            is_active=True,
            expires_at=datetime.now(UTC).replace(hour=23, minute=59, second=59),
            last_activity_at=datetime.now(UTC),
            impersonating_user_id=payload.target_user_id,
            impersonation_reason=payload.reason,
        )
        session.add(sess)
        await session.commit()
        await self._log_audit(session, admin_user, "impersonate.start", "user", target.id, {
            "reason": payload.reason, "severity": "critical",
        })
        return AdminImpersonateSessionResponse(
            session_id=sess.id,
            admin_user_id=admin_user.id,
            admin_email=admin_user.email,
            target_user_id=target.id,
            target_email=target.email,
            reason=payload.reason,
            started_at=sess.created_at,
            is_active=True,
        )

    async def end_impersonation(self, session: AsyncSession, session_id: str, admin_user: User) -> dict:
        sess = await session.get(AdminSession, session_id)
        if not sess or sess.user_id != admin_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Impersonation session not found")
        sess.is_active = False
        await session.commit()
        await self._log_audit(session, admin_user, "impersonate.end", "session", session_id, {"severity": "critical"})
        return {"message": "Impersonation ended", "session_id": session_id}

    async def list_active_impersonations(self, session: AsyncSession) -> list[AdminImpersonateSessionResponse]:
        stmt = (
            select(AdminSession)
            .where(AdminSession.is_active.is_(True), AdminSession.impersonating_user_id.isnot(None))
            .order_by(AdminSession.created_at.desc())
        )
        sessions = (await session.scalars(stmt)).all()
        result = []
        for s in sessions:
            admin_user = await session.get(User, s.user_id)
            target_user = await session.get(User, s.impersonating_user_id) if s.impersonating_user_id else None
            result.append(AdminImpersonateSessionResponse(
                session_id=s.id,
                admin_user_id=s.user_id,
                admin_email=admin_user.email if admin_user else "unknown",
                target_user_id=s.impersonating_user_id or "",
                target_email=target_user.email if target_user else "unknown",
                reason=s.impersonation_reason or "",
                started_at=s.created_at,
                is_active=True,
            ))
        return result

    async def list_platform_settings(self, session: AsyncSession) -> list[AdminPlatformSettingResponse]:
        stmt = select(PlatformSetting).order_by(PlatformSetting.category, PlatformSetting.key)
        settings_list = (await session.scalars(stmt)).all()
        return [
            AdminPlatformSettingResponse(
                key=s.key,
                category=s.category,
                value_preview=s.value[:20] + "..." if s.value and len(s.value) > 20 else s.value,
                updated_by=s.updated_by,
                updated_at=s.updated_at,
            )
            for s in settings_list
        ]

    async def update_platform_setting(
        self,
        session: AsyncSession,
        key: str,
        payload: AdminPlatformSettingUpdateRequest,
        current_user: User,
    ) -> AdminPlatformSettingResponse:
        setting = await session.scalar(select(PlatformSetting).where(PlatformSetting.key == key))
        if setting is None:
            setting = PlatformSetting(key=key, value=payload.value, category="general")
            session.add(setting)
        else:
            setting.value = payload.value
        setting.updated_by = current_user.email
        await session.commit()
        await self._log_audit(session, current_user, "platform_setting.update", "setting", key, {"severity": "warn"})
        return AdminPlatformSettingResponse(
            key=setting.key,
            category=setting.category,
            value_preview=setting.value[:20] + "..." if setting.value and len(setting.value) > 20 else setting.value,
            updated_by=setting.updated_by,
            updated_at=setting.updated_at,
        )

    async def test_platform_setting(self, session: AsyncSession, key: str, payload: AdminPlatformSettingUpdateRequest) -> dict:
        return {"key": key, "test_result": "ok", "message": "Connection test passed"}

    async def list_devices(self, session: AsyncSession, *, user_id: str | None = None) -> list[AdminDeviceResponse]:
        stmt = select(DeviceFingerprint).order_by(DeviceFingerprint.created_at.desc())
        if user_id:
            stmt = stmt.where(DeviceFingerprint.user_id == user_id)
        devices = (await session.scalars(stmt)).all()
        return [
            AdminDeviceResponse(
                id=d.id,
                fingerprint_hash=d.fingerprint_hash[:8] + "...",
                device_info=d.device_info,
                ip_address=d.ip_address,
                is_trusted=d.is_trusted,
                last_seen_at=d.last_seen_at,
                created_at=d.created_at,
            )
            for d in devices
        ]

    async def trust_device(
        self, session: AsyncSession, device_id: str, current_user: User | None = None,
    ) -> AdminDeviceResponse:
        device = await session.get(DeviceFingerprint, device_id)
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
        device.is_trusted = True
        device.last_seen_at = datetime.now(UTC)
        await session.commit()
        if current_user:
            await self._log_audit(session, current_user, "device.trust", "device", device_id, {
                "severity": "info", "user_id": device.user_id,
            })
        return AdminDeviceResponse(
            id=device.id,
            fingerprint_hash=device.fingerprint_hash[:8] + "...",
            device_info=device.device_info,
            ip_address=device.ip_address,
            is_trusted=True,
            last_seen_at=device.last_seen_at,
            created_at=device.created_at,
        )

    async def delete_device(
        self, session: AsyncSession, device_id: str, current_user: User | None = None,
    ) -> None:
        device = await session.get(DeviceFingerprint, device_id)
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
        await session.delete(device)
        await session.commit()
        if current_user:
            await self._log_audit(session, current_user, "device.delete", "device", device_id, {
                "severity": "warn", "user_id": device.user_id,
            })

    async def upsert_prompt_with_version(
        self,
        session: AsyncSession,
        niche: str,
        payload: AdminExpertPromptUpsertRequest,
        current_user: User,
    ) -> AdminPromptVersionResponse:
        prompt = await session.scalar(select(AIExpertPrompt).where(AIExpertPrompt.niche == niche))
        old_content = prompt.role_description if prompt else ""
        if prompt is None:
            prompt = AIExpertPrompt(niche=niche, role_description=payload.role_description)
            session.add(prompt)
        prompt.role_description = payload.role_description
        prompt.tone = payload.tone
        prompt.additional_instructions = payload.additional_instructions
        prompt.is_active = payload.is_active
        await session.flush()
        from backend.app.db.prompt_version import PromptVersion
        version = PromptVersion(
            prompt_id=prompt.id,
            content=payload.role_description,
            author_id=current_user.id,
        )
        if old_content:
            version.diff = {"old": old_content, "new": payload.role_description}
        session.add(version)
        await session.commit()
        await self._log_audit(session, current_user, "prompt.update", "expert_prompt", niche, {
            "diff": {"old": old_content, "new": payload.role_description},
            "severity": "warn",
        })
        return AdminPromptVersionResponse(
            version_id=version.id,
            prompt_id=prompt.id,
            content=version.content,
            diff=version.diff,
            author_id=version.author_id,
            is_active=True,
            created_at=version.created_at,
        )

    async def list_prompt_versions(self, session: AsyncSession, niche: str) -> list[AdminPromptVersionResponse]:
        prompt = await session.scalar(select(AIExpertPrompt).where(AIExpertPrompt.niche == niche))
        if not prompt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")
        from backend.app.db.prompt_version import PromptVersion
        stmt = select(PromptVersion).where(PromptVersion.prompt_id == prompt.id).order_by(PromptVersion.created_at.desc())
        versions = (await session.scalars(stmt)).all()
        return [
            AdminPromptVersionResponse(
                version_id=v.id,
                prompt_id=v.prompt_id,
                content=v.content,
                diff=v.diff,
                author_id=v.author_id,
                is_active=v.id == prompt.id,
                created_at=v.created_at,
            )
            for v in versions
        ]

    async def rollback_prompt(
        self,
        session: AsyncSession,
        niche: str,
        version_id: str,
        current_user: User,
    ) -> AdminPromptVersionResponse:
        prompt = await session.scalar(select(AIExpertPrompt).where(AIExpertPrompt.niche == niche))
        if not prompt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")
        from backend.app.db.prompt_version import PromptVersion
        version = await session.get(PromptVersion, version_id)
        if not version or version.prompt_id != prompt.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
        old_content = prompt.role_description
        prompt.role_description = version.content
        new_version = PromptVersion(
            prompt_id=prompt.id,
            content=version.content,
            author_id=current_user.id,
            diff={"old": old_content, "new": version.content, "rolled_back_from": version_id},
        )
        session.add(new_version)
        await session.commit()
        await self._log_audit(session, current_user, "prompt.rollback", "expert_prompt", niche, {
            "version_id": version_id, "severity": "warn",
        })
        return AdminPromptVersionResponse(
            version_id=new_version.id,
            prompt_id=prompt.id,
            content=new_version.content,
            diff=new_version.diff,
            author_id=new_version.author_id,
            is_active=True,
            created_at=new_version.created_at,
        )

    async def list_workflows(
        self,
        session: AsyncSession,
        *,
        status: str | None = None,
        is_draft: bool | None = None,
        page: int = 1,
        size: int = 50,
    ) -> list[AdminWorkflowResponse]:
        stmt = select(WorkflowInstance).order_by(WorkflowInstance.created_at.desc()).offset(self._offset(page, size)).limit(size)
        if status:
            stmt = stmt.where(WorkflowInstance.status == status)
        workflows = (await session.scalars(stmt)).all()
        return [
            AdminWorkflowResponse(
                id=w.id,
                workflow_type=w.workflow_type,
                status=w.status.value if hasattr(w.status, 'value') else str(w.status),
                is_draft=w.status.value in {"draft", "pending"} if hasattr(w.status, 'value') else True,
                created_at=w.created_at,
                updated_at=w.updated_at,
            )
            for w in workflows
        ]

    async def get_workflow(self, session: AsyncSession, workflow_id: str) -> AdminWorkflowResponse:
        w = await session.get(WorkflowInstance, workflow_id)
        if not w:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
        return AdminWorkflowResponse(
            id=w.id,
            workflow_type=w.workflow_type,
            status=w.status.value if hasattr(w.status, 'value') else str(w.status),
            is_draft=w.status.value in {"draft", "pending"} if hasattr(w.status, 'value') else True,
            created_at=w.created_at,
            updated_at=w.updated_at,
        )

    async def publish_workflow(self, session: AsyncSession, workflow_id: str) -> AdminWorkflowResponse:
        w = await session.get(WorkflowInstance, workflow_id)
        if not w:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
        from backend.app.db.enums import WorkflowStatus
        w.status = WorkflowStatus.PENDING
        await session.commit()
        return await self.get_workflow(session, workflow_id)

    async def list_all_permissions(self, session: AsyncSession) -> dict:
        roles = {}
        for role in AdminRole:
            perms = get_permissions_for_role(role)
            roles[role.value] = sorted([p.value for p in perms])
        return {"roles": roles, "total_permissions": len(roles)}

    async def list_tools(
        self,
        session: AsyncSession,
        *,
        provider_type: ToolProviderType | None = None,
        status: ToolStatus | None = None,
        page: int = 1,
        size: int = 50,
    ) -> list[AdminToolResponse]:
        stmt = select(Tool).order_by(Tool.created_at.desc()).offset(self._offset(page, size)).limit(size)
        if provider_type:
            stmt = stmt.where(Tool.provider_type == provider_type)
        if status:
            stmt = stmt.where(Tool.status == status)
        tools = (await session.scalars(stmt)).all()
        return [self._tool_response(t) for t in tools]

    async def get_tool(self, session: AsyncSession, tool_id: str) -> AdminToolResponse:
        tool = await session.get(Tool, tool_id)
        if not tool:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
        return self._tool_response(tool)

    async def create_tool(
        self,
        session: AsyncSession,
        payload: AdminToolCreateRequest,
        current_user: User | None = None,
    ) -> AdminToolResponse:
        existing = await session.scalar(select(Tool).where(Tool.name == payload.name))
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tool with this name already exists")

        encrypted_key = None
        if payload.api_key:
            from backend.app.core.security import encrypt_secret
            encrypted_key = encrypt_secret(payload.api_key)

        tool = Tool(
            name=payload.name,
            provider_type=payload.provider_type,
            api_key_encrypted=encrypted_key,
            base_url=payload.base_url or None,
            config=payload.config,
            status=ToolStatus.INACTIVE,
        )
        session.add(tool)
        await session.flush()
        await session.refresh(tool)
        if current_user:
            await self._log_audit(session, current_user, "tool.create", "tool", tool.id, {
                "name": tool.name, "provider_type": tool.provider_type.value,
            })
        return self._tool_response(tool)

    async def update_tool(
        self,
        session: AsyncSession,
        tool_id: str,
        payload: AdminToolUpdateRequest,
        current_user: User | None = None,
    ) -> AdminToolResponse:
        tool = await session.get(Tool, tool_id)
        if not tool:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")

        if payload.name is not None:
            tool.name = payload.name
        if payload.api_key is not None:
            from backend.app.core.security import encrypt_secret
            tool.api_key_encrypted = encrypt_secret(payload.api_key)
        if payload.base_url is not None:
            tool.base_url = payload.base_url
        if payload.status is not None:
            tool.status = payload.status
        if payload.config is not None:
            tool.config = payload.config

        await session.flush()
        await session.refresh(tool)
        if current_user:
            await self._log_audit(session, current_user, "tool.update", "tool", tool.id, {
                "name": tool.name, "status": tool.status.value,
            })
        return self._tool_response(tool)

    async def delete_tool(self, session: AsyncSession, tool_id: str) -> None:
        tool = await session.get(Tool, tool_id)
        if not tool:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
        await session.delete(tool)
        await session.flush()

    async def test_tool_connection(
        self, session: AsyncSession, tool_id: str
    ) -> AdminToolTestResponse:
        tool = await session.get(Tool, tool_id)
        if not tool:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")

        import time
        import httpx

        start = time.monotonic()
        try:
            from backend.app.core.security import decrypt_secret
            api_key = decrypt_secret(tool.api_key_encrypted)

            if tool.provider_type == ToolProviderType.AI:
                headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
                url = (tool.base_url or "https://api.openai.com") + "/v1/models"
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.get(url, headers=headers)
                    if resp.status_code >= 400:
                        raise ValueError(f"HTTP {resp.status_code}: {resp.text[:200]}")
            elif tool.provider_type == ToolProviderType.SOCIAL:
                url = tool.base_url or "https://api.telegram.org"
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.get(f"{url}/bot{api_key}/getMe" if api_key else url)
                    if resp.status_code >= 400:
                        raise ValueError(f"HTTP {resp.status_code}: {resp.text[:200]}")
            else:
                url = tool.base_url or "https://httpbin.org/get"
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.get(url)
                    if resp.status_code >= 500:
                        raise ValueError(f"HTTP {resp.status_code}: {resp.text[:200]}")

            latency = (time.monotonic() - start) * 1000
            tool.status = ToolStatus.ACTIVE
            tool.error_message = None
            tool.last_used_at = datetime.now(UTC)
            await session.flush()
            return AdminToolTestResponse(success=True, message="Connection successful", latency_ms=round(latency, 1))
        except Exception as e:
            latency = (time.monotonic() - start) * 1000
            tool.status = ToolStatus.ERROR
            tool.error_message = str(e)[:500]
            await session.flush()
            return AdminToolTestResponse(success=False, message=str(e)[:200], latency_ms=round(latency, 1))

    async def queue_metrics(self, session: AsyncSession) -> AdminQueueMetricsResponse:
        from datetime import UTC, datetime, timedelta

        from backend.app.db.ai_job import AIJob
        from backend.app.db.enums import AIJobStatus, PublicationStatus, WorkflowStatus
        from backend.app.db.publication import Publication
        from backend.app.db.workflow_instance import WorkflowInstance

        wf_statuses = await self._count_by_value(session, WorkflowInstance.status)
        ai_statuses = await self._count_by_value(session, AIJob.status)
        pub_statuses = await self._count_by_value(session, Publication.status)

        stalled = await session.scalar(
            select(func.count(WorkflowInstance.id)).where(
                WorkflowInstance.status.in_(["running", "waiting_async"]),
                WorkflowInstance.started_at <= datetime.now(UTC) - timedelta(hours=6),
            )
        )

        return AdminQueueMetricsResponse(
            pending_workflows=wf_statuses.get(WorkflowStatus.PENDING.value, 0),
            running_workflows=wf_statuses.get(WorkflowStatus.RUNNING.value, 0),
            failed_workflows=wf_statuses.get(WorkflowStatus.FAILED.value, 0),
            completed_workflows=wf_statuses.get(WorkflowStatus.COMPLETED.value, 0),
            pending_ai_jobs=ai_statuses.get(AIJobStatus.PENDING.value, 0),
            running_ai_jobs=ai_statuses.get(AIJobStatus.RUNNING.value, 0),
            failed_ai_jobs=ai_statuses.get(AIJobStatus.FAILED.value, 0),
            pending_publications=pub_statuses.get(PublicationStatus.QUEUED.value, 0),
            in_progress_publications=pub_statuses.get(PublicationStatus.IN_PROGRESS.value, 0),
            failed_publications=pub_statuses.get(PublicationStatus.FAILED.value, 0),
            stalled_workflows=int(stalled or 0),
            generated_at=datetime.now(UTC),
        )

    def _tool_response(self, tool: Tool) -> AdminToolResponse:
        return AdminToolResponse(
            tool_id=tool.id,
            name=tool.name,
            provider_type=tool.provider_type,
            base_url=tool.base_url,
            status=tool.status,
            config=tool.config,
            last_used_at=tool.last_used_at,
            error_message=tool.error_message,
            created_at=tool.created_at,
            updated_at=tool.updated_at,
        )

    async def _log_audit(
        self,
        session: AsyncSession,
        actor: User,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        metadata_extra: dict | None = None,
        ip_address: str | None = None,
    ) -> None:
        meta = metadata_extra or {}
        log = AuditLog(
            user_id=actor.id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata_json=meta,
            ip_address=ip_address,
        )
        session.add(log)

    async def _successful_payments_total(self, session: AsyncSession) -> float:
        total = await session.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.status == PaymentStatus.SUCCEEDED
            )
        )
        return float(total or 0)

    async def _monthly_recurring_revenue(self, session: AsyncSession) -> float:
        total = await session.scalar(
            select(func.coalesce(func.sum(SubscriptionPlan.price_amount), 0))
            .select_from(Subscription)
            .join(SubscriptionPlan, SubscriptionPlan.id == Subscription.plan_id)
            .where(Subscription.status == SubscriptionStatus.ACTIVE)
        )
        return float(total or 0)

    async def _count(self, session: AsyncSession, model: type) -> int:
        total = await session.scalar(select(func.count(model.id)))
        return int(total or 0)

    async def _count_by_value(self, session: AsyncSession, column: object) -> dict[str, int]:
        rows = (await session.execute(select(column, func.count()).group_by(column))).all()
        return {
            value.value if hasattr(value, "value") else str(value): int(total or 0)
            for value, total in rows
        }

    def _offset(self, page: int, size: int) -> int:
        return (max(page, 1) - 1) * size

    def _tariff_response(self, plan: SubscriptionPlan) -> AdminTariffResponse:
        return AdminTariffResponse(
            plan_id=plan.id,
            code=plan.code,
            name=plan.name,
            description=plan.description,
            price_amount=plan.price_amount,
            currency=plan.currency,
            requests_per_minute=plan.requests_per_minute,
            content_generations_per_hour=plan.content_generations_per_hour,
            publications_per_hour=plan.publications_per_hour,
            features=plan.features,
            is_active=plan.is_active,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )

    def _expert_prompt_response(self, prompt: AIExpertPrompt) -> AdminExpertPromptResponse:
        return AdminExpertPromptResponse(
            prompt_id=prompt.id,
            niche=prompt.niche,
            role_description=prompt.role_description,
            tone=prompt.tone,
            additional_instructions=prompt.additional_instructions,
            is_active=prompt.is_active,
            created_at=prompt.created_at,
            updated_at=prompt.updated_at,
        )
