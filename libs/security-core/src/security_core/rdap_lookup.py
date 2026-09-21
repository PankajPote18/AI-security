"""RDAP domain lookup (registrar, creation date -> domain age) via the public rdap.org bootstrap
redirector, which resolves the request to the authoritative registry RDAP server. This avoids
this module needing to implement IANA's RDAP bootstrap registry itself.

Like `dns_lookup`, a failure is reported as a result with `found=False` and an `error` code
rather than raised, so callers can degrade gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import httpx

DEFAULT_TIMEOUT_SECONDS = 5.0
RDAP_BASE_URL = "https://rdap.org/domain"


@dataclass(frozen=True)
class RdapResult:
    domain: str
    found: bool
    registrar: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    status: list[str] = field(default_factory=list)
    error: str | None = None

    @property
    def age_days(self) -> int | None:
        if self.created_at is None:
            return None
        return (datetime.now(tz=UTC) - self.created_at).days


def _parse_event(events: list[dict[str, Any]], action: str) -> datetime | None:
    for event in events or []:
        if event.get("eventAction") != action:
            continue
        raw = event.get("eventDate")
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _parse_registrar(entities: list[dict[str, Any]]) -> str | None:
    for entity in entities or []:
        if "registrar" not in (entity.get("roles") or []):
            continue
        for vcard_field in (entity.get("vcardArray") or [None, []])[1]:
            if vcard_field[0] == "fn":
                return str(vcard_field[3])
        handle = entity.get("handle")
        if handle:
            return str(handle)
    return None


async def lookup_rdap(
    registered_domain: str,
    client: httpx.AsyncClient | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> RdapResult:
    owns_client = client is None
    # rdap.org deliberately 302-redirects to the authoritative registry's RDAP server; without
    # follow_redirects every lookup would fail.
    client = client or httpx.AsyncClient(timeout=timeout, follow_redirects=True)
    try:
        response = await client.get(f"{RDAP_BASE_URL}/{registered_domain}")
        if response.status_code == 404:
            return RdapResult(domain=registered_domain, found=False)
        response.raise_for_status()
        data = response.json()
        return RdapResult(
            domain=registered_domain,
            found=True,
            registrar=_parse_registrar(data.get("entities", [])),
            created_at=_parse_event(data.get("events", []), "registration"),
            updated_at=_parse_event(data.get("events", []), "last changed"),
            status=list(data.get("status", [])),
        )
    except httpx.TimeoutException:
        return RdapResult(domain=registered_domain, found=False, error="timeout")
    except httpx.HTTPError as error:
        return RdapResult(domain=registered_domain, found=False, error=type(error).__name__)
    finally:
        if owns_client:
            await client.aclose()
