from __future__ import annotations

from backend.app.core.configs import settings
from backend.app.workers.analytics_worker import WorkerSettings as AnalyticsWorkerSettings
from backend.app.workers.llm_worker import WorkerSettings as LlmWorkerSettings
from backend.app.workers.outbox_worker import WorkerSettings as OutboxWorkerSettings
from backend.app.workers.publisher_worker import WorkerSettings as PublisherWorkerSettings


def test_workers_use_dedicated_queue_names() -> None:
    assert LlmWorkerSettings.queue_name == settings.workers.llm_queue_name
    assert PublisherWorkerSettings.queue_name == settings.workers.publisher_queue_name
    assert AnalyticsWorkerSettings.queue_name == settings.workers.analytics_queue_name
    assert OutboxWorkerSettings.queue_name == settings.workers.outbox_queue_name


def test_workers_use_namespaced_health_keys() -> None:
    assert LlmWorkerSettings.health_check_key == f"{settings.workers.llm_queue_name}:health"
    assert PublisherWorkerSettings.health_check_key == f"{settings.workers.publisher_queue_name}:health"
    assert AnalyticsWorkerSettings.health_check_key == f"{settings.workers.analytics_queue_name}:health"
    assert OutboxWorkerSettings.health_check_key == f"{settings.workers.outbox_queue_name}:health"
