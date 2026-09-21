"""Asynchronous DNS lookups (A/AAAA/MX/NS/TXT), run concurrently, with a per-query timeout.

A lookup failure never raises past this module: it is reported as an empty result plus an
`error` code, so callers (`analysis_service`) can mark an analysis `degraded` instead of failing
the whole request because one DNS record type timed out.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

import dns.asyncresolver
import dns.exception
import dns.resolver

DEFAULT_TIMEOUT_SECONDS = 3.0
RECORD_TYPES: tuple[str, ...] = ("A", "AAAA", "MX", "NS", "TXT")


@dataclass(frozen=True)
class DnsRecordResult:
    record_type: str
    values: list[str] = field(default_factory=list)
    error: str | None = None  # None = success (values may still be empty for NoAnswer)


@dataclass(frozen=True)
class DnsLookupResult:
    host: str
    records: dict[str, DnsRecordResult]

    @property
    def resolved(self) -> bool:
        return any(record.values for record in self.records.values())

    @property
    def degraded(self) -> bool:
        """True if a query failed for a reason other than "no such record type"."""
        return any(
            record.error not in (None, "NXDOMAIN", "no_answer") for record in self.records.values()
        )


async def _lookup_one(
    resolver: dns.asyncresolver.Resolver, host: str, record_type: str, timeout: float
) -> DnsRecordResult:
    try:
        answer = await resolver.resolve(host, record_type, lifetime=timeout)
    except dns.resolver.NXDOMAIN:
        return DnsRecordResult(record_type, error="NXDOMAIN")
    except dns.resolver.NoAnswer:
        return DnsRecordResult(record_type, error="no_answer")
    except (dns.resolver.LifetimeTimeout, dns.exception.Timeout):
        return DnsRecordResult(record_type, error="timeout")
    except dns.resolver.NoNameservers:
        return DnsRecordResult(record_type, error="no_nameservers")
    except dns.exception.DNSException as error:
        return DnsRecordResult(record_type, error=type(error).__name__)
    return DnsRecordResult(record_type, values=[str(item) for item in answer])


async def lookup_dns(
    host: str,
    record_types: tuple[str, ...] = RECORD_TYPES,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> DnsLookupResult:
    resolver = dns.asyncresolver.Resolver()
    results = await asyncio.gather(
        *(_lookup_one(resolver, host, record_type, timeout) for record_type in record_types)
    )
    return DnsLookupResult(host=host, records=dict(zip(record_types, results, strict=True)))
