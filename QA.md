# QA

Last prepared: 2026-11-11. Environment for the next manual run: Python 3.11+, clean clone on Windows or Linux, Docker optional.

## Test strategy

| Layer | What | Why |
| --- | --- | --- |
| Unit | Config validators, JSON log redaction | Fast feedback on pure logic |
| Behaviour / readiness | `tests/test_production_readiness.py` | Fails if a production requirement is removed |
| Integration-ish | Alembic `upgrade head` against temp SQLite; lifespan dispose | Proves migrations and shutdown wiring |
| Static | ruff, mypy (strict), Dockerfile structural asserts | Catch drift before runtime |
| Manual | Checklist below | Things CI cannot see (compose bring-up, Pages UX) |

## How to run each layer

```bash
ruff check .
ruff format --check .
mypy
pytest
python -m build
docker compose up --build   # optional smoke
```

## Manual checklist

| Step | Expected | Pass/Fail |
| --- | --- | --- |
| `cp .env.example .env` and start with `uvicorn app.main:create_app --factory` | Process starts; missing `APP_ENVIRONMENT` refuses boot with that name | |
| `GET /healthz` | `200` `{"status":"ok"}` | |
| `GET /readyz` with no checks | `200` | |
| Send bad `X-Request-ID` | Response header is a generated id | |
| Trip rate limit (`APP_RATE_LIMIT_REQUESTS=2`) | Third request `429`; `/healthz` still `200` | |
| `alembic upgrade head` | Completes; SQLite file created | |
| `docker compose up --build` | Container healthy; process not root (`docker compose exec api id`) | |
| Open Pages checklist | Expand/collapse, filter, local progress persist | |
| Keyboard-only through checklist | Focus visible; checkboxes operable | |
| Mobile width 360px | Hero and checklist usable, no horizontal page scroll | |

## Known bugs / limits

- Unhandled 500 responses miss CORS headers.
- In-process rate limiter only.
- Key-name log redaction only.
- Behind a reverse proxy the rate limiter needs `APP_TRUSTED_PROXY_HOPS`; at the default every client shares one bucket.

## Demo assets for you to record

1. Terminal: boot without `APP_ENVIRONMENT`, then with `.env`, hit `/healthz` and a 429.
2. Browser: expand three checklist items on the Pages URL.
3. Optional: `docker compose exec api id` showing uid 10001.
