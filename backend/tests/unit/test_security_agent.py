"""Tests for the Stage 4 deep-mode agent. `_build_trace` is tested directly as a pure function.
`run_deep_analysis` is tested against a scripted fake chat model (no live LLM call) and a fake
MCP client (no subprocess spawn) - the real MCP protocol wiring is already covered by
mcp-server's own stdio integration test; this only covers the backend-side orchestration:
tool-call-trace extraction, the deterministic-score handoff, and the step-limit guardrail.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from app.agents import security_agent
from app.agents.security_agent import AgentError, ToolCallTrace, _build_trace, _evidence_text
from app.llm.client import LlmNotConfiguredError
from app.llm.schemas import SecurityReportLLMOutput
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import tool
from pydantic import Field

# ---- _build_trace: pure function, no agent framework involved --------------------------------


def _ai_message(tool_calls: list[dict[str, Any]]) -> AIMessage:
    return AIMessage(content="", tool_calls=tool_calls)


def _tool_message(
    name: str, tool_call_id: str, *, status: str = "success", artifact: dict[str, Any] | None = None
) -> ToolMessage:
    return ToolMessage(
        content="ok", name=name, tool_call_id=tool_call_id, status=status, artifact=artifact
    )


def test_build_trace_extracts_the_analyze_url_result() -> None:
    messages = [
        _ai_message(
            [{"name": "analyze_url", "args": {"url": "https://example.com"}, "id": "call_1"}]
        ),
        _tool_message(
            "analyze_url", "call_1", artifact={"structured_content": {"risk_score": 80.0}}
        ),
    ]
    trace, url_analysis = _build_trace(messages)

    assert trace == [
        ToolCallTrace(tool="analyze_url", status="success", args={"url": "https://example.com"})
    ]
    assert url_analysis == {"risk_score": 80.0}


def test_build_trace_pairs_multiple_tool_calls_in_order() -> None:
    messages = [
        _ai_message(
            [{"name": "analyze_url", "args": {"url": "https://example.com"}, "id": "call_1"}]
        ),
        _tool_message(
            "analyze_url", "call_1", artifact={"structured_content": {"risk_score": 10.0}}
        ),
        _ai_message([{"name": "lookup_dns", "args": {"host": "example.com"}, "id": "call_2"}]),
        _tool_message(
            "lookup_dns", "call_2", artifact={"structured_content": {"host": "example.com"}}
        ),
    ]
    trace, url_analysis = _build_trace(messages)

    assert [t.tool for t in trace] == ["analyze_url", "lookup_dns"]
    assert trace[1].args == {"host": "example.com"}
    assert url_analysis == {"risk_score": 10.0}


def test_build_trace_returns_none_when_analyze_url_was_never_called() -> None:
    messages = [
        _ai_message([{"name": "lookup_dns", "args": {"host": "example.com"}, "id": "call_1"}]),
        _tool_message(
            "lookup_dns", "call_1", artifact={"structured_content": {"host": "example.com"}}
        ),
    ]
    _, url_analysis = _build_trace(messages)
    assert url_analysis is None


def test_build_trace_ignores_a_failed_analyze_url_call() -> None:
    messages = [
        _ai_message([{"name": "analyze_url", "args": {"url": "not a url"}, "id": "call_1"}]),
        _tool_message("analyze_url", "call_1", status="error", artifact=None),
    ]
    trace, url_analysis = _build_trace(messages)
    assert trace[0].status == "error"
    assert url_analysis is None


def test_evidence_text_flattens_successful_tool_results_and_skips_failures() -> None:
    messages = [
        _tool_message("analyze_url", "c1", artifact={"structured_content": {"risk_score": 5.0}}),
        _tool_message("lookup_dns", "c2", status="error", artifact=None),
        _tool_message("threat_lookup", "c3", artifact=None),
    ]
    text = _evidence_text(messages)
    assert "[analyze_url]" in text
    assert "'risk_score': 5.0" in text
    assert "lookup_dns" not in text
    assert "[threat_lookup]" in text  # no structured content: falls back to the message text


def test_build_trace_defaults_args_to_empty_when_the_call_id_is_unmatched() -> None:
    messages = [_tool_message("analyze_url", "orphan_call_id", artifact={"structured_content": {}})]
    trace, _ = _build_trace(messages)
    assert trace[0].args == {}


# ---- run_deep_analysis: scripted fake model, no live LLM or MCP subprocess -------------------


class _ScriptedFakeChatModel(BaseChatModel):
    responses: list[AIMessage] = Field(default_factory=list)
    call_count: int = 0

    @property
    def _llm_type(self) -> str:
        return "scripted-fake"

    def bind_tools(self, tools: Any, **kwargs: Any) -> _ScriptedFakeChatModel:
        return self

    def _generate(
        self, messages: Any, stop: Any = None, run_manager: Any = None, **kwargs: Any
    ) -> ChatResult:
        response = self.responses[min(self.call_count, len(self.responses) - 1)]
        self.call_count += 1
        return ChatResult(generations=[ChatGeneration(message=response)])

    async def _agenerate(
        self, messages: Any, stop: Any = None, run_manager: Any = None, **kwargs: Any
    ) -> ChatResult:
        return self._generate(messages, stop, run_manager, **kwargs)


# langchain_mcp_adapters converts each MCP tool into a `StructuredTool` with
# response_format="content_and_artifact", whose artifact carries {"structured_content": ...} -
# see `MCPToolArtifact` - so `_build_trace` can read a tool's structured result straight off the
# ToolMessage. A plain @tool function does not do this by itself, so these fakes mimic it.
def _analyze_url_fn(url: str) -> tuple[str, dict[str, Any]]:
    structured = {
        "url": url,
        "risk_score": 91.0,
        "risk_level": "high",
        "classification": "likely_phishing",
    }
    return str(structured), {"structured_content": structured}


analyze_url = tool(
    "analyze_url", response_format="content_and_artifact", description="Fake analyze_url tool."
)(_analyze_url_fn)


def _lookup_dns_fn(host: str) -> tuple[str, dict[str, Any]]:
    structured = {"host": host, "resolved": True}
    return str(structured), {"structured_content": structured}


lookup_dns = tool(
    "lookup_dns", response_format="content_and_artifact", description="Fake lookup_dns tool."
)(_lookup_dns_fn)


def _fake_mcp_client(tools: list[Any]) -> Any:
    client = AsyncMock()
    client.get_tools = AsyncMock(return_value=tools)
    return client


def _calls(name: str, args: dict[str, Any], call_id: str) -> AIMessage:
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": call_id}])


_REPORT = SecurityReportLLMOutput(
    summary="Likely phishing based on the score.", indicator_explanations=[], recommendations=[]
)


def _patched(model: BaseChatModel, tools: list[Any], report_result: Any) -> Any:
    """The chat model + MCP client + report-writing step are all faked: no live LLM, no
    subprocess. The report step is faked whole because it is a separate json_schema call whose
    provider behaviour is only verifiable live."""
    return (
        patch("app.agents.security_agent.get_chat_model", return_value=model),
        patch("app.agents.security_agent._mcp_client", return_value=_fake_mcp_client(tools)),
        patch("app.agents.security_agent._write_report", new=AsyncMock(return_value=report_result)),
    )


async def test_run_deep_analysis_extracts_the_deterministic_score_and_report() -> None:
    model = _ScriptedFakeChatModel(
        responses=[
            _calls("analyze_url", {"url": "https://example.com"}, "call_1"),
            AIMessage(content="done investigating"),
        ]
    )
    p1, p2, p3 = _patched(model, [analyze_url], (_REPORT, "fake-model", 100, 20, None))
    with p1, p2, p3:
        result = await security_agent.run_deep_analysis("https://example.com")

    assert result.url_analysis["risk_score"] == 91.0
    assert result.url_analysis["classification"] == "likely_phishing"
    assert result.report == _REPORT
    assert result.model_name == "fake-model"
    assert (result.prompt_tokens, result.completion_tokens) == (100, 20)
    assert [t.tool for t in result.trace] == ["analyze_url"]


async def test_a_report_failure_does_not_fail_the_analysis() -> None:
    model = _ScriptedFakeChatModel(
        responses=[
            _calls("analyze_url", {"url": "https://example.com"}, "call_1"),
            AIMessage(content="done"),
        ]
    )
    p1, p2, p3 = _patched(model, [analyze_url], (None, "fake-model", None, None, "parse failed"))
    with p1, p2, p3:
        result = await security_agent.run_deep_analysis("https://example.com")

    assert result.url_analysis["risk_score"] == 91.0  # the deterministic score still stands
    assert result.report is None
    assert result.report_error == "parse failed"


async def test_run_deep_analysis_selects_multiple_tools_in_order() -> None:
    model = _ScriptedFakeChatModel(
        responses=[
            _calls("analyze_url", {"url": "https://example.com"}, "call_1"),
            _calls("lookup_dns", {"host": "example.com"}, "call_2"),
            AIMessage(content="done"),
        ]
    )
    p1, p2, p3 = _patched(model, [analyze_url, lookup_dns], (_REPORT, "m", None, None, None))
    with p1, p2, p3:
        result = await security_agent.run_deep_analysis("https://example.com")

    assert [t.tool for t in result.trace] == ["analyze_url", "lookup_dns"]
    assert result.trace[1].args == {"host": "example.com"}


async def test_run_deep_analysis_raises_agent_error_when_analyze_url_is_never_called() -> None:
    model = _ScriptedFakeChatModel(
        responses=[
            _calls("lookup_dns", {"host": "example.com"}, "call_1"),
            AIMessage(content="done"),
        ]
    )
    p1, p2, p3 = _patched(model, [lookup_dns], (_REPORT, "m", None, None, None))
    with p1, p2, p3, pytest.raises(AgentError, match="never called analyze_url"):
        await security_agent.run_deep_analysis("https://example.com")


async def test_run_deep_analysis_degrades_when_the_llm_is_not_configured() -> None:
    def _raise() -> BaseChatModel:
        raise LlmNotConfiguredError("HF_TOKEN is not set")

    with (
        patch("app.agents.security_agent.get_chat_model", side_effect=_raise),
        patch(
            "app.agents.security_agent._mcp_client", return_value=_fake_mcp_client([analyze_url])
        ),
        pytest.raises(AgentError, match="HF_TOKEN is not set"),
    ):
        await security_agent.run_deep_analysis("https://example.com")


async def test_run_deep_analysis_respects_the_step_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    # A model that always calls a tool and never stops must not loop forever - MAX_STEPS bounds it.
    monkeypatch.setattr(security_agent, "MAX_STEPS", 3)
    model = _ScriptedFakeChatModel(responses=[_calls("lookup_dns", {"host": "e.com"}, "call_x")])
    p1, p2, p3 = _patched(model, [lookup_dns], (_REPORT, "m", None, None, None))
    with p1, p2, p3, pytest.raises(AgentError):
        await security_agent.run_deep_analysis("https://example.com")


async def test_write_report_returns_the_error_instead_of_raising() -> None:
    def _raise() -> BaseChatModel:
        raise LlmNotConfiguredError("HF_TOKEN is not set")

    with patch("app.agents.security_agent.get_chat_model", side_effect=_raise):
        report, _, _, _, error = await security_agent._write_report("evidence")

    assert report is None
    assert error == "HF_TOKEN is not set"
