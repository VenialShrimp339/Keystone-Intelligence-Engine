"""Phase 4H: ResearchAgent must route LLM calls through ErrorRecovery.

The agent's synthesis and absence-report paths used to call
``retry_llm_call`` directly, leaving ``self._error_recovery`` unused.
These tests verify that the wire-up is live: transient failures walk
the recovery chain, and the chain is truncated at STANDARD so research
never silently degrades to Haiku.
"""

from __future__ import annotations

import json

import pytest

from keystone.gateway.audit_log import AuditLogger
from keystone.gateway.auth import ToolAuthorizer
from keystone.gateway.mcp_gateway import MCPGateway, MockMCPClient
from keystone.gateway.rate_limiter import InMemoryRateLimiter, RateLimit
from keystone.gateway.servers import register_all_tools
from keystone.gateway.tool_registry import ToolRegistry
from keystone.models.agents import AgentDefinition, AgentInstance, AgentRole, ResearchAgentType
from keystone.models.research import (
    EngagementSpec,
    EngagementType,
    EvaluationProfileName,
    PipelineProfile,
    ResearchQuestion,
    ResearchSpec,
    ValidationReport,
)
from keystone.models.tasks import (
    ModelTier,
    ResearchTask,
    TaskCategory,
    TaskDecomposition,
    TaskImportance,
    TaskType,
)
from keystone.research.error_recovery import FALLBACK_CHAIN, ErrorRecovery
from keystone.research.research_agent import ResearchAgent

_MOCK_CLAIMS = json.dumps(
    [
        {
            "text": "Test claim",
            "evidence": "Test evidence",
            "citation_refs": ["SRC-001"],
            "confidence": 0.9,
            "caveats": [],
        }
    ]
)
_MOCK_ABSENCE = json.dumps(["Nothing was missing"])


def _build_gateway() -> MCPGateway:
    registry = ToolRegistry()
    register_all_tools(registry)
    mock_client = MockMCPClient()
    authorizer = ToolAuthorizer(registry)
    rate_limiter = InMemoryRateLimiter(
        {
            "exa-mcp-server": RateLimit(max_tokens=100, refill_rate=10.0),
            "brave-search-mcp-server": RateLimit(max_tokens=100, refill_rate=10.0),
            "edgartools-mcp": RateLimit(max_tokens=100, refill_rate=10.0),
            "fred-mcp-server": RateLimit(max_tokens=100, refill_rate=10.0),
            "finnhub-mcp": RateLimit(max_tokens=100, refill_rate=10.0),
            "paper-search-mcp": RateLimit(max_tokens=100, refill_rate=10.0),
            "doi-mcp": RateLimit(max_tokens=100, refill_rate=10.0),
        }
    )
    return MCPGateway(
        registry=registry,
        authorizer=authorizer,
        rate_limiter=rate_limiter,
        audit_logger=AuditLogger(),
        client=mock_client,
    )


def _build_task_and_spec() -> tuple[ResearchTask, EngagementSpec, AgentInstance]:
    eid = "eng_recov_0001"
    cid = "client_recov"
    task = ResearchTask(
        id="task_recov_001",
        engagement_id=eid,
        client_id=cid,
        category=TaskCategory.STRATEGIC_POSITIONING,
        type=TaskType.ESTIMATIVE,
        target_decision_usefulness=3,
        description="probe",
        acceptance_criteria=["criterion"],
        deliverable_destination="Section",
        priority=1,
        importance=TaskImportance.PRIMARY,
        anti_confirmatory_framing="both sides",
        assigned_tools=["exa_search", "brave_search", "paper_search"],
        assigned_model=ModelTier.STANDARD,
        end_product="analysis",
    )

    rs = ResearchSpec(
        engagement_id=eid,
        client_id=cid,
        title="recov test",
        created_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
        specification_version=1,
        decision_context="dc",
        surprising_finding="sf",
        questions=[ResearchQuestion(question="probe?", is_primary=True)],
        methodology=[],
        source_requirements=[],
        output_format="markdown",
        non_goals=[],
        engagement_type=EngagementType.EVALUATIVE,
        day_1_hypothesis="hyp",
        recommended_pipeline_profile=PipelineProfile.STANDARD,
        effective_pipeline_profile=PipelineProfile.STANDARD,
        effective_evaluation_profile=EvaluationProfileName.DEFAULT,
        profile_source="test",
    )
    td = TaskDecomposition(
        project="recov test",
        engagement_id=eid,
        client_id=cid,
        research_md_path=f"engagements/{eid}/RESEARCH.md",
        specification_version=1,
        decomposition_rationale="test",
        tasks=[task],
    )
    spec = EngagementSpec(
        research_spec=rs,
        task_decomposition=td,
        validation_report=ValidationReport(
            intent_clear=True,
            scope_valid=True,
            within_frontier=True,
            quality_threshold_met=True,
        ),
        issue_tree={},
    )

    agent = AgentInstance(
        agent_id="agent_recov_001",
        engagement_id=eid,
        client_id=cid,
        definition=AgentDefinition(
            name="quantitative-analyst",
            role=AgentRole.RESEARCH,
            research_type=ResearchAgentType.QUANTITATIVE,
            description="Quantitative research analyst for testing",
            tools=["exa_search", "brave_search"],
            scope="Test agent",
        ),
        working_dir=f"/tmp/recov/{eid}",
        task_ids=[task.id],
    )
    return task, spec, agent


