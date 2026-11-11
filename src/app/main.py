from collections.abc import Mapping

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app import __version__
from app.config import Settings, load_settings
from app.errors import register_exception_handlers
from app.health import ReadinessCheck
from app.health import router as health_router
from app.logging import configure_logging
from app.middleware import REQUEST_ID_HEADER, RequestContextMiddleware, SecurityHeadersMiddleware


def create_app(
    settings: Settings | None = None,
    readiness_checks: Mapping[str, ReadinessCheck] | None = None,
) -> FastAPI:
    """Build the app. Run it with `uvicorn app.main:create_app --factory`."""
    settings = settings or load_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="fastapi-prod-checklist",
        version=__version__,
        debug=settings.debug,
        docs_url=None,
        redoc_url=None,
    )
    app.state.settings = settings
    app.state.readiness_checks = dict(readiness_checks or {})

    register_exception_handlers(app)
    app.include_router(health_router)

    # The last middleware added is the outermost. The request-context layer has to wrap
    # CORS so that preflight responses also carry a request ID.
    if settings.cors_allow_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_allow_origins,
            allow_credentials=settings.cors_allow_credentials,
            allow_methods=settings.cors_allow_methods,
            allow_headers=["Authorization", "Content-Type", REQUEST_ID_HEADER],
            expose_headers=[REQUEST_ID_HEADER],
        )
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(SecurityHeadersMiddleware, hsts=settings.environment != "local")
    return app
