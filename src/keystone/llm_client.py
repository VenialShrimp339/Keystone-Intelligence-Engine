"""LLM client factory for the Keystone Intelligence Engine.

Three transport paths:
  * **claude_cli** (default): Shells out to ``claude -p`` on the local
    machine.  Requires a Claude Max subscription.  3-5s per call with
    full parallelism (concurrency from PipelineConfig).
  * **api_key**: Standard OpenAI API at api.openai.com.
  * **codex_oauth** (legacy): Routes through the ChatGPT-authenticated
    Codex backend at chatgpt.com/backend-api/codex.

Set LLM_PROVIDER env var to choose: claude_cli | api_key | codex_oauth.

The LLM factory is the single place that reads :class:`AppConfig` and
:class:`PipelineConfig`. Every downstream caller gets an LLM by tier,
optionally with an effort override, or by pipeline layer name (which
resolves tier + effort from config).
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
from collections.abc import Callable
from pathlib import Path
from typing import TypeAlias

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None  # Only needed for api_key/codex_oauth paths

from keystone.evaluator.retry import LLMCallable
from keystone.llm_settings import (
    get_layer_effort,
    get_layer_tier,
    get_model_id,
    get_reasoning_effort,
)
from keystone.models.config import AppConfig, PipelineConfig
from keystone.models.tasks import ModelTier

logger = logging.getLogger(__name__)

LLMFactory: TypeAlias = Callable[[ModelTier], LLMCallable]

CODEX_BASE_URL = "https://chatgpt.com/backend-api/codex"


# ---- Claude CLI model map (backward-compat module-level view) -----------
#
# The canonical source is AppConfig.flagship_model / standard_model /
# fast_model, resolved via :func:`_resolve_claude_model`. This module
# constant remains exported for legacy call sites and tests; it reflects
# the default AppConfig values.
CLAUDE_MODEL_MAP: dict[ModelTier, str] = {
    ModelTier.FLAGSHIP: AppConfig.model_fields["flagship_model"].default,
    ModelTier.STANDARD: AppConfig.model_fields["standard_model"].default,
    ModelTier.FAST: AppConfig.model_fields["fast_model"].default,
    ModelTier.LIGHT: AppConfig.model_fields["fast_model"].default,
}


# ---- Backward-compat module-level semaphores ----------------------------
#
# Primary path: :class:`LayerAwareLLMFactory` holds its own instance-level
# semaphores sized by :class:`PipelineConfig`. These module-level ones
# remain for legacy direct callers (e.g. tests importing
# ``_research_semaphore``). Sized with the PipelineConfig defaults.
_DEFAULT_PIPELINE_CONFIG = PipelineConfig()
_claude_semaphore = asyncio.Semaphore(_DEFAULT_PIPELINE_CONFIG.claude_cli_concurrency)
_research_semaphore = asyncio.Semaphore(_DEFAULT_PIPELINE_CONFIG.research_concurrency)


def _resolve_claude_model(tier: ModelTier, config: AppConfig) -> str:
    """Return the Claude CLI model ID for a tier, reading from AppConfig.

    Previously this was a hardcoded ``CLAUDE_MODEL_MAP`` that ignored
    configuration. The claude_cli path now reads ``AppConfig.flagship_model``
    / ``standard_model`` / ``fast_model`` so operators can swap models via
    env var without patching source.
    """
    mapping: dict[ModelTier, str] = {
        ModelTier.FLAGSHIP: config.flagship_model,
        ModelTier.STANDARD: config.standard_model,
        ModelTier.FAST: config.fast_model,
        ModelTier.LIGHT: config.fast_model,
    }
    return mapping.get(tier, config.standard_model)


# ---- Claude CLI transport ----


async def _call_claude_cli(
    prompt: str,
    model: str,
    effort: str,
    semaphore: asyncio.Semaphore,
    timeout_s: int = 600,
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
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
        except asyncio.TimeoutError:
            raise RuntimeError(f"claude -p timed out after {timeout_s}s (model={model})") from None
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
    timeout_s: int | None = None,
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
    - ``timeout_s`` seconds timeout (deep research sessions: many web
      searches + full page reads). The ``DEEP_RESEARCH_TIMEOUT`` env var
      overrides both the parameter and the default. Default (None) pulls
      from :class:`PipelineConfig.deep_research_timeout_s`.
    """
    if timeout_s is None:
        timeout_s = _DEFAULT_PIPELINE_CONFIG.deep_research_timeout_s
    legacy_override = os.environ.get("DEEP_RESEARCH_TIMEOUT")
    if legacy_override is not None:
        with contextlib.suppress(ValueError):
            timeout_s = int(legacy_override)

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
                timeout=timeout_s,
            )
        except asyncio.TimeoutError:
            raise RuntimeError(
                f"claude -p research timed out after {timeout_s}s (model={model})"
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


class LayerAwareLLMFactory:
    """LLM factory that resolves tier + effort + model ID from config.

    Three access patterns:

    - ``factory(tier)`` — backward-compat callable interface; returns an
      LLM at the tier's default effort.
    - ``factory.for_tier(tier, effort=<override>)`` — explicit tier, with
      an optional per-call effort override.
    - ``factory.for_layer(layer_name)`` — reads ``PipelineConfig`` to
      resolve the tier and reasoning effort for a named pipeline layer
      (e.g. ``"l0_specification"``).

    Semaphores controlling concurrency for the ``claude -p`` transports
    are instance-level so every pipeline run can tune them via
    :class:`PipelineConfig`. Instances share state across the components
    they build, so one factory per pipeline-run is the intended pattern.
    """

    def __init__(
        self,
        config: AppConfig,
        pipeline_config: PipelineConfig | None = None,
    ) -> None:
        self._config = config
        self._pipeline_config = pipeline_config or config.pipeline
        self._claude_semaphore = asyncio.Semaphore(self._pipeline_config.claude_cli_concurrency)
        self._research_semaphore = asyncio.Semaphore(self._pipeline_config.research_concurrency)

    @property
    def app_config(self) -> AppConfig:
        return self._config

    @property
    def pipeline_config(self) -> PipelineConfig:
        return self._pipeline_config

    def __call__(self, tier: ModelTier) -> LLMCallable:
        """Backward-compat shim: ``factory(tier)`` returns an LLM at tier default."""
        return self.for_tier(tier)

    def for_tier(
        self,
        tier: ModelTier,
        *,
        effort: str | None = None,
    ) -> LLMCallable:
        """Create an LLMCallable for a tier, with optional effort override."""
        effective_effort = effort if effort is not None else get_reasoning_effort(tier)
        return _build_llm_callable(
            tier,
            effective_effort,
            self._config,
            claude_semaphore=self._claude_semaphore,
        )

    def for_layer(self, layer_name: str) -> LLMCallable:
        """Create an LLMCallable configured for a named pipeline layer.

        Tier comes from ``PipelineConfig.model_mixing``; effort from
        ``PipelineConfig.layer_effort_overrides`` (falling back to the
        tier default when no override is set).
        """
        tier = get_layer_tier(layer_name, self._pipeline_config)
        effort = get_layer_effort(layer_name, tier, self._pipeline_config)
        return self.for_tier(tier, effort=effort)

    def deep_research_callable(self) -> LLMCallable:
        """Create an LLMCallable for deep web research via Claude CLI.

        Uses the standard tier's model (Sonnet by default) with WebSearch
        and WebFetch tools enabled, allowing multi-turn research
        sessions. Concurrency honors ``PipelineConfig.research_concurrency``
        and timeout honors ``PipelineConfig.deep_research_timeout_s``.
        """
        if os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError(
                "ANTHROPIC_API_KEY is set! claude -p will bill to API, "
                "not Max subscription. Run: unset ANTHROPIC_API_KEY"
            )

        model = _resolve_claude_model(ModelTier.STANDARD, self._config)
        timeout_s = self._pipeline_config.deep_research_timeout_s
        semaphore = self._research_semaphore

        async def _call_research(prompt: str) -> str:
            return await _call_claude_cli_research(prompt, model, semaphore, timeout_s)

        return _call_research


def _build_llm_callable(
    tier: ModelTier,
    effort: str,
    config: AppConfig,
    *,
    claude_semaphore: asyncio.Semaphore,
) -> LLMCallable:
    """Return an LLMCallable bound to the active provider transport.

    Split out of :class:`LayerAwareLLMFactory` so the module-level
    :func:`get_llm_for_tier` helper (legacy API) can share the same
    construction path without requiring a factory instance.
    """
    provider = _resolve_provider()

    if provider == "claude_cli":
        if os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError(
                "ANTHROPIC_API_KEY is set! claude -p will bill to API, "
                "not Max subscription. Run: unset ANTHROPIC_API_KEY"
            )
        model = _resolve_claude_model(tier, config)

        async def _call_claude(prompt: str) -> str:
            return await _call_claude_cli(prompt, model, effort, claude_semaphore)

        return _call_claude

    # Legacy OpenAI paths (api_key / codex_oauth)
    client = _get_cached_client(config)
    model_id = get_model_id(tier, config)
    is_oauth = provider == "codex_oauth"

    async def _call_llm(prompt: str) -> str:
        if is_oauth:
            return await _call_codex_oauth(client, model_id, effort, prompt)
        return await _call_standard_api(client, model_id, effort, prompt)

    return _call_llm


def get_llm_for_tier(
    tier: ModelTier,
    config: AppConfig,
    *,
    effort: str | None = None,
) -> LLMCallable:
    """Create an LLMCallable for a specific model tier.

    Legacy free-function API kept for call sites that construct one-off
    LLMs without a :class:`LayerAwareLLMFactory`. The factory is the
    recommended entry point because it owns the shared concurrency
    semaphores; this helper spins up its own semaphore per call and so
    should only be used outside a pipeline run.
    """
    effective_effort = effort if effort is not None else get_reasoning_effort(tier)
    semaphore = asyncio.Semaphore(config.pipeline.claude_cli_concurrency)
    return _build_llm_callable(
        tier,
        effective_effort,
        config,
        claude_semaphore=semaphore,
    )


def create_llm_factory(
    config: AppConfig,
    pipeline_config: PipelineConfig | None = None,
) -> LayerAwareLLMFactory:
    """Return a :class:`LayerAwareLLMFactory` bound to *config*.

    Usage::

        factory = create_llm_factory(AppConfig())
        spec_llm = factory.for_layer("l0_specification")  # xhigh effort
        sonnet = factory(ModelTier.STANDARD)              # backward-compat
        sonnet_xhigh = factory.for_tier(ModelTier.STANDARD, effort="xhigh")
    """
    return LayerAwareLLMFactory(config, pipeline_config)


def get_deep_research_callable(
    config: AppConfig | None = None,
    pipeline_config: PipelineConfig | None = None,
) -> LLMCallable:
    """Return an LLMCallable for deep web research via Claude CLI.

    Retained as a module-level helper for callers that do not hold a
    :class:`LayerAwareLLMFactory` instance. Internally constructs a
    short-lived factory so concurrency limits and model selection come
    from config.

    Configuration channels:
    - **Env vars** always take effect — omitting ``config`` builds a
      fresh :class:`AppConfig`, which re-reads its ``BaseSettings``
      sources (``.env`` + process environment). ``PIPELINE__...`` nested
      vars also flow through this path.
    - **Programmatic overrides** (e.g. ``AppConfig(standard_model=
      "custom-sonnet")``) only flow through when ``config`` is passed
      explicitly. Callers that built an AppConfig in code and want the
      deep-research path to honor model-ID overrides MUST pass that
      AppConfig here. The orchestrator routes through the active
      :class:`LayerAwareLLMFactory` when it has one, which preserves
      any programmatic overrides the factory was constructed with.
    """
    factory = LayerAwareLLMFactory(config or AppConfig(), pipeline_config)
    return factory.deep_research_callable()
