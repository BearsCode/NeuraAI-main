from __future__ import annotations

from datetime import UTC, datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.dialects import postgresql

revision: str = "20260704_000011"
down_revision: Union[str, None] = "20260702_000010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    session = orm.Session(bind=bind)

    now = datetime.now(UTC)

    # Seed Business plan (25,000 RUB/month)
    business_plan = session.execute(
        sa.text(
            "SELECT id FROM subscription_plans WHERE code = 'business' LIMIT 1"
        )
    ).fetchone()

    if not business_plan:
        session.execute(
            sa.text(
                """INSERT INTO subscription_plans (id, code, name, description, price_amount, currency,
                   requests_per_minute, content_generations_per_hour, publications_per_hour, features, is_active,
                   created_at, updated_at)
                VALUES (gen_random_uuid(), 'business', 'Бизнес', 'Тариф для владельцев МСБ',
                        25000, 'RUB', 120, 100, 50,
                        '{"ai_avatar": true, "ai_retail": true, "auto_publish": true, "internship": true,
                          "analytics": true, "ceo_reports": true, "referral_program": false, "priority_support": false,
                          "collaboration": false}',
                        true, :now, :now)"""
            ),
            {"now": now},
        )

    # Seed Creator plan (30,000 RUB/month)
    creator_plan = session.execute(
        sa.text(
            "SELECT id FROM subscription_plans WHERE code = 'creator' LIMIT 1"
        )
    ).fetchone()

    if not creator_plan:
        session.execute(
            sa.text(
                """INSERT INTO subscription_plans (id, code, name, description, price_amount, currency,
                   requests_per_minute, content_generations_per_hour, publications_per_hour, features, is_active,
                   created_at, updated_at)
                VALUES (gen_random_uuid(), 'creator', 'Креатор', 'Тариф для контент-мейкеров и предпринимателей',
                        30000, 'RUB', 120, 100, 50,
                        '{"ai_avatar": true, "ai_retail": true, "auto_publish": true, "internship": true,
                          "analytics": true, "ceo_reports": true, "referral_program": true, "priority_support": true,
                          "collaboration": true}',
                        true, :now, :now)"""
            ),
            {"now": now},
        )

    session.commit()


def downgrade() -> None:
    op.execute("DELETE FROM subscription_plans WHERE code IN ('business', 'creator')")
