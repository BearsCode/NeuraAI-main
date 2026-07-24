from datetime import datetime

from pydantic import BaseModel


class AssetResponse(BaseModel):
    asset_id: str
    project_id: str
    asset_type: str
    file_name: str
    content_type: str
    storage_uri: str
    public_url: str | None = None
    created_at: datetime
