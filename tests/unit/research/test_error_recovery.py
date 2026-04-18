"""Tests for error recovery with retry and model fallback chain."""

import pytest

from keystone.models.tasks import ModelTier
from keystone.research.error_recovery import (
    ErrorCategory,
    ErrorRecovery,
    classify_error,
)


# ---------------------------------------------------------------------------
# Error classification
# ---------------------------------------------------------------------------


def test_classify_rate_limit() -> None:
    assert classify_error(Exception("rate limit exceeded")) == ErrorCategory.TRANSIENT


def test_classify_timeout() -> None:
    assert classify_error(Exception("request timed out")) == ErrorCategory.TRANSIENT


def test_classify_429() -> None:
    assert classify_error(Exception("HTTP 429")) == ErrorCategory.TRANSIENT


def test_classify_model_overloaded() -> None:
    assert classify_error(Exception("model overloaded")) == ErrorCategory.MODEL_ERROR


def test_classify_503() -> None:
    assert classify_error(Exception("HTTP 503")) == ErrorCategory.MODEL_ERROR


def test_classify_auth_error() -> None:
    assert classify_error(Exception("authentication failed")) == ErrorCategory.PERMANENT


def test_classify_permission_denied() -> None:
    assert classify_error(Exception("permission denied")) == ErrorCategory.PERMANENT


def test_classify_partial() -> None:
    assert classify_error(Exception("partial result")) == ErrorCategory.PARTIAL


def test_classify_unknown_defaults_transient() -> None:
    assert classify_error(Exception("something weird")) == ErrorCategory.TRANSIENT


# ---------------------------------------------------------------------------
# Retry with backoff
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_succeeds_on_first_try() -> None:
    async def good_llm(prompt: str) -> str:
        return "success"

    recovery = ErrorRecovery(max_retries=3, base_delay=0.01)
    result = await recovery.execute_with_recovery(good_llm, "test")
    assert result == "success"


@pytest.mark.asyncio
async def test_retries_transient_errors() -> None:
    call_count = 0

    async def flaky_llm(prompt: str) -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("rate limit exceeded")
        return "success after retries"

    recovery = ErrorRecovery(max_retries=3, base_delay=0.01)
    result = await recovery.execute_with_recovery(flaky_llm, "test")
    assert result == "success after retries"
    assert call_count == 3


@pytest.mark.asyncio
async def test_dead_letter_after_all_retries() -> None:
    async def always_fails(prompt: str) -> str:
        raise Exception("rate limit exceeded")

    recovery = ErrorRecovery(max_retries=2, base_delay=0.01)
    with pytest.raises(RuntimeError, match="failed after all retries"):
        await recovery.execute_with_recovery(always_fails, "test")


# ---------------------------------------------------------------------------
# Permanent errors: no retry
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_permanent_error_no_retry() -> None:
    call_count = 0

    async def auth_fail(prompt: str) -> str:
        nonlocal call_count
        call_count += 1
        raise Exception("authentication failed")

    recovery = ErrorRecovery(max_retries=3, base_delay=0.01)
    with pytest.raises(Exception, match="authentication"):
        await recovery.execute_with_recovery(auth_fail, "test")
    assert call_count == 1  # No retry on permanent errors


# ---------------------------------------------------------------------------
# Model fallback chain
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fallback_to_next_tier() -> None:
    tiers_tried: list[ModelTier] = []

    def make_llm(tier: ModelTier):
        async def llm(prompt: str) -> str:
            tiers_tried.append(tier)
            if tier == ModelTier.STANDARD:
                raise Exception("model overloaded")
            return f"success at {tier}"

        return llm

    recovery = ErrorRecovery(
        max_retries=1,
        base_delay=0.01,
        llm_factory=make_llm,
    )

    # Start at STANDARD, should fall back to FAST
    base_llm = make_llm(ModelTier.STANDARD)
    result = await recovery.execute_with_recovery(base_llm, "test", current_tier=ModelTier.STANDARD)
    assert result == f"success at {ModelTier.FAST}"
    assert ModelTier.STANDARD in tiers_tried
    assert ModelTier.FAST in tiers_tried


@pytest.mark.asyncio
async def test_fallback_chain_order() -> None:
    recovery = ErrorRecovery()
    tiers = recovery._get_fallback_tiers(ModelTier.FLAGSHIP)
    assert tiers == [ModelTier.FLAGSHIP, ModelTier.STANDARD, ModelTier.FAST]

    tiers = recovery._get_fallback_tiers(ModelTier.STANDARD)
    assert tiers == [ModelTier.STANDARD, ModelTier.FAST]

    tiers = recovery._get_fallback_tiers(ModelTier.FAST)
    assert tiers == [ModelTier.FAST]


@pytest.mark.asyncio
async def test_unknown_tier_uses_itself() -> None:
    recovery = ErrorRecovery()
    tiers = recovery._get_fallback_tiers(ModelTier.LIGHT)
    assert tiers == [ModelTier.LIGHT]


# ---------------------------------------------------------------------------
# llm_factory wiring (Task #13)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_error_recovery_uses_wired_llm_factory() -> None:
    """ErrorRecovery with wired llm_factory invokes factory to get fallback LLM."""
    tiers_requested: list[ModelTier] = []

    def factory(tier: ModelTier):
        async def llm(prompt: str) -> str:
            tiers_requested.append(tier)
            if tier == ModelTier.STANDARD:
                raise Exception("model overloaded")
            return f"ok from {tier}"

        return llm

    recovery = ErrorRecovery(max_retries=1, base_delay=0.0, llm_factory=factory)
    base_llm = factory(ModelTier.STANDARD)
    result = await recovery.execute_with_recovery(
        base_llm, "prompt", current_tier=ModelTier.STANDARD
    )

    # Factory must have been called for the fallback tier (FAST)
    assert ModelTier.FAST in tiers_requested
    assert result == f"ok from {ModelTier.FAST}"
