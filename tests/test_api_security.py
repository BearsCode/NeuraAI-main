from __future__ import annotations

import json
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import create_app


def _register_user(client: TestClient) -> str:
    email = f"security-{uuid4().hex[:10]}@example.com"
    register_response = client.post(
        "/api/v1/identity/register",
        json={
            "email": email,
            "password": "StrongPass123",
            "full_name": "Security Test User",
        },
    )
    assert register_response.status_code == 201, register_response.text
    verify_response = client.post(
        "/api/v1/identity/verify-email",
        json={"email": email, "code": register_response.json()["debug_code"]},
    )
    assert verify_response.status_code == 200, verify_response.text
    return verify_response.json()["access_token"]


def _create_business(client: TestClient, access_token: str, *, idempotency_key: str, tenant_slug: str | None = None) -> dict[str, str]:
    response = client.post(
        "/api/v1/onboarding/businesses",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Idempotency-Key": idempotency_key,
        },
        json={
            "tenant_name": "Security Tenant",
            "tenant_slug": tenant_slug or f"security-{uuid4().hex[:8]}",
            "company_name": "Security Company",
            "business_description": "Security-focused marketing automation platform.",
            "city": "Moscow",
            "industry": "Marketing",
            "services": ["Strategy"],
            "social_links": [],
            "target_audience": "B2B owners",
            "competitors": ["Agency X"],
            "business_features": ["Approval workflow"],
            "timezone": "Europe/Moscow",
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    return {
        "tenant_id": payload["tenant_id"],
        "project_id": payload["project_id"],
    }


def test_identity_me_requires_valid_token() -> None:
    app = create_app()

    with TestClient(app) as client:
        unauthorized = client.get("/api/v1/identity/me")
        assert unauthorized.status_code == 401
        assert unauthorized.json()["error_code"] == "http_error"

        invalid = client.get(
            "/api/v1/identity/me",
            headers={"Authorization": "Bearer definitely-invalid-token"},
        )
        assert invalid.status_code == 401
        assert invalid.json()["message"] == "Could not validate credentials"


def test_onboarding_requires_idempotency_key() -> None:
    app = create_app()

    with TestClient(app) as client:
        access_token = _register_user(client)
        response = client.post(
            "/api/v1/onboarding/businesses",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "tenant_name": "No Idempotency Tenant",
                "tenant_slug": f"no-idem-{uuid4().hex[:8]}",
                "company_name": "No Idempotency Company",
                "business_description": "Missing idempotency key test.",
                "city": "Moscow",
                "industry": "Marketing",
                "services": ["Strategy"],
                "social_links": [],
                "target_audience": "SMB",
                "competitors": [],
                "business_features": ["Security"],
                "timezone": "Europe/Moscow",
            },
        )
        assert response.status_code == 400
        assert response.json()["message"] == "Idempotency-Key header is required"


def test_admin_endpoint_is_forbidden_for_client_role() -> None:
    app = create_app()

    with TestClient(app) as client:
        access_token = _register_user(client)
        response = client.get(
            "/api/v1/admin/overview",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 403
        assert response.json()["message"] == "Insufficient permissions"


def test_idempotency_payload_mismatch_returns_conflict() -> None:
    app = create_app()

    with TestClient(app) as client:
        access_token = _register_user(client)
        idempotency_key = f"security-idem-{uuid4().hex[:8]}"

        first = client.post(
            "/api/v1/onboarding/businesses",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Idempotency-Key": idempotency_key,
            },
                json={
                    "tenant_name": "Conflict Tenant One",
                    "tenant_slug": f"idem-{uuid4().hex[:8]}",
                    "company_name": "Conflict Company One",
                    "business_description": "Initial request with enough details for validation.",
                    "city": "Moscow",
                    "industry": "Marketing",
                    "services": ["Strategy"],
                    "social_links": [],
                    "target_audience": "SMB owners",
                    "competitors": [],
                    "business_features": ["Security"],
                    "timezone": "Europe/Moscow",
                },
        )
        assert first.status_code == 200, first.text

        second = client.post(
            "/api/v1/onboarding/businesses",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Idempotency-Key": idempotency_key,
            },
                json={
                    "tenant_name": "Conflict Tenant Two",
                    "tenant_slug": f"idem-{uuid4().hex[:8]}",
                    "company_name": "Conflict Company Two",
                    "business_description": "Modified request body.",
                    "city": "Saint Petersburg",
                    "industry": "Analytics",
                    "services": ["Analytics"],
                    "social_links": [],
                    "target_audience": "Enterprise buyers",
                    "competitors": ["Agency Y"],
                    "business_features": ["Different payload"],
                    "timezone": "Europe/Moscow",
                },
        )
        assert second.status_code == 409
        assert second.json()["message"] == "Idempotency key payload mismatch"


def test_ai_analysis_requires_tenant_header() -> None:
    app = create_app()

    with TestClient(app) as client:
        access_token = _register_user(client)
        business = _create_business(
            client,
            access_token,
            idempotency_key=f"security-onboarding-{uuid4().hex[:8]}",
        )

        response = client.post(
            f"/api/v1/onboarding/projects/{business['project_id']}/ai-analysis",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Idempotency-Key": f"security-ai-{uuid4().hex[:8]}",
            },
            json={"task_type": "strategy_generation"},
        )
        assert response.status_code == 400
        assert response.json()["message"] == "X-Tenant-ID header is required"


def test_health_ready_redacts_sensitive_details_and_sets_security_headers() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 200

        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "X-Request-ID" in response.headers

        payload = response.json()
        components = {component["name"]: component["details"] for component in payload["components"]}

        assert {"driver", "message"}.issubset(components["database"])
        assert {"backend", "tls"}.issubset(components["queue"])
        assert "dsn" not in components["queue"]
        assert "path" not in components["storage"]

        raw_body = json.dumps(payload)
        assert "redis://" not in raw_body
        assert "postgresql://" not in raw_body
        assert "storage/uploads" not in raw_body
