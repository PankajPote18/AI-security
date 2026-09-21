"""Orchestrates one URL analysis: validate -> ML + security analysis (concurrently) -> score ->
persist -> build the response. This is the only place that wires those pieces together; each
piece (`ml_service`, `security_analysis_service`, `scoring_service`) is independently testable.
"""

from __future__ import annotations

import asyncio
import hashlib
import time
import uuid
from dataclasses import asdict
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import Analysis
from app.repositories import analyses as analyses_repo
from app.repositories import domains as domains_repo
from app.repositories import predictions as predictions_repo
from app.repositories import urls as urls_repo
from app.schemas.analysis import AnalysisOut, AnalysisStepOut
from app.schemas.evidence import (
    DnsRecordOut,
    DomainInfoOut,
    FeatureContributionOut,
    IndicatorOut,
    MlAnalysisOut,
)
from app.services import ml_service, scoring_service, security_analysis_service
from security_core.url_validation import InvalidUrlError, validate_and_normalize


class AnalysisNotFoundError(LookupError):
    """Either the analysis does not exist, or it belongs to a different user (never distinguish
    the two in an API response - that would leak which ids exist)."""


async def run_analysis(db: AsyncSession, *, user_id: uuid.UUID, raw_url: str) -> AnalysisOut:
    try:
        normalized = validate_and_normalize(raw_url)
    except InvalidUrlError as error:
        raise ValueError(str(error)) from error

    sha256 = hashlib.sha256(normalized.normalized.encode("utf-8")).hexdigest()
    url_row = await urls_repo.get_or_create(db, normalized=normalized.normalized, sha256=sha256)
    analysis_row = await analyses_repo.create(db, user_id=user_id, url_id=url_row.id)
    analysis_row.status = "running"

    steps: list[AnalysisStepOut] = []

    async def timed_ml() -> ml_service.MlPredictionResult:
        start = time.perf_counter()
        try:
            result = await ml_service.predict_url(normalized.normalized)
            steps.append(
                AnalysisStepOut(step="ml", status="done", ms=(time.perf_counter() - start) * 1000)
            )
            return result
        except Exception as error:
            steps.append(
                AnalysisStepOut(
                    step="ml",
                    status="failed",
                    ms=(time.perf_counter() - start) * 1000,
                    error=str(error),
                )
            )
            raise

    async def timed_security() -> security_analysis_service.SecurityAnalysisResult:
        start = time.perf_counter()
        result = await security_analysis_service.analyze(db, normalized.normalized, normalized.host)
        steps.append(
            AnalysisStepOut(
                step="security_analysis", status="done", ms=(time.perf_counter() - start) * 1000
            )
        )
        return result

    try:
        ml_result, security_result = await asyncio.gather(timed_ml(), timed_security())
    except Exception as error:
        analysis_row.status = "failed"
        analysis_row.error = str(error)
        analysis_row.steps = [s.model_dump() for s in steps]
        await db.commit()
        return _to_out(
            analysis_row, url_row.normalized, ml_analysis=None, indicators=[], domain_info=None
        )

    domain_row = await domains_repo.get_by_registered_domain(db, security_result.registered_domain)
    scoring = scoring_service.score(ml_result.probability, security_result.indicators)

    analysis_row.status = "completed"
    analysis_row.domain_id = domain_row.id if domain_row else None
    analysis_row.risk_score = scoring.risk_score
    analysis_row.risk_level = scoring.risk_level
    analysis_row.classification = scoring.classification
    analysis_row.indicators = [asdict(i) for i in security_result.indicators]
    analysis_row.degraded = security_result.degraded
    analysis_row.steps = [s.model_dump() for s in steps]
    analysis_row.completed_at = datetime.now(UTC)

    await predictions_repo.create(
        db,
        analysis_id=analysis_row.id,
        model_name=ml_result.model_name,
        feature_schema_version=ml_result.feature_schema_version,
        artifact_sha256=ml_result.artifact_sha256,
        probability=ml_result.probability,
        threshold=ml_result.threshold,
        label=ml_result.label,
        top_contributions=[{"feature": f, "shap_value": v} for f, v in ml_result.top_contributions],
        latency_ms=ml_result.latency_ms,
    )
    await db.commit()

    ml_analysis = MlAnalysisOut(
        model_name=ml_result.model_name,
        probability=ml_result.probability,
        threshold=ml_result.threshold,
        label=ml_result.label,
        top_contributions=[
            FeatureContributionOut(feature=f, shap_value=v) for f, v in ml_result.top_contributions
        ],
        latency_ms=ml_result.latency_ms,
    )
    domain_info = DomainInfoOut(
        registered_domain=security_result.registered_domain,
        dns_records=[
            DnsRecordOut(record_type=rt, values=rec.values, error=rec.error)
            for rt, rec in security_result.dns_result.records.items()
        ],
        dns_resolved=security_result.dns_result.resolved,
        registrar=security_result.rdap_result.registrar,
        domain_created_at=security_result.rdap_result.created_at,
        domain_age_days=security_result.rdap_result.age_days,
        rdap_found=security_result.rdap_result.found,
        degraded=security_result.degraded,
    )
    indicators = [IndicatorOut(**asdict(i)) for i in security_result.indicators]

    return _to_out(analysis_row, url_row.normalized, ml_analysis, indicators, domain_info)


