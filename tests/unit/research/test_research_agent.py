"""Tests for single-agent execution with mock LLM + MockMCPClient.

Verifies: iterative loop, event emission (all 5 L1 event types),
stopping criteria, and StructuredFinding production.
"""

import json

import pytest

from keystone.events import (
    CitationExtracted,
    FindingSynthesized,
    ResearchComplete,
    ResearchStarted,
    SourceFound,
)
from keystone.gateway.audit_log import AuditLogger
from keystone.gateway.auth import ToolAuthorizer
from keystone.gateway.mcp_gateway import MCPGateway, MockMCPClient
from keystone.gateway.rate_limiter import InMemoryRateLimiter, RateLimit
from keystone.gateway.servers import register_all_tools
from keystone.gateway.tool_registry import ToolRegistry
from keystone.models.agents import AgentDefinition, AgentInstance, AgentRole, ResearchAgentType
from keystone.models.research import FindingStatus, StructuredFinding
from keystone.models.tasks import (
    ModelTier,
    ResearchTask,
    TaskCategory,
    TaskType,
)
from keystone.research.finding_writer import FindingWriter
from keystone.research.research_agent import ResearchAgent

# ---------------------------------------------------------------------------
# Test fixtures and helpers
# ---------------------------------------------------------------------------

# Standard claims the mock LLM returns.
# citation_refs must reference SRC-001 (the first citation in the round table).
_MOCK_CLAIMS = json.dumps(
    [
        {
            "text": "Global EV battery market projected at $150B by 2030",
            "evidence": "BloombergNEF and IEA projections converge",
            "citation_refs": ["SRC-001"],
            "confidence": 0.85,
            "caveats": ["Projections vary by 20%"],
        },
        {
            "text": "CATL and LG lead with 50% combined market share",
            "evidence": "SEC filings and industry reports",
            "citation_refs": ["SRC-001"],
            "confidence": 0.9,
            "caveats": [],
        },
    ]
)

_MOCK_ABSENCE = json.dumps(
    [
        "No sub-Saharan Africa market data found",
        "No projections beyond 2035",
    ]
)


async def _mock_llm(prompt: str) -> str:
    """Mock LLM that returns canned synthesis and absence responses."""
    if "NOT found" in prompt or "absence" in prompt.lower():
        return _MOCK_ABSENCE
    return _MOCK_CLAIMS


def _build_gateway(
    mock_client: MockMCPClient | None = None,
) -> tuple[MCPGateway, MockMCPClient]:
    """Build a fully wired gateway with mock client."""
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


def _make_task(**overrides) -> ResearchTask:
    defaults = {
        "id": "task_001",
        "engagement_id": "eng_001",
        "client_id": "client_001",
        "category": TaskCategory.MARKET_SIZING,
        "type": TaskType.ESTIMATIVE,
        "target_decision_usefulness": 4,
        "description": "Estimate TAM for L4+ AV sensor market",
        "acceptance_criteria": ["Cite at least 3 sources", "Include confidence ranges"],
        "deliverable_destination": "Section 2.1",
        "priority": 1,
        "anti_confirmatory_framing": "What evidence challenges the projected market size?",
        "assigned_tools": ["exa_search", "brave_search", "edgar_filings"],
        "assigned_model": ModelTier.STANDARD,
        "end_product": "Market sizing estimate with ranges",
    }
    defaults.update(overrides)
    return ResearchTask(**defaults)


def _make_agent(**overrides) -> AgentInstance:
    defn = AgentDefinition(
        name="quantitative_analyst",
        description="Quantitative research specialist",
        role=AgentRole.RESEARCH,
        model=ModelTier.STANDARD,
        tools=["exa_search", "brave_search", "edgar_filings"],
        research_type=ResearchAgentType.QUANTITATIVE,
    )
    defaults = {
        "agent_id": "agent_001",
        "engagement_id": "eng_001",
        "client_id": "client_001",
        "definition": defn,
        "working_dir": "/tmp/keystone/agent_001",
    }
    defaults.update(overrides)
    return AgentInstance(**defaults)


