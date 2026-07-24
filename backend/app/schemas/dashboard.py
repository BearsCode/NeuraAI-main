from datetime import datetime

from pydantic import BaseModel


class DashboardMetric(BaseModel):
    label: str
    value: str | int | float
    delta: str | None = None


class DashboardCalendarItem(BaseModel):
    publication_id: str
    platform: str
    scheduled_at: datetime
    status: str


class DashboardResponse(BaseModel):
    project_id: str
    metrics: list[DashboardMetric]
    ai_recommendations: list[str]
    content_calendar: list[DashboardCalendarItem]
    strategy_state: str
