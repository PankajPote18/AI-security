"""Provider-agnostic threat-intelligence lookups: check a URL against an external reputation
feed, normalized into one shape regardless of provider, so callers (`security_analysis_service`,
the MCP `threat_lookup` tool) don't need to know which provider answered or add a new code path
when a second provider is added later.

Every provider degrades to `status="unavailable"` rather than raising - on a missing key,
timeout, rate limit, or any other HTTP error - so a threat-intel outage makes an analysis
`degraded`, never fails it outright. See `urlhaus.py` for the one currently wired-up provider.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol

ThreatIntelStatus = Literal["listed", "not_listed", "unavailable"]


@dataclass(frozen=True)
class ThreatIntelResult:
    provider: str
    status: ThreatIntelStatus
    threat_type: str | None = None
    tags: list[str] = field(default_factory=list)
    reference_url: str | None = None
    error: str | None = None


class ThreatIntelProvider(Protocol):
    name: str

    async def check_url(self, url: str) -> ThreatIntelResult: ...