def _make_spec():
    """Build a minimal EngagementSpec for testing."""
    from keystone.models.research import (
        EngagementSpec,
        EngagementType,
        ResearchQuestion,
        ResearchSpec,
        ValidationReport,
    )
    from keystone.models.tasks import TaskDecomposition

    research_spec = ResearchSpec(
        engagement_id="eng_001",
        client_id="client_001",
        title="AV Sensor Market Analysis",
        created_at="2026-04-06T00:00:00Z",
        specification_version=1,
        decision_context="Evaluate market entry opportunity for L4+ AV sensors",
        surprising_finding="Market is shrinking or consolidating faster than expected",
        questions=[
            ResearchQuestion(question="What is the TAM for L4+ AV sensors?", is_primary=True),
        ],
        output_format="markdown",
        engagement_type=EngagementType.SIZING,
    )
    validation = ValidationReport(
        intent_clear=True,
        scope_valid=True,
        within_frontier=True,
        quality_threshold_met=True,
    )
    decomposition = TaskDecomposition(
        project="AV Sensor Market Analysis",
        engagement_id="eng_001",
        client_id="client_001",
        research_md_path="eng_001/RESEARCH.md",
        specification_version=1,
        decomposition_rationale="Single market sizing task for testing",
        tasks=[_make_task()],
    )
    return EngagementSpec(
        research_spec=research_spec,
        task_decomposition=decomposition,
        validation_report=validation,
    )


# ---------------------------------------------------------------------------
# Core execution
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_produces_all_event_types() -> None:
    """Verify all 5 L1 event types are emitted."""
    gateway, client = _build_gateway()
    # Set responses with URLs so citations are extracted
    client.set_response(
        "exa_search",
        {
            "url": "https://example.com/ev-report",
            "title": "EV Battery Market Report",
            "data": "Market projected at $150B",
        },
    )
    client.set_response(
        "brave_search",
        {
            "url": "https://example.com/av-sensors",
            "title": "AV Sensor Landscape",
            "data": "L4+ sensors growing 30% YoY",
        },
    )
    client.set_response(
        "edgar_filings",
        {
            "url": "https://sec.gov/filing/12345",
            "title": "CATL 10-K Filing",
            "data": "Revenue: $35B",
        },
    )

    agent = ResearchAgent(
        llm=_mock_llm,
        gateway=gateway,
        max_rounds=1,
    )
    task = _make_task()
    spec = _make_spec()
    agent_inst = _make_agent()

    events = []
    async for event in agent.execute(task, spec, agent_inst):
        events.append(event)

    event_types = {type(e).__name__ for e in events}
    assert "ResearchStarted" in event_types
    assert "SourceFound" in event_types
    assert "CitationExtracted" in event_types
    assert "FindingSynthesized" in event_types
    assert "ResearchComplete" in event_types


@pytest.mark.asyncio
async def test_execute_produces_structured_finding() -> None:
    gateway, client = _build_gateway()
    client.set_response(
        "exa_search",
        {
            "url": "https://example.com/report",
            "title": "Report",
        },
    )
    client.set_response(
        "brave_search",
        {
            "url": "https://example.com/report2",
            "title": "Report 2",
        },
    )
    client.set_response(
        "edgar_filings",
        {
            "url": "https://sec.gov/filing",
            "title": "Filing",
        },
    )

    agent = ResearchAgent(llm=_mock_llm, gateway=gateway, max_rounds=1)
    task = _make_task()

    async for _ in agent.execute(task, _make_spec(), _make_agent()):
        pass

    finding = await agent.get_finding()
    assert isinstance(finding, StructuredFinding)
    assert finding.task_id == "task_001"
    assert finding.agent_id == "agent_001"
    assert finding.agent_type == "quantitative"
    assert len(finding.claims) == 2
    assert finding.sources_consulted >= 3
    assert len(finding.absence_report) >= 1


@pytest.mark.asyncio
async def test_claims_have_citations() -> None:
    """Every claim must have at least one citation (structural enforcement)."""
    gateway, client = _build_gateway()
    client.set_response(
        "exa_search",
        {
            "url": "https://example.com/r1",
            "title": "Source 1",
        },
    )
    client.set_response(
        "brave_search",
        {
            "url": "https://example.com/r2",
            "title": "Source 2",
        },
    )
    client.set_response(
        "edgar_filings",
        {
            "url": "https://example.com/r3",
            "title": "Source 3",
        },
    )

    agent = ResearchAgent(llm=_mock_llm, gateway=gateway, max_rounds=1)

    async for _ in agent.execute(_make_task(), _make_spec(), _make_agent()):
        pass

    finding = await agent.get_finding()
    for claim in finding.claims:
        assert len(claim.citations) >= 1, "Every claim must have citations"
        assert claim.confidence >= 0.0
        assert claim.confidence <= 1.0


@pytest.mark.asyncio
async def test_claims_have_confidence_scores() -> None:
    gateway, client = _build_gateway()
    client.set_response("exa_search", {"url": "https://ex.com/a", "title": "A"})
    client.set_response("brave_search", {"url": "https://ex.com/b", "title": "B"})
    client.set_response("edgar_filings", {"url": "https://ex.com/c", "title": "C"})

    agent = ResearchAgent(llm=_mock_llm, gateway=gateway, max_rounds=1)

    async for _ in agent.execute(_make_task(), _make_spec(), _make_agent()):
        pass

    finding = await agent.get_finding()
    for claim in finding.claims:
        assert 0.0 <= claim.confidence <= 1.0
        assert claim.confidence_tier is not None


