"""Integration tests: L1 Research Agents + MCP Gateway with REAL API calls.

Tests real GPT-5.4 LLM calls AND real Exa/Brave search calls.
First time agents do actual research. Goal: find everything that breaks.

Run with: pytest tests/integration/test_research_agent_live.py -v -m integration -s
Consumes API quota (LLM + search). Expect ~30-50 LLM calls total.

Wave 4a Session 10 pressure test.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
from dotenv import load_dotenv

from keystone.events import (
    CitationExtracted,
    FindingSynthesized,
    ResearchComplete,
    ResearchStarted,
    SourceFound,
)
from keystone.gateway.audit_log import AuditLogger
from keystone.gateway.auth import ToolAuthorizer
from keystone.gateway.mcp_gateway import MCPGateway, MockMCPClient, ToolCall
from keystone.gateway.rate_limiter import InMemoryRateLimiter, RateLimit
from keystone.gateway.servers import register_all_tools
from keystone.gateway.simple_client import SimpleMCPClient
from keystone.gateway.tool_registry import ToolRegistry
from keystone.llm_client import _client_cache, get_llm_for_tier
from keystone.models.agents import (
    AgentDefinition,
    AgentInstance,
    AgentRole,
    ResearchAgentType,
)
from keystone.models.config import AppConfig
from keystone.models.research import (
    EngagementSpec,
    EngagementType,
    MethodologyRequirement,
    ResearchQuestion,
    ResearchSpec,
    StructuredFinding,
    ValidationReport,
)
from keystone.models.tasks import (
    ModelTier,
    ResearchTask,
    TaskCategory,
    TaskDecomposition,
    TaskType,
)
from keystone.research.finding_writer import FindingWriter
from keystone.research.isolation import IsolationManager
from keystone.research.research_agent import ResearchAgent
from keystone.tool_names import ToolName

# Load .env
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

pytestmark = pytest.mark.integration

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tracking
# ---------------------------------------------------------------------------

_token_log: list[dict] = []


def _log_tokens(test_name: str, tokens: int, elapsed: float, llm_calls: int, search_calls: int = 0):
    entry = {
        "test": test_name,
        "tokens": tokens,
        "elapsed_s": round(elapsed, 2),
        "llm_calls": llm_calls,
        "search_calls": search_calls,
    }
    _token_log.append(entry)
    print(
        f"\n  [TOKENS] {test_name}: ~{tokens} tokens, {elapsed:.1f}s, "
        f"{llm_calls} LLM calls, {search_calls} search calls"
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _fresh_client():
    _client_cache.clear()
    yield
    _client_cache.clear()


@pytest.fixture()
def live_config() -> AppConfig:
    return AppConfig()


@pytest.fixture()
def llm(live_config):
    """Real LLM callable (gpt-5.4 via Codex OAuth)."""
    return get_llm_for_tier(ModelTier.STANDARD, live_config)


@pytest.fixture()
async def simple_client():
    """Real HTTP client for Exa/Brave APIs."""
    client = SimpleMCPClient()
    yield client
    await client.close()


@pytest.fixture()
def gateway_with_real_search(simple_client) -> MCPGateway:
    """MCPGateway wired to real Exa/Brave via SimpleMCPClient."""
    registry = ToolRegistry()
    register_all_tools(registry)
    authorizer = ToolAuthorizer(registry)
    rate_limiter = InMemoryRateLimiter(
        {
            "exa-mcp-server": RateLimit(max_tokens=10, refill_rate=2.0),
            "brave-search-mcp-server": RateLimit(max_tokens=10, refill_rate=2.0),
        }
    )
    audit_logger = AuditLogger(debug=True)
    return MCPGateway(
        registry=registry,
        authorizer=authorizer,
        rate_limiter=rate_limiter,
        audit_logger=audit_logger,
        client=simple_client,
    )


@pytest.fixture()
def gateway_with_mock() -> MCPGateway:
    """MCPGateway wired to MockMCPClient for error/isolation tests."""
    registry = ToolRegistry()
    register_all_tools(registry)
    authorizer = ToolAuthorizer(registry)
    rate_limiter = InMemoryRateLimiter({})
    audit_logger = AuditLogger(debug=True)
    mock_client = MockMCPClient()
    # Set canned responses with URLs so citation extraction works
    mock_client.set_response(
        "exa_search",
        {
            "status": "ok",
            "results": [
                {
                    "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany",
                    "title": "SEC EDGAR Company Search",
                    "text": "The autonomous vehicle sensor market is projected to reach $15B by 2030.",
                }
            ],
        },
    )
    mock_client.set_response(
        "brave_search",
        {
            "status": "ok",
            "results": [
                {
                    "url": "https://en.wikipedia.org/wiki/Lidar",
                    "title": "Lidar - Wikipedia",
                    "text": "Lidar sensors are critical components for autonomous driving.",
                }
            ],
        },
    )
    mock_client.set_response(
        "edgar_filings",
        {
            "status": "ok",
            "results": [],
            "data": "No filings found for query.",
        },
    )
    return MCPGateway(
        registry=registry,
        authorizer=authorizer,
        rate_limiter=rate_limiter,
        audit_logger=audit_logger,
        client=mock_client,
    )


def _make_task(
    task_id: str = "task_001",
    description: str = "Estimate the total addressable market for L4+ AV sensors in North America through 2030",
    tools: list[str] | None = None,
) -> ResearchTask:
    """Create a ResearchTask for testing."""
    return ResearchTask(
        id=task_id,
        engagement_id="ENG-TEST-001",
        client_id="CLIENT-TEST",
        category=TaskCategory.MARKET_SIZING,
        type=TaskType.ESTIMATIVE,
        target_decision_usefulness=3,
        description=description,
        acceptance_criteria=[
            "Market size estimate with 3+ supporting data points",
            "Include both bottom-up and top-down sizing approaches",
            "Identify key growth drivers and inhibitors",
        ],
        deliverable_destination="Section 2: Market Landscape",
        priority=1,
        anti_confirmatory_framing=(
            "Evaluate the evidence for and against a large TAM for L4+ AV sensors, "
            "including technological barriers, regulatory delays, and competing approaches"
        ),
        assigned_tools=tools
        or [
            ToolName.EXA_SEARCH,
            ToolName.BRAVE_SEARCH,
            ToolName.EDGAR_FILINGS,
        ],
        assigned_model=ModelTier.STANDARD,
        end_product="Market size estimate with supporting analysis",
    )


def _make_spec() -> EngagementSpec:
    """Create a minimal EngagementSpec for testing."""
    research_spec = ResearchSpec(
        engagement_id="ENG-TEST-001",
        client_id="CLIENT-TEST",
        title="L4+ Autonomous Vehicle Sensor Market Analysis",
        created_at=datetime.now(UTC),
        specification_version=1,
        decision_context="Client is evaluating investment in AV sensor startups",
        surprising_finding="Evidence that LiDAR is being displaced by camera-only systems",
        questions=[
            ResearchQuestion(
                question="What is the TAM for L4+ AV sensors in North America through 2030?",
                is_primary=True,
            ),
        ],
        methodology=[
            MethodologyRequirement(
                framework="Top-down and bottom-up market sizing",
                mandatory=True,
                rationale="Standard approach for TAM estimation",
            ),
        ],
        output_format="markdown",
        engagement_type=EngagementType.SIZING,
        day_1_hypothesis="The L4+ AV sensor TAM exceeds $10B by 2030",
    )
    task_decomp = TaskDecomposition(
        project="AV Sensor Market Analysis",
        engagement_id="ENG-TEST-001",
        client_id="CLIENT-TEST",
        research_md_path="engagements/ENG-TEST-001/RESEARCH.md",
        specification_version=1,
        decomposition_rationale="Market sizing requires quantitative + competitive + regulatory analysis",
        tasks=[_make_task()],
    )
    validation = ValidationReport(
        intent_clear=True,
        scope_valid=True,
        within_frontier=True,
        quality_threshold_met=True,
    )
    return EngagementSpec(
        research_spec=research_spec,
        task_decomposition=task_decomp,
        validation_report=validation,
    )


def _make_agent(
    agent_id: str = "agent_quant_001",
    research_type: ResearchAgentType = ResearchAgentType.QUANTITATIVE,
    tools: list[str] | None = None,
) -> AgentInstance:
    """Create an AgentInstance for testing."""
    definition = AgentDefinition(
        name=f"test-{research_type.value}-agent",
        description=f"Test {research_type.value} research agent",
        role=AgentRole.RESEARCH,
        model=ModelTier.STANDARD,
        tools=tools or [ToolName.EXA_SEARCH, ToolName.BRAVE_SEARCH, ToolName.EDGAR_FILINGS],
        research_type=research_type,
    )
    return AgentInstance(
        agent_id=agent_id,
        engagement_id="ENG-TEST-001",
        client_id="CLIENT-TEST",
        definition=definition,
        working_dir="/tmp/keystone_test",
    )


# ===================================================================
# BASELINE TEST 1: Single agent, single round with REAL search
# ===================================================================


async def test_single_agent_real_search(llm, gateway_with_real_search, simple_client):
    """Single quantitative agent with real Exa/Brave search + real LLM synthesis."""
    start = time.monotonic()
    task = _make_task()
    spec = _make_spec()
    agent = _make_agent()

    research_agent = ResearchAgent(
        llm=llm,
        gateway=gateway_with_real_search,
        max_rounds=1,  # single round to conserve quota
    )

    events = []
    async with asyncio.timeout(120):
        async for event in research_agent.execute(task, spec, agent):
            events.append(event)
            print(f"  Event: {type(event).__name__}")

    finding = await research_agent.get_finding()
    elapsed = time.monotonic() - start

    # --- Verify event sequence ---
    event_types = [type(e).__name__ for e in events]
    assert "ResearchStarted" in event_types, f"Missing ResearchStarted. Got: {event_types}"
    assert "SourceFound" in event_types, f"Missing SourceFound. Got: {event_types}"
    assert "FindingSynthesized" in event_types, f"Missing FindingSynthesized. Got: {event_types}"
    assert "ResearchComplete" in event_types, f"Missing ResearchComplete. Got: {event_types}"

    # --- Verify StructuredFinding ---
    assert finding is not None
    assert len(finding.claims) > 0, "No claims produced"
    assert finding.sources_consulted > 0, "No sources consulted"
    assert len(finding.absence_report) > 0, "Empty absence report"

    # --- Verify claims have structure ---
    for i, claim in enumerate(finding.claims):
        assert claim.text, f"Claim {i} has empty text"
        assert claim.evidence, f"Claim {i} has empty evidence"
        assert 0.0 <= claim.confidence <= 1.0, (
            f"Claim {i} confidence out of range: {claim.confidence}"
        )
        assert len(claim.citations) > 0, f"Claim {i} has no citations"

    # --- Verify search APIs were actually called ---
    assert simple_client.call_count > 0, "No search API calls made"
    print(
        f"\n  Finding: {len(finding.claims)} claims, "
        f"{finding.sources_consulted} sources, "
        f"{finding.tokens_consumed} tokens"
    )
    print(f"  Search calls: exa={simple_client.exa_calls}, brave={simple_client.brave_calls}")

    _log_tokens(
        "single_agent_real_search",
        finding.tokens_consumed,
        elapsed,
        llm_calls=2,
        search_calls=simple_client.call_count,
    )


# ===================================================================
# BASELINE TEST 2: Tool call verification (Exa + Brave individually)
# ===================================================================


async def test_exa_search_returns_results(simple_client):
    """Verify Exa search returns actual results for AV sensor query."""
    start = time.monotonic()

    registry = ToolRegistry()
    register_all_tools(registry)
    authorizer = ToolAuthorizer(registry)
    rate_limiter = InMemoryRateLimiter({})
    audit_logger = AuditLogger(debug=True)
    gateway = MCPGateway(
        registry=registry,
        authorizer=authorizer,
        rate_limiter=rate_limiter,
        audit_logger=audit_logger,
        client=simple_client,
    )

    call = ToolCall(
        agent_id="agent_test_exa",
        tool_name=ToolName.EXA_SEARCH,
        parameters={"query": "autonomous vehicle sensor market size 2030"},
        engagement_id="ENG-TEST-001",
        client_id="CLIENT-TEST",
        assigned_tools=[ToolName.EXA_SEARCH, ToolName.BRAVE_SEARCH, ToolName.EDGAR_FILINGS],
    )

    async with asyncio.timeout(30):
        result = await gateway.execute(call)

    elapsed = time.monotonic() - start

    assert result.result["status"] == "ok", f"Exa search failed: {result.result}"
    assert result.result["result_count"] > 0, "Exa returned 0 results"
    assert len(result.result["results"]) > 0

    # Verify results have content
    for r in result.result["results"]:
        assert r.get("url"), f"Result missing URL: {r}"
        assert r.get("title"), f"Result missing title: {r}"

    # Verify citations were extracted
    assert len(result.citations) > 0, "No citations extracted from Exa results"
    print(f"\n  Exa results: {result.result['result_count']}")
    print(f"  Citations extracted: {len(result.citations)}")
    print(f"  Latency: {elapsed:.2f}s")

    # Verify audit log captured the call
    entries = audit_logger.get_entries(tool_name=ToolName.EXA_SEARCH)
    assert len(entries) > 0, "No audit log entry for Exa call"
    assert entries[0].success is True

    _log_tokens("exa_search", 0, elapsed, llm_calls=0, search_calls=1)


async def test_brave_search_returns_results(simple_client):
    """Verify Brave search returns actual results for AV sensor query."""
    start = time.monotonic()

    registry = ToolRegistry()
    register_all_tools(registry)
    authorizer = ToolAuthorizer(registry)
    rate_limiter = InMemoryRateLimiter({})
    audit_logger = AuditLogger(debug=True)
    gateway = MCPGateway(
        registry=registry,
        authorizer=authorizer,
        rate_limiter=rate_limiter,
        audit_logger=audit_logger,
        client=simple_client,
    )

    call = ToolCall(
        agent_id="agent_test_brave",
        tool_name=ToolName.BRAVE_SEARCH,
        parameters={"query": "autonomous vehicle sensor market size 2030"},
        engagement_id="ENG-TEST-001",
        client_id="CLIENT-TEST",
        assigned_tools=[ToolName.EXA_SEARCH, ToolName.BRAVE_SEARCH, ToolName.EDGAR_FILINGS],
    )

    async with asyncio.timeout(30):
        result = await gateway.execute(call)

    elapsed = time.monotonic() - start

    assert result.result["status"] == "ok", f"Brave search failed: {result.result}"
    assert result.result["result_count"] > 0, "Brave returned 0 results"

    for r in result.result["results"]:
        assert r.get("url"), f"Result missing URL: {r}"
        assert r.get("title"), f"Result missing title: {r}"

    assert len(result.citations) > 0, "No citations extracted from Brave results"
    print(f"\n  Brave results: {result.result['result_count']}")
    print(f"  Citations extracted: {len(result.citations)}")
    print(f"  Latency: {elapsed:.2f}s")

    _log_tokens("brave_search", 0, elapsed, llm_calls=0, search_calls=1)


async def test_gateway_auth_check(simple_client):
    """Verify gateway rejects unauthorized tool calls."""
    registry = ToolRegistry()
    register_all_tools(registry)
    authorizer = ToolAuthorizer(registry)
    rate_limiter = InMemoryRateLimiter({})
    audit_logger = AuditLogger()
    gateway = MCPGateway(
        registry=registry,
        authorizer=authorizer,
        rate_limiter=rate_limiter,
        audit_logger=audit_logger,
        client=simple_client,
    )

    call = ToolCall(
        agent_id="agent_unauthorized",
        tool_name=ToolName.FINNHUB_MARKET,
        parameters={"query": "TSLA"},
        engagement_id="ENG-TEST-001",
        client_id="CLIENT-TEST",
        assigned_tools=[ToolName.EXA_SEARCH],  # agent only has exa
    )

    from keystone.gateway.auth import AuthorizationError

    with pytest.raises(AuthorizationError):
        await gateway.execute(call)

    # Verify audit log captured the rejection
    entries = audit_logger.get_entries(agent_id="agent_unauthorized")
    assert len(entries) > 0
    assert entries[0].success is False


# ===================================================================
# BASELINE TEST 3: Filesystem isolation
# ===================================================================


async def test_filesystem_isolation():
    """Verify two agents have isolated workspaces that cannot cross-read."""
    isolation = IsolationManager()

    try:
        ws_a = await isolation.create_workspace("agent_A")
        ws_b = await isolation.create_workspace("agent_B")

        # Each agent writes to its own workspace
        await ws_a.write_file("findings.md", "Agent A findings")
        await ws_b.write_file("findings.md", "Agent B findings")

        # Verify each reads its own
        a_content = await ws_a.read_file("findings.md")
        b_content = await ws_b.read_file("findings.md")
        assert a_content == "Agent A findings"
        assert b_content == "Agent B findings"

        # Verify isolation: agent A cannot access agent B's files
        assert not isolation.verify_isolation("agent_A", ws_b.path / "findings.md")
        assert not isolation.verify_isolation("agent_B", ws_a.path / "findings.md")

        # Verify each agent IS within its own workspace
        assert isolation.verify_isolation("agent_A", ws_a.path / "findings.md")
        assert isolation.verify_isolation("agent_B", ws_b.path / "findings.md")

        # Verify path escape is blocked
        with pytest.raises(PermissionError):
            await ws_a.write_file("../../etc/passwd", "hacked")

        print("\n  Isolation verified: workspaces are independent")
        print(f"  Agent A dir: {ws_a.path}")
        print(f"  Agent B dir: {ws_b.path}")
    finally:
        await isolation.cleanup_all()


# ===================================================================
# BASELINE TEST 4: Iterative loop (2 rounds with mock to save quota)
# ===================================================================


async def test_iterative_loop_two_rounds(llm, gateway_with_mock):
    """Run agent for 2 rounds, verify context evolves between rounds."""
    start = time.monotonic()
    task = _make_task()
    spec = _make_spec()
    agent = _make_agent()

    research_agent = ResearchAgent(
        llm=llm,
        gateway=gateway_with_mock,
        max_rounds=2,
    )

    events = []
    async with asyncio.timeout(120):
        async for event in research_agent.execute(task, spec, agent):
            events.append(event)

    finding = await research_agent.get_finding()
    elapsed = time.monotonic() - start

    # Should have 2 FindingSynthesized events (one per round)
    synth_events = [e for e in events if isinstance(e, FindingSynthesized)]
    print(f"\n  Synthesis events: {len(synth_events)}")
    for i, se in enumerate(synth_events):
        print(f"    Round {i + 1}: {se.claim_count} claims, confidence {se.confidence_range}")

    # Verify round 2 has at least as many claims as round 1
    if len(synth_events) >= 2:
        assert synth_events[1].claim_count >= synth_events[0].claim_count, (
            f"Round 2 ({synth_events[1].claim_count}) should have >= "
            f"round 1 ({synth_events[0].claim_count}) claims"
        )

    # Verify stopping criteria were checked
    complete_events = [e for e in events if isinstance(e, ResearchComplete)]
    assert len(complete_events) == 1
    assert complete_events[0].sources_consulted > 0

    _log_tokens(
        "iterative_two_rounds", finding.tokens_consumed, elapsed, llm_calls=4, search_calls=0
    )  # 2 synthesis + 2 absence (approx)


# ===================================================================
# BASELINE TEST 5: Error recovery
# ===================================================================


async def test_error_recovery_continues_after_tool_failure(llm):
    """Configure one tool to fail, verify agent continues with others."""
    start = time.monotonic()

    registry = ToolRegistry()
    register_all_tools(registry)
    authorizer = ToolAuthorizer(registry)
    rate_limiter = InMemoryRateLimiter({})
    audit_logger = AuditLogger(debug=True)
    mock_client = MockMCPClient()

    # exa_search will fail
    mock_client.set_failure("exa_search", ConnectionError("API unreachable"))
    # brave_search will succeed
    mock_client.set_response(
        "brave_search",
        {
            "status": "ok",
            "results": [
                {
                    "url": "https://example.com/av-sensor-market",
                    "title": "AV Sensor Market Report",
                    "text": "The market is expected to grow significantly.",
                }
            ],
        },
    )
    mock_client.set_response(
        "edgar_filings",
        {
            "status": "ok",
            "results": [],
            "data": "No filings found.",
        },
    )

    gateway = MCPGateway(
        registry=registry,
        authorizer=authorizer,
        rate_limiter=rate_limiter,
        audit_logger=audit_logger,
        client=mock_client,
    )
    # Reduce retry backoff for faster test
    gateway.BACKOFF_BASE = 0.01

    task = _make_task()
    spec = _make_spec()
    agent = _make_agent()

    research_agent = ResearchAgent(
        llm=llm,
        gateway=gateway,
        max_rounds=1,
    )

    events = []
    async with asyncio.timeout(120):
        async for event in research_agent.execute(task, spec, agent):
            events.append(event)

    finding = await research_agent.get_finding()
    elapsed = time.monotonic() - start

    # Agent should still produce findings from the tools that worked
    assert finding is not None, "Agent failed completely despite some tools working"
    assert len(finding.claims) > 0, "No claims despite working tools"

    # Verify source events -- exa failed, brave and edgar succeeded
    source_events = [e for e in events if isinstance(e, SourceFound)]
    source_tools = [e.source_type for e in source_events]
    assert "brave_search" in source_tools, f"brave_search missing from sources: {source_tools}"

    # Verify dead letters for exa (3 retries -> dead letter)
    dead_letters = gateway.dead_letters
    print(f"\n  Dead letters: {len(dead_letters)}")
    for dl in dead_letters:
        print(f"    Tool: {dl.call.tool_name}, attempts: {dl.attempts}, error: {dl.error}")

    _log_tokens("error_recovery", finding.tokens_consumed, elapsed, llm_calls=2, search_calls=0)


# ===================================================================
# BASELINE TEST 6: Citation reality check (URL liveness)
# ===================================================================


async def test_citation_url_liveness(llm, gateway_with_real_search, simple_client):
    """For every citation produced, HTTP HEAD the URL to check liveness."""
    start = time.monotonic()
    task = _make_task()
    spec = _make_spec()
    agent = _make_agent()

    research_agent = ResearchAgent(
        llm=llm,
        gateway=gateway_with_real_search,
        max_rounds=1,
    )

    async with asyncio.timeout(120):
        async for _ in research_agent.execute(task, spec, agent):
            pass

    finding = await research_agent.get_finding()
    elapsed = time.monotonic() - start

    # Collect all unique URLs from citations
    all_urls: set[str] = set()
    for claim in finding.claims:
        for cit in claim.citations:
            if cit.url.startswith("http"):
                all_urls.add(cit.url)

    print(f"\n  Total citations across claims: {sum(len(c.citations) for c in finding.claims)}")
    print(f"  Unique HTTP URLs: {len(all_urls)}")

    # HEAD check each URL
    live_count = 0
    dead_count = 0
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as http:
        for url in all_urls:
            try:
                resp = await http.head(url)
                if resp.status_code < 400:
                    live_count += 1
                else:
                    dead_count += 1
                    print(f"  [DEAD] {url} -> {resp.status_code}")
            except Exception as exc:
                dead_count += 1
                print(f"  [DEAD] {url} -> {type(exc).__name__}: {exc}")

    print(f"  Live URLs: {live_count}/{len(all_urls)}")
    print(f"  Dead URLs: {dead_count}/{len(all_urls)}")

    # At least some URLs should be live (we used real search)
    if all_urls:
        assert live_count > 0, "All citation URLs are dead"

    _log_tokens(
        "citation_url_liveness",
        finding.tokens_consumed,
        elapsed,
        llm_calls=2,
        search_calls=simple_client.call_count,
    )


# ===================================================================
# ADDITIONAL TEST: Zero search results handling
# ===================================================================


async def test_zero_search_results(llm):
    """What happens when search returns zero results?"""
    start = time.monotonic()

    registry = ToolRegistry()
    register_all_tools(registry)
    authorizer = ToolAuthorizer(registry)
    rate_limiter = InMemoryRateLimiter({})
    audit_logger = AuditLogger()
    mock_client = MockMCPClient()

    # All tools return empty results
    mock_client.set_response("exa_search", {"status": "ok", "results": []})
    mock_client.set_response("brave_search", {"status": "ok", "results": []})
    mock_client.set_response("edgar_filings", {"status": "ok", "results": []})

    gateway = MCPGateway(
        registry=registry,
        authorizer=authorizer,
        rate_limiter=rate_limiter,
        audit_logger=audit_logger,
        client=mock_client,
    )

    task = _make_task()
    spec = _make_spec()
    agent = _make_agent()

    research_agent = ResearchAgent(
        llm=llm,
        gateway=gateway,
        max_rounds=1,
    )

    from keystone.research.finding_writer import FindingValidationError

    events = []
    error_occurred = False
    error_type = None
    try:
        async with asyncio.timeout(120):
            async for event in research_agent.execute(task, spec, agent):
                events.append(event)
        finding = await research_agent.get_finding()
        print(f"\n  With zero results: {len(finding.claims)} claims produced")
        print(f"  Absence report: {finding.absence_report}")
    except (RuntimeError, FindingValidationError) as exc:
        error_occurred = True
        error_type = type(exc).__name__
        print(f"\n  Expected error with zero results: {error_type}: {exc}")

    elapsed = time.monotonic() - start
    # Expected behavior: FindingValidationError because claims lack citations.
    # This is structural enforcement working correctly -- unsubstantiated
    # claims are rejected, not silently passed through.
    print(f"  Error occurred: {error_occurred} ({error_type})")
    if error_occurred:
        print("  [CORRECT] System correctly refuses to produce unsubstantiated findings")
    _log_tokens("zero_search_results", 0, elapsed, llm_calls=2, search_calls=0)


# ===================================================================
# ADDITIONAL TEST: Agent synthesis quality check
# ===================================================================


async def test_synthesis_reflects_search_results(llm, gateway_with_real_search, simple_client):
    """Verify the agent's synthesis actually reflects search content, not hallucination."""
    start = time.monotonic()
    task = _make_task(
        description="What is the current market size for LiDAR sensors used in autonomous vehicles?"
    )
    spec = _make_spec()
    agent = _make_agent()

    research_agent = ResearchAgent(
        llm=llm,
        gateway=gateway_with_real_search,
        max_rounds=1,
    )

    async with asyncio.timeout(120):
        async for _ in research_agent.execute(task, spec, agent):
            pass

    finding = await research_agent.get_finding()
    elapsed = time.monotonic() - start

    # The claims should contain relevant terms from the actual search
    all_claim_text = " ".join(c.text.lower() for c in finding.claims)
    relevant_terms = ["lidar", "sensor", "market", "autonomous", "vehicle"]
    matched_terms = [t for t in relevant_terms if t in all_claim_text]

    print(f"\n  Claims text length: {len(all_claim_text)} chars")
    print(f"  Relevant terms found: {matched_terms}")
    print(f"  Claims: {len(finding.claims)}")

    # At least some relevant terms should appear
    assert len(matched_terms) >= 2, (
        f"Synthesis doesn't reflect search results. "
        f"Only matched: {matched_terms} of {relevant_terms}"
    )

    _log_tokens(
        "synthesis_quality",
        finding.tokens_consumed,
        elapsed,
        llm_calls=2,
        search_calls=simple_client.call_count,
    )


