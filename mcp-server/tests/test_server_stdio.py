"""Integration test over the real MCP protocol: spawns the actual server as a subprocess and
talks to it over stdio via the standard MCP client, the same way the backend's LangChain agent
(via `langchain-mcp-adapters`) and any external MCP host (Claude Desktop, MCP Inspector) do. Unit
tests in `test_service.py` cover the tool logic itself; this only proves the protocol wiring -
tool registration, argument passing, structured output, and error propagation - is intact.
"""

from __future__ import annotations

import sys

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

_SERVER_PARAMS = StdioServerParameters(command=sys.executable, args=["-m", "copilot_mcp.server"])

_EXPECTED_TOOL_NAMES = {
    "analyze_url",
    "lookup_dns",
    "check_domain",
    "threat_lookup",
    "search_security_knowledge",
}


@pytest.mark.asyncio
async def test_the_server_advertises_every_tool_with_a_docstring() -> None:
    async with stdio_client(_SERVER_PARAMS) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        result = await session.list_tools()

    tools_by_name = {t.name: t for t in result.tools}
    assert set(tools_by_name) == _EXPECTED_TOOL_NAMES
    assert all(t.description for t in tools_by_name.values())


@pytest.mark.asyncio
async def test_calling_analyze_url_returns_structured_content() -> None:
    async with stdio_client(_SERVER_PARAMS) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool("analyze_url", {"url": "https://www.example.com/"})

    assert result.isError is False
    assert result.structuredContent is not None
    assert 0 <= result.structuredContent["risk_score"] <= 100
    assert result.structuredContent["classification"] in {
        "likely_legitimate",
        "suspicious",
        "likely_phishing",
    }


@pytest.mark.asyncio
async def test_an_invalid_url_is_reported_as_a_tool_error_not_a_crash() -> None:
    async with stdio_client(_SERVER_PARAMS) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool("analyze_url", {"url": "javascript:alert(1)"})

    assert result.isError is True
    assert result.content  # the model gets a readable message, not an empty result


@pytest.mark.asyncio
async def test_calling_search_security_knowledge_with_a_custom_top_k() -> None:
    async with stdio_client(_SERVER_PARAMS) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool(
            "search_security_knowledge",
            {"query": "how to detect phishing lookalike domains", "top_k": 2},
        )

    assert result.isError is False
    assert 0 < len(result.structuredContent["result"]) <= 2
