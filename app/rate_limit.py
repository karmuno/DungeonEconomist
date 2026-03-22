"""Simple in-memory rate limiter for auth endpoints."""

import time
from collections import defaultdict

from fastapi import HTTPException, Request


class RateLimiter:
    """Token-bucket rate limiter keyed by client IP."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def check(self, request: Request) -> None:
        """Raise 429 if the client has exceeded the rate limit."""
        ip = self._client_ip(request)
        now = time.monotonic()
        cutoff = now - self.window_seconds

        # Prune old entries
        self._requests[ip] = [t for t in self._requests[ip] if t > cutoff]

        if len(self._requests[ip]) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail=f"Too many requests. Try again in {self.window_seconds} seconds.",
            )

        self._requests[ip].append(now)


# 10 requests per 60 seconds for auth endpoints
auth_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
