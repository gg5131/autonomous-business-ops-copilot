"""Tracing middleware generating unique trace / correlation IDs per API call."""

from __future__ import annotations

import uuid
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.observability.logging import trace_id_var


class TracingMiddleware(BaseHTTPMiddleware):
    """Middleware extracting or generating X-Trace-ID correlation headers."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Check for client-supplied correlation headers
        trace_id = request.headers.get("X-Trace-ID") or request.headers.get("X-Request-ID")
        if not trace_id:
            trace_id = str(uuid.uuid4())

        # Bind to ContextVar for duration of thread execution
        token = trace_id_var.set(trace_id)

        try:
            response = await call_next(request)
        finally:
            # Revert context variable state
            trace_id_var.reset(token)

        # Attach correlation ID to response headers
        response.headers["X-Trace-ID"] = trace_id
        return response
