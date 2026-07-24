from typing import Any
from backend.app.modules.automation.agents.capabilities.base import Capability
from backend.app.integrations.ai_adapters import build_ai_adapter, AIGenerateRequest

class BuildBriefCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        context_data = kwargs.get("context", {})
        request = AIGenerateRequest(
            task_type="director.build_brief",
            context={
                "system_prompt": (
                    "Ты — Prompt Director платформы Нейра. Ты переводишь тему публикации в точное "
                    "техническое задание для видео-агентов — определяешь структуру сцен, длительность, стиль, "
                    "источники медиа и брендинг.\n"
                    "ПРАВИЛА:\n"
                    "1. Длительность: Reels/ВК 15-30с, Stories до 15с.\n"
                    "2. Структура сцен логически раскрывает тему.\n"
                    "3. Для конкретного товара укажи catalog_item_id и используй реальное фото/видео.\n"
                    "4. Определи нужны ли сгенерированные сцены или достаточно Каталога + стоков.\n"
                    "5. Для фоновых клипов укажи search_query."
                ),
                "user_prompt": (
                    f"Тема: {context_data.get('content_theme', 'Нет темы')}\n"
                    f"Карточка товара: {context_data.get('selected_product', 'Нет данных')}\n"
                    f"Ниша: {context_data.get('company_industry', '')}, Tone: {context_data.get('tone_of_voice', '')}\n"
                    f"Цвета: {context_data.get('brand_colors', '')}, Шрифты: {context_data.get('brand_fonts', '')}\n"
                    f"Площадка: {context_data.get('platform', 'Reels')}\n"
                    "Сформируй полный видео-бриф."
                ),
                "response_schema": {
                    "duration_sec": "number",
                    "platform": "string",
                    "aspect_ratio": "string",
                    "scenes": [
                        {
                            "timing": "string",
                            "description": "string",
                            "source": "string",
                            "catalog_item_id": "string",
                            "generation_agent": "string",
                            "stock_search_query": "string"
                        }
                    ],
                    "visual_style": {
                        "colors": ["string"],
                        "fonts": ["string"],
                        "mood": "string"
                    },
                    "branding": {
                        "logo_position": "string",
                        "appears_at_sec": "number"
                    }
                }
            }
        )
        return await adapter.generate(request)
