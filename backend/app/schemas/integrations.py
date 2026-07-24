from pydantic import BaseModel, ConfigDict, Field


class IntegrationConnectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    platform: str
    account_handle: str
    access_token: str | None = None
    refresh_token: str | None = None
    autoposting_enabled: bool = True
    publication_settings: dict = Field(default_factory=dict)


class IntegrationUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_handle: str | None = None
    status: str | None = None
    autoposting_enabled: bool | None = None
    publication_settings: dict | None = None


class IntegrationConnectionResponse(BaseModel):
    integration_id: str
    project_id: str
    platform: str
    account_handle: str
    connected: bool
    status: str
    autoposting_enabled: bool
    publication_settings: dict
