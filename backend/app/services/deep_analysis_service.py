"""Deep-mode analysis (`mode=deep`): the row is created and returned immediately with
`status="running"`; a FastAPI background task then runs the Stage 4 agent and persists its
result when it finishes. The client polls `GET /analyses/{id}` (and `/analyses/{id}/report` once
complete) exactly as for standard mode - only how the evidence is gathered differs, so both
modes share the same response shapes and polling contract.

Unlike standard mode, a deep analysis has no `Prediction` row: the MCP `analyze_url` tool
reports a risk score/level/classification/indicators (the same deterministic
`security_core.scoring.score` standard mode uses) but not the lower-level SHAP/threshold detail
a `Prediction` row requires - that detail is backend-internal audit data an MCP tool consumed by
any host, not just this backend, has no reason to expose. `ml_analysis` is simply `None` in a
deep analysis's response, a state `AnalysisOut` already supports.
"""

from __future__ import annotations

import hashlib
import time
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.security_agent import AGENT_PROMPT_VERSION, AgentError, run_deep_analysis
from app.db.session import async_session_factory
from app.repositories import analyses as analyses_repo
from app.repositories import security_reports as security_reports_repo
from app.repositories import urls as urls_repo
from app.schemas.analysis import AnalysisOut
from app.services.analysis_service import to_analysis_out
from security_core.url_validation import InvalidUrlError, validate_and_normalize

PROVIDER = "huggingface"


async def start_deep_analysis(
    db: AsyncSession, *, user_id: uuid.UUID, raw_url: str
) -> tuple[AnalysisOut, str]:
    """Creates the analysis row and returns it immediately (`status="running"`); the caller is
    responsible for scheduling `run_and_persist_deep_analysis` as a background task with the
    returned normalized URL."""
    try:
        normalized = validate_and_normalize(raw_url)
    except InvalidUrlError as error:
        raise ValueError(str(error)) from error

    sha256 = hashlib.sha256(normalized.normalized.encode("utf-8")).hexdigest()
    url_row = await urls_repo.get_or_create(db, normalized=normalized.normalized, sha256=sha256)
    analysis_row = await analyses_repo.create(db, user_id=user_id, url_id=url_row.id, mode="deep")
    analysis_row.status = "running"
    analysis_row.steps = [{"step": "agent", "status": "running"}]
    await db.commit()

    return to_analysis_out(analysis_row, url_row.normalized, None, [], None), normalized.normalized


async def run_and_persist_deep_analysis(analysis_id: uuid.UUID, url: str) -> None:
    """Runs as a FastAPI `BackgroundTask`, after the request's response has already been sent -
    it owns its own DB session rather than reusing the (by-then-closed) request-scoped one."""
    async with async_session_factory() as db:
        analysis_row = await analyses_repo.get_by_id(db, analysis_id)
        if analysis_row is None:
            return  # defensive: unreachable in practice, the row was just created

        start = time.perf_counter()
        try:
            result = await run_deep_analysis(url)
        except AgentError as error:
            analysis_row.status = "failed"
            analysis_row.error = str(error)
            analysis_row.steps = [
                {
                    "step": "agent",
                    "status": "failed",
                    "ms": (time.perf_counter() - start) * 1000,
                    "error": str(error),
                }
            ]
            await db.commit()
            return

        url_analysis = result.url_analysis
        analysis_row.status = "completed"
        analysis_row.risk_score = url_analysis.get("risk_score")
        analysis_row.risk_level = url_analysis.get("risk_level")
        analysis_row.classification = url_analysis.get("classification")
        analysis_row.indicators = url_analysis.get("indicators", [])
        analysis_row.degraded = False
        analysis_row.completed_at = datetime.now(UTC)
        analysis_row.steps = [
            {"step": "agent", "status": "done", "ms": (time.perf_counter() - start) * 1000},
            *({"step": f"tool:{t.tool}", "status": t.status, "args": t.args} for t in result.trace),
        ]

        report_payload = None
        report_status = "failed"
        report_error: str | None = (
            result.report_error or "the agent did not produce a structured report"
        )
        if result.report is not None:
            report_payload = {
                "summary": result.report.summary,
                "indicator_explanations": [
                    e.model_dump() for e in result.report.indicator_explanations
                ],
                "recommendations": result.report.recommendations,
            }
            report_status = "completed"
            report_error = None

        await security_reports_repo.upsert(
            db,
            analysis_id=analysis_row.id,
            status=report_status,
            provider=PROVIDER,
            model_name=result.model_name,
            prompt_version=AGENT_PROMPT_VERSION,
            report=report_payload,
            # the agent cites tool-provided evidence inline; no pre-numbered [Source N] list
            # like standard mode's report_service builds from a retrieval query
            sources=[],
            error=report_error,
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            latency_ms=(time.perf_counter() - start) * 1000,
        )
        await db.commit()
