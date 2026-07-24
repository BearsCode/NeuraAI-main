from typing import Any
from backend.app.modules.automation.agents.capabilities.base import Capability
from backend.app.integrations.ai_adapters import build_ai_adapter, AIGenerateRequest

class GenerateCoverCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        context_data = kwargs.get("context", {})
        request = AIGenerateRequest(
            task_type="preview.generate_cover",
            context={
                "system_prompt": (
                    "Ты — Preview Agent платформы Нейра. Ты создаёшь обложки (превью) для видео-контента, "
                    "которые зритель видит в ленте соцсети до воспроизведения ролика.\n"
                    "ПРАВИЛА:\n"
                    "1. Не бери случайный кадр, выбери 'продающий' момент.\n"
                    "2. Обязательно используй реальное фото товара из Каталога, не генерируй замену.\n"
                    "3. Для видео с ценой предложи вариант с крупным текстом.\n"
                    "4. Для UGC-Аватар видео — обложка с лицом аватара крупным планом.\n"
                    "5. Используй фирменные цвета и шрифты бренда.\n"
                    "6. Генерируй минимум 2 варианта с разным подходом."
                ),
                "user_prompt": (
                    f"Сценарий/Сцены: {context_data.get('scenes', 'Нет данных')}\n"
                    f"Карточка товара: {context_data.get('selected_product', 'Нет данных')}\n"
                    f"Брендинг: {context_data.get('brand_colors', '')}, {context_data.get('brand_fonts', '')}\n"
                    f"Площадка: {context_data.get('platform', 'Reels')}\n"
                    "Создай 2-3 варианта обложки."
                ),
                "response_schema": {
                    "variants": [
                        {
                            "image_url": "string",
                            "approach": "string",
                            "based_on_scene": "number",
                            "reasoning": "string"
                        }
                    ],
                    "aspect_ratio": "string",
                    "catalog_item_id": "string"
                }
            }
        )
        return await adapter.generate(request)
