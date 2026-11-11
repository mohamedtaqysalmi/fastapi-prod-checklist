"""One test per production requirement.

Each test is written against observable behaviour, so it fails if the requirement is removed
from the app and not only if a particular function is renamed. The README links each
requirement to its test.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import ConfigurationError, load_settings
from conftest import AppFactory, make_settings

ERROR_KEYS = {"code", "message", "request_id"}


def test_health_endpoint_reports_liveness(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_endpoint_does_not_depend_on_readiness_checks(app_factory: AppFactory) -> None:
    async def down() -> None:
        raise ConnectionError("database is down")

    client = TestClient(app_factory({"database": down}))
    assert client.get("/healthz").status_code == 200


def test_readiness_endpoint_fails_when_a_dependency_check_fails(app_factory: AppFactory) -> None:
    async def up() -> None:
        return None

    async def down() -> None:
        raise ConnectionError("database is down")

    healthy = TestClient(app_factory({"cache": up}))
    assert healthy.get("/readyz").status_code == 200

    unhealthy = TestClient(app_factory({"cache": up, "database": down}))
    response = unhealthy.get("/readyz")
    assert response.status_code == 503
    assert response.json()["checks"] == {"cache": "ok", "database": "failed"}
    assert "database is down" not in response.text


def test_debug_is_off_by_default(app_factory: AppFactory) -> None:
    assert make_settings().debug is False
    assert app_factory().debug is False


def test_debug_is_rejected_in_production() -> None:
    with pytest.raises(ValidationError, match="debug must be off"):
        make_settings(environment="production", debug=True)


def test_missing_required_setting_stops_startup_with_a_clear_message() -> None:
    with pytest.raises(ConfigurationError, match="APP_ENVIRONMENT: required but not set"):
        load_settings()


@pytest.mark.parametrize(
    ("method", "path", "headers"),
    [
        ("get", "/healthz", {}),
        ("get", "/missing", {}),
        ("get", "/items/not-a-number", {}),
        ("get", "/boom", {}),
        ("post", "/healthz", {}),
        (
            "options",
            "/healthz",
            {"Origin": "https://app.example.com", "Access-Control-Request-Method": "GET"},
        ),
    ],
)
def test_every_response_carries_a_request_id(
    app_factory: AppFactory, method: str, path: str, headers: dict[str, str]
) -> None:
    app = app_factory(cors_allow_origins=["https://app.example.com"])
    client = TestClient(app, raise_server_exceptions=False)
    response = client.request(method, path, headers=headers)
    assert response.headers.get("x-request-id")


def test_request_id_is_reused_only_when_it_is_sane(client: TestClient) -> None:
    assert (
        client.get("/healthz", headers={"X-Request-ID": "abc-123.DEF_4"}).headers["x-request-id"]
        == "abc-123.DEF_4"
    )

    for bad in ["has space", "new\tline", "x" * 65, "<script>"]:
        returned = client.get("/healthz", headers={"X-Request-ID": bad}).headers["x-request-id"]
        assert returned != bad
        assert len(returned) == 32


def test_wildcard_cors_with_credentials_is_refused_at_startup() -> None:
    with pytest.raises(ValidationError, match="must not contain '\\*'"):
        make_settings(cors_allow_origins=["*"], cors_allow_credentials=True)


def test_cors_only_allows_configured_origins(app_factory: AppFactory) -> None:
    client = TestClient(app_factory(cors_allow_origins=["https://app.example.com"]))
    allowed = client.get("/healthz", headers={"Origin": "https://app.example.com"})
    assert allowed.headers["access-control-allow-origin"] == "https://app.example.com"
    other = client.get("/healthz", headers={"Origin": "https://evil.example.net"})
    assert "access-control-allow-origin" not in other.headers


def test_cors_is_off_when_no_origin_is_configured(client: TestClient) -> None:
    response = client.get("/healthz", headers={"Origin": "https://app.example.com"})
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize("path", ["/healthz", "/missing", "/boom"])
def test_security_headers_are_present(client: TestClient, path: str) -> None:
    headers = client.get(path).headers
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert headers["referrer-policy"] == "no-referrer"
    assert "frame-ancestors 'none'" in headers["content-security-policy"]
    assert "max-age=" in headers["strict-transport-security"]


@pytest.mark.parametrize(
    ("path", "status", "code"),
    [
        ("/missing", 404, "not_found"),
        ("/items/not-a-number", 422, "validation_error"),
        ("/boom", 500, "internal_server_error"),
    ],
)
def test_error_bodies_share_one_shape(
    client: TestClient, path: str, status: int, code: str
) -> None:
    response = client.get(path)
    assert response.status_code == status
    error = response.json()["error"]
    assert set(error) >= ERROR_KEYS
    assert error["code"] == code
    assert error["request_id"] == response.headers["x-request-id"]


def test_method_not_allowed_uses_the_same_error_shape(client: TestClient) -> None:
    response = client.post("/healthz")
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "method_not_allowed"
    assert response.headers["allow"]


def test_unhandled_exception_does_not_leak_details_to_the_client(client: TestClient) -> None:
    response = client.get("/boom")
    assert response.status_code == 500
    assert "secret-internal-detail" not in response.text
    assert "Traceback" not in response.text
    assert response.json()["error"]["message"] == "Internal server error"


def test_validation_errors_do_not_echo_submitted_values(client: TestClient) -> None:
    response = client.get("/items/hunter2")
    assert response.status_code == 422
    assert "hunter2" not in response.text
    assert response.json()["error"]["details"][0]["loc"] == ["path", "item_id"]


def test_rate_limit_returns_429_with_the_shared_error_shape(app_factory: AppFactory) -> None:
    client = TestClient(
        app_factory(rate_limit_enabled=True, rate_limit_requests=2, rate_limit_window_seconds=60),
        raise_server_exceptions=False,
    )
    assert client.get("/items/1").status_code == 200
    assert client.get("/items/2").status_code == 200
    limited = client.get("/items/3")
    assert limited.status_code == 429
    error = limited.json()["error"]
    assert error["code"] == "too_many_requests"
    assert error["request_id"] == limited.headers["x-request-id"]
    assert limited.headers.get("retry-after")
    # Liveness stays reachable when the limiter is tripped.
    assert client.get("/healthz").status_code == 200


def test_rate_limiting_is_enabled_by_default() -> None:
    from app.config import Settings

    settings = Settings(_env_file=None, environment="production")  # type: ignore[call-arg]
    assert settings.rate_limit_enabled is True
    assert settings.rate_limit_requests >= 1
    assert settings.rate_limit_window_seconds > 0


def test_sentry_stays_off_without_a_dsn(app_factory: AppFactory) -> None:
    from app.sentry import init_sentry, sentry_is_initialized

    settings = make_settings(sentry_dsn="")
    assert init_sentry(settings) is False
    assert sentry_is_initialized() is False
    # Booting the app must not require Sentry.
    with TestClient(app_factory(sentry_dsn="")) as client:
        assert client.get("/healthz").status_code == 200
    assert sentry_is_initialized() is False


def test_sentry_hook_initializes_when_dsn_is_set(monkeypatch: pytest.MonkeyPatch) -> None:
    import sys
    import types

    from app import sentry

    calls: list[dict[str, object]] = []

    def fake_init(**kwargs: object) -> None:
        calls.append(kwargs)

    fake = types.ModuleType("sentry_sdk")
    fake.init = fake_init  # type: ignore[attr-defined]
    integrations = types.ModuleType("sentry_sdk.integrations")
    fastapi_mod = types.ModuleType("sentry_sdk.integrations.fastapi")
    starlette_mod = types.ModuleType("sentry_sdk.integrations.starlette")

    class FastApiIntegration:
        def __init__(self, **kwargs: object) -> None:
            self.kwargs = kwargs

    class StarletteIntegration:
        def __init__(self, **kwargs: object) -> None:
            self.kwargs = kwargs

    fastapi_mod.FastApiIntegration = FastApiIntegration  # type: ignore[attr-defined]
    starlette_mod.StarletteIntegration = StarletteIntegration  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "sentry_sdk", fake)
    monkeypatch.setitem(sys.modules, "sentry_sdk.integrations", integrations)
    monkeypatch.setitem(sys.modules, "sentry_sdk.integrations.fastapi", fastapi_mod)
    monkeypatch.setitem(sys.modules, "sentry_sdk.integrations.starlette", starlette_mod)

    assert sentry.init_sentry(make_settings(sentry_dsn="https://public@example.com/1")) is True
    assert sentry.sentry_is_initialized() is True
    assert calls and calls[0]["dsn"] == "https://public@example.com/1"
    assert calls[0]["send_default_pii"] is False


def test_graceful_shutdown_disposes_the_database_engine(
    app_factory: AppFactory, tmp_path: Path
) -> None:
    from app.db import get_engine

    db_path = tmp_path / "shutdown.db"
    url = f"sqlite+aiosqlite:///{db_path.as_posix()}"
    app = app_factory(database_url=url, database_ready_check=True)
    with TestClient(app) as client:
        assert client.get("/readyz").status_code == 200
        assert get_engine() is not None
    assert get_engine() is None


def test_alembic_migration_files_exist_and_upgrade_runs(tmp_path: Path) -> None:
    from alembic.command import upgrade
    from alembic.config import Config

    root = Path(__file__).resolve().parents[1]
    assert (root / "alembic.ini").is_file()
    assert (root / "alembic" / "env.py").is_file()
    versions = list((root / "alembic" / "versions").glob("*.py"))
    assert versions, "expected at least one Alembic revision"

    db_file = tmp_path / "alembic.db"
    cfg = Config(str(root / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_file.as_posix()}")
    upgrade(cfg, "head")
    assert db_file.exists()


def test_dockerfile_is_multistage_and_runs_as_non_root() -> None:
    from pathlib import Path

    dockerfile = (Path(__file__).resolve().parents[1] / "Dockerfile").read_text(encoding="utf-8")
    from_lines = [
        line.strip() for line in dockerfile.splitlines() if line.strip().upper().startswith("FROM ")
    ]
    assert len(from_lines) >= 2, "Dockerfile must be multi-stage"

    user_lines = [
        line.strip() for line in dockerfile.splitlines() if line.strip().upper().startswith("USER ")
    ]
    assert user_lines, "Dockerfile must set USER"
    last_user = user_lines[-1].split(None, 1)[1]
    assert last_user not in {"root", "0", "0:0"}, "final stage must not run as root"
    assert "10001" in last_user or last_user == "app"
