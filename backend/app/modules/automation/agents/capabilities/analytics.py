from typing import Any
from backend.app.modules.automation.agents.capabilities.base import Capability
from backend.app.integrations.ai_adapters import build_ai_adapter, AIGenerateRequest
import json

class CollectAnalyticsCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        # Collects from DB / API
        return {"analytics_collected": True, "metrics": {"views": 1000, "likes": 50}}

class AnalyzePerformanceCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        context_data = kwargs.get("context", {})
        request = AIGenerateRequest(
            task_type="analytics.analyze_performance",
            context={
                "system_prompt": "Ты — AI Planner и Data Analyst. Твоя задача — проанализировать результаты контента.",
                "user_prompt": f"Метрики: {json.dumps(context_data.get('metrics', {}))}\nОпредели лучшие и худшие посты.",
                "response_schema": {
                    "top_performing": ["string"],
                    "low_performing": ["string"],
                    "insights": ["string"]
                }
            }
        )
        return await adapter.generate(request)

class ImproveStrategyCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        context_data = kwargs.get("context", {})
        request = AIGenerateRequest(
            task_type="analytics.improve_strategy",
            context={
                "system_prompt": "Ты — стратег. Обнови контент-стратегию на основе аналитики.",
                "user_prompt": f"Инсайты: {context_data.get('insights')}\nЧто нужно изменить в контент-плане?",
                "response_schema": {
                    "strategy_changes": ["string"],
                    "new_format_mix": "string"
                }
            }
        )
        return await adapter.generate(request)
