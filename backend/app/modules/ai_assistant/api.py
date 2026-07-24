from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db_session
from backend.app.db.user import User
from backend.app.integrations.ai_adapters import AIGenerateRequest, build_ai_adapter
from backend.app.services_internal.business_memory import BusinessMemoryService

router = APIRouter(prefix="/ai-assistant", tags=["ai-assistant"])


class ChatMessageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str
    attachments: list[str] | None = None


class ActionCard(BaseModel):
    title: str
    action_type: str
    payload: dict[str, Any]


class ChatMessageResponse(BaseModel):
    reply: str
    suggested_actions: list[ActionCard] | None = None
    routed_agent: str | None = None


@router.post("/chat", response_model=ChatMessageResponse)
async def ai_assistant_chat(
    payload: ChatMessageRequest,
    x_tenant_id: str = Header(alias="X-Tenant-ID", default="default-tenant"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    business_context = ""
    try:
        memory = BusinessMemoryService()
        profile = await memory.get_company_profile(session, tenant_id=x_tenant_id, project_id=x_tenant_id)
        if profile:
            company = profile.get("company_name", "Unknown")
            desc = profile.get("description", "")
            business_context = f"\nBusiness: {company}\nDescription: {desc}\n"
    except Exception:
        pass

    system_prompt = f"""
    ROLE: Ты — CEO Agent платформы Нейра, центральный AI-ассистент.
    MISSION: Понимать контекст бизнеса пользователя и маршрутизировать запросы к специализированным агентам.

    RULES:
    1. Не раскрывай данные других клиентов.
    2. Не выполняй действия вне прав текущей роли.
    3. В ручном режиме не публикуй контент, только создавай черновики.
    4. Не давай юридических/налоговых/финансовых советов.
    5. Не раскрывай технические детали инфраструктуры.
    6. Не обещай гарантированных результатов.
    7. При отказе: кратко объясни причину, предложи альтернативу.
    8. Тон: дружелюбный, проактивный.

    Routing keywords:
    - "Напиши пост", "Перепиши текст" -> Content Agent
    - "Покажи аналитику", "Сравни показатели" -> Analytics
    - "Создай план", "Перепланируй" -> AI Planner
    - "Анализ конкурентов" -> Marketing Agent
    - "Сценарий Reels" -> Prompt Director + Content Agent
    - Загружено фото/прайс -> Retail Agent
    {business_context}
    """

    response_schema = {
        "type": "object",
        "properties": {
            "reply": {"type": "string"},
            "routed_agent": {"type": "string"},
            "actions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "action_type": {"type": "string"},
                        "payload": {"type": "object"},
                    },
                    "required": ["title", "action_type", "payload"],
                },
            },
        },
        "required": ["reply"],
    }



    user_prompt = payload.message
    if payload.attachments:
        user_prompt += f"\nAttachments: {', '.join(payload.attachments)}"

    try:
        adapter = build_ai_adapter()
        result = await adapter.generate(
            AIGenerateRequest(
                task_type="ai_assistant.chat",
                context={
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt,
                    "response_schema": response_schema,
                },
            )
        )
        data = result.payload
        reply = data.get("reply", "Извините, не удалось сформировать ответ.")
        routed_agent = data.get("routed_agent")
        actions_raw = data.get("actions", [])
        actions = [
            ActionCard(title=a["title"], action_type=a["action_type"], payload=a.get("payload", {}))
            for a in actions_raw if isinstance(a, dict) and "title" in a and "action_type" in a
        ]
        return ChatMessageResponse(
            reply=reply,
            suggested_actions=actions if actions else None,
            routed_agent=routed_agent,
        )
    except Exception as e:
        return ChatMessageResponse(reply=f"Ошибка: {str(e)}")
