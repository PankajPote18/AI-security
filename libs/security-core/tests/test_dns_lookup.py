"""Mocks `dns.asyncresolver.Resolver.resolve` so these tests never touch the network."""

from unittest.mock import AsyncMock, patch

import dns.exception
import dns.resolver
import pytest

from security_core.dns_lookup import DnsLookupResult, lookup_dns


class _FakeAnswer(list):
    """Stands in for a dnspython Answer: iterating it yields record-like objects."""


@pytest.mark.asyncio
async def test_successful_lookup_collects_values_for_every_record_type() -> None:
    async def fake_resolve(host: str, record_type: str, lifetime: float) -> _FakeAnswer:
        return _FakeAnswer([f"{record_type}-value-1", f"{record_type}-value-2"])

    with patch("dns.asyncresolver.Resolver.resolve", new=AsyncMock(side_effect=fake_resolve)):
        result = await lookup_dns("example.com", record_types=("A", "MX"))

    assert result.host == "example.com"
    assert result.records["A"].values == ["A-value-1", "A-value-2"]
    assert result.records["A"].error is None
    assert result.resolved
    assert not result.degraded


@pytest.mark.asyncio
async def test_nxdomain_is_reported_without_marking_degraded() -> None:
    async def fake_resolve(host: str, record_type: str, lifetime: float) -> _FakeAnswer:
        raise dns.resolver.NXDOMAIN()

    with patch("dns.asyncresolver.Resolver.resolve", new=AsyncMock(side_effect=fake_resolve)):
        result = await lookup_dns("does-not-exist.invalid", record_types=("A",))

    assert result.records["A"].error == "NXDOMAIN"
    assert result.records["A"].values == []
    assert not result.resolved
    assert not result.degraded  # NXDOMAIN is a real, conclusive answer, not a failure


@pytest.mark.asyncio
async def test_timeout_is_reported_and_marks_degraded() -> None:
    async def fake_resolve(host: str, record_type: str, lifetime: float) -> _FakeAnswer:
        raise dns.exception.Timeout()

    with patch("dns.asyncresolver.Resolver.resolve", new=AsyncMock(side_effect=fake_resolve)):
        result = await lookup_dns("slow.example", record_types=("A",))

    assert result.records["A"].error == "timeout"
    assert result.degraded


@pytest.mark.asyncio
async def test_no_answer_is_not_an_error_and_not_degraded() -> None:
    async def fake_resolve(host: str, record_type: str, lifetime: float) -> _FakeAnswer:
        raise dns.resolver.NoAnswer()

    with patch("dns.asyncresolver.Resolver.resolve", new=AsyncMock(side_effect=fake_resolve)):
        result = await lookup_dns("example.com", record_types=("TXT",))

    assert result.records["TXT"].error == "no_answer"
    assert not result.degraded


@pytest.mark.asyncio
async def test_all_record_types_are_queried_concurrently_and_independently() -> None:
    calls: list[str] = []

    async def fake_resolve(host: str, record_type: str, lifetime: float) -> _FakeAnswer:
        calls.append(record_type)
        if record_type == "MX":
            raise dns.resolver.NoAnswer()
        return _FakeAnswer([f"{record_type}-ok"])

    with patch("dns.asyncresolver.Resolver.resolve", new=AsyncMock(side_effect=fake_resolve)):
        result: DnsLookupResult = await lookup_dns("example.com")

    assert set(calls) == set(result.records)
    assert result.records["MX"].error == "no_answer"
    assert result.records["A"].values == ["A-ok"]
