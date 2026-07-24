from __future__ import annotations

import asyncio
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app.core.database import get_session_factory
from backend.app.db.enums import UserRole
from backend.app.db.user import User
from backend.app.main import create_app


def _register_user(client: TestClient, prefix: str, referral_code: str | None = None) -> tuple[str, str]:
    email = f"{prefix}-{uuid4().hex[:10]}@example.com"
    payload = {
        "email": email,
        "password": "StrongPass123",
        "full_name": f"{prefix.title()} User",
    }
    if referral_code:
        payload["referral_code"] = referral_code
    register_response = client.post(
        "/api/v1/identity/register",
        json=payload,
    )
    assert register_response.status_code == 201, register_response.text
    verify_response = client.post(
        "/api/v1/identity/verify-email",
        json={"email": email, "code": register_response.json()["debug_code"]},
    )
    assert verify_response.status_code == 200, verify_response.text
    return email, verify_response.json()["access_token"]


def _promote_user_to_admin(email: str) -> None:
    async def _run() -> None:
        async with get_session_factory()() as session:
            user = await session.scalar(select(User).where(User.email == email))
            assert user is not None
            user.role = UserRole.ADMIN
            await session.commit()

    asyncio.run(_run())


def _create_business(client: TestClient, access_token: str) -> str:
    response = client.post(
        "/api/v1/onboarding/businesses",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Idempotency-Key": f"promo-onboarding-{uuid4().hex[:8]}",
        },
        json={
            "tenant_name": "Promo Tenant",
            "tenant_slug": f"promo-{uuid4().hex[:8]}",
            "company_name": "Promo Company",
            "business_description": "Subscription promo validation flow for product QA.",
            "city": "Moscow",
            "industry": "Marketing",
            "services": ["Strategy"],
            "social_links": [],
            "target_audience": "Growing B2B teams",
            "competitors": ["Agency Z"],
            "business_features": ["Approval workflow"],
            "timezone": "Europe/Moscow",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["tenant_id"]


def test_promocode_admin_and_billing_flow() -> None:
    app = create_app()

    with TestClient(app) as client:
        # Seed default plans so onboarding and billing see the same pricing surface.
        tariffs = client.get("/api/v1/tariffs")
        assert tariffs.status_code == 200, tariffs.text

        admin_email, admin_token = _register_user(client, "promo-admin")
        _promote_user_to_admin(admin_email)

        create_promocode = client.post(
            "/api/v1/admin/promocodes",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "code": "growth50",
                "description": "Half off Growth for first charge",
                "type_promo": "percent",
                "value": 50,
                "max_uses": 10,
                "is_active": True,
            },
        )
        assert create_promocode.status_code == 201, create_promocode.text
        assert create_promocode.json()["code"] == "GROWTH50"

        list_promocodes = client.get(
            "/api/v1/admin/promocodes",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert list_promocodes.status_code == 200, list_promocodes.text
        assert any(item["code"] == "GROWTH50" for item in list_promocodes.json())

        _, client_token = _register_user(client, "promo-client")
        tenant_id = _create_business(client, client_token)
        auth_headers = {
            "Authorization": f"Bearer {client_token}",
            "X-Tenant-ID": tenant_id,
        }

        preview = client.post(
            "/api/v1/billing/promocodes/preview",
            headers=auth_headers,
            json={
                "code": "growth50",
                "plan_code": "growth",
            },
        )
        assert preview.status_code == 200, preview.text
        preview_payload = preview.json()
        assert preview_payload["type_promo"] == "percent"
        assert preview_payload["original_price_amount"] == 39900
        assert preview_payload["discount_amount"] == 19950
        assert preview_payload["final_price_amount"] == 19950

        apply = client.patch(
            "/api/v1/billing/subscription",
            headers={
                **auth_headers,
                "Idempotency-Key": f"promo-apply-{uuid4().hex[:8]}",
            },
            json={
                "plan_code": "growth",
                "promo_code": "growth50",
            },
        )
        assert apply.status_code == 200, apply.text
        apply_payload = apply.json()
        assert apply_payload["plan_code"] == "growth"
        assert apply_payload["price_amount"] == 39900
        assert apply_payload["next_charge_amount"] == 19950
        assert apply_payload["applied_promocode"]["code"] == "GROWTH50"
        assert apply_payload["applied_promocode"]["final_price_amount"] == 19950

        subscription = client.get("/api/v1/billing/subscription", headers=auth_headers)
        assert subscription.status_code == 200, subscription.text
        assert subscription.json()["applied_promocode"]["code"] == "GROWTH50"

        reused = client.patch(
            "/api/v1/billing/subscription",
            headers={
                **auth_headers,
                "Idempotency-Key": f"promo-reuse-{uuid4().hex[:8]}",
            },
            json={
                "plan_code": "growth",
                "promo_code": "growth50",
            },
        )
        assert reused.status_code == 409
        assert reused.json()["message"] == "Promocode has already been redeemed for this tenant"


def test_successful_payment_accrues_partner_commission() -> None:
    app = create_app()

    with TestClient(app) as client:
        tariffs = client.get("/api/v1/tariffs")
        assert tariffs.status_code == 200, tariffs.text

        _, partner_token = _register_user(client, "partner-referrer")
        referral = client.get(
            "/api/v1/identity/partner/referral",
            headers={"Authorization": f"Bearer {partner_token}"},
        )
        assert referral.status_code == 200, referral.text
        referral_code = referral.json()["referral_code"]

        _, referred_token = _register_user(client, "partner-referred", referral_code=referral_code)
        tenant_id = _create_business(client, referred_token)
        referred_headers = {
            "Authorization": f"Bearer {referred_token}",
            "X-Tenant-ID": tenant_id,
        }

        subscription = client.patch(
            "/api/v1/billing/subscription",
            headers={
                **referred_headers,
                "Idempotency-Key": f"partner-plan-{uuid4().hex[:8]}",
            },
            json={"plan_code": "growth"},
        )
        assert subscription.status_code == 200, subscription.text
        subscription_id = subscription.json()["subscription_id"]

        payment = client.post(
            "/api/v1/payments/webhook",
            json={
                "subscription_id": subscription_id,
                "provider_payment_id": f"pay-{uuid4().hex[:8]}",
                "amount": 10000,
                "currency": "RUB",
                "status": "succeeded",
            },
        )
        assert payment.status_code == 200, payment.text
        assert payment.json()["status"] == "accepted"

        commissions = client.get(
            "/api/v1/billing/commissions",
            headers={"Authorization": f"Bearer {partner_token}"},
        )
        assert commissions.status_code == 200, commissions.text
        assert any(item["amount"] == 2000 for item in commissions.json())

        updated_referral = client.get(
            "/api/v1/identity/partner/referral",
            headers={"Authorization": f"Bearer {partner_token}"},
        )
        assert updated_referral.status_code == 200, updated_referral.text
        assert updated_referral.json()["pending_payout"] == 2000
