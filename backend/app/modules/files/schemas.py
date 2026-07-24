from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreateUploadUrlRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_name: str
    content_type: str
    asset_type: str = Field(default="other")
    size_bytes: int = Field(gt=0)


class UploadUrlResponse(BaseModel):
    object_key: str
    upload_url: str
    expires_in: int


class CompleteUploadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    object_key: str
    file_name: str
    content_type: str
    asset_type: str
    size_bytes: int
    checksum_sha256: str | None = None


class FileAssetResponse(BaseModel):
    asset_id: str
    tenant_id: str
    project_id: str
    file_name: str
    content_type: str
    asset_type: str
    storage_uri: str
    public_url: str | None
    size_bytes: int
    created_at: datetime
