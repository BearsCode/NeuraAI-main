from pydantic import BaseModel


class AIAnalysisResponse(BaseModel):
    project_id: str
    business_analysis: list[str]
    market_analysis: list[str]
    competitor_analysis: list[str]


class StrategyResponse(BaseModel):
    project_id: str
    positioning: str
    content_pillars: list[str]
    channels: list[str]
    publishing_frequency: str


class AIRecommendationResponse(BaseModel):
    project_id: str
    recommendations: list[str]
    optimization_mode: str
