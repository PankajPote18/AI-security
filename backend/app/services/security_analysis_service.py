"""Structural indicators + DNS + RDAP + threat intelligence for one URL, with a Postgres-backed
cache (`domains`, `threat_intel_lookups`) so repeated analyses of the same registered domain or
URL within their respective TTLs skip a re-lookup.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.repositories import domains as domains_repo
from app.repositories import threat_intel as threat_intel_repo
from security_core.dns_lookup import DnsLookupResult, DnsRecordResult, lookup_dns
from security_core.hostnames import extractor
from security_core.indicators import Indicator, evaluate_indicators
from security_core.rdap_lookup import RdapResult, lookup_rdap
from security_core.threat_intel import ThreatIntelResult, ThreatIntelStatus, UrlhausProvider

CACHE_TTL = timedelta(hours=24)
THREAT_INTEL_CACHE_TTL = timedelta(hours=6)  # reputation data churns faster than domain WHOIS


@dataclass(frozen=True)
class SecurityAnalysisResult:
    registered_domain: str
    indicators: list[Indicator]
    dns_result: DnsLookupResult
    rdap_result: RdapResult
    threat_intel: list[ThreatIntelResult]
    degraded: bool
    from_cache: bool


def _dns_to_snapshot(result: DnsLookupResult) -> dict[str, Any]:
    return {rt: {"values": rec.values, "error": rec.error} for rt, rec in result.records.items()}


def _dns_from_snapshot(host: str, snapshot: dict[str, Any]) -> DnsLookupResult:
    records = {
        rt: DnsRecordResult(rt, values=rec.get("values", []), error=rec.get("error"))
        for rt, rec in snapshot.items()
    }
    return DnsLookupResult(host=host, records=records)


def _rdap_to_snapshot(result: RdapResult) -> dict[str, Any]:
    return {
        "found": result.found,
        "registrar": result.registrar,
        "created_at": result.created_at.isoformat() if result.created_at else None,
        "updated_at": result.updated_at.isoformat() if result.updated_at else None,
        "status": result.status,
        "error": result.error,
    }


def _rdap_from_snapshot(domain: str, snapshot: dict[str, Any]) -> RdapResult:
    created = snapshot.get("created_at")
    updated = snapshot.get("updated_at")
    return RdapResult(
        domain=domain,
        found=snapshot.get("found", False),
        registrar=snapshot.get("registrar"),
        created_at=datetime.fromisoformat(created) if created else None,
        updated_at=datetime.fromisoformat(updated) if updated else None,
        status=snapshot.get("status", []),
        error=snapshot.get("error"),
    )


def _threat_intel_provider() -> UrlhausProvider | None:
    auth_key = get_settings().urlhaus_auth_key
    return UrlhausProvider(auth_key=auth_key.get_secret_value()) if auth_key is not None else None


async def _lookup_threat_intel(db: AsyncSession, url: str, url_id: uuid.UUID) -> ThreatIntelResult:
    provider = _threat_intel_provider()
    if provider is None:
        return ThreatIntelResult(
            provider=UrlhausProvider.name, status="unavailable", error="not_configured"
        )

    cached = await threat_intel_repo.get_by_url_and_provider(
        db, url_id=url_id, provider=provider.name
    )
    now = datetime.now(UTC)
    if (
        cached is not None
        and (now - cached.fetched_at.replace(tzinfo=UTC)) < THREAT_INTEL_CACHE_TTL
    ):
        return ThreatIntelResult(
            provider=cached.provider,
            status=cast(ThreatIntelStatus, cached.status),
            threat_type=cached.threat_type,
            tags=cached.tags,
            reference_url=cached.reference_url,
            error=cached.error,
        )

    result = await provider.check_url(url)
    await threat_intel_repo.upsert(
        db,
        url_id=url_id,
        provider=result.provider,
        status=result.status,
        threat_type=result.threat_type,
        tags=result.tags,
        reference_url=result.reference_url,
        error=result.error,
        fetched_at=now,
    )
    return result


def _threat_intel_indicators(results: list[ThreatIntelResult]) -> list[Indicator]:
    """A URL a threat-intel feed has already observed in the wild is stronger evidence than any
    structural pattern - surfaced as a high-severity indicator so it flows through the same
    scoring, persistence and display path as `evaluate_indicators`'s output, rather than a
    parallel code path that scoring_service would need to know about separately."""
    indicators = []
    for result in results:
        if result.status != "listed":
            continue
        threat_label = result.threat_type or "malicious activity"
        tag_suffix = f" (tags: {', '.join(result.tags)})" if result.tags else ""
        indicators.append(
            Indicator(
                code="threat_intel_hit",
                severity="high",
                title=f"Listed in {result.provider} threat intelligence as {threat_label}",
                description=(
                    f"{result.provider} has this exact URL on record as {threat_label}"
                    f"{tag_suffix} - already observed in the wild, not just a structural pattern."
                ),
                mitre_technique=None,
            )
        )
    return indicators


async def _dns_and_rdap(host: str, registered_domain: str) -> tuple[DnsLookupResult, RdapResult]:
    return await asyncio.gather(lookup_dns(host), lookup_rdap(registered_domain))


async def analyze(
    db: AsyncSession, url: str, host: str, url_id: uuid.UUID
) -> SecurityAnalysisResult:
    indicators = evaluate_indicators(url)
    registered_domain = extractor(host).top_domain_under_public_suffix if host else host
    registered_domain = registered_domain or host

    cached = await domains_repo.get_by_registered_domain(db, registered_domain)
    now = datetime.now(UTC)
    is_fresh = cached is not None and (now - cached.refreshed_at.replace(tzinfo=UTC)) < CACHE_TTL

    if cached is not None and is_fresh and cached.rdap_snapshot:
        dns_result = _dns_from_snapshot(host, cached.dns_snapshot)
        rdap_result = _rdap_from_snapshot(registered_domain, cached.rdap_snapshot)
        threat_intel_result = await _lookup_threat_intel(db, url, url_id)
        from_cache = True
    else:
        (dns_result, rdap_result), threat_intel_result = await asyncio.gather(
            _dns_and_rdap(host, registered_domain), _lookup_threat_intel(db, url, url_id)
        )
        await domains_repo.upsert_snapshot(
            db,
            registered_domain=registered_domain,
            dns_snapshot=_dns_to_snapshot(dns_result),
            rdap_snapshot=_rdap_to_snapshot(rdap_result),
            domain_created_at=rdap_result.created_at,
            refreshed_at=now,
        )
        from_cache = False

    indicators = indicators + _threat_intel_indicators([threat_intel_result])
    # "unavailable because the feature isn't configured" is not a degraded lookup - only an
    # actual failure (timeout, rate limit, HTTP error) of a provider that IS configured is.
    ti_unavailable = threat_intel_result.status == "unavailable" and threat_intel_result.error != (
        "not_configured"
    )
    degraded = dns_result.degraded or bool(rdap_result.error) or ti_unavailable

    return SecurityAnalysisResult(
        registered_domain,
        indicators,
        dns_result,
        rdap_result,
        [threat_intel_result],
        degraded,
        from_cache,
    )
