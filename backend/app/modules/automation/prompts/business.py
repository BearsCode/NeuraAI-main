from pydantic import BaseModel, Field

class CompanyProfileSchema(BaseModel):
    niche: str = Field(description="The main business niche")
    target_audience: str = Field(description="Description of target audience")
    usp: str = Field(description="Unique selling proposition")
    positioning: str = Field(description="Brand positioning in the market")
    competitors_analysis: str = Field(description="Analysis of key competitors")
    key_messages: list[str] = Field(description="Core messages to communicate to audience")
    forbidden_topics: list[str] = Field(description="Topics that should never be discussed by the brand")

ANALYZE_COMPANY_SYSTEM = """
You are an expert Business Analyst. 
Your goal is to analyze the provided raw company data and extract a structured company profile.
Be concise, analytical, and precise.
"""

ANALYZE_COMPANY_USER = """
Raw company data:
{raw_data}

Please generate the structured company profile.
"""

SWOT_SYSTEM = """
You are a strategic Business Analyst. 
Generate a comprehensive SWOT analysis based on the company profile.
"""

SWOT_USER = """
Company Profile:
{profile_data}
"""

TONE_OF_VOICE_SYSTEM = """
You are a Brand Strategist.
Define the exact Tone of Voice for this company. Return as a descriptive paragraph.
"""
