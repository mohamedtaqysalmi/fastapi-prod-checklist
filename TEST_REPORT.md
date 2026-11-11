# TEST_REPORT — v0.1.0

Date: 2026-11-11 (to be filled with the green CI run that ships the tag).

## Automated

| Check | Result | Notes |
| --- | --- | --- |
| ruff check / format | pending CI | |
| mypy strict | pending CI | |
| pytest + coverage | pending CI | floor 85% (`fail_under`) |
| `python -m build` | pending CI | |
| CodeQL | pending CI | |

Re-run locally after install:

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
