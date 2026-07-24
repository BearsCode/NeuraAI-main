from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DashboardKPIResponse(BaseModel):
    code: str
    value: float | int | str
    label: str


class DashboardScheduleItemResponse(BaseModel):
    content_item_id: str
    platform: str
    content_type: str
    publish_at: datetime
    status: str


class DashboardResponse(BaseModel):
    tenant_id: str
    project_id: str
    strategy_status: str
    connected_platforms: list[str] = Field(default_factory=list)
    approval_mode: str
    kpis: list[DashboardKPIResponse] = Field(default_factory=list)
    ai_recommendations: list[str] = Field(default_factory=list)
    upcoming_schedule: list[DashboardScheduleItemResponse] = Field(default_factory=list)
