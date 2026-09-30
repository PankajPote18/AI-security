# ADR-0005: A real MCP server over stdio; the agent is `mode=deep`, not the default path

- Status: accepted
- Date: 2026-09-30

## Context

Stage 4 needed two things: expose the security-analysis capabilities as real MCP tools (so any
MCP host - Claude Desktop, MCP Inspector, not just this backend - can use them), and let an LLM
agent dynamically choose which evidence to gather for a "deep" analysis. Two open questions: does
the agent get its own copy of the analysis logic, or call the same tools an external host would;
and does `mode=deep` replace the standard deterministic pipeline or sit alongside it.

## Decision

**A standalone `mcp-server` package** (`copilot-mcp`), built directly on the existing libs
(`ml`, `security-core`, `rag-core`) and never on the `backend` app - the same dependency rule
("apps depend on libs, never on each other") that already separates `backend` from `ml`. The
backend's agent (`backend/app/agents/security_agent.py`) spawns it as a **stdio subprocess** via
`langchain-mcp-adapters`' `MultiServerMCPClient`, exactly the transport and connection method any
other MCP host would use - the agent is a client of the public tool surface, not a privileged
caller with backend-internal access. `analyze_url`, the first tool the agent's system prompt
instructs it to always call, runs the same `security_core.scoring.score` standard mode uses (see
ADR-0003), so `run_deep_analysis` recovers the deterministic score from the agent's own tool-call
trace afterward rather than asking the model for it.

**`mode=deep` is additive, not a replacement.** `POST /analyze/url` still defaults to
`mode=standard`'s fixed DNS+RDAP+ML+threat-intel pipeline; `mode=deep` is an opt-in, slower,
agent-driven alternative that returns 202 immediately and finishes in a background task, polled
the same way as standard mode. Both modes write to the same `analyses` and `security_reports`
tables and are indistinguishable in the API response shape (`AnalysisOut.mode` is the only tell) -
deep mode never became a separate feature with its own contract.

**The MCP server keeps its own local Qdrant index** (`.qdrant-mcp`, distinct from the backend's
`.qdrant`), for the reason ADR-0002 already established: local-mode Qdrant permits one process per
storage path, and the agent's subprocess can run concurrently with the backend's own
`knowledge_service`. Both are derived, rebuildable copies of `knowledge-base/`; `QDRANT_URL`
remains the escape hatch to point both processes at one real server with no code change.

**The default LLM model is `openai/gpt-oss-120b`, not the smaller `gpt-oss-20b`** used
provisionally in Stage 3. Live-testing the agent's multi-round tool-calling loop against Hugging
Face's router surfaced a real, reproducible reliability bug in `gpt-oss-20b` specifically: it
intermittently emits a tool call the router's own parser rejects with a bare `output_parse_failed`
and no further detail, well over half the time across dozens of live runs, and a same-request
retry hits the same wall. `gpt-oss-120b` produced zero such failures across the same test URLs.
`20b` remains fine for Stage 3's single-shot structured-output call, which is a different code
path with no repeated tool-calling round-trip - see `backend/app/llm/client.py` for the full
account, kept there rather than only here because it is exactly the kind of model-selection
tradeoff a reader debugging a model swap needs to find next to the code, not only in this log.

## Consequences

- The MCP server is genuinely independently useful and testable: `mcp-server/tests` includes an
  integration test that spawns it as a real subprocess and drives it over the actual MCP stdio
  protocol, not just calls into its Python functions directly.
- The agent's final report is written as a **separate** `json_schema` call over flattened evidence
  text (`_write_report`), not via `create_agent`'s built-in `response_format` - that mechanism
  forces one more synthetic tool call into the same long tool-calling conversation, and live
  testing showed that also triggers the router's `output_parse_failed` bug. The separate call is
  shorter-context and has not shown the same failure.
- Running deep mode costs real inference spend per analysis (a chat-completions call per agent
  turn plus the report call) and is measurably slower (tens of seconds to low minutes) than
  standard mode's synchronous response - the explicit reason it is opt-in rather than the default.
- A deep analysis has no `Prediction` row (see `deep_analysis_service.py`'s docstring): the MCP
  `analyze_url` tool intentionally does not expose SHAP/threshold/artifact-checksum detail, since
  an external MCP host has no use for backend-internal audit fields. `ml_analysis` is `None` in a
  deep analysis's API response, a state the schema already supported.
