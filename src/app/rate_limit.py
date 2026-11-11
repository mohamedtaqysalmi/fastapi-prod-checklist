"""In-process fixed-window rate limiter.

Good enough for a single-process template. Behind multiple workers you need a
shared store; the readiness test still fails if this middleware is removed.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from starlette.datastructures import Headers
from starlette.types import ASGIApp, Receive, Scope, Send

from app.errors import error_response


class RateLimitMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        requests: int,
        window_seconds: float,
        enabled: bool = True,
    ) -> None:
        self.app = app
        self.requests = requests
        self.window_seconds = window_seconds
        self.enabled = enabled
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _client_key(self, scope: Scope) -> str:
        headers = Headers(scope=scope)
        forwarded = headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",", 1)[0].strip()
        client = scope.get("client")
        if client and client[0]:
            return str(client[0])
        return "unknown"

    def _allow(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            bucket = self._hits[key]
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= self.requests:
                return False
            bucket.append(now)
            return True

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not self.enabled:
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        # Probes must stay cheap and never trip the limiter.
        if path in {"/healthz", "/readyz"}:
            await self.app(scope, receive, send)
            return

        if self._allow(self._client_key(scope)):
            await self.app(scope, receive, send)
            return

        response = error_response(
            429,
            "too_many_requests",
            "Rate limit exceeded",
            headers={"Retry-After": str(int(self.window_seconds))},
        )
        await response(scope, receive, send)
