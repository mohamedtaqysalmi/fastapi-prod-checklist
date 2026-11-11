# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Project scaffold: packaging, lint, type-check and test configuration.
- Community files, issue and PR templates, Dependabot config.
- CI workflow (ruff, mypy, pytest with coverage, build on Python 3.11 and 3.14) and CodeQL analysis.
- Application factory with settings validated at startup (`pydantic-settings`, `APP_` prefix) and `.env.example`.
- JSON logging with a per-request ID and key-based redaction of sensitive fields.
- `/healthz` liveness and `/readyz` readiness with pluggable checks.
- One error body for validation errors, HTTP errors and unhandled exceptions, without stack traces.
- CORS configured from settings (wildcard origin with credentials is refused) and a security headers middleware.
- `tests/test_production_readiness.py`, one test per requirement above, plus unit tests for config and logging.
