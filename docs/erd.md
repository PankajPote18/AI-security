# Entity-relationship diagram

```
users                    urls                      domains
------                   ------                    --------
id (pk, uuid)            id (pk, uuid)              id (pk, uuid)
email (unique)           normalized                 registered_domain (unique)
password_hash            sha256 (unique)             dns_snapshot (jsonb)
is_active                created_at                  rdap_snapshot (jsonb)
created_at                 |                          domain_created_at
   |                       | 1:N                      refreshed_at
   |                       v                          created_at
   |                 threat_intel_lookups                  |
   |                 --------------------                  |
   |                 id (pk, uuid)                          |
   |                 url_id    -> urls.id (cascade)         |
   |                 provider        "urlhaus" (more providers: additive)|
   |                 status           "listed" | "not_listed" | "unavailable"
   |                 threat_type      text, nullable        |
   |                 tags             jsonb  [str, ...]      |
   |                 reference_url    text, nullable         |
   |                 error            text, nullable         |
   |                 fetched_at       timestamptz            |
   |                 created_at                              |
   |                 unique(url_id, provider)                |
   |                        |                                |
   +---------+   +----------+                     +----------+
             |   |                                 |
             v   v                                 v
            analyses
            --------
            id (pk, uuid)
            user_id     -> users.id     (cascade delete)
            url_id      -> urls.id
            domain_id   -> domains.id   (nullable: set once security_analysis_service resolves it)
            status            "pending" | "running" | "completed" | "failed"
            mode              "standard" | "deep"
            steps             jsonb  [{step, status, ms, error}, ...] - deep mode's agent tool
                               calls appear here too, as {"step": "tool:<name>", ...}
            risk_score        float, 0-100
            risk_level        "low" | "medium" | "high"
            classification    "likely_legitimate" | "suspicious" | "likely_phishing"
            indicators        jsonb  [{code, severity, title, description, mitre_technique}, ...]
            degraded          bool
            error             text, nullable
            completed_at      timestamptz, nullable
            created_at
              |                    \                       \
              | 1:1                  \ 1:N                    \ 1:1
              v                        v                        v
          predictions               feedback              security_reports
          -----------               --------              -----------------
          id (pk, uuid)              id (pk, uuid)          id (pk, uuid)
          analysis_id -> analyses.id  analysis_id -> analyses.id  analysis_id -> analyses.id
            (unique, cascade)           (cascade)                   (unique, cascade)
          model_name                  user_id     -> users.id     status    "completed" | "failed"
          feature_schema_version      verdict     "agree" | "disagree"  provider  "huggingface"
          artifact_sha256             comment     text, nullable   model_name
          probability                 created_at                  prompt_version
          threshold                                                report    jsonb, nullable
          label  1=phishing, 0=legit                                 {summary, indicator_explanations, recommendations}
          top_contributions jsonb                                  sources   jsonb [{chunk_id, title, source_url, ...}]
            [{feature, shap_value}, ...]                           error     text, nullable
          latency_ms                                               prompt_tokens, completion_tokens  int, nullable
          created_at                                                latency_ms
                                                                     created_at
```

`predictions` exists only for standard-mode analyses (`mode="standard"`) - a deep-mode analysis
has no `Prediction` row by design (the MCP `analyze_url` tool intentionally doesn't expose
SHAP/threshold/artifact-checksum detail to external MCP hosts; see ADR-0005), so
`AnalysisOut.ml_analysis` is `null` for those. `security_reports` is populated by both modes -
standard mode's `report_service` and deep mode's `deep_analysis_service` write the same shape.

**Design notes**

- **UUID primary keys** everywhere, not sequential integers: IDs are not enumerable in a
  security product (a sequential id would let one user probe `/analyses/{n}` for other users'
  analyses even though the authorization check would still reject it).
- **`urls`** dedupes: the same normalised URL analysed twice reuses one row (`sha256` unique).
  It does **not** dedupe `analyses` - a user can re-analyse the same URL and gets a fresh
  `analyses` row each time (the model or DNS/RDAP facts may have changed).
- **`domains`** is a durable cache, not just history: `refreshed_at` lets
  `security_analysis_service` skip a DNS/RDAP re-lookup for a registered domain analysed
  recently (see `CACHE_TTL` in that module).
- **`predictions`** is 1:1 with `analyses` (a unique index on `analysis_id`), split out so the
  exact model identity (`model_name`, `feature_schema_version`, `artifact_sha256`) that produced
  a score is always reconstructable, independent of the `analyses` row's other fields.
- **`analyses.indicators`** is denormalised (JSONB copy) rather than a join table: indicators are
  written once, read as a unit with the rest of the analysis, and never queried independently
  across analyses in this stage. A join table would be premature normalisation.
- Every timestamp is `timestamptz` (UTC): see the ADR-worthy bug this caught in git history -
  asyncpg rejects timezone-aware Python `datetime` values against a naive column.
- **`threat_intel_lookups`** is keyed by `(url_id, provider)`, not `(analysis_id, provider)` -
  the same reasoning as `domains`: it is a durable, per-URL cache (`fetched_at` gates a re-lookup
  independent of which analysis triggers it), and a second provider is an additive row shape, not
  a schema change (mirroring the provider-agnostic `ThreatIntelProvider` interface in code).
- **`security_reports`** is 1:1 with `analyses`, same reasoning as `predictions`: the exact
  prompt version and model identity that produced an explanation stays reconstructable
  independent of the analysis it explains, and a report can be regenerated (upserted) without
  touching the analysis row itself.