# ===================================================================
# ADDITIONAL TEST: Search query relevance
# ===================================================================


async def test_search_queries_are_relevant(simple_client):
    """Verify the search queries the agent would generate are actually relevant."""
    # The ResearchAgent passes task.description as the query directly
    # Verify search APIs return relevant results for our task description
    start = time.monotonic()

    query = "Estimate the total addressable market for L4+ AV sensors in North America through 2030"

    # Test Exa
    exa_result = await simple_client.call_tool("exa-mcp-server", "exa_search", {"query": query})
    exa_results = exa_result.get("results", [])

    # Test Brave
    brave_result = await simple_client.call_tool(
        "brave-search-mcp-server", "brave_search", {"query": query}
    )
    brave_results = brave_result.get("results", [])

    elapsed = time.monotonic() - start

    print(f"\n  Exa results for task query: {len(exa_results)}")
    for r in exa_results[:3]:
        print(f"    - {r.get('title', 'N/A')[:80]}")
    print(f"  Brave results for task query: {len(brave_results)}")
    for r in brave_results[:3]:
        print(f"    - {r.get('title', 'N/A')[:80]}")

    # At least one engine should return results
    total = len(exa_results) + len(brave_results)
    assert total > 0, "Both search engines returned 0 results for a reasonable query"

    _log_tokens("search_relevance", 0, elapsed, llm_calls=0, search_calls=2)


