from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.modules.admin.security import (
    require_admin,
    require_confirm,
)
from backend.app.core.configs import settings
from backend.app.core.database import get_db_session
from backend.app.db.enums import AdminRole, PaymentStatus, SubscriptionStatus, ToolProviderType, ToolStatus, UserRole
from backend.app.db.user import User
from backend.app.modules.admin.dynamic_path import get_today_path, get_login_path, get_yesterday_path
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
    AdminPathResponse,
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
    AdminWorkflowResponse,
)
from backend.app.modules.admin.service import AdminService
from backend.app.schemas.promocode import ChangePromocode, CreatePromocode

router = APIRouter(prefix="/admin", tags=["admin"])
service = AdminService()


@router.post("/confirm", status_code=status.HTTP_201_CREATED)
async def issue_confirmation_token_endpoint(
    request: Request,
    action: str = Query(description="Action to authorize (e.g. impersonate, change_role, update_settings)"),
    current_user: User = Depends(require_admin(AdminRole.OWNER, AdminRole.SUPER_OWNER)),
) -> dict:
    redis = getattr(request.app.state, "redis", None)
    if redis is None:
        raise HTTPException(status_code=503, detail="Redis unavailable")
    from backend.app.modules.admin.security import issue_confirmation_token
    token = await issue_confirmation_token(redis, current_user.id, action)
    return {"token": token, "action": action, "expires_in_seconds": 300}


@router.get("/path", response_model=AdminPathResponse)
async def get_admin_path() -> AdminPathResponse:
    return AdminPathResponse(
        today_path=get_today_path(),
        yesterday_path=get_yesterday_path(),
        login_path=get_login_path(),
        session_ttl_minutes=settings.admin.session_ttl_minutes,
    )


