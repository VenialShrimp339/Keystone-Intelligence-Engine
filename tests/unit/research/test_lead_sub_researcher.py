"""Tests for LeadResearcher + SubResearcher two-tier dispatch.

Covers:
- Plan shape (3 sub-queries with distinct methodologies)
- Citation round-trip (SRC/EV refs survive merge)
- Merge correctness (contradictions tagged, claims collated not averaged)
- Fallback (all sub-agents fail -> single-agent ResearchAgent path)
- Flag off: pool uses direct path unchanged
"""

import json

import pytest

from keystone.events import (
    PartialFindingMerged,
    ResearchComplete,
    ResearchStarted,
    SubAgentDispatched,
)
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
from keystone.research.agent_pool import AgentPool
from keystone.research.lead_researcher import LeadResearcher, _AllSubAgentsFailedError

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_PLAN_RESPONSE = json.dumps(
    [
        {
            "sub_id": "SUB-001",
            "objective": "Analyze financial filings for revenue data",
            "methodology": "financial_data",
            "allowed_tools": ["edgar_filings"],
            "anti_confirmatory_framing": (
                "Evaluate whether reported revenue growth is sustainable"
            ),
            "stop_criterion": "3+ independent sources",
            "output_focus": "quantitative financial metrics",
        },
        {
            "sub_id": "SUB-002",
            "objective": "Survey market intelligence reports",
            "methodology": "market_intelligence",
            "allowed_tools": ["exa_search"],
            "anti_confirmatory_framing": (
                "Assess whether market projections are overly optimistic"
            ),
            "stop_criterion": "3+ independent sources",
            "output_focus": "market sizing data",
        },
        {
            "sub_id": "SUB-003",
            "objective": "Review academic literature on technology adoption",
            "methodology": "academic_technical",
            "allowed_tools": ["brave_search"],
            "anti_confirmatory_framing": ("Evaluate whether technology adoption curves apply here"),
            "stop_criterion": "3+ independent sources",
            "output_focus": "adoption rate data and models",
        },
    ]
)

_SUB_CLAIMS = json.dumps(
    [
        {
            "text": "Market growing at 25% CAGR",
            "evidence": "Industry report confirms growth",
            "citation_refs": ["SRC-001"],
            "confidence": 0.82,
            "caveats": [],
        },
    ]
)

_MERGE_RESPONSE = json.dumps(
    {
        "claims": [
            {
                "text": "Market growing at 25% CAGR",
                "evidence": "Corroborated across financial and market intelligence sources",
                "citation_refs": ["SRC-001", "SRC-002"],
                "confidence": 0.88,
                "caveats": [],
                "contradiction_note": None,
            },
            {
                "text": "Growth may decelerate to 15% by 2027",
                "evidence": "Academic models suggest saturation",
                "citation_refs": ["SRC-003"],
                "confidence": 0.65,
                "caveats": ["Contradicts the 25% sustained growth claim from financial data"],
                "contradiction_note": ("Contradicts '25% CAGR' from financial_data methodology"),
            },
        ],
        "absence_report": ["No data on emerging market segments"],
        "status": "complete",
        "n_contradictions": 1,
    }
)

_ABSENCE = json.dumps(["No data on emerging markets"])

_DIRECT_CLAIMS = json.dumps(
    [
        {
            "text": "Direct agent claim",
            "evidence": "Direct evidence",
            "citation_refs": ["SRC-001"],
            "confidence": 0.8,
            "caveats": [],
        },
    ]
)


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


