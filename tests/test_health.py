import unittest
import os
import tempfile

from fastapi.testclient import TestClient

os.environ.setdefault(
    "DB__DSN",
    f"sqlite+aiosqlite:///{tempfile.gettempdir()}/neura-test-suite.db",
)
os.environ.setdefault("DB__RUN_MIGRATIONS_ON_STARTUP", "true")

from backend.app.main import create_app


class HealthEndpointTests(unittest.TestCase):
    def test_live_and_ready_endpoints(self) -> None:
        app = create_app()
        with TestClient(app) as client:
            live_response = client.get("/api/v1/health/live")
            self.assertEqual(live_response.status_code, 200)
            self.assertEqual(live_response.json()["status"], "ok")

            ready_response = client.get("/api/v1/health/ready")
            self.assertEqual(ready_response.status_code, 200)
            ready_payload = ready_response.json()
            self.assertIn(ready_payload["status"], {"ok", "degraded"})
            component_names = {component["name"] for component in ready_payload["components"]}
            self.assertTrue({"database", "queue", "storage", "ai"}.issubset(component_names))
