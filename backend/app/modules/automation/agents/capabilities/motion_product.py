from typing import Any
from backend.app.modules.automation.agents.capabilities.base import Capability
from backend.app.integrations.ai_adapters import build_ai_adapter, AIGenerateRequest

class DetectObjectCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        request = AIGenerateRequest(
            task_type="motion.detect_object",
            context={
                "system_prompt": "Определение типа товара по фото из Каталога (украшение, техника, обувь, напиток и т.д.).",
                "user_prompt": "Определи тип объекта.",
                "response_schema": {
                    "detected_object_type": "string"
                }
            }
        )
        return await adapter.generate(request)

class SelectStyleCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        request = AIGenerateRequest(
            task_type="motion.select_style",
            context={
                "system_prompt": "Подбор стиля анимации (вращение, левитация, дым и т.д.) под тип товара и бренд-стиль.",
                "user_prompt": "Выбери стиль анимации.",
                "response_schema": {
                    "animation_style": "string"
                }
            }
        )
        return await adapter.generate(request)

class PlanScenesCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        context_data = kwargs.get("context", {})
        request = AIGenerateRequest(
            task_type="motion.plan_scenes",
            context={
                "system_prompt": (
                    "Ты — Motion-Товар Агент платформы Нейра. Ты создаёшь премиальные рекламные видео товаров, "
                    "где главный герой — сам продукт. Твоя задача — превратить обычное фото товара в "
                    "кинематографичную анимацию."
                ),
                "user_prompt": (
                    f"Товар: {context_data.get('selected_product')}\n"
                    f"Фирменные цвета: {context_data.get('brand_colors')}\n"
                    f"Стиль: {context_data.get('animation_style')}\n"
                    "Сгенерируй раскадровку строго из 5 сцен: тёмный фон -> появление товара -> "
                    "вращение/движение -> крупный план -> логотип."
                ),
                "response_schema": {
                    "scenes": [
                        { "scene_number": "number", "description": "string", "prompt": "string" }
                    ],
                    "music_mood": "string",
                    "target_model": "string"
                }
            }
        )
        return await adapter.generate(request)

class GenerateMotionVideoCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        request = AIGenerateRequest(
            task_type="motion.generate_video",
            context={
                "system_prompt": "Генерация видео по сценам через выбранную video-модель.",
                "user_prompt": "Сгенерируй сцены.",
                "response_schema": {
                    "scene_videos": ["string"]
                }
            }
        )
        return await adapter.generate(request)

class AssembleVideoCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        request = AIGenerateRequest(
            task_type="motion.assemble_video",
            context={
                "system_prompt": "Финальный монтаж — склейка сцен, музыка, переходы, логотип.",
                "user_prompt": "Собери видео.",
                "response_schema": {
                    "video_url": "string",
                    "logo_present": "boolean",
                    "aspect_ratio": "string"
                }
            }
        )
        return await adapter.generate(request)
