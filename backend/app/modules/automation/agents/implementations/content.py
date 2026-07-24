from backend.app.modules.automation.agents.implementations.base import AgentType, AgentConfig
from backend.app.modules.automation.agents.registry import AgentRegistry
from backend.app.modules.automation.agents.capabilities.content import (
    GenerateTopicsCapability,
    WritePostsCapability,
    WriteStoriesCapability,
    WriteReelsCapability,
    GenerateCTA
)

config = AgentConfig(
    id=AgentType.CONTENT,
    name="Content Agent",
    description="Создает весь текстовый контент.",
    dependencies=[AgentType.PLANNER],
    outputs=["topics", "posts", "stories", "reels", "cta"],
    capabilities=[
        GenerateTopicsCapability,
        WritePostsCapability,
        WriteStoriesCapability,
        WriteReelsCapability,
        GenerateCTA
    ]
)

AgentRegistry.register(config)
