from __future__ import annotations

from collections.abc import Sequence

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_fastapi_instrumentator import routing as instrumentator_routing
from starlette.requests import HTTPConnection
from starlette.routing import Match
from starlette.types import Scope

from backend.app.core.configs import settings


def configure_telemetry(app: FastAPI, engine) -> None:
    if settings.observability.metrics_enabled:
        _patch_instrumentator_route_name_resolution()
        Instrumentator().instrument(app).expose(app)

    if not settings.observability.traces_enabled or not settings.observability.otlp_endpoint:
        return

    resource = Resource.create({"service.name": settings.observability.service_name})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.observability.otlp_endpoint))
    )
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)
    RedisInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)


def _patch_instrumentator_route_name_resolution() -> None:
    instrumentator_routing._get_route_name = _safe_get_route_name
    instrumentator_routing.get_route_name = _safe_get_request_route_name


def _safe_get_route_name(
    scope: Scope,
    routes: Sequence[object],
    route_name: str | None = None,
) -> str | None:
    for route in routes:
        matches = getattr(route, "matches", None)
        if not callable(matches):
            continue

        match, child_scope = matches(scope)
        path = getattr(route, "path", None)
        child_routes = getattr(route, "routes", None)

        if match == Match.FULL:
            resolved_name = path
            merged_scope = {**scope, **child_scope}
            if child_routes:
                child_route_name = _safe_get_route_name(merged_scope, child_routes, resolved_name)
                if child_route_name is None:
                    resolved_name = None
                elif resolved_name:
                    resolved_name += child_route_name
                else:
                    resolved_name = child_route_name
            return resolved_name

        if match == Match.PARTIAL and route_name is None and path:
            route_name = path

    return route_name


def _safe_get_request_route_name(request: HTTPConnection) -> str | None:
    app = request.app
    scope = request.scope
    routes = app.routes
    route_name = _safe_get_route_name(scope, routes)

    if not route_name and app.router.redirect_slashes and scope["path"] != "/":
        redirect_scope = dict(scope)
        if scope["path"].endswith("/"):
            redirect_scope["path"] = scope["path"][:-1]
            trim = True
        else:
            redirect_scope["path"] = scope["path"] + "/"
            trim = False

        route_name = _safe_get_route_name(redirect_scope, routes)
        if route_name is not None:
            route_name = route_name + "/" if trim else route_name[:-1]

    return route_name
