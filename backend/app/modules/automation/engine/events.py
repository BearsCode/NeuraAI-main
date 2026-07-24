from backend.app.events.schemas import EventEnvelope
from backend.app.modules.automation.agents.implementations.base import AgentType
from backend.app.modules.automation.engine.orchestrator import WorkflowOrchestrator

EVENT_ROUTING: dict[str, list[AgentType]] = {
    "content_queue_empty": [AgentType.PLANNER],
    "analytics_updated": [AgentType.PLANNER],
    "high_reach_achieved": [AgentType.PLANNER],
    "low_engagement": [AgentType.PLANNER],
    "trend_detected": [AgentType.CEO],
    "retail_sync_completed": [AgentType.RETAIL],
    "publication_completed": [AgentType.ANALYTICS],
}

class EventEngine:
    def __init__(self, orchestrator: WorkflowOrchestrator) -> None:
        self.orchestrator = orchestrator

    async def handle_event(self, envelope: EventEnvelope) -> None:
        target_agents = EVENT_ROUTING.get(envelope.event_type)
        if not target_agents:
            return

        context = {
            "tenant_id": envelope.tenant_id,
            "aggregate_id": envelope.aggregate_id,
            "event_payload": envelope.payload,
        }

        await self.orchestrator.execute_workflow(target_agents, context)
