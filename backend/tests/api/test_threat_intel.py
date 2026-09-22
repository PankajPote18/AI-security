"""Threat-intelligence evidence on `/analyze/url`. DNS/RDAP are mocked (same fixture as
`test_analyses.py`); URLhaus is mocked via `_threat_intel_provider` so no live network call is
ever made and the test controls exactly what the provider reports. The one exception is
`test_threat_intel_defaults_to_unavailable_when_not_configured`, which relies on the real,
current local/CI state of not having `URLHAUS_AUTH_KEY` set - the actual graceful-degradation
path a developer without a key sees today.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.core.config import get_settings
from httpx import AsyncClient

from security_core.dns_lookup import DnsLookupResult, DnsRecordResult
from security_core.rdap_lookup import RdapResult
from security_core.threat_intel import ThreatIntelResult

pytestmark = pytest.mark.asyncio


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


@pytest.fixture
def _mock_threat_intel(request: pytest.FixtureRequest) -> AsyncIterator[MagicMock]:
    result: ThreatIntelResult = request.param
    provider = MagicMock()
    provider.name = result.provider
    provider.check_url = AsyncMock(return_value=result)

    with patch(
        "app.services.security_analysis_service._threat_intel_provider", return_value=provider
    ):
        yield provider


async def test_threat_intel_defaults_to_unavailable_when_not_configured(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    assert get_settings().urlhaus_auth_key is None  # the real, current local state - not mocked

    response = await client.post(
        "/api/v1/analyze/url", json={"url": "https://example.com/"}, headers=auth_headers
    )
    assert response.status_code == 200
    body = response.json()

    assert body["threat_intelligence"] == [
        {
            "provider": "urlhaus",
            "status": "unavailable",
            "threat_type": None,
            "tags": [],
            "reference_url": None,
            "error": "not_configured",
        }
    ]
    # an optional feature simply not being configured is not itself a degraded analysis
    assert body["degraded"] is False


@pytest.mark.parametrize(
    "_mock_threat_intel",
    [
        ThreatIntelResult(
            provider="urlhaus",
            status="listed",
            threat_type="malware_download",
            tags=["phishing", "emotet"],
            reference_url="https://urlhaus.abuse.ch/url/12345/",
        )
    ],
    indirect=True,
)
async def test_a_listed_url_adds_a_high_severity_indicator(
    client: AsyncClient, auth_headers: dict[str, str], _mock_threat_intel: MagicMock
) -> None:
    # The score impact of a "high" severity indicator is covered by scoring_service's own unit
    # tests; this only checks the URLhaus hit is wired through to a real indicator, not silently
    # dropped, and doesn't get miscategorised as a degraded lookup.
    response = await client.post(
        "/api/v1/analyze/url", json={"url": "https://example.com/"}, headers=auth_headers
    )
    assert response.status_code == 200
    body = response.json()

    assert body["threat_intelligence"] == [
        {
            "provider": "urlhaus",
            "status": "listed",
            "threat_type": "malware_download",
            "tags": ["phishing", "emotet"],
            "reference_url": "https://urlhaus.abuse.ch/url/12345/",
            "error": None,
        }
    ]
    assert any(
        i["code"] == "threat_intel_hit" and i["severity"] == "high" for i in body["indicators"]
    )
    assert body["degraded"] is False  # a real verdict, not a provider failure


@pytest.mark.parametrize(
    "_mock_threat_intel",
    [ThreatIntelResult(provider="urlhaus", status="not_listed")],
    indirect=True,
)
async def test_a_clean_url_adds_no_indicator(
    client: AsyncClient, auth_headers: dict[str, str], _mock_threat_intel: MagicMock
) -> None:
    response = await client.post(
        "/api/v1/analyze/url", json={"url": "https://example.com/"}, headers=auth_headers
    )
    body = response.json()

    assert body["threat_intelligence"][0]["status"] == "not_listed"
    assert not any(i["code"] == "threat_intel_hit" for i in body["indicators"])
    assert body["degraded"] is False


@pytest.mark.parametrize(
    "_mock_threat_intel",
    [ThreatIntelResult(provider="urlhaus", status="unavailable", error="timeout")],
    indirect=True,
)
async def test_a_configured_but_failing_provider_marks_the_analysis_degraded(
    client: AsyncClient, auth_headers: dict[str, str], _mock_threat_intel: MagicMock
) -> None:
    response = await client.post(
        "/api/v1/analyze/url", json={"url": "https://example.com/"}, headers=auth_headers
    )
    body = response.json()

    assert body["threat_intelligence"][0] == {
        "provider": "urlhaus",
        "status": "unavailable",
        "threat_type": None,
        "tags": [],
        "reference_url": None,
        "error": "timeout",
    }
    assert body["degraded"] is True


@pytest.mark.parametrize(
    "_mock_threat_intel",
    [ThreatIntelResult(provider="urlhaus", status="not_listed")],
    indirect=True,
)
async def test_the_verdict_is_cached_and_not_refetched_within_the_ttl(
    client: AsyncClient, auth_headers: dict[str, str], _mock_threat_intel: MagicMock
) -> None:
    url = "https://example.com/repeat-check"
    first = await client.post("/api/v1/analyze/url", json={"url": url}, headers=auth_headers)
    second = await client.post("/api/v1/analyze/url", json={"url": url}, headers=auth_headers)

    assert first.status_code == second.status_code == 200
    assert _mock_threat_intel.check_url.await_count == 1
    assert second.json()["threat_intelligence"][0]["status"] == "not_listed"
