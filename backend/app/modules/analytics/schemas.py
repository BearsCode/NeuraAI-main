from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class AnalyticsMetricResponse(BaseModel):
    name: str
    value: float | int
    unit: str


class AnalyticsOverviewResponse(BaseModel):
    snapshot_id: str
    tenant_id: str
    project_id: str
    platform: str
    collected_at: datetime
    metrics: list[AnalyticsMetricResponse] = Field(default_factory=list)
    ai_summary: list[str] = Field(default_factory=list)


class AnalyticsDashboardPoint(BaseModel):
    """Aggregated analytics metrics for one day and social platform."""

    date: date
    platform: str
    reach: int
    followers: int
    likes: int
    comments: int
    saves: int
    ctr: float
    er: float


class AnalyticsDashboardResponse(BaseModel):
    """Seven-day dashboard grouped by day and social platform."""

    tenant_id: str
    project_id: str
    days: int = 7
    points: list[AnalyticsDashboardPoint] = Field(default_factory=list)
