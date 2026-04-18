"""Tests for the MCP Gateway audit logger."""

import pytest

from keystone.gateway.audit_log import AuditLogger


# ---------------------------------------------------------------------------
# Basic logging
# ---------------------------------------------------------------------------


class TestAuditLogging:
    def test_log_successful_call(self) -> None:
        logger = AuditLogger()
        entry = logger.log_call(
            agent_id="agent_001",
            engagement_id="eng_001",
            client_id="client_001",
            tool_name="exa_search",
            parameters={"query": "market size"},
            result={"data": "some results"},
            latency_ms=150.0,
        )
        assert entry.success is True
        assert entry.agent_id == "agent_001"
        assert entry.tool_name == "exa_search"
        assert entry.latency_ms == 150.0
        assert entry.input_hash is not None
        assert entry.output_hash is not None
        assert entry.error_type is None

    def test_log_failed_call(self) -> None:
        logger = AuditLogger()
        error = ConnectionError("timeout")
        entry = logger.log_call(
            agent_id="agent_001",
            engagement_id="eng_001",
            client_id="client_001",
            tool_name="exa_search",
            parameters={"query": "test"},
            error=error,
            latency_ms=5000.0,
        )
        assert entry.success is False
        assert entry.error_type == "ConnectionError"
        assert "timeout" in entry.error_message

    def test_log_dead_letter(self) -> None:
        logger = AuditLogger()
        entry = logger.log_call(
            agent_id="agent_001",
            engagement_id="eng_001",
            client_id="client_001",
            tool_name="exa_search",
            parameters={"query": "test"},
            error=ConnectionError("final failure"),
            latency_ms=10000.0,
            dead_lettered=True,
        )
        assert entry.dead_lettered is True


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------


class TestHashing:
    def test_same_input_same_hash(self) -> None:
        logger = AuditLogger()
        params = {"query": "market size", "count": 10}

        entry1 = logger.log_call(
            agent_id="a",
            engagement_id="e",
            client_id="c",
            tool_name="t",
            parameters=params,
        )
        entry2 = logger.log_call(
            agent_id="a",
            engagement_id="e",
            client_id="c",
            tool_name="t",
            parameters=params,
        )
        assert entry1.input_hash == entry2.input_hash

    def test_different_input_different_hash(self) -> None:
        logger = AuditLogger()
        entry1 = logger.log_call(
            agent_id="a",
            engagement_id="e",
            client_id="c",
            tool_name="t",
            parameters={"query": "alpha"},
        )
        entry2 = logger.log_call(
            agent_id="a",
            engagement_id="e",
            client_id="c",
            tool_name="t",
            parameters={"query": "beta"},
        )
        assert entry1.input_hash != entry2.input_hash

    def test_hash_is_truncated_sha256(self) -> None:
        logger = AuditLogger()
        entry = logger.log_call(
            agent_id="a",
            engagement_id="e",
            client_id="c",
            tool_name="t",
            parameters={"key": "value"},
        )
        # 16 hex chars (first 8 bytes of SHA-256)
        assert len(entry.input_hash) == 16
        assert all(c in "0123456789abcdef" for c in entry.input_hash)


# ---------------------------------------------------------------------------
# Querying
# ---------------------------------------------------------------------------


class TestQuerying:
    def test_get_entries_all(self) -> None:
        logger = AuditLogger()
        for i in range(5):
            logger.log_call(
                agent_id=f"agent_{i}",
                engagement_id="eng_001",
                client_id="c",
                tool_name="exa_search",
                parameters={},
            )
        assert len(logger.get_entries()) == 5

    def test_filter_by_agent(self) -> None:
        logger = AuditLogger()
        logger.log_call(
            agent_id="agent_a",
            engagement_id="eng_001",
            client_id="c",
            tool_name="exa_search",
            parameters={},
        )
        logger.log_call(
            agent_id="agent_b",
            engagement_id="eng_001",
            client_id="c",
            tool_name="exa_search",
            parameters={},
        )
        results = logger.get_entries(agent_id="agent_a")
        assert len(results) == 1
        assert results[0].agent_id == "agent_a"

    def test_filter_by_tool(self) -> None:
        logger = AuditLogger()
        logger.log_call(
            agent_id="a",
            engagement_id="e",
            client_id="c",
            tool_name="exa_search",
            parameters={},
        )
        logger.log_call(
            agent_id="a",
            engagement_id="e",
            client_id="c",
            tool_name="brave_search",
            parameters={},
        )
        results = logger.get_entries(tool_name="brave_search")
        assert len(results) == 1

    def test_get_dead_letters(self) -> None:
        logger = AuditLogger()
        logger.log_call(
            agent_id="a",
            engagement_id="e",
            client_id="c",
            tool_name="t",
            parameters={},
        )
        logger.log_call(
            agent_id="a",
            engagement_id="e",
            client_id="c",
            tool_name="t",
            parameters={},
            error=RuntimeError("fail"),
            dead_lettered=True,
        )
        dead = logger.get_dead_letters()
        assert len(dead) == 1
        assert dead[0].dead_lettered is True


# ---------------------------------------------------------------------------
# Debug mode
# ---------------------------------------------------------------------------


class TestDebugMode:
    def test_debug_mode_logs_full_data(self) -> None:
        """Debug mode should not crash. Full I/O is logged via structlog."""
        logger = AuditLogger(debug=True)
        entry = logger.log_call(
            agent_id="a",
            engagement_id="e",
            client_id="c",
            tool_name="t",
            parameters={"secret": "data"},
            result={"full": "output"},
        )
        assert entry.success is True
