from collections.abc import Mapping

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app import __version__
from app.config import Settings, load_settings
from app.errors import register_exception_handlers
from app.health import ReadinessCheck
from app.health import router as health_router
from app.lifespan import app_lifespan
from app.logging import configure_logging
from app.middleware import REQUEST_ID_HEADER, RequestContextMiddleware, SecurityHeadersMiddleware
from app.rate_limit import RateLimitMiddleware
from app.shutdown import InFlightMiddleware, InFlightTracker


def create_app(
    settings: Settings | None = None,
    readiness_checks: Mapping[str, ReadinessCheck] | None = None,
) -> FastAPI:
    """Build the app. Run it with `uvicorn app.main:create_app --factory`."""
    settings = settings or load_settings()
    configure_logging(settings.log_level)

    tracker = InFlightTracker()
    app = FastAPI(
        title="fastapi-prod-checklist",
        version=__version__,
        debug=settings.debug,
        docs_url=None,
        redoc_url=None,
        lifespan=app_lifespan,
    )
    app.state.settings = settings
    app.state.readiness_checks = dict(readiness_checks or {})
    app.state.in_flight = tracker

    register_exception_handlers(app)
    app.include_router(health_router)

    # Last added = outermost. Request-context and security headers must wrap the
    # rate limiter so 429 responses still get a request ID and headers. In-flight
    # tracking wraps everything so shutdown can wait on open requests.
    if settings.cors_allow_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_allow_origins,
            allow_credentials=settings.cors_allow_credentials,
            allow_methods=settings.cors_allow_methods,
            allow_headers=["Authorization", "Content-Type", REQUEST_ID_HEADER],
            expose_headers=[REQUEST_ID_HEADER],
        )
    app.add_middleware(
        RateLimitMiddleware,
        requests=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
        enabled=settings.rate_limit_enabled,
    )
    # Security headers must wrap request-context so 500s built there still get headers.
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(SecurityHeadersMiddleware, hsts=settings.environment != "local")
    app.add_middleware(InFlightMiddleware, tracker=tracker)
    return app
