# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-11-11

### Added

- Application factory with settings validated at startup (`pydantic-settings`, `APP_` prefix).
- JSON logging with request IDs and key-based redaction.
- `/healthz` and `/readyz`, shared error bodies, CORS guards, security headers.
- In-process rate limiting (probes exempt) and Sentry hook that stays off without a DSN.
- Async SQLAlchemy wiring, Alembic migrations, graceful shutdown with in-flight drain.
- Multi-stage non-root Dockerfile and `docker compose` smoke path.
- Full `tests/test_production_readiness.py` matrix mapped from the README.
- GitHub Pages interactive checklist (`site/`), Pages workflow, QA.md and TEST_REPORT.md.
- Architecture ADRs and API notes under `docs/`.

## [0.0.1] - 2026-11-11

### Added

- Project scaffold: packaging, lint, type-check, test configuration, community files, CI and CodeQL.
