"""Unit tests for ResearchAgent deep research mode.

Deep mode replaces the multi-round gateway loop with one multi-turn
``claude -p`` call that is given WebSearch + WebFetch tools and must
output a single structured JSON payload. These tests exercise the
prompt construction, response parsing, event emission, fallback to
shallow mode, and absence-report generation without touching a real
Claude subprocess.

All LLM calls are mocked. No real web traffic.
"""

from __future__ import annotations

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
from keystone.gateway.rate_limiter import InMemoryRateLimiter
from keystone.gateway.servers import build_default_rate_limits, register_all_tools
from keystone.gateway.tool_registry import ToolRegistry
from keystone.models.agents import (
    AgentDefinition,
    AgentInstance,
    AgentRole,
    ResearchAgentType,
)
from keystone.models.citations import SourceType
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
from keystone.research.evidence_context import EvidenceContextProvider
from keystone.research.research_agent import ResearchAgent
from keystone.retrieval.parse_models import (
    Coverage,
    CoverageStatus,
    EvidencePrepRecord,
    Locator,
    ParseConfidence,
    ParseConfidenceTier,
    ParserIdentity,
    PassageKind,
    SourceFamily,
)

# ---------------------------------------------------------------------------
# Canned deep-research JSON payloads
# ---------------------------------------------------------------------------

_DEEP_JSON_DICT = {
    "claims": [
        {
            "text": "LiDAR TAM in North America reaches $9.5B by 2030",
            "evidence": "Yole Developpement and Frost & Sullivan converge on $8-11B.",
            "confidence": 0.82,
            "caveats": ["Depends on L4 robotaxi timelines slipping no more than 2 years"],
            "sources": [
                {
                    "url": "https://www.yolegroup.com/report/lidar-2030",
                    "title": "Yole LiDAR Market Report",
                    "content_snippet": "LiDAR TAM forecast revised to $9.5B by 2030...",
                },
                {
                    "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=LAZR",
                    "title": "Luminar 10-K filings",
                    "content_snippet": "Revenue 2025 guidance set at $110-130M...",
                },
            ],
        },
        {
            "text": "Chinese LiDAR makers now hold 60% of global unit share",
            "evidence": "Hesai + RoboSense shipments crossed 500k combined in 2025.",
            "confidence": 0.71,
            "caveats": ["Unit share and revenue share diverge materially"],
            "sources": [
                {
                    "url": "https://www.hesaitech.com/investor",
                    "title": "Hesai Investor Update Q4 2025",
                    "content_snippet": "Delivered 220k units in Q4 2025...",
                }
            ],
        },
    ],
    "absence_report": [
        "No public disclosure of Mobileye chauffeur LiDAR BoM",
        "No 2030 unit shipment forecast with a transparent methodology",
        "No concrete L4 mandatory-LiDAR regulation timeline from NHTSA",
    ],
}

_DEEP_JSON_LIST_ONLY = [
    {
        "text": "Hesai leads Chinese LiDAR share",
        "evidence": "Hesai press release + industry tracker",
        "confidence": 0.6,
        "caveats": [],
        "sources": [
            {
                "url": "https://example.com/hesai-share",
                "title": "Hesai share report",
                "content_snippet": "Hesai recorded 220k units Q4 2025...",
            }
        ],
    }
]


def _deep_response_dict() -> str:
    # Real claude output wraps the JSON in ```json fences sometimes; include
    # a little pre/post prose to exercise the parser's tolerance.
    body = json.dumps(_DEEP_JSON_DICT)
    return f"Here is my analysis.\n\n```json\n{body}\n```\n\nThanks."


def _deep_response_list() -> str:
    return json.dumps(_DEEP_JSON_LIST_ONLY)


async def _deep_llm(prompt: str) -> str:
    return _deep_response_dict()


async def _deep_llm_list(prompt: str) -> str:
    return _deep_response_list()


async def _deep_llm_empty(prompt: str) -> str:
    return json.dumps({"claims": []})


async def _deep_llm_no_absence(prompt: str) -> str:
    data = {**_DEEP_JSON_DICT, "absence_report": []}
    return json.dumps(data)


