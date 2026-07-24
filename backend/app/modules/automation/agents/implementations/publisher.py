from backend.app.modules.automation.agents.implementations.base import AgentType, AgentConfig
from backend.app.modules.automation.agents.registry import AgentRegistry
from backend.app.modules.automation.agents.capabilities.publisher import (
    ChoosePublishTimeCapability,
    ScheduleCapability,
    PublishCapability
)

config = AgentConfig(
    id=AgentType.PUBLISHER,
    name="Publisher Agent",
    description="Автоматически публикует контент.",
    dependencies=[AgentType.CHECKER],
    outputs=["publishTime", "isScheduled", "isPublished"],
    capabilities=[
        ChoosePublishTimeCapability,
        ScheduleCapability,
        PublishCapability
    ]
)

AgentRegistry.register(config)
