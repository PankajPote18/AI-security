# AI Security Copilot

An **evidence-first** phishing and malicious-URL analysis platform. Machine learning,
deterministic security analysis, threat intelligence and retrieval-augmented cybersecurity
knowledge produce the evidence and the risk score. An LLM only *explains* that evidence: it
never decides the classification or the score (see [ADR-0003](docs/adr/0003-deterministic-scoring-never-decided-by-the-llm.md)).

> **Status: Stage 5 of 5 in progress.** Stages 1-4 (ML pipeline, backend/security analysis,
> RAG + LLM reports, threat intelligence + MCP server + LangChain agent) are complete, tested,
> and live-verified. The React dashboard (this stage's core deliverable) is built and verified
> end to end in a real browser. Deployment docs and a threat model exist; a production deploy
> has not yet been performed.

## What it does

Submit a URL. A deterministic pipeline (ML classifier + structural indicators + DNS/RDAP +
threat intelligence) scores it 0-100 and classifies it, in a couple of seconds
(`mode=standard`). Optionally, a LangChain agent investigates the same URL by dynamically
choosing which of the same evidence-gathering tools to call, through a real MCP server it
spawns over stdio (`mode=deep`, asynchronous, polled). Either way, an LLM can generate a
plain-language, cited explanation of the deterministic result - it explains a verdict it did not
make.

## Design principles

- **Evidence first.** ML + rules + threat intel + RAG → evidence → deterministic scoring → LLM
  explanation with citations. The LLM's own output schemas have no field capable of expressing a
  score or classification - not a convention, a type-level guarantee.
- **Honest evaluation.** Group-aware splits, shortcut audits (caught and fixed a real feature
  leak - see the model card), calibration, realistic-prevalence metrics.
- **Defensive only.** URL and infrastructure metadata analysis; no page-content fetching, no
  active scanning or exploitation. See [`docs/threat-model.md`](docs/threat-model.md).
- **Runs natively.** No Docker is required to develop, test, or deploy this project. Every
  external-API integration (LLM, threat intel) degrades gracefully when unconfigured rather than
  failing the analysis.
- **Clean separation.** Training code never ships in the inference path; `backend` and
  `mcp-server` both depend only on shared libs (`ml`, `security-core`, `rag-core`), never on each
  other - the MCP server is a real, independently runnable server, not backend-internal code with
  extra steps.
- **Live-verified, not just tested.** Nearly every non-trivial integration in this project (RDAP
  redirects, Qdrant hybrid search, LLM structured output, the agent's tool-calling loop) was
  checked against the real, running service at least once, and several real bugs were only found
  that way - see the ADRs and ADR-0005 in particular for one example.

## Architecture

```
React dashboard ──► FastAPI (/api/v1) ──┬─► ml (Predictor: XGBoost + SHAP)
                                         ├─► security-core (indicators, DNS/RDAP, threat intel, scoring)
                                         ├─► rag-core (Qdrant hybrid search over knowledge-base/)
                                         └─► llm/ (HF Inference Providers, structured output)
                                                        │
                           mode=deep ──► LangChain agent ──stdio──► mcp-server (same libs, real MCP tools)
```

## Stages

| Stage | Scope | Status |
|---|---|---|
| 1 | Dataset, feature engineering, model training/evaluation, SHAP, model + data cards | Done |
| 2 | FastAPI, PostgreSQL, security analysis (DNS/RDAP), ML inference API, auth | Done |
| 3 | Embeddings, RAG over a curated cybersecurity knowledge base, LLM reports | Done |
| 4 | Threat intelligence, MCP server, LangChain agent (`mode=deep`) | Done |
| 5 | React dashboard, deployment docs, documentation | Dashboard done; production deploy not yet performed |

## Quick start

Requirements: Windows/macOS/Linux, [uv](https://docs.astral.sh/uv/) (installs the pinned Python
3.12 for you), **PostgreSQL 16+** (native install), **Node.js 20+** (for the dashboard).

```bash
uv sync                                    # every Python package: ml, security-core, rag-core, mcp-server, backend
cp .env.example .env                       # fill in DATABASE_URL/JWT_SECRET_KEY at minimum - see the file's comments
uv run copilot-ml data build && uv run copilot-ml train   # trains the model backend/needs to start
cd backend && uv run alembic upgrade head && cd ..
uv run pytest                              # the whole workspace's tests
```

Run the backend and dashboard (two terminals):

```bash
cd backend && uv run uvicorn app.main:app --reload   # http://localhost:8000/docs (Swagger)
cd frontend && npm install && npm run dev             # http://localhost:5173
```

`HF_TOKEN` (report generation, the deep-mode agent) and `URLHAUS_AUTH_KEY` (threat intelligence)
are both optional - everything degrades gracefully without them. Full walkthrough, including the
database setup script and troubleshooting: [`docs/local-development.md`](docs/local-development.md).
Deploying to a real server: [`docs/deployment.md`](docs/deployment.md).

## Repository layout

```
ml/               copilot_ml: data, features, training, evaluation, explainability, inference
libs/security-core/   URL validation, structural indicators, DNS/RDAP, threat intel, deterministic scoring
libs/rag-core/    knowledge-base loading/chunking/embedding, Qdrant hybrid search, ingest CLI
backend/          FastAPI app: auth, analysis orchestration, LLM reports, the deep-mode agent
mcp-server/       copilot-mcp: the same capabilities as real, standalone MCP tools over stdio
frontend/         React + TypeScript + Tailwind/shadcn dashboard
knowledge-base/   curated, licensed cybersecurity documents (phishing, MITRE ATT&CK, OWASP, DNS/HTTP)
evals/rag/        retrieval evaluation (hit@k, MRR), CI-enforced thresholds
docs/             ERD, local-dev and deployment guides, threat model, ADRs
infrastructure/   native Postgres setup script, systemd/Nginx/backup deployment templates
```

## Documentation

- [`docs/local-development.md`](docs/local-development.md) - run everything locally, no Docker
- [`docs/deployment.md`](docs/deployment.md) - native VPS deployment (systemd + Nginx + certbot)
- [`docs/threat-model.md`](docs/threat-model.md) - what this defends against, and what is
  explicitly out of scope
- [`docs/erd.md`](docs/erd.md) - database schema
- [`docs/adr/`](docs/adr/) - architecture decisions and why, including two real bugs found only
  by live-testing against real providers (ADR-0005)

## Data source

[PhiUSIIL Phishing URL Dataset](https://archive.ics.uci.edu/dataset/967/phiusiil+phishing+url+dataset)
(Prasad & Chandra, 2024), CC BY 4.0. Only the URL text and label are used. See
`ml/reports/data_card.md` (generated by `copilot-ml data build`) for known limitations. The
curated knowledge base's sources and licensing are documented in
[`knowledge-base/SOURCES.md`](knowledge-base/SOURCES.md).
