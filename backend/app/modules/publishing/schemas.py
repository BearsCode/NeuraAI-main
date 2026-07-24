from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreatePublicationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content_item_id: str
    integration_ids: list[str] = Field(default_factory=list)
    scheduled_at: datetime | None = None
    all_or_nothing: bool = True


class PublicationTargetResponse(BaseModel):
    publication_target_id: str
    integration_id: str
    platform: str
    status: str
    external_post_id: str | None = None
    published_at: datetime | None = None


class PublicationResponse(BaseModel):
    publication_id: str
    tenant_id: str
    project_id: str
    content_item_id: str | None
    status: str
    scheduled_at: datetime
    all_or_nothing: bool
    approval_required: bool
    saga_id: str | None
    targets: list[PublicationTargetResponse] = Field(default_factory=list)


class RetryTargetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str | None = None
