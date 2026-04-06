"""Tests for the MCP Gateway token-bucket rate limiter."""

import time
from unittest.mock import patch

import pytest

from keystone.gateway.rate_limiter import (
    InMemoryRateLimiter,
    RateLimit,
    RateLimiterBackend,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def limiter() -> InMemoryRateLimiter:
    """Rate limiter with 5 tokens, 1 token/second refill for exa."""
    limits = {
        "exa-mcp-server": RateLimit(max_tokens=5, refill_rate=1.0),
        "brave-search-mcp-server": RateLimit(max_tokens=3, refill_rate=0.5),
    }
    return InMemoryRateLimiter(limits)


# ---------------------------------------------------------------------------
# Token bucket basics
# ---------------------------------------------------------------------------

class TestTokenBucket:
    @pytest.mark.asyncio
    async def test_allows_within_capacity(self, limiter: InMemoryRateLimiter) -> None:
        """Calls within bucket capacity are allowed."""
        for _ in range(5):
            assert await limiter.try_acquire("exa-mcp-server") is True

    @pytest.mark.asyncio
    async def test_rejects_when_exhausted(self, limiter: InMemoryRateLimiter) -> None:
        """Calls beyond bucket capacity are rejected."""
        for _ in range(5):
            await limiter.try_acquire("exa-mcp-server")
        assert await limiter.try_acquire("exa-mcp-server") is False

    @pytest.mark.asyncio
    async def test_tokens_refill_over_time(self, limiter: InMemoryRateLimiter) -> None:
        """Tokens refill after time passes."""
        # Exhaust bucket
        for _ in range(5):
            await limiter.try_acquire("exa-mcp-server")
        assert await limiter.try_acquire("exa-mcp-server") is False

        # Simulate 3 seconds passing (should refill 3 tokens at 1/sec)
        bucket = limiter._buckets["exa-mcp-server"]
        bucket.last_refill = time.monotonic() - 3.0

        assert await limiter.try_acquire("exa-mcp-server") is True

    @pytest.mark.asyncio
    async def test_refill_capped_at_max(self, limiter: InMemoryRateLimiter) -> None:
        """Tokens don't exceed bucket capacity after refill."""
        bucket = limiter._buckets["exa-mcp-server"]
        # Simulate long time passing
        bucket.last_refill = time.monotonic() - 1000.0

        remaining = await limiter.get_remaining("exa-mcp-server")
        assert remaining <= 5


# ---------------------------------------------------------------------------
# Per-provider isolation
# ---------------------------------------------------------------------------

class TestProviderIsolation:
    @pytest.mark.asyncio
    async def test_separate_buckets(self, limiter: InMemoryRateLimiter) -> None:
        """Each provider has its own independent bucket."""
        # Exhaust exa
        for _ in range(5):
            await limiter.try_acquire("exa-mcp-server")
        assert await limiter.try_acquire("exa-mcp-server") is False

        # Brave should still have capacity
        assert await limiter.try_acquire("brave-search-mcp-server") is True

    @pytest.mark.asyncio
    async def test_unknown_provider_allowed(self, limiter: InMemoryRateLimiter) -> None:
        """Providers without configured limits are allowed through."""
        assert await limiter.try_acquire("unknown-server") is True

    @pytest.mark.asyncio
    async def test_unknown_provider_remaining(self, limiter: InMemoryRateLimiter) -> None:
        """Unknown provider returns -1 for remaining."""
        remaining = await limiter.get_remaining("unknown-server")
        assert remaining == -1


# ---------------------------------------------------------------------------
# get_remaining and get_retry_after
# ---------------------------------------------------------------------------

class TestUtilities:
    @pytest.mark.asyncio
    async def test_get_remaining(self, limiter: InMemoryRateLimiter) -> None:
        remaining = await limiter.get_remaining("exa-mcp-server")
        assert remaining == 5

        await limiter.try_acquire("exa-mcp-server")
        remaining = await limiter.get_remaining("exa-mcp-server")
        assert remaining == 4

    def test_get_retry_after_when_empty(self, limiter: InMemoryRateLimiter) -> None:
        """Retry-after is positive when bucket is empty."""
        bucket = limiter._buckets["exa-mcp-server"]
        bucket.tokens = 0.0
        retry = limiter.get_retry_after("exa-mcp-server")
        assert retry > 0

    def test_get_retry_after_when_available(self, limiter: InMemoryRateLimiter) -> None:
        """Retry-after is 0 when tokens are available."""
        retry = limiter.get_retry_after("exa-mcp-server")
        assert retry == 0.0


# ---------------------------------------------------------------------------
# Protocol compliance
# ---------------------------------------------------------------------------

class TestProtocol:
    def test_implements_backend_protocol(self) -> None:
        """InMemoryRateLimiter satisfies the RateLimiterBackend protocol."""
        assert isinstance(InMemoryRateLimiter({}), RateLimiterBackend)
