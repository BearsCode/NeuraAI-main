from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SocialConnectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    platform: str
    account_handle: str = Field(min_length=2, max_length=255)
    access_token: str
    refresh_token: str | None = None
    autoposting_enabled: bool = True
    publication_settings: dict = Field(default_factory=dict)
    scopes: list[str] = Field(default_factory=list)


class SocialAuthorizeResponse(BaseModel):
    authorization_url: str
    state: str
    code_verifier: str | None = None


class SocialOAuthCallbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    redirect_uri: str
    code_verifier: str | None = None
    account_handle: str | None = None
    autoposting_enabled: bool = True
    publication_settings: dict = Field(default_factory=dict)


class SocialUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    autoposting_enabled: bool | None = None
    publication_settings: dict | None = None
    refresh_token: str | None = None
    access_token: str | None = None


class SocialConnectionResponse(BaseModel):
    integration_id: str
    project_id: str
    tenant_id: str
    platform: str
    account_handle: str
    status: str
    autoposting_enabled: bool
    scopes: list[str]
    publication_settings: dict
    created_at: datetime
