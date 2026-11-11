import pytest
from pydantic import ValidationError

from app.config import ConfigurationError, load_settings
from conftest import make_settings


def test_load_settings_reads_prefixed_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENVIRONMENT", "staging")
    monkeypatch.setenv("APP_LOG_LEVEL", "DEBUG")
    settings = load_settings()
    assert settings.environment == "staging"
    assert settings.log_level == "DEBUG"


def test_load_settings_reports_invalid_values_by_variable_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENVIRONMENT", "prod")
    with pytest.raises(ConfigurationError, match="APP_ENVIRONMENT"):
        load_settings()


def test_origins_accept_comma_separated_and_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENVIRONMENT", "local")
    monkeypatch.setenv("APP_CORS_ALLOW_ORIGINS", "https://a.example.com, https://b.example.com")
    assert load_settings().cors_allow_origins == ["https://a.example.com", "https://b.example.com"]
    monkeypatch.setenv("APP_CORS_ALLOW_ORIGINS", '["https://c.example.com"]')
    assert load_settings().cors_allow_origins == ["https://c.example.com"]
    monkeypatch.setenv("APP_CORS_ALLOW_ORIGINS", "")
    assert load_settings().cors_allow_origins == []


def test_readiness_timeout_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        make_settings(readiness_timeout_seconds=0)


def test_debug_is_allowed_outside_production() -> None:
    assert make_settings(environment="local", debug=True).debug is True


def test_hsts_is_not_sent_in_local_environment() -> None:
    from fastapi.testclient import TestClient

    from app.main import create_app

    client = TestClient(create_app(make_settings(environment="local")))
    assert "strict-transport-security" not in client.get("/healthz").headers
