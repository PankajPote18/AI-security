import uuid
from datetime import UTC, datetime

from app.schemas.analysis import AnalysisOut
from app.schemas.evidence import IndicatorOut
from app.services.report_service import _build_retrieval_query


def _analysis(classification: str | None, indicators: list[IndicatorOut]) -> AnalysisOut:
    return AnalysisOut(
        id=uuid.uuid4(),
        url="https://example.com/",
        status="completed",
        mode="standard",
        steps=[],
        risk_score=42.0,
        risk_level="medium",
        classification=classification,
        degraded=False,
        error=None,
        ml_analysis=None,
        indicators=indicators,
        domain_info=None,
        created_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )


def _indicator(title: str, mitre_technique: str | None = None) -> IndicatorOut:
    return IndicatorOut(
        code="x", severity="medium", title=title, description="d", mitre_technique=mitre_technique
    )


def test_query_includes_classification_and_indicator_titles() -> None:
    analysis = _analysis(
        "likely_phishing",
        [_indicator("IP address used as host"), _indicator("Suspicious keyword in path")],
    )
    query = _build_retrieval_query(analysis)
    assert "likely_phishing" in query
    assert "IP address used as host" in query
    assert "Suspicious keyword in path" in query


def test_query_includes_mitre_technique_when_present() -> None:
    analysis = _analysis("suspicious", [_indicator("Malicious link", mitre_technique="T1204.001")])
    query = _build_retrieval_query(analysis)
    assert "T1204.001" in query


def test_query_with_no_classification_and_no_indicators_is_empty_string() -> None:
    analysis = _analysis(None, [])
    assert _build_retrieval_query(analysis) == ""


def test_query_skips_missing_mitre_technique_without_error() -> None:
    analysis = _analysis("likely_legitimate", [_indicator("No indicators fired")])
    query = _build_retrieval_query(analysis)
    assert query == "likely_legitimate No indicators fired"
