"""One test per production requirement.

Each test is written against observable behaviour, so it fails if the requirement is removed
from the app and not only if a particular function is renamed. The README links each
requirement to its test.
"""

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
