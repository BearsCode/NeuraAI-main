from __future__ import annotations

from enum import StrEnum

enum_kwargs = {"native_enum": False, "validate_strings": True}


class UserRole(StrEnum):
    CLIENT = "client"
    CREATOR = "creator"
    PARTNER = "partner"
    ADMIN = "admin"


class AdminRole(StrEnum):
    SUPER_OWNER = "super_owner"
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    EDITOR = "editor"
    VIEWER = "viewer"
    SUPPORT = "support"
    AUDITOR = "auditor"


class TenantStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class MembershipRole(StrEnum):
    OWNER = "owner"
    MANAGER = "manager"
    VIEWER = "viewer"


class StrategyStatus(StrEnum):
    DRAFT = "draft"
    ANALYZING = "analyzing"
    ACTIVE = "active"
    NEEDS_REVIEW = "needs_review"


class IntegrationPlatform(StrEnum):
    TELEGRAM = "telegram"
    VK = "vk"
    INSTAGRAM = "instagram"
    THREADS = "threads"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    WHATSAPP_BUSINESS = "whatsapp_business"
    MAX = "max"


class IntegrationStatus(StrEnum):
    PENDING = "pending"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    REAUTH_REQUIRED = "reauth_required"
    FAILED = "failed"


class ContentType(StrEnum):
    POST = "post"
    CAROUSEL = "carousel"
    STORY = "story"
    VIDEO = "video"
    REEL = "reel"
    SHORT = "short"
    THREAD = "thread"


class ContentSourceMode(StrEnum):
    UPLOADED = "uploaded_materials"
    SOCIALS = "social_analysis"
    MIXED = "mixed"


class ContentStatus(StrEnum):
    DRAFT = "draft"
    GENERATED = "generated"
    READY = "ready"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"


class ApprovalMode(StrEnum):
    MANUAL = "manual"
    AUTO = "auto"


class PublicationStatus(StrEnum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    POSTPONED = "postponed"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELED = "canceled"
    COMPENSATED = "compensated"


class PublicationTargetStatus(StrEnum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    PUBLISHED = "published"
    FAILED = "failed"
    COMPENSATED = "compensated"


class SubscriptionStatus(StrEnum):
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    PAUSED = "paused"
    CANCELED = "canceled"
    PENDING_PAYMENT = "pending_payment"
    EXPIRED = "expired"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class PromoCodeKind(StrEnum):
    BALANCE = "balance"
    PERCENT = "percent"
    DISCOUNT = "discount"
    GIFT_PLAN = "gift_plan"


class CommissionStatus(StrEnum):
    PENDING = "pending"
    AVAILABLE = "available"
    PAID = "paid"
    CANCELED = "canceled"


class AssetType(StrEnum):
    LOGO = "logo"
    PHOTO = "photo"
    VIDEO = "video"
    BRANDBOOK = "brandbook"
    PRESENTATION = "presentation"
    OTHER = "other"


class OutboxStatus(StrEnum):
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"


class AIJobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class AITrainingStatus(StrEnum):
    NOT_STARTED = "not_started"
    INITIALIZING = "initializing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXTENDED = "extended"
    FAILED = "failed"


class WorkflowStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_ASYNC = "waiting_async"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class AgentType(StrEnum):
    BUSINESS = "business"
    MARKETING = "marketing"
    BRAND = "brand"
    CONTENT = "content"
    IMAGE = "image"
    VIDEO = "video"
    RETAIL = "retail"
    CEO = "ceo"
    CHECKER = "checker"
    TRAINING = "training"


class WorkflowStepType(StrEnum):
    GENERATE_TEXT = "generate_text"
    GENERATE_IMAGE = "generate_image"
    GENERATE_VIDEO = "generate_video"
    CHECK_CONTENT = "check_content"
    WAIT_ASYNC = "wait_async"
    PUBLISH = "publish"
    NOTIFY = "notify"
    SPLIT = "split"
    MERGE = "merge"


class AvatarStatus(StrEnum):
    PENDING = "pending"
    TRAINING = "training"
    READY = "ready"
    FAILED = "failed"


class AvatarType(StrEnum):
    PHOTO = "photo"
    VIDEO = "video"


class RetailSyncStatus(StrEnum):
    PENDING = "pending"
    SYNCING = "syncing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class OperationMode(StrEnum):
    AUTOMATIC = "automatic"
    SEMI_AUTOMATIC = "semi_automatic"
    MANUAL = "manual"


class InternshipStage(StrEnum):
    INITIALIZATION = "initialization"
    ACTIVE_LEARNING = "active_learning"
    CALIBRATION = "calibration"
    FINAL_CHECK = "final_check"
    COMPLETED = "completed"
    EXTENDED = "extended"


class ToolProviderType(StrEnum):
    AI = "ai"
    SOCIAL = "social"
    PAYMENT = "payment"
    STORAGE = "storage"
    AVATAR = "avatar"
    EMAIL = "email"
    ANALYTICS = "analytics"
    MONITORING = "monitoring"
    OTHER = "other"


class ToolStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class PlanCode(StrEnum):
    BUSINESS = "business"
    CREATOR = "creator"


class OptimizationStatus(StrEnum):
    PENDING = "pending"
    APPLIED = "applied"
    DISMISSED = "dismissed"


class IdempotencyStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


__all__ = [
    "AdminRole",
    "AIJobStatus",
    "ApprovalMode",
    "AssetType",
    "CommissionStatus",
    "ContentSourceMode",
    "ContentStatus",
    "ContentType",
    "IdempotencyStatus",
    "IntegrationPlatform",
    "IntegrationStatus",
    "InternshipStage",
    "MembershipRole",
    "OptimizationStatus",
    "OutboxStatus",
    "PaymentStatus",
    "PlanCode",
    "PromoCodeKind",
    "PublicationStatus",
    "PublicationTargetStatus",
    "StrategyStatus",
    "SubscriptionStatus",
    "TenantStatus",
    "ToolProviderType",
    "ToolStatus",
    "UserRole",
    "enum_kwargs",
]
