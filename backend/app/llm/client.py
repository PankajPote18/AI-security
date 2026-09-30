"""Provider-agnostic chat model factory.

Currently wired to Hugging Face Inference Providers' OpenAI-compatible router endpoint
(https://router.huggingface.co/v1), reached through `langchain_openai.ChatOpenAI` pointed at a
custom `base_url` - not the `langchain-huggingface` package, precisely because the router
endpoint speaks the same OpenAI chat-completions wire format `ChatOpenAI` already implements.
Swapping providers later (Anthropic, OpenAI directly) means changing only this function; every
caller (`report_service`, Stage 4's agent) depends on `BaseChatModel`, not on this provider.

Model: `openai/gpt-oss-120b` by default (override via `HF_MODEL`) - Apache 2.0, native
structured-output/tool-calling support. `openai/gpt-oss-20b` is the smaller, cheaper sibling and
works fine for Stage 3's single-shot report generation, but live-testing Stage 4's multi-round
agent loop against it through Hugging Face's router surfaced a real reliability bug: it
intermittently (well over half the time, across dozens of live runs) emits a tool call the
router's own parser rejects with a bare `output_parse_failed` and no other detail - not a prompt
issue, since `run_deep_analysis` retries a fresh attempt on any failure and the retry hits the
same wall. `gpt-oss-120b` produced zero such failures across the same test URLs. Swap back to
`20b` only for standard-mode-only deployments that never enable `mode=deep`.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_openai import ChatOpenAI

from app.core.config import get_settings

HF_ROUTER_BASE_URL = "https://router.huggingface.co/v1"
TEMPERATURE = 0.0  # deterministic: a security report should not vary run to run on the same input


class LlmNotConfiguredError(RuntimeError):
    """HF_TOKEN is not set. Report generation degrades to `report=null` rather than failing the
    whole analysis - see `services/report_service.py`."""


@lru_cache
def get_chat_model() -> ChatOpenAI:
    settings = get_settings()
    if settings.hf_token is None:
        raise LlmNotConfiguredError("HF_TOKEN is not set")
    return ChatOpenAI(
        base_url=HF_ROUTER_BASE_URL,
        api_key=settings.hf_token,
        model=settings.hf_model,
        temperature=TEMPERATURE,
    )


def is_configured() -> bool:
    return get_settings().hf_token is not None
