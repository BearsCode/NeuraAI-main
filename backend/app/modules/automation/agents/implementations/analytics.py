from backend.app.modules.automation.agents.implementations.base import AgentType, AgentConfig
from backend.app.modules.automation.agents.registry import AgentRegistry
from backend.app.modules.automation.agents.capabilities.analytics import (
    CollectAnalyticsCapability,
    AnalyzePerformanceCapability,
    ImproveStrategyCapability
)

config = AgentConfig(
    id=AgentType.ANALYTICS,
    name="Analytics Agent",
    description="Анализирует результаты и улучшает стратегию.",
    dependencies=[AgentType.PUBLISHER],
    outputs=["analyticsData", "performanceReport", "strategyImprovements"],
    capabilities=[
        CollectAnalyticsCapability,
        AnalyzePerformanceCapability,
        ImproveStrategyCapability
    ]
)

AgentRegistry.register(config)
