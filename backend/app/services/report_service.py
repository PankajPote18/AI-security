"""Orchestrates security-report generation: build a deterministic retrieval query from the
analysis's evidence -> retrieve grounding context -> ask the LLM for a structured explanation ->
validate its citations -> persist.

Degrades gracefully (status="failed", report=null) rather than raising, on any failure along the
way (LLM not configured, retrieval error, malformed structured output) - report generation is
optional enrichment on top of the deterministic analysis, never a reason that analysis becomes
unavailable. This mirrors the same fallback contract `analysis_service` uses for DNS/RDAP.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.client import get_chat_model
from app.llm.prompts import PROMPT_VERSION, build_messages
from app.llm.schemas import SecurityReportLLMOutput
from app.models.security_report import SecurityReport
from app.repositories import security_reports as security_reports_repo
from app.schemas.analysis import AnalysisOut
from app.schemas.report import IndicatorExplanationOut, SecurityReportOut, SourceOut
from app.services import analysis_service, knowledge_service

PROVIDER = "huggingface"
TOP_K_SOURCES = 5


class AnalysisNotCompleteError(ValueError):
    """A report can only be generated for a completed analysis - there is no evidence yet."""


def _build_retrieval_query(analysis: AnalysisOut) -> str:
    parts = [analysis.classification or ""]
    for indicator in analysis.indicators:
        parts.append(indicator.title)
        if indicator.mitre_technique:
            parts.append(indicator.mitre_technique)
    return " ".join(p for p in parts if p)


async def generate_report(
    db: AsyncSession, *, analysis_id: uuid.UUID, user_id: uuid.UUID
) -> SecurityReportOut:
    analysis = await analysis_service.get_analysis(db, analysis_id=analysis_id, user_id=user_id)
    if analysis.status != "completed" or analysis.ml_analysis is None:
        raise AnalysisNotCompleteError(f"analysis {analysis_id} is not completed")

    start = time.perf_counter()
    model_name = ""
    sources: list[dict[str, Any]] = []
    report_payload: dict[str, Any] | None = None
    error: str | None = None

    try:
        retrieval = knowledge_service.search(_build_retrieval_query(analysis), top_k=TOP_K_SOURCES)
        sources = retrieval.as_sources()

        chat_model = get_chat_model()
        model_name = chat_model.model_name
        structured_model = chat_model.with_structured_output(
            SecurityReportLLMOutput, method="json_schema", include_raw=True
        )

        domain_info = analysis.domain_info
        messages = build_messages(
            url=analysis.url,
            risk_score=analysis.risk_score or 0.0,
            risk_level=analysis.risk_level or "unknown",
            classification=analysis.classification or "unknown",
            ml_probability=analysis.ml_analysis.probability,
            ml_model_name=analysis.ml_analysis.model_name,
            indicators=[i.model_dump() for i in analysis.indicators],
            registered_domain=domain_info.registered_domain if domain_info else "unknown",
            registrar=domain_info.registrar if domain_info else None,
            domain_age_days=domain_info.domain_age_days if domain_info else None,
            dns_records=[r.model_dump() for r in domain_info.dns_records] if domain_info else [],
            degraded=analysis.degraded,
            context_text=retrieval.as_context_text(),
        )

        envelope = await structured_model.ainvoke(messages)
        if envelope["parsing_error"] is not None:
            raise ValueError(f"LLM output failed schema validation: {envelope['parsing_error']}")

        llm_output: SecurityReportLLMOutput = envelope["parsed"]
        usage = getattr(envelope["raw"], "usage_metadata", None) or {}
        prompt_tokens = usage.get("input_tokens")
        completion_tokens = usage.get("output_tokens")

        valid_source_numbers = set(range(1, len(sources) + 1))
        report_payload = {
            "summary": llm_output.summary,
            "indicator_explanations": [
                {
                    "indicator_code": e.indicator_code,
                    "explanation": e.explanation,
                    "source_numbers": [n for n in e.source_numbers if n in valid_source_numbers],
                }
                for e in llm_output.indicator_explanations
            ],
            "recommendations": llm_output.recommendations,
        }
        status = "completed"
    except Exception as caught_error:
        status = "failed"
        error = str(caught_error)
        prompt_tokens = None
        completion_tokens = None

    latency_ms = (time.perf_counter() - start) * 1000
    row = await security_reports_repo.upsert(
        db,
        analysis_id=analysis.id,
        status=status,
        provider=PROVIDER,
        model_name=model_name,
        prompt_version=PROMPT_VERSION,
        report=report_payload,
        sources=sources,
        error=error,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        latency_ms=latency_ms,
    )
    await db.commit()
    return _to_out(row)


async def get_report(
    db: AsyncSession, *, analysis_id: uuid.UUID, user_id: uuid.UUID
) -> SecurityReportOut | None:
    # get_analysis enforces per-user authorization even though this only reads the report row.
    await analysis_service.get_analysis(db, analysis_id=analysis_id, user_id=user_id)
    row = await security_reports_repo.get_by_analysis_id(db, analysis_id)
    return _to_out(row) if row else None


def _to_out(row: SecurityReport) -> SecurityReportOut:
    report = row.report or {}
    return SecurityReportOut(
        id=row.id,
        analysis_id=row.analysis_id,
        status=row.status,
        provider=row.provider,
        model_name=row.model_name,
        prompt_version=row.prompt_version,
        summary=report.get("summary"),
        indicator_explanations=[
            IndicatorExplanationOut(**e) for e in report.get("indicator_explanations", [])
        ],
        recommendations=report.get("recommendations", []),
        sources=[SourceOut(**s) for s in row.sources],
        error=row.error,
        latency_ms=row.latency_ms,
        created_at=row.created_at,
    )