async def get_analysis(
    db: AsyncSession, *, analysis_id: uuid.UUID, user_id: uuid.UUID
) -> AnalysisOut:
    analysis_row = await analyses_repo.get_for_user(db, analysis_id=analysis_id, user_id=user_id)
    if analysis_row is None:
        raise AnalysisNotFoundError(str(analysis_id))

    prediction_row = await predictions_repo.get_by_analysis_id(db, analysis_id)
    ml_analysis = (
        MlAnalysisOut(
            model_name=prediction_row.model_name,
            probability=prediction_row.probability,
            threshold=prediction_row.threshold,
            label=prediction_row.label,
            top_contributions=[
                FeatureContributionOut(**c) for c in prediction_row.top_contributions
            ],
            latency_ms=prediction_row.latency_ms,
        )
        if prediction_row
        else None
    )
    indicators = [IndicatorOut(**i) for i in (analysis_row.indicators or [])]

    domain_info = None
    if analysis_row.domain_id is not None:
        domain_row = await domains_repo.get_by_id(db, analysis_row.domain_id)
        if domain_row is not None:
            domain_info = DomainInfoOut(
                registered_domain=domain_row.registered_domain,
                dns_records=[
                    DnsRecordOut(
                        record_type=rt, values=rec.get("values", []), error=rec.get("error")
                    )
                    for rt, rec in domain_row.dns_snapshot.items()
                ],
                dns_resolved=any(rec.get("values") for rec in domain_row.dns_snapshot.values()),
                registrar=domain_row.rdap_snapshot.get("registrar"),
                domain_created_at=domain_row.domain_created_at,
                domain_age_days=None,
                rdap_found=domain_row.rdap_snapshot.get("found", False),
                degraded=analysis_row.degraded,
            )

    return _to_out(analysis_row, analysis_row.url.normalized, ml_analysis, indicators, domain_info)


def _to_out(
    analysis_row: Analysis,
    url_text: str,
    ml_analysis: MlAnalysisOut | None,
    indicators: list[IndicatorOut],
    domain_info: DomainInfoOut | None,
) -> AnalysisOut:
    return AnalysisOut(
        id=analysis_row.id,
        url=url_text,
        status=analysis_row.status,
        mode=analysis_row.mode,
        steps=[AnalysisStepOut(**s) if isinstance(s, dict) else s for s in analysis_row.steps],
        risk_score=analysis_row.risk_score,
        risk_level=analysis_row.risk_level,
        classification=analysis_row.classification,
        degraded=analysis_row.degraded,
        error=analysis_row.error,
        ml_analysis=ml_analysis,
        indicators=indicators,
        domain_info=domain_info,
        created_at=analysis_row.created_at,
        completed_at=analysis_row.completed_at,
    )
