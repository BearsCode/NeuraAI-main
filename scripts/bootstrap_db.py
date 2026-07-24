from __future__ import annotations

import asyncio
import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import select

from backend.app.core.database import close_database, get_session_factory, init_database
from backend.app.core.security import get_password_hash
from backend.app.core.configs import settings
from backend.app.db.models import AIExpertPrompt, SubscriptionPlan, User, UserRole

DEFAULT_PLANS = [
    {
        "code": "starter",
        "name": "Starter",
        "description": "MVP plan for small teams launching their first AI marketing pipeline.",
        "price_amount": 14900,
        "requests_per_minute": 120,
        "content_generations_per_hour": 80,
        "publications_per_hour": 30,
        "features": {
            "projects": 1,
            "platforms": ["telegram", "vk"],
            "approval_center": True,
            "analytics": True,
        },
    },
    {
        "code": "growth",
        "name": "Growth",
        "description": "Balanced plan for growing B2B teams with automation and partner payouts.",
        "price_amount": 39900,
        "requests_per_minute": 240,
        "content_generations_per_hour": 200,
        "publications_per_hour": 80,
        "features": {
            "projects": 3,
            "platforms": ["telegram", "vk", "instagram", "threads"],
            "approval_center": True,
            "analytics": True,
            "optimization": True,
        },
    },
    {
        "code": "scale",
        "name": "Scale",
        "description": "High-volume plan for agencies and multi-brand operations.",
        "price_amount": 89900,
        "requests_per_minute": 500,
        "content_generations_per_hour": 500,
        "publications_per_hour": 200,
        "features": {
            "projects": 10,
            "platforms": "all",
            "approval_center": True,
            "analytics": True,
            "optimization": True,
            "priority_support": True,
        },
    },
]

DEFAULT_AI_PROMPTS = [
    {
        "niche": "cosmetology",
        "role_description": "You are a senior beauty marketing strategist focused on trust, safety, and repeat visits.",
        "tone": "expert, warm, evidence-led",
        "additional_instructions": "Avoid medical claims; emphasize consultation, before-after proof, and retention offers.",
    },
    {
        "niche": "dentistry",
        "role_description": "You are a dental clinic growth strategist focused on patient trust and treatment education.",
        "tone": "calm, authoritative, reassuring",
        "additional_instructions": "Avoid fear tactics; explain procedures simply and highlight prevention.",
    },
    {
        "niche": "jewelry",
        "role_description": "You are a jewelry retail marketing expert focused on occasion-led demand and premium storytelling.",
        "tone": "refined, concise, emotionally resonant",
        "additional_instructions": "Use product provenance, gifting moments, and craftsmanship as core angles.",
    },
    {
        "niche": "restaurant",
        "role_description": "You are a restaurant marketing operator focused on reservations, repeat visits, and local discovery.",
        "tone": "appetizing, practical, energetic",
        "additional_instructions": "Prioritize menu hooks, social proof, events, and time-bound offers.",
    },
    {
        "niche": "real_estate",
        "role_description": "You are a real estate marketing strategist focused on lead quality and local market authority.",
        "tone": "confident, clear, data-aware",
        "additional_instructions": "Use neighborhood expertise, investment logic, and clear next steps.",
    },
    {
        "niche": "other",
        "role_description": "You are a B2B marketing strategist who builds practical AI-assisted content systems.",
        "tone": "direct, useful, business-oriented",
        "additional_instructions": "Keep advice specific to the business profile and measurable outcomes.",
    },
]


async def main() -> None:
    _run_migrations()
    await init_database()
    session_factory = get_session_factory()
    async with session_factory() as session:
        for plan in DEFAULT_PLANS:
            existing = await session.scalar(
                select(SubscriptionPlan).where(SubscriptionPlan.code == plan["code"])
            )
            if existing is None:
                session.add(
                    SubscriptionPlan(
                        code=plan["code"],
                        name=plan["name"],
                        description=plan["description"],
                        price_amount=plan["price_amount"],
                        currency=settings.billing.currency,
                        requests_per_minute=plan["requests_per_minute"],
                        content_generations_per_hour=plan["content_generations_per_hour"],
                        publications_per_hour=plan["publications_per_hour"],
                        features=plan["features"],
                    )
                )

        for prompt in DEFAULT_AI_PROMPTS:
            existing_prompt = await session.scalar(
                select(AIExpertPrompt).where(AIExpertPrompt.niche == prompt["niche"])
            )
            if existing_prompt is None:
                session.add(AIExpertPrompt(**prompt))

        admin_email = os.getenv("BOOTSTRAP_ADMIN_EMAIL") or settings.web.admin_login
        admin_password_secret = settings.web.admin_password
        admin_password = (
            os.getenv("BOOTSTRAP_ADMIN_PASSWORD")
            or (admin_password_secret.get_secret_value() if admin_password_secret else None)
        )
        admin_name = os.getenv("BOOTSTRAP_ADMIN_NAME", "Neura Platform Admin")
        if admin_email and admin_password:
            admin = await session.scalar(select(User).where(User.email == admin_email))
            if admin is None:
                session.add(
                    User(
                        email=admin_email,
                        password_hash=get_password_hash(admin_password),
                        full_name=admin_name,
                        role=UserRole.ADMIN,
                        is_active=True,
                        is_verified=True,
                    )
                )
            else:
                admin.password_hash = get_password_hash(admin_password)
                admin.full_name = admin_name
                admin.role = UserRole.ADMIN
                admin.is_active = True
                admin.is_verified = True

        await session.commit()

    await close_database()


def _run_migrations() -> None:
    """Bring the configured database to the latest schema before seeding defaults."""
    root_dir = Path(__file__).resolve().parents[1]
    alembic_cfg = Config(str(root_dir / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")


if __name__ == "__main__":
    asyncio.run(main())
