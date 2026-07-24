from __future__ import annotations

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db_session
from backend.app.db.user import User
from backend.app.modules.agents import agent_registry
from backend.app.modules.agents.content_agent import ContentAgent
from backend.app.modules.agents.image_agent import ImageAgent
from backend.app.modules.agents.ceo_agent import CEOAgent
from backend.app.modules.agents.checker_agent import CheckerAgent
from backend.app.modules.agents.training_agent import TrainingAgent

router = APIRouter(prefix="/agents", tags=["agents"])


class AgentExecuteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    input_data: dict = {}


@router.get("")
async def list_agents():
    return {"agents": agent_registry.list_agents()}


@router.post("/{agent_name}/execute")
async def execute_agent(
    agent_name: str,
    payload: AgentExecuteRequest,
    project_id: str | None = None,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    agent = agent_registry.get_agent(agent_name)
    if not agent:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent '{agent_name}' not found")

    input_data = dict(payload.input_data)
    input_data.setdefault("project_id", project_id)
    input_data.setdefault("tenant_id", x_tenant_id)

    return await agent.execute(session, input_data)


@router.post("/content/generate")
async def generate_content(
    payload: AgentExecuteRequest,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    agent = ContentAgent()
    input_data = dict(payload.input_data)
    input_data.setdefault("tenant_id", x_tenant_id)
    return await agent.execute(session, input_data)


@router.post("/image/generate")
async def generate_image(
    payload: AgentExecuteRequest,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    agent = ImageAgent()
    input_data = dict(payload.input_data)
    input_data.setdefault("tenant_id", x_tenant_id)
    return await agent.execute(session, input_data)


@router.post("/checker/validate")
async def validate_content(
    payload: AgentExecuteRequest,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    agent = CheckerAgent()
    input_data = dict(payload.input_data)
    input_data.setdefault("tenant_id", x_tenant_id)
    return await agent.execute(session, input_data)


@router.post("/training/signal")
async def process_training_signal(
    payload: AgentExecuteRequest,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    agent = TrainingAgent()
    input_data = dict(payload.input_data)
    input_data.setdefault("tenant_id", x_tenant_id)
    return await agent.execute(session, input_data)


@router.post("/ceo/report")
async def generate_ceo_report(
    payload: AgentExecuteRequest,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    agent = CEOAgent()
    input_data = dict(payload.input_data)
    input_data.setdefault("tenant_id", x_tenant_id)
    return await agent.execute(session, input_data)
