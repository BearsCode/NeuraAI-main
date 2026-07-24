from .base import AgentConfig, AgentType
from ..registry import AgentRegistry
from ..capabilities.checker import CheckContentCapability, ValidateVideoCapability

config = AgentConfig(
    id=AgentType.CHECKER,
    name="Checker Agent",
    description="Final moderation before publishing.",
    dependencies=[AgentType.CONTENT, AgentType.IMAGE, AgentType.VIDEO, AgentType.EDITOR, AgentType.PREVIEW],
    outputs=[
        "status",
        "score",
        "issues",
        "auto_fixes",
        "block_reason"
    ],
    capabilities=[CheckContentCapability, ValidateVideoCapability]
)

AgentRegistry.register(config)
