# ADR-0004: JWT access tokens + argon2 password hashing, no refresh tokens yet

- Status: accepted
- Date: 2026-09-22

## Context

Stage 2 needs auth: users register, log in, and every other endpoint must know who is asking and
scope data to them (a user must never read another user's analysis by guessing its id - see
`analysis_service.AnalysisNotFoundError`'s deliberate 404-not-403 handling). The realistic options
were session cookies with server-side session storage, or stateless JWTs.

## Decision

**Stateless JWT access tokens** (PyJWT, HS256, signed with `JWT_SECRET_KEY`), a 60-minute TTL by
default (`JWT_ACCESS_TTL_MINUTES`), carried as `Authorization: Bearer <token>` and validated on
every request via a FastAPI dependency - no server-side session store, so no Redis or sticky
sessions to run (consistent with the project's "no Redis" decision: see the plan's Must/Should/
Optional triage). Passwords are hashed with **argon2** via `pwdlib`'s `PasswordHash.recommended()`
- the current OWASP-recommended algorithm, memory-hard against GPU cracking, and `pwdlib` tracks
the recommendation forward without an app-code change if it is ever revised.

**No refresh tokens in this stage** (Should-tier, not built): a 60-minute access token that simply
expires, requiring a fresh login, is a deliberately simple starting point for a portfolio-scale
deployment with one user role and no long-lived sessions to protect.

## Consequences

- Every backend process can validate a token independently (no shared session store to reach) -
  the MCP server and any future horizontally-scaled backend instance need only the same
  `JWT_SECRET_KEY`.
- A compromised or leaked token is valid until it expires; there is no server-side revocation
  list. Mitigated by the short TTL, not eliminated - a real revocation mechanism (a denylist, or
  short-lived tokens plus refresh tokens with rotation) is the natural next step if this moves
  past portfolio scale.
- Password hashing cost (argon2's memory/time parameters) is `pwdlib`'s recommended default, not
  independently tuned for this deployment's hardware - acceptable for the current scale, worth
  revisiting under real load.
