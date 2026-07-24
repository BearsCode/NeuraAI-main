from typing import Any
from backend.app.modules.automation.agents.capabilities.base import Capability
from backend.app.integrations.ai_adapters import build_ai_adapter, AIGenerateRequest
from backend.app.integrations.media_adapters import build_image_adapter

class GenerateImageCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        context_data = kwargs.get("context", {})
        request = AIGenerateRequest(
            task_type="image.generate_prompt",
            context={
                "system_prompt": "Ты — Image Agent платформы Нейра. Создай промпт для изображения к посту. Промпт должен быть на английском.",
                "user_prompt": f"ПОСТ: {context_data.get('post_text')}\nСТИЛЬ: {context_data.get('brand_style')}",
                "response_schema": {
                    "dalle_prompt": "string",
                    "negative_prompt": "string",
                    "size": "string"
                }
            }
        )
        ai_response = await adapter.generate(request)
        
        # Now actually generate the image
        img_adapter = build_image_adapter()
        image_url = await img_adapter.generate_image(
            prompt=ai_response.payload.get("dalle_prompt", "Business illustration"),
            size="1024x1024"
        )
        
        ai_response.payload["image_url"] = image_url
        return ai_response

class GenerateCarouselCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        context_data = kwargs.get("context", {})
        request = AIGenerateRequest(
            task_type="image.generate_carousel",
            context={
                "system_prompt": "Ты — дизайнер. Придумай текстовые и визуальные описания для 3-5 слайдов карусели.",
                "user_prompt": f"Тема: {context_data.get('topic')}",
                "response_schema": {
                    "slides": [{"slide_number": "number", "text": "string", "image_prompt": "string"}]
                }
            }
        )
        return await adapter.generate(request)

class GenerateCoverCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        context_data = kwargs.get("context", {})
        request = AIGenerateRequest(
            task_type="image.generate_cover",
            context={
                "system_prompt": "Ты — дизайнер обложек (Reels/Shorts). Придумай промпт для обложки с крупным заголовком.",
                "user_prompt": f"Заголовок: {context_data.get('title')}",
                "response_schema": {
                    "cover_prompt": "string",
                    "text_overlay": "string"
                }
            }
        )
        return await adapter.generate(request)
