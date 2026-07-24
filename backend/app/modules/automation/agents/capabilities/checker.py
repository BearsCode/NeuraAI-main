from typing import Any
from backend.app.modules.automation.agents.capabilities.base import Capability
from backend.app.integrations.ai_adapters import build_ai_adapter, AIGenerateRequest

class CheckContentCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        context_data = kwargs.get("context", {})
        request = AIGenerateRequest(
            task_type="checker.check_content",
            context={
                "system_prompt": "Ты — Checker Agent платформы Нейра.\nПроверь контент перед публикацией. Строго, но без лишних блокировок.",
                "user_prompt": (
                    f"КОНТЕНТ: {context_data.get('post_text')}, хэштеги: {context_data.get('hashtags')}\n"
                    f"СКРИПТ: {context_data.get('video_script')}, платформа: {context_data.get('platform')}\n"
                    f"КРИТЕРИИ: tone {context_data.get('tone_of_voice')}, запреты {context_data.get('forbidden_topics')}, правила {context_data.get('platform_rules')}\n"
                    f"КАТАЛОГ (для сверки цен): {context_data.get('retail_catalog', 'Нет данных')}\n"
                    f"Проверь: орфографию, тон, запрещённые темы, хэштеги, длину, CTA, упоминания конкурентов, юридику. ЕСЛИ в контенте есть цена на товар, проверь ее актуальность по КАТАЛОГУ."
                ),
                "response_schema": {
                    "status": "string",
                    "score": "number",
                    "issues": ["string"],
                    "auto_fixes": "string",
                    "block_reason": "string"
                }
            }
        )
        return await adapter.generate(request)

class ValidateVideoCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        request = AIGenerateRequest(
            task_type="checker.validate_video",
            context={
                "system_prompt": "Универсальная проверка видео-контента перед публикацией.",
                "user_prompt": "Проверь длительность, наличие CTA и логотипа.",
                "response_schema": {
                    "is_valid": "boolean",
                    "issues": ["string"]
                }
            }
        )
        return await adapter.generate(request)
