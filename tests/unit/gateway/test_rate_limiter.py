"""Tests for the token-bucket rate limiter."""

import asyncio
from unittest.mock import patch

import pytest

from keystone.gateway.rate_limiter import InMemoryRateLimiter, RateLimit, RateLimiterBackend


def _make_limiter(**provider_limits) -> InMemoryRateLimiter:
    limits = {}
    for provider, (max_tokens, refill_rate) in provider_limits.items():
        limits[provider] = RateLimit(max_tokens=max_tokens, refill_rate=refill_rate)
    return limits and InMemoryRateLimiter(limits) or InMemoryRateLimiter({})


class TestTokenBucket:
    @pytest.mark.asyncio
    async def test_allows_within_capacity(self):
        limiter = _make_limiter(exa=(5, 1.0))

        for _ in range(5):
            assert await limiter.try_acquire("exa")

    @pytest.mark.asyncio
    async def test_rejects_when_exhausted(self):
        limiter = _make_limiter(exa=(3, 1.0))

        for _ in range(3):
            assert await limiter.try_acquire("exa")

        assert not await limiter.try_acquire("exa")

    @pytest.mark.asyncio
    async def test_refills_over_time(self):
        limiter = _make_limiter(exa=(2, 100.0))  # Fast refill: 100 tokens/sec

        # Exhaust bucket
        assert await limiter.try_acquire("exa")
        assert await limiter.try_acquire("exa")
        assert not await limiter.try_acquire("exa")

        # Wait for refill (100 tokens/sec = 1 token per 10ms)
        await asyncio.sleep(0.05)  # 50ms = ~5 tokens refilled

        assert await limiter.try_acquire("exa")

    @pytest.mark.asyncio
    async def test_per_provider_isolation(self):
        limiter = _make_limiter(exa=(2, 1.0), brave=(3, 1.0))

        # Exhaust exa
        assert await limiter.try_acquire("exa")
        assert await limiter.try_acquire("exa")
        assert not await limiter.try_acquire("exa")

        # Brave should still have capacity
        assert await limiter.try_acquire("brave")
        assert await limiter.try_acquire("brave")
        assert await limiter.try_acquire("brave")

    @pytest.mark.asyncio
    async def test_unknown_provider_allowed(self):
        """Providers without configured limits are allowed through."""
        limiter = _make_limiter(exa=(2, 1.0))
        assert await limiter.try_acquire("unknown_provider")

    @pytest.mark.asyncio
    async def test_multi_token_acquire(self):
        limiter = _make_limiter(exa=(10, 1.0))

        assert await limiter.try_acquire("exa", tokens=5)
        assert await limiter.try_acquire("exa", tokens=5)
        assert not await limiter.try_acquire("exa", tokens=1)

    @pytest.mark.asyncio
    async def test_get_remaining(self):
        limiter = _make_limiter(exa=(5, 1.0))

        assert await limiter.get_remaining("exa") == 5
        await limiter.try_acquire("exa", tokens=2)
        assert await limiter.get_remaining("exa") == 3

    @pytest.mark.asyncio
    async def test_get_remaining_unknown_provider(self):
        limiter = _make_limiter(exa=(5, 1.0))
        assert await limiter.get_remaining("unknown") == -1

    def test_get_retry_after(self):
        limiter = _make_limiter(exa=(5, 2.0))
        # When bucket is full, retry_after should be 0
        assert limiter.get_retry_after("exa") == 0.0

    def test_get_retry_after_unknown(self):
        limiter = _make_limiter(exa=(5, 1.0))
        assert limiter.get_retry_after("unknown") == 0.0

    @pytest.mark.asyncio
    async def test_bucket_does_not_exceed_capacity(self):
        """Tokens should never exceed max_tokens after refill."""
        limiter = _make_limiter(exa=(3, 100.0))

        # Wait to accumulate tokens
        await asyncio.sleep(0.1)

        remaining = await limiter.get_remaining("exa")
        assert remaining <= 3


class TestRateLimiterBackend:
    def test_inmemory_implements_protocol(self):
        limiter = _make_limiter(exa=(5, 1.0))
        assert isinstance(limiter, RateLimiterBackend)
