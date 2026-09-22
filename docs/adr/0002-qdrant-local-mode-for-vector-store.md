# ADR-0002: Qdrant (local mode) as the vector store, pgvector rejected

- Status: accepted
- Date: 2026-09-22

## Context

Stage 3 needs a vector store for the cybersecurity knowledge base (~1-3k chunks) supporting
hybrid (dense + sparse) retrieval, and it must run natively on Windows with no Docker (project
constraint) and no server process the developer has to remember to start.

Two real candidates: **pgvector** (an extension of the Postgres already running for Stage 2) and
**Qdrant** (a dedicated vector database).

## Decision

**Qdrant, using its Python client's local mode** (`QdrantClient(path=...)`, SQLite-backed, no
server) for development, CI and single-process deployment; a native `qdrant.exe` server (an
official Windows build exists) only if a second process (the Stage 4 MCP server) needs concurrent
access to the same index.

Verified empirically (`libs/rag-core`'s vector store spike), not assumed:
- `QdrantClient(path=...)` requires no server and no Docker.
- Hybrid search (`Prefetch` per vector field + `FusionQuery(fusion=RRF)`) works identically in
  local mode and against a real server - confirmed by running dense, sparse and fused queries
  locally and inspecting the ranking.
- Re-upserting a chunk with the same content-hash id overwrites rather than duplicates (needed
  for the idempotent ingest CLI).
- pgvector's Windows story is a from-source extension build against the native Postgres install;
  Qdrant's local mode is `pip install qdrant-client` and nothing else.

The KB index is derived, rebuildable data (re-run the ingest CLI against `knowledge-base/`), so
keeping it out of the transactional Postgres database is also the right separation of concerns:
a vector index has different operational characteristics (rebuild-from-source, no foreign keys
to the app's relational data) than `analyses`/`predictions`/`users`.

## Consequences

- One extra Python dependency (`qdrant-client` + `fastembed`), no extra service to install or run
  locally.
- `QDRANT_URL` (unset by default) is the only thing that changes between local-mode development
  and a real server at deploy time; `libs/rag-core/vector_store.py` does not otherwise branch on
  which mode is active.
- Local mode's local mode is exact brute-force search (no HNSW index) - irrelevant at this
  corpus size (low thousands of chunks), worth revisiting only if the knowledge base grows by
  orders of magnitude.
