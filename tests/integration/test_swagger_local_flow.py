from fastapi.testclient import TestClient
from uuid import uuid4

from backend.app.main import create_app


def test_local_swagger_login_can_call_protected_mutating_endpoint_without_manual_headers() -> None:
    app = create_app()

    with TestClient(app) as client:
        register = client.post(
            "/api/v1/identity/register",
            json={
                "email": f"swagger-{uuid4().hex[:8]}@example.com",
                "password": "StrongPass123",
                "full_name": "Swagger User",
            },
            headers={"referer": "http://testserver/docs"},
        )
        assert register.status_code == 201
        verify = client.post(
            "/api/v1/identity/verify-email",
            json={
                "email": register.json()["email"],
                "code": register.json()["debug_code"],
            },
            headers={"referer": "http://testserver/docs"},
        )
        assert verify.status_code == 200

        create_business = client.post(
            "/api/v1/onboarding/businesses",
            json={
                "tenant_name": "Swagger Tenant",
                "tenant_slug": f"swagger-{uuid4().hex[:8]}",
                "company_name": "Swagger LLC",
                "business_description": "Local swagger auth and idempotency smoke test for onboarding.",
                "city": "Moscow",
                "industry": "saas",
                "services": ["automation"],
                "target_audience": "SMB founders",
                "business_features": ["speed"],
            },
            headers={"referer": "http://testserver/docs"},
        )
        assert create_business.status_code == 200
        assert create_business.headers.get("x-generated-idempotency-key")
