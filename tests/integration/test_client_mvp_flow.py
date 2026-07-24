from __future__ import annotations

import os
import tempfile
from uuid import uuid4

from fastapi.testclient import TestClient

os.environ.setdefault(
    "DB__DSN",
    f"sqlite+aiosqlite:///{tempfile.gettempdir()}/neura-test-suite.db",
)
os.environ.setdefault("DB__RUN_MIGRATIONS_ON_STARTUP", "true")

from backend.app.main import create_app


def test_client_mvp_flow() -> None:
    app = create_app()
    email = f"mvp-{uuid4().hex[:8]}@example.com"

    with TestClient(app) as client:
        register = client.post(
            "/api/v1/identity/register",
            json={
                "email": email,
                "password": "StrongPass123",
                "full_name": "MVP Owner",
            },
        )
        assert register.status_code == 201
        verify = client.post(
            "/api/v1/identity/verify-email",
            json={"email": email, "code": register.json()["debug_code"]},
        )
        assert verify.status_code == 200
        auth_payload = verify.json()
        access_token = auth_payload["access_token"]

        create_business = client.post(
            "/api/v1/onboarding/businesses",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Idempotency-Key": "mvp-onboarding-001",
            },
            json={
                "tenant_name": "MVP Tenant",
                "tenant_slug": f"mvp-{uuid4().hex[:6]}",
                "company_name": "MVP Company",
                "business_description": "AI-driven marketing automation for B2B companies with strategy and analytics.",
                "city": "Moscow",
                "industry": "Marketing",
                "services": ["Strategy", "Analytics"],
                "social_links": [],
                "target_audience": "SMB founders",
                "competitors": ["Agency X"],
                "business_features": ["Fast setup", "Approval workflow"],
                "timezone": "Europe/Moscow",
            },
        )
        assert create_business.status_code == 200
        business = create_business.json()
        tenant_id = business["tenant_id"]
        project_id = business["project_id"]

        connect_social = client.post(
            f"/api/v1/social/projects/{project_id}/connections",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Tenant-ID": tenant_id,
            },
            json={
                "platform": "telegram",
                "account_handle": "@mvp_company",
                "access_token": "telegram-token",
                "autoposting_enabled": True,
                "publication_settings": {"parse_mode": "HTML"},
                "scopes": ["messages", "media"],
            },
        )
        assert connect_social.status_code == 200
        integration_id = connect_social.json()["integration_id"]

        ai_job = client.post(
            f"/api/v1/onboarding/projects/{project_id}/ai-analysis",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Tenant-ID": tenant_id,
                "Idempotency-Key": "mvp-ai-001",
            },
            json={"task_type": "strategy_generation"},
        )
        assert ai_job.status_code == 200

        content_plan = client.post(
            f"/api/v1/content-plans/projects/{project_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Tenant-ID": tenant_id,
                "Idempotency-Key": "mvp-plan-001",
            },
            json={
                "period_days": 7,
                "source_mode": "mixed",
                "platforms": ["telegram"],
                "content_types": ["post"],
            },
        )
        assert content_plan.status_code == 200
        first_item = content_plan.json()["items"][0]

        publication = client.post(
            f"/api/v1/publishing/projects/{project_id}/publications",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Tenant-ID": tenant_id,
                "Idempotency-Key": "mvp-publication-001",
            },
            json={
                "content_item_id": first_item["content_item_id"],
                "integration_ids": [integration_id],
                "all_or_nothing": True,
            },
        )
        assert publication.status_code == 200
        publication_id = publication.json()["publication_id"]

        approval = client.post(
            f"/api/v1/approval/publications/{publication_id}/approve",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Tenant-ID": tenant_id,
            },
        )
        assert approval.status_code == 200
        assert approval.json()["status"] == "approved"

        dashboard = client.get(
            f"/api/v1/dashboard/projects/{project_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Tenant-ID": tenant_id,
            },
        )
        assert dashboard.status_code == 200
        assert dashboard.json()["tenant_id"] == tenant_id

        analytics = client.get(
            f"/api/v1/analytics/projects/{project_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Tenant-ID": tenant_id,
            },
        )
        assert analytics.status_code == 200

        analytics_dashboard = client.get(
            "/api/v1/analytics/dashboard",
            params={"project_id": project_id},
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Tenant-ID": tenant_id,
            },
        )
        assert analytics_dashboard.status_code == 200
        assert analytics_dashboard.json()["tenant_id"] == tenant_id
        assert analytics_dashboard.json()["project_id"] == project_id
        assert analytics_dashboard.json()["points"]


def test_auto_publish_mode_creates_approved_publication() -> None:
    app = create_app()
    email = f"auto-{uuid4().hex[:8]}@example.com"

    with TestClient(app) as client:
        register = client.post(
            "/api/v1/identity/register",
            json={
                "email": email,
                "password": "StrongPass123",
                "full_name": "Auto Publish Owner",
            },
        )
        assert register.status_code == 201
        verify = client.post(
            "/api/v1/identity/verify-email",
            json={"email": email, "code": register.json()["debug_code"]},
        )
        assert verify.status_code == 200
        access_token = verify.json()["access_token"]

        create_business = client.post(
            "/api/v1/onboarding/businesses",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Idempotency-Key": "auto-onboarding-001",
            },
            json={
                "tenant_name": "Auto Tenant",
                "tenant_slug": f"auto-{uuid4().hex[:6]}",
                "company_name": "Auto Company",
                "business_description": "Automated publishing pipeline for timezone aware campaigns.",
                "city": "Moscow",
                "industry": "Marketing",
                "services": ["Strategy"],
                "social_links": [],
                "target_audience": "SMB founders",
                "competitors": ["Agency X"],
                "business_features": ["Autopublishing"],
                "timezone": "Europe/Moscow",
            },
        )
        assert create_business.status_code == 200
        business = create_business.json()
        tenant_id = business["tenant_id"]
        project_id = business["project_id"]

        policy = client.patch(
            f"/api/v1/approval/projects/{project_id}/policy",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Tenant-ID": tenant_id,
            },
            json={
                "mode": "auto",
                "auto_publish_enabled": True,
                "auto_publish_platforms": ["telegram"],
            },
        )
        assert policy.status_code == 200

        connect_social = client.post(
            f"/api/v1/social/projects/{project_id}/connections",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Tenant-ID": tenant_id,
            },
            json={
                "platform": "telegram",
                "account_handle": "@auto_company",
                "access_token": "telegram-token",
                "autoposting_enabled": True,
                "publication_settings": {"parse_mode": "HTML"},
                "scopes": ["messages"],
            },
        )
        assert connect_social.status_code == 200
        integration_id = connect_social.json()["integration_id"]

        content_plan = client.post(
            f"/api/v1/content-plans/projects/{project_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Tenant-ID": tenant_id,
                "Idempotency-Key": "auto-plan-001",
            },
            json={
                "period_days": 7,
                "source_mode": "mixed",
                "platforms": ["telegram"],
                "content_types": ["post"],
            },
        )
        assert content_plan.status_code == 200
        item = content_plan.json()["items"][0]

        publication = client.post(
            f"/api/v1/publishing/projects/{project_id}/publications",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Tenant-ID": tenant_id,
                "Idempotency-Key": "auto-publication-001",
            },
            json={
                "content_item_id": item["content_item_id"],
                "integration_ids": [integration_id],
                "all_or_nothing": True,
            },
        )
        assert publication.status_code == 200
        assert publication.json()["status"] == "approved"
        assert publication.json()["approval_required"] is False