# ===================================================================
# ADDITIONAL TEST: Hallucinates tool name not in assigned set
# ===================================================================


async def test_unauthorized_tool_rejected_at_gateway(simple_client):
    """Agent tries to call a tool not in its assigned set -- gateway rejects."""
    registry = ToolRegistry()
    register_all_tools(registry)
    authorizer = ToolAuthorizer(registry)
    rate_limiter = InMemoryRateLimiter({})
    audit_logger = AuditLogger()
    gateway = MCPGateway(
        registry=registry,
        authorizer=authorizer,
        rate_limiter=rate_limiter,
        audit_logger=audit_logger,
        client=simple_client,
    )

    # Agent only has exa_search, tries to call paper_search
    call = ToolCall(
        agent_id="agent_rogue",
        tool_name=ToolName.PAPER_SEARCH,
        parameters={"query": "AV sensors"},
        engagement_id="ENG-TEST-001",
        client_id="CLIENT-TEST",
        assigned_tools=[ToolName.EXA_SEARCH, ToolName.BRAVE_SEARCH, ToolName.EDGAR_FILINGS],
    )

    from keystone.gateway.auth import AuthorizationError

    with pytest.raises(AuthorizationError):
        await gateway.execute(call)


# ===================================================================
# ADDITIONAL TEST: Parallel agents via AgentPool
# ===================================================================


