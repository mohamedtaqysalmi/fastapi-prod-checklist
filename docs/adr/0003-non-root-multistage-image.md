# ADR 0003 — Multi-stage non-root image

- Status: Accepted
- Date: 2026-11-11

## Context

A single-stage root image is common in demos and is an easy privilege path if the process is compromised.

## Decision

Builder stage installs into a venv; runtime copies it and runs as UID 10001. A readiness test parses the Dockerfile for multiple `FROM` lines and a non-root final `USER`.

## Consequences

The image is slightly more verbose. CI fails if someone reintroduces `USER root` as the last user directive.
