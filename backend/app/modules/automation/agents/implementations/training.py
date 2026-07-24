from .base import AgentConfig, AgentType
from ..registry import AgentRegistry
from ..capabilities.training import UpdatePreferenceModelCapability

config = AgentConfig(
    id=AgentType.TRAINING,
    name="Training Agent",
    description="RLHF preference model updating.",
    dependencies=[],
    outputs=[
        "signal_type",
        "detected_pattern",
        "preference_updates",
        "learning_note"
    ],
    capabilities=[UpdatePreferenceModelCapability]
)

AgentRegistry.register(config)
