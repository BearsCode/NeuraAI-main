from typing import Any
from backend.app.modules.automation.agents.capabilities.base import Capability
from backend.app.integrations.ai_adapters import build_ai_adapter, AIGenerateRequest

class AnalyzeBrandStyleCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        context_data = kwargs.get("context", {})
        request = AIGenerateRequest(
            task_type="brand.analyze_style",
            context={
                "system_prompt": "Ты — Brand Agent платформы Нейра.\nПроанализируй визуальные материалы бренда и сформируй стайл-гайд.",
                "user_prompt": (
                    f"МАТЕРИАЛЫ: {context_data.get('uploaded_brand_files')}\n"
                    f"ПРОФИЛЬ: {context_data.get('company_profile')}\n"
                    f"TONE: {context_data.get('tone_of_voice')}\n\n"
                    f"ЗАДАЧИ:\n"
                    f"1. Цветовая палитра (hex-коды)\n"
                    f"2. Визуальный стиль: минимализм/насыщенность/профессионализм\n"
                    f"3. Список визуальных запретов\n"
                    f"4. Базовый промпт для DALL-E, отражающий стиль бренда\n"
                    f"5. Типичная сцена для фото-постов (фон, освещение, настроение)"
                ),
                "response_schema": {
                    "color_palette": ["string"],
                    "visual_style": "string",
                    "visual_forbidden": ["string"],
                    "dalle_base_prompt": "string",
                    "photo_scene_template": "string"
                }
            }
        )
        return await adapter.generate(request)
