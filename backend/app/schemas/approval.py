from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ApprovalItemResponse(BaseModel):
    publication_id: str
    content_item_id: str | None = None
    platform: str
    scheduled_at: datetime
    status: str
    preview_text: str
    requires_changes: bool


class ApprovalDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    comment: str | None = None


class PostponePublicationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scheduled_at: datetime


class PublicationActionResponse(BaseModel):
    publication_id: str
    status: str
    message: str
    queue_reference: str | None = None
