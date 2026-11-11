import os
from collections.abc import Callable

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import Settings
from app.health import ReadinessCheck
from app.main import create_app

AppFactory = Callable[..., FastAPI]


@pytest.fixture(autouse=True)
def _clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    # A developer's shell or .env must not change what the tests see.
    for name in list(os.environ):
        if name.startswith("APP_"):
            monkeypatch.delenv(name)


def make_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {"environment": "production"}
    values.update(overrides)
    return Settings(_env_file=None, **values)  # type: ignore[call-arg, arg-type]


@pytest.fixture
def settings() -> Settings:
    return make_settings()


@pytest.fixture
def app_factory() -> AppFactory:
    def build(
        readiness_checks: dict[str, ReadinessCheck] | None = None, **settings_overrides: object
    ) -> FastAPI:
        app = create_app(make_settings(**settings_overrides), readiness_checks)

        @app.get("/boom")
        async def boom() -> None:
            raise RuntimeError("secret-internal-detail")

        @app.get("/items/{item_id}")
        async def item(item_id: int) -> dict[str, int]:
            return {"item_id": item_id}

        return app

    return build


@pytest.fixture
def client(app_factory: AppFactory) -> TestClient:
    return TestClient(app_factory(), raise_server_exceptions=False)
