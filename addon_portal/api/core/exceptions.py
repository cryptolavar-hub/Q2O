"""Custom exceptions and handlers for the licensing API."""

from __future__ import annotations

from http import HTTPStatus
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .logging import get_logger

LOGGER = get_logger(__name__)


class BusinessLogicError(Exception):
    """Base class for domain-specific errors raised by the licensing API."""

    status_code: HTTPStatus = HTTPStatus.BAD_REQUEST
    error_code: str = "business_logic_error"

    def __init__(self, message: str, *, detail: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail or {}


class TenantNotFoundError(BusinessLogicError):
    """Raised when a tenant record cannot be located."""

    status_code = HTTPStatus.NOT_FOUND
    error_code = "tenant_not_found"


class TenantConflictError(BusinessLogicError):
    """Raised when attempting to create or update a tenant that conflicts with existing data."""

    status_code = HTTPStatus.CONFLICT
    error_code = "tenant_conflict"


class PlanNotFoundError(BusinessLogicError):
    """Raised when a requested subscription plan is missing."""

    status_code = HTTPStatus.BAD_REQUEST
    error_code = "plan_not_found"


class InvalidOperationError(BusinessLogicError):
    """Raised when a requested state change violates business rules."""

    status_code = HTTPStatus.BAD_REQUEST
    error_code = "invalid_operation"


class ConfigurationError(BusinessLogicError):
    """Raised for invalid or inconsistent configuration changes."""

    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    error_code = "configuration_error"


def _build_error_payload(exc: BusinessLogicError) -> Dict[str, Any]:
    return {
        "errorCode": exc.error_code,
        "message": exc.message,
        "detail": exc.detail,
    }


def register_exception_handlers(app: FastAPI) -> None:
    """Register FastAPI exception handlers for domain errors.

    Args:
        app: The FastAPI application instance.
    """

    @app.exception_handler(BusinessLogicError)
    async def _handle_business_error(request: Request, exc: BusinessLogicError) -> JSONResponse:
        # Skip OPTIONS requests - let CORS middleware handle them
        if request.method == "OPTIONS":
            LOGGER.info(f"Skipping BusinessLogicError for OPTIONS request to {request.url.path}")
            from starlette.responses import Response
            return Response(status_code=200)
        LOGGER.error("business_logic_error", extra={"error": _build_error_payload(exc)})
        return JSONResponse(status_code=int(exc.status_code), content=_build_error_payload(exc))

    @app.exception_handler(Exception)
    async def _handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        # Skip OPTIONS requests - let CORS middleware handle them
        if request.method == "OPTIONS":
            LOGGER.info(f"Skipping Exception for OPTIONS request to {request.url.path}: {type(exc).__name__}: {str(exc)}")
            from starlette.responses import Response
            return Response(status_code=200)
        LOGGER.error("unexpected_error", extra={"exception": str(exc), "path": request.url.path, "method": request.method})
        return JSONResponse(
            status_code=int(HTTPStatus.INTERNAL_SERVER_ERROR),
            content={
                "errorCode": "internal_server_error",
                "message": "An unexpected error occurred while processing the request.",
            },
        )
