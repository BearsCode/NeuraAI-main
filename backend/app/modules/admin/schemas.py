from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.app.db.enums import AdminRole, ToolProviderType, ToolStatus, UserRole
from backend.app.schemas.promocode import PromocodeResponse


class AdminPathResponse(BaseModel):
    today_path: str
    yesterday_path: str | None = None
    login_path: str
    session_ttl_minutes: int


class AdminOverviewResponse(BaseModel):
    users_total: int
    active_users_total: int
    tenants_total: int
    active_tenants_total: int
    projects_total: int
    active_projects_total: int
    active_subscriptions: int
    partners_total: int
    monthly_recurring_revenue: float
    successful_payments_total: float
    pending_outbox_events: int
    failed_ai_jobs: int


class AdminTenantResponse(BaseModel):
    tenant_id: str
    slug: str
    name: str
    status: str
    owner_user_id: str
    owner_email: str | None
    projects_total: int
    subscriptions_total: int
    created_at: datetime


class AdminProjectResponse(BaseModel):
    project_id: str
    tenant_id: str
    tenant_name: str | None
    owner_user_id: str
    owner_email: str | None
    company_name: str
    city: str
    industry: str
    strategy_status: str
    integrations_total: int
    content_items_total: int
    publications_total: int
    created_at: datetime


class AdminUserResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    role: str
    admin_role: str | None = None
    is_active: bool
    is_verified: bool
    tenants_total: int
    projects_total: int
    created_at: datetime


class AdminUserTenantResponse(BaseModel):
    tenant_id: str
    tenant_name: str
    role: str
    is_primary: bool


class AdminUserSubscriptionResponse(BaseModel):
    subscription_id: str
    tenant_id: str
    plan_code: str | None
    status: str
    starts_at: datetime
    ends_at: datetime | None
    next_charge_at: datetime | None


class AdminUserDetailResponse(AdminUserResponse):
    phone: str | None
    last_login_at: datetime | None
    referred_by_user_id: str | None
    tenants: list[AdminUserTenantResponse]
    subscriptions: list[AdminUserSubscriptionResponse]


class AdminRoleUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: UserRole


class AdminAdminRoleUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    admin_role: AdminRole


class AdminSubscriptionResponse(BaseModel):
    subscription_id: str
    tenant_id: str
    tenant_name: str | None
    plan_id: str
    plan_code: str | None
    plan_name: str | None
    status: str
    seats: int
    starts_at: datetime
    ends_at: datetime | None
    next_charge_at: datetime | None
    trial_ends_at: datetime | None
    created_at: datetime


class AdminPaymentResponse(BaseModel):
    payment_id: str
    tenant_id: str
    tenant_name: str | None
    subscription_id: str
    plan_code: str | None
    amount: float
    currency: str
    status: str
    provider: str
    external_payment_id: str | None
    paid_at: datetime | None
    created_at: datetime


class AdminPartnerResponse(BaseModel):
    partner_profile_id: str
    user_id: str
    email: str
    full_name: str
    referral_code: str
    commission_rate: float
    total_income: float
    pending_payout: float
    referrals_total: int
    commissions_total: float
    available_commission: float
    created_at: datetime


class AdminReferralResponse(BaseModel):
    referred_user_id: str
    referred_email: str
    referrer_user_id: str
    referrer_email: str
    created_at: datetime


class AdminAnalyticsResponse(BaseModel):
    users_total: int
    tenants_total: int
    projects_total: int
    content_items_total: int
    publications_total: int
    connected_integrations_total: int
    active_subscriptions_total: int
    revenue_total: float
    monthly_recurring_revenue: float


class AdminMonitoringResponse(BaseModel):
    outbox_events: dict[str, int]
    ai_jobs: dict[str, int]
    publications: dict[str, int]
    social_integrations: dict[str, int]
    failed_ai_jobs: int
    pending_outbox_events: int
    generated_at: datetime


class AdminTariffUpsertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=120)
    description: str = ""
    price_amount: float = Field(ge=0)
    currency: str = Field(default="RUB", min_length=3, max_length=8)
    requests_per_minute: int = Field(default=120, ge=1)
    content_generations_per_hour: int = Field(default=100, ge=1)
    publications_per_hour: int = Field(default=50, ge=1)
    features: dict = Field(default_factory=dict)
    is_active: bool = True


class AdminTariffResponse(BaseModel):
    plan_id: str
    code: str
    name: str
    description: str
    price_amount: float
    currency: str
    requests_per_minute: int
    content_generations_per_hour: int
    publications_per_hour: int
    features: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AdminExpertPromptUpsertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    niche: str = Field(min_length=1, max_length=120)
    role_description: str = Field(min_length=1)
    tone: str = Field(default="expert, practical, concise", min_length=1, max_length=120)
    additional_instructions: str = ""
    is_active: bool = True


class AdminExpertPromptResponse(BaseModel):
    prompt_id: str
    niche: str
    role_description: str
    tone: str
    additional_instructions: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AdminPromocodeResponse(PromocodeResponse):
    pass


class AdminImpersonateStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_user_id: str
    reason: str = Field(min_length=10)


class AdminImpersonateSessionResponse(BaseModel):
    session_id: str
    admin_user_id: str
    admin_email: str
    target_user_id: str
    target_email: str
    reason: str
    started_at: datetime
    is_active: bool


class AdminAuditLogResponse(BaseModel):
    log_id: str
    actor_id: str
    actor_email: str | None
    action: str
    target_type: str
    target_id: str | None
    details: dict | None
    diff: dict | None
    ip_address: str | None
    severity: str
    reason: str | None
    created_at: datetime


class AdminPlatformSettingResponse(BaseModel):
    key: str
    category: str
    value_preview: str | None
    updated_by: str | None
    updated_at: datetime | None


class AdminPlatformSettingUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: str


class AdminDeviceResponse(BaseModel):
    id: str
    fingerprint_hash: str
    device_info: str | None
    ip_address: str | None
    is_trusted: bool
    last_seen_at: datetime | None
    created_at: datetime


class AdminPricingResponse(BaseModel):
    token_price_per_1k: float
    generation_price_per_1k: float
    storage_price_gb: float


class AdminPricingUpdateRequest(BaseModel):
    token_price_per_1k: float | None = None
    generation_price_per_1k: float | None = None
    storage_price_gb: float | None = None


class AdminNotificationCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    body: str = Field(min_length=1)
    target_role: str | None = None
    target_user_id: str | None = None


class AdminWorkflowResponse(BaseModel):
    id: str
    workflow_type: str
    status: str
    is_draft: bool
    created_at: datetime
    updated_at: datetime


class AdminToolResponse(BaseModel):
    tool_id: str
    name: str
    provider_type: ToolProviderType
    base_url: str | None
    status: ToolStatus
    config: dict
    last_used_at: datetime | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class AdminToolCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    provider_type: ToolProviderType
    api_key: str | None = None
    base_url: str | None = None
    config: dict = Field(default_factory=dict)


class AdminToolUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=120)
    api_key: str | None = None
    base_url: str | None = None
    status: ToolStatus | None = None
    config: dict | None = None


class AdminToolTestResponse(BaseModel):
    success: bool
    message: str
    latency_ms: float | None = None


class AdminQueueMetricsResponse(BaseModel):
    pending_workflows: int
    running_workflows: int
    failed_workflows: int
    completed_workflows: int
    pending_ai_jobs: int
    running_ai_jobs: int
    failed_ai_jobs: int
    pending_publications: int
    in_progress_publications: int
    failed_publications: int
    stalled_workflows: int
    generated_at: datetime


class AdminPromptVersionResponse(BaseModel):
    version_id: str
    prompt_id: str
    content: str
    diff: dict | None
    author_id: str
    is_active: bool
    created_at: datetime
