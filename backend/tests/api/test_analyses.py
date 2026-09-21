"""End-to-end `/analyze/url` tests. DNS/RDAP are mocked (no live network in tests); the ML model
is the real exported Stage 1 artifact, so this is the one place with true end-to-end confidence
that `ml_service`, `security_analysis_service` and `scoring_service` actually compose correctly.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from security_core.dns_lookup import DnsLookupResult, DnsRecordResult
from security_core.rdap_lookup import RdapResult


def _fake_dns(host: str) -> DnsLookupResult:
    return DnsLookupResult(
        host=host,
        records={
            "A": DnsRecordResult("A", values=["93.184.216.34"]),
            "AAAA": DnsRecordResult("AAAA", values=[]),
            "MX": DnsRecordResult("MX", values=[], error="no_answer"),
            "NS": DnsRecordResult("NS", values=["ns1.example.com."]),
            "TXT": DnsRecordResult("TXT", values=[]),
        },
    )


def _fake_rdap(domain: str) -> RdapResult:
    return RdapResult(domain=domain, found=True, registrar="Example Registrar", status=["active"])


@pytest.fixture(autouse=True)
async def _mock_dns_and_rdap() -> AsyncIterator[None]:
    async def fake_lookup_dns(host: str, *args: object, **kwargs: object) -> DnsLookupResult:
        return _fake_dns(host)

    async def fake_lookup_rdap(domain: str, *args: object, **kwargs: object) -> RdapResult:
        return _fake_rdap(domain)

    with (
        patch(
            "app.services.security_analysis_service.lookup_dns",
            new=AsyncMock(side_effect=fake_lookup_dns),
        ),
        patch(
            "app.services.security_analysis_service.lookup_rdap",
            new=AsyncMock(side_effect=fake_lookup_rdap),
        ),
    ):
        yield


async def _register_and_login(client: AsyncClient, email: str) -> dict[str, str]:
    password = "a-reasonably-long-password"  # noqa: S105 - test fixture, not a real credential
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.mark.asyncio
async def test_analyze_a_clean_url_returns_a_full_report(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/analyze/url", json={"url": "https://www.example.com/"}, headers=auth_headers
    )
    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "completed"
    assert 0 <= body["risk_score"] <= 100
    assert body["risk_level"] in {"low", "medium", "high"}
    assert body["classification"] in {"likely_legitimate", "suspicious", "likely_phishing"}
    assert body["ml_analysis"]["model_name"]
    assert 0 <= body["ml_analysis"]["probability"] <= 1
    assert body["domain_info"]["registered_domain"] == "example.com"
    assert body["domain_info"]["registrar"] == "Example Registrar"
    assert isinstance(body["indicators"], list)
    assert body["degraded"] is False


@pytest.mark.asyncio
async def test_analyze_persists_and_is_retrievable(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    created = await client.post(
        "/api/v1/analyze/url", json={"url": "https://example.com/"}, headers=auth_headers
    )
    analysis_id = created.json()["id"]

    fetched = await client.get(f"/api/v1/analyses/{analysis_id}", headers=auth_headers)
    assert fetched.status_code == 200
    assert fetched.json()["id"] == analysis_id
    assert (
        fetched.json()["ml_analysis"]["model_name"] == created.json()["ml_analysis"]["model_name"]
    )


@pytest.mark.asyncio
async def test_analyze_appears_in_the_users_history(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await client.post(
        "/api/v1/analyze/url", json={"url": "https://one.example.com/"}, headers=auth_headers
    )
    await client.post(
        "/api/v1/analyze/url", json={"url": "https://two.example.com/"}, headers=auth_headers
    )

    listing = await client.get("/api/v1/analyses", headers=auth_headers)
    assert listing.status_code == 200
    urls = {row["url"] for row in listing.json()}
    assert urls == {"https://one.example.com/", "https://two.example.com/"}


@pytest.mark.asyncio
async def test_a_user_cannot_read_another_users_analysis(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    created = await client.post(
        "/api/v1/analyze/url", json={"url": "https://example.com/"}, headers=auth_headers
    )
    analysis_id = created.json()["id"]
    other_headers = await _register_and_login(client, "other@example.com")

    response = await client.get(f"/api/v1/analyses/{analysis_id}", headers=other_headers)
    assert response.status_code == 404  # not 403: existence of the id is not revealed either


@pytest.mark.asyncio
async def test_unknown_analysis_id_is_404(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.get(f"/api/v1/analyses/{uuid.uuid4()}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_disallowed_scheme_is_rejected(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/analyze/url", json={"url": "javascript:alert(1)"}, headers=auth_headers
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_sql_injection_style_payload_is_handled_safely(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    payload = "https://example.com/'; DROP TABLE users; --"
    response = await client.post("/api/v1/analyze/url", json={"url": payload}, headers=auth_headers)
    assert response.status_code == 200  # a weird but *valid* URL - analysed, not rejected

    # the users table must still exist and still contain this request's own history
    listing = await client.get("/api/v1/analyses", headers=auth_headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1


@pytest.mark.asyncio
async def test_oversized_url_is_rejected(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    huge = "https://example.com/" + "a" * 5000
    response = await client.post("/api/v1/analyze/url", json={"url": huge}, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_feedback_round_trips(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    created = await client.post(
        "/api/v1/analyze/url", json={"url": "https://example.com/"}, headers=auth_headers
    )
    analysis_id = created.json()["id"]

    response = await client.post(
        f"/api/v1/analyses/{analysis_id}/feedback",
        json={"verdict": "agree", "comment": "looks right"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["verdict"] == "agree"


@pytest.mark.asyncio
async def test_feedback_with_invalid_verdict_is_rejected(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    created = await client.post(
        "/api/v1/analyze/url", json={"url": "https://example.com/"}, headers=auth_headers
    )
    analysis_id = created.json()["id"]

    response = await client.post(
        f"/api/v1/analyses/{analysis_id}/feedback", json={"verdict": "maybe"}, headers=auth_headers
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_feedback_on_missing_analysis_is_404(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        f"/api/v1/analyses/{uuid.uuid4()}/feedback", json={"verdict": "agree"}, headers=auth_headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_current_model_endpoint_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/models/current")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_current_model_endpoint_returns_model_metadata(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.get("/api/v1/models/current", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["model_name"]
    assert body["feature_view"] == "host"