def _make_task(
    task_id: str = "task_001",
    category: TaskCategory = TaskCategory.COMPETITIVE_LANDSCAPE,
    **overrides,
) -> ResearchTask:
    defaults = {
        "id": task_id,
        "engagement_id": "eng_001",
        "client_id": "client_001",
        "category": category,
        "type": TaskType.ESTIMATIVE,
        "target_decision_usefulness": 4,
        "description": "Analyze competitive landscape for AV sensor market",
        "acceptance_criteria": ["Cite 3+ sources"],
        "deliverable_destination": "Section 2.1",
        "priority": 1,
        "anti_confirmatory_framing": (
            "What evidence challenges the projected competitive dynamics?"
        ),
        "assigned_tools": ["exa_search", "brave_search", "edgar_filings"],
        "assigned_model": ModelTier.STANDARD,
        "end_product": "Competitive landscape analysis",
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
            ResearchQuestion(question="What is the competitive landscape?", is_primary=True),
        ],
        output_format="markdown",
        engagement_type=EngagementType.EVALUATIVE,
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
# LeadResearcher: plan shape tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_plan_produces_three_distinct_methodologies() -> None:
    """plan_subqueries must produce exactly 3 sub-queries with distinct methodologies."""
    call_count = 0

    async def mock_flagship(prompt: str) -> str:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _PLAN_RESPONSE
        return _MERGE_RESPONSE

    async def mock_standard(prompt: str) -> str:
        if "absence" in prompt.lower():
            return _ABSENCE
        return _SUB_CLAIMS

    gateway, client = _build_gateway()
    client.set_response("exa_search", {"url": "https://ex.com/a", "title": "A"})
    client.set_response("brave_search", {"url": "https://ex.com/b", "title": "B"})
    client.set_response("edgar_filings", {"url": "https://ex.com/c", "title": "C"})

    lead = LeadResearcher(
        flagship_llm=mock_flagship,
        standard_llm=mock_standard,
        gateway=gateway,
    )

    task = _make_task()
    spec = _make_spec()
    agent = _make_agent()

    events = []
    async for event in lead.execute(task, spec, agent):
        events.append(event)

    # Check dispatch events — should have exactly 3 SubAgentDispatched
    dispatch_events = [e for e in events if isinstance(e, SubAgentDispatched)]
    assert len(dispatch_events) == 3

    methodologies = {e.methodology for e in dispatch_events}
    assert len(methodologies) == 3, f"Expected 3 distinct methodologies, got {methodologies}"


# ---------------------------------------------------------------------------
# LeadResearcher: citation round-trip
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_citation_refs_survive_merge() -> None:
    """SRC/EV refs from sub-agents must appear in the merged StructuredFinding."""
    call_count = 0

    async def mock_flagship(prompt: str) -> str:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _PLAN_RESPONSE
        return _MERGE_RESPONSE

    async def mock_standard(prompt: str) -> str:
        if "absence" in prompt.lower():
            return _ABSENCE
        return _SUB_CLAIMS

    gateway, client = _build_gateway()
    client.set_response("exa_search", {"url": "https://ex.com/a", "title": "A"})
    client.set_response("brave_search", {"url": "https://ex.com/b", "title": "B"})
    client.set_response("edgar_filings", {"url": "https://ex.com/c", "title": "C"})

    lead = LeadResearcher(
        flagship_llm=mock_flagship,
        standard_llm=mock_standard,
        gateway=gateway,
    )

    task = _make_task()
    spec = _make_spec()
    agent = _make_agent()

    async for _ in lead.execute(task, spec, agent):
        pass

    finding = await lead.get_finding()
    assert finding is not None
    assert len(finding.claims) >= 1
    for claim in finding.claims:
        assert len(claim.citations) >= 1, f"Claim '{claim.text}' lost its citations"


