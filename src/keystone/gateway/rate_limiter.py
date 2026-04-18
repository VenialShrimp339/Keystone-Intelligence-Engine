"""Token-bucket rate limiter for the MCP Gateway.

Per-provider rate limiting prevents exceeding external API quotas.
Phase 1 uses in-memory buckets. Phase 2 swaps to Redis backend
via the RateLimiterBackend protocol (drop-in replacement).

Token-bucket math extracted from mcp-gateway's RateLimitBucket
(core/state.py): monotonic clock for timing, async lock for
thread safety, configurable capacity and refill rate.
"""

from __future__ import annotations

import asyncio
import time
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field


class RateLimit(BaseModel):
    """Rate limit configuration for a single provider."""

    max_tokens: int = Field(ge=1, description="Bucket capacity (max burst)")
    refill_rate: float = Field(gt=0, description="Tokens added per second")
    refill_interval: float = Field(
        default=1.0, gt=0, description="Seconds between refill calculations"
    )


class RateLimitExceeded(Exception):
    """Provider rate limit has been exceeded."""

    def __init__(self, provider: str, retry_after: float) -> None:
        self.provider = provider
        self.retry_after = retry_after
        super().__init__(
            f"Rate limit exceeded for provider '{provider}'. Retry after {retry_after:.1f}s"
        )


@runtime_checkable
class RateLimiterBackend(Protocol):
    """Backend interface for rate limit state.

    In-memory for Phase 1, Redis for Phase 2. The gateway only
    depends on this protocol, making Redis a drop-in replacement.
    """

    async def try_acquire(self, key: str, tokens: int = 1) -> bool:
        """Attempt to acquire tokens. Returns True if allowed."""
        ...

    async def get_remaining(self, key: str) -> int:
        """Return remaining tokens in the bucket."""
        ...


class _TokenBucket:
    """Single token bucket with monotonic clock timing.

    Extracted from mcp-gateway's RateLimitBucket pattern.
    Uses time.monotonic() to avoid wall-clock drift issues.
    """

    def __init__(self, limit: RateLimit) -> None:
        self.capacity = limit.max_tokens
        self.refill_rate = limit.refill_rate
        self.tokens = float(limit.max_tokens)
        self.last_refill = time.monotonic()
        self.lock = asyncio.Lock()

    def _refill(self) -> None:
        """Add tokens based on elapsed time since last refill."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.refill_rate,
        )
        self.last_refill = now

    async def try_acquire(self, tokens: int = 1) -> bool:
        """Attempt to consume tokens from the bucket."""
        async with self.lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    async def get_remaining(self) -> int:
        """Return current token count (after refill)."""
        async with self.lock:
            self._refill()
            return int(self.tokens)

    def time_until_available(self, tokens: int = 1) -> float:
        """Estimate seconds until tokens become available."""
        deficit = tokens - self.tokens
        if deficit <= 0:
            return 0.0
        return deficit / self.refill_rate


class InMemoryRateLimiter:
    """Token-bucket rate limiter with configurable per-provider limits.

    Implements the RateLimiterBackend protocol for Phase 1.
    Each provider gets its own independent bucket.
    """

    def __init__(self, limits: dict[str, RateLimit]) -> None:
        self._buckets: dict[str, _TokenBucket] = {
            provider: _TokenBucket(limit) for provider, limit in limits.items()
        }
        self._limits = limits

    async def try_acquire(self, key: str, tokens: int = 1) -> bool:
        """Attempt to acquire tokens for a provider.

        Returns True if the provider has capacity, False if exhausted.
        Unknown providers are allowed through (no rate limit configured).
        """
        bucket = self._buckets.get(key)
        if bucket is None:
            return True  # No rate limit configured for this provider
        return await bucket.try_acquire(tokens)

    async def get_remaining(self, key: str) -> int:
        """Return remaining tokens for a provider."""
        bucket = self._buckets.get(key)
        if bucket is None:
            return -1  # No rate limit configured
        return await bucket.get_remaining()

    def get_retry_after(self, key: str, tokens: int = 1) -> float:
        """Estimate seconds until tokens are available for a provider."""
        bucket = self._buckets.get(key)
        if bucket is None:
            return 0.0
        return bucket.time_until_available(tokens)
