from pydantic import BaseModel, Field

PACKAGING_SYSTEM = """You are the Packaging Agent for a social media brand.
Your job is to analyze the current state of a brand's social media profile and package it for maximum conversion and clarity.
You do not write daily posts. You generate the core profile elements: Bio, Highlights structure, and Pinned Post ideas."""

PACKAGING_USER = """
Business Description:
{description}

Target Audience:
{audience}

Please generate the packaging strategy for this profile.
"""

class PackagingSchema(BaseModel):
    bio_text: str = Field(..., description="An optimized Instagram/TikTok bio under 150 characters.")
    highlights: list[str] = Field(..., description="A list of 4-5 Highlight categories (e.g. 'About Us', 'Reviews', 'FAQ').")
    pinned_posts_ideas: list[str] = Field(..., description="Ideas for the top 3 pinned posts to maximize conversion.")
