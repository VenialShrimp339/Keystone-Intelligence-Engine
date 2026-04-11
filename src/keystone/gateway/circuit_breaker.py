"""Per-provider circuit breaker for the MCP Gateway.

State machine: CLOSED -> OPEN (after failure_threshold failures)
               OPEN -> HALF_OPEN (after recovery_timeout seconds)
               HALF_OPEN -> CLOSED (on success) or OPEN (on failure)

Pattern extracted from mcp-gateway's middleware/circuit_breaker.py:
async-lock-guarded state transitions, monotonic clock for timing,
configurable failure threshold and recovery timeout.

Defaults: 3 failures -> OPEN, 30s recovery -> HALF_OPEN (per spec).
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from enum import StrEnum
from typing import Any


class CircuitState(StrEnum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    """Circuit breaker is OPEN, rejecting calls."""

    def __init__(self, provider: str, retry_after: float) -> None:
        self.provider = provider
        self.retry_after = retry_after
        super().__init__(
            f"Circuit breaker OPEN for provider '{provider}'. "
            f"Retry after {retry_after:.1f}s"
        )


class CircuitBreaker:
    """Per-provider circuit breaker.

    Tracks consecutive failures per provider. Opens the circuit after
    failure_threshold failures. After recovery_timeout seconds, transitions
    to HALF_OPEN and allows a single probe call.

    Thread-safe via asyncio.Lock (extracted from mcp-gateway pattern).
    Uses time.monotonic() for timing to avoid wall-clock issues.
    """

    def __init__(
        self,
        provider: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
    ) -> None:
        self.provider = provider
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: float = 0.0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Current circuit state.

        Checks if OPEN should transition to HALF_OPEN based on elapsed time.
        This is a read-only check; actual transitions happen under the lock
        in the call() method.
        """
        if self._state == CircuitState.OPEN:
            elapsed = time.monotonic() - self._last_failure_time
            if elapsed >= self.recovery_timeout:
                return CircuitState.HALF_OPEN
        return self._state

    @property
    def failure_count(self) -> int:
        return self._failure_count

    async def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute func through the circuit breaker.

        CLOSED: execute normally, track failures.
        OPEN: raise CircuitOpenError if recovery_timeout hasn't elapsed.
               Transition to HALF_OPEN if it has, and allow one probe.
        HALF_OPEN: allow exactly one probe. The lock is held through probe
                   execution so concurrent callers see OPEN and are rejected,
                   preventing multiple simultaneous probes.
        """
        async with self._lock:
            current_state = self._check_state_transition()

            if current_state == CircuitState.OPEN:
                retry_after = self.recovery_timeout - (
                    time.monotonic() - self._last_failure_time
                )
                raise CircuitOpenError(self.provider, max(0.0, retry_after))

            if current_state == CircuitState.HALF_OPEN:
                # Hold the lock for the duration of the probe so concurrent
                # callers see HALF_OPEN -> OPEN (via _check_state_transition
                # returning HALF_OPEN which we re-check below) and are rejected.
                # We keep _state as HALF_OPEN so that additional callers that
                # acquire the lock while we probe will hit the OPEN branch after
                # we flip back to OPEN on failure, or see CLOSED on success.
                try:
                    result = await func(*args, **kwargs)
                except BaseException as exc:
                    self._failure_count += 1
                    self._last_failure_time = time.monotonic()
                    self._state = CircuitState.OPEN
                    raise exc
                else:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    return result

        # CLOSED: execute outside the lock to avoid holding it during I/O
        try:
            result = await func(*args, **kwargs)
        except BaseException as exc:
            await self._record_failure()
            raise exc
        else:
            await self._record_success()
            return result

    def _check_state_transition(self) -> CircuitState:
        """Check and perform time-based state transitions (called under lock)."""
        if self._state == CircuitState.OPEN:
            elapsed = time.monotonic() - self._last_failure_time
            if elapsed >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
        return self._state

    async def _record_failure(self) -> None:
        """Record a failure and potentially open the circuit (CLOSED path only)."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()

            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN

    async def _record_success(self) -> None:
        """Record a success in CLOSED state, resetting the failure count."""
        async with self._lock:
            self._failure_count = 0

    async def reset(self) -> None:
        """Manually reset the circuit breaker to CLOSED state."""
        async with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._last_failure_time = 0.0
