from __future__ import annotations

import re
from datetime import UTC, date, datetime, time, timedelta
from secrets import randbelow
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.api.deps import get_current_user
from backend.app.core.configs import settings
from backend.app.core.database import get_db_session
from backend.app.core.security import generate_referral_code, hash_email_otp
from backend.app.db.ai_job import AIJob
from backend.app.db.approval_policy import ApprovalPolicy
from backend.app.db.asset import Asset
from backend.app.db.content_item import ContentItem
from backend.app.db.email_verification_code import EmailVerificationCode
from backend.app.db.enums import (
    AIJobStatus,
    ApprovalMode,
    AssetType,
    ContentStatus,
    ContentType,
    IntegrationPlatform,
    IntegrationStatus,
    MembershipRole,
    PublicationStatus,
    StrategyStatus,
    SubscriptionStatus,
)
from backend.app.db.optimization_recommendation import OptimizationRecommendation
from backend.app.db.partner_profile import PartnerProfile
from backend.app.db.project import Project
from backend.app.db.project_strategy import ProjectStrategy
from backend.app.db.publication import Publication
from backend.app.db.social_integration import SocialIntegration
from backend.app.db.subscription import Subscription
from backend.app.db.subscription_plan import SubscriptionPlan
from backend.app.db.tenant import Tenant
from backend.app.db.tenant_membership import TenantMembership
from backend.app.db.user import User
from backend.app.events.schemas import AIRequestedEvent, EventEnvelope
from backend.app.infra.outbox import OutboxService
from backend.app.integrations.storage_client import StorageClient
from backend.app.modules.ai_optimization.service import AIOptimizationService
from backend.app.modules.analytics.service import AnalyticsService
from backend.app.modules.internship.service import InternshipService
from backend.app.modules.ai_retail.service import RetailService
from backend.app.modules.billing.service import BillingService
from backend.app.modules.billing.schemas import SubscriptionPlanResponse
from backend.app.modules.content_plan.schemas import GenerateContentPlanRequest
from backend.app.modules.content_plan.service import ContentPlanService
from backend.app.modules.identity.schemas import RegisterRequest, TokenResponse
from backend.app.modules.identity.service import IdentityService
from backend.app.modules.publishing.schemas import CreatePublicationRequest
from backend.app.modules.publishing.service import PublishingService
from backend.app.modules.social_integration.schemas import (
    SocialAuthorizeResponse,
    SocialConnectRequest,
    SocialOAuthCallbackRequest,
    SocialUpdateRequest,
)
from backend.app.modules.social_integration.service import SocialIntegrationService

router = APIRouter(tags=["product_flow"])


class BusinessProfileUpsertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_name: str = Field(min_length=2, max_length=255)
    inn: str | None = Field(default=None, min_length=10, max_length=12, pattern=r"^\d{10,12}$")
    description: str = Field(min_length=10)
    city: str = Field(min_length=2, max_length=120)
    industry: str = Field(default="other", max_length=120)
    services: list[str] = Field(default_factory=list)
    website: HttpUrl | None = None
    phone: str | None = None
    email: EmailStr | None = None
    target_audience: str = Field(min_length=5)
    competitors: list[str] = Field(default_factory=list)
    features: list[str] = Field(default_factory=list)
    social_links: list[str] = Field(default_factory=list)
    offer_accepted: bool | None = None
    data_confirmed: bool | None = None
    timezone: str = "UTC"


class BusinessProfileResponse(BaseModel):
    business_profile_id: str
    tenant_id: str
    company_name: str
    inn: str | None
    description: str
    city: str
    industry: str
    services: list[str]
    website: str | None
    phone: str | None
    email: str | None
    target_audience: str
    competitors: list[str]
    features: list[str]
    strategy_status: str
    offer_accepted: bool
    data_confirmed: bool
    onboarding_completed: bool
    created_at: datetime
    updated_at: datetime


class BusinessFileResponse(BaseModel):
    file_id: str
    business_profile_id: str
    type: str
    s3_key: str
    original_name: str
    url: str | None
    uploaded_at: datetime


class TaskResponse(BaseModel):
    job_id: str
    status: str
    task_type: str


class StrategyResponse(BaseModel):
    strategy_id: str | None
    status: str
    market_analysis: list[str]
    competitor_analysis: list[str]
    strategy_plan: dict[str, Any]
    content_strategy: dict[str, Any]


class SocialConnectCompatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    platform: str
    account_identifier: str = Field(min_length=2, max_length=255)
    access_token: str
    refresh_token: str | None = None
    token_expires_at: datetime | None = None
    settings: dict[str, Any] = Field(default_factory=dict)
    scopes: list[str] = Field(default_factory=list)


class SocialAccountResponse(BaseModel):
    id: str
    business_profile_id: str
    platform: str
    account_identifier: str
    status: str
    settings: dict[str, Any]


class ContentPlanGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    period_days: int = Field(default=30, ge=7, le=90)
    platforms: list[str] = Field(default_factory=lambda: ["telegram"])
    post_types: list[str] = Field(default_factory=lambda: ["post"])
    source_mode: str = "mixed"


class GeneratePostRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: str = Field(min_length=2)
    platform: str = "telegram"
    post_type: str = "post"
    source: str = "ai"
    prompt_context: dict[str, Any] = Field(default_factory=dict)


class PlannedPostResponse(BaseModel):
    id: str
    platform: str
    post_type: str
    scheduled_at: datetime
    status: str
    text: str
    media_s3_keys: list[str]
    ai_generated_text: str | None
    approval_mode: str


class RejectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    comment: str | None = None


class RescheduleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scheduled_at: datetime


class ApprovalSettingsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: str = Field(pattern="^(manual|auto)$")
    platforms: list[str] = Field(default_factory=list)
    auto_publish_enabled: bool = False


class PublishTriggerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    post_id: str


class PublishedPostResponse(BaseModel):
    publication_id: str
    planned_post_id: str | None
    platform: str
    status: str
    scheduled_at: datetime
    published_at: datetime | None
    platform_post_id: str | None


class AnalyticsSummaryResponse(BaseModel):
    followers: int
    impressions: int
    likes: int
    comments: int
    saves: int
    ctr: float
    er: float


class OptimizationStatusResponse(BaseModel):
    last_optimization_at: datetime | None
    recommendations_count: int
    mode: str


class PartnerDashboardResponse(BaseModel):
    referral_code: str
    referral_link: str
    total_referrals: int
    successful_payments_count: int
    total_commission: float
    available_balance: float
    commission_rate: float


class ProfileResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    role: str
    subscription: dict[str, Any] | None


class NotificationSettingsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email_enabled: bool = True
    telegram_enabled: bool = False
    digest_frequency: str = "weekly"


class SubscriptionChangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan: str
    promo_code: str | None = None
class PaymentWebhookRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subscription_id: str | None = None
    provider_payment_id: str
    amount: float = 0
    currency: str = "RUB"
    status: str = "succeeded"


class ReferralResolveResponse(BaseModel):
    referral_code: str | None
    is_valid: bool
    partner_user_id: str | None = None


class EmailCodeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr


class EmailCodeResponse(BaseModel):
    email: EmailStr
    status: str
    expires_at: datetime
    debug_code: str | None = None


class EmailConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class EmailConfirmResponse(BaseModel):
    email: EmailStr
    verified: bool


class RegistrationCompleteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: str = Field(min_length=1, max_length=120)
    last_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=10)
    email_code: str | None = Field(default=None, min_length=6, max_length=6, pattern=r"^\d{6}$")
    referral_code: str | None = None
    company_name: str = Field(min_length=2, max_length=255)
    category: str = Field(default="other", max_length=120)
    inn: str = Field(min_length=10, max_length=12, pattern=r"^\d{10,12}$")
    offer_accepted: bool
    data_confirmed: bool


class RegistrationCompleteResponse(BaseModel):
    auth: TokenResponse
    business_profile: BusinessProfileResponse


class RegistrationStatusResponse(BaseModel):
    user_registered: bool
    email_confirmed: bool
    company_completed: bool
    offer_accepted: bool
    data_confirmed: bool
    onboarding_completed: bool
    next_step: str


class UserDashboardResponse(BaseModel):
    user: ProfileResponse
    business_profile: BusinessProfileResponse | None
    subscription: dict[str, Any] | None
    connected_socials: list[SocialAccountResponse]
    can_run_brand_analysis: bool
    next_actions: list[str]


@router.get("/registration/referral", response_model=ReferralResolveResponse)
async def resolve_referral(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    code: str | None = Query(default=None),
) -> ReferralResolveResponse:
    referral_code = code.strip() if code else None
    if not referral_code:
        return ReferralResolveResponse(referral_code=None, is_valid=False)
    profile = await session.scalar(
        select(PartnerProfile).where(PartnerProfile.referral_code == referral_code)
    )
    return ReferralResolveResponse(
        referral_code=referral_code,
        is_valid=profile is not None,
        partner_user_id=profile.user_id if profile else None,
    )


