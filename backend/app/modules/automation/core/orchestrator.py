import asyncio
import logging
from typing import Dict, Any, List, Set
from backend.app.modules.automation.agents.registry import AgentRegistry
from backend.app.modules.automation.agents.implementations.base import AgentType, AgentConfig

logger = logging.getLogger(__name__)


class WorkflowEngine:
    def __init__(self):
        self.internship_mode = True
        self.training_counter = 0
        self.TRAINING_THRESHOLD = 14

    def _build_execution_plan(self, target_agents: List[AgentType]) -> List[AgentConfig]:
        visited: Set[AgentType] = set()
        plan: List[AgentConfig] = []

        def visit(agent_type: AgentType):
            if agent_type in visited:
                return

            agent_config = AgentRegistry.get(agent_type)
            for dep in agent_config.dependencies:
                visit(dep)

            visited.add(agent_type)
            plan.append(agent_config)

        for agent in target_agents:
            visit(agent)

        return plan

    async def execute_dag(self, initial_context: Dict[str, Any], target_agents: List[AgentType]) -> Dict[str, Any]:
        plan = self._build_execution_plan(target_agents)

        context = initial_context.copy()

        for agent_config in plan:
            agent_results = {}
            for CapClass in agent_config.capabilities:
                cap_instance = CapClass()
                try:
                    result = await cap_instance.execute(context=context)
                    if result:
                        if hasattr(result, 'payload'):
                            if 'ai_telemetry' not in context:
                                context['ai_telemetry'] = {'total_cost': 0.0, 'total_tokens': 0, 'calls': []}
                            context['ai_telemetry']['calls'].append({
                                'agent': agent_config.id.value,
                                'capability': CapClass.__name__,
                                'tokens': result.usage.total_tokens,
                                'cost': result.usage.cost_usd,
                                'latency_ms': result.latency_ms,
                                'model': result.model_used,
                            })
                            context['ai_telemetry']['total_cost'] += result.usage.cost_usd
                            context['ai_telemetry']['total_tokens'] += result.usage.total_tokens

                            agent_results.update(result.payload)
                            context.update(result.payload)
                        else:
                            agent_results.update(result)
                            context.update(result)
                except Exception as e:
                    logger.exception("Capability execution failed", extra={"capability": CapClass.__name__, "error": str(e)})
                
                # Добавляем искусственную задержку, чтобы не упираться в лимиты API (Rate Limits 429)
                await asyncio.sleep(2.0)
            
            # Проверка режима стажировки, если это Publisher Agent
            if agent_config.id == AgentType.PUBLISHER:
                if self.internship_mode:
                    self.training_counter += 1
                    if self.training_counter >= self.TRAINING_THRESHOLD:
                        self.internship_mode = False

        return context


class Orchestrator(WorkflowEngine):
    async def run_pipeline(self, prompt: str, platform: str = "Instagram") -> Dict[str, Any]:
        initial_context = {
            "topic": prompt,
            "platform": platform,
            "tone_of_voice": "Friendly",
            "forbidden_topics": "politics",
        }

        target_agents = [AgentType.PUBLISHER]
        return await self.execute_dag(initial_context, target_agents)
