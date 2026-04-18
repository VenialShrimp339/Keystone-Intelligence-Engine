"""LLM client factory for the Keystone Intelligence Engine.

Three transport paths:
  * **claude_cli** (default): Shells out to ``claude -p`` on the local
    machine.  Requires a Claude Max subscription.  3-5s per call with
    full parallelism (10 concurrent).
  * **api_key**: Standard OpenAI API at api.openai.com.
  * **codex_oauth** (legacy): Routes through the ChatGPT-authenticated
    Codex backend at chatgpt.com/backend-api/codex.

Set LLM_PROVIDER env var to choose: claude_cli | api_key | codex_oauth.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import TypeAlias

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None  # Only needed for api_key/codex_oauth paths

from keystone.evaluator.retry import LLMCallable
from keystone.llm_settings import get_model_id, get_reasoning_effort
from keystone.models.config import AppConfig
from keystone.models.tasks import ModelTier

logger = logging.getLogger(__name__)

LLMFactory: TypeAlias = Callable[[ModelTier], LLMCallable]

CODEX_BASE_URL = "https://chatgpt.com/backend-api/codex"

# ---- Claude CLI mappings ----

CLAUDE_MODEL_MAP: dict[ModelTier, str] = {
    ModelTier.FLAGSHIP: "claude-opus-4-6",
    ModelTier.STANDARD: "claude-sonnet-4-6",
    ModelTier.FAST: "claude-haiku-4-5",
    ModelTier.LIGHT: "claude-haiku-4-5",
}

CLAUDE_EFFORT_MAP: dict[ModelTier, str] = {
    ModelTier.FLAGSHIP: "high",
    ModelTier.STANDARD: "medium",
    ModelTier.FAST: "low",
    ModelTier.LIGHT: "low",
}

_claude_semaphore = asyncio.Semaphore(10)

# Deep research: lower concurrency (heavier calls, 5-10 min each)
_research_semaphore = asyncio.Semaphore(5)


# ---- Claude CLI transport ----


async def _call_claude_cli(
    prompt: str,
    model: str,
    effort: str,
    semaphore: asyncio.Semaphore,
) -> str:
    """Call Claude via the ``claude -p`` CLI.

    Requires the Claude CLI installed and a Max subscription active.
    """
    async with semaphore:
        proc = await asyncio.create_subprocess_exec(
            "claude",
            "-p",
            prompt,
            "--model",
            model,
            "--effort",
            effort,
            "--output-format",
            "text",
            "--no-session-persistence",
            "--tools",
            "",
            "--system-prompt",
            "",
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
        except asyncio.TimeoutError:
            raise RuntimeError(f"claude -p timed out after 300s (model={model})") from None
        finally:
            # Kill the subprocess if it is still running (TimeoutError,
            # CancelledError, or any other early exit).
            # asyncio.shield prevents a second CancelledError from interrupting
            # this cleanup await and leaving the process unkilled.
            if proc.returncode is None:
                proc.kill()
                await asyncio.shield(proc.wait())

        if proc.returncode != 0:
            raise RuntimeError(f"claude -p exited {proc.returncode}: {stderr.decode().strip()}")

        return stdout.decode()


async def _call_claude_cli_research(
    prompt: str,
    model: str,
    semaphore: asyncio.Semaphore,
) -> str:
    """Call Claude via ``claude -p`` with web research tools enabled.

    Unlike the pure-LLM transport (``_call_claude_cli``), this enables
    WebSearch and WebFetch tools so Claude can perform multi-turn web
    research: searching, reading full pages, following citations, and
    synthesizing across many sources.

    Key differences from pure-LLM path:
    - ``--allowedTools "WebSearch,WebFetch"`` instead of ``--tools ""``
    - No ``--system-prompt ""`` (default context aids web research)
    - No ``--bare`` (breaks Max subscription auth)
    - ``--effort medium`` (depth comes from web search turns, not thinking)
    - 1200s timeout (deep research sessions: many web searches + full page reads)
    """
    timeout = int(os.environ.get("DEEP_RESEARCH_TIMEOUT", "1200"))
    async with semaphore:
        proc = await asyncio.create_subprocess_exec(
            "claude",
            "-p",
            prompt,
            "--model",
            model,
            "--effort",
            "medium",
            "--allowedTools",
            "WebSearch,WebFetch",
            "--output-format",
            "text",
            "--no-session-persistence",
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            raise RuntimeError(
                f"claude -p research timed out after {timeout}s (model={model})"
            ) from None
        finally:
            # Kill the subprocess if it is still running (TimeoutError,
            # CancelledError, or any other early exit).
            # asyncio.shield prevents a second CancelledError from interrupting
            # this cleanup await and leaving the process unkilled.
            if proc.returncode is None:
                proc.kill()
                await asyncio.shield(proc.wait())

        if proc.returncode != 0:
            raise RuntimeError(
                f"claude -p research exited {proc.returncode}: {stderr.decode().strip()}"
            )

        return stdout.decode()


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
                    f"No access_token in {self._auth_file}. Run 'codex login' to re-authenticate."
                )

            self._cached_token = access_token
            self._last_mtime = current_mtime
            logger.debug("Read Codex OAuth token from %s", self._auth_file)
            return self._cached_token


# ---- Client creation and caching ----

_client_cache: dict[str, AsyncOpenAI] = {}


def _resolve_openai_auth_type() -> str:
    """Resolve the OpenAI auth mode for legacy provider paths.

    ``LLM_PROVIDER`` is the documented switch and takes precedence. We still
    fall back to ``OPENAI_AUTH_TYPE`` for backwards compatibility with older
    configs and tests.
    """
    provider = os.environ.get("LLM_PROVIDER")
    if provider in ("api_key", "codex_oauth"):
        return provider

    auth_type = os.environ.get("OPENAI_AUTH_TYPE", "")
    if auth_type in ("api_key", "codex_oauth"):
        return auth_type

    return "api_key"


def create_openai_client(config: AppConfig) -> AsyncOpenAI:
    """Create an AsyncOpenAI client based on auth configuration.

    Reads ``OPENAI_AUTH_TYPE`` from the environment:
    - ``codex_oauth``: callable token provider + chatgpt.com base URL
    - ``api_key`` (default): static API key + default api.openai.com
    """
    if AsyncOpenAI is None:
        raise ImportError(
            "openai package required for api_key/codex_oauth providers. "
            "Install with: pip install openai"
        )
    auth_type = _resolve_openai_auth_type()

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
    auth_type = _resolve_openai_auth_type()
    if auth_type not in _client_cache:
        _client_cache[auth_type] = create_openai_client(config)
    return _client_cache[auth_type]


# ---- Implementation helpers (one per auth path) ----


async def _call_standard_api(client: AsyncOpenAI, model_id: str, effort: str, prompt: str) -> str:
    """Standard OpenAI Responses API (api.openai.com).

    Uses the documented, clean interface: string input, non-streaming,
    instructions optional.  Returns ``response.output_text``.
    """
    kwargs: dict = {"model": model_id, "input": prompt, "service_tier": "fast"}
    if effort:
        kwargs["reasoning"] = {"effort": effort}
    async with asyncio.timeout(300):  # 5-minute ceiling per API call
        response = await client.responses.create(**kwargs)
    return response.output_text


async def _call_codex_oauth(client: AsyncOpenAI, model_id: str, effort: str, prompt: str) -> str:
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
        "service_tier": "fast",
    }
    if effort:
        kwargs["reasoning"] = {"effort": effort}

    text_parts: list[str] = []
    async with asyncio.timeout(300):  # 5-minute ceiling per streaming call
        async with client.responses.stream(**kwargs) as stream:
            async for event in stream:
                if event.type == "response.output_text.delta":
                    text_parts.append(event.delta)
    return "".join(text_parts)


# ---- LLMCallable factory ----


def _resolve_provider() -> str:
    """Determine the LLM provider from environment variables.

    Checks LLM_PROVIDER first. Falls back to inferring from
    OPENAI_AUTH_TYPE for backwards compatibility with existing configs
    and tests.
    """
    explicit = os.environ.get("LLM_PROVIDER")
    if explicit:
        return explicit
    auth_type = os.environ.get("OPENAI_AUTH_TYPE", "")
    if auth_type in ("api_key", "codex_oauth"):
        return auth_type
    return "claude_cli"


def get_llm_for_tier(tier: ModelTier, config: AppConfig) -> LLMCallable:
    """Create an LLMCallable for a specific model tier.

    Returns an async callable ``(str) -> str`` that sends the prompt to
    the configured provider and returns the response text.
    """
    provider = _resolve_provider()

    if provider == "claude_cli":
        if os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError(
                "ANTHROPIC_API_KEY is set! claude -p will bill to API, "
                "not Max subscription. Run: unset ANTHROPIC_API_KEY"
            )
        model = CLAUDE_MODEL_MAP[tier]
        effort = CLAUDE_EFFORT_MAP[tier]

        async def _call_claude(prompt: str) -> str:
            return await _call_claude_cli(prompt, model, effort, _claude_semaphore)

        return _call_claude

    # Legacy OpenAI paths (api_key / codex_oauth)
    client = _get_cached_client(config)
    model_id = get_model_id(tier, config)
    effort = get_reasoning_effort(tier)
    is_oauth = provider == "codex_oauth"

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


def get_deep_research_callable() -> LLMCallable:
    """Return an LLMCallable for deep web research via Claude CLI.

    Uses Sonnet with WebSearch + WebFetch tools enabled, allowing
    multi-turn research sessions (5-10 minutes per call).

    Concurrency limited to 5 simultaneous research sessions.
    """
    if os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "ANTHROPIC_API_KEY is set! claude -p will bill to API, "
            "not Max subscription. Run: unset ANTHROPIC_API_KEY"
        )

    model = CLAUDE_MODEL_MAP[ModelTier.STANDARD]  # sonnet

    async def _call_research(prompt: str) -> str:
        return await _call_claude_cli_research(prompt, model, _research_semaphore)

    return _call_research
