from pydantic import BaseModel, Field

ANALYTICS_SYSTEM = """You are the Analytics Agent for a Social Media Automation platform.
Your job is to analyze raw performance data (views, likes, comments, shares, etc.) from various platforms and extract meaningful insights.
You will be provided with the weekly stats.
Your output must be a structured JSON report identifying top performing content, worst performing content, and actionable optimization tips."""

ANALYTICS_USER = """
Weekly Performance Data:
{stats}

Previous Strategy:
{strategy}

Please analyze the metrics. Identify what worked well, what failed, and calculate the overall engagement trends.
"""

class AnalyticsReportSchema(BaseModel):
    top_performing_topics: list[str] = Field(..., description="Topics that got the highest engagement.")
    underperforming_topics: list[str] = Field(..., description="Topics that failed to get traction.")
    audience_insights: str = Field(..., description="General conclusion about what the audience wants.")
    optimization_tips: list[str] = Field(..., description="Actionable tips for the CEO Agent to consider for the next strategy.")