# ---------------------------------------------------------------------------
# LeadResearcher: merge correctness — contradictions tagged
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_contradictions_tagged_not_averaged() -> None:
    """When sub-agents disagree, both claims survive with contradiction caveats."""
    call_count = 0

    async def mock_flagship(prompt: str) -> str:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _PLAN_RESPONSE
        return _MERGE_RESPONSE

    async def mock_standard(prompt: str) -> str:
        if "absence" in prompt.lower():
            return _ABSENCE
        return _SUB_CLAIMS

    gateway, client = _build_gateway()
    client.set_response("exa_search", {"url": "https://ex.com/a", "title": "A"})
    client.set_response("brave_search", {"url": "https://ex.com/b", "title": "B"})
    client.set_response("edgar_filings", {"url": "https://ex.com/c", "title": "C"})

    lead = LeadResearcher(
        flagship_llm=mock_flagship,
        standard_llm=mock_standard,
        gateway=gateway,
    )

    task = _make_task()
    spec = _make_spec()
    agent = _make_agent()

    async for _ in lead.execute(task, spec, agent):
        pass

    finding = await lead.get_finding()
    assert len(finding.claims) == 2

    # The merge response has one claim with a contradiction note
    contradiction_claims = [
        c for c in finding.claims if any("contradict" in cav.lower() for cav in c.caveats)
    ]
    assert len(contradiction_claims) >= 1, "Contradiction should be tagged in caveats"

    # Both the high-confidence and the contradicting claim must survive (collation, not averaging)
    confidences = [c.confidence for c in finding.claims]
    assert 0.88 in confidences, "High-confidence corroborated claim must survive"
    assert 0.65 in confidences, "Lower-confidence contradicting claim must survive"


# ---------------------------------------------------------------------------
# LeadResearcher: PartialFindingMerged event
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_merge_event_emitted() -> None:
    call_count = 0

    async def mock_flagship(prompt: str) -> str:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _PLAN_RESPONSE
        return _MERGE_RESPONSE

    async def mock_standard(prompt: str) -> str:
        if "absence" in prompt.lower():
            return _ABSENCE
        return _SUB_CLAIMS

    gateway, client = _build_gateway()
    client.set_response("exa_search", {"url": "https://ex.com/a", "title": "A"})
    client.set_response("brave_search", {"url": "https://ex.com/b", "title": "B"})
    client.set_response("edgar_filings", {"url": "https://ex.com/c", "title": "C"})

    lead = LeadResearcher(
        flagship_llm=mock_flagship,
        standard_llm=mock_standard,
        gateway=gateway,
    )

    events = []
    async for event in lead.execute(_make_task(), _make_spec(), _make_agent()):
        events.append(event)

    merge_events = [e for e in events if isinstance(e, PartialFindingMerged)]
    assert len(merge_events) == 1
    assert merge_events[0].n_sub_findings >= 1
    assert merge_events[0].n_total_claims >= 1

    # Full event lifecycle: Started -> Dispatched(x3) -> Completed(x3) -> Merged -> Complete
    assert isinstance(events[0], ResearchStarted)
    assert isinstance(events[-1], ResearchComplete)


# ---------------------------------------------------------------------------
# Fallback: all sub-agents fail -> _AllSubAgentsFailedError
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_all_sub_agents_fail_raises() -> None:
    """When all sub-agents fail, LeadResearcher raises _AllSubAgentsFailedError."""

    async def mock_flagship(prompt: str) -> str:
        return _PLAN_RESPONSE

    async def failing_standard(prompt: str) -> str:
        raise RuntimeError("Sub-agent LLM failure")

    gateway, client = _build_gateway()
    # Gateway tool calls also fail
    client.set_response("exa_search", RuntimeError("Tool failure"))
    client.set_response("brave_search", RuntimeError("Tool failure"))
    client.set_response("edgar_filings", RuntimeError("Tool failure"))

    lead = LeadResearcher(
        flagship_llm=mock_flagship,
        standard_llm=failing_standard,
        gateway=gateway,
    )

    with pytest.raises(_AllSubAgentsFailedError):
        async for _ in lead.execute(_make_task(), _make_spec(), _make_agent()):
            pass


# ---------------------------------------------------------------------------
# AgentPool: flag OFF uses direct path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pool_flag_off_uses_direct_path() -> None:
    """With l1_orchestrator_enabled=False, eligible tasks still use ResearchAgent."""

    async def mock_llm(prompt: str) -> str:
        if "absence" in prompt.lower():
            return _ABSENCE
        return _DIRECT_CLAIMS

    gateway, client = _build_gateway()
    client.set_response("exa_search", {"url": "https://ex.com/a", "title": "A"})
    client.set_response("brave_search", {"url": "https://ex.com/b", "title": "B"})
    client.set_response("edgar_filings", {"url": "https://ex.com/c", "title": "C"})

    pool = AgentPool(
        llm=mock_llm,
        gateway=gateway,
        l1_orchestrator_enabled=False,
    )
    spec = _make_spec()
    task = _make_task(category=TaskCategory.COMPETITIVE_LANDSCAPE)
    agent = _make_agent()

    results = await pool.execute_all([(task, spec, agent)])
    assert len(results) == 1
    assert results[0].success

    # Should NOT have SubAgentDispatched events (used direct path)
    dispatch_events = [e for e in results[0].events if isinstance(e, SubAgentDispatched)]
    assert len(dispatch_events) == 0


