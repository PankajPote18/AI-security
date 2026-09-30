"""`POST /analyze/url?mode=deep`. The agent itself is mocked (its own tests live in
`unit/test_security_agent.py`); this covers the API contract: 202 + immediate `running` row, the
background task persisting the result, failure degradation, and the shared polling shape.

httpx's ASGITransport runs FastAPI background tasks before `client.post` returns, so by the time
the response is in hand the background work has finished. The background task normally opens its
own session from the dev engine; tests point it at the test database instead.
"""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import AsyncMock, patch

import pytest
from app.agents.security_agent import AgentError, DeepAnalysisResult, ToolCallTrace
from app.llm.schemas import IndicatorExplanation, SecurityReportLLMOutput
from httpx import AsyncClient

from tests.conftest import _TestSessionFactory

_URL_ANALYSIS = {
    "url": "https://example.com/login",
    "risk_score": 77.5,
    "risk_level": "high",
    "classification": "likely_phishing",
    "ml_probability": 0.9,
    "ml_model_name": "test-model",
    "indicators": [
        {
            "code": "ip_host",
            "severity": "high",
            "title": "Host is a raw IP address",
            "description": "d",
            "mitre_technique": "T1583.001",
        }
    ],
}


@pytest.fixture(autouse=True)
def _test_db_for_background_task() -> Iterator[None]:
    with patch("app.services.deep_analysis_service.async_session_factory", new=_TestSessionFactory):
        yield


def _result(report: SecurityReportLLMOutput | None) -> DeepAnalysisResult:
    return DeepAnalysisResult(
        url_analysis=_URL_ANALYSIS,
        report=report,
        trace=[
            ToolCallTrace("analyze_url", "success", {"url": "https://example.com/login"}),
            ToolCallTrace("lookup_dns", "success", {"host": "example.com"}),
        ],
    )


async def test_deep_mode_returns_202_with_a_running_analysis(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    with patch(
        "app.services.deep_analysis_service.run_deep_analysis",
        new=AsyncMock(return_value=_result(None)),
    ):
        response = await client.post(
            "/api/v1/analyze/url?mode=deep",
            json={"url": "https://example.com/login"},
            headers=auth_headers,
        )

    assert response.status_code == 202
    body = response.json()
    assert body["mode"] == "deep"
    assert body["status"] == "running"
    assert body["risk_score"] is None


async def test_deep_analysis_result_is_persisted_and_pollable(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    report = SecurityReportLLMOutput(
        summary="Raw IP host suggests throwaway infrastructure.",
        indicator_explanations=[
            IndicatorExplanation(indicator_code="ip_host", explanation="Raw IP.", source_numbers=[])
        ],
        recommendations=["Do not enter credentials."],
    )
    with patch(
        "app.services.deep_analysis_service.run_deep_analysis",
        new=AsyncMock(return_value=_result(report)),
    ):
        created = await client.post(
            "/api/v1/analyze/url?mode=deep",
            json={"url": "https://example.com/login"},
            headers=auth_headers,
        )
    analysis_id = created.json()["id"]

    polled = await client.get(f"/api/v1/analyses/{analysis_id}", headers=auth_headers)
    body = polled.json()
    assert body["status"] == "completed"
    assert body["risk_score"] == 77.5
    assert body["classification"] == "likely_phishing"
    assert body["indicators"][0]["code"] == "ip_host"
    assert body["ml_analysis"] is None  # deep mode stores no Prediction row
    steps = [s["step"] for s in body["steps"]]
    assert steps == ["agent", "tool:analyze_url", "tool:lookup_dns"]

    report_response = await client.get(
        f"/api/v1/analyses/{analysis_id}/report", headers=auth_headers
    )
    assert report_response.status_code == 200
    assert report_response.json()["status"] == "completed"
    assert report_response.json()["summary"].startswith("Raw IP host")


async def test_agent_failure_marks_the_analysis_failed_not_a_500(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    with patch(
        "app.services.deep_analysis_service.run_deep_analysis",
        new=AsyncMock(side_effect=AgentError("agent invocation failed: HF_TOKEN is not set")),
    ):
        created = await client.post(
            "/api/v1/analyze/url?mode=deep",
            json={"url": "https://example.com/"},
            headers=auth_headers,
        )
    assert created.status_code == 202

    polled = await client.get(f"/api/v1/analyses/{created.json()['id']}", headers=auth_headers)
    body = polled.json()
    assert body["status"] == "failed"
    assert "HF_TOKEN" in body["error"]


async def test_a_missing_structured_report_still_completes_the_analysis(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    with patch(
        "app.services.deep_analysis_service.run_deep_analysis",
        new=AsyncMock(return_value=_result(None)),
    ):
        created = await client.post(
            "/api/v1/analyze/url?mode=deep",
            json={"url": "https://example.com/"},
            headers=auth_headers,
        )
    analysis_id = created.json()["id"]

    assert (await client.get(f"/api/v1/analyses/{analysis_id}", headers=auth_headers)).json()[
        "status"
    ] == "completed"
    report = await client.get(f"/api/v1/analyses/{analysis_id}/report", headers=auth_headers)
    assert report.json()["status"] == "failed"


async def test_deep_mode_rejects_an_invalid_url(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/analyze/url?mode=deep", json={"url": "javascript:alert(1)"}, headers=auth_headers
    )
    assert response.status_code == 422


async def test_an_unknown_mode_is_rejected(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/analyze/url?mode=bogus", json={"url": "https://example.com/"}, headers=auth_headers
    )
    assert response.status_code == 422
