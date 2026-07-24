from .base import AgentConfig, AgentType
from ..registry import AgentRegistry
from ..capabilities.prompt_director import BuildBriefCapability

config = AgentConfig(
    id=AgentType.PROMPT_DIRECTOR,
    name="Prompt Director Agent",
    description="Переводит тему публикации в структурированный видео-бриф.",
    dependencies=[AgentType.CONTENT, AgentType.RETAIL],
    outputs=[
        "duration_sec",
        "platform",
        "aspect_ratio",
        "scenes",
        "visual_style",
        "branding"
    ],
    capabilities=[
        BuildBriefCapability
    ]
)

AgentRegistry.register(config)
