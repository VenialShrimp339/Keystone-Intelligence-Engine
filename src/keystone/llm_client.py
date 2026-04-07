"""LLM client factory for the Keystone Intelligence Engine.

Bridges the LLMCallable abstraction to real OpenAI Responses API calls.

Two auth paths:
  * **api_key** (recommended for production): Standard OpenAI API at
    api.openai.com.  Non-streaming, string input, optional instructions.
  * **codex_oauth** (dev/testing only): Routes through the ChatGPT-
    authenticated Codex backend at chatgpt.com/backend-api/codex. This
    private endpoint has quirks that differ from the standard API:
    streaming is mandatory, input must be a message list, instructions
    are required, and the final Response object's ``output`` is empty
    (text must be collected from stream delta events).  These are NOT
    properties of the standard Responses API.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import TypeAlias

from openai import AsyncOpenAI

from keystone.evaluator.retry import LLMCallable
from keystone.llm_settings import get_model_id, get_reasoning_effort
from keystone.models.config import AppConfig
from keystone.models.tasks import ModelTier

logger = logging.getLogger(__name__)

LLMFactory: TypeAlias = Callable[[ModelTier], LLMCallable]

CODEX_BASE_URL = "https://chatgpt.com/backend-api/codex"


class CodexTokenProvider:
    """Reads access tokens from the Codex CLI's auth.json file.

    The Codex CLI manages OAuth token refresh externally. This class
    re-reads the file when its mtime changes, caching otherwise.

    Implements ``Callable[[], Awaitable[str]]`` -- the async callable
    interface that ``AsyncOpenAI`` accepts for ``api_key``.
    """

    def __init__(self, auth_file: str | Path = "~/.codex/auth.json") -> None:
        self._auth_file = Path(auth_file).expanduser()
        self._lock = asyncio.Lock()
        self._cached_token: str | None = None
        self._last_mtime: float = 0.0

    async def __call__(self) -> str:
        """Return the current access token, re-reading if the file changed."""
        async with self._lock:
            try:
                current_mtime = self._auth_file.stat().st_mtime
            except FileNotFoundError:
                raise FileNotFoundError(
                    f"Codex auth file not found: {self._auth_file}. "
                    "Run 'codex login' to authenticate."
                ) from None

            if self._cached_token is not None and current_mtime == self._last_mtime:
                return self._cached_token

            with open(self._auth_file) as f:
                data = json.load(f)

            tokens = data.get("tokens", {})
            access_token = tokens.get("access_token")
            if not access_token:
                raise ValueError(
                    f"No access_token in {self._auth_file}. "
                    "Run 'codex login' to re-authenticate."
                )

            self._cached_token = access_token
            self._last_mtime = current_mtime
            logger.debug("Read Codex OAuth token from %s", self._auth_file)
            return self._cached_token


# ---- Client creation and caching ----

_client_cache: dict[str, AsyncOpenAI] = {}


def create_openai_client(config: AppConfig) -> AsyncOpenAI:
    """Create an AsyncOpenAI client based on auth configuration.

    Reads ``OPENAI_AUTH_TYPE`` from the environment:
    - ``codex_oauth``: callable token provider + chatgpt.com base URL
    - ``api_key`` (default): static API key + default api.openai.com
    """
    auth_type = os.environ.get("OPENAI_AUTH_TYPE", "api_key")

    if auth_type == "codex_oauth":
        auth_file = os.environ.get("CODEX_AUTH_FILE", "~/.codex/auth.json")
        token_provider = CodexTokenProvider(auth_file)
        return AsyncOpenAI(
            api_key=token_provider,
            base_url=CODEX_BASE_URL,
        )

    api_key = config.openai_api_key
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set. Required for api_key auth type.")
    return AsyncOpenAI(api_key=api_key)


def _get_cached_client(config: AppConfig) -> AsyncOpenAI:
    """Return a shared AsyncOpenAI client, creating on first call."""
    auth_type = os.environ.get("OPENAI_AUTH_TYPE", "api_key")
    if auth_type not in _client_cache:
        _client_cache[auth_type] = create_openai_client(config)
    return _client_cache[auth_type]


# ---- Implementation helpers (one per auth path) ----


async def _call_standard_api(
    client: AsyncOpenAI, model_id: str, effort: str, prompt: str
) -> str:
    """Standard OpenAI Responses API (api.openai.com).

    Uses the documented, clean interface: string input, non-streaming,
    instructions optional.  Returns ``response.output_text``.
    """
    kwargs: dict = {"model": model_id, "input": prompt}
    if effort:
        kwargs["reasoning"] = {"effort": effort}
    response = await client.responses.create(**kwargs)
    return response.output_text


async def _call_codex_oauth(
    client: AsyncOpenAI, model_id: str, effort: str, prompt: str
) -> str:
    """ChatGPT-authenticated Codex backend (chatgpt.com/backend-api/codex).

    This private endpoint differs from the standard API in several ways:
    * Streaming is mandatory (400 if ``stream`` is not true).
    * ``input`` must be a message list, not a plain string.
    * ``instructions`` is required (400 if omitted).
    * ``store`` must be false.
    * The final ``Response.output`` list is empty; text must be
      collected from ``response.output_text.delta`` stream events.

    These constraints are properties of this specific backend, NOT of
    the standard OpenAI Responses API or Codex CLI in general.
    """
    kwargs: dict = {
        "model": model_id,
        "input": [{"role": "user", "content": prompt}],
        "instructions": "You are a helpful assistant.",
        "store": False,
    }
    if effort:
        kwargs["reasoning"] = {"effort": effort}

    text_parts: list[str] = []
    async with client.responses.stream(**kwargs) as stream:
        async for event in stream:
            if event.type == "response.output_text.delta":
                text_parts.append(event.delta)
    return "".join(text_parts)


# ---- LLMCallable factory ----


def get_llm_for_tier(tier: ModelTier, config: AppConfig) -> LLMCallable:
    """Create an LLMCallable for a specific model tier.

    Returns an async callable ``(str) -> str`` that sends the prompt to
    the Responses API and returns ``response.output_text``.
    """
    client = _get_cached_client(config)
    model_id = get_model_id(tier, config)
    effort = get_reasoning_effort(tier)
    is_oauth = os.environ.get("OPENAI_AUTH_TYPE", "api_key") == "codex_oauth"

    async def _call_llm(prompt: str) -> str:
        if is_oauth:
            return await _call_codex_oauth(client, model_id, effort, prompt)
        return await _call_standard_api(client, model_id, effort, prompt)

    return _call_llm


def create_llm_factory(config: AppConfig) -> LLMFactory:
    """Return an ``LLMFactory`` bound to *config*.

    Usage::

        factory = create_llm_factory(AppConfig())
        llm = factory(ModelTier.FLAGSHIP)
        result = await llm("What is the market size for ...")
    """

    def _factory(tier: ModelTier) -> LLMCallable:
        return get_llm_for_tier(tier, config)

    return _factory
