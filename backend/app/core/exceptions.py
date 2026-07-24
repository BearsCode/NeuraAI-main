from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from backend.app.observability.logging import get_logger
from backend.app.schemas.errors import ErrorResponse

logger = get_logger(__name__)


class BusinessRuleError(Exception):
    """Domain exception used for user-facing business rule violations."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class AIServiceError(Exception):
    """Domain exception for AI provider errors (used in service/worker layers)."""

    def __init__(self, message: str, status_code: int = 502) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _build_error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: Any = None,
) -> JSONResponse:
    payload = ErrorResponse(
        request_id=getattr(request.state, "request_id", None),
        error_code=code,
        message=message,
        details=details,
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return _build_error_response(
        request=request,
        status_code=exc.status_code,
        code="http_error",
        message=str(exc.detail),
    )


async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return _build_error_response(
        request=request,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="validation_error",
        message="Request validation failed",
        details=exc.errors(),
    )


async def pydantic_validation_exception_handler(
    request: Request,
    exc: ValidationError,
) -> JSONResponse:
    return _build_error_response(
        request=request,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="validation_error",
        message="Payload validation failed",
        details=exc.errors(),
    )


async def business_rule_exception_handler(
    request: Request,
    exc: BusinessRuleError,
) -> JSONResponse:
    return _build_error_response(
        request=request,
        status_code=status.HTTP_400_BAD_REQUEST,
        code="business_rule_error",
        message=exc.message,
    )


async def ai_service_exception_handler(
    request: Request,
    exc: AIServiceError,
) -> JSONResponse:
    logger.exception("ai_service_error", extra={"path": request.url.path})
    return _build_error_response(
        request=request,
        status_code=exc.status_code,
        code="ai_service_error",
        message=exc.message,
    )


async def integrity_exception_handler(
    request: Request,
    exc: IntegrityError,
) -> JSONResponse:
    logger.exception("database_integrity_error", extra={"path": request.url.path})
    return _build_error_response(
        request=request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="database_error",
        message="Database operation failed",
    )


async def database_exception_handler(
    request: Request,
    exc: SQLAlchemyError,
) -> JSONResponse:
    logger.exception("database_error", extra={"path": request.url.path})
    return _build_error_response(
        request=request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="database_error",
        message="Database operation failed",
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.exception("unhandled_exception", extra={"path": request.url.path})
    return _build_error_response(
        request=request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="internal_server_error",
        message="Unexpected server error",
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
    app.add_exception_handler(BusinessRuleError, business_rule_exception_handler)
    app.add_exception_handler(AIServiceError, ai_service_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_exception_handler)
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
