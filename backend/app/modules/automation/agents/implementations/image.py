from backend.app.modules.automation.agents.implementations.base import AgentType, AgentConfig
from backend.app.modules.automation.agents.registry import AgentRegistry
from backend.app.modules.automation.agents.capabilities.image import (
    GenerateImageCapability,
    GenerateCarouselCapability,
    GenerateCoverCapability
)

config = AgentConfig(
    id=AgentType.IMAGE,
    name="Image Agent",
    description="Создает изображения.",
    dependencies=[AgentType.CONTENT, AgentType.BRAND],
    outputs=["image", "carousel", "cover"],
    capabilities=[
        GenerateImageCapability,
        GenerateCarouselCapability,
        GenerateCoverCapability
    ]
)

AgentRegistry.register(config)
