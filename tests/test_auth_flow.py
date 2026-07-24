import unittest
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


class AuthFlowTests(unittest.TestCase):
    def test_register_refresh_and_read_profile(self) -> None:
        email = f"test-{uuid4().hex[:8]}@example.com"
        app = create_app()

        with TestClient(app) as client:
            register_response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "password": "StrongPass123",
                    "full_name": "Test User",
                    "company_name": "Acme",
                },
            )
            self.assertEqual(register_response.status_code, 201)
            register_payload = register_response.json()
            self.assertTrue(register_payload["verification_required"])

            verify_response = client.post(
                "/api/v1/auth/verify-email",
                json={
                    "email": email,
                    "code": register_payload["debug_code"],
                },
            )
            self.assertEqual(verify_response.status_code, 200)
            verify_payload = verify_response.json()
            self.assertIn("access_token", verify_payload)
            self.assertIn("refresh_token", verify_payload)

            profile_response = client.get(
                "/api/v1/users/me",
                headers={
                    "Authorization": f"Bearer {verify_payload['access_token']}",
                },
            )
            self.assertEqual(profile_response.status_code, 200)
            self.assertEqual(profile_response.json()["email"], email)

            refresh_response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": verify_payload["refresh_token"]},
            )
            self.assertEqual(refresh_response.status_code, 200)
            refresh_payload = refresh_response.json()
            self.assertIn("access_token", refresh_payload)
            self.assertIn("refresh_expires_in", refresh_payload)

            logout_response = client.post(
                "/api/v1/auth/logout",
                json={"refresh_token": refresh_payload["refresh_token"]},
            )
            self.assertEqual(logout_response.status_code, 200)
            self.assertEqual(
                logout_response.json()["message"],
                "Logged out successfully",
            )

    def test_update_profile_updates_user_and_company_context(self) -> None:
        email = f"profile-{uuid4().hex[:8]}@example.com"
        app = create_app()

        with TestClient(app) as client:
            register_response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "password": "StrongPass123",
                    "full_name": "Profile User",
                    "company_name": "Starter Brand",
                },
            )
            self.assertEqual(register_response.status_code, 201)
            register_payload = register_response.json()

            verify_response = client.post(
                "/api/v1/auth/verify-email",
                json={
                    "email": email,
                    "code": register_payload["debug_code"],
                },
            )
            self.assertEqual(verify_response.status_code, 200)
            access_token = verify_response.json()["access_token"]

            create_project_response = client.post(
                "/api/v1/projects",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "company_name": "Starter Brand",
                    "business_description": "A focused B2B service with fast onboarding.",
                    "city": "Moscow",
                    "industry": "IT services",
                    "services": ["Consulting"],
                    "website": "https://example.com",
                    "phone": "+7 999 123 45 67",
                    "email": "hello@example.com",
                    "social_links": ["https://t.me/example"],
                    "target_audience": "SMB owners and growth teams",
                    "competitors": ["Competitor A"],
                    "business_features": ["Fast launch"],
                },
            )
            self.assertEqual(create_project_response.status_code, 201)
            project_id = create_project_response.json()["project_id"]

            update_response = client.patch(
                "/api/v1/users/me",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "full_name": "Updated Profile User",
                    "phone": "+7 999 000 00 00",
                    "company_name": "Updated Brand",
                },
            )
            self.assertEqual(update_response.status_code, 200)
            update_payload = update_response.json()
            self.assertEqual(update_payload["full_name"], "Updated Profile User")
            self.assertEqual(update_payload["phone"], "+7 999 000 00 00")
            self.assertEqual(update_payload["company_name"], "Updated Brand")

            project_response = client.get(
                f"/api/v1/projects/{project_id}",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            self.assertEqual(project_response.status_code, 200)
            self.assertEqual(project_response.json()["company_name"], "Updated Brand")

    def test_update_profile_persists_without_existing_project(self) -> None:
        email = f"plain-profile-{uuid4().hex[:8]}@example.com"
        app = create_app()

        with TestClient(app) as client:
            register_response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "password": "StrongPass123",
                    "full_name": "Plain User",
                    "company_name": "Initial Company",
                },
            )
            self.assertEqual(register_response.status_code, 201)
            register_payload = register_response.json()

            verify_response = client.post(
                "/api/v1/auth/verify-email",
                json={
                    "email": email,
                    "code": register_payload["debug_code"],
                },
            )
            self.assertEqual(verify_response.status_code, 200)
            access_token = verify_response.json()["access_token"]

            update_response = client.patch(
                "/api/v1/users/me",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "full_name": "Plain User Updated",
                    "phone": "+7 999 111 22 33",
                    "company_name": "Updated Company",
                },
            )
            self.assertEqual(update_response.status_code, 200)

            profile_response = client.get(
                "/api/v1/users/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            self.assertEqual(profile_response.status_code, 200)
            profile_payload = profile_response.json()
            self.assertEqual(profile_payload["full_name"], "Plain User Updated")
            self.assertEqual(profile_payload["phone"], "+7 999 111 22 33")
            self.assertEqual(profile_payload["company_name"], "Updated Company")
