from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ContentPlanGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    period_days: int = Field(default=30, ge=1, le=90)
    source_mode: str = "mixed"
    platforms: list[str] = Field(default_factory=list)
    content_types: list[str] = Field(default_factory=list)


class PlannedContentItem(BaseModel):
    content_item_id: str
    date: date
    time: str
    platform: str
    content_type: str
    status: str
    text: str
    image_url: str | None = None
    video_url: str | None = None


class ContentPlanResponse(BaseModel):
    plan_id: str
    project_id: str
    period_days: int
    source_mode: str
    status: str
    items: list[PlannedContentItem]


class GeneratePostRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    platform: str = "telegram"
    content_type: str = "post"
    topic_hint: str | None = None
    scheduled_at: datetime | None = None


class GeneratedContentResponse(BaseModel):
    content_id: str
    project_id: str
    platform: str
    content_type: str
    caption: str
    status: str
    created_at: datetime
    publication_id: str | None = None


class PublicationResponse(BaseModel):
    publication_id: str
    project_id: str
    content_item_id: str | None = None
    platform: str
    scheduled_at: datetime
    status: str
    retry_count: int
    error_message: str | None = None
