"""`/analyses/{id}/report` and `/knowledge/search`. No live LLM call is ever made here: the
success path mocks `get_chat_model`, and the degradation-path test relies on the real, current
local setup having no `HF_TOKEN` configured (see `app/llm/client.py`) rather than mocking it -
that is the actual graceful-degradation behaviour a developer without a token sees today.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.core.config import get_settings
from app.llm.schemas import IndicatorExplanation, SecurityReportLLMOutput
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def _analyze(client: AsyncClient, headers: dict[str, str]) -> str:
    response = await client.post(
        "/api/v1/analyze/url", json={"url": "https://example.com/login"}, headers=headers
    )
    assert response.status_code == 200
    return response.json()["id"]


def _fake_llm_output(*, source_numbers: list[int]) -> SecurityReportLLMOutput:
    return SecurityReportLLMOutput(
        summary="This URL shows a low-confidence phishing signal.",
        indicator_explanations=[
            IndicatorExplanation(
                indicator_code="x",
                explanation="Explained with grounding.",
                source_numbers=source_numbers,
            )
        ],
        recommendations=["Verify the sender before entering credentials."],
    )


@pytest.fixture
def _mock_chat_model(request: pytest.FixtureRequest) -> AsyncIterator[MagicMock]:
    source_numbers = getattr(request, "param", [1])
    envelope = {
        "raw": MagicMock(usage_metadata={"input_tokens": 123, "output_tokens": 45}),
        "parsed": _fake_llm_output(source_numbers=source_numbers),
        "parsing_error": None,
    }
    structured_model = MagicMock()
    structured_model.ainvoke = AsyncMock(return_value=envelope)

    chat_model = MagicMock()
    chat_model.model_name = "openai/gpt-oss-20b"
    chat_model.with_structured_output.return_value = structured_model

    with patch("app.services.report_service.get_chat_model", return_value=chat_model):
        yield chat_model


async def test_report_degrades_gracefully_when_the_llm_is_not_configured(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    assert get_settings().hf_token is None  # the real, current local state - not mocked

    analysis_id = await _analyze(client, auth_headers)
    response = await client.post(f"/api/v1/analyses/{analysis_id}/report", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert body["error"] == "HF_TOKEN is not set"
    assert body["summary"] is None
    # retrieval itself ran and succeeded even though the LLM call could not be made
    assert len(body["sources"]) > 0


async def test_getting_a_report_that_was_never_generated_is_404(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    analysis_id = await _analyze(client, auth_headers)
    response = await client.get(f"/api/v1/analyses/{analysis_id}/report", headers=auth_headers)
    assert response.status_code == 404


async def test_report_on_unknown_analysis_is_404(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(f"/api/v1/analyses/{uuid.uuid4()}/report", headers=auth_headers)
    assert response.status_code == 404


async def test_a_user_cannot_generate_a_report_for_another_users_analysis(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    analysis_id = await _analyze(client, auth_headers)

    password = "a-reasonably-long-password"  # noqa: S105 - test fixture, not a real credential
    await client.post(
        "/api/v1/auth/register", json={"email": "other@example.com", "password": password}
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": "other@example.com", "password": password}
    )
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = await client.post(f"/api/v1/analyses/{analysis_id}/report", headers=other_headers)
    assert response.status_code == 404


@pytest.mark.usefixtures("_mock_chat_model")
async def test_report_generation_succeeds_with_a_mocked_llm(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    analysis_id = await _analyze(client, auth_headers)
    response = await client.post(f"/api/v1/analyses/{analysis_id}/report", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["provider"] == "huggingface"
    assert body["model_name"] == "openai/gpt-oss-20b"
    assert body["summary"] == "This URL shows a low-confidence phishing signal."
    assert body["recommendations"] == ["Verify the sender before entering credentials."]
    assert body["indicator_explanations"][0]["source_numbers"] == [1]


@pytest.mark.usefixtures("_mock_chat_model")
async def test_generated_report_is_retrievable_afterwards(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    analysis_id = await _analyze(client, auth_headers)
    await client.post(f"/api/v1/analyses/{analysis_id}/report", headers=auth_headers)

    response = await client.get(f"/api/v1/analyses/{analysis_id}/report", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


@pytest.mark.parametrize("_mock_chat_model", [[1, 999, -3]], indirect=True)
async def test_citation_numbers_outside_the_retrieved_sources_are_dropped(
    client: AsyncClient, auth_headers: dict[str, str], _mock_chat_model: MagicMock
) -> None:
    analysis_id = await _analyze(client, auth_headers)
    response = await client.post(f"/api/v1/analyses/{analysis_id}/report", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    source_numbers = body["indicator_explanations"][0]["source_numbers"]
    assert 999 not in source_numbers
    assert -3 not in source_numbers
    assert all(1 <= n <= len(body["sources"]) for n in source_numbers)


async def test_knowledge_search_requires_auth(client: AsyncClient) -> None:
    response = await client.post("/api/v1/knowledge/search", json={"query": "phishing"})
    assert response.status_code in (401, 403)


async def test_knowledge_search_returns_relevant_sources(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    # Ranking quality itself is covered by evals/rag (hit@k, MRR); this only checks that the
    # endpoint is wired to real retrieval and returns well-formed, sensibly ordered results.
    response = await client.post(
        "/api/v1/knowledge/search",
        json={"query": "how to detect phishing lookalike domains", "top_k": 3},
        headers=auth_headers,
    )
    assert response.status_code == 200
    results = response.json()
    assert 0 < len(results) <= 3
    assert all(r["chunk_id"] and r["topic"] for r in results)
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)


async def test_knowledge_search_rejects_an_empty_query(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/knowledge/search", json={"query": ""}, headers=auth_headers
    )
    assert response.status_code == 422
