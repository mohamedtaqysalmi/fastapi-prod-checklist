import asyncio
import logging
from collections.abc import Awaitable, Callable, Mapping

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# A check returns normally when its dependency is usable and raises when it is not.
ReadinessCheck = Callable[[], Awaitable[None]]

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def liveness() -> dict[str, str]:
    # Liveness must not touch dependencies: a database outage should not get the pod restarted.
    return {"status": "ok"}


async def _run_check(name: str, check: ReadinessCheck, timeout: float) -> bool:
    try:
        await asyncio.wait_for(check(), timeout=timeout)
    except Exception:
        logger.warning("readiness check failed", extra={"check": name}, exc_info=True)
        return False
    return True


@router.get("/readyz")
async def readiness(request: Request) -> JSONResponse:
    checks: Mapping[str, ReadinessCheck] = request.app.state.readiness_checks
    timeout: float = request.app.state.settings.readiness_timeout_seconds
    outcomes = await asyncio.gather(*(_run_check(n, c, timeout) for n, c in checks.items()))
    results = dict(zip(checks, outcomes, strict=True))
    ready = all(results.values())
    body = {
        "status": "ok" if ready else "unavailable",
        "checks": {name: "ok" if ok else "failed" for name, ok in results.items()},
    }
    return JSONResponse(body, status_code=200 if ready else 503)