# ---------------------------------------------------------------------------
# AgentPool: flag ON routes eligible tasks
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pool_flag_on_routes_eligible_tasks() -> None:
    """With flag ON, competitive_landscape tasks use LeadResearcher dispatch."""
    call_count = 0

    async def mock_llm(prompt: str) -> str:
        nonlocal call_count
        call_count += 1
        if "DECOMPOSITION" in prompt.upper() or "BREAK THIS TASK" in prompt.upper():
            return _PLAN_RESPONSE
        if "MERGE" in prompt.upper() or "COLLAT" in prompt.upper():
            return _MERGE_RESPONSE
        if "absence" in prompt.lower():
            return _ABSENCE
        return _SUB_CLAIMS

    gateway, client = _build_gateway()
    client.set_response("exa_search", {"url": "https://ex.com/a", "title": "A"})
    client.set_response("brave_search", {"url": "https://ex.com/b", "title": "B"})
    client.set_response("edgar_filings", {"url": "https://ex.com/c", "title": "C"})

    pool = AgentPool(
        llm=mock_llm,
        gateway=gateway,
        l1_orchestrator_enabled=True,
    )
    spec = _make_spec()
    task = _make_task(category=TaskCategory.COMPETITIVE_LANDSCAPE)
    agent = _make_agent()

    results = await pool.execute_all([(task, spec, agent)])
    assert len(results) == 1
    assert results[0].success

    # Should have SubAgentDispatched events
    dispatch_events = [e for e in results[0].events if isinstance(e, SubAgentDispatched)]
    assert len(dispatch_events) == 3


# ---------------------------------------------------------------------------
# AgentPool: ineligible category uses direct path even with flag ON
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pool_ineligible_category_uses_direct_path() -> None:
    """Tasks with non-eligible categories use direct ResearchAgent even with flag ON."""

    async def mock_llm(prompt: str) -> str:
        if "absence" in prompt.lower():
            return _ABSENCE
        return _DIRECT_CLAIMS

    gateway, client = _build_gateway()
    client.set_response("exa_search", {"url": "https://ex.com/a", "title": "A"})
    client.set_response("brave_search", {"url": "https://ex.com/b", "title": "B"})
    client.set_response("edgar_filings", {"url": "https://ex.com/c", "title": "C"})

    pool = AgentPool(
        llm=mock_llm,
        gateway=gateway,
        l1_orchestrator_enabled=True,
    )
    spec = _make_spec()
    # REGULATORY is not in the eligible set
    task = _make_task(category=TaskCategory.REGULATORY)
    agent = _make_agent()

    results = await pool.execute_all([(task, spec, agent)])
    assert len(results) == 1
    assert results[0].success

    # Should NOT have SubAgentDispatched events
    dispatch_events = [e for e in results[0].events if isinstance(e, SubAgentDispatched)]
    assert len(dispatch_events) == 0