async def test_parallel_agents_with_pool(llm, gateway_with_mock):
    """Run 2 agents in parallel via AgentPool, verify both produce findings."""
    from keystone.research.agent_pool import AgentPool

    start = time.monotonic()

    pool = AgentPool(llm=llm, gateway=gateway_with_mock, max_retries=0)

    task1 = _make_task(
        task_id="task_001",
        description="Estimate TAM for L4+ AV sensors in North America",
    )
    task2 = _make_task(
        task_id="task_002",
        description="Analyze competitive landscape of LiDAR sensor manufacturers",
        tools=[ToolName.EXA_SEARCH, ToolName.BRAVE_SEARCH, ToolName.EDGAR_FILINGS],
    )

    spec = _make_spec()
    agent1 = _make_agent(agent_id="agent_quant_001")
    agent2 = _make_agent(
        agent_id="agent_qual_002",
        research_type=ResearchAgentType.QUALITATIVE,
    )

    assignments = [
        (task1, spec, agent1),
        (task2, spec, agent2),
    ]

    async with asyncio.timeout(180):
        results = await pool.execute_all(assignments)

    elapsed = time.monotonic() - start

    successful = pool.get_successful_findings(results)
    failed = pool.get_failed_agents(results)

    print(f"\n  Parallel agents: {len(results)} total")
    print(f"  Successful: {len(successful)}")
    print(f"  Failed: {len(failed)}")
    for r in results:
        status = "OK" if r.success else f"FAIL: {r.error}"
        print(f"    {r.agent_id}: {status}")
        if r.finding:
            print(f"      Claims: {len(r.finding.claims)}, Tokens: {r.finding.tokens_consumed}")

    # At least one should succeed
    assert len(successful) >= 1, f"All agents failed: {[str(r.error) for r in failed]}"

    _log_tokens(
        "parallel_agents",
        sum(f.tokens_consumed for f in successful),
        elapsed,
        llm_calls=8,
        search_calls=0,
    )


