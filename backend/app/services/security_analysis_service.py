"""Structural indicators + DNS + RDAP for one URL, with a Postgres-backed cache (`domains`
table) so repeated analyses of the same registered domain within `CACHE_TTL` skip a re-lookup.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import domains as domains_repo
from security_core.dns_lookup import DnsLookupResult, DnsRecordResult, lookup_dns
from security_core.hostnames import extractor
from security_core.indicators import Indicator, evaluate_indicators
from security_core.rdap_lookup import RdapResult, lookup_rdap

CACHE_TTL = timedelta(hours=24)


@dataclass(frozen=True)
class SecurityAnalysisResult:
    registered_domain: str
    indicators: list[Indicator]
    dns_result: DnsLookupResult
    rdap_result: RdapResult
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


async def analyze(db: AsyncSession, url: str, host: str) -> SecurityAnalysisResult:
    indicators = evaluate_indicators(url)
    registered_domain = extractor(host).top_domain_under_public_suffix if host else host
    registered_domain = registered_domain or host

    cached = await domains_repo.get_by_registered_domain(db, registered_domain)
    now = datetime.now(UTC)
    is_fresh = cached is not None and (now - cached.refreshed_at.replace(tzinfo=UTC)) < CACHE_TTL

    if cached is not None and is_fresh and cached.rdap_snapshot:
        dns_result = _dns_from_snapshot(host, cached.dns_snapshot)
        rdap_result = _rdap_from_snapshot(registered_domain, cached.rdap_snapshot)
        degraded = dns_result.degraded or bool(rdap_result.error)
        return SecurityAnalysisResult(
            registered_domain, indicators, dns_result, rdap_result, degraded, from_cache=True
        )

    dns_result, rdap_result = await asyncio.gather(lookup_dns(host), lookup_rdap(registered_domain))
    await domains_repo.upsert_snapshot(
        db,
        registered_domain=registered_domain,
        dns_snapshot=_dns_to_snapshot(dns_result),
        rdap_snapshot=_rdap_to_snapshot(rdap_result),
        domain_created_at=rdap_result.created_at,
        refreshed_at=now,
    )
    degraded = dns_result.degraded or bool(rdap_result.error)
    return SecurityAnalysisResult(
        registered_domain, indicators, dns_result, rdap_result, degraded, from_cache=False
    )
