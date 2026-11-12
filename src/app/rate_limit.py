"""In-process fixed-window rate limiter.

Good enough for a single-process template. Behind multiple workers you need a
shared store; the readiness test still fails if this middleware is removed.
"""

from __future__ import annotations

import math
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
        trusted_proxy_hops: int = 0,
    ) -> None:
        self.app = app
        self.requests = requests
        self.window_seconds = window_seconds
        self.enabled = enabled
        self.trusted_proxy_hops = trusted_proxy_hops
        self._last_sweep = time.monotonic()
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _client_key(self, scope: Scope) -> str:
        if self.trusted_proxy_hops:
            forwarded = Headers(scope=scope).get("x-forwarded-for")
            if forwarded:
                hops = [hop.strip() for hop in forwarded.split(",")]
                # Each trusted proxy appends the address it saw, so the entry that counts is
                # counted from the right. Anything further left is client-controlled.
                if len(hops) >= self.trusted_proxy_hops:
                    return hops[-self.trusted_proxy_hops][:64]
        client = scope.get("client")
        if client and client[0]:
            return str(client[0])
        return "unknown"

    def _sweep(self, now: float) -> None:
        # Buckets for clients that went quiet would otherwise stay in memory forever.
        cutoff = now - self.window_seconds
        for key in [k for k, hits in self._hits.items() if not hits or hits[-1] < cutoff]:
            del self._hits[key]
        self._last_sweep = now

    def _allow(self, key: str) -> float | None:
        """Return None when the request is allowed, else the seconds until a slot frees up."""
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            if now - self._last_sweep >= self.window_seconds:
                self._sweep(now)
            bucket = self._hits[key]
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= self.requests:
                return max(0.0, bucket[0] + self.window_seconds - now)
            bucket.append(now)
            return None

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not self.enabled:
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        # Probes must stay cheap and never trip the limiter.
        if path in {"/healthz", "/readyz"}:
            await self.app(scope, receive, send)
            return

        retry_after = self._allow(self._client_key(scope))
        if retry_after is None:
            await self.app(scope, receive, send)
            return

        response = error_response(
            429,
            "too_many_requests",
            "Rate limit exceeded",
            headers={"Retry-After": str(max(1, math.ceil(retry_after)))},
        )
        await response(scope, receive, send)
