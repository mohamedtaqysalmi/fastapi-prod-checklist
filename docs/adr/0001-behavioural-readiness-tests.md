# ADR 0001 — Behavioural readiness tests

- Status: Accepted
- Date: 2026-11-11

## Context

Templates often claim "production-ready" in a README. That claim drifts when a middleware or probe is deleted and nothing fails.

## Decision

`tests/test_production_readiness.py` asserts observable behaviour: HTTP responses, settings validation, Alembic CLI, and Dockerfile structure. The README maps each requirement to its test.

## Consequences

Renaming a private helper does not greenwash a removed feature. Structural checks (Dockerfile `USER`) are intentional for file-based requirements.
