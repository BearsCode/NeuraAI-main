from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApprovalPolicyUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: str = Field(pattern="^(manual|auto)$")
    auto_publish_enabled: bool = False
    auto_publish_platforms: list[str] = Field(default_factory=list)


class ApprovalPolicyResponse(BaseModel):
    policy_id: str
    tenant_id: str
    project_id: str
    mode: str
    auto_publish_enabled: bool
    auto_publish_platforms: list[str]


class ApprovalQueueItemResponse(BaseModel):
    publication_id: str
    content_item_id: str | None
    status: str
    scheduled_at: datetime
    target_platforms: list[str]


class ApprovalDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    comment: str | None = None


class PostponeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scheduled_at: datetime
