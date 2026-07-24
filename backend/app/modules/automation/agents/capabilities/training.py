from typing import Any
from backend.app.modules.automation.agents.capabilities.base import Capability
from backend.app.integrations.ai_adapters import build_ai_adapter, AIGenerateRequest
import json

class UpdatePreferenceModelCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        context_data = kwargs.get("context", {})
        request = AIGenerateRequest(
            task_type="training.update_preferences",
            context={
                "system_prompt": "Ты — Training Agent платформы Нейра.\nОбработай сигнал обратной связи, обнови модель предпочтений.",
                "user_prompt": (
                    f"КОНТЕНТ: текст {context_data.get('post_text')}, тема {context_data.get('post_topic')}\n"
                    f"СИГНАЛ: {context_data.get('action')}, комментарий: {context_data.get('user_comment')}\n"
                    f"DIFF: {context_data.get('user_edit_diff')}, вес: {context_data.get('signal_weight')}\n"
                    f"ТЕКУЩАЯ МОДЕЛЬ: {json.dumps(context_data.get('preference_model_json', {}))}\n\n"
                    f"ЗАДАЧИ:\n"
                    f"1. Определи что понравилось/нет\n"
                    f"2. Если есть правка — извлеки паттерн\n"
                    f"3. Обнови веса"
                ),
                "response_schema": {
                    "signal_type": "string",
                    "detected_pattern": "string",
                    "preference_updates": {"topic_weights": "string", "tone_weights": "string"},
                    "learning_note": "string"
                }
            }
        )
        return await adapter.generate(request)
