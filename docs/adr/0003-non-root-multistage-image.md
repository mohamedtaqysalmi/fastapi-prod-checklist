# ADR 0003 — Multi-stage non-root image

- Status: Accepted
- Date: 2026-11-11

## Context

A single-stage root image is common in demos and is an easy privilege path if the process is compromised.

## Decision

Builder stage installs into a venv; runtime copies it and runs as UID 10001. A readiness test parses the Dockerfile for multiple `FROM` lines and a non-root `USER` in the final stage (a `USER` in the builder stage does not count).

## Consequences

The image is slightly more verbose. CI fails if the final stage loses its `USER` or sets it to root. CI does not build the image; that was checked by hand.
