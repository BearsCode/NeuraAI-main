from .base import AgentConfig, AgentType
from ..registry import AgentRegistry
from ..capabilities.brand import AnalyzeBrandStyleCapability

config = AgentConfig(
    id=AgentType.BRAND,
    name="Brand Agent",
    description="Visual style, color palette, style guide.",
    dependencies=[AgentType.BUSINESS],
    outputs=[
        "color_palette",
        "visual_style",
        "visual_forbidden",
        "dalle_base_prompt",
        "photo_scene_template"
    ],
    capabilities=[AnalyzeBrandStyleCapability]
)

AgentRegistry.register(config)
