# Architecture

Short ADRs for the choices that shape this template.

## ADR 1 — Readiness tests assert behaviour, not private names

**Decision:** `tests/test_production_readiness.py` drives HTTP, settings, file layout and Alembic CLI outcomes.

**Why:** A rename of an internal helper should not greenwash a removed feature. If `/healthz` disappears, the liveness test fails.

**Trade-off:** Some ops checks (Dockerfile `USER`, Alembic files) are structural. That is intentional: those requirements are files, not runtime endpoints.

## ADR 2 — In-process rate limiting by default

**Decision:** Fixed-window limiter in middleware, keyed by `X-Forwarded-For` or peer IP. `/healthz` and `/readyz` are exempt.

**Why:** A single-process template needs a guard that works with zero infrastructure.

**Trade-off:** Multiple workers need a shared store. Documented as a known limit and tracked for v0.2.0.

## ADR 3 — Sentry stays off without a DSN

**Decision:** `init_sentry` returns immediately when `APP_SENTRY_DSN` is empty. Init uses `send_default_pii=False`.

**Why:** Local and CI runs must stay quiet. Opt-in avoids accidental event spam from template clones.

## ADR 4 — Alembic ships beside an optional async engine

**Decision:** App creates an async SQLAlchemy engine only when `APP_DATABASE_URL` is set. Alembic rewrites async URLs to sync drivers for migrations.

**Why:** Not every deploy needs a database on day one, but the migration path must already exist and be tested.

## ADR 5 — Multi-stage non-root image

**Decision:** Builder installs into a venv; runtime copies it and runs as UID 10001. A readiness test parses the Dockerfile.

**Why:** Root in the container is an easy escalation path. Asserting `USER` in CI keeps the requirement from drifting.
