from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class HealthComponentResponse(BaseModel):
    name: str
    status: Literal["ok", "degraded", "down"]
    details: dict[str, str] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "down"]
    service: str
    environment: str
    version: str
    timestamp: datetime
    components: list[HealthComponentResponse] = Field(default_factory=list)
