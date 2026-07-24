from typing import Any

from backend.app.modules.automation.agents.implementations.base import AgentType
from backend.app.modules.automation.agents.registry import AgentRegistry

class WorkflowOrchestrator:
    def __init__(self) -> None:
        self.registry = AgentRegistry

    def resolve_execution_order(self, target_agents: list[AgentType]) -> list[AgentType]:
        visited: set[AgentType] = set()
        order: list[AgentType] = []

        def visit(agent_id: AgentType) -> None:
            if agent_id in visited:
                return
            config = self.registry.get(agent_id)
            for dependency in config.dependencies:
                if dependency in target_agents:
                    visit(dependency)
            visited.add(agent_id)
            order.append(agent_id)

        for agent in target_agents:
            visit(agent)

        return order

    async def execute_workflow(self, target_agents: list[AgentType], initial_context: dict[str, Any]) -> dict[str, Any]:
        execution_order = self.resolve_execution_order(target_agents)
        workflow_state = initial_context.copy()

        for agent_id in execution_order:
            agent_config = self.registry.get(agent_id)
            
            for capability_class in agent_config.capabilities:
                capability_instance = capability_class()
                result = await capability_instance.execute(**workflow_state)
                
                if isinstance(result, dict):
                    workflow_state.update(result)

        return workflow_state
