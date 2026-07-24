from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import create_app


def test_legacy_workspace_flow() -> None:
    app = create_app()
    email = f"workspace-{uuid4().hex[:8]}@example.com"

    with TestClient(app) as client:
        register = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "Passw0rd",
                "full_name": "Workspace Owner",
                "company_name": "North Star Dental",
            },
        )
        assert register.status_code == 201
        verify = client.post(
            "/api/v1/auth/verify-email",
            json={"email": email, "code": register.json()["debug_code"]},
        )
        assert verify.status_code == 200
        tokens = verify.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        profile_before = client.get("/api/v1/users/me", headers=headers)
        assert profile_before.status_code == 200
        assert profile_before.json()["email"] == email
        assert profile_before.json()["referral_code"] is not None

        create_project = client.post(
            "/api/v1/projects",
            headers=headers,
            json={
                "company_name": "North Star Dental",
                "business_description": "Premium family dental clinic focused on implants, whitening, and retention.",
                "city": "Austin",
                "industry": "Healthcare",
                "services": ["Implants", "Whitening"],
                "website": "https://northstar.example.com",
                "phone": "+1 555 010 3000",
                "email": "hello@northstar.example.com",
                "social_links": ["https://t.me/northstar"],
                "target_audience": "Busy families and professionals seeking premium local care.",
                "competitors": ["Bright Smile", "Downtown Dental"],
                "business_features": ["Same-day consults", "Premium diagnostics"],
            },
        )
        assert create_project.status_code == 201
        project = create_project.json()
        project_id = project["project_id"]
        assert project["strategy_status"] == "draft"

        profile_after = client.get("/api/v1/users/me", headers=headers)
        assert profile_after.status_code == 200
        assert profile_after.json()["company_name"] == "North Star Dental"

        projects = client.get("/api/v1/projects", headers=headers)
        assert projects.status_code == 200
        assert projects.json()[0]["project_id"] == project_id

        project_detail = client.get(f"/api/v1/projects/{project_id}", headers=headers)
        assert project_detail.status_code == 200
        assert project_detail.json()["company_name"] == "North Star Dental"

        dashboard = client.get(f"/api/v1/dashboard/{project_id}", headers=headers)
        assert dashboard.status_code == 200
        assert dashboard.json()["project_id"] == project_id

        content_plan = client.post(
            f"/api/v1/content/{project_id}/plan/generate",
            headers=headers,
            json={
                "period_days": 7,
                "source_mode": "mixed",
                "platforms": ["telegram"],
                "content_types": ["post"],
            },
        )
        assert content_plan.status_code == 201
        assert len(content_plan.json()["items"]) == 7

        strategy = client.post(f"/api/v1/ai/{project_id}/generate", headers=headers)
        assert strategy.status_code == 200
        assert strategy.json()["project_id"] == project_id

        project_after_strategy = client.get(f"/api/v1/projects/{project_id}", headers=headers)
        assert project_after_strategy.status_code == 200
        assert project_after_strategy.json()["strategy_status"] == "active"
