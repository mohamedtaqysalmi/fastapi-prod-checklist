import io
import json
import logging
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.logging import REDACTED, JsonFormatter, redact, request_id_var
from conftest import AppFactory


@pytest.fixture
def log_stream() -> Iterator[io.StringIO]:
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.addHandler(handler)
    previous = root.level
    root.setLevel(logging.INFO)
    yield stream
    root.removeHandler(handler)
    root.setLevel(previous)


def lines(stream: io.StringIO) -> list[dict[str, object]]:
    return [json.loads(line) for line in stream.getvalue().splitlines() if line]


def test_formatter_emits_json_with_request_id() -> None:
    token = request_id_var.set("req-1")
    try:
        record = logging.LogRecord("x", logging.INFO, __file__, 1, "hello %s", ("world",), None)
        payload = json.loads(JsonFormatter().format(record))
    finally:
        request_id_var.reset(token)
    assert payload["message"] == "hello world"
    assert payload["level"] == "INFO"
    assert payload["request_id"] == "req-1"


def test_formatter_redacts_sensitive_extra_fields() -> None:
    record = logging.LogRecord("x", logging.INFO, __file__, 1, "login", None, None)
    record.password = "hunter2"
    record.payload = {"api_key": "abc", "name": "visible"}
    output = JsonFormatter().format(record)
    assert "hunter2" not in output
    assert "abc" not in output
    assert json.loads(output)["payload"] == {"api_key": REDACTED, "name": "visible"}


def test_redact_handles_nested_lists() -> None:
    assert redact([{"token": "t"}, 1]) == [{"token": REDACTED}, 1]


def test_each_request_logs_one_line_with_its_request_id(
    app_factory: AppFactory, log_stream: io.StringIO
) -> None:
    client = TestClient(app_factory(), raise_server_exceptions=False)
    client.get("/healthz", headers={"X-Request-ID": "trace-42"})
    entries = [e for e in lines(log_stream) if e["message"] == "request completed"]
    assert len(entries) == 1
    assert entries[0]["request_id"] == "trace-42"
    assert entries[0]["path"] == "/healthz"
    assert entries[0]["status"] == 200


def test_request_headers_and_query_strings_are_not_logged(
    app_factory: AppFactory, log_stream: io.StringIO
) -> None:
    client = TestClient(app_factory(), raise_server_exceptions=False)
    client.get(
        "/healthz?token=query-secret",
        headers={"Authorization": "Bearer header-secret", "Cookie": "sid=cookie-secret"},
    )
    # The test client logs its own request line, including the URL; only the app's lines count.
    app_lines = [line for line in log_stream.getvalue().splitlines() if '"logger": "app.' in line]
    assert app_lines
    output = " ".join(app_lines)
    for secret in ("query-secret", "header-secret", "cookie-secret"):
        assert secret not in output


def test_unhandled_exception_is_logged_server_side(
    app_factory: AppFactory, log_stream: io.StringIO
) -> None:
    client = TestClient(app_factory(), raise_server_exceptions=False)
    client.get("/boom")
    entries = lines(log_stream)
    failure = next(e for e in entries if e["message"] == "unhandled exception")
    assert "RuntimeError" in str(failure["exception"])
    completed = next(e for e in entries if e["message"] == "request completed")
    assert completed["status"] == 500
