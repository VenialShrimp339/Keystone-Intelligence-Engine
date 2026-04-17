"""Tests for the Lane E -> research bridge.

Covers the pure provider surface (selection, reference table, prompt
rendering), the ``evidence_to_citation`` mapping (provenance + source
type + quality score), and the ``ResearchAgent`` integration path
(EV-NNN refs in synthesis, Citation minting, SourceFound/CitationExtracted
events, sources_consulted accounting).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from keystone.events import CitationExtracted, SourceFound
from keystone.gateway.audit_log import AuditLogger
from keystone.gateway.auth import ToolAuthorizer
from keystone.gateway.mcp_gateway import MCPGateway, MockMCPClient
from keystone.gateway.rate_limiter import InMemoryRateLimiter, RateLimit
from keystone.gateway.servers import register_all_tools
from keystone.gateway.tool_registry import ToolRegistry
from keystone.models.agents import AgentDefinition, AgentInstance, AgentRole, ResearchAgentType
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
from keystone.research.evidence_context import (
    EvidenceContextProvider,
    evidence_to_citation,
    infer_source_type,
)
from keystone.research.research_agent import ResearchAgent
from keystone.retrieval.parse_models import (
    Coverage,
    CoverageStatus,
    EvidencePrepRecord,
    Locator,
    ParserIdentity,
    PassageKind,
    SourceFamily,
    confidence,
)

HASH_ZERO = "0" * 64
HASH_DEADBEEF = "deadbeef" * 8


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_record(
    *,
    record_id: str = "ev:passage-1",
    artifact_id: str = "art-1",
    canonical_url: str = "https://example.com/story",
    text: str = "The market grew 20% YoY according to the 2025 industry survey.",
    source_family: SourceFamily = SourceFamily.ARTICLE,
    passage_kind: PassageKind = PassageKind.PARAGRAPH,
    parse_score: float = 0.9,
    section_path: list[str] | None = None,
    page_number: int | None = None,
    title: str | None = "Industry Survey 2025",
    content_hash: str = HASH_ZERO,
    fetched_at: datetime | None = None,
) -> EvidencePrepRecord:
    return EvidencePrepRecord(
        record_id=record_id,
        artifact_id=artifact_id,
        canonical_url=canonical_url,
        content_hash=content_hash,
        coverage=Coverage(status=CoverageStatus.COMPLETE),
        source_family=source_family,
        parser=ParserIdentity(name="keystone.article.v1", version="1.0"),
        locator=Locator(
            section_path=section_path or [],
            paragraph_index=0,
            page_number=page_number,
        ),
        passage_kind=passage_kind,
        text=text,
        parse_confidence=confidence(parse_score, ["TEST"]),
        fetched_at=fetched_at or datetime(2026, 4, 17, 12, 0, tzinfo=UTC),
        title=title,
    )


def _make_task(**overrides) -> ResearchTask:
    defaults = {
        "id": "task_001",
        "engagement_id": "eng_001",
        "client_id": "client_001",
        "category": TaskCategory.MARKET_SIZING,
        "type": TaskType.ESTIMATIVE,
        "target_decision_usefulness": 4,
        "description": "Estimate market size",
        "acceptance_criteria": ["Cite 3+ sources", "Include ranges"],
        "deliverable_destination": "Section 2.1",
        "priority": 1,
        "anti_confirmatory_framing": "Evaluate what challenges the projection",
        "assigned_tools": ["exa_search", "brave_search", "edgar_filings"],
        "assigned_model": ModelTier.STANDARD,
        "end_product": "Market sizing estimate",
    }
    defaults.update(overrides)
    return ResearchTask(**defaults)


def _make_agent() -> AgentInstance:
    defn = AgentDefinition(
        name="quantitative_analyst",
        description="Quantitative research specialist",
        role=AgentRole.RESEARCH,
        model=ModelTier.STANDARD,
        tools=["exa_search", "brave_search", "edgar_filings"],
        research_type=ResearchAgentType.QUANTITATIVE,
    )
    return AgentInstance(
        agent_id="agent_001",
        engagement_id="eng_001",
        client_id="client_001",
        definition=defn,
        working_dir="/tmp/keystone/agent_001",
    )


def _make_spec() -> EngagementSpec:
    research_spec = ResearchSpec(
        engagement_id="eng_001",
        client_id="client_001",
        title="Market Analysis",
        created_at="2026-04-17T00:00:00Z",
        specification_version=1,
        decision_context="Evaluate entry",
        surprising_finding="Market is shrinking faster than expected",
        questions=[
            ResearchQuestion(question="What is the TAM?", is_primary=True),
        ],
        output_format="markdown",
        engagement_type=EngagementType.SIZING,
    )
    decomposition = TaskDecomposition(
        project="Market Analysis",
        engagement_id="eng_001",
        client_id="client_001",
        research_md_path="eng_001/RESEARCH.md",
        specification_version=1,
        decomposition_rationale="Single task for testing",
        tasks=[_make_task()],
    )
    return EngagementSpec(
        research_spec=research_spec,
        task_decomposition=decomposition,
        validation_report=ValidationReport(
            intent_clear=True,
            scope_valid=True,
            within_frontier=True,
            quality_threshold_met=True,
        ),
    )


def _build_gateway() -> tuple[MCPGateway, MockMCPClient]:
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
    client = MockMCPClient()
    gateway = MCPGateway(
        registry=registry,
        authorizer=authorizer,
        rate_limiter=limiter,
        audit_logger=audit,
        client=client,
    )
    return gateway, client


# ---------------------------------------------------------------------------
# evidence_to_citation
# ---------------------------------------------------------------------------


class TestEvidenceToCitation:
    def test_preserves_provenance_chain(self) -> None:
        record = _make_record(content_hash=HASH_DEADBEEF)
        citation = evidence_to_citation(
            record,
            citation_id="CIT-ENG00001-AGENT001-001",
            engagement_id="eng_001",
            client_id="client_001",
            agent_id="agent_001",
        )
        assert citation.url == record.canonical_url
        assert citation.content_hash == HASH_DEADBEEF
        assert citation.title == "Industry Survey 2025"
        assert citation.engagement_id == "eng_001"
        assert citation.client_id == "client_001"
        assert citation.found_by_agents == ["agent_001"]
        assert citation.access_date == record.fetched_at

    def test_source_type_from_url_pattern(self) -> None:
        record = _make_record(canonical_url="https://www.sec.gov/cgi-bin/browse-edgar")
        citation = evidence_to_citation(
            record,
            citation_id="CIT-E-A-001",
            engagement_id="eng_001",
            client_id="client_001",
            agent_id="agent_001",
        )
        assert citation.source_type is SourceType.FILING

    def test_source_type_falls_back_to_family_for_unknown_url(self) -> None:
        pdf_record = _make_record(
            canonical_url="https://internal.example.org/paper", source_family=SourceFamily.PDF
        )
        citation = evidence_to_citation(
            pdf_record,
            citation_id="CIT-E-A-002",
            engagement_id="eng_001",
            client_id="client_001",
            agent_id="agent_001",
        )
        assert citation.source_type is SourceType.REPORT

        article_record = _make_record(
            canonical_url="https://unknown.example.org/post",
            source_family=SourceFamily.ARTICLE,
        )
        citation = evidence_to_citation(
            article_record,
            citation_id="CIT-E-A-003",
            engagement_id="eng_001",
            client_id="client_001",
            agent_id="agent_001",
        )
        assert citation.source_type is SourceType.NEWS

    def test_quality_score_mirrors_parse_tier(self) -> None:
        high = evidence_to_citation(
            _make_record(parse_score=0.95),
            citation_id="CIT-E-A-004",
            engagement_id="eng_001",
            client_id="client_001",
            agent_id="agent_001",
        )
        medium = evidence_to_citation(
            _make_record(parse_score=0.6),
            citation_id="CIT-E-A-005",
            engagement_id="eng_001",
            client_id="client_001",
            agent_id="agent_001",
        )
        low = evidence_to_citation(
            _make_record(parse_score=0.2),
            citation_id="CIT-E-A-006",
            engagement_id="eng_001",
            client_id="client_001",
            agent_id="agent_001",
        )
        assert high.quality_score > medium.quality_score > low.quality_score
        assert high.quality_score == pytest.approx(0.75)
        assert medium.quality_score == pytest.approx(0.6)
        assert low.quality_score == pytest.approx(0.4)

    def test_content_snippet_is_trimmed(self) -> None:
        long_text = "lorem ipsum " * 100
        record = _make_record(text=long_text)
        citation = evidence_to_citation(
            record,
            citation_id="CIT-E-A-007",
            engagement_id="eng_001",
            client_id="client_001",
            agent_id="agent_001",
        )
        assert citation.content_snippet is not None
        assert len(citation.content_snippet) <= 500
        assert citation.content_snippet.startswith("lorem ipsum")

    def test_title_falls_back_when_missing(self) -> None:
        record = _make_record(title=None)
        citation = evidence_to_citation(
            record,
            citation_id="CIT-E-A-008",
            engagement_id="eng_001",
            client_id="client_001",
            agent_id="agent_001",
        )
        assert "ev:passage-1" in citation.title
        assert record.source_family.value.title() in citation.title

    def test_naive_datetime_gets_utc_tz(self) -> None:
        record = _make_record()
        naive = datetime(2026, 4, 17, 9, 0)
        citation = evidence_to_citation(
            record,
            citation_id="CIT-E-A-009",
            engagement_id="eng_001",
            client_id="client_001",
            agent_id="agent_001",
            access_date=naive,
        )
        assert citation.access_date.tzinfo is not None


# ---------------------------------------------------------------------------
# infer_source_type
# ---------------------------------------------------------------------------


class TestInferSourceType:
    @pytest.mark.parametrize(
        "url, family, expected",
        [
            ("https://www.sec.gov/filing/x", SourceFamily.ARTICLE, SourceType.FILING),
            ("https://arxiv.org/abs/1234", SourceFamily.PDF, SourceType.ACADEMIC),
            ("https://reuters.com/article", SourceFamily.ARTICLE, SourceType.NEWS),
            ("https://custom.gov/paper.pdf", SourceFamily.PDF, SourceType.GOVERNMENT),
            ("https://random.co/news", SourceFamily.ARTICLE, SourceType.NEWS),
            ("https://random.co/paper", SourceFamily.PDF, SourceType.REPORT),
            ("https://random.co/thing", SourceFamily.UNKNOWN, SourceType.REPORT),
        ],
    )
    def test_url_domain_precedence(
        self, url: str, family: SourceFamily, expected: SourceType
    ) -> None:
        assert infer_source_type(url, family) is expected


# ---------------------------------------------------------------------------
# EvidenceContextProvider
# ---------------------------------------------------------------------------


class TestEvidenceContextProvider:
    def test_empty_provider_returns_no_records(self) -> None:
        provider = EvidenceContextProvider([])
        assert provider.record_count == 0
        assert provider.records_for_task(_make_task()) == []
        assert provider.render_passages_for_prompt({}) == ""

    def test_dedupes_by_record_id(self) -> None:
        r1 = _make_record(record_id="ev:dup")
        r2 = _make_record(record_id="ev:dup", text="Different text, same id")
        provider = EvidenceContextProvider([r1, r2])
        assert provider.record_count == 1
        # First occurrence wins
        assert provider.all_records()[0].text == r1.text

    def test_records_for_task_returns_all_when_no_filter(self) -> None:
        records = [
            _make_record(record_id="ev:1"),
            _make_record(record_id="ev:2"),
            _make_record(record_id="ev:3"),
        ]
        provider = EvidenceContextProvider(records)
        selected = provider.records_for_task(_make_task())
        assert [r.record_id for r in selected] == ["ev:1", "ev:2", "ev:3"]

    def test_task_filter_is_applied(self) -> None:
        r_pdf = _make_record(record_id="ev:pdf", source_family=SourceFamily.PDF)
        r_article = _make_record(record_id="ev:article", source_family=SourceFamily.ARTICLE)
        provider = EvidenceContextProvider(
            [r_pdf, r_article],
            task_filter=lambda _task, rec: rec.source_family is SourceFamily.PDF,
        )
        selected = provider.records_for_task(_make_task())
        assert [r.record_id for r in selected] == ["ev:pdf"]

    def test_max_passages_per_task_caps_selection(self) -> None:
        records = [_make_record(record_id=f"ev:{i}") for i in range(10)]
        provider = EvidenceContextProvider(records, max_passages_per_task=3)
        selected = provider.records_for_task(_make_task())
        assert len(selected) == 3
        assert [r.record_id for r in selected] == ["ev:0", "ev:1", "ev:2"]

    def test_max_passages_rejects_zero(self) -> None:
        with pytest.raises(ValueError, match="max_passages_per_task"):
            EvidenceContextProvider([], max_passages_per_task=0)

    def test_reference_table_is_stable_ordered(self) -> None:
        records = [_make_record(record_id=f"ev:{i}") for i in range(3)]
        provider = EvidenceContextProvider(records)
        selected = provider.records_for_task(_make_task())
        table = provider.build_reference_table(selected)
        assert list(table.keys()) == ["EV-001", "EV-002", "EV-003"]
        assert table["EV-001"].record_id == "ev:0"
        assert table["EV-003"].record_id == "ev:2"

    def test_render_passages_includes_ref_url_title_and_tier(self) -> None:
        record = _make_record(
            title="AV Sensor TAM",
            canonical_url="https://example.com/tam",
            parse_score=0.9,
            section_path=["Chapter 1", "Market"],
        )
        provider = EvidenceContextProvider([record])
        selected = provider.records_for_task(_make_task())
        rendered = provider.render_passages_for_prompt(provider.build_reference_table(selected))
        assert "EV-001" in rendered
        assert "AV Sensor TAM" in rendered
        assert "https://example.com/tam" in rendered
        assert "parse=high" in rendered
        assert "Chapter 1 > Market" in rendered

    def test_render_empty_table_returns_empty_string(self) -> None:
        provider = EvidenceContextProvider([_make_record()])
        assert provider.render_passages_for_prompt({}) == ""

    def test_pdf_locator_includes_page_number(self) -> None:
        record = _make_record(
            source_family=SourceFamily.PDF,
            passage_kind=PassageKind.PARAGRAPH,
            page_number=7,
        )
        provider = EvidenceContextProvider([record])
        selected = provider.records_for_task(_make_task())
        rendered = provider.render_passages_for_prompt(provider.build_reference_table(selected))
        assert "p.7" in rendered


# ---------------------------------------------------------------------------
# ResearchAgent integration
# ---------------------------------------------------------------------------


_MOCK_EVIDENCE_CLAIMS = json.dumps(
    [
        {
            "text": "Market grew 20% YoY",
            "evidence": "Industry survey cited in parsed article",
            "citation_refs": ["EV-001"],
            "confidence": 0.82,
            "caveats": [],
        },
        {
            "text": "Leading provider holds 40% share",
            "evidence": "Filing data from tool search",
            "citation_refs": ["SRC-001"],
            "confidence": 0.85,
            "caveats": [],
        },
    ]
)

_MOCK_ABSENCE = json.dumps(["Nothing on APAC growth"])


async def _evidence_llm(prompt: str) -> str:
    if "NOT found" in prompt or "absence" in prompt.lower():
        return _MOCK_ABSENCE
    return _MOCK_EVIDENCE_CLAIMS


class TestResearchAgentEvidenceIntegration:
    @pytest.mark.asyncio
    async def test_ev_ref_resolves_to_citation(self) -> None:
        gateway, client = _build_gateway()
        client.set_response("exa_search", {"url": "https://ex.com/a", "title": "Tool Source"})
        client.set_response("brave_search", {"url": "https://ex.com/b", "title": "Tool Source 2"})
        client.set_response("edgar_filings", {"url": "https://ex.com/c", "title": "Filing"})

        record = _make_record(canonical_url="https://example.com/survey", title="Parsed Survey")
        provider = EvidenceContextProvider([record])

        agent = ResearchAgent(
            llm=_evidence_llm,
            gateway=gateway,
            evidence_provider=provider,
            max_rounds=1,
        )
        async for _ in agent.execute(_make_task(), _make_spec(), _make_agent()):
            pass

        finding = await agent.get_finding()
        assert len(finding.claims) == 2

        # Claim referencing EV-001 must carry the parsed-evidence URL on its citation
        ev_claim = next(c for c in finding.claims if "20% YoY" in c.text)
        urls = {cit.url for cit in ev_claim.citations}
        assert "https://example.com/survey" in urls

    @pytest.mark.asyncio
    async def test_evidence_citation_emits_events_and_bumps_sources(self) -> None:
        gateway, client = _build_gateway()
        client.set_response("exa_search", {"url": "https://ex.com/a", "title": "Tool Source"})
        client.set_response("brave_search", {"url": "https://ex.com/b", "title": "Tool Source"})
        client.set_response("edgar_filings", {"url": "https://ex.com/c", "title": "Tool Source"})

        record = _make_record(canonical_url="https://example.com/survey")
        provider = EvidenceContextProvider([record])

        agent = ResearchAgent(
            llm=_evidence_llm,
            gateway=gateway,
            evidence_provider=provider,
            max_rounds=1,
        )
        events = []
        async for event in agent.execute(_make_task(), _make_spec(), _make_agent()):
            events.append(event)

        source_found = [e for e in events if isinstance(e, SourceFound)]
        ev_sources = [e for e in source_found if e.source_type == "lane_e_evidence"]
        assert len(ev_sources) == 1
        assert ev_sources[0].url == "https://example.com/survey"

        # CitationExtracted fires for every cited source (tool + parsed passage)
        cit_events = [e for e in events if isinstance(e, CitationExtracted)]
        assert any("survey" in e.title.lower() or "ev:" in e.title.lower() for e in cit_events)

        finding = await agent.get_finding()
        # Three tool citations + one parsed-evidence source
        assert finding.sources_consulted >= 4

    @pytest.mark.asyncio
    async def test_same_ev_ref_cited_twice_yields_one_citation(self) -> None:
        """A record cited from two claims still mints only one Citation."""

        double_ref_claims = json.dumps(
            [
                {
                    "text": "Claim A",
                    "evidence": "From parsed evidence",
                    "citation_refs": ["EV-001"],
                    "confidence": 0.81,
                    "caveats": [],
                },
                {
                    "text": "Claim B",
                    "evidence": "Also from parsed evidence",
                    "citation_refs": ["EV-001"],
                    "confidence": 0.82,
                    "caveats": [],
                },
            ]
        )

        async def llm(prompt: str) -> str:
            if "NOT found" in prompt or "absence" in prompt.lower():
                return _MOCK_ABSENCE
            return double_ref_claims

        gateway, client = _build_gateway()
        client.set_response("exa_search", {"url": "https://ex.com/a", "title": "Tool"})
        client.set_response("brave_search", {"url": "https://ex.com/b", "title": "Tool"})
        client.set_response("edgar_filings", {"url": "https://ex.com/c", "title": "Tool"})

        record = _make_record(canonical_url="https://example.com/survey")
        provider = EvidenceContextProvider([record])

        agent = ResearchAgent(
            llm=llm,
            gateway=gateway,
            evidence_provider=provider,
            max_rounds=1,
        )
        events = []
        async for event in agent.execute(_make_task(), _make_spec(), _make_agent()):
            events.append(event)

        finding = await agent.get_finding()
        ev_citation_ids = {
            cit.citation_id
            for claim in finding.claims
            for cit in claim.citations
            if cit.url == "https://example.com/survey"
        }
        assert len(ev_citation_ids) == 1

        ev_source_events = [
            e for e in events if isinstance(e, SourceFound) and e.source_type == "lane_e_evidence"
        ]
        assert len(ev_source_events) == 1

    @pytest.mark.asyncio
    async def test_unknown_ref_drops_its_claim(self) -> None:
        bad_claims = json.dumps(
            [
                {
                    "text": "Has no valid ref",
                    "evidence": "None",
                    "citation_refs": ["EV-999"],
                    "confidence": 0.8,
                    "caveats": [],
                },
                {
                    "text": "Has a valid ref",
                    "evidence": "Tool",
                    "citation_refs": ["SRC-001"],
                    "confidence": 0.8,
                    "caveats": [],
                },
            ]
        )

        async def llm(prompt: str) -> str:
            if "NOT found" in prompt or "absence" in prompt.lower():
                return _MOCK_ABSENCE
            return bad_claims

        gateway, client = _build_gateway()
        client.set_response("exa_search", {"url": "https://ex.com/a", "title": "Tool"})
        client.set_response("brave_search", {"url": "https://ex.com/b", "title": "Tool"})
        client.set_response("edgar_filings", {"url": "https://ex.com/c", "title": "Tool"})

        provider = EvidenceContextProvider([_make_record()])
        agent = ResearchAgent(
            llm=llm,
            gateway=gateway,
            evidence_provider=provider,
            max_rounds=1,
        )
        async for _ in agent.execute(_make_task(), _make_spec(), _make_agent()):
            pass

        finding = await agent.get_finding()
        texts = {c.text for c in finding.claims}
        assert "Has no valid ref" not in texts
        assert "Has a valid ref" in texts

    @pytest.mark.asyncio
    async def test_no_evidence_provider_means_no_ev_section(self) -> None:
        """Without an evidence provider, synthesis prompt omits the EV block."""
        gateway, client = _build_gateway()
        client.set_response("exa_search", {"url": "https://ex.com/a", "title": "Tool"})
        client.set_response("brave_search", {"url": "https://ex.com/b", "title": "Tool"})
        client.set_response("edgar_filings", {"url": "https://ex.com/c", "title": "Tool"})

        captured_prompts: list[str] = []

        async def capturing_llm(prompt: str) -> str:
            captured_prompts.append(prompt)
            if "NOT found" in prompt or "absence" in prompt.lower():
                return _MOCK_ABSENCE
            return json.dumps(
                [
                    {
                        "text": "T",
                        "evidence": "e",
                        "citation_refs": ["SRC-001"],
                        "confidence": 0.85,
                        "caveats": [],
                    }
                ]
            )

        agent = ResearchAgent(llm=capturing_llm, gateway=gateway, max_rounds=1)
        async for _ in agent.execute(_make_task(), _make_spec(), _make_agent()):
            pass

        synthesis_prompts = [p for p in captured_prompts if "Synthesize findings" in p]
        assert synthesis_prompts
        for prompt in synthesis_prompts:
            assert "Parsed evidence passages" not in prompt
            assert "EV-001" not in prompt

    @pytest.mark.asyncio
    async def test_ev_block_is_present_in_synthesis_prompt_when_provider_set(self) -> None:
        gateway, client = _build_gateway()
        client.set_response("exa_search", {"url": "https://ex.com/a", "title": "Tool"})
        client.set_response("brave_search", {"url": "https://ex.com/b", "title": "Tool"})
        client.set_response("edgar_filings", {"url": "https://ex.com/c", "title": "Tool"})

        captured_prompts: list[str] = []

        async def capturing_llm(prompt: str) -> str:
            captured_prompts.append(prompt)
            if "NOT found" in prompt or "absence" in prompt.lower():
                return _MOCK_ABSENCE
            return _MOCK_EVIDENCE_CLAIMS

        provider = EvidenceContextProvider([_make_record(title="Survey")])
        agent = ResearchAgent(
            llm=capturing_llm,
            gateway=gateway,
            evidence_provider=provider,
            max_rounds=1,
        )
        async for _ in agent.execute(_make_task(), _make_spec(), _make_agent()):
            pass

        synthesis_prompts = [p for p in captured_prompts if "Synthesize findings" in p]
        assert any("Parsed evidence passages" in p for p in synthesis_prompts)
        assert any("EV-001" in p for p in synthesis_prompts)
        assert any("Survey" in p for p in synthesis_prompts)


# ---------------------------------------------------------------------------
# AgentPool threading
# ---------------------------------------------------------------------------


class TestAgentPoolThreading:
    @pytest.mark.asyncio
    async def test_pool_passes_evidence_provider_to_agents(self) -> None:
        from keystone.research.agent_pool import AgentPool

        gateway, client = _build_gateway()
        client.set_response("exa_search", {"url": "https://ex.com/a", "title": "Tool"})
        client.set_response("brave_search", {"url": "https://ex.com/b", "title": "Tool"})
        client.set_response("edgar_filings", {"url": "https://ex.com/c", "title": "Tool"})

        provider = EvidenceContextProvider(
            [_make_record(canonical_url="https://example.com/survey")]
        )
        pool = AgentPool(
            llm=_evidence_llm,
            gateway=gateway,
            evidence_provider=provider,
        )

        task, spec, agent = _make_task(), _make_spec(), _make_agent()
        results = await pool.execute_all([(task, spec, agent)])
        assert len(results) == 1
        assert results[0].success

        finding = results[0].finding
        assert finding is not None
        ev_citation = next(
            (
                cit
                for claim in finding.claims
                for cit in claim.citations
                if cit.url == "https://example.com/survey"
            ),
            None,
        )
        assert ev_citation is not None, (
            "AgentPool must propagate evidence_provider into each ResearchAgent"
        )
