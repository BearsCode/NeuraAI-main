from typing import Any
from backend.app.modules.automation.agents.capabilities.base import Capability
from backend.app.integrations.ai_adapters import build_ai_adapter, AIGenerateRequest
import json

class BuildBusinessProfileCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        context_data = kwargs.get("context", {})
        
        system_prompt = (
            "Ты — Business Agent платформы Нейра.\n"
            "Задача: провести глубокий анализ бизнеса и сформировать профиль компании.\n"
        )
        user_prompt = (
            f"ВХОДНЫЕ ДАННЫЕ:\n"
            f"Компания: {context_data.get('company_name', 'Unknown')}, сфера: {context_data.get('industry', 'Unknown')}\n"
            f"Ответы онбординга: {json.dumps(context_data.get('onboarding_answers', {}))}\n"
            f"Загруженные материалы: {context_data.get('uploaded_files_summary', '')}\n\n"
            f"ЗАДАЧИ:\n"
            f"1. Суть бизнеса: что продаёт, как зарабатывает, в чём ценность\n"
            f"2. Целевая аудитория: сегменты, боли, язык общения\n"
            f"3. USP — конкурентные преимущества\n"
            f"4. SWOT: сильные, слабые, возможности, угрозы\n"
            f"5. Tone of voice: формальный/неформальный, экспертный/дружелюбный\n"
            f"6. Запрещённые темы и ограничения\n"
            f"7. Ключевые сообщения для контента"
        )
        
        request = AIGenerateRequest(
            task_type="business.build_profile",
            context={
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "response_schema": {
                    "company_profile": "string",
                    "target_audience": ["string"],
                    "usp": ["string"],
                    "swot": "string",
                    "tone_of_voice": "string",
                    "forbidden_topics": ["string"],
                    "key_messages": ["string"]
                }
            }
        )
        return await adapter.generate(request)