# ===================================================================
# ADDITIONAL TEST: JSON parsing robustness
# ===================================================================


async def test_json_parsing_of_synthesis(llm):
    """Verify _parse_synthesis handles various JSON formats from the LLM."""
    from keystone.research.research_agent import ResearchAgent

    gateway = MCPGateway(
        registry=ToolRegistry(),
        authorizer=ToolAuthorizer(ToolRegistry()),
        rate_limiter=InMemoryRateLimiter({}),
        audit_logger=AuditLogger(),
    )
    ra = ResearchAgent(llm=llm, gateway=gateway)

    # Test: valid JSON array
    result1 = ra._parse_synthesis('[{"text": "claim1", "evidence": "ev1", "confidence": 0.8}]')
    assert len(result1) == 1
    assert result1[0]["text"] == "claim1"

    # Test: JSON object with "claims" key
    result2 = ra._parse_synthesis(
        '{"claims": [{"text": "claim2", "evidence": "ev2", "confidence": 0.7}]}'
    )
    assert len(result2) == 1
    assert result2[0]["text"] == "claim2"

    # Test: single JSON object (not wrapped in array)
    result3 = ra._parse_synthesis('{"text": "claim3", "evidence": "ev3", "confidence": 0.6}')
    assert len(result3) == 1

    # Test: markdown-wrapped JSON (common LLM behavior)
    md_wrapped = '```json\n[{"text": "claim4", "evidence": "ev4", "confidence": 0.9}]\n```'
    result4 = ra._parse_synthesis(md_wrapped)
    # Current parser returns empty list for markdown-wrapped JSON
    print(f"\n  Markdown-wrapped JSON parse result: {len(result4)} claims")
    if len(result4) == 0:
        print("  [FINDING] Parser does NOT handle markdown-wrapped JSON")

    # Test: invalid JSON
    result5 = ra._parse_synthesis("This is not JSON at all")
    assert result5 == [], f"Invalid JSON should return empty list, got: {result5}"

    # Test: JSON with trailing commentary
    with_commentary = (
        '[{"text": "claim5", "confidence": 0.5, "evidence": "ev5"}]\n\nHere are my findings...'
    )
    result6 = ra._parse_synthesis(with_commentary)
    print(f"  JSON with trailing text parse result: {len(result6)} claims")
    if len(result6) == 0:
        print("  [FINDING] Parser does NOT handle JSON with trailing commentary")


