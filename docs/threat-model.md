# Threat model

A short account of what this system defends against, how, and what is explicitly out of scope.
Not a formal STRIDE/DREAD exercise - a working list a reviewer or a future contributor can check
new code against.

## What the system does and does not do

AI Security Copilot **analyzes a URL's metadata** - the string itself, DNS records, RDAP
registration data, structural patterns, and reputation-feed lookups - and, in deep mode, lets an
LLM agent choose among those same read-only lookups. It **never fetches the page the URL points
to**: no rendering, no screenshots, no following the URL to see what is there. This is a
deliberate scope boundary, not a missing feature - it keeps the attack surface to "parse and look
up metadata about a string a user gave us," never "render or execute content an attacker
controls." If page-content analysis is ever added, it needs its own threat model pass (an
SSRF-hardened fetcher - see below - and untrusted-HTML handling both apply).

## Assets

- **User accounts and their analysis history.** Email, password hash, and every URL a user has
  submitted plus its results.
- **The JWT signing key, database credentials, and third-party API keys** (`HF_TOKEN`,
  `URLHAUS_AUTH_KEY`) - compromise of any of these is a compromise of the whole deployment.
- **The trained ML artifact's integrity** - a tampered model changes every future verdict.
- **The deterministic score's trustworthiness** - see ADR-0003. This is the system's core promise
  and the thing most worth protecting from indirect manipulation.

## Threats and mitigations already in place

| Threat | Mitigation | Where |
|---|---|---|
| SQL injection via a submitted URL or any user input | SQLAlchemy parameterized queries exclusively, never string-built SQL | throughout `app/repositories/` |
| A user reading another user's analysis by guessing its id | Every read is scoped by `user_id` in the query itself (`analyses_repo.get_for_user`), and a not-found vs not-yours distinction is never revealed (404 either way) | `analysis_service.AnalysisNotFoundError`, `report_service` |
| Credential stuffing / weak passwords | argon2 hashing (memory-hard), minimum password length enforced at the schema level | ADR-0004, `schemas/auth.py` |
| A leaked/expired JWT being replayed indefinitely | Short (60 min) TTL, no server-side session state to poison; see ADR-0004 for what this does *not* cover (no revocation list yet) | `core/security.py` |
| Secrets committed to the repo | `.env` is gitignored; `gitleaks` runs in CI on every push; every secret is read via `pydantic_settings.SecretStr`, never logged or printed (a live-testing rule enforced throughout this project's own session history, not just a policy on paper) | `.github/workflows/ci.yml`, `app/core/config.py` |
| A tampered or corrupted ML artifact being loaded silently | SHA-256 of the artifact file is checked against the checksum pinned in its own `metadata.json` before unpickling; a mismatch raises `ArtifactIntegrityError` and the app fails to start rather than serving a tampered model | `copilot_ml/inference/predictor.py` |
| Prompt injection via evidence an attacker controls (DNS TXT records, a domain's own text, retrieved knowledge-base passages, threat-intel tags) | Every LLM prompt frames evidence inside `<evidence>`/`<context>` tags with an explicit system-prompt instruction to treat their contents as untrusted data, never instructions, and the schema (ADR-0003) makes score/classification manipulation structurally impossible regardless | `app/llm/prompts.py`, `app/agents/security_agent.py` |
| Hallucinated or fabricated citations in an AI-generated report | `report_service` filters `source_numbers` against the actual retrieved source count before persisting - a citation to a source that does not exist is dropped, not trusted | `report_service.generate_report` |
| Rate-limit abuse of `POST /analyze/url` (each call costs ML inference, and in deep mode, real LLM spend) | Per-client-IP rate limiting via `slowapi` (`RATE_LIMIT_ANALYZE`, default 20/minute) | `core/rate_limit.py` |
| Malformed or adversarial URL input crashing the parser | Hypothesis-based "never raises" property tests on the URL/feature parsers; `_safe_split()` wraps `urlsplit` after a real crash (bare IPv6 host) was found this way, not assumed away | `security_core/indicators.py`, `libs/security-core/tests/test_never_raises.py` |
| Submitting a third party's data to yet another third party without consent | Threat-intel providers are **lookup-only** - a URL is checked against a feed, never submitted to one; no query values are forwarded to the LLM's context beyond what the user themselves submitted | `security_core/threat_intel/` |
| An oversized or malformed request exhausting resources | Request body size caps at the Pydantic-field level (`AnalyzeRequest.url` max_length), request timeouts on every outbound lookup (DNS, RDAP, threat-intel, LLM) | `schemas/analysis.py`, per-lookup `timeout` params |

## Explicitly out of scope (deferred, documented, not forgotten)

- **SSRF-hardened outbound fetching.** Nothing in this system currently fetches the target page's
  content, so there is no fetcher to harden yet - see "What the system does and does not do"
  above. If a hardened fetcher is added (the plan's Should-tier item, deferred), it needs: private/
  loopback/link-local/metadata-IP blocking, re-validation on every redirect hop, a port/scheme
  allowlist, and response size/time caps, before the first line of fetching code ships.
- **JWT revocation.** See ADR-0004's consequences. A leaked token is valid until its 60-minute TTL
  expires; there is no denylist.
- **Multi-tenant rate limiting beyond per-IP.** A user behind a shared IP (a NAT, a corporate
  proxy) shares that IP's rate-limit budget with everyone else behind it.
- **IP-reputation lookups and a second threat-intel provider.** Deferred Should-tier scope; the
  provider interface (`security_core/threat_intel/base.py`) is already provider-agnostic so adding
  one is additive, not a redesign.
- **Supply-chain verification of third-party model weights.** The ML artifact's own integrity is
  checked (see above), but the Hugging Face-hosted LLM the app calls at inference time is trusted
  as a service, not independently verified per call.
