from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TriggerOptimizationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str | None = None


class OptimizationRecommendationResponse(BaseModel):
    recommendation_id: str
    tenant_id: str
    project_id: str
    status: str
    summary: str
    details: dict
    created_at: datetime
