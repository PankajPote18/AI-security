from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security_report import SecurityReport


async def get_by_analysis_id(db: AsyncSession, analysis_id: uuid.UUID) -> SecurityReport | None:
    result = await db.execute(
        select(SecurityReport).where(SecurityReport.analysis_id == analysis_id)
    )
    return result.scalar_one_or_none()


async def upsert(
    db: AsyncSession,
    *,
    analysis_id: uuid.UUID,
    status: str,
    provider: str,
    model_name: str,
    prompt_version: str,
    report: dict[str, Any] | None,
    sources: list[dict[str, Any]],
    error: str | None,
    prompt_tokens: int | None,
    completion_tokens: int | None,
    latency_ms: float,
) -> SecurityReport:
    """Regenerating a report for the same analysis replaces the previous one - the report is
    derived, disposable content (see the model docstring), so there is no history to preserve."""
    values = {
        "analysis_id": analysis_id,
        "status": status,
        "provider": provider,
        "model_name": model_name,
        "prompt_version": prompt_version,
        "report": report,
        "sources": sources,
        "error": error,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "latency_ms": latency_ms,
    }
    stmt = (
        pg_insert(SecurityReport)
        .values(**values)
        .on_conflict_do_update(index_elements=[SecurityReport.analysis_id], set_=values)
        .returning(SecurityReport)
    )
    result = await db.execute(stmt)
    return result.scalar_one()
