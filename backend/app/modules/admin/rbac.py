from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from backend.app.db.enums import AdminRole


class Permission(StrEnum):
    DASHBOARD_VIEW = "dashboard.view"
    USERS_READ = "users.read"
    USERS_WRITE = "users.write"
    USERS_DELETE = "users.delete"
    TENANTS_READ = "tenants.read"
    TENANTS_WRITE = "tenants.write"
    BILLING_READ = "billing.read"
    BILLING_WRITE = "billing.write"
    TARIFFS_READ = "tariffs.read"
    TARIFFS_WRITE = "tariffs.write"
    PRICING_READ = "pricing.read"
    PRICING_WRITE = "pricing.write"
    NOTIFICATIONS_READ = "notifications.read"
    NOTIFICATIONS_WRITE = "notifications.write"
    ANALYTICS_VIEW = "analytics.view"
    ANALYTICS_EXPORT = "analytics.export"
    BUSINESS_MEMORY_READ = "business_memory.read"
    BUSINESS_MEMORY_WRITE = "business_memory.write"
    AGENTS_READ = "agents.read"
    AGENTS_WRITE = "agents.write"
    CAPABILITIES_READ = "capabilities.read"
    CAPABILITIES_WRITE = "capabilities.write"
    PROMPTS_READ = "prompts.read"
    PROMPTS_WRITE = "prompts.write"
    PROMPTS_CONFIRM = "prompts.confirm"
    PROMPTS_ROLLBACK = "prompts.rollback"
    WORKFLOWS_READ = "workflows.read"
    WORKFLOWS_WRITE = "workflows.write"
    WORKFLOWS_PUBLISH = "workflows.publish"
    TOOLS_READ = "tools.read"
    TOOLS_WRITE = "tools.write"
    MODELS_READ = "models.read"
    MODELS_WRITE = "models.write"
    QUEUE_VIEW = "queue.view"
    WORKFLOW_HISTORY_VIEW = "workflow_history.view"
    AI_MONITORING_VIEW = "ai_monitoring.view"
    LOGS_VIEW = "logs.view"
    LOGS_EXPORT = "logs.export"
    TEST_CENTER_READ = "test_center.read"
    TEST_CENTER_WRITE = "test_center.write"
    DEPLOYMENTS_VIEW = "deployments.view"
    DEPLOYMENTS_WRITE = "deployments.write"
    PERMISSIONS_READ = "permissions.read"
    PERMISSIONS_WRITE = "permissions.write"
    PLATFORM_SETTINGS_READ = "platform_settings.read"
    PLATFORM_SETTINGS_WRITE = "platform_settings.write"
    IMPERSONATE = "impersonate"
    IMPERSONATE_WITHOUT_PERMISSION = "impersonate.without_permission"
    AUDIT_READ = "audit.read"
    AUDIT_DELETE_PROTECTED = "audit.delete_protected"
    ROLES_MANAGE = "roles.manage"
    SUPER_ADMIN = "super_admin"


