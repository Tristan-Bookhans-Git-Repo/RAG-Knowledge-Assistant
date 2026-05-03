# ADR-003: JWT stored in HTTP-only cookies

**Date:** 2026-04-30
**Status:** Validated

## Context

The frontend needs to carry authentication credentials on every API call. Three common approaches:

| Approach | XSS risk | CSRF risk | JS access |
|----------|----------|-----------|-----------|
| `Authorization: Bearer` header + localStorage | High — JS can read localStorage | None | Required |
| `Authorization: Bearer` header + memory | Low | None | Required — lost on refresh |
| HTTP-only cookie | None — JS cannot read | Moderate | None |

The frontend is server-rendered Jinja2 with minimal JavaScript. There is no SPA framework managing token state. Requiring JS to attach an `Authorization` header on every request adds complexity for no benefit in this architecture.

## Decision

Issue 2 HTTP-only cookies on successful login:
- `access_token` — JWT, TTL 15 minutes, `HttpOnly`, `SameSite=Lax`, `Secure` in production
- `refresh_token` — JWT, TTL 7 days, `HttpOnly`, `SameSite=Lax`, `Secure` in production, path restricted to `/auth/refresh`

The browser sends cookies automatically on every same-origin request. JavaScript cannot read or access them, eliminating the XSS token theft vector.

CSRF is mitigated by:
1. `SameSite=Lax` — cookies are not sent on cross-site POST requests initiated by third-party pages
2. All state-changing endpoints use `POST`, `DELETE` — not `GET`

`SECURE_COOKIES=True` is set via environment variable and requires HTTPS. It is `False` in local development (no TLS in docker-compose).

## Consequences

- Frontend JS never handles tokens — simpler frontend code, 401 responses redirect to `/login`
- Works correctly with Jinja2 server-rendered templates without any token management logic
- `SameSite=Lax` is not a complete CSRF defence for all browsers — a CSRF token per form could be added as a hardening step in v2
- Refresh token rotation: on each `/auth/refresh` call, the old refresh token is invalidated and a new one is issued