# ===================================================================
# ADDITIONAL TEST: Audit log completeness
# ===================================================================


async def test_audit_log_captures_all_calls(llm, simple_client):
    """Verify the audit log captures every tool call with full context."""
    start = time.monotonic()

    registry = ToolRegistry()
    register_all_tools(registry)
    authorizer = ToolAuthorizer(registry)
    rate_limiter = InMemoryRateLimiter({})
    audit_logger = AuditLogger(debug=True)
    gateway = MCPGateway(
        registry=registry,
        authorizer=authorizer,
        rate_limiter=rate_limiter,
        audit_logger=audit_logger,
        client=simple_client,
    )

    task = _make_task()
    spec = _make_spec()
    agent = _make_agent()

    research_agent = ResearchAgent(
        llm=llm,
        gateway=gateway,
        max_rounds=1,
    )

    async with asyncio.timeout(120):
        async for _ in research_agent.execute(task, spec, agent):
            pass

    elapsed = time.monotonic() - start

    # Check audit entries
    entries = audit_logger.get_entries(engagement_id="ENG-TEST-001")
    print(f"\n  Audit entries: {len(entries)}")
    for entry in entries:
        print(
            f"    {entry.tool_name}: success={entry.success}, "
            f"latency={entry.latency_ms:.0f}ms, retry={entry.retry_attempt}"
        )

    # Should have entries for each tool call
    assert len(entries) > 0, "No audit entries recorded"

    # All entries should have engagement context
    for entry in entries:
        assert entry.engagement_id == "ENG-TEST-001"
        assert entry.client_id == "CLIENT-TEST"
        assert entry.tool_name in [
            ToolName.EXA_SEARCH,
            ToolName.BRAVE_SEARCH,
            ToolName.EDGAR_FILINGS,
        ]

    _log_tokens("audit_log", 0, elapsed, llm_calls=2, search_calls=simple_client.call_count)


# ===================================================================
# Summary fixture
# ===================================================================


def test_zz_token_summary():
    """Print token consumption summary (runs last due to name)."""
    if not _token_log:
        print("\n  No token data collected (tests may have been skipped)")
        return

    print("\n" + "=" * 70)
    print("  TOKEN CONSUMPTION SUMMARY")
    print("=" * 70)
    total_tokens = 0
    total_elapsed = 0
    total_llm = 0
    total_search = 0
    for entry in _token_log:
        total_tokens += entry["tokens"]
        total_elapsed += entry["elapsed_s"]
        total_llm += entry["llm_calls"]
        total_search += entry["search_calls"]
        print(
            f"  {entry['test']:40s} {entry['tokens']:>8} tokens  "
            f"{entry['elapsed_s']:>6.1f}s  {entry['llm_calls']:>2} LLM  "
            f"{entry['search_calls']:>2} search"
        )
    print("-" * 70)
    print(
        f"  {'TOTAL':40s} {total_tokens:>8} tokens  "
        f"{total_elapsed:>6.1f}s  {total_llm:>2} LLM  "
        f"{total_search:>2} search"
    )
    print("=" * 70)
