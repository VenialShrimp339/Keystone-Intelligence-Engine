"""Tests for Layer 4 process trajectory evaluation."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from keystone.evaluator.evaluator import (
    DEFAULT_LAYER3_WEIGHT,
    _blend_layer3_layer4,
)
from keystone.evaluator.layer4_trajectory import (
    Layer4Evaluator,
    ProcessContext,
    _compute_deterministic_flags,
    _compute_deterministic_metrics,
    _compute_process_quality_score,
    _extract_domain,
    _find_sibling_branch_ids,
    _merge_flags,
)
from keystone.events import (
    FindingSynthesized,
    ResearchComplete,
    ResearchStarted,
    SourceFound,
)
from keystone.models.agents import (
    AgentDefinition,
    AgentInstance,
    AgentRole,
    ResearchAgentType,
)
from keystone.models.citations import Citation, CitationManifest, SourceType
from keystone.models.evaluation import ProcessFlag
from keystone.models.tasks import (
    ModelTier,
    ResearchTask,
    TaskCategory,
    TaskType,
)

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


ENG = "ENG-001"
CID = "CLT-001"


def _task(
    task_id: str = "task_001",
    *,
    assigned_tools: list[str] | None = None,
    issue_tree_branch_id: str | None = "fin_1",
) -> ResearchTask:
    return ResearchTask(
        id=task_id,
        engagement_id=ENG,
        client_id=CID,
        category=TaskCategory.COMPETITIVE_LANDSCAPE,
        type=TaskType.CURRENT,
        target_decision_usefulness=4,
        description="Evaluate competitive landscape for autonomous-vehicle sensors.",
        acceptance_criteria=["Identify 5+ competitors"],
        deliverable_destination="Section 2",
        priority=1,
        anti_confirmatory_framing=(
            "Evaluate whether the market is consolidating or fragmenting, "
            "including evidence both for and against."
        ),
        assigned_tools=assigned_tools or ["web_search", "sec_filings", "news_api"],
        end_product="comparison table",
        dependencies=[],
        issue_tree_branch_id=issue_tree_branch_id,
    )


def _agent(agent_id: str = "agent_task_001_abc123") -> AgentInstance:
    return AgentInstance(
        agent_id=agent_id,
        engagement_id=ENG,
        client_id=CID,
        definition=AgentDefinition(
            name="competitive_analyst",
            description="Competitive landscape agent",
            role=AgentRole.RESEARCH,
            model=ModelTier.STANDARD,
            tools=["web_search", "sec_filings", "news_api"],
            research_type=ResearchAgentType.QUANTITATIVE,
        ),
        working_dir=f"/tmp/keystone/{ENG}/{agent_id}",
        task_ids=["task_001"],
    )


def _source_event(
    agent_id: str,
    url: str,
    source_type: str,
    quality_score: float = 0.75,
) -> SourceFound:
    return SourceFound(
        event_id=f"evt_{url[:12]}",
        engagement_id=ENG,
        client_id=CID,
        agent_id=agent_id,
        url=url,
        source_type=source_type,
        quality_score=quality_score,
    )


def _synthesis_event(agent_id: str, claim_count: int = 3) -> FindingSynthesized:
    return FindingSynthesized(
        event_id=f"evt_synth_{claim_count}",
        engagement_id=ENG,
        client_id=CID,
        agent_id=agent_id,
        claim_count=claim_count,
        confidence_range="0.50-0.80",
    )


def _complete_event(
    agent_id: str,
    sources: int,
    tokens: int = 500,
) -> ResearchComplete:
    return ResearchComplete(
        event_id=f"evt_complete_{agent_id}",
        engagement_id=ENG,
        client_id=CID,
        agent_id=agent_id,
        task_id="task_001",
        sources_consulted=sources,
        tokens_consumed=tokens,
        absence_count=2,
    )


def _manifest(*citations: Citation) -> CitationManifest:
    return CitationManifest(
        manifest_id="MAN-001",
        engagement_id=ENG,
        client_id=CID,
        citations=list(citations),
    )


def _citation(cid: str, quality: float = 0.80, domain: str = "example.com") -> Citation:
    return Citation(
        citation_id=cid,
        engagement_id=ENG,
        client_id=CID,
        url=f"https://{domain}/{cid}",
        title=f"Source {cid}",
        source_type=SourceType.REPORT,
        quality_score=quality,
        access_date=datetime.now(UTC),
    )


def _issue_tree_with_siblings() -> dict:
    """Issue tree where fin_1 has siblings fin_2, fin_3."""
    return {
        "root": {
            "id": "fin_root",
            "name": "Financial Root",
            "description": "Financial lens root",
            "children": [
                {"id": "fin_1", "name": "Unit economics", "description": "", "children": []},
                {"id": "fin_2", "name": "Capital structure", "description": "", "children": []},
                {"id": "fin_3", "name": "Pricing power", "description": "", "children": []},
            ],
        }
    }


def _good_process_events(agent_id: str) -> list:
    return [
        ResearchStarted(
            event_id="evt_start",
            engagement_id=ENG,
            client_id=CID,
            agent_id=agent_id,
            task_id="task_001",
        ),
        _source_event(agent_id, "https://sec.gov/filing1", "filing", 0.85),
        _source_event(agent_id, "https://bloomberg.com/article-1", "news", 0.80),
        _source_event(agent_id, "https://reuters.com/article-2", "news", 0.75),
        _source_event(agent_id, "https://arxiv.org/abs/xyz", "academic", 0.85),
        _source_event(agent_id, "https://www.sec.gov/filing2", "filing", 0.85),
        _synthesis_event(agent_id, claim_count=3),
        _source_event(agent_id, "https://wsj.com/article-3", "news", 0.78),
        _source_event(agent_id, "https://bis.gov/report", "government", 0.9),
        _synthesis_event(agent_id, claim_count=7),
        _source_event(agent_id, "https://imf.org/wp/2025/abc", "academic", 0.85),
        _synthesis_event(agent_id, claim_count=10),
        _complete_event(agent_id, sources=9, tokens=4200),
    ]


# ---------------------------------------------------------------------------
# Helper function tests (no LLM)
# ---------------------------------------------------------------------------


class TestExtractDomain:
    def test_strips_scheme_and_www(self) -> None:
        assert _extract_domain("https://www.sec.gov/filing1") == "sec.gov"

    def test_tool_scheme(self) -> None:
        assert _extract_domain("tool://web_search/round_1") == "web_search"

    def test_empty_url(self) -> None:
        assert _extract_domain("") == ""


class TestFindSiblingBranchIds:
    def test_finds_siblings_for_known_branch(self) -> None:
        tree = _issue_tree_with_siblings()
        siblings = _find_sibling_branch_ids(tree, "fin_1")
        assert set(siblings) == {"fin_1", "fin_2", "fin_3"}

    def test_returns_empty_when_branch_missing(self) -> None:
        tree = _issue_tree_with_siblings()
        assert _find_sibling_branch_ids(tree, "mkt_7") == []


class TestBlendL3L4:
    def test_high_l3_low_l4_drags_composite(self) -> None:
        # Geometric mean should punish disparity more than arithmetic mean.
        composite = _blend_layer3_layer4(90.0, 40.0, layer3_weight=0.8)
        assert composite < 90.0
        # Below arithmetic mean (0.8*90 + 0.2*40 = 82)
        assert composite < 82.0
        # Well above floor
        assert composite > 50.0

    def test_equal_scores_return_that_score(self) -> None:
        assert _blend_layer3_layer4(70.0, 70.0, layer3_weight=0.8) == pytest.approx(70.0, abs=0.01)

    def test_zero_l4_drags_composite_far_below_l3(self) -> None:
        # Score of 0 floored at epsilon so composite is very low but finite,
        # and well below the L3 score alone.
        composite = _blend_layer3_layer4(80.0, 0.0, layer3_weight=0.8)
        assert composite > 0.0
        assert composite < 20.0  # arithmetic mean would be 64; geometric pins this low

    def test_default_weight_matches_constant(self) -> None:
        assert pytest.approx(0.8) == DEFAULT_LAYER3_WEIGHT


# ---------------------------------------------------------------------------
# Deterministic metric computation
# ---------------------------------------------------------------------------


class TestComputeDeterministicMetrics:
    def test_counts_sources_domains_rounds_and_tools(self) -> None:
        task = _task()
        agent = _agent()
        events = _good_process_events(agent.agent_id)
        context = ProcessContext(agent_id=agent.agent_id, task=task, agent=agent, events=events)
        manifest = _manifest(
            _citation("CIT-001", quality=0.90, domain="sec.gov"),
            _citation("CIT-002", quality=0.80, domain="bloomberg.com"),
        )

        metrics = _compute_deterministic_metrics(context, manifest)

        assert metrics["source_count"] == 9  # ResearchComplete authoritative
        # sec.gov + www.sec.gov normalize to the same domain -> 7 unique
        assert metrics["unique_domains"] == 7
        # source_type set includes: filing, news, academic, government
        assert metrics["source_type_diversity"] >= 4
        assert metrics["round_count"] == 3  # Three FindingSynthesized events
        assert set(metrics["assigned_tools"]) == {"web_search", "sec_filings", "news_api"}
        assert metrics["citation_quality"]["HIGH"] == 2
        assert metrics["citation_quality"]["MEDIUM"] == 0
        assert metrics["citation_quality"]["LOW"] == 0

    def test_tool_utilization_reflects_exercised_tools(self) -> None:
        task = _task(assigned_tools=["web_search", "sec_filings", "news_api"])
        agent = _agent()
        # Only web_search is used (via tool:// scheme, shallow mode)
        events = [
            _source_event(agent.agent_id, "tool://web_search/round_1", "web_search"),
            _synthesis_event(agent.agent_id, 2),
            _complete_event(agent.agent_id, sources=1),
        ]
        context = ProcessContext(agent_id=agent.agent_id, task=task, agent=agent, events=events)
        metrics = _compute_deterministic_metrics(context, _manifest())
        assert metrics["tool_utilization"] == pytest.approx(1 / 3, abs=0.01)
        assert metrics["tools_used"] == ["web_search"]

    def test_source_count_falls_back_to_events_when_no_complete(self) -> None:
        task = _task()
        agent = _agent()
        events = [
            _source_event(agent.agent_id, "https://a.com", "news"),
            _source_event(agent.agent_id, "https://b.com", "news"),
        ]
        context = ProcessContext(agent_id=agent.agent_id, task=task, agent=agent, events=events)
        metrics = _compute_deterministic_metrics(context, _manifest())
        assert metrics["source_count"] == 2

    def test_branch_coverage_records_siblings(self) -> None:
        task = _task(issue_tree_branch_id="fin_1")
        agent = _agent()
        context = ProcessContext(
            agent_id=agent.agent_id,
            task=task,
            agent=agent,
            events=_good_process_events(agent.agent_id),
            issue_tree=_issue_tree_with_siblings(),
        )
        metrics = _compute_deterministic_metrics(context, _manifest())
        assert metrics["branches_covered"] == ["fin_1"]
        assert set(metrics["branches_missed"]) == {"fin_2", "fin_3"}


# ---------------------------------------------------------------------------
# Deterministic flag computation
# ---------------------------------------------------------------------------


class TestComputeDeterministicFlags:
    def test_good_process_raises_no_flags(self) -> None:
        task = _task()
        agent = _agent()
        context = ProcessContext(
            agent_id=agent.agent_id,
            task=task,
            agent=agent,
            events=_good_process_events(agent.agent_id),
            issue_tree=_issue_tree_with_siblings(),
        )
        manifest = _manifest(
            _citation("CIT-001", quality=0.90, domain="sec.gov"),
            _citation("CIT-002", quality=0.85, domain="bloomberg.com"),
        )
        metrics = _compute_deterministic_metrics(context, manifest)
        flags = _compute_deterministic_flags(metrics, context)
        assert ProcessFlag.SINGLE_SOURCE_TYPE not in flags
        assert ProcessFlag.SINGLE_DOMAIN not in flags
        assert ProcessFlag.NO_MULTI_ROUND not in flags
        assert ProcessFlag.LOW_SOURCE_COUNT not in flags
        assert ProcessFlag.NO_HIGH_CONFIDENCE_CITATIONS not in flags
        assert ProcessFlag.COVERAGE_GAP not in flags

    def test_single_source_type_flagged(self) -> None:
        task = _task()
        agent = _agent()
        events = [_source_event(agent.agent_id, f"https://a{i}.com", "news") for i in range(6)] + [
            _synthesis_event(agent.agent_id, 3),
            _complete_event(agent.agent_id, sources=6),
        ]
        context = ProcessContext(
            agent_id=agent.agent_id,
            task=task,
            agent=agent,
            events=events,
            issue_tree=_issue_tree_with_siblings(),
        )
        metrics = _compute_deterministic_metrics(context, _manifest(_citation("CIT-001")))
        flags = _compute_deterministic_flags(metrics, context)
        assert ProcessFlag.SINGLE_SOURCE_TYPE in flags

    def test_no_multi_round_flagged(self) -> None:
        task = _task()
        agent = _agent()
        events = [
            _source_event(agent.agent_id, "https://a.com", "news"),
            _source_event(agent.agent_id, "https://b.com", "news"),
            _source_event(agent.agent_id, "https://c.com", "academic"),
            _synthesis_event(agent.agent_id, 3),
            _complete_event(agent.agent_id, sources=3),
        ]
        context = ProcessContext(
            agent_id=agent.agent_id,
            task=task,
            agent=agent,
            events=events,
            issue_tree=_issue_tree_with_siblings(),
        )
        metrics = _compute_deterministic_metrics(context, _manifest(_citation("CIT-001")))
        flags = _compute_deterministic_flags(metrics, context)
        assert ProcessFlag.NO_MULTI_ROUND in flags

    def test_low_tool_diversity_flagged(self) -> None:
        # 3 tools assigned, agent only uses 1 (utilization 0.33 -> flag)
        task = _task(assigned_tools=["web_search", "sec_filings", "news_api"])
        agent = _agent()
        events = [
            _source_event(agent.agent_id, "tool://web_search/round_1", "web_search"),
            _source_event(agent.agent_id, "tool://web_search/round_2", "web_search"),
            _synthesis_event(agent.agent_id, 3),
            _synthesis_event(agent.agent_id, 5),
            _complete_event(agent.agent_id, sources=2),
        ]
        context = ProcessContext(
            agent_id=agent.agent_id,
            task=task,
            agent=agent,
            events=events,
            issue_tree=_issue_tree_with_siblings(),
        )
        metrics = _compute_deterministic_metrics(context, _manifest())
        flags = _compute_deterministic_flags(metrics, context)
        assert ProcessFlag.LOW_TOOL_DIVERSITY in flags

    def test_single_domain_flagged(self) -> None:
        task = _task()
        agent = _agent()
        events = [
            _source_event(agent.agent_id, "https://example.com/a", "news"),
            _source_event(agent.agent_id, "https://example.com/b", "news"),
            _source_event(agent.agent_id, "https://example.com/c", "news"),
            _synthesis_event(agent.agent_id, 3),
            _synthesis_event(agent.agent_id, 5),
            _complete_event(agent.agent_id, sources=3),
        ]
        context = ProcessContext(
            agent_id=agent.agent_id,
            task=task,
            agent=agent,
            events=events,
            issue_tree=_issue_tree_with_siblings(),
        )
        metrics = _compute_deterministic_metrics(context, _manifest(_citation("CIT-001")))
        flags = _compute_deterministic_flags(metrics, context)
        assert ProcessFlag.SINGLE_DOMAIN in flags

    def test_coverage_gap_when_no_branch(self) -> None:
        task = _task(issue_tree_branch_id=None)
        agent = _agent()
        events = _good_process_events(agent.agent_id)
        context = ProcessContext(
            agent_id=agent.agent_id,
            task=task,
            agent=agent,
            events=events,
            issue_tree=None,
        )
        metrics = _compute_deterministic_metrics(context, _manifest(_citation("CIT-001")))
        flags = _compute_deterministic_flags(metrics, context)
        assert ProcessFlag.COVERAGE_GAP in flags

    def test_no_high_confidence_citations_flagged(self) -> None:
        task = _task()
        agent = _agent()
        context = ProcessContext(
            agent_id=agent.agent_id,
            task=task,
            agent=agent,
            events=_good_process_events(agent.agent_id),
            issue_tree=_issue_tree_with_siblings(),
        )
        manifest = _manifest(
            _citation("CIT-001", quality=0.55),
            _citation("CIT-002", quality=0.60),
        )
        metrics = _compute_deterministic_metrics(context, manifest)
        flags = _compute_deterministic_flags(metrics, context)
        assert ProcessFlag.NO_HIGH_CONFIDENCE_CITATIONS in flags


# ---------------------------------------------------------------------------
# Score blending
# ---------------------------------------------------------------------------


class TestProcessQualityScore:
    def test_no_flags_scores_around_qualitative(self) -> None:
        score = _compute_process_quality_score(80.0, [])
        assert score == pytest.approx(90.0, abs=0.1)

    def test_critical_flag_reduces_score(self) -> None:
        clean = _compute_process_quality_score(80.0, [])
        flagged = _compute_process_quality_score(80.0, [ProcessFlag.SINGLE_DOMAIN])
        assert flagged < clean
        assert clean - flagged == pytest.approx(7.5, abs=0.1)  # 15/2 critical penalty

    def test_warning_flag_reduces_score_less(self) -> None:
        critical = _compute_process_quality_score(80.0, [ProcessFlag.LOW_TOOL_DIVERSITY])
        warning = _compute_process_quality_score(80.0, [ProcessFlag.NO_MULTI_ROUND])
        assert warning > critical

    def test_score_floored_at_zero(self) -> None:
        many_flags = [
            ProcessFlag.SINGLE_DOMAIN,
            ProcessFlag.LOW_TOOL_DIVERSITY,
            ProcessFlag.NO_HIGH_CONFIDENCE_CITATIONS,
            ProcessFlag.NO_MULTI_ROUND,
            ProcessFlag.SINGLE_SOURCE_TYPE,
            ProcessFlag.LOW_SOURCE_COUNT,
            ProcessFlag.COVERAGE_GAP,
        ]
        score = _compute_process_quality_score(10.0, many_flags)
        assert 0.0 <= score <= 50.0


class TestMergeFlags:
    def test_preserves_order_and_dedups(self) -> None:
        det = [ProcessFlag.SINGLE_DOMAIN, ProcessFlag.NO_MULTI_ROUND]
        llm = [ProcessFlag.NO_MULTI_ROUND, ProcessFlag.NARROW_INQUIRY]
        merged = _merge_flags(det, llm)
        assert merged == [
            ProcessFlag.SINGLE_DOMAIN,
            ProcessFlag.NO_MULTI_ROUND,
            ProcessFlag.NARROW_INQUIRY,
        ]


# ---------------------------------------------------------------------------
# Full Layer4Evaluator
# ---------------------------------------------------------------------------


def _mock_llm_ok(score: int = 75, flags: list[str] | None = None):
    payload = {
        "qualitative_score": score,
        "rationale": "The agent consulted diverse primary sources and iterated.",
        "skepticism_assessment": "Anti-confirmatory framing was honored.",
        "missed_inquiries": [],
        "additional_flags": flags or [],
    }

    async def llm(prompt: str) -> str:
        return json.dumps(payload)

    return llm


def _mock_llm_broken():
    async def llm(prompt: str) -> str:
        return "this is not JSON at all"

    return llm


class TestLayer4EvaluatorFull:
    @pytest.mark.asyncio
    async def test_good_process_scores_high_no_flags(self) -> None:
        agent = _agent()
        task = _task()
        context = ProcessContext(
            agent_id=agent.agent_id,
            task=task,
            agent=agent,
            events=_good_process_events(agent.agent_id),
            issue_tree=_issue_tree_with_siblings(),
        )
        manifest = _manifest(
            _citation("CIT-001", quality=0.90, domain="sec.gov"),
            _citation("CIT-002", quality=0.85, domain="bloomberg.com"),
        )
        evaluator = Layer4Evaluator(llm=_mock_llm_ok(score=85))
        result = await evaluator.evaluate(context, manifest)

        assert result.process_quality_score >= 80
        assert result.qualitative_score == 85
        assert result.round_count == 3
        assert result.source_count == 9
        assert ProcessFlag.SINGLE_SOURCE_TYPE.value not in result.process_flags
        assert ProcessFlag.SINGLE_DOMAIN.value not in result.process_flags

    @pytest.mark.asyncio
    async def test_narrow_research_flags_and_lowers_score(self) -> None:
        """Single tool, single domain, single round → multiple flags, lower score."""
        agent = _agent()
        task = _task(assigned_tools=["web_search", "sec_filings", "news_api"])
        events = [
            _source_event(agent.agent_id, "tool://web_search/round_1", "web_search"),
            _source_event(agent.agent_id, "tool://web_search/round_1b", "web_search"),
            _synthesis_event(agent.agent_id, 3),
            _complete_event(agent.agent_id, sources=2),
        ]
        context = ProcessContext(
            agent_id=agent.agent_id,
            task=task,
            agent=agent,
            events=events,
            issue_tree=_issue_tree_with_siblings(),
        )
        manifest = _manifest(_citation("CIT-001", quality=0.60))
        evaluator = Layer4Evaluator(llm=_mock_llm_ok(score=45))
        result = await evaluator.evaluate(context, manifest)

        assert ProcessFlag.NO_MULTI_ROUND.value in result.process_flags
        assert ProcessFlag.LOW_TOOL_DIVERSITY.value in result.process_flags
        assert ProcessFlag.SINGLE_SOURCE_TYPE.value in result.process_flags
        assert ProcessFlag.LOW_SOURCE_COUNT.value in result.process_flags
        assert ProcessFlag.NO_HIGH_CONFIDENCE_CITATIONS.value in result.process_flags
        assert result.process_quality_score < 60

    @pytest.mark.asyncio
    async def test_llm_failure_falls_back_to_deterministic(self) -> None:
        agent = _agent()
        task = _task()
        context = ProcessContext(
            agent_id=agent.agent_id,
            task=task,
            agent=agent,
            events=_good_process_events(agent.agent_id),
            issue_tree=_issue_tree_with_siblings(),
        )
        manifest = _manifest(_citation("CIT-001", quality=0.90))
        evaluator = Layer4Evaluator(llm=_mock_llm_broken())
        result = await evaluator.evaluate(context, manifest)

        # LLM couldn't score; qualitative_score defaults to 50.
        assert result.qualitative_score == 50.0
        assert (
            "unparseable" in result.rationale.lower() or "unavailable" in result.rationale.lower()
        )

    @pytest.mark.asyncio
    async def test_llm_additional_flags_merged_in(self) -> None:
        agent = _agent()
        task = _task()
        context = ProcessContext(
            agent_id=agent.agent_id,
            task=task,
            agent=agent,
            events=_good_process_events(agent.agent_id),
            issue_tree=_issue_tree_with_siblings(),
        )
        manifest = _manifest(_citation("CIT-001", quality=0.90))
        llm = _mock_llm_ok(score=70, flags=["narrow_inquiry"])
        evaluator = Layer4Evaluator(llm=llm)
        result = await evaluator.evaluate(context, manifest)
        assert ProcessFlag.NARROW_INQUIRY.value in result.process_flags

    @pytest.mark.asyncio
    async def test_issue_tree_missed_branches_surfaced(self) -> None:
        agent = _agent()
        task = _task(issue_tree_branch_id="fin_1")
        context = ProcessContext(
            agent_id=agent.agent_id,
            task=task,
            agent=agent,
            events=_good_process_events(agent.agent_id),
            issue_tree=_issue_tree_with_siblings(),
        )
        manifest = _manifest(_citation("CIT-001", quality=0.90))
        evaluator = Layer4Evaluator(llm=_mock_llm_ok(score=75))
        result = await evaluator.evaluate(context, manifest)
        assert result.issue_tree_branches_covered == ["fin_1"]
        assert set(result.issue_tree_branches_missed) == {"fin_2", "fin_3"}

    @pytest.mark.asyncio
    async def test_unknown_llm_flag_is_ignored_silently(self) -> None:
        agent = _agent()
        task = _task()
        context = ProcessContext(
            agent_id=agent.agent_id,
            task=task,
            agent=agent,
            events=_good_process_events(agent.agent_id),
            issue_tree=_issue_tree_with_siblings(),
        )
        manifest = _manifest(_citation("CIT-001", quality=0.90))
        llm = _mock_llm_ok(score=70, flags=["this_flag_does_not_exist"])
        evaluator = Layer4Evaluator(llm=llm)
        result = await evaluator.evaluate(context, manifest)
        # Unknown flag dropped; result still usable
        assert "this_flag_does_not_exist" not in result.process_flags
        assert result.qualitative_score == 70
