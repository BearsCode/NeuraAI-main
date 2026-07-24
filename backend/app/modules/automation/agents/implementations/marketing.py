from .base import AgentConfig, AgentType
from ..registry import AgentRegistry
from ..capabilities.marketing import BuildContentStrategyCapability

config = AgentConfig(
    id=AgentType.MARKETING,
    name="Marketing Agent",
    description="Content strategy, rubrics, formats.",
    dependencies=[AgentType.BUSINESS],
    outputs=[
        "content_pillars",
        "format_mix",
        "posting_schedule",
        "kpi_month_1",
        "content_funnel"
    ],
    capabilities=[BuildContentStrategyCapability]
)

AgentRegistry.register(config)
