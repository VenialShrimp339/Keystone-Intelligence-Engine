"""Retry wrapper for all LLM calls in the Evaluator (Directive 9).

Every LLM call must flow through retry_llm_call. Exponential backoff
with dead-letter after max retries exhausted. No silent swallowing.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)

LLMCallable = Callable[[str], Awaitable[str]]


async def retry_llm_call(
    llm: LLMCallable,
    prompt: str,
    *,
    max_retries: int = 3,
    base_delay: float = 1.0,
    description: str = "",
) -> str:
    """Call an LLM with exponential backoff retry.

    Delays: base_delay * 2^attempt (1s, 2s, 4s for defaults).
    Raises RuntimeError after max_retries exhausted (dead-letter).
    Logs each retry attempt with the description for debugging.

    Args:
        llm: Async callable that takes a prompt string and returns a response.
        prompt: The prompt to send.
        max_retries: Maximum number of retry attempts.
        base_delay: Base delay in seconds for exponential backoff.
        description: Human-readable label for log messages.

    Returns:
        The LLM response string.

    Raises:
        RuntimeError: After all retries exhausted.
    """
    last_error: Exception | None = None

    for attempt in range(max_retries):
        try:
            return await llm(prompt)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt)
                logger.warning(
                    "LLM call failed (attempt %d/%d, %s): %s. Retrying in %.1fs.",
                    attempt + 1,
                    max_retries,
                    description or "unnamed",
                    exc,
                    delay,
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    "LLM call dead-lettered after %d attempts (%s): %s",
                    max_retries,
                    description or "unnamed",
                    exc,
                )

    msg = (
        f"LLM call '{description}' failed after {max_retries} retries: {last_error}"
    )
    raise RuntimeError(msg)
