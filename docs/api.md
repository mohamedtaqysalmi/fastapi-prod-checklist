# API reference

The template exposes health probes and a shared error body. Application routes are yours to add.

## `GET /healthz`

Liveness. Does not run readiness checks.

```json
{"status": "ok"}
```

## `GET /readyz`

Runs every registered readiness check with `APP_READINESS_TIMEOUT_SECONDS`.

Success:

```json
{"status": "ok", "checks": {"cache": "ok"}}
```

Failure (`503`):

```json
{"status": "unavailable", "checks": {"cache": "ok", "database": "failed"}}
```

Exception text never appears in the body.

## Error body

All HTTP errors, validation failures and unhandled exceptions use:

```json
{
  "error": {
    "code": "not_found",
    "message": "Not Found",
    "request_id": "…",
    "details": [{"loc": ["path", "item_id"], "msg": "…", "type": "…"}]
  }
}
```

`details` is present only for validation errors. Submitted input values are never echoed.

## Headers

| Header | When |
| --- | --- |
| `X-Request-ID` | Every response, including CORS preflight |
| `Retry-After` | `429` from the rate limiter |
| Security headers | Every response (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Content-Security-Policy`; `Strict-Transport-Security` when not `local`) |