ROLE_PERMISSIONS: dict[AdminRole, set[Permission]] = {
    AdminRole.SUPER_OWNER: {
        Permission.DASHBOARD_VIEW,
        Permission.USERS_READ,
        Permission.USERS_WRITE,
        Permission.USERS_DELETE,
        Permission.TENANTS_READ,
        Permission.TENANTS_WRITE,
        Permission.BILLING_READ,
        Permission.BILLING_WRITE,
        Permission.TARIFFS_READ,
        Permission.TARIFFS_WRITE,
        Permission.PRICING_READ,
        Permission.PRICING_WRITE,
        Permission.NOTIFICATIONS_READ,
        Permission.NOTIFICATIONS_WRITE,
        Permission.ANALYTICS_VIEW,
        Permission.ANALYTICS_EXPORT,
        Permission.BUSINESS_MEMORY_READ,
        Permission.BUSINESS_MEMORY_WRITE,
        Permission.AGENTS_READ,
        Permission.AGENTS_WRITE,
        Permission.CAPABILITIES_READ,
        Permission.CAPABILITIES_WRITE,
        Permission.PROMPTS_READ,
        Permission.PROMPTS_WRITE,
        Permission.PROMPTS_CONFIRM,
        Permission.PROMPTS_ROLLBACK,
        Permission.WORKFLOWS_READ,
        Permission.WORKFLOWS_WRITE,
        Permission.WORKFLOWS_PUBLISH,
        Permission.TOOLS_READ,
        Permission.TOOLS_WRITE,
        Permission.MODELS_READ,
        Permission.MODELS_WRITE,
        Permission.QUEUE_VIEW,
        Permission.WORKFLOW_HISTORY_VIEW,
        Permission.AI_MONITORING_VIEW,
        Permission.LOGS_VIEW,
        Permission.LOGS_EXPORT,
        Permission.TEST_CENTER_READ,
        Permission.TEST_CENTER_WRITE,
        Permission.DEPLOYMENTS_VIEW,
        Permission.DEPLOYMENTS_WRITE,
        Permission.PERMISSIONS_READ,
        Permission.PERMISSIONS_WRITE,
        Permission.PLATFORM_SETTINGS_READ,
        Permission.PLATFORM_SETTINGS_WRITE,
        Permission.IMPERSONATE,
        Permission.IMPERSONATE_WITHOUT_PERMISSION,
        Permission.AUDIT_READ,
        Permission.AUDIT_DELETE_PROTECTED,
        Permission.ROLES_MANAGE,
        Permission.SUPER_ADMIN,
    },
    AdminRole.OWNER: {
        Permission.DASHBOARD_VIEW,
        Permission.USERS_READ,
        Permission.USERS_WRITE,
        Permission.USERS_DELETE,
        Permission.TENANTS_READ,
        Permission.TENANTS_WRITE,
        Permission.BILLING_READ,
        Permission.BILLING_WRITE,
        Permission.TARIFFS_READ,
        Permission.TARIFFS_WRITE,
        Permission.PRICING_READ,
        Permission.PRICING_WRITE,
        Permission.NOTIFICATIONS_READ,
        Permission.NOTIFICATIONS_WRITE,
        Permission.ANALYTICS_VIEW,
        Permission.ANALYTICS_EXPORT,
        Permission.BUSINESS_MEMORY_READ,
        Permission.BUSINESS_MEMORY_WRITE,
        Permission.AGENTS_READ,
        Permission.AGENTS_WRITE,
        Permission.CAPABILITIES_READ,
        Permission.CAPABILITIES_WRITE,
        Permission.PROMPTS_READ,
        Permission.PROMPTS_WRITE,
        Permission.PROMPTS_CONFIRM,
        Permission.PROMPTS_ROLLBACK,
        Permission.WORKFLOWS_READ,
        Permission.WORKFLOWS_WRITE,
        Permission.WORKFLOWS_PUBLISH,
        Permission.TOOLS_READ,
        Permission.TOOLS_WRITE,
        Permission.MODELS_READ,
        Permission.MODELS_WRITE,
        Permission.QUEUE_VIEW,
        Permission.WORKFLOW_HISTORY_VIEW,
        Permission.AI_MONITORING_VIEW,
        Permission.LOGS_VIEW,
        Permission.LOGS_EXPORT,
        Permission.TEST_CENTER_READ,
        Permission.TEST_CENTER_WRITE,
        Permission.DEPLOYMENTS_VIEW,
        Permission.DEPLOYMENTS_WRITE,
        Permission.PERMISSIONS_READ,
        Permission.PLATFORM_SETTINGS_READ,
        Permission.PLATFORM_SETTINGS_WRITE,
        Permission.IMPERSONATE,
        Permission.AUDIT_READ,
        Permission.ROLES_MANAGE,
    },
    AdminRole.ADMIN: {
        Permission.DASHBOARD_VIEW,
        Permission.USERS_READ,
        Permission.USERS_WRITE,
        Permission.USERS_DELETE,
        Permission.TENANTS_READ,
        Permission.TENANTS_WRITE,
        Permission.BILLING_READ,
        Permission.BILLING_WRITE,
        Permission.TARIFFS_READ,
        Permission.TARIFFS_WRITE,
        Permission.PRICING_READ,
        Permission.PRICING_WRITE,
        Permission.NOTIFICATIONS_READ,
        Permission.NOTIFICATIONS_WRITE,
        Permission.ANALYTICS_VIEW,
        Permission.ANALYTICS_EXPORT,
        Permission.BUSINESS_MEMORY_READ,
        Permission.BUSINESS_MEMORY_WRITE,
        Permission.AGENTS_READ,
        Permission.AGENTS_WRITE,
        Permission.CAPABILITIES_READ,
        Permission.CAPABILITIES_WRITE,
        Permission.PROMPTS_READ,
        Permission.PROMPTS_WRITE,
        Permission.PROMPTS_CONFIRM,
        Permission.PROMPTS_ROLLBACK,
        Permission.WORKFLOWS_READ,
        Permission.WORKFLOWS_WRITE,
        Permission.WORKFLOWS_PUBLISH,
        Permission.TOOLS_READ,
        Permission.TOOLS_WRITE,
        Permission.MODELS_READ,
        Permission.MODELS_WRITE,
        Permission.QUEUE_VIEW,
        Permission.WORKFLOW_HISTORY_VIEW,
        Permission.AI_MONITORING_VIEW,
        Permission.LOGS_VIEW,
        Permission.LOGS_EXPORT,
        Permission.TEST_CENTER_READ,
        Permission.TEST_CENTER_WRITE,
        Permission.DEPLOYMENTS_VIEW,
        Permission.DEPLOYMENTS_WRITE,
        Permission.PLATFORM_SETTINGS_READ,
        Permission.PLATFORM_SETTINGS_WRITE,
        Permission.IMPERSONATE,
        Permission.AUDIT_READ,
    },
    AdminRole.MANAGER: {
        Permission.DASHBOARD_VIEW,
        Permission.USERS_READ,
        Permission.USERS_WRITE,
        Permission.TENANTS_READ,
        Permission.TENANTS_WRITE,
        Permission.BILLING_READ,
        Permission.BILLING_WRITE,
        Permission.TARIFFS_READ,
        Permission.TARIFFS_WRITE,
        Permission.PRICING_READ,
        Permission.PRICING_WRITE,
        Permission.NOTIFICATIONS_READ,
        Permission.NOTIFICATIONS_WRITE,
        Permission.ANALYTICS_VIEW,
        Permission.QUEUE_VIEW,
        Permission.WORKFLOW_HISTORY_VIEW,
        Permission.AI_MONITORING_VIEW,
        Permission.LOGS_VIEW,
    },
    AdminRole.EDITOR: {
        Permission.DASHBOARD_VIEW,
        Permission.USERS_READ,
        Permission.TENANTS_READ,
        Permission.BUSINESS_MEMORY_READ,
        Permission.BUSINESS_MEMORY_WRITE,
        Permission.AGENTS_READ,
        Permission.AGENTS_WRITE,
        Permission.CAPABILITIES_READ,
        Permission.CAPABILITIES_WRITE,
        Permission.PROMPTS_READ,
        Permission.PROMPTS_WRITE,
        Permission.PROMPTS_CONFIRM,
        Permission.PROMPTS_ROLLBACK,
        Permission.WORKFLOWS_READ,
        Permission.WORKFLOWS_WRITE,
        Permission.WORKFLOWS_PUBLISH,
        Permission.TOOLS_READ,
        Permission.TOOLS_WRITE,
        Permission.MODELS_READ,
        Permission.MODELS_WRITE,
        Permission.QUEUE_VIEW,
        Permission.WORKFLOW_HISTORY_VIEW,
        Permission.AI_MONITORING_VIEW,
        Permission.TEST_CENTER_READ,
        Permission.TEST_CENTER_WRITE,
    },
    AdminRole.VIEWER: {
        Permission.DASHBOARD_VIEW,
        Permission.USERS_READ,
        Permission.TENANTS_READ,
        Permission.BILLING_READ,
        Permission.TARIFFS_READ,
        Permission.PRICING_READ,
        Permission.NOTIFICATIONS_READ,
        Permission.ANALYTICS_VIEW,
        Permission.BUSINESS_MEMORY_READ,
        Permission.AGENTS_READ,
        Permission.CAPABILITIES_READ,
        Permission.PROMPTS_READ,
        Permission.WORKFLOWS_READ,
        Permission.TOOLS_READ,
        Permission.MODELS_READ,
        Permission.QUEUE_VIEW,
        Permission.WORKFLOW_HISTORY_VIEW,
        Permission.AI_MONITORING_VIEW,
        Permission.LOGS_VIEW,
    },
    AdminRole.SUPPORT: {
        Permission.DASHBOARD_VIEW,
        Permission.USERS_READ,
        Permission.TENANTS_READ,
        Permission.BILLING_READ,
        Permission.LOGS_VIEW,
        Permission.IMPERSONATE,
        Permission.AUDIT_READ,
    },
    AdminRole.AUDITOR: {
        Permission.LOGS_VIEW,
        Permission.LOGS_EXPORT,
        Permission.AUDIT_READ,
        Permission.WORKFLOW_HISTORY_VIEW,
    },
}


@lru_cache(maxsize=1)
def get_permissions_for_role(role: AdminRole) -> frozenset[Permission]:
    return frozenset(ROLE_PERMISSIONS.get(role, set()))


def has_permission(role: AdminRole, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())


def role_hierarchy_level(role: AdminRole) -> int:
    levels = {
        AdminRole.SUPER_OWNER: 100,
        AdminRole.OWNER: 80,
        AdminRole.ADMIN: 60,
        AdminRole.MANAGER: 40,
        AdminRole.EDITOR: 30,
        AdminRole.SUPPORT: 25,
        AdminRole.VIEWER: 20,
        AdminRole.AUDITOR: 15,
    }
    return levels.get(role, 0)


def can_manage_role(actor_role: AdminRole, target_role: AdminRole) -> bool:
    return role_hierarchy_level(actor_role) > role_hierarchy_level(target_role)
