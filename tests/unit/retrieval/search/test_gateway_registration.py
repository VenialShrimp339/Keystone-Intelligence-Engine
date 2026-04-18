"""Gateway-side checks for the retrieval tool registration."""

from __future__ import annotations

from keystone.gateway.servers import (
    RETRIEVAL_MAX_REQ_PER_SEC,
    RETRIEVAL_SERVER_NAME,
    SERVER_RATE_LIMITS,
    TOOL_CONFIGS,
    build_default_rate_limits,
)
from keystone.gateway.tool_registry import TransportType
from keystone.tool_names import (
    ALL_TOOLS,
    DEFAULT_TOOLS,
    FINANCIAL_TOOLS,
    RETRIEVAL_TOOLS,
    SEARCH_TOOLS,
    SYSTEM_OWNED_TOOLS,
    ToolName,
)


class TestRetrievalToolRegistration:
    def test_both_names_registered(self) -> None:
        assert ToolName.SEMANTIC_SEARCH in TOOL_CONFIGS
        assert ToolName.HYBRID_SEARCH in TOOL_CONFIGS

    def test_shared_server(self) -> None:
        semantic = TOOL_CONFIGS[ToolName.SEMANTIC_SEARCH]
        hybrid = TOOL_CONFIGS[ToolName.HYBRID_SEARCH]
        assert semantic.server_name == RETRIEVAL_SERVER_NAME
        assert hybrid.server_name == RETRIEVAL_SERVER_NAME

    def test_in_process_transport(self) -> None:
        semantic = TOOL_CONFIGS[ToolName.SEMANTIC_SEARCH]
        hybrid = TOOL_CONFIGS[ToolName.HYBRID_SEARCH]
        assert semantic.transport_type is TransportType.IN_PROCESS
        assert hybrid.transport_type is TransportType.IN_PROCESS

    def test_marked_system_owned(self) -> None:
        for name in (ToolName.SEMANTIC_SEARCH, ToolName.HYBRID_SEARCH):
            assert TOOL_CONFIGS[name].config.get("system_owned") is True

    def test_retrieval_rate_limit_present(self) -> None:
        assert RETRIEVAL_SERVER_NAME in SERVER_RATE_LIMITS
        rl = SERVER_RATE_LIMITS[RETRIEVAL_SERVER_NAME]
        assert rl.max_tokens == RETRIEVAL_MAX_REQ_PER_SEC
        assert rl.refill_rate == float(RETRIEVAL_MAX_REQ_PER_SEC)

    def test_build_default_rate_limits_includes_retrieval(self) -> None:
        limits = build_default_rate_limits()
        assert RETRIEVAL_SERVER_NAME in limits

    def test_tools_not_in_task_assignable_groups(self) -> None:
        # System-owned retrieval tools must not appear in agent-assignable groups
        assert ToolName.SEMANTIC_SEARCH not in DEFAULT_TOOLS
        assert ToolName.HYBRID_SEARCH not in DEFAULT_TOOLS
        assert ToolName.SEMANTIC_SEARCH not in SEARCH_TOOLS
        assert ToolName.HYBRID_SEARCH not in SEARCH_TOOLS
        assert ToolName.SEMANTIC_SEARCH not in FINANCIAL_TOOLS
        assert ToolName.HYBRID_SEARCH not in FINANCIAL_TOOLS

    def test_retrieval_tools_group_content(self) -> None:
        assert ToolName.SEMANTIC_SEARCH in RETRIEVAL_TOOLS
        assert ToolName.HYBRID_SEARCH in RETRIEVAL_TOOLS
        assert ToolName.SEMANTIC_SEARCH in SYSTEM_OWNED_TOOLS
        assert ToolName.HYBRID_SEARCH in SYSTEM_OWNED_TOOLS

    def test_all_tools_includes_retrieval(self) -> None:
        assert ToolName.SEMANTIC_SEARCH in ALL_TOOLS
        assert ToolName.HYBRID_SEARCH in ALL_TOOLS
