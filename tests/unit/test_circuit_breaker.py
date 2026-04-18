"""Tests for the MCP Gateway circuit breaker."""

import asyncio
import time

import pytest

from keystone.gateway.circuit_breaker import (
    CircuitBreaker,
    CircuitOpenError,
    CircuitState,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _succeed() -> str:
    return "ok"


async def _fail() -> None:
    raise ConnectionError("server down")


# ---------------------------------------------------------------------------
# State transitions
# ---------------------------------------------------------------------------


class TestStateTransitions:
    @pytest.mark.asyncio
    async def test_starts_closed(self) -> None:
        cb = CircuitBreaker(provider="test", failure_threshold=3)
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_stays_closed_on_success(self) -> None:
        cb = CircuitBreaker(provider="test", failure_threshold=3)
        result = await cb.call(_succeed)
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    @pytest.mark.asyncio
    async def test_closed_to_open_after_threshold(self) -> None:
        """CLOSED -> OPEN after 3 consecutive failures."""
        cb = CircuitBreaker(provider="test", failure_threshold=3)

        for _ in range(3):
            with pytest.raises(ConnectionError):
                await cb.call(_fail)

        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_open_rejects_calls(self) -> None:
        """OPEN state rejects calls with CircuitOpenError."""
        cb = CircuitBreaker(provider="test", failure_threshold=3, recovery_timeout=30.0)

        # Trip the circuit
        for _ in range(3):
            with pytest.raises(ConnectionError):
                await cb.call(_fail)

        # Next call should be rejected
        with pytest.raises(CircuitOpenError) as exc_info:
            await cb.call(_succeed)
        assert exc_info.value.provider == "test"

    @pytest.mark.asyncio
    async def test_open_to_half_open_after_timeout(self) -> None:
        """OPEN -> HALF_OPEN after recovery_timeout seconds."""
        cb = CircuitBreaker(provider="test", failure_threshold=3, recovery_timeout=0.1)

        # Trip the circuit
        for _ in range(3):
            with pytest.raises(ConnectionError):
                await cb.call(_fail)
        assert cb.state == CircuitState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(0.15)
        assert cb.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_half_open_to_closed_on_success(self) -> None:
        """HALF_OPEN -> CLOSED on successful probe."""
        cb = CircuitBreaker(provider="test", failure_threshold=3, recovery_timeout=0.1)

        # Trip and wait for half-open
        for _ in range(3):
            with pytest.raises(ConnectionError):
                await cb.call(_fail)
        await asyncio.sleep(0.15)
        assert cb.state == CircuitState.HALF_OPEN

        # Successful probe
        result = await cb.call(_succeed)
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    @pytest.mark.asyncio
    async def test_half_open_to_open_on_failure(self) -> None:
        """HALF_OPEN -> OPEN on failed probe."""
        cb = CircuitBreaker(provider="test", failure_threshold=3, recovery_timeout=0.1)

        # Trip and wait for half-open
        for _ in range(3):
            with pytest.raises(ConnectionError):
                await cb.call(_fail)
        await asyncio.sleep(0.15)
        assert cb.state == CircuitState.HALF_OPEN

        # Failed probe
        with pytest.raises(ConnectionError):
            await cb.call(_fail)
        assert cb.state == CircuitState.OPEN


# ---------------------------------------------------------------------------
# Failure counting
# ---------------------------------------------------------------------------


class TestFailureCounting:
    @pytest.mark.asyncio
    async def test_failure_count_increments(self) -> None:
        cb = CircuitBreaker(provider="test", failure_threshold=5)
        with pytest.raises(ConnectionError):
            await cb.call(_fail)
        assert cb.failure_count == 1

        with pytest.raises(ConnectionError):
            await cb.call(_fail)
        assert cb.failure_count == 2

    @pytest.mark.asyncio
    async def test_success_resets_failure_count(self) -> None:
        cb = CircuitBreaker(provider="test", failure_threshold=5)

        # 2 failures
        for _ in range(2):
            with pytest.raises(ConnectionError):
                await cb.call(_fail)
        assert cb.failure_count == 2

        # 1 success resets
        await cb.call(_succeed)
        assert cb.failure_count == 0


# ---------------------------------------------------------------------------
# Manual reset
# ---------------------------------------------------------------------------


class TestReset:
    @pytest.mark.asyncio
    async def test_manual_reset(self) -> None:
        cb = CircuitBreaker(provider="test", failure_threshold=3)

        # Trip the circuit
        for _ in range(3):
            with pytest.raises(ConnectionError):
                await cb.call(_fail)
        assert cb.state == CircuitState.OPEN

        # Manual reset
        await cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

        # Should work again
        result = await cb.call(_succeed)
        assert result == "ok"
