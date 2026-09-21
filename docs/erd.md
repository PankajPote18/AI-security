# Entity-relationship diagram — Stage 2

```
users                    urls                      domains
------                   ------                    --------
id (pk, uuid)            id (pk, uuid)              id (pk, uuid)
email (unique)           normalized                 registered_domain (unique)
password_hash            sha256 (unique)             dns_snapshot (jsonb)
is_active                created_at                  rdap_snapshot (jsonb)
created_at                                           domain_created_at
                                                      refreshed_at
                                                      created_at
   |                        |                             |
   |                        |                             |
   +---------+   +----------+                  +----------+
             |   |                              |
             v   v                              v
            analyses
            --------
            id (pk, uuid)
            user_id     -> users.id     (cascade delete)
            url_id      -> urls.id
            domain_id   -> domains.id   (nullable: set once security_analysis_service resolves it)
            status            "pending" | "running" | "completed" | "failed"
            mode              "standard" | "deep" (Stage 4)
            steps             jsonb  [{step, status, ms, error}, ...]
            risk_score        float, 0-100
            risk_level        "low" | "medium" | "high"
            classification    "likely_legitimate" | "suspicious" | "likely_phishing"
            indicators        jsonb  [{code, severity, title, description, mitre_technique}, ...]
            degraded          bool
            error             text, nullable
            completed_at      timestamptz, nullable
            created_at
              |                                    \
              | 1:1                                  \ 1:N
              v                                        v
          predictions                               feedback
          -----------                               --------
          id (pk, uuid)                              id (pk, uuid)
          analysis_id -> analyses.id (unique, cascade)  analysis_id -> analyses.id (cascade)
          model_name                                    user_id     -> users.id
          feature_schema_version                        verdict     "agree" | "disagree"
          artifact_sha256                               comment     text, nullable
          probability                                   created_at
          threshold
          label             1 = phishing, 0 = legitimate
          top_contributions jsonb  [{feature, shap_value}, ...]
          latency_ms
          created_at
```

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
