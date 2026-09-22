"""URLhaus (abuse.ch) URL-reputation lookups: is this URL already known to be serving malware.
Lookup-only - this module only ever reads URLhaus's database, never submits URLs to it.

Requires a free Auth-Key from https://auth.abuse.ch/ (see `.env.example`'s `URLHAUS_AUTH_KEY`);
abuse.ch's "Community First" policy has required one on every request since mid-2025.
"""

from __future__ import annotations

import httpx

from security_core.threat_intel.base import ThreatIntelResult

DEFAULT_TIMEOUT_SECONDS = 5.0
URL_LOOKUP_ENDPOINT = "https://urlhaus-api.abuse.ch/v1/url/"
PROVIDER_NAME = "urlhaus"


class UrlhausProvider:
    name = PROVIDER_NAME

    def __init__(self, auth_key: str, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> None:
        self._auth_key = auth_key
        self._timeout = timeout

    async def check_url(
        self, url: str, client: httpx.AsyncClient | None = None
    ) -> ThreatIntelResult:
        owns_client = client is None
        client = client or httpx.AsyncClient(timeout=self._timeout)
        try:
            response = await client.post(
                URL_LOOKUP_ENDPOINT, data={"url": url}, headers={"Auth-Key": self._auth_key}
            )
            response.raise_for_status()
            data = response.json()
            query_status = data.get("query_status")

            if query_status == "ok":
                return ThreatIntelResult(
                    provider=PROVIDER_NAME,
                    status="listed",
                    threat_type=data.get("threat"),
                    tags=list(data.get("tags") or []),
                    reference_url=data.get("urlhaus_reference"),
                )
            if query_status == "no_results":
                return ThreatIntelResult(provider=PROVIDER_NAME, status="not_listed")
            # invalid_url / http_post_expected / an unrecognised value: treat as a provider
            # problem, not a verdict about the URL.
            return ThreatIntelResult(
                provider=PROVIDER_NAME,
                status="unavailable",
                error=f"unexpected query_status: {query_status}",
            )
        except httpx.TimeoutException:
            return ThreatIntelResult(provider=PROVIDER_NAME, status="unavailable", error="timeout")
        except httpx.HTTPError as error:
            return ThreatIntelResult(
                provider=PROVIDER_NAME, status="unavailable", error=type(error).__name__
            )
        finally:
            if owns_client:
                await client.aclose()
