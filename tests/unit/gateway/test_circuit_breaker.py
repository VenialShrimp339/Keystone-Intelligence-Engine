"""Tests for the per-provider circuit breaker."""

import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest

from keystone.gateway.circuit_breaker import (
    CircuitBreaker,
    CircuitOpenError,
    CircuitState,
)


async def _success():
    return "ok"


async def _failure():
    raise ConnectionError("server unreachable")


class TestCircuitBreakerStates:
    @pytest.mark.asyncio
    async def test_closed_stays_closed_on_success(self):
        cb = CircuitBreaker("test-provider", failure_threshold=3)
        result = await cb.call(_success)

        assert result == "ok"
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_closed_to_open_after_threshold_failures(self):
        cb = CircuitBreaker("test-provider", failure_threshold=3)

        for _ in range(3):
            with pytest.raises(ConnectionError):
                await cb.call(_failure)

        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_open_rejects_calls(self):
        cb = CircuitBreaker("test-provider", failure_threshold=1, recovery_timeout=30.0)

        with pytest.raises(ConnectionError):
            await cb.call(_failure)

        assert cb.state == CircuitState.OPEN

        with pytest.raises(CircuitOpenError) as exc_info:
            await cb.call(_success)

        assert exc_info.value.provider == "test-provider"
        assert exc_info.value.retry_after > 0

    @pytest.mark.asyncio
    async def test_open_to_half_open_after_timeout(self):
        cb = CircuitBreaker("test-provider", failure_threshold=1, recovery_timeout=0.05)

        with pytest.raises(ConnectionError):
            await cb.call(_failure)

        assert cb.state == CircuitState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(0.1)

        assert cb.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_half_open_to_closed_on_success(self):
        cb = CircuitBreaker("test-provider", failure_threshold=1, recovery_timeout=0.05)

        with pytest.raises(ConnectionError):
            await cb.call(_failure)

        await asyncio.sleep(0.1)
        assert cb.state == CircuitState.HALF_OPEN

        result = await cb.call(_success)
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    @pytest.mark.asyncio
    async def test_half_open_to_open_on_failure(self):
        cb = CircuitBreaker("test-provider", failure_threshold=1, recovery_timeout=0.05)

        with pytest.raises(ConnectionError):
            await cb.call(_failure)

        await asyncio.sleep(0.1)
        assert cb.state == CircuitState.HALF_OPEN

        with pytest.raises(ConnectionError):
            await cb.call(_failure)

        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_success_resets_failure_count(self):
        cb = CircuitBreaker("test-provider", failure_threshold=3)

        # 2 failures (below threshold)
        for _ in range(2):
            with pytest.raises(ConnectionError):
                await cb.call(_failure)

        assert cb.failure_count == 2

        # Success resets count
        await cb.call(_success)
        assert cb.failure_count == 0
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_manual_reset(self):
        cb = CircuitBreaker("test-provider", failure_threshold=1)

        with pytest.raises(ConnectionError):
            await cb.call(_failure)

        assert cb.state == CircuitState.OPEN

        await cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0


class TestCircuitBreakerConfig:
    def test_default_config(self):
        cb = CircuitBreaker("test-provider")
        assert cb.failure_threshold == 3
        assert cb.recovery_timeout == 30.0

    def test_custom_config(self):
        cb = CircuitBreaker("test-provider", failure_threshold=5, recovery_timeout=60.0)
        assert cb.failure_threshold == 5
        assert cb.recovery_timeout == 60.0


class TestCircuitOpenError:
    def test_error_attributes(self):
        err = CircuitOpenError("exa-server", 15.0)
        assert err.provider == "exa-server"
        assert err.retry_after == 15.0
        assert "OPEN" in str(err)
