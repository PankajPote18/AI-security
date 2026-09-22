"""Provider-agnostic chat model factory.

Currently wired to Hugging Face Inference Providers' OpenAI-compatible router endpoint
(https://router.huggingface.co/v1), reached through `langchain_openai.ChatOpenAI` pointed at a
custom `base_url` - not the `langchain-huggingface` package, precisely because the router
endpoint speaks the same OpenAI chat-completions wire format `ChatOpenAI` already implements.
Swapping providers later (Anthropic, OpenAI directly) means changing only this function; every
caller (`report_service`, Stage 4's agent) depends on `BaseChatModel`, not on this provider.

Model: `openai/gpt-oss-20b` by default (override via `HF_MODEL`) - chosen for native structured-
output/tool-calling support (purpose-built for it, unlike most instruction-tuned models bolting
JSON mode on afterwards), Apache 2.0 licensing, and low cost from its mixture-of-experts design
(21B total / 3.6B active parameters). `openai/gpt-oss-120b` is a stronger, pricier option if
`gpt-oss-20b`'s report quality proves insufficient - one environment variable to switch.
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
