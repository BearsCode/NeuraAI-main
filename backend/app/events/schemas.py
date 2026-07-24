from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class EventEnvelope(BaseModel):
    event_id: str = Field(default_factory=lambda: uuid4().hex)
    event_type: str
    topic: str
    tenant_id: str
    aggregate_id: str
    payload: dict[str, Any]
    schema_version: Literal["1.0"] = "1.0"
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class BusinessOnboardedEvent(BaseModel):
    tenant_id: str
    project_id: str
    owner_user_id: str


class AIRequestedEvent(BaseModel):
    tenant_id: str
    project_id: str
    job_id: str
    task_type: str


class ContentPlanGeneratedEvent(BaseModel):
    tenant_id: str
    plan_id: str
    project_id: str
    items_count: int


class PublicationApprovedEvent(BaseModel):
    tenant_id: str
    publication_id: str
    approved_by_user_id: str


class PublicationResultEvent(BaseModel):
    tenant_id: str
    publication_id: str
    platform: str
    status: str
    message: str | None = None


class AnalyticsCollectedEvent(BaseModel):
    tenant_id: str
    project_id: str
    snapshot_id: str


class BillingChargedEvent(BaseModel):
    tenant_id: str
    subscription_id: str
    payment_id: str


class OptimizationSuggestedEvent(BaseModel):
    tenant_id: str
    recommendation_id: str


class PublicationCompletedEvent(BaseModel):
    tenant_id: str
    project_id: str
    publication_id: str
    platform: str
    external_url: str | None = None
    external_post_id: str | None = None


class PublicationFailedEvent(BaseModel):
    tenant_id: str
    project_id: str
    publication_id: str
    platform: str
    error: str
    retry_count: int


class HighReachAchievedEvent(BaseModel):
    tenant_id: str
    project_id: str
    publication_id: str
    reach: int
    threshold: int


class LowEngagementEvent(BaseModel):
    tenant_id: str
    project_id: str
    publication_id: str
    engagement_rate: float
    threshold: float


class ContentQueueEmptyEvent(BaseModel):
    tenant_id: str
    project_id: str
    empty_slots: int


class ImageGenerationDoneEvent(BaseModel):
    tenant_id: str
    project_id: str
    job_id: str
    image_url: str


class VideoGenerationDoneEvent(BaseModel):
    tenant_id: str
    project_id: str
    job_id: str
    video_url: str


class AnalyticsUpdatedEvent(BaseModel):
    tenant_id: str
    project_id: str
    snapshot_id: str


class RetailSyncCompletedEvent(BaseModel):
    tenant_id: str
    project_id: str
    sync_id: str
    total_products: int
    synced_products: int


class AvatarTrainingDoneEvent(BaseModel):
    tenant_id: str
    avatar_id: str
    status: str
    model_url: str | None = None


class WorkflowCompletedEvent(BaseModel):
    tenant_id: str
    project_id: str
    workflow_id: str
    workflow_type: str
    result: dict | None = None


class WorkflowFailedEvent(BaseModel):
    tenant_id: str
    project_id: str
    workflow_id: str
    workflow_type: str
    error: str
    step: int
