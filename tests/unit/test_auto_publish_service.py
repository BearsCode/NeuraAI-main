from __future__ import annotations

from datetime import UTC, datetime

from backend.app.db.enums import PublicationStatus
from backend.app.db.publication import Publication
from backend.app.services.auto_publish_service import AutoPublishService


def test_auto_publish_window_matches_tenant_local_nine_am() -> None:
    service = AutoPublishService()
    publication = Publication(
        tenant_id="tenant-1",
        project_id="project-1",
        status=PublicationStatus.APPROVED,
        scheduled_at=datetime(2026, 6, 18, 5, 0, tzinfo=UTC),
    )

    assert service._is_autopublish_window(
        publication,
        "Europe/Moscow",
        datetime(2026, 6, 18, 6, 2, tzinfo=UTC),
    )


def test_auto_publish_window_rejects_outside_five_minute_window() -> None:
    service = AutoPublishService()
    publication = Publication(
        tenant_id="tenant-1",
        project_id="project-1",
        status=PublicationStatus.APPROVED,
        scheduled_at=datetime(2026, 6, 18, 5, 0, tzinfo=UTC),
    )

    assert not service._is_autopublish_window(
        publication,
        "Europe/Moscow",
        datetime(2026, 6, 18, 6, 10, tzinfo=UTC),
    )
