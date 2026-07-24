from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class GenerateContentPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    period_days: int = Field(default=30, ge=7, le=90)
    source_mode: str = "mixed"
    platforms: list[str] = Field(default_factory=list)
    content_types: list[str] = Field(default_factory=list)


class GenerateContentVersionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: str
    platform: str = "telegram"
    content_type: str = "post"
    prompt_context: dict = Field(default_factory=dict)


class ContentPlanItemResponse(BaseModel):
    content_item_id: str
    platform: str
    content_type: str
    publish_at: str
    status: str
    text: str


class ContentPlanResponse(BaseModel):
    plan_id: str
    tenant_id: str
    project_id: str
    version: int
    period_days: int
    source_mode: str
    status: str
    items: list[ContentPlanItemResponse]


class ContentVersionResponse(BaseModel):
    version_id: str
    tenant_id: str
    project_id: str
    content_item_id: str
    version_number: int
    text: str
    ai_provider: str
    ai_model: str
    created_at: datetime
