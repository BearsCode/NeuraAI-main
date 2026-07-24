from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import execute_idempotent, get_current_user, require_idempotency_header
from backend.app.core.database import get_db_session
from backend.app.db.user import User
from backend.app.modules.ai_core.planner import AIPlanner
from backend.app.modules.ai_core.workflow_engine import WorkflowEngine
from backend.app.modules.ai_core.publisher_service import PublisherService

router = APIRouter(prefix="/ai-core", tags=["ai_core"])
planner = AIPlanner()
workflow_engine = WorkflowEngine()
publisher = PublisherService()


@router.post("/projects/{project_id}/analyze-need")
async def analyze_content_need(
    project_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await planner.analyze_content_need(session, x_tenant_id, project_id)


@router.post("/projects/{project_id}/create-plan")
async def create_content_plan(
    project_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await planner.create_content_plan(session, x_tenant_id, project_id)


@router.post("/projects/{project_id}/optimal-time")
async def get_optimal_time(
    project_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await planner.determine_optimal_time(session, x_tenant_id, project_id)


@router.post("/projects/{project_id}/adjust-strategy")
async def adjust_strategy(
    project_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await planner.adjust_strategy(session, x_tenant_id, project_id)


@router.post("/workflows/{workflow_id}/start")
async def start_workflow(
    workflow_id: str,
    request: Request,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    idempotency_key: str = Depends(require_idempotency_header),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await execute_idempotent(
        request=request,
        session=session,
        current_user=current_user,
        tenant_id=x_tenant_id,
        idempotency_key=idempotency_key,
        payload={},
        response_model=dict,
        operation=lambda: workflow_engine.start_workflow(session, workflow_id),
    )


@router.get("/workflows/{workflow_id}")
async def get_workflow_status(
    workflow_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await workflow_engine.get_workflow(session, workflow_id)


@router.get("/projects/{project_id}/scheduler/queue-status")
async def get_queue_status(
    project_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    from backend.app.modules.ai_core.scheduler import SchedulerService
    scheduler = SchedulerService()
    return await scheduler.check_content_queue(session, x_tenant_id, project_id)


@router.post("/publications/{publication_id}/publish")
async def publish_content(
    publication_id: str,
    request: Request,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    idempotency_key: str = Depends(require_idempotency_header),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await execute_idempotent(
        request=request,
        session=session,
        current_user=current_user,
        tenant_id=x_tenant_id,
        idempotency_key=idempotency_key,
        payload={},
        response_model=dict,
        operation=lambda: publisher.publish(session, publication_id),
    )


@router.post("/publications/{publication_id}/retry")
async def retry_publication(
    publication_id: str,
    request: Request,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    idempotency_key: str = Depends(require_idempotency_header),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await execute_idempotent(
        request=request,
        session=session,
        current_user=current_user,
        tenant_id=x_tenant_id,
        idempotency_key=idempotency_key,
        payload={},
        response_model=dict,
        operation=lambda: publisher.retry_publication(session, publication_id),
    )


@router.get("/publications/{publication_id}")
async def get_publication_status(
    publication_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await publisher.get_publication_status(session, publication_id)
