from typing import Any
from backend.app.modules.automation.agents.capabilities.base import Capability
from backend.app.integrations.ai_adapters import build_ai_adapter, AIGenerateRequest

class BuildContentStrategyCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        context_data = kwargs.get("context", {})
        system_prompt = (
            "Ты — Marketing Agent платформы Нейра.\n"
            "Разработай контентную стратегию для бизнеса."
        )
        user_prompt = (
            f"ПРОФИЛЬ: {context_data.get('company_profile')}\n"
            f"ЦА: {context_data.get('target_audience')}\n"
            f"КЛЮЧЕВЫЕ СООБЩЕНИЯ: {context_data.get('key_messages')}\n"
            f"ПЛАТФОРМЫ: {context_data.get('connected_platforms')}\n\n"
            f"ЗАДАЧИ:\n"
            f"1. 5–7 контентных рубрик с примерами тем\n"
            f"2. Баланс форматов: текст/фото/видео/карусель (%)\n"
            f"3. Частота публикаций по платформам\n"
            f"4. KPI на первый месяц: охват, ER, рост подписчиков\n"
            f"5. Контентная воронка: осведомлённость → вовлечение → конверсия"
        )
        request = AIGenerateRequest(
            task_type="marketing.build_strategy",
            context={
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "response_schema": {
                    "content_pillars": ["string"],
                    "format_mix": "string",
                    "posting_schedule": "string",
                    "kpi_month_1": "string",
                    "content_funnel": "string"
                }
            }
        )
        return await adapter.generate(request)
