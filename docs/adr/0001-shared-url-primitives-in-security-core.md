# ADR-0001: URL/host primitive detectors live in `security-core`, not `copilot-ml`

- Status: accepted
- Date: 2026-09-21

## Context

Stage 2 needs to detect several of the same URL/host properties the ML feature extractor
already detects correctly: whether a host is a raw (or obfuscated) IP address, string entropy,
and registered-domain/TLD decomposition. These live in `copilot_ml.features` because that
package existed first (Stage 1).

Re-implementing them inside `libs/security-core` would violate "avoid duplicated logic" and risk
subtle drift between what the ML model sees and what a human-facing security indicator reports
(the IP-obfuscation detector in particular has enough edge cases that a second, slightly
different implementation is a real correctness risk, not just a style concern).

The original plan stated libs never import each other (`apps -> libs`, one level). Two ways to
resolve the conflict: have `security-core` depend on `copilot-ml`, or extract the shared pieces
into `security-core` and have `copilot-ml` depend on it instead.

## Decision

Move the three dependency-light, pure detectors - `ip_host.py`, `entropy.py`, `hostnames.py`
(the shared `tldextract` configuration) - into `security-core`. `copilot-ml` now depends on
`security-core`; `security-core` does not depend on `copilot-ml` and never will.

This is a narrow, deliberate exception to "libs never import each other": it is one-way, it is
three small stdlib/`tldextract`-only modules, and it points from the heavier package (`copilot-ml`,
which pulls in pandas/scikit-learn/xgboost/shap/matplotlib) to the lighter one. The alternative
(security-core depending on copilot-ml) would force the backend and the future MCP server to
install the entire ML stack just to classify an IP string, which is worse.

`copilot_ml.features.lexical` (keyword/shortener/brand word lists) stays in `copilot-ml`: it is
specific to the ML feature schema's exact wording and versioning (`FEATURE_SCHEMA_VERSION`), not
a general-purpose primitive. `security-core`'s own indicator logic (Stage 2) may use a
differently-worded, differently-versioned list without needing to touch the ML schema.

## Consequences

- `security-core` has no dependency on `copilot-ml`, keeping it light for the backend and MCP
  server.
- `copilot-ml`'s already-exported model artifact (the pickled sklearn `Pipeline`) is unaffected:
  these modules are used before the pipeline runs, not inside it, so nothing needed retraining.
- Any future third consumer of these detectors (e.g. the MCP server) imports `security-core`
  directly, the same as `copilot-ml` does now.
