"""Rate limiting middleware using in-memory token bucket algorithm."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Awaitable, Callable, Dict, Tuple

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from configs.settings import get_settings

settings = get_settings()


class RateLimiter(BaseHTTPMiddleware):
    """In-memory rate limiter based on client host IP address."""

    def __init__(self, app: any) -> None:
        super().__init__(app)
        self._limit = settings.rate_limit.requests
        self._window = settings.rate_limit.window_seconds
        # Maps host_ip -> (tokens_left, last_updated_time)
        self._buckets: Dict[str, Tuple[float, float]] = defaultdict(
            lambda: (float(self._limit), time.time())
        )

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        client_ip = request.client.host if request.client else "unknown"

        # Rate limiting override for testing or health checks
        if request.url.path.endswith("/health"):
            return await call_next(request)

        now = time.time()
        tokens, last_update = self._buckets[client_ip]

        # Calculate time elapsed and refill bucket
        elapsed = now - last_update
        refill_amount = elapsed * (self._limit / self._window)
        new_tokens = min(float(self._limit), tokens + refill_amount)

        # Check if client has tokens remaining
        if new_tokens < 1.0:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {
                        "type": "RateLimitExceeded",
                        "message": "Too many requests. Please try again later.",
                        "details": {"retry_after_seconds": int(self._window - elapsed)},
                    },
                },
            )

        # Consume token and update bucket
        self._buckets[client_ip] = (new_tokens - 1.0, now)

        return await call_next(request)
