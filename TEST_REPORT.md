# TEST_REPORT — v0.1.0

Date: 2026-11-11

## Automated

| Check | Result | Notes |
| --- | --- | --- |
| ruff check / format | pass (local) | also expected green on CI |
| mypy strict | pass (local) | 17 source files |
| pytest + coverage | pass (local) | 45 passed, 94.13% (floor 85%) |
| `python -m build` | pending CI | CI job on main / PR |
| CodeQL | pending CI | workflow on main / PR |

Local re-run:

```bash
pip install -e ".[dev]"
ruff check . && ruff format --check . && mypy && pytest
```

## Not covered

- Multi-worker / shared-store rate limiting
- Real Sentry network delivery (init is stubbed / DSN-gated)
- Load or soak tests
- Browser Lighthouse numbers (measure after Pages deploy; target 90+)
- End-to-end Kubernetes probes against a live cluster

## Manual

See [QA.md](QA.md). Manual pass/fail column is for the maintainer run after merge.
