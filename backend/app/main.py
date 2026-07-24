from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.staticfiles import StaticFiles

from backend.app.api.openapi import OPENAPI_TAGS
from backend.app.api.router import api_router
from backend.app.api.websocket import router as ws_router
from backend.app.core.database import close_database, database_manager, init_database
from backend.app.core.exceptions import register_exception_handlers
from backend.app.core.middleware import (
    AuthenticationContextMiddleware,
    RequestContextMiddleware,
    SecurityHeadersMiddleware,
)
from backend.app.modules.admin.dynamic_path import AdminPathMiddleware
from backend.app.core.redis import get_redis_client
from backend.app.core.configs import settings
from backend.app.observability.logging import configure_logging, get_logger
from backend.app.observability.telemetry import configure_telemetry
from backend.app.events import bus as event_bus_module
from backend.app.events.bus import RedisEventBus
from backend.app.events.engine import EventEngine
from backend.app.events.schemas import EventEnvelope
from backend.app.modules.automation.engine.events import EventEngine as AutomationEventEngine
from backend.app.modules.automation.engine.orchestrator import WorkflowOrchestrator
from backend.app.modules.ai_core.scheduler import SchedulerService

configure_logging()
logger = get_logger(__name__)

EVENT_TOPICS = [
    "biz:onboarded",
    "ai:requested",
    "content:plan_generated",
    "content:queue_empty",
    "publication:approved",
    "publication:completed",
    "publication:failed",
    "analytics:collected",
    "analytics:updated",
    "billing:charged",
    "optimization:suggested",
    "reach:high_achieved",
    "engagement:low",
    "image:generation_done",
    "video:generation_done",
    "retail:sync_completed",
    "avatar:training_done",
    "workflow:completed",
    "workflow:failed",
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Production safety checks
    if settings.app.env == "production" and settings.app.debug:
        raise RuntimeError("DEBUG must be False in production environment")
    if settings.app.env == "production" and settings.web.docs_enabled:
        logger.warning("docs_enabled is True in production - consider setting to False")
    if settings.app.env == "production" and settings.web.openapi_enabled:
        logger.warning("openapi_enabled is True in production - consider setting to False")
    
    redis = get_redis_client()
    app.state.redis = redis
    await init_database()

    # Initialize event bus singleton
    bus = RedisEventBus(redis)
    event_bus_module.event_bus = bus
    app.state.event_bus = bus

    # Initialize event engine with Redis pub/sub
    event_engine = EventEngine(redis)
    app.state.event_engine = event_engine

    # Bridge automation EventEngine
    orchestrator = WorkflowOrchestrator()
    automation_engine = AutomationEventEngine(orchestrator)

    @event_engine.on("content_queue_empty")
    async def _on_content_queue_empty(envelope, session):
        await automation_engine.handle_event(envelope)

    @event_engine.on("analytics_updated")
    async def _on_analytics_updated(envelope, session):
        await automation_engine.handle_event(envelope)

    @event_engine.on("high_reach_achieved")
    async def _on_high_reach(envelope, session):
        await automation_engine.handle_event(envelope)

    @event_engine.on("low_engagement")
    async def _on_low_engagement(envelope, session):
        await automation_engine.handle_event(envelope)

    @event_engine.on("trend_detected")
    async def _on_trend(envelope, session):
        await automation_engine.handle_event(envelope)

    @event_engine.on("retail_sync_completed")
    async def _on_retail_sync(envelope, session):
        await automation_engine.handle_event(envelope)

    @event_engine.on("publication_completed")
    async def _on_publication_completed(envelope, session):
        await automation_engine.handle_event(envelope)

    # Autonomous content cycle background task
    scheduler = SchedulerService()
    CYCLE_LOCK_KEY = "scheduler:content_cycle_lock"
    MAX_PUBS_PER_CYCLE = 50

    async def _content_cycle_loop():
        while True:
            cycle_lock = await redis.set(CYCLE_LOCK_KEY, "1", nx=True, ex=60)
            if cycle_lock:
                try:
                    from backend.app.core.database import get_db_session
                    async for session in get_db_session():
                        try:
                            due = await scheduler.check_publication_queue(session)
                            for pub in due[:MAX_PUBS_PER_CYCLE]:
                                try:
                                    await bus.publish(
                                        EventEnvelope(
                                            event_type="publication_due",
                                            topic="publication:completed",
                                            tenant_id=pub["tenant_id"],
                                            aggregate_id=pub["publication_id"],
                                            payload=pub,
                                        )
                                    )
                                except Exception:
                                    logger.exception("Failed to publish publication_due event")
                        finally:
                            await session.close()
                except Exception:
                    logger.exception("content_cycle iteration failed")
                finally:
                    await redis.delete(CYCLE_LOCK_KEY)

            await asyncio.sleep(300)

    listen_task = asyncio.create_task(event_engine.listen_loop(EVENT_TOPICS))
    content_cycle_task = asyncio.create_task(_content_cycle_loop())

    logger.info(
        "application_started",
        extra={
            "environment": settings.app.env,
            "api_prefix": settings.web.api_v1_prefix,
            "database_driver": settings.database_driver_name,
            "storage_backend": settings.storage_backend,
            "ai_provider": settings.ai.provider,
        },
    )
    try:
        yield
    finally:
        listen_task.cancel()
        content_cycle_task.cancel()
        await redis.aclose()
        await close_database()
        logger.info("application_stopped", extra={"environment": settings.app.env})


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app.name,
        version=settings.app.version,
        description="Production-grade backend for Neura AI B2B marketing SaaS",
        debug=settings.app.debug,
        docs_url=None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.web.openapi_enabled else None,
        openapi_tags=OPENAPI_TAGS,
        lifespan=lifespan,
    )

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(AdminPathMiddleware)
    app.add_middleware(AuthenticationContextMiddleware)
    app.add_middleware(RequestContextMiddleware)

    if settings.web.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.web.cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type", "X-Tenant-ID", "Idempotency-Key", "X-Device-Fingerprint", "X-Admin-Path"],
        )

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.web.api_v1_prefix)
    app.include_router(ws_router)
    configure_telemetry(app, engine=database_manager.engine)

    if settings.web.docs_enabled:
        static_dir = Path(__file__).parent / "static"
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

        @app.get("/docs", include_in_schema=False)
        async def swagger_ui_html():
            return get_swagger_ui_html(
                openapi_url=app.openapi_url,
                title=f"{settings.app.name} - Swagger UI",
                swagger_js_url="/static/swagger-ui-bundle.js",
                swagger_css_url="/static/swagger-ui.css",
            )

        @app.get("/redoc", include_in_schema=False)
        async def redoc_html():
            return get_redoc_html(
                openapi_url=app.openapi_url,
                title=f"{settings.app.name} - ReDoc",
                redoc_js_url="/static/redoc.standalone.js",
            )

    return app


app = create_app()
