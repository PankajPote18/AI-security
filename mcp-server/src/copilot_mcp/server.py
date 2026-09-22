"""MCP server exposing security-analysis tools over stdio.

Run standalone with `uv run copilot-mcp` (e.g. from an MCP Inspector or Claude Desktop config),
or spawned as a subprocess by the backend's LangChain agent via `langchain-mcp-adapters`. Every
tool here is read-only and idempotent - safe for a model to call freely without confirmation.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from copilot_mcp import service
from copilot_mcp.schemas import (
    DnsLookupOut,
    DomainInfoOut,
    KnowledgeSourceOut,
    ThreatIntelOut,
    UrlAnalysisOut,
)

mcp = FastMCP("AI Security Copilot")


@mcp.tool()
async def analyze_url(url: str) -> UrlAnalysisOut:
    """Run the deterministic phishing-detection pipeline (ML classifier + structural indicators)
    on a URL and return its risk score (0-100), risk level, classification, and the structural
    indicators that fired. Does not perform DNS, RDAP or threat-intel lookups - call
    `lookup_dns`, `check_domain` or `threat_lookup` separately for those."""
    try:
        return await service.analyze_url(url)
    except service.InvalidInputError as error:
        raise ToolError(str(error)) from error


@mcp.tool()
async def lookup_dns(host: str) -> DnsLookupOut:
    """Look up A, AAAA, MX, NS and TXT DNS records for a hostname."""
    return await service.lookup_dns_records(host)


@mcp.tool()
async def check_domain(registered_domain: str) -> DomainInfoOut:
    """Look up RDAP registration details - registrar, creation date, domain age in days, and
    status codes - for a registered domain, e.g. "example.com" (not a full URL or subdomain)."""
    return await service.check_domain(registered_domain)


@mcp.tool()
async def threat_lookup(url: str) -> ThreatIntelOut:
    """Check a URL against the URLhaus threat-intelligence feed for known malware-hosting or
    phishing activity. `status` is "listed" (a real verdict - this exact URL is on record),
    "not_listed" (checked, nothing found), or "unavailable" (no verdict was possible - the
    provider is not configured, rate-limited, or unreachable; treat this as missing evidence,
    not as a clean result)."""
    return await service.threat_lookup(url)


@mcp.tool()
async def search_security_knowledge(query: str, top_k: int = 5) -> list[KnowledgeSourceOut]:
    """Search the curated cybersecurity knowledge base (phishing techniques, MITRE ATT&CK
    entries, OWASP guidance, DNS/HTTP background) for passages relevant to a query. Returns up
    to `top_k` sources with their text and provenance, most relevant first."""
    return await service.search_security_knowledge(query, top_k)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
