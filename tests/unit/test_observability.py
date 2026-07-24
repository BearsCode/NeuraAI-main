from __future__ import annotations

from dataclasses import dataclass, field

from starlette.routing import Match

from backend.app.observability.telemetry import _safe_get_route_name


@dataclass
class FakeRoute:
    match_result: Match
    path: str | None = None
    routes: list["FakeRoute"] = field(default_factory=list)

    def matches(self, scope):  # type: ignore[no-untyped-def]
        return self.match_result, {}


def test_safe_get_route_name_handles_router_without_path() -> None:
    nested_route = FakeRoute(match_result=Match.FULL, path="/api/v1/health/live")
    included_router = FakeRoute(match_result=Match.FULL, path=None, routes=[nested_route])

    route_name = _safe_get_route_name({"path": "/api/v1/health/live"}, [included_router])

    assert route_name == "/api/v1/health/live"
