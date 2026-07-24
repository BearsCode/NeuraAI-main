from typing import Any
from backend.app.modules.automation.agents.capabilities.base import Capability
from backend.app.integrations.ai_adapters import build_ai_adapter, AIGenerateRequest

class AnalyzeAndPlanCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        context_data = kwargs.get("context", {})
        request = AIGenerateRequest(
            task_type="planner.plan_content",
            context={
                "system_prompt": "Ты — AI Planner платформы Нейра.\nРешай: нужно ли создавать контент прямо сейчас, и если да — что именно.",
                "user_prompt": (
                    f"БИЗНЕС-КОНТЕКСТ:\n"
                    f"Профиль: {context_data.get('company_profile')}, Рубрики: {context_data.get('content_pillars')}\n"
                    f"КАТАЛОГ (Меню/Товары): {context_data.get('retail_catalog', 'Нет данных')} \n"
                    f"Заметка/Пожелание (мягкий приоритет): {context_data.get('manual_catalog_input', 'Нет')}\n"
                    f"Модель предпочтений: {context_data.get('preference_model')}\n"
                    f"Запреты: {context_data.get('forbidden_topics')}, Tone: {context_data.get('tone_of_voice')}\n\n"
                    f"СОСТОЯНИЕ:\n"
                    f"Очередь: {context_data.get('queue_count', 0)} постов на {context_data.get('queue_days_ahead', 0)} дней\n"
                    f"Последние публикации: {context_data.get('recent_publications')}\n"
                    f"Топ по ER: {context_data.get('top_performing_content')}\n"
                    f"Аутсайдеры: {context_data.get('low_performing_content')}\n"
                    f"Платформы: {context_data.get('connected_platforms')}\n\n"
                    f"Если очередь < 7 постов — обязательно создать.\n"
                    f"Обязательно используй позиции из КАТАЛОГА для генерации тем, если они подходят под рубрики (естественное встраивание).\n"
                    f"Для каждого поста: рубрика, тема, формат, платформа, аватар, время публикации, приоритет."
                ),
                "response_schema": {
                    "should_generate": "boolean",
                    "reason": "string",
                    "tasks": [{"pillar": "string", "topic": "string", "format": "string", "platform": "string"}]
                }
            }
        )
        return await adapter.generate(request)