async def _deep_llm_defaultless(prompt: str) -> str:
    # Claim dict with only `text` + `sources`; parser must fill defaults.
    return json.dumps(
        {
            "claims": [
                {
                    "text": "Bare claim",
                    "sources": [
                        {
                            "url": "https://sec.gov/edgar",
                            "title": "EDGAR",
                        }
                    ],
                }
            ],
            "absence_report": ["nothing missing"],
        }
    )


async def _deep_llm_garbage(prompt: str) -> str:
    return "this is not json and never will be {]}"


async def _shallow_fallback_llm(prompt: str) -> str:
    # If the agent ends up in shallow mode, _execute_shallow expects a JSON
    # array of claims with citation_refs. Confidence is 0.85 so the quality
    # threshold halts shallow after one round (stable single-claim output).
    if "NOT found" in prompt or "absence" in prompt.lower():
        return json.dumps(["Shallow fallback absence 1"])
    return json.dumps(
        [
            {
                "text": "Shallow fallback claim",
                "evidence": "Fallback evidence",
                "citation_refs": ["SRC-001"],
                "confidence": 0.85,
                "caveats": [],
            }
        ]
    )


# ---------------------------------------------------------------------------
# Fixtures shared across all tests
# ---------------------------------------------------------------------------


def _build_gateway() -> tuple[MCPGateway, MockMCPClient]:
    registry = ToolRegistry()
    register_all_tools(registry)
    authorizer = ToolAuthorizer(registry)
    limiter = InMemoryRateLimiter(build_default_rate_limits())
    audit = AuditLogger()
    client = MockMCPClient()
    for tool in ("exa_search", "brave_search", "edgar_filings"):
        client.set_response(tool, {"url": f"https://example.com/{tool}", "title": tool})
    gateway = MCPGateway(
        registry=registry,
        authorizer=authorizer,
        rate_limiter=limiter,
        audit_logger=audit,
        client=client,
    )
    return gateway, client


def _make_task(**overrides: object) -> ResearchTask:
    defaults: dict[str, object] = {
        "id": "task_deep",
        "engagement_id": "eng_deep",
        "client_id": "client_deep",
        "category": TaskCategory.MARKET_SIZING,
        "type": TaskType.ESTIMATIVE,
        "target_decision_usefulness": 4,
        "description": "Estimate TAM for LiDAR sensors in L4+ AV market through 2030.",
        "acceptance_criteria": [
            "Cite at least 3 primary sources",
            "Provide a 2026-2030 CAGR",
        ],
        "deliverable_destination": "Section 3.2",
        "priority": 1,
        "anti_confirmatory_framing": "Where does LiDAR-free robotaxi economics win?",
        "assigned_tools": ["exa_search", "brave_search", "edgar_filings"],
        "assigned_model": ModelTier.STANDARD,
        "end_product": "LiDAR TAM estimate with methodology and sensitivity analysis",
    }
    defaults.update(overrides)
    return ResearchTask(**defaults)  # type: ignore[arg-type]


def _make_agent() -> AgentInstance:
    defn = AgentDefinition(
        name="deep_researcher",
        description="Deep research agent",
        role=AgentRole.RESEARCH,
        model=ModelTier.STANDARD,
        tools=["exa_search", "brave_search", "edgar_filings"],
        research_type=ResearchAgentType.QUANTITATIVE,
    )
    return AgentInstance(
        agent_id="agent_deep",
        engagement_id="eng_deep",
        client_id="client_deep",
        definition=defn,
        working_dir="/tmp/keystone/agent_deep",
    )