# ---------------------------------------------------------------------------
# Iterative loop
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_iterative_loop_runs_multiple_rounds() -> None:
    """Use low-confidence claims so the quality threshold doesn't stop round 1."""
    _low_conf_claims = json.dumps(
        [
            {
                "text": "Preliminary market estimate around $100B",
                "evidence": "Early industry forecasts",
                "citation_refs": ["SRC-001"],
                "confidence": 0.55,
                "caveats": ["Highly uncertain"],
            },
        ]
    )

    async def low_conf_llm(prompt: str) -> str:
        if "NOT found" in prompt or "absence" in prompt.lower():
            return _MOCK_ABSENCE
        return _low_conf_claims

    gateway, client = _build_gateway()
    client.set_response("exa_search", {"url": "https://ex.com/a", "title": "A"})
    client.set_response("brave_search", {"url": "https://ex.com/b", "title": "B"})
    client.set_response("edgar_filings", {"url": "https://ex.com/c", "title": "C"})

    agent = ResearchAgent(llm=low_conf_llm, gateway=gateway, max_rounds=3)

    events = []
    async for event in agent.execute(_make_task(), _make_spec(), _make_agent()):
        events.append(event)

    synth_events = [e for e in events if isinstance(e, FindingSynthesized)]
    assert len(synth_events) >= 2, "Iterative loop should run at least 2 rounds"


# ---------------------------------------------------------------------------
# Stopping criteria
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stops_on_novelty_exhaustion() -> None:
    """When the LLM returns no new claims, the loop stops."""
    round_count = 0

    async def static_llm(prompt: str) -> str:
        nonlocal round_count
        if "NOT found" in prompt or "absence" in prompt.lower():
            return _MOCK_ABSENCE
        round_count += 1
        if round_count == 1:
            return _MOCK_CLAIMS
        # Subsequent rounds: return empty (no new claims)
        return "[]"

    gateway, client = _build_gateway()
    client.set_response("exa_search", {"url": "https://ex.com/a", "title": "A"})
    client.set_response("brave_search", {"url": "https://ex.com/b", "title": "B"})
    client.set_response("edgar_filings", {"url": "https://ex.com/c", "title": "C"})

    agent = ResearchAgent(llm=static_llm, gateway=gateway, max_rounds=5)

    events = []
    async for event in agent.execute(_make_task(), _make_spec(), _make_agent()):
        events.append(event)

    synth_events = [e for e in events if isinstance(e, FindingSynthesized)]
    # Should stop early (round 2 produces no new claims)
    assert len(synth_events) <= 3


# ---------------------------------------------------------------------------
# Event metadata
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_event_ids_unique() -> None:
    gateway, client = _build_gateway()
    client.set_response("exa_search", {"url": "https://ex.com/a", "title": "A"})
    client.set_response("brave_search", {"url": "https://ex.com/b", "title": "B"})
    client.set_response("edgar_filings", {"url": "https://ex.com/c", "title": "C"})

    agent = ResearchAgent(llm=_mock_llm, gateway=gateway, max_rounds=1)

    events = []
    async for event in agent.execute(_make_task(), _make_spec(), _make_agent()):
        events.append(event)

    event_ids = [e.event_id for e in events]
    assert len(event_ids) == len(set(event_ids)), "Event IDs must be unique"


@pytest.mark.asyncio
async def test_research_complete_has_metadata() -> None:
    gateway, client = _build_gateway()
    client.set_response("exa_search", {"url": "https://ex.com/a", "title": "A"})
    client.set_response("brave_search", {"url": "https://ex.com/b", "title": "B"})
    client.set_response("edgar_filings", {"url": "https://ex.com/c", "title": "C"})

    agent = ResearchAgent(llm=_mock_llm, gateway=gateway, max_rounds=1)

    events = []
    async for event in agent.execute(_make_task(), _make_spec(), _make_agent()):
        events.append(event)

    complete = [e for e in events if isinstance(e, ResearchComplete)][0]
    assert complete.task_id == "task_001"
    assert complete.agent_id == "agent_001"
    assert complete.sources_consulted >= 3
    assert complete.absence_count >= 1


# ---------------------------------------------------------------------------
# get_finding before execute
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_finding_before_execute_raises() -> None:
    gateway, _ = _build_gateway()
    agent = ResearchAgent(llm=_mock_llm, gateway=gateway)

    with pytest.raises(RuntimeError, match="No finding available"):
        await agent.get_finding()
