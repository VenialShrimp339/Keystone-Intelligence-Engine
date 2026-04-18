"""Unit tests for Pipeline-L2 ContentStructurer.

Covers: framework selection, outline construction, provenance
preservation, per-task section text, sprint-contract negotiation,
event emission, filter_outline_by_passed_tasks.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from keystone.contracts import ContentStructuringContract
from keystone.events import (
    OutlineGenerated,
    SectionDrafted,
    SprintContractProposed,
)
from keystone.models.citations import Citation, ConfidenceTier, SourceType
from keystone.models.confidence import (
    ConfidenceMap,
    ContestedClaim,
    HighConfidenceClaim,
    InsufficientEvidenceClaim,
    ModerateConfidenceClaim,
    WeakConfidenceClaim,
)
from keystone.models.evaluation import SprintContract
from keystone.models.research import (
    EngagementSpec,
    EngagementType,
    FindingClaim,
    ResearchQuestion,
    ResearchSpec,
    StructuredFinding,
    ValidationReport,
)
from keystone.models.structuring import (
    AnalyticalFramework,
    FrameworkHint,
    OutlineItemType,
    OutlineSectionType,
)
from keystone.models.tasks import (
    ResearchTask,
    TaskCategory,
    TaskDecomposition,
    TaskType,
)
from keystone.structuring import (
    ContentStructurer,
    filter_outline_by_passed_tasks,
    frameworks_for_engagement,
    primary_framework,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _task(task_id: str, branch_id: str = "leaf_1") -> ResearchTask:
    return ResearchTask(
        id=task_id,
        engagement_id="eng_test",
        client_id="client_test",
        category=TaskCategory.MARKET_SIZING,
        type=TaskType.ESTIMATIVE,
        target_decision_usefulness=4,
        description=f"Investigate {branch_id}",
        acceptance_criteria=["Return evidence-backed claims."],
        deliverable_destination=f"Section {branch_id}",
        priority=1,
        anti_confirmatory_framing=(f"Evaluate {branch_id} including counterevidence."),
        assigned_tools=["exa_search", "brave_search", "edgar_filings"],
        end_product="Structured findings",
        issue_tree_branch_id=branch_id,
    )


def _spec(
    tasks: list[ResearchTask] | None = None,
    engagement_type: EngagementType = EngagementType.SIZING,
) -> EngagementSpec:
    tasks = tasks or [_task("task_001", "leaf_1"), _task("task_002", "leaf_2")]
    return EngagementSpec(
        research_spec=ResearchSpec(
            engagement_id="eng_test",
            client_id="client_test",
            title="L2 Unit Test",
            created_at=datetime.now(UTC),
            specification_version=1,
            decision_context="Test the L2 outline surface.",
            surprising_finding="The outline drops provenance.",
            questions=[ResearchQuestion(question="What changed?", is_primary=True)],
            output_format="markdown",
            engagement_type=engagement_type,
        ),
        task_decomposition=TaskDecomposition(
            project="L2 Unit",
            engagement_id="eng_test",
            client_id="client_test",
            research_md_path="/tmp/RESEARCH.md",
            specification_version=1,
            decomposition_rationale="One task per branch.",
            tasks=tasks,
        ),
        validation_report=ValidationReport(
            intent_clear=True,
            scope_valid=True,
            within_frontier=True,
            quality_threshold_met=True,
        ),
        issue_tree={
            "root": {
                "id": "root",
                "name": "Root",
                "children": [
                    {"id": "leaf_1", "name": "Branch One", "children": []},
                    {"id": "leaf_2", "name": "Branch Two", "children": []},
                ],
            }
        },
    )


def _citation(citation_id: str) -> Citation:
    return Citation(
        citation_id=citation_id,
        engagement_id="eng_test",
        client_id="client_test",
        url=f"https://example.com/{citation_id}",
        title=f"Source {citation_id}",
        access_date=datetime.now(UTC),
        source_type=SourceType.REPORT,
        quality_score=0.8,
    )


def _finding(
    task_id: str,
    branch_text: str,
    citation_id: str,
    confidence: float = 0.84,
    tier: ConfidenceTier = ConfidenceTier.HIGH,
) -> StructuredFinding:
    return StructuredFinding(
        task_id=task_id,
        agent_id=f"agent_{task_id}",
        engagement_id="eng_test",
        client_id="client_test",
        agent_type="quantitative",
        claims=[
            FindingClaim(
                text=branch_text,
                evidence=f"Evidence for {branch_text}",
                citations=[_citation(citation_id)],
                citation_ids=[citation_id],
                confidence=confidence,
                confidence_tier=tier,
                claim_id=f"claim_{task_id}",
                caveats=["Caveat A"],
            )
        ],
        absence_report=[f"No additional evidence for {task_id}"],
        sources_consulted=3,
        tokens_consumed=300,
    )


def _confidence_map(include_all_tiers: bool = False) -> ConfidenceMap:
    high = HighConfidenceClaim(
        claim="Branch One is covered",
        methodological_agreement="3/3",
        sources=2,
        corroboration_count=2,
        robustness="Stable",
        curmudgeon_challenge="Could still narrow",
        aggregated_claim_id="agg_high_001",
        task_ids=["task_001"],
    )
    if not include_all_tiers:
        return ConfidenceMap(
            engagement_id="eng_test",
            client_id="client_test",
            high_confidence_above_80pct=[high],
            provenance_index={"agg_high_001": ["task_001"]},
            gap_provenance={"Gap in branch two": ["task_002"]},
            gaps_identified=["Gap in branch two"],
        )

    return ConfidenceMap(
        engagement_id="eng_test",
        client_id="client_test",
        high_confidence_above_80pct=[high],
        moderate_confidence_60_80pct=[
            ModerateConfidenceClaim(
                claim="Moderate claim",
                methodological_agreement="2/3",
                dissent="Analyst X disagreed on framing",
                sources=2,
                sensitivity="Flips if assumption B changes",
                aggregated_claim_id="agg_mod_001",
                task_ids=["task_001"],
            )
        ],
        weak_confidence_50_60pct=[
            WeakConfidenceClaim(
                claim="Weak claim",
                methodological_agreement="1/3",
                key_issue="Limited sources",
                sources=1,
                recommendation="Frame as directional, not estimate",
                aggregated_claim_id="agg_weak_001",
                task_ids=["task_002"],
            )
        ],
        contested_below_50pct=[
            ContestedClaim(
                claim="Contested claim",
                methodological_agreement="0/3",
                key_disagreement="Framework choice",
                sources=2,
                steelmanned_opposing_view="Actually the opposite is true",
                aggregated_claim_id="agg_cont_001",
                task_ids=["task_002"],
            )
        ],
        insufficient_evidence=[
            InsufficientEvidenceClaim(
                claim="Sparse claim",
                reason="No sources found",
                priority="high",
                aggregated_claim_id="agg_insuf_001",
                task_ids=["task_002"],
            )
        ],
        gaps_identified=["Branch-two gap"],
        gap_provenance={"Branch-two gap": ["task_002"]},
        provenance_index={
            "agg_high_001": ["task_001"],
            "agg_mod_001": ["task_001"],
            "agg_weak_001": ["task_002"],
            "agg_cont_001": ["task_002"],
            "agg_insuf_001": ["task_002"],
        },
    )


def _mock_contract_generator(
    contract_factory=None,
) -> MagicMock:
    """Mock SprintContractGenerator that returns per-task contracts."""
    gen = MagicMock()

    async def _generate(task: ResearchTask, spec: EngagementSpec) -> SprintContract:
        if contract_factory is not None:
            return contract_factory(task, spec)
        return SprintContract(
            section_id=f"section_{task.id}",
            engagement_id=task.engagement_id,
            client_id=task.client_id,
            task_id=task.id,
            section_title=task.deliverable_destination,
            acceptance_criteria=["Mock criterion A", "Mock criterion B"],
        )

    gen.generate = AsyncMock(side_effect=_generate)
    return gen


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


class TestProtocolConformance:
    def test_content_structurer_isinstance(self) -> None:
        structurer = ContentStructurer()
        assert isinstance(structurer, ContentStructuringContract)


# ---------------------------------------------------------------------------
# Framework selection
# ---------------------------------------------------------------------------


class TestFrameworkSelection:
    def test_sizing_selects_estimation(self) -> None:
        assert primary_framework(EngagementType.SIZING) == AnalyticalFramework.ESTIMATION

    def test_diagnostic_selects_root_cause(self) -> None:
        assert primary_framework(EngagementType.DIAGNOSTIC) == AnalyticalFramework.ROOT_CAUSE

    def test_evaluative_selects_porters_then_value_chain(self) -> None:
        hints = frameworks_for_engagement(EngagementType.EVALUATIVE)
        frameworks = [h.framework for h in hints]
        assert frameworks == [
            AnalyticalFramework.PORTERS_FIVE_FORCES,
            AnalyticalFramework.VALUE_CHAIN,
        ]
        assert hints[0].mandatory is True
        assert hints[1].mandatory is False

    def test_exploratory_selects_landscape(self) -> None:
        assert (
            primary_framework(EngagementType.EXPLORATORY) == AnalyticalFramework.LANDSCAPE_MAPPING
        )

    def test_strategic_selects_scenario_plus_swot(self) -> None:
        hints = frameworks_for_engagement(EngagementType.STRATEGIC)
        assert [h.framework for h in hints] == [
            AnalyticalFramework.SCENARIO_PLANNING,
            AnalyticalFramework.SWOT,
        ]

    def test_override_replaces_default_mapping(self) -> None:
        override = [
            FrameworkHint(
                framework=AnalyticalFramework.SWOT,
                rationale="Custom choice for a novel engagement.",
                mandatory=True,
            ),
        ]
        assert frameworks_for_engagement(EngagementType.SIZING, override=override) == override
        assert (
            primary_framework(EngagementType.SIZING, override=override) == AnalyticalFramework.SWOT
        )

    def test_empty_override_yields_no_frameworks(self) -> None:
        # An explicit empty list is a caller decision, not a fallback signal.
        assert frameworks_for_engagement(EngagementType.SIZING, override=[]) == []
        assert primary_framework(EngagementType.SIZING, override=[]) is None

    def test_override_primary_prefers_mandatory_then_first(self) -> None:
        override = [
            FrameworkHint(
                framework=AnalyticalFramework.VALUE_CHAIN,
                rationale="Augmenting.",
                mandatory=False,
            ),
            FrameworkHint(
                framework=AnalyticalFramework.PORTERS_FIVE_FORCES,
                rationale="Primary.",
                mandatory=True,
            ),
        ]
        assert (
            primary_framework(EngagementType.SIZING, override=override)
            == AnalyticalFramework.PORTERS_FIVE_FORCES
        )

    @pytest.mark.asyncio
    async def test_structurer_threads_frameworks_override_into_outline(self) -> None:
        override = [
            FrameworkHint(
                framework=AnalyticalFramework.SWOT,
                rationale="Novel engagement; SWOT chosen by Spec Engine.",
                mandatory=True,
            ),
        ]
        spec = _spec()  # engagement_type=SIZING → default would be ESTIMATION
        structurer = ContentStructurer(
            sprint_contract_generator=_mock_contract_generator(),
            frameworks_override=override,
        )
        async for _event in structurer.structure(
            _confidence_map(),
            [_finding("task_001", "Branch one claim", "CAN-001")],
            spec,
            spec.task_decomposition.tasks,
            "eng_test",
            "client_test",
        ):
            pass

        outline = await structurer.get_outline()
        framework_section = next(
            section
            for section in outline.sections
            if section.section_type == OutlineSectionType.FRAMEWORK_ANALYSIS
        )
        assert framework_section.framework == AnalyticalFramework.SWOT
        assert [hint.framework for hint in outline.frameworks] == [AnalyticalFramework.SWOT]


# ---------------------------------------------------------------------------
# Outline construction
# ---------------------------------------------------------------------------


class TestOutlineConstruction:
    @pytest.mark.asyncio
    async def test_outline_groups_claims_by_issue_tree_branch(self) -> None:
        spec = _spec()
        findings = [
            _finding("task_001", "Branch one claim", "CAN-001"),
            _finding("task_002", "Branch two claim", "CAN-002"),
        ]

        structurer = ContentStructurer(sprint_contract_generator=_mock_contract_generator())
        async for _event in structurer.structure(
            _confidence_map(),
            findings,
            spec,
            spec.task_decomposition.tasks,
            "eng_test",
            "client_test",
        ):
            pass

        outline = await structurer.get_outline()
        branch_sections = {
            section.issue_tree_branch_id: section
            for section in outline.sections
            if section.section_type == OutlineSectionType.BRANCH
        }
        assert set(branch_sections) == {"leaf_1", "leaf_2"}
        assert branch_sections["leaf_1"].title == "Branch One"
        assert branch_sections["leaf_2"].title == "Branch Two"
        assert branch_sections["leaf_1"].items[0].text == "Branch one claim"
        assert branch_sections["leaf_2"].items[0].text == "Branch two claim"

    @pytest.mark.asyncio
    async def test_outline_preserves_claim_and_task_provenance(self) -> None:
        spec = _spec()
        structurer = ContentStructurer(sprint_contract_generator=_mock_contract_generator())
        async for _event in structurer.structure(
            _confidence_map(),
            [_finding("task_001", "Branch one claim", "CAN-001")],
            spec,
            spec.task_decomposition.tasks,
            "eng_test",
            "client_test",
        ):
            pass

        outline = await structurer.get_outline()
        executive = next(
            section for section in outline.sections if section.section_id == "executive_summary"
        )
        assert executive.items[0].task_ids == ["task_001"]
        assert executive.items[0].issue_tree_branch_id == "leaf_1"
        assert executive.claim_ids == ["agg_high_001"]

    @pytest.mark.asyncio
    async def test_outline_lists_uncovered_branches(self) -> None:
        spec = _spec()
        structurer = ContentStructurer(sprint_contract_generator=_mock_contract_generator())
        async for _event in structurer.structure(
            _confidence_map(),
            [_finding("task_001", "Branch one claim", "CAN-001")],
            spec,
            spec.task_decomposition.tasks,
            "eng_test",
            "client_test",
        ):
            pass

        outline = await structurer.get_outline()
        assert outline.uncovered_branch_ids == ["leaf_2"]

    @pytest.mark.asyncio
    async def test_outline_includes_framework_analysis_section(self) -> None:
        spec = _spec()
        structurer = ContentStructurer(sprint_contract_generator=_mock_contract_generator())
        async for _event in structurer.structure(
            _confidence_map(),
            [_finding("task_001", "Branch one claim", "CAN-001")],
            spec,
            spec.task_decomposition.tasks,
            "eng_test",
            "client_test",
        ):
            pass

        outline = await structurer.get_outline()
        frameworks_section = next(
            section
            for section in outline.sections
            if section.section_type == OutlineSectionType.FRAMEWORK_ANALYSIS
        )
        assert frameworks_section.framework == AnalyticalFramework.ESTIMATION
        assert frameworks_section.items[0].item_type == OutlineItemType.FRAMEWORK_NOTE

    @pytest.mark.asyncio
    async def test_outline_renders_all_confidence_tiers(self) -> None:
        spec = _spec()
        structurer = ContentStructurer(sprint_contract_generator=_mock_contract_generator())
        async for _event in structurer.structure(
            _confidence_map(include_all_tiers=True),
            [
                _finding("task_001", "Branch one claim", "CAN-001"),
                _finding("task_002", "Branch two claim", "CAN-002"),
            ],
            spec,
            spec.task_decomposition.tasks,
            "eng_test",
            "client_test",
        ):
            pass

        outline = await structurer.get_outline()
        section_types = {section.section_type for section in outline.sections}
        assert OutlineSectionType.EXECUTIVE_SUMMARY in section_types
        assert OutlineSectionType.FRAMEWORK_ANALYSIS in section_types
        assert OutlineSectionType.BRANCH in section_types
        assert OutlineSectionType.MODERATE in section_types
        assert OutlineSectionType.WEAK in section_types
        assert OutlineSectionType.CONTESTED in section_types
        assert OutlineSectionType.GAPS in section_types
        assert OutlineSectionType.INSUFFICIENT in section_types
        assert OutlineSectionType.ABSENCE in section_types

    @pytest.mark.asyncio
    async def test_empty_findings_and_confidence_map_produces_minimal_outline(
        self,
    ) -> None:
        spec = _spec(tasks=[_task("task_001", "leaf_1")])
        empty_cm = ConfidenceMap(engagement_id="eng_test", client_id="client_test")
        structurer = ContentStructurer(sprint_contract_generator=_mock_contract_generator())

        events = []
        async for event in structurer.structure(
            empty_cm,
            [],
            spec,
            spec.task_decomposition.tasks,
            "eng_test",
            "client_test",
        ):
            events.append(event)

        outline = await structurer.get_outline()
        # No claims or findings; still a framework-analysis section and the
        # terminal OutlineGenerated event fire.
        assert outline.engagement_id == "eng_test"
        assert outline.engagement_type == "sizing"
        assert outline.rendered_task_ids == []
        assert any(
            section.section_type == OutlineSectionType.FRAMEWORK_ANALYSIS
            for section in outline.sections
        )
        assert any(isinstance(e, OutlineGenerated) for e in events)


# ---------------------------------------------------------------------------
# Per-task section text
# ---------------------------------------------------------------------------


class TestPerTaskSectionText:
    @pytest.mark.asyncio
    async def test_section_text_includes_lede_and_evidence(self) -> None:
        spec = _spec(tasks=[_task("task_001", "leaf_1")])
        finding = _finding("task_001", "Branch one claim", "CAN-001")
        structurer = ContentStructurer(sprint_contract_generator=_mock_contract_generator())
        async for _event in structurer.structure(
            _confidence_map(),
            [finding],
            spec,
            spec.task_decomposition.tasks,
            "eng_test",
            "client_test",
        ):
            pass

        text = await structurer.get_task_section_text("task_001")
        assert text.startswith("# Section leaf_1")
        assert "Framework:" in text
        assert "Estimation" in text
        assert "## Lede" in text
        assert "Branch one claim" in text
        assert "## Evidence chain" in text
        assert "CAN-001" in text
        assert "Caveat A" in text

    @pytest.mark.asyncio
    async def test_section_text_surfaces_absence_report_and_gaps(self) -> None:
        spec = _spec(tasks=[_task("task_001", "leaf_1")])
        finding = _finding("task_001", "Branch one claim", "CAN-001").model_copy(
            update={"gaps": ["Per-task gap item"]}
        )
        structurer = ContentStructurer(sprint_contract_generator=_mock_contract_generator())
        async for _event in structurer.structure(
            _confidence_map(),
            [finding],
            spec,
            spec.task_decomposition.tasks,
            "eng_test",
            "client_test",
        ):
            pass

        text = await structurer.get_task_section_text("task_001")
        assert "## Absence report" in text
        assert "No additional evidence for task_001" in text
        assert "Per-task gap item" in text
        assert "## Acceptance criteria" in text

    @pytest.mark.asyncio
    async def test_section_text_cross_references_confidence_map_tiers(self) -> None:
        spec = _spec(tasks=[_task("task_001", "leaf_1")])
        finding = _finding("task_001", "Moderate claim", "CAN-001", confidence=0.7)
        cm = _confidence_map(include_all_tiers=True)
        structurer = ContentStructurer(sprint_contract_generator=_mock_contract_generator())
        async for _event in structurer.structure(
            cm, [finding], spec, spec.task_decomposition.tasks, "eng_test", "client_test"
        ):
            pass

        text = await structurer.get_task_section_text("task_001")
        assert "Analyst X disagreed on framing" in text
        assert "Sensitivity: Flips if assumption B changes" in text

    @pytest.mark.asyncio
    async def test_section_text_for_task_without_finding_states_absence(self) -> None:
        spec = _spec(tasks=[_task("task_001", "leaf_1"), _task("task_002", "leaf_2")])
        structurer = ContentStructurer(sprint_contract_generator=_mock_contract_generator())
        async for _event in structurer.structure(
            _confidence_map(),
            [_finding("task_001", "Branch one claim", "CAN-001")],
            spec,
            spec.task_decomposition.tasks,
            "eng_test",
            "client_test",
        ):
            pass

        text = await structurer.get_task_section_text("task_002")
        assert "## Status" in text
        assert "No finding was produced" in text


# ---------------------------------------------------------------------------
# Sprint contract negotiation
# ---------------------------------------------------------------------------


class TestSprintContractNegotiation:
    @pytest.mark.asyncio
    async def test_contract_generated_per_renderable_task(self) -> None:
        spec = _spec()
        gen = _mock_contract_generator()
        structurer = ContentStructurer(sprint_contract_generator=gen)

        async for _event in structurer.structure(
            _confidence_map(),
            [
                _finding("task_001", "Branch one claim", "CAN-001"),
                _finding("task_002", "Branch two claim", "CAN-002"),
            ],
            spec,
            spec.task_decomposition.tasks,
            "eng_test",
            "client_test",
        ):
            pass

        assert gen.generate.await_count == 2
        contracts = await structurer.get_sprint_contracts()
        assert {c.task_id for c in contracts} == {"task_001", "task_002"}

        contract = await structurer.get_sprint_contract("task_001")
        assert contract is not None
        assert contract.section_id == "section_task_001"

    @pytest.mark.asyncio
    async def test_contract_generation_failure_falls_back_to_task_criteria(
        self,
    ) -> None:
        spec = _spec(tasks=[_task("task_001", "leaf_1")])
        gen = MagicMock()
        gen.generate = AsyncMock(side_effect=RuntimeError("LLM unavailable"))
        structurer = ContentStructurer(sprint_contract_generator=gen)

        async for _event in structurer.structure(
            _confidence_map(),
            [_finding("task_001", "Branch one claim", "CAN-001")],
            spec,
            spec.task_decomposition.tasks,
            "eng_test",
            "client_test",
        ):
            pass

        contract = await structurer.get_sprint_contract("task_001")
        assert contract is not None
        assert contract.section_id == "section_task_001"
        # Fallback mirrors the task's acceptance criteria so L4 still has
        # something concrete to score.
        assert contract.acceptance_criteria == ["Return evidence-backed claims."]

    @pytest.mark.asyncio
    async def test_structurer_without_generator_skips_contract_events(self) -> None:
        spec = _spec(tasks=[_task("task_001", "leaf_1")])
        structurer = ContentStructurer()  # no generator wired
        events = []
        async for event in structurer.structure(
            _confidence_map(),
            [_finding("task_001", "Branch one claim", "CAN-001")],
            spec,
            spec.task_decomposition.tasks,
            "eng_test",
            "client_test",
        ):
            events.append(event)

        assert not any(isinstance(e, SprintContractProposed) for e in events)
        assert await structurer.get_sprint_contracts() == []


# ---------------------------------------------------------------------------
# Event emission
# ---------------------------------------------------------------------------


class TestEventEmission:
    @pytest.mark.asyncio
    async def test_structure_emits_expected_events_in_order(self) -> None:
        spec = _spec()
        structurer = ContentStructurer(sprint_contract_generator=_mock_contract_generator())
        events = []
        async for event in structurer.structure(
            _confidence_map(),
            [
                _finding("task_001", "Branch one claim", "CAN-001"),
                _finding("task_002", "Branch two claim", "CAN-002"),
            ],
            spec,
            spec.task_decomposition.tasks,
            "eng_test",
            "client_test",
        ):
            events.append(event)

        # Per task: SectionDrafted -> SprintContractProposed.
        # Then: OutlineGenerated once at the end.
        assert isinstance(events[0], SectionDrafted)
        assert isinstance(events[1], SprintContractProposed)
        assert isinstance(events[2], SectionDrafted)
        assert isinstance(events[3], SprintContractProposed)
        assert isinstance(events[4], OutlineGenerated)
        assert events[4].section_count == len((await structurer.get_outline()).sections)

    @pytest.mark.asyncio
    async def test_section_drafted_carries_claim_count(self) -> None:
        spec = _spec(tasks=[_task("task_001", "leaf_1")])
        structurer = ContentStructurer(sprint_contract_generator=_mock_contract_generator())
        drafted: list[SectionDrafted] = []
        async for event in structurer.structure(
            _confidence_map(),
            [_finding("task_001", "Branch one claim", "CAN-001")],
            spec,
            spec.task_decomposition.tasks,
            "eng_test",
            "client_test",
        ):
            if isinstance(event, SectionDrafted):
                drafted.append(event)
        assert len(drafted) == 1
        assert drafted[0].claim_count == 1
        assert drafted[0].section_id == "section_task_001"
        assert drafted[0].section_title == "Section leaf_1"


# ---------------------------------------------------------------------------
# filter_outline_by_passed_tasks
# ---------------------------------------------------------------------------


class TestOutlineFiltering:
    @pytest.mark.asyncio
    async def test_filter_drops_failed_branch_material(self) -> None:
        spec = _spec()
        structurer = ContentStructurer(sprint_contract_generator=_mock_contract_generator())
        async for _event in structurer.structure(
            _confidence_map(),
            [
                _finding("task_001", "Branch one claim", "CAN-001"),
                _finding("task_002", "Branch two claim", "CAN-002"),
            ],
            spec,
            spec.task_decomposition.tasks,
            "eng_test",
            "client_test",
        ):
            pass

        outline = await structurer.get_outline()
        filtered = filter_outline_by_passed_tasks(outline, {"task_001"})

        remaining_text = {item.text for section in filtered.sections for item in section.items}
        assert "Branch one claim" in remaining_text
        assert "Branch two claim" not in remaining_text
        assert filtered.rendered_task_ids == ["task_001"]

    @pytest.mark.asyncio
    async def test_filter_preserves_provenance_free_items(self) -> None:
        """Framework notes have no task_ids and must survive filtering."""
        spec = _spec(tasks=[_task("task_001", "leaf_1")])
        structurer = ContentStructurer(sprint_contract_generator=_mock_contract_generator())
        async for _event in structurer.structure(
            _confidence_map(),
            [_finding("task_001", "Branch one claim", "CAN-001")],
            spec,
            spec.task_decomposition.tasks,
            "eng_test",
            "client_test",
        ):
            pass

        outline = await structurer.get_outline()
        # Drop every task to force aggressive filtering.
        filtered = filter_outline_by_passed_tasks(outline, set())
        framework_section = next(
            (
                section
                for section in filtered.sections
                if section.section_type == OutlineSectionType.FRAMEWORK_ANALYSIS
            ),
            None,
        )
        # Framework-analysis items carry no task_ids, so they survive filtering.
        assert framework_section is not None
        assert len(framework_section.items) >= 1

    @pytest.mark.asyncio
    async def test_filter_narrows_multi_task_items(self) -> None:
        """When an item lists multiple task_ids, keep only the surviving ones."""
        spec = _spec()
        structurer = ContentStructurer(sprint_contract_generator=_mock_contract_generator())
        cm = ConfidenceMap(
            engagement_id="eng_test",
            client_id="client_test",
            high_confidence_above_80pct=[
                HighConfidenceClaim(
                    claim="Multi-task claim",
                    methodological_agreement="3/3",
                    sources=4,
                    corroboration_count=2,
                    robustness="Stable",
                    curmudgeon_challenge="n/a",
                    aggregated_claim_id="agg_multi",
                    task_ids=["task_001", "task_002"],
                )
            ],
            provenance_index={"agg_multi": ["task_001", "task_002"]},
        )
        async for _event in structurer.structure(
            cm,
            [
                _finding("task_001", "Branch one claim", "CAN-001"),
                _finding("task_002", "Branch two claim", "CAN-002"),
            ],
            spec,
            spec.task_decomposition.tasks,
            "eng_test",
            "client_test",
        ):
            pass

        outline = await structurer.get_outline()
        filtered = filter_outline_by_passed_tasks(outline, {"task_001"})
        executive = next(
            section
            for section in filtered.sections
            if section.section_type == OutlineSectionType.EXECUTIVE_SUMMARY
        )
        multi_item = executive.items[0]
        assert multi_item.task_ids == ["task_001"]


# ---------------------------------------------------------------------------
# Getter safety
# ---------------------------------------------------------------------------


class TestCollectLeafTitlesNested:
    """Pin ``_collect_leaf_titles`` behaviour on deep / irregular trees.

    The structurer consumes the MECE issue tree whole. When Spec Engine
    produces a tree with branches that are themselves decomposed into
    sub-branches (depth 3 and beyond), only the terminal leaves must
    surface as rendering targets -- interior nodes should NOT produce
    their own ``BRANCH`` section.
    """

    def test_depth_three_tree_returns_only_leaves(self) -> None:
        from keystone.structuring.content_structuring import _collect_leaf_titles

        tree = {
            "root": {
                "id": "root",
                "name": "Root",
                "children": [
                    {
                        "id": "branch_A",
                        "name": "A",
                        "children": [
                            {
                                "id": "branch_A1",
                                "name": "A1",
                                "children": [
                                    {"id": "leaf_A1a", "name": "A1 leaf alpha"},
                                    {"id": "leaf_A1b", "name": "A1 leaf beta"},
                                ],
                            },
                            {"id": "leaf_A2", "name": "A leaf two"},
                        ],
                    },
                    {"id": "leaf_B", "name": "B leaf"},
                ],
            }
        }
        leaves = _collect_leaf_titles(tree)
        assert leaves == {
            "leaf_A1a": "A1 leaf alpha",
            "leaf_A1b": "A1 leaf beta",
            "leaf_A2": "A leaf two",
            "leaf_B": "B leaf",
        }
        # Interior node IDs must NOT appear.
        assert "branch_A" not in leaves
        assert "branch_A1" not in leaves
        assert "root" not in leaves

    def test_depth_four_tree_returns_only_leaves(self) -> None:
        from keystone.structuring.content_structuring import _collect_leaf_titles

        tree = {
            "root": {
                "id": "root",
                "name": "Root",
                "children": [
                    {
                        "id": "l1",
                        "name": "Level 1",
                        "children": [
                            {
                                "id": "l2",
                                "name": "Level 2",
                                "children": [
                                    {
                                        "id": "l3",
                                        "name": "Level 3",
                                        "children": [{"id": "leaf_deep", "name": "Deep leaf"}],
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        }
        leaves = _collect_leaf_titles(tree)
        assert leaves == {"leaf_deep": "Deep leaf"}

    def test_non_dict_children_are_ignored(self) -> None:
        from keystone.structuring.content_structuring import _collect_leaf_titles

        # Malformed child entries (strings, None) should not trip the walk.
        tree = {
            "root": {
                "id": "root",
                "name": "Root",
                "children": [
                    "not_a_dict",  # type: ignore[list-item]
                    None,  # type: ignore[list-item]
                    {"id": "leaf_only", "name": "Only leaf"},
                ],
            }
        }
        leaves = _collect_leaf_titles(tree)
        assert leaves == {"leaf_only": "Only leaf"}

    def test_label_alias_used_when_name_missing(self) -> None:
        from keystone.structuring.content_structuring import _collect_leaf_titles

        tree = {
            "id": "root",
            "name": "Root",
            "children": [
                {"id": "leaf_x", "label": "Label alias"},
                {
                    "id": "mid",
                    "label": "Mid",
                    "children": [{"id": "leaf_y", "label": "Deeper alias"}],
                },
            ],
        }
        leaves = _collect_leaf_titles(tree)
        assert leaves == {"leaf_x": "Label alias", "leaf_y": "Deeper alias"}


class TestGetterSafety:
    @pytest.mark.asyncio
    async def test_get_outline_before_structure_raises(self) -> None:
        structurer = ContentStructurer()
        with pytest.raises(RuntimeError, match="structure"):
            await structurer.get_outline()

    @pytest.mark.asyncio
    async def test_get_task_section_text_for_unknown_task_returns_empty(self) -> None:
        structurer = ContentStructurer()
        assert await structurer.get_task_section_text("unknown") == ""

    @pytest.mark.asyncio
    async def test_get_sprint_contract_for_unknown_task_returns_none(self) -> None:
        structurer = ContentStructurer()
        assert await structurer.get_sprint_contract("unknown") is None


# ---------------------------------------------------------------------------
# Slop detection (deterministic prose-quality filter)
# ---------------------------------------------------------------------------


def _sloppy_finding(task_id: str, citation_id: str = "CAN-001") -> StructuredFinding:
    """Finding whose claim text is packed with slop patterns so the
    rendered section text deterministically triggers the detector."""
    return StructuredFinding(
        task_id=task_id,
        agent_id=f"agent_{task_id}",
        engagement_id="eng_test",
        client_id="client_test",
        agent_type="quantitative",
        claims=[
            FindingClaim(
                text=(
                    "It is important to note that we leverage cutting-edge "
                    "tooling to delve into a plethora of synergies"
                ),
                evidence=(
                    "Furthermore, the landscape of tier-one suppliers "
                    "showcases incredibly attractive unit economics."
                ),
                citations=[_citation(citation_id)],
                citation_ids=[citation_id],
                confidence=0.85,
                confidence_tier=ConfidenceTier.HIGH,
                claim_id=f"claim_{task_id}",
                caveats=["Utilize primary sources where possible"],
            )
        ],
        absence_report=["As previously mentioned, no counter-evidence was found"],
        sources_consulted=3,
        tokens_consumed=300,
    )


class TestSlopFiltering:
    @pytest.mark.asyncio
    async def test_slop_event_emitted_per_task_with_matches(self) -> None:
        from keystone.events import SlopDetected

        spec = _spec(tasks=[_task("task_001", "leaf_1")])
        structurer = ContentStructurer()
        events = []
        async for event in structurer.structure(
            _confidence_map(),
            [_sloppy_finding("task_001")],
            spec,
            spec.task_decomposition.tasks,
            "eng_test",
            "client_test",
        ):
            events.append(event)

        slop_events = [e for e in events if isinstance(e, SlopDetected)]
        assert len(slop_events) == 1
        evt = slop_events[0]
        assert evt.task_id == "task_001"
        assert evt.section_id == "section_task_001"
        assert evt.total_count > 0
        assert evt.high_count > 0
        assert evt.cleaned is True
        assert evt.top_categories  # non-empty

    @pytest.mark.asyncio
    async def test_section_text_is_scrubbed(self) -> None:
        spec = _spec(tasks=[_task("task_001", "leaf_1")])
        structurer = ContentStructurer()
        async for _event in structurer.structure(
            _confidence_map(),
            [_sloppy_finding("task_001")],
            spec,
            spec.task_decomposition.tasks,
            "eng_test",
            "client_test",
        ):
            pass
        section = await structurer.get_task_section_text("task_001")
        lowered = section.lower()
        assert "it is important to note that" not in lowered
        assert "leverage" not in lowered
        assert "plethora" not in lowered
        assert "delve into" not in lowered

    @pytest.mark.asyncio
    async def test_no_slop_event_when_finding_is_clean(self) -> None:
        from keystone.events import SlopDetected

        clean_finding = StructuredFinding(
            task_id="task_001",
            agent_id="agent_task_001",
            engagement_id="eng_test",
            client_id="client_test",
            agent_type="quantitative",
            claims=[
                FindingClaim(
                    text="Revenue grew 12% year over year in 2026",
                    evidence="Internal financials cross-checked against SEC 10-K",
                    citations=[_citation("CAN-001")],
                    citation_ids=["CAN-001"],
                    confidence=0.9,
                    confidence_tier=ConfidenceTier.HIGH,
                    claim_id="claim_task_001",
                    caveats=["Subject to revision on Q4 release"],
                )
            ],
            absence_report=[],
            sources_consulted=3,
            tokens_consumed=100,
        )
        # Use an engagement type that won't inject framework-specific slop.
        spec = _spec(tasks=[_task("task_001", "leaf_1")])
        structurer = ContentStructurer()
        events = []
        async for event in structurer.structure(
            _confidence_map(),
            [clean_finding],
            spec,
            spec.task_decomposition.tasks,
            "eng_test",
            "client_test",
        ):
            events.append(event)

        # The stock render_task_section_text template is deterministic so
        # the emission depends only on whether the finding contents
        # contain slop. A clean finding should produce no SlopDetected.
        slop_events = [e for e in events if isinstance(e, SlopDetected)]
        # The template may still emit hits for boilerplate ("various", "notably",
        # etc.) — accept zero or one, but when one is emitted it must be LOW-only.
        if slop_events:
            assert slop_events[0].high_count == 0
            assert slop_events[0].medium_count == 0

    @pytest.mark.asyncio
    async def test_injected_detector_is_used(self) -> None:
        from keystone.events import SlopDetected
        from keystone.quality import (
            Category,
            Severity,
            SlopDetector,
            SlopPattern,
        )

        # Custom detector with a single pattern that will definitely match
        # the rendered section text.
        single = SlopPattern(
            phrase="evidence",
            regex=r"\bEvidence\b",
            category=Category.WEAK_OPENER,
            severity=Severity.MEDIUM,
        )
        detector = SlopDetector([single])

        spec = _spec(tasks=[_task("task_001", "leaf_1")])
        structurer = ContentStructurer(slop_detector=detector)
        events = []
        async for event in structurer.structure(
            _confidence_map(),
            [_finding("task_001", "Branch one claim", "CAN-001")],
            spec,
            spec.task_decomposition.tasks,
            "eng_test",
            "client_test",
        ):
            events.append(event)

        slop_events = [e for e in events if isinstance(e, SlopDetected)]
        assert len(slop_events) == 1
        assert slop_events[0].medium_count >= 1
        assert "weak_opener" in slop_events[0].top_categories
