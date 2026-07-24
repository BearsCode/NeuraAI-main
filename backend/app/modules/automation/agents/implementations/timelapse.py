from .base import AgentConfig, AgentType
from ..registry import AgentRegistry
from ..capabilities.timelapse import (
    AnalyzeProjectCapability,
    BuildStagesCapability,
    PlanCameraCapability,
    GenerateScenesCapability,
    AssembleFinalCapability
)
from ..capabilities.checker import ValidateVideoCapability

config = AgentConfig(
    id=AgentType.TIMELAPSE,
    name="Таймлапс Агент",
    description="Генерирует таймлапс-видео процессов (ремонт, производство).",
    dependencies=[AgentType.BUSINESS],
    outputs=[
        "video_url"
    ],
    capabilities=[
        AnalyzeProjectCapability,
        BuildStagesCapability,
        PlanCameraCapability,
        GenerateScenesCapability,
        AssembleFinalCapability,
        ValidateVideoCapability
    ]
)

AgentRegistry.register(config)
