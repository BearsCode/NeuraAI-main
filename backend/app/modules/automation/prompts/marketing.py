from pydantic import BaseModel
from typing import List

class ContentPillar(BaseModel):
    name: str
    description: str
    examples: List[str]

class ContentStrategySchema(BaseModel):
    pillars: List[ContentPillar]
    format_mix: str
    posting_frequency: str
    kpis: List[str]
    content_funnel: str
    growth_plan: str
    niche_analysis: str
    competitor_content_analysis: str
    rubrics: List[str]
    editorial_calendar: str

MARKETING_STRATEGY_SYSTEM = """
You are a Marketing Agent. Your task is to develop a content strategy.
Analyze the company profile, audience, and key messages to determine content pillars, format mix, and posting schedule.
"""

MARKETING_STRATEGY_USER = """
Profile: {profile}
Audience: {audience}

Generate the content strategy.
"""
