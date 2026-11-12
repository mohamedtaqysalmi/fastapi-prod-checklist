# TEST_REPORT

Date: 2026-11-12. Covers `main` after v0.1.0 plus the review fixes in this branch.

## Automated, run locally on Python 3.15

| Check | Result |
| --- | --- |
| `ruff check .` and `ruff format --check .` | pass |
| `mypy` (strict) | pass, 18 files |
| `pytest` with coverage | 53 passed, 94.37% (floor is 85%) |
| `python -m build` | pass |

CI runs the same commands on Python 3.11 and 3.14 plus CodeQL. The latest runs on `main` were green when this was written.

Re-run:

```bash
pip install -e ".[dev]"
ruff check . && ruff format --check . && mypy && pytest
```

## Checked by hand

| Check | Result |
| --- | --- |
| Fresh clone, README quickstart (venv, `pip install -e ".[dev]"`, `uvicorn app.main:create_app --factory`) | works; `/healthz` 200 with request ID and security headers |
| `docker build .` | works, 284 MB image |
| `docker run`: `id` | `uid=10001(app)` |
| Container healthcheck | `healthy` |
| SIGTERM | logs `shutdown began`, `application stopped`, exits cleanly |
| `alembic upgrade head` in the container | failed before this branch (`/app` not writable by the non-root user); works after the Dockerfile fix and a rebuild |
| Removing each requirement and re-running the suite | each of 20 removals was caught, except one: an empty Alembic revision, now covered by `test_alembic_upgrade_creates_the_schema` |

## Not covered

- Shared-store rate limiting across several workers
- Real Sentry network delivery (init is stubbed in tests)
- Load or soak tests
- Lighthouse numbers for the Pages site
- Probes against a live Kubernetes cluster
- `docker compose up` was not re-run for this report

## Manual

See [QA.md](QA.md). The pass/fail column there is for the maintainer to fill in.
