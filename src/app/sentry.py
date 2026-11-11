"""Optional Sentry wiring. Stays completely inert unless a DSN is configured."""

from __future__ import annotations

import logging
from typing import Any

from app.config import Settings

logger = logging.getLogger(__name__)

_initialized = False


def sentry_is_initialized() -> bool:
    return _initialized


def reset_sentry_state_for_tests() -> None:
    global _initialized
    _initialized = False


def init_sentry(settings: Settings) -> bool:
    """Initialise Sentry when a DSN is set. Returns True only when init ran."""
    global _initialized
    if not settings.sentry_dsn:
        logger.debug("sentry disabled: no APP_SENTRY_DSN")
        _initialized = False
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
    except ImportError:
        logger.warning(
            "APP_SENTRY_DSN is set but sentry-sdk is not installed; error reporting stays off"
        )
        _initialized = False
        return False

    options: dict[str, Any] = {
        "dsn": settings.sentry_dsn,
        "environment": settings.environment,
        "traces_sample_rate": settings.sentry_traces_sample_rate,
        "send_default_pii": False,
        "integrations": [
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
        ],
    }
    sentry_sdk.init(**options)
    _initialized = True
    logger.info("sentry initialised", extra={"environment": settings.environment})
    return True
