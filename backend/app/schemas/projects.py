from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


class BusinessOnboardingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_name: str
    business_description: str
    city: str
    industry: str
    services: list[str] = Field(default_factory=list)
    website: HttpUrl | None = None
    phone: str | None = None
    email: EmailStr | None = None
    social_links: list[str] = Field(default_factory=list)
    target_audience: str
    competitors: list[str] = Field(default_factory=list)
    business_features: list[str] = Field(default_factory=list)


class ProjectSummaryResponse(BaseModel):
    project_id: str
    company_name: str
    industry: str
    city: str
    strategy_status: str


class ProjectResponse(BaseModel):
    project_id: str
    owner_user_id: str
    company_name: str
    business_description: str
    city: str
    industry: str
    services: list[str]
    website: str | None = None
    phone: str | None = None
    email: str | None = None
    social_links: list[str]
    target_audience: str
    competitors: list[str]
    business_features: list[str]
    strategy_status: str
    created_at: datetime
    updated_at: datetime
