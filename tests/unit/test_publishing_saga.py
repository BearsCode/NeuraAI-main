from __future__ import annotations

from datetime import UTC, datetime

from backend.app.db.enums import (
    PublicationStatus,
    PublicationTargetStatus,
    IntegrationPlatform,
)
from backend.app.db.publication import Publication
from backend.app.db.publication_target import PublicationTarget
from backend.app.modules.publishing.saga import PublishingSagaCoordinator


def test_publishing_saga_compensates_published_targets_on_failure() -> None:
    publication = Publication(
        tenant_id="tenant-1",
        project_id="project-1",
        scheduled_at=datetime.now(UTC),
        all_or_nothing=True,
    )
    published_target = PublicationTarget(
        tenant_id="tenant-1",
        publication_id="publication-1",
        integration_id="integration-1",
        platform=IntegrationPlatform.TELEGRAM,
        status=PublicationTargetStatus.PUBLISHED,
    )
    failed_target = PublicationTarget(
        tenant_id="tenant-1",
        publication_id="publication-1",
        integration_id="integration-2",
        platform=IntegrationPlatform.VK,
        status=PublicationTargetStatus.QUEUED,
    )
    publication.targets = [published_target, failed_target]

    PublishingSagaCoordinator().handle_target_failure(publication, failed_target, all_or_nothing=True)

    assert publication.status == PublicationStatus.COMPENSATED
    assert published_target.status == PublicationTargetStatus.COMPENSATED
    assert failed_target.status == PublicationTargetStatus.FAILED
