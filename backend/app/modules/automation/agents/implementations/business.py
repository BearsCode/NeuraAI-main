from .base import AgentConfig, AgentType
from ..registry import AgentRegistry
from ..capabilities.business import BuildBusinessProfileCapability

config = AgentConfig(
    id=AgentType.BUSINESS,
    name="Business Agent",
    description="Business analysis, SWOT, positioning.",
    dependencies=[],
    outputs=[
        "company_profile",
        "target_audience",
        "usp",
        "swot",
        "tone_of_voice",
        "forbidden_topics",
        "key_messages"
    ],
    capabilities=[BuildBusinessProfileCapability]
)

AgentRegistry.register(config)
