from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

from backend.app.core.configs import settings


def configure_logging() -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.processors.JSONRenderer() if settings.observability.log_json else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        level=getattr(logging, settings.observability.log_level.upper(), logging.INFO),
        stream=sys.stdout,
        format="%(message)s",
    )


def get_logger(name: str):
    return structlog.get_logger(name)
