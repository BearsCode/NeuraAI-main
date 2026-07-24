from .base import AgentConfig, AgentType
from ..registry import AgentRegistry
from ..capabilities.ceo import GenerateCEOBriefingCapability

config = AgentConfig(
    id=AgentType.CEO,
    name="CEO Agent",
    description="Weekly analysis and briefing.",
    dependencies=[AgentType.ANALYTICS],
    outputs=[
        "briefing",
        "insights",
        "strategy_recommendation"
    ],
    capabilities=[GenerateCEOBriefingCapability]
)

AgentRegistry.register(config)
