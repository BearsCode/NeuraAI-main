from .base import AgentConfig, AgentType
from ..registry import AgentRegistry
from ..capabilities.planner import AnalyzeAndPlanCapability

config = AgentConfig(
    id=AgentType.PLANNER,
    name="AI Planner",
    description="Strategic planning, decides what/when to publish.",
    dependencies=[AgentType.BUSINESS, AgentType.MARKETING, AgentType.RETAIL],
    outputs=[
        "should_generate",
        "reason",
        "tasks"
    ],
    capabilities=[AnalyzeAndPlanCapability]
)

AgentRegistry.register(config)
