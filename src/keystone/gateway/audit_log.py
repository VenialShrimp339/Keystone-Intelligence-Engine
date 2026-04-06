"""Structured audit logging for the MCP Gateway.

Logs every tool call with full context for debugging and compliance.
I/O is SHA-256 hashed by default (data volume concern); full I/O
available in debug mode.

Pattern extracted from mcp-gateway's middleware/logging_mw.py:
structlog JSON output + request context propagation.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any

import structlog


@dataclass
class AuditEntry:
    """A single audit log entry for a tool call."""

    timestamp: float
    agent_id: str
    engagement_id: str
    client_id: str
    tool_name: str
    input_hash: str
    output_hash: str | None
    latency_ms: float
    success: bool
    error_type: str | None = None
    error_message: str | None = None
    retry_attempt: int = 0
    dead_lettered: bool = False


class AuditLogger:
    """Logs every tool call with full context.

    Uses structlog for structured JSON output. Input/output are
    SHA-256 hashed by default to control data volume. Set debug=True
    for full I/O logging (development only).
    """

    def __init__(self, debug: bool = False) -> None:
        self._debug = debug
        self._logger = structlog.get_logger("keystone.gateway.audit")
        self._entries: list[AuditEntry] = []

    @staticmethod
    def _hash_data(data: Any) -> str:
        """SHA-256 hash of JSON-serialized data."""
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]

    def log_call(
        self,
        agent_id: str,
        engagement_id: str,
        client_id: str,
        tool_name: str,
        parameters: dict[str, Any],
        result: Any | None = None,
        error: Exception | None = None,
        latency_ms: float = 0.0,
        retry_attempt: int = 0,
        dead_lettered: bool = False,
    ) -> AuditEntry:
        """Log a tool call with full context.

        Returns the AuditEntry for testing/inspection.
        """
        input_hash = self._hash_data(parameters)
        output_hash = self._hash_data(result) if result is not None else None

        entry = AuditEntry(
            timestamp=time.time(),
            agent_id=agent_id,
            engagement_id=engagement_id,
            client_id=client_id,
            tool_name=tool_name,
            input_hash=input_hash,
            output_hash=output_hash,
            latency_ms=latency_ms,
            success=error is None,
            error_type=type(error).__name__ if error else None,
            error_message=str(error) if error else None,
            retry_attempt=retry_attempt,
            dead_lettered=dead_lettered,
        )

        self._entries.append(entry)

        log_kwargs: dict[str, Any] = {
            "agent_id": agent_id,
            "engagement_id": engagement_id,
            "client_id": client_id,
            "tool_name": tool_name,
            "input_hash": input_hash,
            "output_hash": output_hash,
            "latency_ms": round(latency_ms, 2),
            "success": entry.success,
            "retry_attempt": retry_attempt,
        }

        if dead_lettered:
            log_kwargs["dead_lettered"] = True

        if self._debug:
            log_kwargs["input_data"] = parameters
            if result is not None:
                log_kwargs["output_data"] = result

        if error:
            log_kwargs["error_type"] = entry.error_type
            log_kwargs["error_message"] = entry.error_message
            self._logger.error("tool_call_failed", **log_kwargs)
        else:
            self._logger.info("tool_call_success", **log_kwargs)

        return entry

    def get_entries(
        self,
        agent_id: str | None = None,
        engagement_id: str | None = None,
        tool_name: str | None = None,
    ) -> list[AuditEntry]:
        """Query audit entries with optional filters."""
        entries = self._entries
        if agent_id is not None:
            entries = [e for e in entries if e.agent_id == agent_id]
        if engagement_id is not None:
            entries = [e for e in entries if e.engagement_id == engagement_id]
        if tool_name is not None:
            entries = [e for e in entries if e.tool_name == tool_name]
        return entries

    def get_dead_letters(self) -> list[AuditEntry]:
        """Return all dead-lettered entries."""
        return [e for e in self._entries if e.dead_lettered]
