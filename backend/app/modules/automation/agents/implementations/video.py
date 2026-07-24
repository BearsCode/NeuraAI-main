from backend.app.modules.automation.agents.implementations.base import AgentType, AgentConfig
from backend.app.modules.automation.agents.registry import AgentRegistry
from backend.app.modules.automation.agents.capabilities.video import (
    CreateAvatarCapability,
    GenerateVideoCapability,
    AddVoiceCapability,
    AddSubtitlesCapability
)

config = AgentConfig(
    id=AgentType.VIDEO,
    name="Video Agent",
    description="Создает видеоконтент.",
    dependencies=[AgentType.CONTENT, AgentType.BRAND],
    outputs=["avatar", "video", "voice", "subtitles"],
    capabilities=[
        CreateAvatarCapability,
        GenerateVideoCapability,
        AddVoiceCapability,
        AddSubtitlesCapability
    ]
)

AgentRegistry.register(config)