# ---------------------------------------------------------------------------
# AgentPool: orchestrated failure falls back to direct path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pool_orchestrated_failure_falls_back() -> None:
    """If LeadResearcher fails completely, AgentPool falls back to single-agent."""
    call_count = 0

    async def mock_llm(prompt: str) -> str:
        nonlocal call_count
        call_count += 1
        # First call is plan_subqueries — return invalid JSON to trigger failure
        if call_count == 1:
            raise RuntimeError("Flagship LLM unavailable")
        # Fallback path uses regular ResearchAgent
        if "absence" in prompt.lower():
            return _ABSENCE
        return _DIRECT_CLAIMS

    gateway, client = _build_gateway()
    client.set_response("exa_search", {"url": "https://ex.com/a", "title": "A"})
    client.set_response("brave_search", {"url": "https://ex.com/b", "title": "B"})
    client.set_response("edgar_filings", {"url": "https://ex.com/c", "title": "C"})

    pool = AgentPool(
        llm=mock_llm,
        gateway=gateway,
        l1_orchestrator_enabled=True,
    )
    spec = _make_spec()
    task = _make_task(category=TaskCategory.COMPETITIVE_LANDSCAPE)
    agent = _make_agent()

    results = await pool.execute_all([(task, spec, agent)])
    assert len(results) == 1
    # Should succeed via fallback path
    assert results[0].success


# ---------------------------------------------------------------------------
# SubQuery: plan parsing resilience
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_lead_pads_subqueries_when_llm_returns_fewer() -> None:
    """If LLM returns <3 sub-queries, Lead pads to 3."""
    call_count = 0
    partial_plan = json.dumps(
        [
            {
                "sub_id": "SUB-001",
                "objective": "Only one sub-query returned",
                "methodology": "financial_data",
                "allowed_tools": ["edgar_filings"],
                "anti_confirmatory_framing": "Evaluate whether X holds",
                "stop_criterion": "done",
                "output_focus": "data",
            }
        ]
    )

    async def mock_flagship(prompt: str) -> str:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return partial_plan
        return _MERGE_RESPONSE

    async def mock_standard(prompt: str) -> str:
        if "absence" in prompt.lower():
            return _ABSENCE
        return _SUB_CLAIMS

    gateway, client = _build_gateway()
    client.set_response("exa_search", {"url": "https://ex.com/a", "title": "A"})
    client.set_response("brave_search", {"url": "https://ex.com/b", "title": "B"})
    client.set_response("edgar_filings", {"url": "https://ex.com/c", "title": "C"})

    lead = LeadResearcher(
        flagship_llm=mock_flagship,
        standard_llm=mock_standard,
        gateway=gateway,
    )

    events = []
    async for event in lead.execute(_make_task(), _make_spec(), _make_agent()):
        events.append(event)

    dispatch_events = [e for e in events if isinstance(e, SubAgentDispatched)]
    assert len(dispatch_events) == 3, "Should pad to 3 sub-queries"


# ---------------------------------------------------------------------------
# StructuredFinding contract unchanged
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_finding_contract_unchanged() -> None:
    """The StructuredFinding from LeadResearcher has the same fields as a direct agent."""
    call_count = 0

    async def mock_flagship(prompt: str) -> str:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _PLAN_RESPONSE
        return _MERGE_RESPONSE

    async def mock_standard(prompt: str) -> str:
        if "absence" in prompt.lower():
            return _ABSENCE
        return _SUB_CLAIMS

    gateway, client = _build_gateway()
    client.set_response("exa_search", {"url": "https://ex.com/a", "title": "A"})
    client.set_response("brave_search", {"url": "https://ex.com/b", "title": "B"})
    client.set_response("edgar_filings", {"url": "https://ex.com/c", "title": "C"})

    lead = LeadResearcher(
        flagship_llm=mock_flagship,
        standard_llm=mock_standard,
        gateway=gateway,
    )

    async for _ in lead.execute(_make_task(), _make_spec(), _make_agent()):
        pass

    finding = await lead.get_finding()

    # All mandatory StructuredFinding fields must be present
    assert finding.task_id == "task_001"
    assert finding.agent_id == "agent_001"
    assert finding.engagement_id == "eng_001"
    assert finding.client_id == "client_001"
    assert finding.agent_type == "quantitative"
    assert len(finding.claims) >= 1
    assert len(finding.absence_report) >= 1
    assert finding.sources_consulted >= 0
    assert finding.tokens_consumed >= 0
    # Status must be a valid FindingStatus
    from keystone.models.research import FindingStatus

    assert finding.status in {
        FindingStatus.COMPLETE,
        FindingStatus.PARTIAL,
        FindingStatus.GAP_FOUND,
    }
