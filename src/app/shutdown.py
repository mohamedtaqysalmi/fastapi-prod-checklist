"""Track in-flight requests so shutdown can wait briefly before dropping them."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from starlette.types import ASGIApp, Receive, Scope, Send


@dataclass
class InFlightTracker:
    count: int = 0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _idle: asyncio.Event = field(default_factory=asyncio.Event)

    def __post_init__(self) -> None:
        self._idle.set()

    async def enter(self) -> None:
        async with self._lock:
            self.count += 1
            self._idle.clear()

    async def leave(self) -> None:
        async with self._lock:
            self.count = max(0, self.count - 1)
            if self.count == 0:
                self._idle.set()

    async def wait_idle(self, timeout: float) -> bool:
        try:
            await asyncio.wait_for(self._idle.wait(), timeout=timeout)
        except TimeoutError:
            return False
        return True


class InFlightMiddleware:
    def __init__(self, app: ASGIApp, *, tracker: InFlightTracker) -> None:
        self.app = app
        self.tracker = tracker

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        await self.tracker.enter()
        try:
            await self.app(scope, receive, send)
        finally:
            await self.tracker.leave()
