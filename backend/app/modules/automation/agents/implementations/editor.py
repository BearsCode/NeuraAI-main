from .base import AgentConfig, AgentType
from ..registry import AgentRegistry
from ..capabilities.editor import (
    WriteCompositionCapability,
    RenderAndQACapability,
    SyncCoverCapability
)

config = AgentConfig(
    id=AgentType.EDITOR,
    name="Editor Agent (Монтажёр)",
    description="Программный монтаж через Claude Code + Remotion.",
    dependencies=[
        AgentType.PROMPT_DIRECTOR, 
        AgentType.UGC_AVATAR, 
        AgentType.MOTION_PRODUCT, 
        AgentType.TIMELAPSE, 
        AgentType.VIDEO, 
        AgentType.PREVIEW
    ],
    outputs=[
        "composition_code_path",
        "final_video_url",
        "duration_sec",
        "scenes_used",
        "qa_report",
        "cover_sync_status"
    ],
    capabilities=[
        WriteCompositionCapability,
        RenderAndQACapability,
        SyncCoverCapability
    ]
)

AgentRegistry.register(config)