# ---- Tests ---------------------------------------------------------------


class TestFallbackChainTruncation:
    def test_chain_stops_at_standard(self):
        """FALLBACK_CHAIN no longer includes FAST. Research must never go to Haiku."""
        assert FALLBACK_CHAIN == [ModelTier.FLAGSHIP, ModelTier.STANDARD]
        assert ModelTier.FAST not in FALLBACK_CHAIN

    def test_starting_at_standard_never_reaches_fast(self):
        recovery = ErrorRecovery()
        tiers = recovery._get_fallback_tiers(ModelTier.STANDARD)
        assert tiers == [ModelTier.STANDARD]


class TestResearchAgentUsesErrorRecovery:
    @pytest.mark.asyncio
    async def test_synthesis_routes_through_error_recovery(self, caplog):
        """A transient failure on the primary LLM must trigger ErrorRecovery retries.

        Pre-fix, the research agent called ``retry_llm_call`` directly and
        ``self._error_recovery`` was never used. Post-fix, the call goes
        through ``execute_with_recovery``, which logs a distinct
        "Transient error ... Retrying in" message when the LLM raises.
        We assert on that log line — it is only produced by the
        :class:`ErrorRecovery` path.
        """
        import logging

        call_log: list[str] = []

        async def flaky_llm(prompt: str) -> str:
            call_log.append(prompt[:30])
            # The first LLM call (first synthesis) raises a transient
            # error; subsequent calls succeed. The retry must fire.
            if len(call_log) == 1:
                raise RuntimeError("rate limit exceeded on initial try")
            if "absence" in prompt.lower() or "NOT found" in prompt:
                return _MOCK_ABSENCE
            return _MOCK_CLAIMS

        gateway = _build_gateway()
        agent_obj = ResearchAgent(
            llm=flaky_llm,
            gateway=gateway,
            error_recovery=ErrorRecovery(max_retries=3, base_delay=0.0),
        )

        task, spec, agent = _build_task_and_spec()
        with caplog.at_level(logging.WARNING, logger="keystone.research.error_recovery"):
            try:
                async for _ in agent_obj.execute(task, spec, agent):
                    pass
            except RuntimeError:
                # The finding may fail to build for unrelated reasons (mock
                # gateway quirks); we only care that recovery fired.
                pass

        # The ErrorRecovery retry log fires only on the execute_with_recovery
        # path. Presence of this log is the Phase 4H contract: research calls
        # flow through the recovery wrapper, not plain retry_llm_call.
        assert any(
            "Transient error" in record.getMessage() and "Retrying" in record.getMessage()
            for record in caplog.records
        )
        # And the mock LLM was called more than once (fail + retry).
        assert len(call_log) >= 2

    @pytest.mark.asyncio
    async def test_research_agent_stores_error_recovery(self):
        """Verify the agent's error_recovery attribute is wired and non-default."""
        gateway = _build_gateway()

        async def plain_llm(_prompt: str) -> str:
            return _MOCK_CLAIMS

        custom = ErrorRecovery(max_retries=7, base_delay=0.01)
        agent_obj = ResearchAgent(
            llm=plain_llm,
            gateway=gateway,
            error_recovery=custom,
        )
        assert agent_obj._error_recovery is custom
