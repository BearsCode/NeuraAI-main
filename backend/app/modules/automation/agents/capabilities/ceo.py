from typing import Any
from backend.app.modules.automation.agents.capabilities.base import Capability
from backend.app.integrations.ai_adapters import build_ai_adapter, AIGenerateRequest
import json

class GenerateCEOBriefingCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        context_data = kwargs.get("context", {})
        request = AIGenerateRequest(
            task_type="ceo.generate_briefing",
            context={
                "system_prompt": "Ты — CEO Agent платформы Нейра.\nСделай еженедельный анализ и утренний брифинг для владельца бизнеса.",
                "user_prompt": (
                    f"Метрики: {json.dumps(context_data.get('metrics', {}))}\n"
                    f"Выполненный контент-план: {context_data.get('published_posts')}\n"
                    f"Сформулируй краткую выжимку (что хорошо, что плохо) и стратегический совет."
                ),
                "response_schema": {
                    "briefing": "string",
                    "insights": ["string"],
                    "strategy_recommendation": "string"
                }
            }
        )
        return await adapter.generate(request)
