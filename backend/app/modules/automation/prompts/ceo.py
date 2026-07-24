from pydantic import BaseModel, Field

CEO_SYSTEM = """You are the CEO Agent (Chief Executive Officer) of a Social Media Strategy team.
Your job is to receive analytics reports, business goals, and current market context, and make high-level strategic decisions.
You do NOT write content. You dictate the strategy, focus, and content pillars for the upcoming week based on data.
Your output must be a JSON object containing the Morning Briefing (strategy directives)."""

CEO_USER = """
Business Context & Goals:
{business_context}

Last Week's Analytics Report:
{analytics_report}

Based on this data, pivot or reinforce the current strategy. What should the Marketing and Content agents focus on this week?
"""

class MorningBriefingSchema(BaseModel):
    strategic_focus: str = Field(..., description="The main strategic goal for the upcoming week.")
    content_pillars_to_prioritize: list[str] = Field(..., description="Specific topics or content pillars to focus on.")
    formats_to_avoid: list[str] = Field(..., description="Formats or topics to stop doing, based on analytics.")
    ceo_message: str = Field(..., description="A motivational and clear directive message to the agent team.")
