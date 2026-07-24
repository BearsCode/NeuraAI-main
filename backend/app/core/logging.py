from __future__ import annotations

import contextvars
import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id",
    default="-",
)


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get("-")
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }

        extra_keys = {
            key: value
            for key, value in record.__dict__.items()
            if key
            not in {
                "args",
                "created",
                "exc_info",
                "exc_text",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "msg",
                "name",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "thread",
                "threadName",
                "request_id",
            }
        }
        payload.update(extra_keys)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=True, default=str)


def configure_logging(level: str) -> None:
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(RequestContextFilter())

    root_logger.addHandler(handler)
    root_logger.setLevel(level.upper())

    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.error").handlers.clear()


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