def _make_spec() -> EngagementSpec:
    research_spec = ResearchSpec(
        engagement_id="eng_deep",
        client_id="client_deep",
        title="AV LiDAR Market Deep Dive",
        created_at="2026-04-17T00:00:00Z",
        specification_version=1,
        decision_context="Decide whether to greenlight a LiDAR sensor OEM investment",
        surprising_finding="LiDAR TAM is collapsing faster than consensus expects",
        questions=[
            ResearchQuestion(
                question="What is the 2030 TAM for automotive LiDAR?",
                is_primary=True,
            ),
            ResearchQuestion(
                question="Who are the credible market leaders?",
                is_primary=False,
            ),
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
        project="AV LiDAR Market Deep Dive",
        engagement_id="eng_deep",
        client_id="client_deep",
        research_md_path="eng_deep/RESEARCH.md",
        specification_version=1,
        decomposition_rationale="Single deep-research task",
        tasks=[_make_task()],
    )
    return EngagementSpec(
        research_spec=research_spec,
        task_decomposition=decomposition,
        validation_report=validation,
    )


def _make_evidence_record(
    *,
    record_id: str = "rec-001",
    artifact_id: str = "art-deep-001",
    url: str = "https://example.com/context-pdf",
    title: str = "Context PDF",
    text: str = "Contextual evidence about LiDAR growth",
    page: int = 1,
) -> EvidencePrepRecord:
    return EvidencePrepRecord(
        record_id=record_id,
        artifact_id=artifact_id,
        canonical_url=url,
        title=title,
        source_family=SourceFamily.PDF,
        passage_kind=PassageKind.PARAGRAPH,
        text=text,
        locator=Locator(section_path=[], paragraph_index=0, page_number=page),
        parse_confidence=ParseConfidence(
            score=0.9,
            tier=ParseConfidenceTier.HIGH,
            reasons=["PDF_PAGE_TEXT"],
        ),
        content_hash="d" * 64,
        fetched_at="2026-04-17T12:00:00Z",
        coverage=Coverage(status=CoverageStatus.COMPLETE),
        parser=ParserIdentity(name="keystone.pdf.v1", version="1.0.0"),
    )


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------


class TestDeepPromptConstruction:
    def test_prompt_includes_engagement_title_and_task_description(self) -> None:
        gw, _ = _build_gateway()
        agent = ResearchAgent(llm=_shallow_fallback_llm, gateway=gw, deep_llm=_deep_llm)
        task = _make_task()
        spec = _make_spec()

        prompt = agent._build_deep_research_prompt(task, spec, _make_agent())

        assert "AV LiDAR Market Deep Dive" in prompt
        assert "Estimate TAM for LiDAR sensors" in prompt
        assert "robotaxi" in prompt  # anti-confirmatory framing

    def test_prompt_enumerates_every_research_question(self) -> None:
        gw, _ = _build_gateway()
        agent = ResearchAgent(llm=_shallow_fallback_llm, gateway=gw, deep_llm=_deep_llm)
        prompt = agent._build_deep_research_prompt(_make_task(), _make_spec(), _make_agent())

        assert "[PRIMARY] What is the 2030 TAM for automotive LiDAR?" in prompt
        assert "Who are the credible market leaders?" in prompt

    def test_prompt_includes_every_acceptance_criterion(self) -> None:
        gw, _ = _build_gateway()
        agent = ResearchAgent(llm=_shallow_fallback_llm, gateway=gw, deep_llm=_deep_llm)
        prompt = agent._build_deep_research_prompt(_make_task(), _make_spec(), _make_agent())

        assert "Cite at least 3 primary sources" in prompt
        assert "Provide a 2026-2030 CAGR" in prompt

    def test_prompt_requests_structured_json_with_sources(self) -> None:
        gw, _ = _build_gateway()
        agent = ResearchAgent(llm=_shallow_fallback_llm, gateway=gw, deep_llm=_deep_llm)
        prompt = agent._build_deep_research_prompt(_make_task(), _make_spec(), _make_agent())

        assert '"claims"' in prompt
        assert '"absence_report"' in prompt
        assert '"sources"' in prompt
        assert "confidence" in prompt
        assert "caveats" in prompt

    def test_prompt_omits_evidence_block_when_no_provider(self) -> None:
        gw, _ = _build_gateway()
        agent = ResearchAgent(llm=_shallow_fallback_llm, gateway=gw, deep_llm=_deep_llm)
        # Pass the prompt through the same preparation path the executor uses.
        agent._prepare_evidence_context(_make_task())
        prompt = agent._build_deep_research_prompt(_make_task(), _make_spec(), _make_agent())

        assert "PARSED EVIDENCE ALREADY FETCHED" not in prompt

    def test_prompt_includes_evidence_block_when_provider_has_records(self) -> None:
        record = _make_evidence_record(text="Key LiDAR revenue datum: $450M in 2025")
        provider = EvidenceContextProvider([record])
        gw, _ = _build_gateway()
        agent = ResearchAgent(
            llm=_shallow_fallback_llm,
            gateway=gw,
            deep_llm=_deep_llm,
            evidence_provider=provider,
        )
        agent._prepare_evidence_context(_make_task())
        prompt = agent._build_deep_research_prompt(_make_task(), _make_spec(), _make_agent())

        assert "PARSED EVIDENCE ALREADY FETCHED" in prompt
        assert "Key LiDAR revenue datum" in prompt

    def test_prompt_demands_at_least_twenty_claims(self) -> None:
        """Regression: deep mode is worthless if we forget to ask for volume."""
        gw, _ = _build_gateway()
        agent = ResearchAgent(llm=_shallow_fallback_llm, gateway=gw, deep_llm=_deep_llm)
        prompt = agent._build_deep_research_prompt(_make_task(), _make_spec(), _make_agent())

        assert "at least 20 claims" in prompt

    def test_prompt_bakes_in_anti_confirmatory_instructions(self) -> None:
        gw, _ = _build_gateway()
        agent = ResearchAgent(llm=_shallow_fallback_llm, gateway=gw, deep_llm=_deep_llm)
        prompt = agent._build_deep_research_prompt(_make_task(), _make_spec(), _make_agent())

        assert "evidence AGAINST" in prompt
        assert "contrarian" in prompt


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------


class TestDeepResponseParsing:
    def test_parse_dict_shape_returns_claims_and_absence(self) -> None:
        gw, _ = _build_gateway()
        agent = ResearchAgent(llm=_shallow_fallback_llm, gateway=gw, deep_llm=_deep_llm)

        parsed = agent._parse_deep_response(_deep_response_dict())
        assert len(parsed["claims"]) == 2
        assert len(parsed["absence_report"]) == 3

    def test_parse_list_shape_hydrates_into_dict(self) -> None:
        gw, _ = _build_gateway()
        agent = ResearchAgent(llm=_shallow_fallback_llm, gateway=gw, deep_llm=_deep_llm_list)

        parsed = agent._parse_deep_response(_deep_response_list())
        assert len(parsed["claims"]) == 1
        assert parsed["absence_report"] == []

    def test_parse_dict_without_claims_returns_empty(self) -> None:
        gw, _ = _build_gateway()
        agent = ResearchAgent(llm=_shallow_fallback_llm, gateway=gw, deep_llm=_deep_llm)

        parsed = agent._parse_deep_response(json.dumps({"something_else": "whatever"}))
        assert parsed == {"claims": [], "absence_report": []}

    def test_parse_completely_broken_json_raises(self) -> None:
        gw, _ = _build_gateway()
        agent = ResearchAgent(llm=_shallow_fallback_llm, gateway=gw, deep_llm=_deep_llm_garbage)

        with pytest.raises(RuntimeError, match="parseable JSON"):
            agent._parse_deep_response("this is not json and never will be {]}")


# ---------------------------------------------------------------------------
# End-to-end execute() in deep mode
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestDeepExecute:
    async def test_deep_execute_emits_all_pipeline_event_types(self) -> None:
        gw, _ = _build_gateway()
        agent = ResearchAgent(llm=_shallow_fallback_llm, gateway=gw, deep_llm=_deep_llm)

        events = []
        async for event in agent.execute(_make_task(), _make_spec(), _make_agent()):
            events.append(event)

        types = {type(e).__name__ for e in events}
        assert "ResearchStarted" in types
        assert "SourceFound" in types
        assert "CitationExtracted" in types
        assert "FindingSynthesized" in types
        assert "ResearchComplete" in types

    async def test_deep_execute_produces_finding_with_expected_claim_count(self) -> None:
        gw, _ = _build_gateway()
        agent = ResearchAgent(llm=_shallow_fallback_llm, gateway=gw, deep_llm=_deep_llm)

        async for _ in agent.execute(_make_task(), _make_spec(), _make_agent()):
            pass

        finding = await agent.get_finding()
        assert len(finding.claims) == 2
        assert finding.agent_id == "agent_deep"
        assert finding.task_id == "task_deep"
        # Deep mode attaches per-claim sources, so absence_report must still
        # be non-empty (either from the LLM or from the shallow fallback
        # generator).
        assert finding.absence_report, "absence report must not be empty"

    async def test_deep_execute_attaches_each_source_as_citation(self) -> None:
        gw, _ = _build_gateway()
        agent = ResearchAgent(llm=_shallow_fallback_llm, gateway=gw, deep_llm=_deep_llm)

        async for _ in agent.execute(_make_task(), _make_spec(), _make_agent()):
            pass

        finding = await agent.get_finding()
        # Claim 0 had 2 sources, claim 1 had 1 source => 3 total citations.
        total_cits = sum(len(c.citations) for c in finding.claims)
        assert total_cits == 3

    async def test_deep_execute_source_types_inferred_from_url(self) -> None:
        gw, _ = _build_gateway()
        agent = ResearchAgent(llm=_shallow_fallback_llm, gateway=gw, deep_llm=_deep_llm)

        async for _ in agent.execute(_make_task(), _make_spec(), _make_agent()):
            pass

        finding = await agent.get_finding()
        flat = [cit for c in finding.claims for cit in c.citations]
        sec_cits = [c for c in flat if "sec.gov" in c.url.lower()]
        assert sec_cits and sec_cits[0].source_type is SourceType.FILING

    async def test_deep_execute_emits_one_citation_event_per_source(self) -> None:
        gw, _ = _build_gateway()
        agent = ResearchAgent(llm=_shallow_fallback_llm, gateway=gw, deep_llm=_deep_llm)

        events = []
        async for event in agent.execute(_make_task(), _make_spec(), _make_agent()):
            events.append(event)

        source_events = [e for e in events if isinstance(e, SourceFound)]
        citation_events = [e for e in events if isinstance(e, CitationExtracted)]
        # 3 sources in the canned response => 3 SourceFound + 3 CitationExtracted.
        assert len(source_events) == 3
        assert len(citation_events) == 3
        for se in source_events:
            assert se.source_type == "deep_research"

    async def test_deep_execute_fills_defaults_for_sparse_claim_fields(self) -> None:
        gw, _ = _build_gateway()
        agent = ResearchAgent(
            llm=_shallow_fallback_llm,
            gateway=gw,
            deep_llm=_deep_llm_defaultless,
        )

        async for _ in agent.execute(_make_task(), _make_spec(), _make_agent()):
            pass

        finding = await agent.get_finding()
        claim = finding.claims[0]
        # evidence defaults to the claim text, confidence to 0.5, caveats to [].
        assert claim.evidence == "Bare claim"
        assert claim.confidence == pytest.approx(0.5)
        assert claim.caveats == []

    async def test_deep_execute_zero_claims_falls_back_to_shallow(self) -> None:
        # Empty claims raises inside _execute_deep; execute() catches the
        # exception and retries via shallow mode.
        gw, _ = _build_gateway()
        agent = ResearchAgent(
            llm=_shallow_fallback_llm,
            gateway=gw,
            deep_llm=_deep_llm_empty,
        )

        async for _ in agent.execute(_make_task(), _make_spec(), _make_agent()):
            pass

        finding = await agent.get_finding()
        # Shallow mock yields 1 claim with 1 citation.
        assert len(finding.claims) == 1
        assert finding.claims[0].text == "Shallow fallback claim"

    async def test_deep_execute_falls_back_when_deep_llm_raises(self) -> None:
        async def broken_deep(prompt: str) -> str:
            raise RuntimeError("deep research timed out")

        gw, _ = _build_gateway()
        agent = ResearchAgent(
            llm=_shallow_fallback_llm,
            gateway=gw,
            deep_llm=broken_deep,
        )

        async for _ in agent.execute(_make_task(), _make_spec(), _make_agent()):
            pass

        finding = await agent.get_finding()
        assert len(finding.claims) == 1
        # Citations came from the shallow SRC-NNN table, not from deep mode.
        for claim in finding.claims:
            for cit in claim.citations:
                assert "tool://" in cit.url or cit.url.startswith("https://")

    async def test_deep_execute_generates_absence_report_when_llm_omits_one(self) -> None:
        gw, _ = _build_gateway()
        agent = ResearchAgent(
            llm=_shallow_fallback_llm,
            gateway=gw,
            deep_llm=_deep_llm_no_absence,
        )

        async for _ in agent.execute(_make_task(), _make_spec(), _make_agent()):
            pass

        finding = await agent.get_finding()
        # LLM returned absence_report=[], so agent falls back to
        # _generate_absence_report which goes through the shallow LLM
        # and produces the "Shallow fallback absence 1" canned entry.
        assert finding.absence_report == ["Shallow fallback absence 1"]

    async def test_deep_execute_tokens_consumed_is_rough_estimate(self) -> None:
        gw, _ = _build_gateway()
        agent = ResearchAgent(llm=_shallow_fallback_llm, gateway=gw, deep_llm=_deep_llm)

        async for _ in agent.execute(_make_task(), _make_spec(), _make_agent()):
            pass

        finding = await agent.get_finding()
        assert finding.tokens_consumed > 0

    async def test_deep_execute_source_count_matches_citation_events(self) -> None:
        gw, _ = _build_gateway()
        agent = ResearchAgent(llm=_shallow_fallback_llm, gateway=gw, deep_llm=_deep_llm)

        events = []
        async for event in agent.execute(_make_task(), _make_spec(), _make_agent()):
            events.append(event)
        finding = await agent.get_finding()

        complete = next(e for e in events if isinstance(e, ResearchComplete))
        source_events = [e for e in events if isinstance(e, SourceFound)]
        assert complete.sources_consulted == len(source_events)
        assert finding.sources_consulted == complete.sources_consulted

    async def test_deep_mode_bypasses_gateway(self) -> None:
        """Deep mode must not hit MCPGateway -- the MCP client stays cold."""
        gw, client = _build_gateway()
        agent = ResearchAgent(llm=_shallow_fallback_llm, gateway=gw, deep_llm=_deep_llm)

        async for _ in agent.execute(_make_task(), _make_spec(), _make_agent()):
            pass

        # Gateway's mock MCP client was never called.
        assert client.call_count == 0


# ---------------------------------------------------------------------------
# Research-started event consistency
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestDeepEventMetadata:
    async def test_research_started_and_complete_tie_to_task(self) -> None:
        gw, _ = _build_gateway()
        agent = ResearchAgent(llm=_shallow_fallback_llm, gateway=gw, deep_llm=_deep_llm)

        events = []
        async for event in agent.execute(_make_task(), _make_spec(), _make_agent()):
            events.append(event)

        started = next(e for e in events if isinstance(e, ResearchStarted))
        complete = next(e for e in events if isinstance(e, ResearchComplete))
        assert started.task_id == "task_deep"
        assert complete.task_id == "task_deep"
        assert started.agent_id == complete.agent_id == "agent_deep"

    async def test_finding_synthesized_confidence_range_matches_claims(self) -> None:
        gw, _ = _build_gateway()
        agent = ResearchAgent(llm=_shallow_fallback_llm, gateway=gw, deep_llm=_deep_llm)

        events = []
        async for event in agent.execute(_make_task(), _make_spec(), _make_agent()):
            events.append(event)

        synth = next(e for e in events if isinstance(e, FindingSynthesized))
        # Canned claims have confidence 0.82 and 0.71 -> range "0.71-0.82".
        assert synth.confidence_range == "0.71-0.82"
        assert synth.claim_count == 2

    async def test_deep_execute_writes_audit_log_per_source(self) -> None:
        """Deep mode must restore audit parity: one entry per observed source.

        The claude -p subprocess bypasses ``MCPGateway.call_tool``, so
        without this wiring the audit log would silently miss every
        WebSearch / WebFetch the agent performed. Regression guard.
        Per-source entries have ``latency_ms=None`` (can't disaggregate
        per-fetch timing from a single ``claude -p`` session); the
        wrapping ``deep_research:session`` entry carries the real
        session-level latency and summary counts.
        """

        gw, _ = _build_gateway()
        # Capture the audit logger before calling execute so we can
        # count entries afterwards (the helper shares one AuditLogger
        # across the gateway instance).
        audit_logger = gw.audit_logger
        agent = ResearchAgent(llm=_shallow_fallback_llm, gateway=gw, deep_llm=_deep_llm)

        async for _ in agent.execute(_make_task(), _make_spec(), _make_agent()):
            pass

        entries = audit_logger.get_entries(
            agent_id="agent_deep",
            engagement_id="eng_deep",
        )
        per_source = [
            e
            for e in entries
            if e.tool_name in {"deep_research:WebSearch", "deep_research:WebFetch"}
        ]
        session_entries = [e for e in entries if e.tool_name == "deep_research:session"]

        # 3 canned sources => 3 per-source audit entries.
        assert len(per_source) == 3
        # Exactly one session entry per execute() call.
        assert len(session_entries) == 1

        for entry in per_source:
            assert entry.success is True
            assert entry.client_id == "client_deep"
            assert entry.input_hash  # hashed parameters recorded
            assert entry.output_hash  # hashed result recorded
            assert entry.latency_ms is None, "per-source latency should be None"

        session = session_entries[0]
        assert session.success is True
        assert session.latency_ms is not None
        assert session.latency_ms >= 0.0

    async def test_deep_audit_tool_name_differentiates_fetch_vs_search(self) -> None:
        gw, _ = _build_gateway()
        agent = ResearchAgent(llm=_shallow_fallback_llm, gateway=gw, deep_llm=_deep_llm)

        async for _ in agent.execute(_make_task(), _make_spec(), _make_agent()):
            pass

        entries = gw.audit_logger.get_entries(agent_id="agent_deep")
        tool_names = {e.tool_name for e in entries if e.tool_name.startswith("deep_research:")}
        # Canned deep responses include https:// URLs, so WebFetch must
        # be represented. (WebSearch shows up for non-http URLs, which
        # the canned fixture does not include -- either is acceptable as
        # long as at least one WebFetch name is recorded.)
        assert "deep_research:WebFetch" in tool_names

    async def test_deep_session_audit_records_summary_counts(self) -> None:
        gw, _ = _build_gateway()
        agent = ResearchAgent(llm=_shallow_fallback_llm, gateway=gw, deep_llm=_deep_llm)

        async for _ in agent.execute(_make_task(), _make_spec(), _make_agent()):
            pass

        entries = gw.audit_logger.get_entries(agent_id="agent_deep")
        session = next(e for e in entries if e.tool_name == "deep_research:session")
        assert session.success is True
        # latency_ms must be a real measurement (non-None, non-zero for
        # a non-instantaneous canned fixture).
        assert session.latency_ms is not None
        assert session.latency_ms >= 0.0
        # output_hash encodes n_sources/n_claims on success.
        assert session.output_hash

    async def test_deep_session_audit_records_failure_when_deep_llm_raises(self) -> None:
        async def broken_deep(prompt: str) -> str:
            raise RuntimeError("deep research timed out")

        gw, _ = _build_gateway()
        agent = ResearchAgent(
            llm=_shallow_fallback_llm,
            gateway=gw,
            deep_llm=broken_deep,
        )

        async for _ in agent.execute(_make_task(), _make_spec(), _make_agent()):
            pass

        entries = gw.audit_logger.get_entries(agent_id="agent_deep")
        session_entries = [e for e in entries if e.tool_name == "deep_research:session"]
        # Exactly one failure-session entry, even though execute() fell
        # back to shallow mode.
        assert len(session_entries) == 1
        session = session_entries[0]
        assert session.success is False
        assert session.error_type == "RuntimeError"
        assert session.error_message is not None
        assert "deep research timed out" in session.error_message
        # Failure latency is still measured.
        assert session.latency_ms is not None
        assert session.latency_ms >= 0.0
