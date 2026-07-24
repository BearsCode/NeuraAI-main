from pydantic import BaseModel
from typing import List

class BrandStyleSchema(BaseModel):
    color_palette: List[str]
    visual_style: str
    visual_forbidden: List[str]
    dalle_base_prompt: str
    photo_scene_template: str

BRAND_STYLE_SYSTEM = """
You are a Brand Agent. Analyze the visual materials and company profile.
Extract the visual style and generate a base prompt for DALL-E to maintain a consistent brand look.
"""

BRAND_STYLE_USER = """
Company Profile: {profile}
Tone of Voice: {tone}
Visual Guidelines: {visuals}

Generate the brand style guide.
"""
