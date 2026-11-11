# ADR 0002 — Sentry stays opt-in

- Status: Accepted
- Date: 2026-11-11

## Context

Shipping a hard-wired error reporter spam local and CI clones with events, or fails when the SDK is unused.

## Decision

`init_sentry` does nothing unless `APP_SENTRY_DSN` is set. When it runs, `send_default_pii=False`.

## Consequences

Error reporting is a deliberate deploy choice. Tests assert the off-by-default path and a mocked init path.
