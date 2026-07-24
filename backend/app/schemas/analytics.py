from pydantic import BaseModel


class AnalyticsMetric(BaseModel):
    name: str
    value: float | int
    unit: str


class AnalyticsOverviewResponse(BaseModel):
    project_id: str
    period: str
    metrics: list[AnalyticsMetric]
    ai_summary: list[str]
