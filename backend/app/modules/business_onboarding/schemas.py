from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


class CreateBusinessRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_name: str = Field(min_length=2, max_length=255)
    tenant_slug: str = Field(min_length=2, max_length=120)
    company_name: str = Field(min_length=2, max_length=255)
    business_description: str = Field(min_length=20)
    city: str = Field(min_length=2, max_length=120)
    industry: str = Field(min_length=2, max_length=120)
    services: list[str] = Field(default_factory=list)
    website: HttpUrl | None = None
    phone: str | None = None
    email: EmailStr | None = None
    social_links: list[str] = Field(default_factory=list)
    target_audience: str = Field(min_length=5)
    competitors: list[str] = Field(default_factory=list)
    business_features: list[str] = Field(default_factory=list)
    timezone: str = "UTC"


class BusinessResponse(BaseModel):
    tenant_id: str
    project_id: str
    tenant_name: str
    tenant_slug: str
    company_name: str
    city: str
    industry: str
    strategy_status: str
    created_at: datetime


class AIAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_type: str = Field(default="strategy_generation")


class AIAnalysisJobResponse(BaseModel):
    job_id: str
    tenant_id: str
    project_id: str
    status: str
    task_type: str
