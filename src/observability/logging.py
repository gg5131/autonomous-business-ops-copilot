"""Logging subsystem initialization, structuring console and JSON-formatted logging."""

from __future__ import annotations

import logging
import logging.config
import os
from typing import Any

import structlog
from structlog.types import EventDict, WrappedLogger

from configs.settings import get_settings

# Context variable for trace ID
from contextvars import ContextVar

trace_id_var: ContextVar[str | None] = ContextVar("trace_id", default=None)


def add_trace_id(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Processor to inject trace_id from ContextVar into structlog logs."""
    trace_id = trace_id_var.get()
    if trace_id:
        event_dict["trace_id"] = trace_id
    return event_dict


def setup_logging() -> None:
    """Configures structured logs using structlog and standard logging."""
    settings = get_settings()
    log_level_str = settings.app_log_level.upper()
    numeric_level = getattr(logging, log_level_str, logging.INFO)

    # Ensure logs folder exists
    project_root = settings.project_root
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)

    # Base logging processors
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        add_trace_id,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Check env to switch formatting (JSON for production, Console for development)
    if settings.is_production:
        formatter_processor = structlog.processors.JSONRenderer()
    else:
        formatter_processor = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=shared_processors + [formatter_processor],
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        cache_logger_on_first_use=True,
    )

    # Capture standard library logging
    logging.basicConfig(
        level=numeric_level,
        format="%(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(str(log_dir / "copilot.log"), encoding="utf-8"),
        ],
    )

    # Route standard logs to structlog where possible
    logging.getLogger("uvicorn.error").setLevel(numeric_level)
    logging.getLogger("uvicorn.access").setLevel(numeric_level)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a structlog-compatible bound logger."""
    return structlog.get_logger(name)  # type: ignore
