from .base import AgentConfig, AgentType
from ..registry import AgentRegistry
from ..capabilities.ugc_avatar import (
    AnalyzeProductCapability,
    SelectFormatCapability,
    WriteScriptCapability,
    GenerateVoiceCapability,
    GenerateAvatarVideoCapability
)
from ..capabilities.checker import ValidateVideoCapability

config = AgentConfig(
    id=AgentType.UGC_AVATAR,
    name="UGC AI-Аватар Агент",
    description="Создаёт сценарии и генерирует продающие видео с AI-аватарами бизнеса.",
    dependencies=[AgentType.BUSINESS, AgentType.RETAIL],
    outputs=[
        "full_script",
        "video_url"
    ],
    capabilities=[
        AnalyzeProductCapability,
        SelectFormatCapability,
        WriteScriptCapability,
        GenerateVoiceCapability,
        GenerateAvatarVideoCapability,
        ValidateVideoCapability
    ]
)

AgentRegistry.register(config)
