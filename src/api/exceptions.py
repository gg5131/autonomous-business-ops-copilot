"""Custom exceptions and global FastAPI exception handler mappings."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.observability.logging import get_logger

logger = get_logger(__name__)


class CopilotError(Exception):
    """Base exception for all system-related errors."""

    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(CopilotError):
    """Exception raised when system configurations are invalid."""


class DatabaseError(CopilotError):
    """Exception raised during database operations."""


class SecurityError(CopilotError):
    """Exception raised when security validation or checks fail."""


class PIIValidationError(SecurityError):
    """Exception raised when PII data leakage is detected."""


class AuthenticationError(SecurityError):
    """Exception raised when authentication fails."""


class AuthorizationError(SecurityError):
    """Exception raised when permissions are insufficient."""


async def copilot_exception_handler(request: Request, exc: CopilotError) -> JSONResponse:
    """FastAPI global exception handler for CopilotError exceptions."""
    status_code = 400
    if isinstance(exc, AuthenticationError):
        status_code = 401
    elif isinstance(exc, AuthorizationError):
        status_code = 403
    elif isinstance(exc, ConfigurationError):
        status_code = 500
    elif isinstance(exc, DatabaseError):
        status_code = 500

    logger.error(
        "Application error encountered",
        exception=exc.__class__.__name__,
        message=exc.message,
        details=exc.details,
    )

    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "type": exc.__class__.__name__,
                "message": exc.message,
                "details": exc.details,
            },
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """FastAPI global exception handler for request parameter schema errors."""
    logger.warn(
        "Request validation error",
        errors=exc.errors(),
    )
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "type": "ValidationError",
                "message": "Input validation failed",
                "details": exc.errors(),
            },
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """FastAPI global exception handler for unhandled python errors (fallback)."""
    logger.exception(
        "Unhandled system exception",
        error=str(exc),
    )
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "type": "InternalServerError",
                "message": "An unexpected error occurred. Please contact administrator.",
                "details": {},
            },
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Registers all global exception handlers into FastAPI app instance."""
    app.add_exception_handler(CopilotError, copilot_exception_handler)  # type: ignore
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore
    app.add_exception_handler(Exception, generic_exception_handler)
