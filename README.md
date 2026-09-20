# AI Security Copilot

An **evidence-first** phishing and malicious-URL analysis platform. Machine learning,
deterministic security analysis, threat intelligence and retrieval-augmented cybersecurity
knowledge produce the evidence and the risk score. An LLM only *explains* that evidence: it
never decides the classification or the score.

> **Status: Stage 1 of 5 in progress** — dataset foundation (milestone M1.1). Nothing beyond the
> ML data pipeline exists yet; the sections below describe the target design and are marked with
> the stage that delivers them.

## Design principles

- **Evidence first.** ML + rules + threat intel + RAG → evidence → deterministic scoring → LLM
  explanation with citations.
- **Honest evaluation.** Group-aware splits, shortcut audits, calibration, realistic-prevalence
  metrics. A number is only reported if we can explain how it could be wrong.
- **Defensive only.** URL and infrastructure analysis; no active scanning or exploitation.
- **Runs natively.** No Docker is required to develop or test. Docker packaging is an optional
  deployment extra.
- **Clean separation.** Training code never ships in the inference path; shared libraries are
  imported one-way by the apps.

## Roadmap

| Stage | Scope | Status |
|---|---|---|
| 1 | Dataset, feature engineering, model training/evaluation, SHAP, model + data cards | In progress (M1.1) |
| 2 | FastAPI, PostgreSQL, security analysis (DNS/RDAP), ML inference API, auth | Planned |
| 3 | Embeddings, RAG over a curated cybersecurity knowledge base, LLM reports | Planned |
| 4 | Threat intelligence, MCP server, LangChain agent | Planned |
| 5 | React dashboard, integration, deployment, documentation | Planned |

## Quick start (Stage 1)

Requirements: Windows/macOS/Linux, [uv](https://docs.astral.sh/uv/) (it installs the pinned
Python 3.12 for you).

```bash
uv sync                          # create .venv and install everything from uv.lock
uv run copilot-ml data build     # download (checksum-verified), clean, split, write data card
uv run pytest                    # tests
uv run ruff check . && uv run ruff format --check . && uv run mypy
```

`copilot-ml data build` writes:

- `ml/datasets/processed/{train,val,test}.parquet` — split by *site* so no website appears in
  two splits
- `ml/datasets/processed/split_manifest.json` — machine-readable record of the split
- `ml/reports/data_card.md` — source, cleaning waterfall, split integrity, shortcut audit

Configuration is via environment variables; see [`.env.example`](.env.example). Secrets are never
committed.

## Repository layout

```
ml/          copilot_ml package: data, features, training, evaluation, explainability, inference
docs/adr/    architecture decision records
```

Further top-level directories (`backend/`, `libs/`, `mcp-server/`, `knowledge-base/`,
`frontend/`, `infrastructure/`) are created by the stage that first needs them.

## Data source

[PhiUSIIL Phishing URL Dataset](https://archive.ics.uci.edu/dataset/967/phiusiil+phishing+url+dataset)
(Prasad & Chandra, 2024), CC BY 4.0. Only the URL text and label are used. See the generated data
card for known limitations of this dataset.
