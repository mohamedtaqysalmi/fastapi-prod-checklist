"""Startup and graceful shutdown for the app factory."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import configure_database, dispose_engine, ping_database
from app.sentry import init_sentry
from app.shutdown import InFlightTracker

logger = logging.getLogger(__name__)


@asynccontextmanager
async def app_lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = app.state.settings
    tracker: InFlightTracker = app.state.in_flight
    init_sentry(settings)

    if settings.database_url:
        configure_database(settings.database_url)
        if settings.database_ready_check:
            app.state.readiness_checks["database"] = ping_database

    logger.info("application started", extra={"environment": settings.environment})
    try:
        yield
    finally:
        logger.info(
            "shutdown began",
            extra={
                "in_flight": tracker.count,
                "grace_seconds": settings.shutdown_grace_seconds,
            },
        )
        drained = await tracker.wait_idle(settings.shutdown_grace_seconds)
        if not drained:
            logger.warning(
                "shutdown grace elapsed with requests still in flight",
                extra={"in_flight": tracker.count},
            )
        await dispose_engine()
        logger.info("application stopped")
