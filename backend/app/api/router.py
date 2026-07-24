from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.app.api.deps import enforce_rate_limit
from backend.app.api.v1.endpoints.ai import router as legacy_ai_router
from backend.app.api.v1.endpoints.content import router as legacy_content_router
from backend.app.api.v1.endpoints.dashboard import router as legacy_dashboard_router
from backend.app.api.v1.endpoints.projects import router as legacy_projects_router
from backend.app.api.v1.endpoints.users import router as legacy_users_router
from backend.app.api.health import router as health_router
from backend.app.modules.admin.api import router as admin_router
from backend.app.modules.ai_core.api import router as ai_core_router
from backend.app.modules.ai_optimization.api import router as ai_optimization_router
from backend.app.modules.ai_avatar.api import router as avatar_router
from backend.app.modules.ai_retail.api import router as retail_router
from backend.app.modules.agents.api import router as agents_router
from backend.app.modules.ai_assistant.api import router as ai_assistant_router
from backend.app.modules.analytics.api import router as analytics_router
from backend.app.modules.approval_center.api import router as approval_router
from backend.app.modules.billing.api import router as billing_router
from backend.app.modules.business_memory.api import router as business_memory_router
from backend.app.modules.business_onboarding.api import router as onboarding_router
from backend.app.modules.content_plan.api import router as content_plan_router
from backend.app.modules.content_materials.api import router as content_materials_router
from backend.app.modules.dashboard.api import router as dashboard_router
from backend.app.modules.files.api import router as files_router
from backend.app.modules.identity.api import legacy_router as auth_router
from backend.app.modules.identity.api import router as identity_router
from backend.app.modules.internship.api import router as internship_router
from backend.app.modules.mvp_api import router as mvp_router
from backend.app.modules.publishing.api import router as publishing_router
from backend.app.modules.social_integration.api import router as social_router
from backend.app.modules.webhooks.router import router as webhooks_router

api_router = APIRouter(dependencies=[Depends(enforce_rate_limit)])
api_router.include_router(health_router)
api_router.include_router(identity_router)
api_router.include_router(auth_router)
api_router.include_router(legacy_users_router)
api_router.include_router(legacy_projects_router)
api_router.include_router(legacy_content_router)
api_router.include_router(legacy_ai_router)
api_router.include_router(onboarding_router)
api_router.include_router(dashboard_router)
api_router.include_router(social_router)
api_router.include_router(content_plan_router)
api_router.include_router(content_materials_router)
api_router.include_router(approval_router)
api_router.include_router(publishing_router)
api_router.include_router(analytics_router)
api_router.include_router(ai_optimization_router)
api_router.include_router(billing_router)
api_router.include_router(admin_router)
api_router.include_router(files_router)
api_router.include_router(mvp_router)
api_router.include_router(legacy_dashboard_router)
api_router.include_router(ai_core_router)
api_router.include_router(avatar_router)
api_router.include_router(retail_router)
api_router.include_router(agents_router)
api_router.include_router(business_memory_router)
api_router.include_router(ai_assistant_router)
api_router.include_router(internship_router)
api_router.include_router(webhooks_router)
