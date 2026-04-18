"""Error recovery with retry and model fallback chain.

Retry with exponential backoff (reuses the retry_llm_call pattern).
Model fallback chain: flagship -> standard -> fast.
Error classification drives recovery strategy.

Directive 9: every call has max retries with exponential backoff.
Dead-letter logging after exhaustion.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from enum import StrEnum

from keystone.evaluator.retry import LLMCallable
from keystone.models.tasks import ModelTier

logger = logging.getLogger(__name__)


class ErrorCategory(StrEnum):
    """Classification of errors for recovery strategy selection."""

    TRANSIENT = "transient"
    MODEL_ERROR = "model_error"
    PERMANENT = "permanent"
    PARTIAL = "partial"


FALLBACK_CHAIN: list[ModelTier] = [
    ModelTier.FLAGSHIP,
    ModelTier.STANDARD,
    ModelTier.FAST,
]


def classify_error(error: Exception) -> ErrorCategory:
    """Classify an error to select recovery strategy."""
    msg = str(error).lower()

    if any(kw in msg for kw in ("rate limit", "429", "timeout", "timed out")):
        return ErrorCategory.TRANSIENT
    if any(kw in msg for kw in ("overloaded", "capacity", "503", "model")):
        return ErrorCategory.MODEL_ERROR
    if any(kw in msg for kw in ("auth", "401", "403", "invalid", "permission")):
        return ErrorCategory.PERMANENT
    if "partial" in msg:
        return ErrorCategory.PARTIAL

    return ErrorCategory.TRANSIENT


class ErrorRecovery:
    """Error recovery with retry and model fallback chain.

    1. Retry with exponential backoff at current tier
    2. On model errors, fall back to next tier in chain
    3. Dead-letter after all retries and fallbacks exhausted
    """

    def __init__(
        self,
        *,
        max_retries: int = 3,
        base_delay: float = 1.0,
        llm_factory: Callable[[ModelTier], LLMCallable] | None = None,
    ) -> None:
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._llm_factory = llm_factory

    async def execute_with_recovery(
        self,
        llm: LLMCallable,
        prompt: str,
        *,
        current_tier: ModelTier = ModelTier.STANDARD,
        description: str = "",
    ) -> str:
        """Execute an LLM call with retry and model fallback."""
        last_error: Exception | None = None
        tiers_to_try = self._get_fallback_tiers(current_tier)

        for tier in tiers_to_try:
            active_llm = llm
            if tier != current_tier and self._llm_factory:
                active_llm = self._llm_factory(tier)

            for attempt in range(self._max_retries):
                try:
                    return await active_llm(prompt)
                except Exception as exc:  # noqa: BLE001
                    last_error = exc
                    category = classify_error(exc)

                    if category == ErrorCategory.PERMANENT:
                        raise

                    if category == ErrorCategory.MODEL_ERROR:
                        logger.warning(
                            "Model error at tier %s (attempt %d/%d, %s): %s. "
                            "Falling back to next tier.",
                            tier,
                            attempt + 1,
                            self._max_retries,
                            description or "unnamed",
                            exc,
                        )
                        break  # Skip to next tier

                    if attempt < self._max_retries - 1:
                        delay = self._base_delay * (2**attempt)
                        logger.warning(
                            "Transient error (attempt %d/%d, %s): %s. Retrying in %.1fs.",
                            attempt + 1,
                            self._max_retries,
                            description or "unnamed",
                            exc,
                            delay,
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.warning(
                            "Retries exhausted at tier %s (%s): %s.",
                            tier,
                            description or "unnamed",
                            exc,
                        )

        msg = f"LLM call '{description}' failed after all retries and fallbacks: {last_error}"
        raise RuntimeError(msg)

    def _get_fallback_tiers(self, current: ModelTier) -> list[ModelTier]:
        """Return ordered list of tiers to try, starting from current."""
        if current in FALLBACK_CHAIN:
            idx = FALLBACK_CHAIN.index(current)
            return FALLBACK_CHAIN[idx:]
        return [current]
