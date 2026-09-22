"""Unit tests for the pure logic behind each MCP tool. DNS/RDAP/threat-intel network calls are
mocked (no live network in CI, matching the backend's own test suite); the ML prediction and
knowledge-base search run for real against this checkout's trained artifact and ingested KB.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from copilot_mcp import service
from security_core.dns_lookup import DnsLookupResult, DnsRecordResult
from security_core.rdap_lookup import RdapResult
from security_core.threat_intel import ThreatIntelResult

pytestmark = pytest.mark.asyncio


async def test_analyze_url_returns_a_full_result_for_a_clean_url() -> None:
    result = await service.analyze_url("https://www.example.com/")
    assert result.url == "https://www.example.com/"
    assert 0 <= result.risk_score <= 100
    assert result.risk_level in {"low", "medium", "high"}
    assert result.classification in {"likely_legitimate", "suspicious", "likely_phishing"}
    assert 0 <= result.ml_probability <= 1
    assert result.ml_model_name


async def test_analyze_url_rejects_a_disallowed_scheme() -> None:
    with pytest.raises(service.InvalidInputError):
        await service.analyze_url("javascript:alert(1)")


async def test_analyze_url_flags_an_ip_host_as_a_high_severity_indicator() -> None:
    result = await service.analyze_url("http://192.168.1.1/login")
    assert any(i.code == "ip_host" and i.severity == "high" for i in result.indicators)


async def test_lookup_dns_records_shapes_the_result() -> None:
    fake_result = DnsLookupResult(
        host="example.com",
        records={
            "A": DnsRecordResult("A", values=["93.184.216.34"]),
            "AAAA": DnsRecordResult("AAAA", values=[]),
            "MX": DnsRecordResult("MX", values=[], error="no_answer"),
        },
    )
    with patch("copilot_mcp.service.lookup_dns", new=AsyncMock(return_value=fake_result)):
        result = await service.lookup_dns_records("example.com")

    assert result.host == "example.com"
    assert result.resolved is True
    a_record = next(r for r in result.records if r.record_type == "A")
    assert a_record.values == ["93.184.216.34"]


async def test_check_domain_shapes_the_result() -> None:
    fake_result = RdapResult(
        domain="example.com", found=True, registrar="Example Registrar", status=["active"]
    )
    with patch("copilot_mcp.service.lookup_rdap", new=AsyncMock(return_value=fake_result)):
        result = await service.check_domain("example.com")

    assert result.found is True
    assert result.registrar == "Example Registrar"
    assert result.status == ["active"]


async def test_check_domain_reports_not_found() -> None:
    fake_result = RdapResult(domain="never-registered.example", found=False)
    with patch("copilot_mcp.service.lookup_rdap", new=AsyncMock(return_value=fake_result)):
        result = await service.check_domain("never-registered.example")

    assert result.found is False
    assert result.registrar is None


async def test_threat_lookup_degrades_to_unavailable_when_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("URLHAUS_AUTH_KEY", raising=False)
    result = await service.threat_lookup("https://example.com/")
    assert result.status == "unavailable"
    assert result.error == "not_configured"


async def test_threat_lookup_reports_a_listed_url() -> None:
    fake_result = ThreatIntelResult(
        provider="urlhaus", status="listed", threat_type="malware_download", tags=["emotet"]
    )
    fake_provider = MagicMock()
    fake_provider.check_url = AsyncMock(return_value=fake_result)

    with patch("copilot_mcp.service._threat_intel_provider", return_value=fake_provider):
        result = await service.threat_lookup("https://evil.example/payload")

    assert result.status == "listed"
    assert result.threat_type == "malware_download"
    assert result.tags == ["emotet"]


async def test_search_security_knowledge_returns_relevant_passages() -> None:
    results = await service.search_security_knowledge(
        "how to detect phishing lookalike domains", top_k=3
    )
    assert 0 < len(results) <= 3
    assert all(r.chunk_id and r.text for r in results)
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)
