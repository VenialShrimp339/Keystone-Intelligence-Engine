"""Tests for parallel agent execution and partial-result continuation."""

import json

import pytest

from keystone.evaluator.retry import LLMCallable
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
    ResearchQuestion,
    ResearchSpec,
    ValidationReport,
)
from keystone.models.tasks import (
    ModelTier,
    ResearchTask,
    TaskCategory,
    TaskDecomposition,
    TaskType,
)
from keystone.research.agent_pool import AgentPool, AgentResult

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_CLAIMS = json.dumps(
    [
        {
            "text": "Market growing at 25% CAGR",
            "evidence": "Industry reports confirm growth trajectory",
            "citation_refs": ["SRC-001"],
            "confidence": 0.82,
            "caveats": [],
        },
    ]
)
_ABSENCE = json.dumps(["No data on emerging markets"])


async def _mock_llm(prompt: str) -> str:
    if "NOT found" in prompt or "absence" in prompt.lower():
        return _ABSENCE
    return _CLAIMS


def _build_gateway(
    mock_client: MockMCPClient | None = None,
) -> tuple[MCPGateway, MockMCPClient]:
    registry = ToolRegistry()
    register_all_tools(registry)
    authorizer = ToolAuthorizer(registry)
    limiter = InMemoryRateLimiter(
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
    audit = AuditLogger()
    client = mock_client or MockMCPClient()
    gateway = MCPGateway(
        registry=registry,
        authorizer=authorizer,
        rate_limiter=limiter,
        audit_logger=audit,
        client=client,
    )
    return gateway, client


def _make_task(task_id: str = "task_001", **overrides) -> ResearchTask:
    defaults = {
        "id": task_id,
        "engagement_id": "eng_001",
        "client_id": "client_001",
        "category": TaskCategory.MARKET_SIZING,
        "type": TaskType.ESTIMATIVE,
        "target_decision_usefulness": 4,
        "description": "Estimate TAM for L4+ AV sensor market",
        "acceptance_criteria": ["Cite 3+ sources"],
        "deliverable_destination": "Section 2.1",
        "priority": 1,
        "anti_confirmatory_framing": "What evidence challenges the projected market size?",
        "assigned_tools": ["exa_search", "brave_search", "edgar_filings"],
        "assigned_model": ModelTier.STANDARD,
        "end_product": "Market sizing estimate",
    }
    defaults.update(overrides)
    return ResearchTask(**defaults)


def _make_agent(
    agent_id: str = "agent_001",
    research_type: ResearchAgentType = ResearchAgentType.QUANTITATIVE,
) -> AgentInstance:
    defn = AgentDefinition(
        name=f"{research_type.value}_analyst",
        description=f"{research_type.value} research specialist",
        role=AgentRole.RESEARCH,
        model=ModelTier.STANDARD,
        tools=["exa_search", "brave_search", "edgar_filings"],
        research_type=research_type,
    )
    return AgentInstance(
        agent_id=agent_id,
        engagement_id="eng_001",
        client_id="client_001",
        definition=defn,
        working_dir=f"/tmp/keystone/{agent_id}",
    )


def _make_spec() -> EngagementSpec:
    research_spec = ResearchSpec(
        engagement_id="eng_001",
        client_id="client_001",
        title="AV Sensor Market Analysis",
        created_at="2026-04-06T00:00:00Z",
        specification_version=1,
        decision_context="Evaluate market entry for AV sensors",
        surprising_finding="Market shrinking faster than expected",
        questions=[
            ResearchQuestion(question="What is the TAM?", is_primary=True),
        ],
        output_format="markdown",
        engagement_type=EngagementType.SIZING,
    )
    task = _make_task()
    return EngagementSpec(
        research_spec=research_spec,
        task_decomposition=TaskDecomposition(
            project="AV Sensor Market Analysis",
            engagement_id="eng_001",
            client_id="client_001",
            research_md_path="eng_001/RESEARCH.md",
            specification_version=1,
            decomposition_rationale="Single task for testing",
            tasks=[task],
        ),
        validation_report=ValidationReport(
            intent_clear=True,
            scope_valid=True,
            within_frontier=True,
            quality_threshold_met=True,
        ),
    )


# ---------------------------------------------------------------------------
# Parallel execution: all succeed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_all_agents_succeed() -> None:
    gateway, client = _build_gateway()
    client.set_response("exa_search", {"url": "https://ex.com/a", "title": "A"})
    client.set_response("brave_search", {"url": "https://ex.com/b", "title": "B"})
    client.set_response("edgar_filings", {"url": "https://ex.com/c", "title": "C"})

    pool = AgentPool(llm=_mock_llm, gateway=gateway)
    spec = _make_spec()

    assignments = [
        (_make_task("task_001"), spec, _make_agent("agent_001", ResearchAgentType.QUANTITATIVE)),
        (_make_task("task_002"), spec, _make_agent("agent_002", ResearchAgentType.QUALITATIVE)),
        (_make_task("task_003"), spec, _make_agent("agent_003", ResearchAgentType.CONTRARIAN)),
    ]

    results = await pool.execute_all(assignments)

    assert len(results) == 3
    assert all(r.success for r in results)

    findings = pool.get_successful_findings(results)
    assert len(findings) == 3


# ---------------------------------------------------------------------------
# Partial-result continuation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_partial_result_continuation() -> None:
    """If some agents fail, combine successful results and retry failures."""
    call_count = 0

    async def sometimes_failing_llm(prompt: str) -> str:
        nonlocal call_count
        call_count += 1
        if "NOT found" in prompt or "absence" in prompt.lower():
            return _ABSENCE
        # Fail early calls to simulate one agent failing
        if call_count == 2:
            raise RuntimeError("Simulated LLM failure")
        return _CLAIMS

    gateway, client = _build_gateway()
    client.set_response("exa_search", {"url": "https://ex.com/a", "title": "A"})
    client.set_response("brave_search", {"url": "https://ex.com/b", "title": "B"})
    client.set_response("edgar_filings", {"url": "https://ex.com/c", "title": "C"})

    pool = AgentPool(
        llm=sometimes_failing_llm,
        gateway=gateway,
        max_retries=1,
    )
    spec = _make_spec()

    assignments = [
        (_make_task("task_001"), spec, _make_agent("agent_001")),
        (_make_task("task_002"), spec, _make_agent("agent_002")),
    ]

    results = await pool.execute_all(assignments)

    # At least one should succeed
    successful = pool.get_successful_findings(results)
    assert len(successful) >= 1


# ---------------------------------------------------------------------------
# All fail
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_all_agents_fail() -> None:
    async def always_fails(prompt: str) -> str:
        raise RuntimeError("LLM unavailable")

    gateway, client = _build_gateway()
    client.set_response("exa_search", {"url": "https://ex.com/a", "title": "A"})
    client.set_response("brave_search", {"url": "https://ex.com/b", "title": "B"})
    client.set_response("edgar_filings", {"url": "https://ex.com/c", "title": "C"})

    pool = AgentPool(llm=always_fails, gateway=gateway, max_retries=0)
    spec = _make_spec()

    assignments = [
        (_make_task("task_001"), spec, _make_agent("agent_001")),
    ]

    results = await pool.execute_all(assignments)

    assert len(results) == 1
    assert not results[0].success
    assert results[0].error is not None

    failed = pool.get_failed_agents(results)
    assert len(failed) == 1


# ---------------------------------------------------------------------------
# AgentResult properties
# ---------------------------------------------------------------------------


def test_agent_result_success() -> None:
    from datetime import UTC, datetime

    from keystone.models.citations import Citation, ConfidenceTier, SourceType
    from keystone.models.research import FindingClaim, FindingStatus, StructuredFinding

    cit = Citation(
        citation_id="CIT-001",
        engagement_id="eng_001",
        client_id="client_001",
        url="https://example.com",
        title="Test",
        access_date=datetime.now(UTC),
        source_type=SourceType.REPORT,
        quality_score=0.8,
    )
    finding = StructuredFinding(
        task_id="task_001",
        agent_id="agent_001",
        engagement_id="eng_001",
        client_id="client_001",
        agent_type="quantitative",
        claims=[
            FindingClaim(
                text="Test claim",
                evidence="Test evidence",
                citations=[cit],
                confidence=0.8,
                confidence_tier=ConfidenceTier.HIGH,
            )
        ],
        absence_report=["Nothing missing"],
        sources_consulted=1,
        tokens_consumed=100,
    )

    result = AgentResult(agent_id="agent_001", task_id="task_001", finding=finding)
    assert result.success

    failed = AgentResult(
        agent_id="agent_001",
        task_id="task_001",
        error=RuntimeError("fail"),
    )
    assert not failed.success


# ---------------------------------------------------------------------------
# Events collected per agent
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_events_collected_per_agent() -> None:
    gateway, client = _build_gateway()
    client.set_response("exa_search", {"url": "https://ex.com/a", "title": "A"})
    client.set_response("brave_search", {"url": "https://ex.com/b", "title": "B"})
    client.set_response("edgar_filings", {"url": "https://ex.com/c", "title": "C"})

    pool = AgentPool(llm=_mock_llm, gateway=gateway)
    spec = _make_spec()

    assignments = [
        (_make_task("task_001"), spec, _make_agent("agent_001")),
    ]

    results = await pool.execute_all(assignments)

    assert results[0].success
    assert len(results[0].events) > 0
    event_types = {type(e).__name__ for e in results[0].events}
    assert "ResearchStarted" in event_types
    assert "ResearchComplete" in event_types


# ---------------------------------------------------------------------------
# GAP-01: per-task LLM routing via llm_factory
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_flagship_task_gets_different_llm_than_pool_default() -> None:
    """Task with assigned_model=FLAGSHIP must use the factory-resolved LLM, not pool default."""
    gateway, client = _build_gateway()
    client.set_response("exa_search", {"url": "https://ex.com/a", "title": "A"})
    client.set_response("brave_search", {"url": "https://ex.com/b", "title": "B"})
    client.set_response("edgar_filings", {"url": "https://ex.com/c", "title": "C"})

    called_tiers: list[ModelTier] = []

    def tracking_factory(tier: ModelTier) -> LLMCallable:
        called_tiers.append(tier)
        return _mock_llm

    pool = AgentPool(
        llm=_mock_llm,
        gateway=gateway,
        llm_factory=tracking_factory,
    )
    spec = _make_spec()
    flagship_task = _make_task("task_flagship", assigned_model=ModelTier.FLAGSHIP)

    assignments = [(flagship_task, spec, _make_agent("agent_001"))]
    results = await pool.execute_all(assignments)

    assert results[0].success
    # Factory must have been called with FLAGSHIP for this task
    assert ModelTier.FLAGSHIP in called_tiers


@pytest.mark.asyncio
async def test_none_assigned_model_falls_back_to_pool_llm() -> None:
    """When assigned_model is None, pool must use the shared self._llm, not the factory."""
    gateway, client = _build_gateway()
    client.set_response("exa_search", {"url": "https://ex.com/a", "title": "A"})
    client.set_response("brave_search", {"url": "https://ex.com/b", "title": "B"})
    client.set_response("edgar_filings", {"url": "https://ex.com/c", "title": "C"})

    factory_calls: list[ModelTier] = []

    def tracking_factory(tier: ModelTier) -> LLMCallable:
        factory_calls.append(tier)
        return _mock_llm

    # Build a task with assigned_model explicitly set to None by bypassing the
    # default so the fallback path is tested.
    task = _make_task("task_none_model", assigned_model=ModelTier.STANDARD)
    # Patch assigned_model to None after construction (field is not frozen)
    task.assigned_model = None  # type: ignore[assignment]

    pool = AgentPool(
        llm=_mock_llm,
        gateway=gateway,
        llm_factory=tracking_factory,
    )
    spec = _make_spec()
    assignments = [(task, spec, _make_agent("agent_001"))]
    results = await pool.execute_all(assignments)

    assert results[0].success
    # Factory must NOT have been called because assigned_model was None
    assert factory_calls == []


@pytest.mark.asyncio
async def test_pool_without_factory_always_uses_shared_llm() -> None:
    """Backward compat: pool with no llm_factory must always use self._llm."""
    gateway, client = _build_gateway()
    client.set_response("exa_search", {"url": "https://ex.com/a", "title": "A"})
    client.set_response("brave_search", {"url": "https://ex.com/b", "title": "B"})
    client.set_response("edgar_filings", {"url": "https://ex.com/c", "title": "C"})

    pool = AgentPool(llm=_mock_llm, gateway=gateway)  # no llm_factory
    spec = _make_spec()
    flagship_task = _make_task("task_flagship_nofc", assigned_model=ModelTier.FLAGSHIP)

    assignments = [(flagship_task, spec, _make_agent("agent_001"))]
    results = await pool.execute_all(assignments)

    # Should still succeed — shared _mock_llm is used, no factory errors
    assert results[0].success
