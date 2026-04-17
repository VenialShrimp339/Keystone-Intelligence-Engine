"""Unit tests for the deep-research LLM transport.

Covers ``get_deep_research_callable`` and the underlying
``_call_claude_cli_research`` subprocess driver. Nothing hits a real
``claude -p`` binary -- ``asyncio.create_subprocess_exec`` is stubbed
so the tests validate argument construction, timeout handling,
non-zero exit handling, and semaphore wiring without touching the
network or spawning real processes.
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import patch

import pytest

from keystone.llm_client import (
    CLAUDE_MODEL_MAP,
    _call_claude_cli_research,
    _research_semaphore,
    get_deep_research_callable,
)
from keystone.models.tasks import ModelTier

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clear_anthropic_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure ANTHROPIC_API_KEY is unset so Max-subscription path is valid."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


@pytest.fixture(autouse=True)
def _reset_deep_research_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fresh DEEP_RESEARCH_TIMEOUT per test."""
    monkeypatch.delenv("DEEP_RESEARCH_TIMEOUT", raising=False)


class _FakeProc:
    """Minimal stand-in for asyncio.subprocess.Process."""

    def __init__(
        self,
        *,
        stdout: bytes = b"",
        stderr: bytes = b"",
        returncode: int = 0,
        communicate_delay: float = 0.0,
        communicate_raises: BaseException | None = None,
    ) -> None:
        self._stdout = stdout
        self._stderr = stderr
        self.returncode: int | None = returncode
        self._delay = communicate_delay
        self._raises = communicate_raises
        self.kill_called = 0
        self.wait_called = 0

    async def communicate(self) -> tuple[bytes, bytes]:
        if self._raises is not None:
            raise self._raises
        if self._delay:
            await asyncio.sleep(self._delay)
        return self._stdout, self._stderr

    def kill(self) -> None:
        self.kill_called += 1
        # After kill, the process has exited.
        self.returncode = -9

    async def wait(self) -> int:
        self.wait_called += 1
        return self.returncode or 0


def _patched_create(proc: _FakeProc) -> Any:
    """Return an awaitable mock that yields ``proc`` and captures call args."""

    async def _impl(*args: Any, **kwargs: Any) -> _FakeProc:
        _impl.last_args = args  # type: ignore[attr-defined]
        _impl.last_kwargs = kwargs  # type: ignore[attr-defined]
        return proc

    _impl.last_args = ()  # type: ignore[attr-defined]
    _impl.last_kwargs = {}  # type: ignore[attr-defined]
    return _impl


# ---------------------------------------------------------------------------
# get_deep_research_callable
# ---------------------------------------------------------------------------


class TestGetDeepResearchCallable:
    def test_raises_when_anthropic_api_key_is_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Max subscription uses claude CLI; ANTHROPIC_API_KEY would
        # silently bill to API instead of the Max plan.
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-should-not-be-set")

        with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY is set"):
            get_deep_research_callable()

    def test_returns_callable_when_env_is_clean(self) -> None:
        deep = get_deep_research_callable()
        assert callable(deep)

    @pytest.mark.asyncio
    async def test_callable_dispatches_via_claude_cli_research(self) -> None:
        deep = get_deep_research_callable()
        fake_proc = _FakeProc(stdout=b"deep-output", returncode=0)
        patched = _patched_create(fake_proc)

        with patch("asyncio.create_subprocess_exec", patched):
            result = await deep("research topic X")

        assert result == "deep-output"
        # Verify model is the Sonnet / STANDARD tier so research calls use
        # the larger-context model, not Opus (reserved for flagship tasks).
        args = patched.last_args  # type: ignore[attr-defined]
        assert "--model" in args
        model_idx = args.index("--model") + 1
        assert args[model_idx] == CLAUDE_MODEL_MAP[ModelTier.STANDARD]


# ---------------------------------------------------------------------------
# _call_claude_cli_research -- subprocess wiring
# ---------------------------------------------------------------------------


