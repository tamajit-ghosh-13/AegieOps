"""Chat models used by the agent graph.

Triage is a bounded classification + short-reasoning task, so it defaults to a
cheaper/faster model. Propose drafts a code patch and keeps a stronger model.
"""

from __future__ import annotations

import os
from typing import Any

DEFAULT_TRIAGE_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_PROPOSE_MODEL = "claude-sonnet-4-6"

DEFAULT_GEMINI_TRIAGE = "gemini-3.5-flash-lite"
DEFAULT_GEMINI_PROPOSE = "gemini-3.5-flash-lite"

DEFAULT_OLLAMA_TRIAGE = "gemma4:31b-cloud"
DEFAULT_OLLAMA_PROPOSE = "gemma4:31b-cloud"


def get_llm(model: str) -> Any:
    ollama_key = os.environ.get("OLLAMA_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

    # 1. Ollama Cloud / Gemma models
    if model.startswith("gemma") or model.startswith("ollama") or (ollama_key and not (gemini_key or anthropic_key)):
        from langchain_openai import ChatOpenAI
        base_url = os.environ.get("OLLAMA_BASE_URL", "https://ollama.com/v1")

        class OllamaCloudChat(ChatOpenAI):
            def with_structured_output(self, schema, **kwargs):
                kwargs.setdefault("method", "function_calling")
                return super().with_structured_output(schema, **kwargs)

        return OllamaCloudChat(model=model, api_key=ollama_key or "no-key", base_url=base_url, temperature=0)

    # 2. Google Gemini models
    if model.startswith("gemini") or (gemini_key and not anthropic_key):
        from langchain_google_genai import ChatGoogleGenerativeAI

        # Fallback to default gemini model if passed a claude model name without anthropic key
        if model.startswith("claude"):
            model = DEFAULT_GEMINI_TRIAGE
        return ChatGoogleGenerativeAI(model=model, api_key=gemini_key)

    # 3. Anthropic Claude models
    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(model=model)


def get_triage_llm() -> Any:
    ollama_key = os.environ.get("OLLAMA_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

    configured = os.environ.get("TRIAGE_MODEL")
    if configured:
        model = configured
    elif ollama_key and not (gemini_key or anthropic_key):
        model = DEFAULT_OLLAMA_TRIAGE
    elif gemini_key and not anthropic_key:
        model = DEFAULT_GEMINI_TRIAGE
    else:
        model = DEFAULT_TRIAGE_MODEL
    return get_llm(model)


def get_propose_llm() -> Any:
    ollama_key = os.environ.get("OLLAMA_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

    configured = os.environ.get("PROPOSE_MODEL")
    if configured:
        model = configured
    elif ollama_key and not (gemini_key or anthropic_key):
        model = DEFAULT_OLLAMA_PROPOSE
    elif gemini_key and not anthropic_key:
        model = DEFAULT_GEMINI_PROPOSE
    else:
        model = DEFAULT_PROPOSE_MODEL
    return get_llm(model)
