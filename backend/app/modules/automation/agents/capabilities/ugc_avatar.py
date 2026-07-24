from typing import Any
from backend.app.modules.automation.agents.capabilities.base import Capability
from backend.app.integrations.ai_adapters import build_ai_adapter, AIGenerateRequest

class AnalyzeProductCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        context_data = kwargs.get("context", {})
        request = AIGenerateRequest(
            task_type="avatar.analyze_product",
            context={
                "system_prompt": "Ты — UGC AI-Аватар Агент платформы Нейра. Выполни анализ товара/услуги.",
                "user_prompt": f"Товар из каталога: {context_data.get('selected_product', 'Нет данных')}",
                "response_schema": {
                    "benefits": ["string"],
                    "pain_points": ["string"],
                    "value_proposition": "string",
                    "sales_scenario": "string"
                }
            }
        )
        return await adapter.generate(request)

class SelectFormatCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        context_data = kwargs.get("context", {})
        request = AIGenerateRequest(
            task_type="avatar.select_format",
            context={
                "system_prompt": "Выбери формат ролика на основе типа товара.",
                "user_prompt": f"Товар: {context_data.get('selected_product')}",
                "response_schema": {
                    "suggested_format": "string"
                }
            }
        )
        return await adapter.generate(request)

class WriteScriptCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        context_data = kwargs.get("context", {})
        request = AIGenerateRequest(
            task_type="avatar.write_script",
            context={
                "system_prompt": (
                    "Ты — UGC AI-Аватар Агент платформы Нейра. Ты пишешь сценарии продающих видео, "
                    "которые озвучивает AI-аватар бизнеса. Твоя речь должна звучать как естественное "
                    "обращение живого человека к камере."
                ),
                "user_prompt": (
                    f"Товар: {context_data.get('selected_product')}\n"
                    f"Тон: {context_data.get('tone_of_voice')}\n"
                    "Обязательно используй факты из карточки товара. "
                    "Структура: Хук -> Проблема -> Решение -> Демо -> Преимущества -> CTA."
                ),
                "response_schema": {
                    "hook": "string",
                    "problem": "string",
                    "solution": "string",
                    "product_demo": "string",
                    "benefits": ["string"],
                    "cta": "string",
                    "full_script": "string",
                    "estimated_duration_sec": "number",
                    "suggested_format": "string"
                }
            }
        )
        return await adapter.generate(request)

class GenerateVoiceCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        request = AIGenerateRequest(
            task_type="avatar.generate_voice",
            context={
                "system_prompt": "Генерация озвучки сценария голосом выбранного аватара",
                "user_prompt": "Генерация аудио",
                "response_schema": {
                    "audio_url": "string",
                    "audio_duration_sec": "number"
                }
            }
        )
        return await adapter.generate(request)

class GenerateAvatarVideoCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        request = AIGenerateRequest(
            task_type="avatar.generate_video",
            context={
                "system_prompt": "Генерация финального видео с AI-аватаром",
                "user_prompt": "Сгенерируй финальное видео с аватаром",
                "response_schema": {
                    "video_url": "string",
                    "duration": "number",
                    "aspect_ratio": "string"
                }
            }
        )
        return await adapter.generate(request)