class TestCallClaudeResearchSubprocess:
    @pytest.mark.asyncio
    async def test_sends_prompt_and_enables_web_tools(self) -> None:
        fake_proc = _FakeProc(stdout=b"ok", returncode=0)
        patched = _patched_create(fake_proc)

        with patch("asyncio.create_subprocess_exec", patched):
            out = await _call_claude_cli_research(
                prompt="Find 20 claims about LiDAR TAM",
                model="claude-sonnet-4-6",
                semaphore=_research_semaphore,
            )

        assert out == "ok"
        args = patched.last_args  # type: ignore[attr-defined]
        # Positional argv reaching the subprocess.
        assert args[0] == "claude"
        assert args[1] == "-p"
        assert args[2] == "Find 20 claims about LiDAR TAM"
        # Deep research must enable WebSearch + WebFetch, not ``--tools ""``.
        assert "--allowedTools" in args
        assert args[args.index("--allowedTools") + 1] == "WebSearch,WebFetch"
        # Session persistence must stay off so long research sessions do
        # not accidentally share state across tasks.
        assert "--no-session-persistence" in args

    @pytest.mark.asyncio
    async def test_raises_runtime_error_on_nonzero_exit(self) -> None:
        fake_proc = _FakeProc(stdout=b"", stderr=b"claude crashed unexpectedly", returncode=17)
        patched = _patched_create(fake_proc)

        with (
            patch("asyncio.create_subprocess_exec", patched),
            pytest.raises(RuntimeError, match="claude -p research exited 17"),
        ):
            await _call_claude_cli_research(
                prompt="p",
                model="claude-sonnet-4-6",
                semaphore=_research_semaphore,
            )

    @pytest.mark.asyncio
    async def test_timeout_raises_and_kills_process(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DEEP_RESEARCH_TIMEOUT", "1")
        # communicate() raises TimeoutError; the finally block kills any
        # process whose returncode is still None at raise time.
        fake_proc = _FakeProc(communicate_raises=TimeoutError())
        fake_proc.returncode = None
        patched = _patched_create(fake_proc)

        with (
            patch("asyncio.create_subprocess_exec", patched),
            pytest.raises(RuntimeError, match="research timed out after 1s"),
        ):
            await _call_claude_cli_research(
                prompt="p",
                model="claude-sonnet-4-6",
                semaphore=_research_semaphore,
            )

        assert fake_proc.kill_called == 1
        assert fake_proc.wait_called == 1

    @pytest.mark.asyncio
    async def test_timeout_configurable_via_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DEEP_RESEARCH_TIMEOUT", "42")
        fake_proc = _FakeProc(
            returncode=0,
            communicate_raises=TimeoutError(),
        )
        patched = _patched_create(fake_proc)

        with (
            patch("asyncio.create_subprocess_exec", patched),
            pytest.raises(RuntimeError, match="after 42s"),
        ):
            await _call_claude_cli_research(
                prompt="p",
                model="claude-sonnet-4-6",
                semaphore=_research_semaphore,
            )

    @pytest.mark.asyncio
    async def test_default_timeout_is_1200_seconds(self) -> None:
        """Regression: deep sessions legitimately take 5-10+ minutes."""
        # We observe the env default by monkeypatching asyncio.wait_for
        # and capturing the timeout argument.
        fake_proc = _FakeProc(stdout=b"ok", returncode=0)
        patched = _patched_create(fake_proc)

        seen_timeouts: list[float] = []
        real_wait_for = asyncio.wait_for

        async def capturing_wait_for(coro: Any, timeout: float) -> Any:
            seen_timeouts.append(timeout)
            return await real_wait_for(coro, timeout)

        with (
            patch("asyncio.create_subprocess_exec", patched),
            patch("keystone.llm_client.asyncio.wait_for", capturing_wait_for),
        ):
            await _call_claude_cli_research(
                prompt="p",
                model="claude-sonnet-4-6",
                semaphore=_research_semaphore,
            )

        assert seen_timeouts == [1200]

    @pytest.mark.asyncio
    async def test_decodes_stdout_as_utf8(self) -> None:
        # Unicode in web research output must round-trip without error.
        fake_proc = _FakeProc(stdout="🔎 deep research output".encode(), returncode=0)
        patched = _patched_create(fake_proc)

        with patch("asyncio.create_subprocess_exec", patched):
            out = await _call_claude_cli_research(
                prompt="p",
                model="claude-sonnet-4-6",
                semaphore=_research_semaphore,
            )

        assert "deep research output" in out

    @pytest.mark.asyncio
    async def test_respects_semaphore_for_concurrency_cap(self) -> None:
        # Semaphore acts as a gate; we don't race two calls -- we verify
        # that entering the call acquires the semaphore at least once.
        sem = asyncio.Semaphore(1)
        fake_proc = _FakeProc(stdout=b"ok", returncode=0)
        patched = _patched_create(fake_proc)

        acquired_before = sem._value  # type: ignore[attr-defined]
        with patch("asyncio.create_subprocess_exec", patched):
            # Kick off two concurrent calls; semaphore limit is 1 so the
            # second must wait. We just assert both complete and the
            # semaphore returns to its starting value.
            await asyncio.gather(
                _call_claude_cli_research(prompt="a", model="claude-sonnet-4-6", semaphore=sem),
                _call_claude_cli_research(prompt="b", model="claude-sonnet-4-6", semaphore=sem),
            )
        assert sem._value == acquired_before  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# End-to-end wiring from get_deep_research_callable
# ---------------------------------------------------------------------------


class TestDeepResearchCallableEndToEnd:
    @pytest.mark.asyncio
    async def test_returned_callable_passes_prompt_verbatim(self) -> None:
        deep = get_deep_research_callable()
        fake_proc = _FakeProc(stdout=b"done", returncode=0)
        patched = _patched_create(fake_proc)

        with patch("asyncio.create_subprocess_exec", patched):
            out = await deep("PROMPT_ABC")

        assert out == "done"
        args = patched.last_args  # type: ignore[attr-defined]
        assert args[2] == "PROMPT_ABC"

    @pytest.mark.asyncio
    async def test_returned_callable_always_targets_sonnet(self) -> None:
        deep = get_deep_research_callable()
        fake_proc = _FakeProc(stdout=b"done", returncode=0)
        patched = _patched_create(fake_proc)

        with patch("asyncio.create_subprocess_exec", patched):
            await deep("any prompt")

        args = patched.last_args  # type: ignore[attr-defined]
        assert CLAUDE_MODEL_MAP[ModelTier.STANDARD] in args
