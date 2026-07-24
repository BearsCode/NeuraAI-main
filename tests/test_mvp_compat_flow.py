from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import create_app


def test_mvp_compat_business_content_approval_and_publish_flow() -> None:
    app = create_app()

    with TestClient(app) as client:
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"mvp-{uuid4().hex[:8]}@example.com",
                "password": "StrongPass123",
                "full_name": "MVP User",
            },
        )
        assert register_response.status_code == 201
        verify_response = client.post(
            "/api/v1/auth/verify-email",
            json={
                "email": register_response.json()["email"],
                "code": register_response.json()["debug_code"],
            },
        )
        assert verify_response.status_code == 200
        access_token = verify_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        business_response = client.post(
            "/api/v1/business/profile",
            headers=headers,
            json={
                "company_name": "MVP Dental",
                "description": "Dental clinic with implantology and preventive services",
                "city": "Moscow",
                "industry": "dentistry",
                "services": ["implantology", "cleaning"],
                "target_audience": "Adults who need careful dental treatment",
                "competitors": ["Clinic A"],
                "features": ["certified doctors"],
            },
        )
        assert business_response.status_code == 200
        assert business_response.json()["industry"] == "dentistry"

        social_response = client.post(
            "/api/v1/social/connect",
            headers=headers,
            json={
                "platform": "telegram",
                "account_identifier": "@mvpdental",
                "access_token": "token",
            },
        )
        assert social_response.status_code == 200

        plan_response = client.post(
            "/api/v1/content/plan/generate",
            headers=headers,
            json={"period_days": 7, "platforms": ["telegram"], "post_types": ["post"]},
        )
        assert plan_response.status_code == 200
        assert len(plan_response.json()["items"]) == 7

        queue_response = client.get("/api/v1/approval/posts", headers=headers)
        assert queue_response.status_code == 200
        post_id = queue_response.json()[0]["id"]

        approve_response = client.post(f"/api/v1/approval/posts/{post_id}/approve", headers=headers)
        assert approve_response.status_code == 200

        trigger_response = client.post(
            "/api/v1/publishing/trigger",
            headers=headers,
            json={"post_id": post_id},
        )
        assert trigger_response.status_code == 200
        assert trigger_response.json()["content_item_id"] == post_id


def test_miniplan_registration_dashboard_and_social_analysis_flow() -> None:
    app = create_app()
    email = f"mini-{uuid4().hex[:8]}@example.com"

    with TestClient(app) as client:
        referral_response = client.get("/api/v1/registration/referral", params={"code": "missing-code"})
        assert referral_response.status_code == 200
        assert referral_response.json()["is_valid"] is False

        code_response = client.post("/api/v1/registration/email/request-code", json={"email": email})
        assert code_response.status_code == 200
        debug_code = code_response.json()["debug_code"]
        assert debug_code is not None

        confirm_response = client.post(
            "/api/v1/registration/email/confirm",
            json={"email": email, "code": debug_code},
        )
        assert confirm_response.status_code == 200
        assert confirm_response.json()["verified"] is True

        complete_response = client.post(
            "/api/v1/registration/complete",
            json={
                "first_name": "Mini",
                "last_name": "Owner",
                "email": email,
                "password": "StrongPass123",
                "company_name": "Mini Plan Clinic",
                "category": "dentistry",
                "inn": "7707083893",
                "offer_accepted": True,
                "data_confirmed": True,
            },
        )
        assert complete_response.status_code == 201
        complete_payload = complete_response.json()
        access_token = complete_payload["auth"]["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        assert complete_payload["business_profile"]["inn"] == "7707083893"
        assert complete_payload["business_profile"]["onboarding_completed"] is True

        status_response = client.get("/api/v1/registration/status", headers=headers)
        assert status_response.status_code == 200
        assert status_response.json()["next_step"] == "tariffs"

        tariffs_response = client.get("/api/v1/tariffs")
        assert tariffs_response.status_code == 200
        assert {plan["code"] for plan in tariffs_response.json()} >= {"starter", "growth", "scale"}

        dashboard_response = client.get("/api/v1/dashboard/user", headers=headers)
        assert dashboard_response.status_code == 200
        assert dashboard_response.json()["can_run_brand_analysis"] is True

        brand_analysis_response = client.post("/api/v1/dashboard/brand-analysis", headers=headers)
        assert brand_analysis_response.status_code == 200
        assert brand_analysis_response.json()["task_type"] == "business_analysis"

        social_response = client.post(
            "/api/v1/social/connect",
            headers=headers,
            json={
                "platform": "telegram",
                "account_identifier": "@miniclinic",
                "access_token": "token",
            },
        )
        assert social_response.status_code == 200

        social_analysis_job = client.post("/api/v1/social/analyze", headers=headers)
        assert social_analysis_job.status_code == 200
        assert social_analysis_job.json()["task_type"] == "social_channel_analysis"

        social_analysis_response = client.get("/api/v1/social/analysis", headers=headers)
        assert social_analysis_response.status_code == 200
        assert social_analysis_response.json()["channels"][0]["platform"] == "telegram"
