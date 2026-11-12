import time

from app.rate_limit import RateLimitMiddleware


async def _noop_app(scope: object, receive: object, send: object) -> None:
    return None


def make_limiter(window: float = 0.05) -> RateLimitMiddleware:
    return RateLimitMiddleware(_noop_app, requests=1, window_seconds=window)


def test_idle_clients_are_evicted_so_memory_does_not_grow_without_bound() -> None:
    limiter = make_limiter()
    for i in range(500):
        assert limiter._allow(f"client-{i}") is None
    assert len(limiter._hits) == 500
    time.sleep(0.1)
    limiter._allow("fresh")
    assert set(limiter._hits) == {"fresh"}


def test_blocked_request_reports_time_until_a_slot_frees() -> None:
    limiter = make_limiter(window=30)
    assert limiter._allow("a") is None
    wait = limiter._allow("a")
    assert wait is not None
    assert 0 < wait <= 30
