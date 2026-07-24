from pydantic import BaseModel

class VisualConceptSchema(BaseModel):
    concept_description: str
    layout_instructions: str
    dalle_prompt: str

CREATIVE_SYSTEM = """
You are a Creative Agent. Your job is to ideate visual concepts and translate text ideas into detailed prompt instructions for image generators.
"""

CREATIVE_USER = """
Task: Create a visual concept for {task_type}.
Text content / topic: {topic}
Brand Style: {brand_style}
Target Platform: {platform}

Provide the concept description, layout instructions, and a ready-to-use DALL-E prompt.
"""
