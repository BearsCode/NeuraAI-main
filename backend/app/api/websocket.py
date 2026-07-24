from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from backend.app.core.database import get_db_session
from backend.app.core.security import decode_access_token
from backend.app.db.internship_state import InternshipState
from backend.app.db.project import Project
from backend.app.db.user import User
from backend.app.integrations import ai_client
from backend.app.services_internal.business_memory import BusinessMemoryService

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, project_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        if project_id not in self.active_connections:
            self.active_connections[project_id] = []
        self.active_connections[project_id].append(websocket)

    def disconnect(self, project_id: str, websocket: WebSocket) -> None:
        if project_id in self.active_connections:
            self.active_connections[project_id] = [
                ws for ws in self.active_connections[project_id] if ws != websocket
            ]
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]

    async def send_to_project(self, project_id: str, message: dict[str, Any]) -> None:
        if project_id not in self.active_connections:
            return
        dead: list[WebSocket] = []
        for ws in self.active_connections[project_id]:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(project_id, ws)

    async def broadcast(self, message: dict[str, Any]) -> None:
        for project_id in list(self.active_connections.keys()):
            await self.send_to_project(project_id, message)


manager = ConnectionManager()


async def _get_user_from_ws(websocket: WebSocket) -> User | None:
    token = websocket.query_params.get("token") or websocket.headers.get("sec-websocket-protocol")
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        if payload is None:
            return None
        async for session in get_db_session():
            user = await session.get(User, payload.subject)
            return user
    except Exception:
        return None
    return None


async def _check_project_owner(project_id: str, user: User) -> Project | None:
    async for session in get_db_session():
        project = await session.get(Project, project_id)
        break
    if not project or project.user_id != user.id:
        return None
    return project


@router.websocket("/ws/onboarding/{project_id}")
async def onboarding_chat(websocket: WebSocket, project_id: str) -> None:
    user = await _get_user_from_ws(websocket)
    if not user:
        await websocket.close(code=4001)
        return

    project = await _check_project_owner(project_id, user)
    if not project:
        await websocket.close(code=4003)
        return

    await manager.connect(project_id, websocket)
    BusinessMemoryService()

    try:
        await websocket.send_json({
            "type": "chat_start",
            "message": "Привет! Я AI-ассистент NeuaraAI. Давай познакомимся с твоим бизнесом.",
            "questions": [
                "Чем занимается ваша компания?",
                "Кто ваша целевая аудитория?",
                "Что вы продаёте?",
                "В чём ваше ключевое отличие от конкурентов?",
                "Какие цели вы ставите перед маркетингом?",
            ],
        })

        answers: dict[str, str] = {}
        current_question_idx = 0
        questions = [
            "business_description",
            "target_audience",
            "products",
            "differentiation",
            "goals",
        ]

        while current_question_idx < len(questions):
            data = await websocket.receive_json()
            if data.get("type") == "answer":
                key = questions[current_question_idx]
                answers[key] = data.get("text", "")
                current_question_idx += 1

                if current_question_idx < len(questions):
                    await websocket.send_json({
                        "type": "question",
                        "field": questions[current_question_idx],
                        "text": _get_question_text(questions[current_question_idx]),
                    })
                else:
                    await websocket.send_json({
                        "type": "analyzing",
                        "message": "Анализирую ваш бизнес...",
                    })

                    analysis = await ai_client.generate(
                        prompt=(
                            f"Проанализируй бизнес на основе ответов владельца.\n"
                            f"Чем занимается: {answers.get('business_description', '')}\n"
                            f"Целевая аудитория: {answers.get('target_audience', '')}\n"
                            f"Продукты: {answers.get('products', '')}\n"
                            f"Отличие: {answers.get('differentiation', '')}\n"
                            f"Цели: {answers.get('goals', '')}\n\n"
                            f"Верни JSON с:\n"
                            f"- summary (str, краткий анализ на русском)\n"
                            f"- content_pillars (list[str], 3-5 рубрик для контента)\n"
                            f"- tone (str, рекомендуемый тон коммуникации)\n"
                            f"- recommendations (list[str], 2-3 рекомендации)"
                        ),
                        response_format={"type": "json_object"},
                    )

                    analysis_data = analysis if isinstance(analysis, dict) else {}
                    await websocket.send_json({
                        "type": "analysis_complete",
                        "analysis": {
                            "summary": analysis_data.get("summary", "Анализ завершён."),
                            "content_pillars": analysis_data.get("content_pillars", []),
                            "tone": analysis_data.get("tone", "профессиональный"),
                            "recommendations": analysis_data.get("recommendations", []),
                        },
                    })

                    await websocket.send_json({
                        "type": "chat_end",
                        "message": "Отлично! Я запомнил всю информацию о вашем бизнесе.",
                    })

            elif data.get("type") == "skip":
                answers[questions[current_question_idx]] = ""
                current_question_idx += 1
                if current_question_idx < len(questions):
                    await websocket.send_json({
                        "type": "question",
                        "field": questions[current_question_idx],
                        "text": _get_question_text(questions[current_question_idx]),
                    })

    except WebSocketDisconnect:
        logger.info("onboarding_ws_disconnect", extra={"project_id": project_id})
    except Exception as exc:
        logger.error("onboarding_ws_error", extra={"project_id": project_id, "error": str(exc)})
        try:
            await websocket.send_json({"type": "error", "message": "Internal error"})
        except Exception:
            pass
    finally:
        manager.disconnect(project_id, websocket)


@router.websocket("/ws/internship/{project_id}")
async def internship_status(websocket: WebSocket, project_id: str) -> None:
    user = await _get_user_from_ws(websocket)
    if not user:
        await websocket.close(code=4001)
        return

    project = await _check_project_owner(project_id, user)
    if not project:
        await websocket.close(code=4003)
        return

    await manager.connect(project_id, websocket)

    try:
        while True:
            async for session in get_db_session():
                state = await session.scalar(
                    select(InternshipState).where(InternshipState.project_id == project_id)
                )
                break

            if state:
                await websocket.send_json({
                    "type": "internship_status",
                    "stage": state.stage,
                    "day": state.day_number,
                    "total_days": state.total_days,
                    "approval_rate": state.approval_rate,
                    "is_extended": state.is_extended,
                    "started_at": state.started_at.isoformat() if state.started_at else None,
                })
            else:
                await websocket.send_json({
                    "type": "internship_status",
                    "stage": "not_started",
                })

            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info("internship_ws_disconnect", extra={"project_id": project_id})
    except Exception as exc:
        logger.error("internship_ws_error", extra={"project_id": project_id, "error": str(exc)})
    finally:
        manager.disconnect(project_id, websocket)


def _get_question_text(field: str) -> str:
    questions = {
        "business_description": "Расскажите подробнее, чем занимается ваша компания.",
        "target_audience": "Кто ваши идеальные клиенты? Опишите целевую аудиторию.",
        "products": "Какие продукты или услуги вы предлагаете?",
        "differentiation": "Чем вы отличаетесь от конкурентов?",
        "goals": "Какие маркетинговые цели вы ставите на ближайшие 3 месяца?",
    }
    return questions.get(field, "Расскажите подробнее.")
