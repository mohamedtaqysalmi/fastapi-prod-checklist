# fastapi-prod-checklist

A FastAPI template where production readiness is enforced by tests, not by a README promise.

**Status: early. The application core exists, the rest of the checklist does not.** Do not use
this as a template yet. Rate limiting, database migrations, graceful shutdown, error reporting
and the Dockerfile are still to be built.

## What the tests enforce today

`tests/test_production_readiness.py` has one test per requirement. Each test checks behaviour
through HTTP or settings, so removing the feature makes the test fail. I checked this by
deleting each feature in turn and confirming the matching test went red.

| Requirement | Enforcing test | Why it matters |
| --- | --- | --- |
| Liveness endpoint `/healthz` that does not touch dependencies | `test_health_endpoint_reports_liveness`, `test_health_endpoint_does_not_depend_on_readiness_checks` | Orchestrators need a cheap probe, and a database outage should not cause restarts. |
| Readiness endpoint `/readyz` with pluggable checks, 503 when one fails, no error text in the body | `test_readiness_endpoint_fails_when_a_dependency_check_fails` | Traffic should only reach instances whose dependencies work. |
| Debug off by default, and rejected in production | `test_debug_is_off_by_default`, `test_debug_is_rejected_in_production` | Debug mode exposes internals. |
| Missing required setting stops startup with a message naming the variable | `test_missing_required_setting_stops_startup_with_a_clear_message` | A bad deploy should fail at boot, not at the first request. |
| Request ID on every response, including errors and CORS preflight; incoming IDs accepted only if they are 1 to 64 characters of `A-Za-z0-9._-` | `test_every_response_carries_a_request_id`, `test_request_id_is_reused_only_when_it_is_sane` | Lets you match a client report to a log line, and keeps client input out of logs. |
| Wildcard CORS origin together with credentials is refused at startup | `test_wildcard_cors_with_credentials_is_refused_at_startup` | Browsers reject the combination, and allowing it by mistake would expose authenticated APIs. |
| CORS allows only configured origins and is off when none are set | `test_cors_only_allows_configured_origins`, `test_cors_is_off_when_no_origin_is_configured` | Default deny. |
| Security headers on every response, including 404 and 500 | `test_security_headers_are_present` | Cheap protection against sniffing, framing and downgrade. HSTS is skipped when `APP_ENVIRONMENT=local`. |
| One error body shape for HTTP errors, validation errors and unhandled exceptions | `test_error_bodies_share_one_shape`, `test_method_not_allowed_uses_the_same_error_shape` | Clients can parse every failure the same way. |
| No stack traces or exception messages to clients, no echoed input in validation errors | `test_unhandled_exception_does_not_leak_details_to_the_client`, `test_validation_errors_do_not_echo_submitted_values` | Error bodies leak internals and submitted secrets otherwise. |
| JSON logs with request ID, no headers or query strings logged, sensitive extra fields redacted | `tests/test_logging.py` | Logs get shipped and read by many people. |

The error body looks like this:

```json
{"error": {"code": "not_found", "message": "Not Found", "request_id": "3f448623b0d34c76863c235cf42c118c"}}
```

Validation errors add a `details` list with `loc`, `msg` and `type` for each problem.

### Known limits

- Unhandled exceptions (500) do not get CORS headers, because the error is turned into a
  response outside the CORS layer. A browser client sees a CORS failure instead of the 500 body.
- Logging redacts by key name. A secret inside a free-text log message is not caught.
- The interactive API docs are switched off, because the strict Content-Security-Policy would
  block them.

### Not built yet

Rate limiting, Alembic migrations, graceful shutdown, Sentry or other error reporting, the
Dockerfile and its non-root user.

## Running it

Configuration comes from `APP_`-prefixed environment variables, see `.env.example`.
`APP_ENVIRONMENT` is required and has no default.

```bash
cp .env.example .env
uvicorn app.main:create_app --factory
```

Use `--no-access-log` if you do not want uvicorn's own access lines next to the app's JSON ones.
Without a request ID header the app generates one per request.

## Development setup

Requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pre-commit install
```

## Running the checks

```bash
ruff check .
ruff format --check .
mypy
pytest
```

## License

MIT, see [LICENSE](LICENSE).