@router.post("/registration/email/request-code", response_model=EmailCodeResponse)
async def request_email_code(
    payload: EmailCodeRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> EmailCodeResponse:
    email = _normalize_email(payload.email)
    code = f"{randbelow(1_000_000):06d}"
    expires_at = datetime.now(UTC) + timedelta(minutes=15)
    session.add(
        EmailVerificationCode(
            email=email,
            code_hash=_hash_email_code(email, code),
            expires_at=expires_at,
        )
    )
    await session.commit()
    return EmailCodeResponse(
        email=email,
        status="sent",
        expires_at=expires_at,
        debug_code=code if settings.app.env == "local" else None,
    )


@router.post("/registration/email/confirm", response_model=EmailConfirmResponse)
async def confirm_email_code(
    payload: EmailConfirmRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> EmailConfirmResponse:
    email = _normalize_email(payload.email)
    await _consume_email_verification(session, email, payload.code)
    return EmailConfirmResponse(email=email, verified=True)


@router.post("/registration/complete", response_model=RegistrationCompleteResponse, status_code=status.HTTP_201_CREATED)
async def complete_registration(
    payload: RegistrationCompleteRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RegistrationCompleteResponse:
    if not payload.offer_accepted or not payload.data_confirmed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Offer and data confirmation are required")

    email = _normalize_email(payload.email)
    if payload.email_code:
        try:
            await _consume_email_verification(session, email, payload.email_code)
        except HTTPException:
            if not await _has_recent_email_confirmation(session, email):
                raise
    elif not await _has_recent_email_confirmation(session, email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email confirmation is required")

    identity_service = IdentityService()
    await identity_service.register(
        session,
        request.app.state.redis,
        RegisterRequest(
            email=email,
            password=payload.password,
            full_name=f"{payload.first_name.strip()} {payload.last_name.strip()}",
            referral_code=payload.referral_code,
        ),
    )
    user = await session.scalar(select(User).where(User.email == email))
    if user is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Registered user was not persisted")
    user.is_verified = True
    await session.commit()
    auth = await identity_service.login(
        session,
        request.app.state.redis,
        email=email,
        password=payload.password,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    business_profile = await upsert_business_profile(
        BusinessProfileUpsertRequest(
            company_name=payload.company_name,
            inn=payload.inn,
            description=f"{payload.company_name} company profile for AI marketing analysis.",
            city="Not specified",
            industry=payload.category,
            target_audience="Customers interested in the company's services",
            offer_accepted=payload.offer_accepted,
            data_confirmed=payload.data_confirmed,
        ),
        user,
        session,
    )
    return RegistrationCompleteResponse(auth=auth, business_profile=business_profile)


@router.get("/registration/status", response_model=RegistrationStatusResponse)
async def registration_status(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RegistrationStatusResponse:
    context = await _get_primary_context(session, current_user, required=False)
    project = context[1] if context else None
    email_confirmed = current_user.is_verified or await _has_recent_email_confirmation(session, current_user.email)
    company_completed = bool(project and project.company_name and project.company_inn and project.industry)
    offer_accepted = bool(project and project.offer_accepted_at)
    data_confirmed = bool(project and project.data_confirmed_at)
    onboarding_completed = bool(project and project.onboarding_completed_at)
    next_step = _registration_next_step(
        email_confirmed=email_confirmed,
        company_completed=company_completed,
        offer_accepted=offer_accepted,
        data_confirmed=data_confirmed,
    )
    return RegistrationStatusResponse(
        user_registered=True,
        email_confirmed=email_confirmed,
        company_completed=company_completed,
        offer_accepted=offer_accepted,
        data_confirmed=data_confirmed,
        onboarding_completed=onboarding_completed,
        next_step=next_step,
    )


@router.get("/tariffs", response_model=list[SubscriptionPlanResponse])
async def tariffs(session: Annotated[AsyncSession, Depends(get_db_session)]) -> list[SubscriptionPlanResponse]:
    await _ensure_default_plans(session)
    return await BillingService().list_plans(session)


@router.get("/dashboard/user", response_model=UserDashboardResponse)
async def user_dashboard(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserDashboardResponse:
    base_profile = await profile(current_user, session)
    context = await _get_primary_context(session, current_user, required=False)
    if context is None:
        return UserDashboardResponse(
            user=base_profile,
            business_profile=None,
            subscription=None,
            connected_socials=[],
            can_run_brand_analysis=False,
            next_actions=["complete_registration"],
        )

    tenant, project = context
    socials = await list_social(current_user, session)
    try:
        subscription_payload = (await BillingService().get_subscription(session, current_user, tenant.id)).model_dump(
            mode="json"
        )
    except HTTPException:
        subscription_payload = None
    next_actions = _dashboard_next_actions(project, socials)
    return UserDashboardResponse(
        user=base_profile,
        business_profile=_business_profile_response(project),
        subscription=subscription_payload,
        connected_socials=socials,
        can_run_brand_analysis=bool(project.onboarding_completed_at),
        next_actions=next_actions,
    )


@router.post("/dashboard/brand-analysis", response_model=TaskResponse)
async def dashboard_brand_analysis(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TaskResponse:
    return await analyze_business(current_user, session)


@router.post("/business/profile", response_model=BusinessProfileResponse)
async def upsert_business_profile(
    payload: BusinessProfileUpsertRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> BusinessProfileResponse:
    confirmation_state = _confirmation_timestamps(payload)
    context = await _get_primary_context(session, current_user, required=False)
    if context is None:
        tenant = Tenant(
            slug=await _unique_tenant_slug(session, payload.company_name),
            name=payload.company_name,
            owner_user_id=current_user.id,
            default_timezone=payload.timezone,
            industry=payload.industry,
            city=payload.city,
            search_document=_search_document(payload),
        )
        session.add(tenant)
        await session.flush()
        session.add(
            TenantMembership(
                tenant_id=tenant.id,
                user_id=current_user.id,
                role=MembershipRole.OWNER,
                is_primary=True,
            )
        )
        project = Project(
            tenant_id=tenant.id,
            owner_user_id=current_user.id,
            company_name=payload.company_name,
            company_inn=payload.inn,
            business_description=payload.description,
            city=payload.city,
            industry=payload.industry.lower(),
            services=payload.services,
            website=str(payload.website) if payload.website else None,
            phone=payload.phone,
            email=str(payload.email) if payload.email else None,
            social_links=payload.social_links,
            target_audience=payload.target_audience,
            competitors=payload.competitors,
            business_features=payload.features,
            strategy_status=StrategyStatus.DRAFT,
            offer_accepted_at=confirmation_state["offer_accepted_at"],
            data_confirmed_at=confirmation_state["data_confirmed_at"],
            onboarding_completed_at=confirmation_state["onboarding_completed_at"],
            search_document=_search_document(payload),
        )
        session.add(project)
        await session.flush()
        session.add(
            ApprovalPolicy(
                tenant_id=tenant.id,
                project_id=project.id,
                mode=ApprovalMode.MANUAL,
            )
        )
    else:
        tenant, project = context
        tenant.name = payload.company_name
        tenant.industry = payload.industry.lower()
        tenant.city = payload.city
        tenant.search_document = _search_document(payload)
        project.company_name = payload.company_name
        if payload.inn is not None:
            project.company_inn = payload.inn
        project.business_description = payload.description
        project.city = payload.city
        project.industry = payload.industry.lower()
        project.services = payload.services
        project.website = str(payload.website) if payload.website else None
        project.phone = payload.phone
        project.email = str(payload.email) if payload.email else None
        project.social_links = payload.social_links
        project.target_audience = payload.target_audience
        project.competitors = payload.competitors
        project.business_features = payload.features
        project.search_document = _search_document(payload)
        _apply_confirmation_state(project, payload)

    await _ensure_default_subscription(session, tenant, current_user.id)
    await session.commit()
    await session.refresh(project)
    return _business_profile_response(project)


@router.get("/business/profile", response_model=BusinessProfileResponse)
async def get_business_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> BusinessProfileResponse:
    _, project = await _get_primary_context(session, current_user)
    return _business_profile_response(project)


@router.post("/business/files", response_model=BusinessFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_business_file(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    upload_type: Annotated[str, Form(alias="type")] = "other",
    file: UploadFile = File(...),
) -> BusinessFileResponse:
    tenant, project = await _get_primary_context(session, current_user)
    storage_uri, public_url = await StorageClient().store_upload(project.id, file)
    asset = Asset(
        tenant_id=tenant.id,
        project_id=project.id,
        asset_type=AssetType(upload_type),
        file_name=file.filename or "upload.bin",
        content_type=file.content_type or "application/octet-stream",
        storage_uri=storage_uri,
        public_url=public_url,
        size_bytes=0,
    )
    session.add(asset)
    await session.commit()
    await session.refresh(asset)
    return _business_file_response(asset)


@router.get("/business/files", response_model=list[BusinessFileResponse])
async def list_business_files(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[BusinessFileResponse]:
    tenant, project = await _get_primary_context(session, current_user)
    assets = (
        await session.scalars(
            select(Asset)
            .where(Asset.tenant_id == tenant.id, Asset.project_id == project.id)
            .order_by(Asset.created_at.desc())
        )
    ).all()
    return [_business_file_response(asset) for asset in assets]


@router.delete("/business/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business_file(
    file_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    tenant, project = await _get_primary_context(session, current_user)
    asset = await session.scalar(
        select(Asset).where(Asset.id == file_id, Asset.tenant_id == tenant.id, Asset.project_id == project.id)
    )
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    await session.delete(asset)
    await session.commit()


@router.post("/business/analyze", response_model=TaskResponse)
async def analyze_business(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TaskResponse:
    tenant, project = await _get_primary_context(session, current_user)
    job = AIJob(
        tenant_id=tenant.id,
        project_id=project.id,
        job_type="business_analysis",
        provider="queued",
        model="queued",
        status=AIJobStatus.PENDING,
        input_payload={"requested_by_user_id": current_user.id},
    )
    session.add(job)
    await session.flush()
    await OutboxService().enqueue(
        session,
        EventEnvelope(
            event_type="ai.requested",
            topic="ai.requested.v1",
            tenant_id=tenant.id,
            aggregate_id=job.id,
            payload=AIRequestedEvent(
                tenant_id=tenant.id,
                project_id=project.id,
                job_id=job.id,
                task_type=job.job_type,
            ).model_dump(mode="json"),
        ),
    )
    project.strategy_status = StrategyStatus.ANALYZING
    await session.commit()
    return TaskResponse(job_id=job.id, status=job.status.value, task_type=job.job_type)


@router.get("/business/strategy", response_model=StrategyResponse)
async def get_business_strategy(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> StrategyResponse:
    _, project = await _get_primary_context(session, current_user)
    strategy = await session.scalar(select(ProjectStrategy).where(ProjectStrategy.project_id == project.id))
    if strategy is None:
        return StrategyResponse(
            strategy_id=None,
            status=project.strategy_status.value,
            market_analysis=[],
            competitor_analysis=[],
            strategy_plan={},
            content_strategy={},
        )
    return StrategyResponse(
        strategy_id=strategy.id,
        status=project.strategy_status.value,
        market_analysis=strategy.market_analysis,
        competitor_analysis=strategy.competitor_analysis,
        strategy_plan={
            "positioning": strategy.positioning,
            "recommendations": strategy.recommendations,
            "publishing_frequency": strategy.publishing_frequency,
        },
        content_strategy={
            "content_pillars": strategy.content_pillars,
            "channels": strategy.channels,
            "optimization_mode": strategy.optimization_mode,
        },
    )


@router.get("/business/recommendations")
async def list_business_recommendations(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[dict[str, Any]]:
    tenant, project = await _get_primary_context(session, current_user)
    items = await AIOptimizationService().list_recommendations(session, current_user, tenant.id, project.id)
    return [item.model_dump(mode="json") for item in items]


@router.post("/social/connect", response_model=SocialAccountResponse)
async def connect_social(
    payload: SocialConnectCompatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SocialAccountResponse:
    tenant, project = await _get_primary_context(session, current_user)
    response = await SocialIntegrationService().connect(
        session,
        current_user,
        tenant.id,
        project.id,
        SocialConnectRequest(
            platform=payload.platform,
            account_handle=payload.account_identifier,
            access_token=payload.access_token,
            refresh_token=payload.refresh_token,
            autoposting_enabled=True,
            publication_settings=payload.settings,
            scopes=payload.scopes,
        ),
    )
    return _social_response(response.model_dump())


@router.get("/social/oauth/{platform}/authorize", response_model=SocialAuthorizeResponse)
async def social_oauth_authorize(
    platform: str,
    redirect_uri: str = Query(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SocialAuthorizeResponse:
    tenant, project = await _get_primary_context(session, current_user)
    return await SocialIntegrationService().begin_authorization(
        session, current_user, tenant.id, project.id, platform, redirect_uri,
    )


@router.post("/social/oauth/{platform}/callback", response_model=SocialAccountResponse)
async def social_oauth_callback(
    platform: str,
    payload: SocialOAuthCallbackRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SocialAccountResponse:
    tenant, project = await _get_primary_context(session, current_user)
    result = await SocialIntegrationService().complete_authorization(
        session, current_user, tenant.id, project.id, platform, payload,
    )
    return _social_response(result.model_dump())


@router.get("/social", response_model=list[SocialAccountResponse])
async def list_social(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[SocialAccountResponse]:
    tenant, project = await _get_primary_context(session, current_user)
    items = await SocialIntegrationService().list_connections(session, current_user, tenant.id, project.id)
    return [_social_response(item.model_dump()) for item in items]


@router.post("/social/analyze", response_model=TaskResponse)
async def analyze_social_channels(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TaskResponse:
    tenant, project = await _get_primary_context(session, current_user)
    integrations = (
        await session.scalars(
            select(SocialIntegration).where(
                SocialIntegration.tenant_id == tenant.id,
                SocialIntegration.project_id == project.id,
                SocialIntegration.status == IntegrationStatus.CONNECTED,
            )
        )
    ).all()
    if not integrations:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Connect at least one social account first")
    job = AIJob(
        tenant_id=tenant.id,
        project_id=project.id,
        job_type="social_channel_analysis",
        provider="queued",
        model="queued",
        status=AIJobStatus.PENDING,
        input_payload={
            "requested_by_user_id": current_user.id,
            "platforms": [integration.platform.value for integration in integrations],
            "account_handles": [integration.account_handle for integration in integrations],
        },
    )
    session.add(job)
    await session.flush()
    await OutboxService().enqueue(
        session,
        EventEnvelope(
            event_type="ai.requested",
            topic="ai.requested.v1",
            tenant_id=tenant.id,
            aggregate_id=job.id,
            payload=AIRequestedEvent(
                tenant_id=tenant.id,
                project_id=project.id,
                job_id=job.id,
                task_type=job.job_type,
            ).model_dump(mode="json"),
        ),
    )
    await session.commit()
    return TaskResponse(job_id=job.id, status=job.status.value, task_type=job.job_type)


@router.get("/social/analysis")
async def social_analysis(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    tenant, project = await _get_primary_context(session, current_user)
    integrations = (
        await session.scalars(
            select(SocialIntegration)
            .where(SocialIntegration.tenant_id == tenant.id, SocialIntegration.project_id == project.id)
            .order_by(SocialIntegration.created_at)
        )
    ).all()
    latest_job = await session.scalar(
        select(AIJob)
        .where(
            AIJob.tenant_id == tenant.id,
            AIJob.project_id == project.id,
            AIJob.job_type == "social_channel_analysis",
        )
        .order_by(AIJob.created_at.desc())
    )
    return {
        "business_profile_id": project.id,
        "status": latest_job.status.value if latest_job else "not_started",
        "summary": _social_analysis_summary(project, latest_job),
        "channels": [
            {
                "platform": integration.platform.value,
                "account_identifier": integration.account_handle,
                "status": integration.status.value,
                "growth_opportunities": _growth_opportunities(integration.platform.value),
            }
            for integration in integrations
        ],
        "next_actions": ["review_growth_opportunities", "generate_content_plan", "approve_posts"],
    }


@router.delete("/social/{platform}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_social(
    platform: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    tenant, project = await _get_primary_context(session, current_user)
    await SocialIntegrationService().disconnect(session, current_user, tenant.id, project.id, platform)


@router.put("/social/{platform}/settings", response_model=SocialAccountResponse)
async def update_social_settings(
    platform: str,
    settings_payload: dict[str, Any],
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SocialAccountResponse:
    tenant, project = await _get_primary_context(session, current_user)
    response = await SocialIntegrationService().update(
        session,
        current_user,
        tenant.id,
        project.id,
        platform,
        SocialUpdateRequest(publication_settings=settings_payload),
    )
    return _social_response(response.model_dump())


@router.get("/content/plan")
async def get_current_content_plan(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    tenant, project = await _get_primary_context(session, current_user)
    plan = await ContentPlanService().get_latest_plan(session, current_user, tenant.id, project.id)
    return plan.model_dump(mode="json")


@router.post("/content/plan/generate")
async def generate_content_plan(
    payload: ContentPlanGenerateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    tenant, project = await _get_primary_context(session, current_user)
    plan = await ContentPlanService().generate_plan(
        session,
        current_user,
        tenant.id,
        project.id,
        GenerateContentPlanRequest(
            period_days=payload.period_days,
            source_mode=payload.source_mode,
            platforms=payload.platforms,
            content_types=payload.post_types,
        ),
    )
    return plan.model_dump(mode="json")


@router.post("/content/posts/generate", response_model=PlannedPostResponse)
async def generate_post(
    payload: GeneratePostRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PlannedPostResponse:
    tenant, project = await _get_primary_context(session, current_user)
    item = ContentItem(
        tenant_id=tenant.id,
        project_id=project.id,
        platform=IntegrationPlatform(payload.platform),
        content_type=ContentType(payload.post_type),
        publish_date=datetime.now(UTC).date(),
        publish_time=time(hour=10),
        status=ContentStatus.GENERATED,
        title=payload.topic,
        text=f"{payload.topic}\n\nAI-generated draft for {project.company_name}.",
        metadata_json={"source": payload.source, "prompt_context": payload.prompt_context},
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return _planned_post_response(item)


@router.get("/content/posts", response_model=list[PlannedPostResponse])
async def list_posts(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    scheduled_date: date | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    platform: str | None = Query(default=None),
) -> list[PlannedPostResponse]:
    tenant, project = await _get_primary_context(session, current_user)
    query = select(ContentItem).where(ContentItem.tenant_id == tenant.id, ContentItem.project_id == project.id)
    if scheduled_date is not None:
        query = query.where(ContentItem.publish_date == scheduled_date)
    if status_filter:
        query = query.where(ContentItem.status == ContentStatus(status_filter))
    if platform:
        query = query.where(ContentItem.platform == IntegrationPlatform(platform))
    items = (await session.scalars(query.order_by(ContentItem.publish_date, ContentItem.publish_time))).all()
    return [_planned_post_response(item) for item in items]


@router.get("/approval/posts", response_model=list[PlannedPostResponse])
async def approval_posts(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[PlannedPostResponse]:
    tenant, project = await _get_primary_context(session, current_user)
    policy = await _get_or_create_policy(session, tenant.id, project.id)
    items = (
        await session.scalars(
            select(ContentItem)
            .where(
                ContentItem.tenant_id == tenant.id,
                ContentItem.project_id == project.id,
                ContentItem.status.in_([ContentStatus.GENERATED, ContentStatus.READY]),
            )
            .order_by(ContentItem.publish_date, ContentItem.publish_time)
        )
    ).all()
    return [_planned_post_response(item, approval_mode=policy.mode.value) for item in items]


@router.post("/approval/posts/{post_id}/approve", response_model=PlannedPostResponse)
async def approve_post(
    post_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PlannedPostResponse:
    tenant, project = await _get_primary_context(session, current_user)
    item = await _get_content_item(session, tenant.id, project.id, post_id)
    item.status = ContentStatus.APPROVED
    await session.commit()
    await _ensure_publication_for_item(session, current_user, tenant, project, item, approved=True)
    await session.refresh(item)
    return _planned_post_response(item)


@router.post("/approval/posts/{post_id}/reject", response_model=PlannedPostResponse)
async def reject_post(
    post_id: str,
    payload: RejectRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PlannedPostResponse:
    tenant, project = await _get_primary_context(session, current_user)
    item = await _get_content_item(session, tenant.id, project.id, post_id)
    item.status = ContentStatus.REJECTED
    item.metadata_json = {**item.metadata_json, "rejection_comment": payload.comment}
    await session.commit()
    await session.refresh(item)
    return _planned_post_response(item)


@router.post("/approval/posts/{post_id}/reschedule", response_model=PlannedPostResponse)
async def reschedule_post(
    post_id: str,
    payload: RescheduleRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PlannedPostResponse:
    tenant, project = await _get_primary_context(session, current_user)
    item = await _get_content_item(session, tenant.id, project.id, post_id)
    scheduled_at = payload.scheduled_at.astimezone(UTC)
    item.publish_date = scheduled_at.date()
    item.publish_time = scheduled_at.time().replace(tzinfo=None)
    await session.commit()
    await session.refresh(item)
    return _planned_post_response(item)


@router.put("/approval/settings")
async def update_approval_settings(
    payload: ApprovalSettingsRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    tenant, project = await _get_primary_context(session, current_user)
    policy = await _get_or_create_policy(session, tenant.id, project.id)
    policy.mode = ApprovalMode(payload.mode)
    policy.auto_publish_enabled = payload.auto_publish_enabled
    policy.auto_publish_platforms = payload.platforms
    await session.commit()
    return {
        "policy_id": policy.id,
        "mode": policy.mode.value,
        "auto_publish_enabled": policy.auto_publish_enabled,
        "platforms": policy.auto_publish_platforms,
    }


@router.post("/publishing/trigger")
async def trigger_publish(
    payload: PublishTriggerRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    tenant, project = await _get_primary_context(session, current_user)
    item = await _get_content_item(session, tenant.id, project.id, payload.post_id)
    publication = await _ensure_publication_for_item(session, current_user, tenant, project, item, approved=True)
    if publication is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No connected social accounts")
    return publication.model_dump(mode="json")


@router.get("/publishing/history", response_model=list[PublishedPostResponse])
async def publishing_history(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[PublishedPostResponse]:
    tenant, project = await _get_primary_context(session, current_user)
    publications = (
        await session.scalars(
            select(Publication)
            .options(selectinload(Publication.targets))
            .where(Publication.tenant_id == tenant.id, Publication.project_id == project.id)
            .order_by(Publication.created_at.desc())
        )
    ).all()
    return [
        PublishedPostResponse(
            publication_id=publication.id,
            planned_post_id=publication.content_item_id,
            platform=target.platform.value if publication.targets else "all",
            status=publication.status.value,
            scheduled_at=publication.scheduled_at,
            published_at=publication.targets[0].published_at if publication.targets else None,
            platform_post_id=publication.targets[0].external_post_id if publication.targets else None,
        )
        for publication in publications
        for target in (publication.targets or [None])
    ]


@router.get("/analytics/summary", response_model=AnalyticsSummaryResponse)
async def analytics_summary(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AnalyticsSummaryResponse:
    tenant, project = await _get_primary_context(session, current_user)
    overview = await AnalyticsService().get_overview(session, current_user, tenant.id, project.id)
    metrics = {metric.name: metric.value for metric in overview.metrics}
    return AnalyticsSummaryResponse(
        followers=int(metrics.get("followers", 0)),
        impressions=int(metrics.get("reach", 0)),
        likes=int(metrics.get("likes", 0)),
        comments=int(metrics.get("comments", 0)),
        saves=int(metrics.get("saves", 0)),
        ctr=float(metrics.get("ctr", 0)),
        er=float(metrics.get("er", 0)),
    )


@router.get("/analytics/platform/{platform}")
async def analytics_platform(
    platform: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    summary = await analytics_summary(current_user, session)
    return {"platform": platform, **summary.model_dump()}


@router.post("/analytics/refresh")
async def analytics_refresh(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    tenant, project = await _get_primary_context(session, current_user)
    overview = await AnalyticsService().get_overview(session, current_user, tenant.id, project.id)
    return {"snapshot_id": overview.snapshot_id, "status": "refreshed"}


@router.get("/analytics/recommendations")
async def analytics_recommendations(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[dict[str, Any]]:
    return await list_business_recommendations(current_user, session)


# ── Workspace: Internship ──────────────────────────────────────────

@router.get("/internship/state")
async def workspace_internship_state(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    ctx = await _get_primary_context(session, current_user, required=False)
    if ctx is None:
        return {"state": "not_started", "current_stage": 0, "total_stages": 6, "stage_name": "", "progress": 0, "started_at": None, "completed_at": None}
    tenant, project = ctx
    raw = await InternshipService().get_status(session, tenant.id, project.id)
    if raw.get("status") == "not_started":
        return {"state": "not_started", "current_stage": 0, "total_stages": 6, "stage_name": "", "progress": 0, "started_at": None, "completed_at": None}
    day = raw.get("day", 1)
    total = raw.get("total_days", 14)
    stage_names = ["Знакомство с брендом", "Анализ ниши", "Изучение аудитории", "Обучение тону коммуникации", "Тестовые публикации", "Финальное тестирование"]
    stage_num = min(int(day / 3) + 1, 6)
    return {
        "state": raw.get("status", "in_progress"),
        "current_stage": stage_num,
        "total_stages": 6,
        "stage_name": stage_names[stage_num - 1],
        "progress": round((day / total) * 100),
        "started_at": raw.get("started_at"),
        "completed_at": raw.get("completed_at"),
    }


@router.post("/internship/start")
async def workspace_internship_start(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    ctx = await _get_primary_context(session, current_user, required=False)
    if ctx is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Business profile required")
    tenant, project = ctx
    await InternshipService().start_internship(session, tenant.id, project.id)
    return {"state": "in_progress", "current_stage": 1, "total_stages": 6, "stage_name": "Знакомство с брендом", "progress": 7, "started_at": None, "completed_at": None}


# ── Workspace: Retail ─────────────────────────────────────────────

@router.get("/retail/metrics")
async def workspace_retail_metrics(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    ctx = await _get_primary_context(session, current_user, required=False)
    if ctx is None:
        return {"total_products": 0, "synced_products": 0, "last_sync": None, "active_offers": 0}
    tenant, project = ctx
    dash = await RetailService().get_dashboard(session, tenant.id, project.id)
    return {
        "total_products": dash.get("total_products", 0),
        "synced_products": (dash.get("last_sync") or {}).get("synced", 0) if dash.get("last_sync") else 0,
        "last_sync": (dash.get("last_sync") or {}).get("created_at") if dash.get("last_sync") else None,
        "active_offers": dash.get("on_sale_count", 0),
    }


@router.get("/retail/products")
async def workspace_retail_products(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[dict]:
    ctx = await _get_primary_context(session, current_user, required=False)
    if ctx is None:
        return []
    tenant, project = ctx
    raw = await RetailService().list_products(session, tenant.id, project.id)
    return [
        {
            "id": p.get("id", ""),
            "name": p.get("name", ""),
            "sku": p.get("external_id", ""),
            "price": p.get("price", 0),
            "status": "active" if p.get("is_on_sale") else "inactive",
        }
        for p in raw
    ]


@router.post("/retail/sync")
async def workspace_retail_sync(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    ctx = await _get_primary_context(session, current_user, required=False)
    if ctx is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Business profile required")
    tenant, project = ctx
    return await RetailService().sync_catalog(session, tenant.id, project.id)


# ── Workspace: AI Core ────────────────────────────────────────────

@router.get("/ai-core/status")
async def workspace_ai_core_status(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    from sqlalchemy import func
    from backend.app.db.workflow_instance import WorkflowInstance
    from backend.app.db.enums import WorkflowStatus
    active_count = 0
    try:
        ctx = await _get_primary_context(session, current_user, required=False)
        if ctx:
            tenant, project = ctx
            active_count = await session.scalar(
                select(func.count(WorkflowInstance.id)).where(
                    WorkflowInstance.tenant_id == tenant.id,
                    WorkflowInstance.project_id == project.id,
                    WorkflowInstance.status == WorkflowStatus.RUNNING.value,
                )
            ) or 0
    except Exception:
        active_count = 0
    return {
        "mode": "auto",
        "startup_phase": "ready",
        "health": "healthy",
        "pipelines_active": active_count,
        "pipelines_queued": 0,
        "pipelines_completed": 0,
        "pipelines_failed": 0,
        "uptime_seconds": 0,
    }


@router.get("/ai-core/pipelines")
async def workspace_ai_core_pipelines(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[dict]:
    return []


@router.get("/optimization/status", response_model=OptimizationStatusResponse)
async def optimization_status(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> OptimizationStatusResponse:
    tenant, project = await _get_primary_context(session, current_user)
    latest = await session.scalar(
        select(OptimizationRecommendation)
        .where(OptimizationRecommendation.tenant_id == tenant.id, OptimizationRecommendation.project_id == project.id)
        .order_by(OptimizationRecommendation.created_at.desc())
    )
    count = await session.scalar(
        select(func.count(OptimizationRecommendation.id)).where(
            OptimizationRecommendation.tenant_id == tenant.id,
            OptimizationRecommendation.project_id == project.id,
        )
    )
    strategy = await session.scalar(select(ProjectStrategy).where(ProjectStrategy.project_id == project.id))
    return OptimizationStatusResponse(
        last_optimization_at=latest.created_at if latest else None,
        recommendations_count=int(count or 0),
        mode=strategy.optimization_mode if strategy else "manual_confirmation",
    )


@router.post("/optimization/run")
async def optimization_run(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    tenant, project = await _get_primary_context(session, current_user)
    result = await AIOptimizationService().trigger(session, current_user, tenant.id, project.id, "manual_run")
    return result.model_dump(mode="json")


@router.put("/optimization/settings")
async def optimization_settings(
    payload: dict[str, Any],
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    tenant, project = await _get_primary_context(session, current_user)
    strategy = await session.scalar(select(ProjectStrategy).where(ProjectStrategy.project_id == project.id))
    if strategy is None:
        strategy = ProjectStrategy(tenant_id=tenant.id, project_id=project.id)
        session.add(strategy)
    strategy.optimization_mode = str(payload.get("mode", "manual_confirmation"))
    await session.commit()
    return {"mode": strategy.optimization_mode}


@router.get("/partner/dashboard", response_model=PartnerDashboardResponse)
async def partner_dashboard(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PartnerDashboardResponse:
    profile = await _get_or_create_partner_profile(session, current_user)
    referrals = await session.scalar(select(func.count(User.id)).where(User.referred_by_user_id == current_user.id))
    return PartnerDashboardResponse(
        referral_code=profile.referral_code,
        referral_link=f"{settings.web.public_base_url.rstrip('/')}/ref/{profile.referral_code}",
        total_referrals=int(referrals or 0),
        successful_payments_count=0,
        total_commission=profile.total_income,
        available_balance=profile.pending_payout,
        commission_rate=profile.commission_rate,
    )


@router.get("/partner/referral-link")
async def partner_referral_link(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, str]:
    dashboard = await partner_dashboard(current_user, session)
    return {"referral_code": dashboard.referral_code, "referral_link": dashboard.referral_link}


@router.get("/partner/payout-history")
async def partner_payout_history(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[dict[str, Any]]:
    commissions = await BillingService().list_commissions(session, current_user)
    return [item.model_dump(mode="json") for item in commissions]


@router.post("/partner/request-payout")
async def partner_request_payout(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    dashboard = await partner_dashboard(current_user, session)
    return {"status": "requested", "amount": dashboard.available_balance}


@router.get("/profile", response_model=ProfileResponse)
async def profile(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ProfileResponse:
    context = await _get_primary_context(session, current_user, required=False)
    subscription = None
    if context is not None:
        tenant, _ = context
        try:
            subscription = (await BillingService().get_subscription(session, current_user, tenant.id)).model_dump(
                mode="json"
            )
        except HTTPException:
            subscription = None
    return ProfileResponse(
        user_id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.value,
        subscription=subscription,
    )


@router.put("/profile/notifications")
async def profile_notifications(
    payload: NotificationSettingsRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    current_user.is_verified = current_user.is_verified
    await session.commit()
    return {"status": "updated", "settings": payload.model_dump(mode="json")}


@router.get("/subscription")
async def subscription(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    tenant, _ = await _get_primary_context(session, current_user)
    response = await BillingService().get_subscription(session, current_user, tenant.id)
    return response.model_dump(mode="json")


@router.post("/subscription/change")
async def subscription_change(
    payload: SubscriptionChangeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    tenant, _ = await _get_primary_context(session, current_user)
    response = await BillingService().change_plan(
        session,
        current_user,
        tenant.id,
        payload.plan,
        payload.promo_code,
    )
    return response.model_dump(mode="json")


@router.get("/payments")
async def payments(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[dict[str, Any]]:
    tenant, _ = await _get_primary_context(session, current_user)
    response = await BillingService().list_payments(session, current_user, tenant.id)
    return [item.model_dump(mode="json") for item in response]


@router.post("/payments/webhook")
async def payments_webhook(
    payload: PaymentWebhookRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    if payload.status != "succeeded":
        return {"status": "ignored"}

    payment = await BillingService().record_successful_payment(
        session,
        subscription_id=payload.subscription_id,
        external_payment_id=payload.provider_payment_id,
        amount=payload.amount,
        currency=payload.currency,
        provider="webhook",
        metadata=payload.model_dump(mode="json"),
    )
    return {"status": "accepted", "payment_id": payment.id}


async def _get_primary_context(
    session: AsyncSession,
    current_user: User,
    *,
    required: bool = True,
) -> tuple[Tenant, Project] | None:
    query = (
        select(Tenant, Project)
        .join(TenantMembership, TenantMembership.tenant_id == Tenant.id)
        .join(Project, Project.tenant_id == Tenant.id)
        .where(TenantMembership.user_id == current_user.id)
        .order_by(TenantMembership.is_primary.desc(), Project.created_at.desc())
    )
    row = (await session.execute(query)).first()
    if row is None:
        if required:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business profile not found. Создайте компанию в настройках.")
        return None
    return row[0], row[1]


async def _consume_email_verification(session: AsyncSession, email: str, code: str) -> None:
    now = datetime.now(UTC)
    verification = await session.scalar(
        select(EmailVerificationCode)
        .where(
            EmailVerificationCode.email == email,
            EmailVerificationCode.consumed_at.is_(None),
            EmailVerificationCode.expires_at > now,
        )
        .order_by(EmailVerificationCode.created_at.desc())
    )
    if verification is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code expired or not found")
    if verification.attempts >= 5:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many verification attempts")
    if verification.code_hash != _hash_email_code(email, code):
        verification.attempts += 1
        await session.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code")

    verification.consumed_at = now
    user = await session.scalar(select(User).where(User.email == email))
    if user is not None:
        user.is_verified = True
    await session.commit()


async def _has_recent_email_confirmation(session: AsyncSession, email: str) -> bool:
    since = datetime.now(UTC) - timedelta(hours=24)
    verification = await session.scalar(
        select(EmailVerificationCode)
        .where(
            EmailVerificationCode.email == _normalize_email(email),
            EmailVerificationCode.consumed_at.is_not(None),
            EmailVerificationCode.consumed_at >= since,
        )
        .order_by(EmailVerificationCode.consumed_at.desc())
    )
    return verification is not None


async def _get_content_item(
    session: AsyncSession,
    tenant_id: str,
    project_id: str,
    post_id: str,
) -> ContentItem:
    item = await session.scalar(
        select(ContentItem).where(
            ContentItem.id == post_id,
            ContentItem.tenant_id == tenant_id,
            ContentItem.project_id == project_id,
        )
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return item


async def _ensure_publication_for_item(
    session: AsyncSession,
    current_user: User,
    tenant: Tenant,
    project: Project,
    item: ContentItem,
    *,
    approved: bool,
) -> Any | None:
    existing = await session.scalar(
        select(Publication)
        .options(selectinload(Publication.targets))
        .where(Publication.tenant_id == tenant.id, Publication.content_item_id == item.id)
    )
    if existing is not None:
        if approved:
            existing.status = PublicationStatus.APPROVED
            await session.commit()
        return await PublishingService().get_publication(session, current_user, tenant.id, existing.id)

    integrations = (
        await session.scalars(
            select(SocialIntegration).where(
                SocialIntegration.tenant_id == tenant.id,
                SocialIntegration.project_id == project.id,
                SocialIntegration.status == IntegrationStatus.CONNECTED,
                SocialIntegration.autoposting_enabled.is_(True),
            )
        )
    ).all()
    if not integrations:
        return None

    scheduled_at = datetime.combine(item.publish_date, item.publish_time).replace(tzinfo=UTC)
    publication = await PublishingService().create_publication(
        session,
        current_user,
        tenant.id,
        project.id,
        CreatePublicationRequest(
            content_item_id=item.id,
            integration_ids=[integration.id for integration in integrations],
            scheduled_at=scheduled_at,
            all_or_nothing=True,
        ),
    )
    if approved:
        publication = await PublishingService().mark_approved(session, current_user, tenant.id, publication.publication_id)
    return publication


async def _get_or_create_policy(session: AsyncSession, tenant_id: str, project_id: str) -> ApprovalPolicy:
    policy = await session.scalar(
        select(ApprovalPolicy).where(ApprovalPolicy.tenant_id == tenant_id, ApprovalPolicy.project_id == project_id)
    )
    if policy is None:
        policy = ApprovalPolicy(tenant_id=tenant_id, project_id=project_id, mode=ApprovalMode.MANUAL)
        session.add(policy)
        await session.flush()
    return policy


async def _ensure_default_subscription(session: AsyncSession, tenant: Tenant, user_id: str) -> None:
    existing = await session.scalar(select(Subscription).where(Subscription.tenant_id == tenant.id))
    if existing is not None:
        return
    plan = await session.scalar(select(SubscriptionPlan).where(SubscriptionPlan.code == "starter"))
    if plan is None:
        plan = SubscriptionPlan(code="starter", name="Starter", price_amount=0, currency=settings.billing.currency)
        session.add(plan)
        await session.flush()
    if settings.database_uses_sqlite and await _sqlite_has_column(session, "subscriptions", "user_id"):
        now = datetime.now(UTC).replace(tzinfo=None)
        await session.execute(
            text(
                """
                INSERT INTO subscriptions
                (id, user_id, tenant_id, plan_id, plan_name, status, amount, billing_period,
                 starts_at, seats, created_at, updated_at)
                VALUES
                (:id, :user_id, :tenant_id, :plan_id, 'starter', 'TRIAL', 0, 'monthly',
                 :starts_at, 1, :created_at, :updated_at)
                """
            ),
            {
                "id": _uuid(),
                "user_id": user_id,
                "tenant_id": tenant.id,
                "plan_id": plan.id,
                "starts_at": now,
                "created_at": now,
                "updated_at": now,
            },
        )
        return
    session.add(
        Subscription(
            tenant_id=tenant.id,
            plan_id=plan.id,
            status=SubscriptionStatus.TRIAL,
            starts_at=datetime.now(UTC),
        )
    )


async def _ensure_default_plans(session: AsyncSession) -> None:
    created = False
    for plan in _default_plan_payloads():
        existing = await session.scalar(select(SubscriptionPlan).where(SubscriptionPlan.code == plan["code"]))
        if existing is None:
            session.add(SubscriptionPlan(currency=settings.billing.currency, **plan))
            created = True
    if created:
        await session.commit()


async def _get_or_create_partner_profile(session: AsyncSession, current_user: User):
    from backend.app.db.partner_profile import PartnerProfile

    profile = await session.scalar(select(PartnerProfile).where(PartnerProfile.user_id == current_user.id))
    if profile is None:
        profile = PartnerProfile(
            user_id=current_user.id,
            referral_code=generate_referral_code(current_user.full_name),
            commission_rate=settings.billing.partner_commission_rate,
        )
        session.add(profile)
        await session.commit()
        await session.refresh(profile)
    return profile


async def _unique_tenant_slug(session: AsyncSession, company_name: str) -> str:
    base = _slugify(company_name)
    candidate = base
    suffix = 1
    while await session.scalar(select(Tenant).where(Tenant.slug == candidate)):
        suffix += 1
        candidate = f"{base}-{suffix}"
    return candidate


def _normalize_email(email: str | EmailStr) -> str:
    return str(email).strip().lower()


def _hash_email_code(email: str, code: str) -> str:
    return hash_email_otp(email, code)


def _confirmation_timestamps(payload: BusinessProfileUpsertRequest) -> dict[str, datetime | None]:
    now = datetime.now(UTC)
    offer_accepted_at = now if payload.offer_accepted is True else None
    data_confirmed_at = now if payload.data_confirmed is True else None
    onboarding_completed_at = (
        now
        if payload.inn and payload.offer_accepted is True and payload.data_confirmed is True
        else None
    )
    return {
        "offer_accepted_at": offer_accepted_at,
        "data_confirmed_at": data_confirmed_at,
        "onboarding_completed_at": onboarding_completed_at,
    }


def _apply_confirmation_state(project: Project, payload: BusinessProfileUpsertRequest) -> None:
    now = datetime.now(UTC)
    if payload.offer_accepted is not None:
        project.offer_accepted_at = now if payload.offer_accepted else None
    if payload.data_confirmed is not None:
        project.data_confirmed_at = now if payload.data_confirmed else None
    if project.company_inn and project.offer_accepted_at and project.data_confirmed_at:
        project.onboarding_completed_at = project.onboarding_completed_at or now
    else:
        project.onboarding_completed_at = None


def _registration_next_step(
    *,
    email_confirmed: bool,
    company_completed: bool,
    offer_accepted: bool,
    data_confirmed: bool,
) -> str:
    if not email_confirmed:
        return "confirm_email"
    if not company_completed:
        return "company_form"
    if not offer_accepted or not data_confirmed:
        return "final_confirmation"
    return "tariffs"


def _dashboard_next_actions(project: Project, socials: list[SocialAccountResponse]) -> list[str]:
    actions: list[str] = []
    if not project.onboarding_completed_at:
        actions.append("complete_registration")
    if not socials:
        actions.append("connect_social_networks")
    if project.onboarding_completed_at:
        actions.append("run_brand_analysis")
    actions.append("review_tariffs")
    return actions


def _social_analysis_summary(project: Project, latest_job: AIJob | None) -> dict[str, Any]:
    if latest_job and latest_job.output_payload:
        return latest_job.output_payload
    return {
        "company_name": project.company_name,
        "industry": project.industry,
        "message": "Social channel analysis is ready to run or still being processed.",
    }


def _growth_opportunities(platform: str) -> list[str]:
    defaults = {
        "telegram": ["tighten channel positioning", "add weekly expert rubric", "track post saves and comments"],
        "vk": ["segment community content", "reuse best Telegram posts", "increase native discussion hooks"],
        "instagram": ["strengthen visual proof", "use reels for top-of-funnel reach", "move leads to direct messages"],
        "threads": ["test founder-style short opinions", "repurpose expert insights", "measure replies"],
        "tiktok": ["turn FAQs into short videos", "test creator-style hooks", "publish in repeatable series"],
        "youtube": ["create educational playlists", "reuse shorts from social topics", "optimize titles by search intent"],
        "whatsapp_business": ["automate quick replies", "tag warm leads", "connect content CTAs to chats"],
        "max": ["validate audience fit", "adapt concise updates", "monitor early engagement signals"],
    }
    return defaults.get(platform, ["collect baseline metrics", "test three content angles", "measure engagement rate"])


def _default_plan_payloads() -> list[dict[str, Any]]:
    return [
        {
            "code": "starter",
            "name": "Starter",
            "description": "MVP plan for one brand and core AI marketing workflow.",
            "price_amount": 14900,
            "requests_per_minute": 120,
            "content_generations_per_hour": 80,
            "publications_per_hour": 30,
            "features": {"projects": 1, "platforms": ["telegram", "vk"], "analytics": True},
        },
        {
            "code": "growth",
            "name": "Growth",
            "description": "Plan for growing teams with optimization and more social channels.",
            "price_amount": 39900,
            "requests_per_minute": 240,
            "content_generations_per_hour": 200,
            "publications_per_hour": 80,
            "features": {"projects": 3, "platforms": ["telegram", "vk", "instagram", "threads"], "analytics": True},
        },
        {
            "code": "scale",
            "name": "Scale",
            "description": "Agency-grade plan for multi-brand publishing and analytics.",
            "price_amount": 89900,
            "requests_per_minute": 500,
            "content_generations_per_hour": 500,
            "publications_per_hour": 200,
            "features": {"projects": 10, "platforms": "all", "priority_support": True},
        },
    ]


def _business_profile_response(project: Project) -> BusinessProfileResponse:
    return BusinessProfileResponse(
        business_profile_id=project.id,
        tenant_id=project.tenant_id,
        company_name=project.company_name,
        inn=project.company_inn,
        description=project.business_description,
        city=project.city,
        industry=project.industry,
        services=project.services,
        website=project.website,
        phone=project.phone,
        email=project.email,
        target_audience=project.target_audience,
        competitors=project.competitors,
        features=project.business_features,
        strategy_status=project.strategy_status.value,
        offer_accepted=project.offer_accepted_at is not None,
        data_confirmed=project.data_confirmed_at is not None,
        onboarding_completed=project.onboarding_completed_at is not None,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def _business_file_response(asset: Asset) -> BusinessFileResponse:
    return BusinessFileResponse(
        file_id=asset.id,
        business_profile_id=asset.project_id,
        type=asset.asset_type.value,
        s3_key=asset.storage_uri,
        original_name=asset.file_name,
        url=asset.public_url,
        uploaded_at=asset.created_at,
    )


def _social_response(payload: dict[str, Any]) -> SocialAccountResponse:
    return SocialAccountResponse(
        id=payload["integration_id"],
        business_profile_id=payload["project_id"],
        platform=payload["platform"],
        account_identifier=payload["account_handle"],
        status=payload["status"],
        settings=payload["publication_settings"],
    )


def _planned_post_response(item: ContentItem, *, approval_mode: str = "manual") -> PlannedPostResponse:
    scheduled_at = datetime.combine(item.publish_date, item.publish_time).replace(tzinfo=UTC)
    return PlannedPostResponse(
        id=item.id,
        platform=item.platform.value,
        post_type=item.content_type.value,
        scheduled_at=scheduled_at,
        status=_compat_post_status(item.status),
        text=item.text,
        media_s3_keys=[
            key
            for key in [item.image_url, item.video_url]
            if key
        ],
        ai_generated_text=item.text,
        approval_mode=approval_mode,
    )


def _compat_post_status(status_value: ContentStatus) -> str:
    if status_value in {ContentStatus.GENERATED, ContentStatus.READY}:
        return "pending_approval"
    return status_value.value


def _search_document(payload: BusinessProfileUpsertRequest) -> str:
    return " ".join(
        [
            payload.company_name,
            payload.inn or "",
            payload.description,
            payload.industry,
            payload.target_audience,
            " ".join(payload.services),
            " ".join(payload.features),
        ]
    )


def _slugify(value: str) -> str:
    normalized = "".join(char.lower() if char.isalnum() else "-" for char in value)
    collapsed = "-".join(part for part in normalized.split("-") if part)
    return collapsed[:80] or "business"


_TABLE_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]{0,127}$")


async def _sqlite_has_column(session: AsyncSession, table_name: str, column_name: str) -> bool:
    if not _TABLE_NAME_RE.match(table_name):
        raise ValueError(f"Invalid table name: {table_name!r}")
    rows = (await session.execute(text("PRAGMA table_info(:table_name)"), {"table_name": table_name})).mappings()
    return any(row["name"] == column_name for row in rows)


def _uuid() -> str:
    from uuid import uuid4

    return str(uuid4())
