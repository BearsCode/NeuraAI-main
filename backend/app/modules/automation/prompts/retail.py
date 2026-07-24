from pydantic import BaseModel, Field

RETAIL_SYSTEM = """You are the Retail Agent.
Your job is to analyze a store's product catalog and extract marketing strategies for individual products, bundles, and promotions.
You are given a raw list of products and current inventory statuses."""

RETAIL_USER = """
Product Catalog (JSON or text):
{catalog}

Current Season/Context:
{season}

Extract the top priority products to push on social media, suggest a promotion, and bundle ideas.
"""

class RetailStrategySchema(BaseModel):
    priority_products: list[str] = Field(..., description="Top 3-5 products to feature this week based on catalog.")
    suggested_promotions: list[str] = Field(..., description="Ideas for discounts, giveaways, or flash sales.")
    bundle_ideas: list[str] = Field(..., description="Suggestions for pairing products together.")
