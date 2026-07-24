from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ContentGenerateRequest(BaseModel):
    prompt: str
    platform: str | None = None
    content_type: str | None = None
    tone: str | None = None
    topic: str | None = None
    keywords: str | None = None

class ContentSaveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str
    platform: str | None = None
    content_type: str | None = "post"
    title: str | None = None

class ContentItemResponse(BaseModel):
    content_item_id: str
    platform: str | None
    content_type: str
    title: str
    text: str
    status: str
    created_at: datetime
