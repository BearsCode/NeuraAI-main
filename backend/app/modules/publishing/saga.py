from __future__ import annotations

from uuid import uuid4

from backend.app.db.enums import PublicationStatus, PublicationTargetStatus
from backend.app.db.publication import Publication
from backend.app.db.publication_target import PublicationTarget


class PublishingSagaCoordinator:
    """Coordinates multi-platform publication and compensation."""

    def start(self, publication: Publication, targets: list[PublicationTarget]) -> str:
        saga_id = uuid4().hex
        publication.saga_id = saga_id
        publication.status = PublicationStatus.QUEUED
        for target in targets:
            target.status = PublicationTargetStatus.QUEUED
        return saga_id

    def handle_target_success(self, publication: Publication, target: PublicationTarget) -> None:
        target.status = PublicationTargetStatus.PUBLISHED
        if all(item.status == PublicationTargetStatus.PUBLISHED for item in publication.targets):
            publication.status = PublicationStatus.PUBLISHED
        else:
            publication.status = PublicationStatus.IN_PROGRESS

    def handle_target_failure(
        self,
        publication: Publication,
        target: PublicationTarget,
        all_or_nothing: bool,
    ) -> None:
        target.status = PublicationTargetStatus.FAILED
        publication.status = PublicationStatus.FAILED
        if all_or_nothing:
            for candidate in publication.targets:
                if candidate.status == PublicationTargetStatus.PUBLISHED:
                    candidate.status = PublicationTargetStatus.COMPENSATED
            publication.status = PublicationStatus.COMPENSATED