@router.get("/overview", response_model=AdminOverviewResponse)
async def overview(
    _: User = Depends(require_admin(AdminRole.VIEWER, AdminRole.SUPPORT, AdminRole.MANAGER, AdminRole.EDITOR, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> AdminOverviewResponse:
    return await service.overview(session)


@router.get("/analytics", response_model=AdminAnalyticsResponse)
async def analytics(
    _: User = Depends(require_admin(AdminRole.VIEWER, AdminRole.MANAGER, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> AdminAnalyticsResponse:
    return await service.analytics(session)


@router.get("/monitoring", response_model=AdminMonitoringResponse)
async def monitoring(
    _: User = Depends(require_admin(AdminRole.VIEWER, AdminRole.MANAGER, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> AdminMonitoringResponse:
    return await service.monitoring(session)


@router.get("/tenants", response_model=list[AdminTenantResponse])
async def tenants(
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    _: User = Depends(require_admin(AdminRole.VIEWER, AdminRole.SUPPORT, AdminRole.MANAGER, AdminRole.EDITOR, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> list[AdminTenantResponse]:
    return await service.list_tenants(session, search=search, page=page, size=size)


@router.get("/projects", response_model=list[AdminProjectResponse])
async def projects(
    search: str | None = None,
    industry: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    _: User = Depends(require_admin(AdminRole.VIEWER, AdminRole.MANAGER, AdminRole.EDITOR, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> list[AdminProjectResponse]:
    return await service.list_projects(session, search=search, industry=industry, page=page, size=size)


@router.get("/users", response_model=list[AdminUserResponse])
async def users(
    search: str | None = None,
    role: UserRole | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    _: User = Depends(require_admin(AdminRole.VIEWER, AdminRole.SUPPORT, AdminRole.MANAGER, AdminRole.EDITOR, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> list[AdminUserResponse]:
    return await service.list_users(session, search=search, role=role, page=page, size=size)


@router.get("/users/{user_id}", response_model=AdminUserDetailResponse)
async def user_details(
    user_id: str,
    _: User = Depends(require_admin(AdminRole.VIEWER, AdminRole.SUPPORT, AdminRole.MANAGER, AdminRole.EDITOR, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> AdminUserDetailResponse:
    return await service.get_user(session, user_id)


@router.put("/users/{user_id}/role", response_model=AdminUserDetailResponse)
async def update_user_role(
    user_id: str,
    payload: AdminRoleUpdateRequest,
    current_user: User = Depends(require_admin(AdminRole.MANAGER, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> AdminUserDetailResponse:
    return await service.update_user_role(session, user_id, payload, current_user)


@router.put("/users/{user_id}/admin-role", response_model=AdminUserDetailResponse)
async def update_user_admin_role(
    user_id: str,
    payload: AdminAdminRoleUpdateRequest,
    current_user: User = Depends(require_admin(AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    _: None = Depends(require_confirm("change_admin_role")),
    session: AsyncSession = Depends(get_db_session),
) -> AdminUserDetailResponse:
    return await service.update_user_admin_role(session, user_id, payload, current_user)


@router.get("/subscriptions", response_model=list[AdminSubscriptionResponse])
async def subscriptions(
    status_filter: SubscriptionStatus | None = Query(default=SubscriptionStatus.ACTIVE, alias="status"),
    plan_code: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    _: User = Depends(require_admin(AdminRole.VIEWER, AdminRole.MANAGER, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> list[AdminSubscriptionResponse]:
    return await service.list_subscriptions(session, status_filter=status_filter, plan_code=plan_code, page=page, size=size)


@router.get("/payments", response_model=list[AdminPaymentResponse])
async def payments(
    status_filter: PaymentStatus | None = Query(default=None, alias="status"),
    provider: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    _: User = Depends(require_admin(AdminRole.VIEWER, AdminRole.MANAGER, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> list[AdminPaymentResponse]:
    return await service.list_payments(session, status_filter=status_filter, provider=provider, page=page, size=size)


@router.get("/partners", response_model=list[AdminPartnerResponse])
async def partners(
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    _: User = Depends(require_admin(AdminRole.VIEWER, AdminRole.MANAGER, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> list[AdminPartnerResponse]:
    return await service.list_partners(session, search=search, page=page, size=size)


@router.get("/referrals", response_model=list[AdminReferralResponse])
async def referrals(
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    _: User = Depends(require_admin(AdminRole.VIEWER, AdminRole.MANAGER, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> list[AdminReferralResponse]:
    return await service.list_referrals(session, search=search, page=page, size=size)


@router.get("/promocodes", response_model=list[AdminPromocodeResponse])
async def promocodes(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    _: User = Depends(require_admin(AdminRole.MANAGER, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> list[AdminPromocodeResponse]:
    return await service.list_promocodes(session, page=page, size=size)


@router.post("/promocodes", response_model=AdminPromocodeResponse, status_code=status.HTTP_201_CREATED)
async def create_promocode(
    payload: CreatePromocode,
    current_user: User = Depends(require_admin(AdminRole.MANAGER, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> AdminPromocodeResponse:
    return await service.create_promocode(session, current_user, payload)


@router.put("/promocodes/{code}", response_model=AdminPromocodeResponse)
async def update_promocode(
    code: str,
    payload: ChangePromocode,
    _: User = Depends(require_admin(AdminRole.MANAGER, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> AdminPromocodeResponse:
    return await service.update_promocode(session, code, payload)


@router.delete("/promocodes/{code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_promocode(
    code: str,
    _: User = Depends(require_admin(AdminRole.MANAGER, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    __: None = Depends(require_confirm("delete_promocode")),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    await service.delete_promocode(session, code)


@router.get("/tariffs", response_model=list[AdminTariffResponse])
async def tariffs(
    _: User = Depends(require_admin(AdminRole.VIEWER, AdminRole.MANAGER, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> list[AdminTariffResponse]:
    return await service.list_tariffs(session)


@router.post("/tariffs", response_model=AdminTariffResponse)
async def upsert_tariff(
    payload: AdminTariffUpsertRequest,
    current_user: User = Depends(require_admin(AdminRole.MANAGER, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    _: None = Depends(require_confirm("upsert_tariff")),
    session: AsyncSession = Depends(get_db_session),
) -> AdminTariffResponse:
    return await service.upsert_tariff(session, payload, current_user)


@router.get("/expert-prompts", response_model=list[AdminExpertPromptResponse])
async def expert_prompts(
    _: User = Depends(require_admin(AdminRole.EDITOR, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> list[AdminExpertPromptResponse]:
    return await service.list_expert_prompts(session)


@router.post("/expert-prompts", response_model=AdminExpertPromptResponse)
async def upsert_expert_prompt(
    payload: AdminExpertPromptUpsertRequest,
    _: User = Depends(require_admin(AdminRole.EDITOR, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> AdminExpertPromptResponse:
    return await service.upsert_expert_prompt(session, payload)


@router.delete("/expert-prompts/{niche}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expert_prompt(
    niche: str,
    _: User = Depends(require_admin(AdminRole.EDITOR, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    await service.delete_expert_prompt(session, niche)


@router.get("/pricing", response_model=AdminPricingResponse)
async def pricing(
    _: User = Depends(require_admin(AdminRole.VIEWER, AdminRole.MANAGER, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> AdminPricingResponse:
    return await service.get_pricing(session)


@router.put("/pricing", response_model=AdminPricingResponse)
async def update_pricing(
    payload: AdminPricingUpdateRequest,
    _: User = Depends(require_admin(AdminRole.MANAGER, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    __: None = Depends(require_confirm("update_pricing")),
    session: AsyncSession = Depends(get_db_session),
) -> AdminPricingResponse:
    return await service.update_pricing(session, payload)


@router.post("/notifications", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_notification(
    payload: AdminNotificationCreateRequest,
    current_user: User = Depends(require_admin(AdminRole.MANAGER, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    return await service.create_notification(session, current_user, payload)


@router.get("/logs", response_model=list[AdminAuditLogResponse])
async def audit_logs(
    action: str | None = None,
    severity: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    _: User = Depends(require_admin(AdminRole.AUDITOR, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> list[AdminAuditLogResponse]:
    return await service.list_audit_logs(session, action=action, severity=severity, page=page, size=size)


@router.get("/logs/{log_id}", response_model=AdminAuditLogResponse)
async def audit_log_detail(
    log_id: str,
    _: User = Depends(require_admin(AdminRole.AUDITOR, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> AdminAuditLogResponse:
    return await service.get_audit_log(session, log_id)


@router.post("/impersonate/start", response_model=AdminImpersonateSessionResponse)
async def impersonate_start(
    payload: AdminImpersonateStartRequest,
    current_user: User = Depends(require_admin(AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    _: None = Depends(require_confirm("impersonate")),
    session: AsyncSession = Depends(get_db_session),
    request: Request = None,
) -> AdminImpersonateSessionResponse:
    return await service.start_impersonation(
        session, current_user, payload,
        ip_address=request.client.host if request and request.client else None,
    )


@router.post("/impersonate/end/{session_id}", response_model=dict)
async def impersonate_end(
    session_id: str,
    current_user: User = Depends(require_admin(AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    return await service.end_impersonation(session, session_id, current_user)


@router.get("/impersonate/active", response_model=list[AdminImpersonateSessionResponse])
async def impersonate_active(
    _: User = Depends(require_admin(AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> list[AdminImpersonateSessionResponse]:
    return await service.list_active_impersonations(session)


@router.get("/settings", response_model=list[AdminPlatformSettingResponse])
async def platform_settings(
    _: User = Depends(require_admin(AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> list[AdminPlatformSettingResponse]:
    return await service.list_platform_settings(session)


@router.put("/settings/{key}", response_model=AdminPlatformSettingResponse)
async def update_platform_setting(
    key: str,
    payload: AdminPlatformSettingUpdateRequest,
    current_user: User = Depends(require_admin(AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    _: None = Depends(require_confirm("update_settings")),
    session: AsyncSession = Depends(get_db_session),
) -> AdminPlatformSettingResponse:
    return await service.update_platform_setting(session, key, payload, current_user)


@router.post("/settings/{key}/test", response_model=dict)
async def test_platform_setting(
    key: str,
    payload: AdminPlatformSettingUpdateRequest,
    _: User = Depends(require_admin(AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    __: None = Depends(require_confirm("test_settings")),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    return await service.test_platform_setting(session, key, payload)


@router.get("/devices", response_model=list[AdminDeviceResponse])
async def admin_devices(
    user_id: str | None = None,
    _: User = Depends(require_admin(AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> list[AdminDeviceResponse]:
    return await service.list_devices(session, user_id=user_id)


@router.put("/devices/{device_id}/trust", response_model=AdminDeviceResponse)
async def trust_device(
    device_id: str,
    current_user: User = Depends(require_admin(AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> AdminDeviceResponse:
    return await service.trust_device(session, device_id, current_user)


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: str,
    current_user: User = Depends(require_admin(AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    await service.delete_device(session, device_id, current_user)


@router.get("/prompts", response_model=list[AdminExpertPromptResponse])
async def prompts_list(
    _: User = Depends(require_admin(AdminRole.EDITOR, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> list[AdminExpertPromptResponse]:
    return await service.list_expert_prompts(session)


@router.put("/prompts/{niche}", response_model=AdminPromptVersionResponse)
async def upsert_prompt_with_version(
    niche: str,
    payload: AdminExpertPromptUpsertRequest,
    current_user: User = Depends(require_admin(AdminRole.EDITOR, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> AdminPromptVersionResponse:
    return await service.upsert_prompt_with_version(session, niche, payload, current_user)


@router.get("/prompts/{niche}/versions", response_model=list[AdminPromptVersionResponse])
async def prompt_versions(
    niche: str,
    _: User = Depends(require_admin(AdminRole.EDITOR, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> list[AdminPromptVersionResponse]:
    return await service.list_prompt_versions(session, niche)


@router.post("/prompts/{niche}/rollback/{version_id}", response_model=AdminPromptVersionResponse)
async def rollback_prompt(
    niche: str,
    version_id: str,
    current_user: User = Depends(require_admin(AdminRole.EDITOR, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> AdminPromptVersionResponse:
    return await service.rollback_prompt(session, niche, version_id, current_user)


@router.get("/workflows", response_model=list[AdminWorkflowResponse])
async def workflows(
    status: str | None = None,
    is_draft: bool | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    _: User = Depends(require_admin(AdminRole.EDITOR, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> list[AdminWorkflowResponse]:
    return await service.list_workflows(session, status=status, is_draft=is_draft, page=page, size=size)


@router.get("/workflows/{workflow_id}", response_model=AdminWorkflowResponse)
async def workflow_detail(
    workflow_id: str,
    _: User = Depends(require_admin(AdminRole.EDITOR, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> AdminWorkflowResponse:
    return await service.get_workflow(session, workflow_id)


@router.post("/workflows/{workflow_id}/publish", response_model=AdminWorkflowResponse)
async def publish_workflow(
    workflow_id: str,
    _: User = Depends(require_admin(AdminRole.EDITOR, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> AdminWorkflowResponse:
    return await service.publish_workflow(session, workflow_id)


@router.get("/permissions", response_model=dict)
async def permissions(
    _: User = Depends(require_admin(AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    return await service.list_all_permissions(session)


@router.put("/permissions/{user_id}", response_model=AdminUserDetailResponse)
async def update_user_permissions(
    user_id: str,
    payload: AdminAdminRoleUpdateRequest,
    current_user: User = Depends(require_admin(AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> AdminUserDetailResponse:
    return await service.update_user_admin_role(session, user_id, payload, current_user)


@router.post("/emergency-access", response_model=dict)
async def emergency_access(
    request: Request,
    current_user: User = Depends(require_admin(AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    _: None = Depends(require_confirm("emergency_access")),
) -> dict:
    from backend.app.modules.admin.dynamic_path import generate_emergency_path
    ip_address = request.client.host if request.client else "unknown"
    path, expires_at = generate_emergency_path(ip_address)
    return {"path": path, "expires_at": expires_at.isoformat(), "ip_address": ip_address}


@router.get("/tools", response_model=list[AdminToolResponse])
async def admin_tools(
    provider_type: ToolProviderType | None = None,
    status: ToolStatus | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    _: User = Depends(require_admin(AdminRole.VIEWER, AdminRole.MANAGER, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> list[AdminToolResponse]:
    return await service.list_tools(session, provider_type=provider_type, status=status, page=page, size=size)


@router.get("/tools/{tool_id}", response_model=AdminToolResponse)
async def admin_tool_detail(
    tool_id: str,
    _: User = Depends(require_admin(AdminRole.VIEWER, AdminRole.MANAGER, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> AdminToolResponse:
    return await service.get_tool(session, tool_id)


@router.post("/tools", response_model=AdminToolResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_tool(
    payload: AdminToolCreateRequest,
    current_user: User = Depends(require_admin(AdminRole.MANAGER, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> AdminToolResponse:
    return await service.create_tool(session, payload, current_user)


@router.put("/tools/{tool_id}", response_model=AdminToolResponse)
async def admin_update_tool(
    tool_id: str,
    payload: AdminToolUpdateRequest,
    current_user: User = Depends(require_admin(AdminRole.MANAGER, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> AdminToolResponse:
    return await service.update_tool(session, tool_id, payload, current_user)


@router.delete("/tools/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_tool(
    tool_id: str,
    _: User = Depends(require_admin(AdminRole.MANAGER, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    __: None = Depends(require_confirm("delete_tool")),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    await service.delete_tool(session, tool_id)


@router.post("/tools/{tool_id}/test", response_model=AdminToolTestResponse)
async def admin_test_tool(
    tool_id: str,
    _: User = Depends(require_admin(AdminRole.MANAGER, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> AdminToolTestResponse:
    return await service.test_tool_connection(session, tool_id)


@router.get("/queue-metrics", response_model=AdminQueueMetricsResponse)
async def admin_queue_metrics(
    _: User = Depends(require_admin(AdminRole.VIEWER, AdminRole.MANAGER, AdminRole.ADMIN, AdminRole.OWNER, AdminRole.SUPER_OWNER)),
    session: AsyncSession = Depends(get_db_session),
) -> AdminQueueMetricsResponse:
    return await service.queue_metrics(session)
