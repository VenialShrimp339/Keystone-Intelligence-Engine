"""Unit tests for the Markdown renderer."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from keystone.models.citations import (
    Citation,
    CitationManifest,
    ConfidenceTier,
    SourceType,
)
from keystone.models.confidence import (
    ConfidenceMap,
    ContestedClaim,
    HighConfidenceClaim,
    InsufficientEvidenceClaim,
    ModerateConfidenceClaim,
    WeakConfidenceClaim,
)
from keystone.models.evaluation import (
    DimensionScore,
    EvaluationIntensity,
    EvaluationResult,
    Layer1Result,
    Layer2Result,
    Layer3Result,
    RubricDimension,
)
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
    OutlineItem,
    OutlineItemType,
    OutlineSectionType,
    StructuredOutline,
    StructuredSection,
)
from keystone.models.tasks import (
    ResearchTask,
    TaskCategory,
    TaskDecomposition,
    TaskType,
)
from keystone.pipeline.markdown_renderer import MarkdownRenderer

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _citation(cid: str = "CIT-001") -> Citation:
    return Citation(
        citation_id=cid,
        engagement_id="eng_test",
        client_id="c1",
        url=f"https://example.com/{cid}",
        title=f"Source {cid}",
        authors=["Smith, J.", "Doe, A."],
        publication="Journal of Testing",
        date_published=None,
        access_date=datetime.now(UTC),
        source_type=SourceType.ACADEMIC,
        quality_score=0.85,
        url_live=True,
        found_by_agents=["agent_001"],
    )


def _spec() -> EngagementSpec:
    task = ResearchTask(
        id="task_001",
        engagement_id="eng_test",
        client_id="c1",
        category=TaskCategory.MARKET_SIZING,
        type=TaskType.ESTIMATIVE,
        target_decision_usefulness=3,
        description="Estimate TAM",
        acceptance_criteria=["Top-down estimate", "Bottom-up estimate"],
        deliverable_destination="Section 1",
        priority=1,
        anti_confirmatory_framing="Evaluate whether the market is as large as projected",
        assigned_tools=["exa_search", "brave_search", "edgar_filings"],
        end_product="TAM estimate",
    )
    return EngagementSpec(
        research_spec=ResearchSpec(
            engagement_id="eng_test",
            client_id="c1",
            title="TAM for L4+ AV Sensor Market",
            created_at=datetime.now(UTC),
            specification_version=1,
            decision_context="Investment decision",
            surprising_finding="Market smaller than expected",
            questions=[ResearchQuestion(question="What is the TAM?", is_primary=True)],
            output_format="markdown",
            engagement_type=EngagementType.SIZING,
            day_1_hypothesis="TAM exceeds $10B by 2030",
        ),
        task_decomposition=TaskDecomposition(
            project="AV Sensors",
            engagement_id="eng_test",
            client_id="c1",
            research_md_path="/tmp/RESEARCH.md",
            specification_version=1,
            decomposition_rationale="Needs multiple approaches",
            tasks=[task],
        ),
        validation_report=ValidationReport(
            intent_clear=True,
            scope_valid=True,
            within_frontier=True,
            quality_threshold_met=True,
        ),
    )


def _findings() -> list[StructuredFinding]:
    return [
        StructuredFinding(
            task_id="task_001",
            agent_id="agent_001",
            engagement_id="eng_test",
            client_id="c1",
            agent_type="quantitative",
            claims=[
                FindingClaim(
                    text="L4+ AV sensor TAM projected at $12B by 2030",
                    evidence="Industry reports from McKinsey, BCG converge",
                    citations=[_citation("CIT-001")],
                    confidence=0.85,
                    confidence_tier=ConfidenceTier.HIGH,
                    caveats=["Assumes regulatory approval timeline holds"],
                ),
                FindingClaim(
                    text="LiDAR costs declining at 20% CAGR",
                    evidence="Historical pricing data from Velodyne, Luminar",
                    citations=[_citation("CIT-002")],
                    confidence=0.72,
                    confidence_tier=ConfidenceTier.MODERATE,
                ),
            ],
            absence_report=["No data on Chinese OEM adoption rates"],
            sources_consulted=8,
            tokens_consumed=1500,
        ),
    ]


def _confidence_map() -> ConfidenceMap:
    return ConfidenceMap(
        engagement_id="eng_test",
        client_id="c1",
        high_confidence_above_80pct=[
            HighConfidenceClaim(
                claim="TAM exceeds $10B by 2030",
                methodological_agreement="3/4 (Quant, Market, Hist)",
                sources=5,
                corroboration_count=3,
                robustness="Holds under +/-20% variation",
                curmudgeon_challenge="Regulation may slow adoption",
            ),
        ],
        moderate_confidence_60_80pct=[
            ModerateConfidenceClaim(
                claim="LiDAR costs declining 20% CAGR",
                methodological_agreement="2/4",
                dissent="Adversarial analyst flags potential price floor",
                sources=3,
                sensitivity="If CAGR is 10% instead, timeline extends 3 years",
            ),
        ],
        weak_confidence_50_60pct=[
            WeakConfidenceClaim(
                claim="Solid-state LiDAR will dominate by 2028",
                methodological_agreement="2/4",
                key_issue="Manufacturing yield uncertainty",
                sources=2,
                recommendation="Present with explicit uncertainty",
            ),
        ],
        contested_below_50pct=[
            ContestedClaim(
                claim="Camera-only approach will fail for L4",
                methodological_agreement="1/4",
                key_disagreement="Tesla's approach may prove viable with FSD V13+",
                sources=4,
                steelmanned_opposing_view=(
                    "Tesla's fleet-scale data advantage could compensate "
                    "for hardware limitations through superior perception software"
                ),
            ),
        ],
        insufficient_evidence=[
            InsufficientEvidenceClaim(
                claim="Chinese OEM sensor adoption trajectory",
                reason="Data not available in English-language sources",
                priority="high",
            ),
        ],
        gaps_identified=["Chinese OEM data", "Insurance industry requirements"],
        absence_report=["No L5 deployment timelines found"],
    )


def _eval_results() -> list[EvaluationResult]:
    return [
        EvaluationResult(
            evaluation_id=str(uuid.uuid4()),
            engagement_id="eng_test",
            client_id="c1",
            task_id="task_001",
            evaluated_at=datetime.now(UTC),
            intensity=EvaluationIntensity.STANDARD,
            passed=True,
            overall_score=72.5,
            layer1_results=Layer1Result(facts_verified=5, facts_failed=1),
            layer2_results=Layer2Result(
                citations_checked=3, citations_verified=3, gate_passed=True
            ),
            feedback="PASSED with score 72.5/100. Strengths: source_quality: 80.",
        ),
    ]


def _manifest() -> CitationManifest:
    return CitationManifest(
        manifest_id="MAN-001",
        engagement_id="eng_test",
        client_id="c1",
        citations=[_citation("CIT-001"), _citation("CIT-002")],
        dead_urls=["CIT-003"],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestBasicRendering:
    def test_render_produces_non_empty_string(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(), _findings(), _confidence_map(), _eval_results(), _manifest()
        )
        assert isinstance(output, str)
        assert len(output) > 100

    def test_title_present(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(), _findings(), _confidence_map(), _eval_results(), _manifest()
        )
        assert "# TAM for L4+ AV Sensor Market" in output


class TestAllSectionsPresent:
    def test_all_sections_in_output(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(), _findings(), _confidence_map(), _eval_results(), _manifest()
        )

        assert "## Executive Summary" in output
        assert "## Key Findings" in output
        assert "## Areas of Uncertainty" in output
        assert "## Research Gaps" in output
        assert "## Sources" in output
        assert "## Quality Assessment" in output

    def test_engagement_metadata(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(), _findings(), _confidence_map(), _eval_results(), _manifest()
        )
        assert "eng_test" in output
        assert "Sizing" in output
        assert "Day-1 Hypothesis" in output


class TestCitationFormatting:
    def test_key_findings_prefer_canonical_citation_ids(self) -> None:
        renderer = MarkdownRenderer()
        findings = _findings()
        canonicalized = [
            findings[0].model_copy(
                update={
                    "claims": [
                        findings[0].claims[0].model_copy(update={"citation_ids": ["CAN-001"]}),
                        findings[0].claims[1].model_copy(update={"citation_ids": ["CAN-002"]}),
                    ]
                }
            )
        ]

        output = renderer._render_key_findings(canonicalized, _confidence_map())

        assert "Sources: CAN-001" in output
        assert "Sources: CAN-002" in output
        assert "Sources: CIT-001" not in output
        assert "Sources: CIT-002" not in output

    def test_citations_formatted_in_sources(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(), _findings(), _confidence_map(), _eval_results(), _manifest()
        )
        assert "CIT-001" in output
        assert "CIT-002" in output
        assert "Smith, J." in output
        assert "Journal of Testing" in output
        assert "https://example.com/CIT-001" in output

    def test_dead_urls_noted(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(), _findings(), _confidence_map(), _eval_results(), _manifest()
        )
        assert "Dead URLs" in output


class TestEmptyFindings:
    def test_empty_findings_graceful(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            [],  # no findings
            ConfidenceMap(engagement_id="eng_test", client_id="c1"),
            [],  # no evals
            CitationManifest(manifest_id="MAN-empty", engagement_id="eng_test", client_id="c1"),
        )

        assert "## Executive Summary" in output
        assert "No claims reached high confidence" in output
        assert "No findings" in output
        assert "No citations in manifest" in output
        assert "No evaluations performed" in output


class TestConfidenceTiers:
    def test_high_confidence_in_executive_summary(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(), _findings(), _confidence_map(), _eval_results(), _manifest()
        )
        # High confidence claims appear in executive summary
        assert "TAM exceeds $10B by 2030" in output
        assert "Curmudgeon challenge" in output.lower() or "curmudgeon" in output.lower()

    def test_moderate_confidence_in_key_findings(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(), _findings(), _confidence_map(), _eval_results(), _manifest()
        )
        assert "LiDAR costs declining 20% CAGR" in output

    def test_weak_claims_in_uncertainty(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(), _findings(), _confidence_map(), _eval_results(), _manifest()
        )
        assert "Solid-state LiDAR" in output
        assert "Weak Confidence" in output

    def test_contested_claims_in_uncertainty(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(), _findings(), _confidence_map(), _eval_results(), _manifest()
        )
        assert "Camera-only approach" in output
        assert "Contested Claims" in output
        assert "Tesla" in output  # steelmanned opposing view

    def test_insufficient_evidence_in_gaps(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(), _findings(), _confidence_map(), _eval_results(), _manifest()
        )
        assert "Chinese OEM sensor adoption" in output
        assert "Insufficient Evidence" in output

    def test_gaps_and_absence_in_research_gaps(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(), _findings(), _confidence_map(), _eval_results(), _manifest()
        )
        assert "Chinese OEM data" in output
        assert "Insurance industry requirements" in output
        assert "Chinese OEM adoption rates" in output  # from absence report


class TestQualityAssessment:
    def test_quality_table_present(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(), _findings(), _confidence_map(), _eval_results(), _manifest()
        )
        assert "Tasks Evaluated" in output
        assert "Tasks Passed" in output
        assert "Average Score" in output
        assert "72.5" in output

    def test_per_task_results(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(), _findings(), _confidence_map(), _eval_results(), _manifest()
        )
        assert "task_001" in output
        assert "PASS" in output


class TestOutlineIntegration:
    def test_render_without_outline_is_unchanged(self) -> None:
        """Back-compat: an outline-less render call still produces a full brief."""
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(), _findings(), _confidence_map(), _eval_results(), _manifest()
        )
        assert "## Analytical Framework" not in output
        assert "## Executive Summary" in output

    def test_render_with_outline_injects_framework_section(self) -> None:
        from keystone.models.structuring import (
            AnalyticalFramework,
            FrameworkHint,
            StructuredOutline,
        )

        outline = StructuredOutline(
            engagement_id="eng_test",
            client_id="c1",
            engagement_type="sizing",
            frameworks=[
                FrameworkHint(
                    framework=AnalyticalFramework.ESTIMATION,
                    rationale="Sizing requires top-down and bottom-up.",
                    mandatory=True,
                )
            ],
        )
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            _eval_results(),
            _manifest(),
            outline,
        )
        assert "## Analytical Framework" in output
        assert "Estimation" in output
        assert "primary" in output
        assert "top-down and bottom-up" in output

    def test_render_with_empty_outline_frameworks_omits_framework_section(
        self,
    ) -> None:
        from keystone.models.structuring import StructuredOutline

        outline = StructuredOutline(
            engagement_id="eng_test",
            client_id="c1",
            engagement_type="sizing",
            frameworks=[],
        )
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            _eval_results(),
            _manifest(),
            outline,
        )
        assert "## Analytical Framework" not in output


# ---------------------------------------------------------------------------
# Outline-driven rendering fixtures
# ---------------------------------------------------------------------------


def _exec_item() -> OutlineItem:
    return OutlineItem(
        item_id="agg_high_001",
        item_type=OutlineItemType.CLAIM,
        text="TAM exceeds $10B by 2030",
        task_ids=["task_001"],
        citation_ids=["CIT-001", "CIT-002"],
        issue_tree_branch_id="branch_sizing",
        note="Robustness: Holds under +/-20% | Curmudgeon: Regulation may slow adoption",
    )


def _branch_item() -> OutlineItem:
    return OutlineItem(
        item_id="claim_001",
        item_type=OutlineItemType.CLAIM,
        text="L4+ sensor TAM projected at $12B by 2030",
        task_ids=["task_001"],
        citation_ids=["CIT-001"],
        issue_tree_branch_id="branch_sizing",
        confidence=0.85,
        confidence_tier=ConfidenceTier.HIGH,
        evidence="McKinsey and BCG converge on the headline number",
        caveats=["Assumes regulatory approval timeline holds"],
    )


def _moderate_item() -> OutlineItem:
    return OutlineItem(
        item_id="agg_mod_001",
        item_type=OutlineItemType.CLAIM,
        text="LiDAR costs declining 20% CAGR",
        task_ids=["task_001"],
        citation_ids=["CIT-002"],
        issue_tree_branch_id="branch_sizing",
        note=(
            "Dissent: Adversarial analyst flags price floor | "
            "Sensitivity: 10% CAGR pushes timeline +3y"
        ),
    )


def _weak_item() -> OutlineItem:
    return OutlineItem(
        item_id="agg_weak_001",
        item_type=OutlineItemType.CLAIM,
        text="Solid-state LiDAR dominates by 2028",
        task_ids=["task_002"],
        citation_ids=["CIT-002"],
        issue_tree_branch_id="branch_technology",
        note="Key issue: Manufacturing yield uncertainty | Recommendation: Frame as directional",
    )


def _contested_item() -> OutlineItem:
    return OutlineItem(
        item_id="agg_cont_001",
        item_type=OutlineItemType.CLAIM,
        text="Camera-only L4 stack will fail",
        task_ids=["task_002"],
        citation_ids=["CIT-001"],
        issue_tree_branch_id="branch_technology",
        note="Key disagreement: Tesla FSD V13+ viability | Steelmanned opposing view: "
        "Fleet-scale data advantage compensates",
    )


def _gap_item() -> OutlineItem:
    return OutlineItem(
        item_id="gap_1",
        item_type=OutlineItemType.GAP,
        text="Chinese OEM adoption trajectory",
        task_ids=["task_002"],
    )


def _insufficient_item() -> OutlineItem:
    return OutlineItem(
        item_id="agg_insuf_001",
        item_type=OutlineItemType.INSUFFICIENT,
        text="Insurance industry sensor requirements",
        task_ids=["task_002"],
        citation_ids=[],
        note="Reason: No English-language sources | Priority: high",
    )


def _absence_item() -> OutlineItem:
    return OutlineItem(
        item_id="absence_task_001_1",
        item_type=OutlineItemType.ABSENCE,
        text="No L5 deployment timelines found in filings",
        task_ids=["task_001"],
    )


def _full_outline() -> StructuredOutline:
    """Outline with every section type populated — the production shape."""
    return StructuredOutline(
        engagement_id="eng_test",
        client_id="c1",
        engagement_type="sizing",
        frameworks=[
            FrameworkHint(
                framework=AnalyticalFramework.ESTIMATION,
                rationale="Sizing requires top-down and bottom-up.",
                mandatory=True,
            ),
        ],
        sections=[
            StructuredSection(
                section_id="executive_summary",
                section_type=OutlineSectionType.EXECUTIVE_SUMMARY,
                title="Executive Summary",
                task_ids=["task_001"],
                claim_ids=["agg_high_001"],
                citation_ids=["CIT-001", "CIT-002"],
                items=[_exec_item()],
            ),
            StructuredSection(
                section_id="framework_analysis",
                section_type=OutlineSectionType.FRAMEWORK_ANALYSIS,
                title="Analytical Framework",
                framework=AnalyticalFramework.ESTIMATION,
                items=[
                    OutlineItem(
                        item_id="framework_estimation",
                        item_type=OutlineItemType.FRAMEWORK_NOTE,
                        text="Estimation (primary): Sizing requires top-down and bottom-up.",
                    ),
                ],
            ),
            StructuredSection(
                section_id="branch_branch_sizing",
                section_type=OutlineSectionType.BRANCH,
                title="Branch: Sizing",
                framework=AnalyticalFramework.ESTIMATION,
                issue_tree_branch_id="branch_sizing",
                task_ids=["task_001"],
                claim_ids=["claim_001"],
                citation_ids=["CIT-001"],
                items=[_branch_item()],
            ),
            StructuredSection(
                section_id="moderate_confidence",
                section_type=OutlineSectionType.MODERATE,
                title="Moderate Confidence Findings (60-80%)",
                task_ids=["task_001"],
                items=[_moderate_item()],
            ),
            StructuredSection(
                section_id="weak_confidence",
                section_type=OutlineSectionType.WEAK,
                title="Weak Confidence (50-60%)",
                task_ids=["task_002"],
                items=[_weak_item()],
            ),
            StructuredSection(
                section_id="contested_claims",
                section_type=OutlineSectionType.CONTESTED,
                title="Contested Claims (<50%)",
                task_ids=["task_002"],
                items=[_contested_item()],
            ),
            StructuredSection(
                section_id="research_gaps",
                section_type=OutlineSectionType.GAPS,
                title="Identified Gaps",
                task_ids=["task_002"],
                items=[_gap_item()],
            ),
            StructuredSection(
                section_id="insufficient_evidence",
                section_type=OutlineSectionType.INSUFFICIENT,
                title="Insufficient Evidence",
                task_ids=["task_002"],
                items=[_insufficient_item()],
            ),
            StructuredSection(
                section_id="absence_reports",
                section_type=OutlineSectionType.ABSENCE,
                title="Absence Reports",
                task_ids=["task_001"],
                items=[_absence_item()],
            ),
        ],
        rendered_task_ids=["task_001", "task_002"],
        uncovered_branch_ids=["branch_adjacent"],
    )


def _eval_result_with_layer3() -> EvaluationResult:
    return EvaluationResult(
        evaluation_id=str(uuid.uuid4()),
        engagement_id="eng_test",
        client_id="c1",
        task_id="task_001",
        evaluated_at=datetime.now(UTC),
        intensity=EvaluationIntensity.STANDARD,
        passed=True,
        overall_score=78.0,
        layer1_results=Layer1Result(facts_verified=5, facts_failed=1),
        layer2_results=Layer2Result(citations_checked=3, citations_verified=3, gate_passed=True),
        layer3_results=Layer3Result(
            dimension_scores=[
                DimensionScore(
                    dimension=RubricDimension.ANALYTICAL_DEPTH,
                    score=80.0,
                    feedback="Solid depth",
                ),
                DimensionScore(
                    dimension=RubricDimension.SOURCE_QUALITY,
                    score=82.0,
                    feedback="Primary sources cited",
                ),
                DimensionScore(
                    dimension=RubricDimension.CALIBRATED_CONFIDENCE,
                    score=70.0,
                    feedback="Slight overconfidence on tail",
                ),
            ],
            weighted_total=77.0,
            gestalt_adjustment=1.0,
            final_score=78.0,
        ),
        feedback="PASSED with score 78.0/100.",
    )


# ---------------------------------------------------------------------------
# Outline-driven rendering — full structure
# ---------------------------------------------------------------------------


class TestOutlineDrivenStructure:
    def test_all_outline_sections_rendered_in_order(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            _eval_results(),
            _manifest(),
            _full_outline(),
        )

        expected_order = [
            "# TAM for L4+ AV Sensor Market",
            "## Executive Summary",
            "## Analytical Framework",
            "## Key Findings",
            "## Areas of Uncertainty",
            "## Evidence Gaps",
            "## Absence Report",
            "## Evaluation Summary",
            "## Sources",
        ]
        positions = [output.find(heading) for heading in expected_order]
        assert -1 not in positions, f"Missing section among: {expected_order}"
        assert positions == sorted(positions), (
            f"Sections out of order: {list(zip(expected_order, positions, strict=True))}"
        )

    def test_no_legacy_section_names_when_outline_provided(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            _eval_results(),
            _manifest(),
            _full_outline(),
        )
        assert "## Research Gaps" not in output
        assert "## Quality Assessment" not in output


# ---------------------------------------------------------------------------
# Outline-driven rendering — Executive Summary
# ---------------------------------------------------------------------------


class TestOutlineExecutiveSummary:
    def test_confidence_distribution_line_present(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            _eval_results(),
            _manifest(),
            _full_outline(),
        )
        assert "Confidence distribution" in output
        assert "high: 1" in output
        assert "moderate: 1" in output
        assert "weak: 1" in output
        assert "contested: 1" in output
        assert "insufficient: 1" in output

    def test_high_confidence_claim_with_tier_badge_and_citations(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            _eval_results(),
            _manifest(),
            _full_outline(),
        )
        # Exec claim uses [HIGH] badge and inline [1][2] refs for CIT-001 + CIT-002.
        assert "**TAM exceeds $10B by 2030** [HIGH] [1][2]" in output
        # Robustness/Curmudgeon note appears as sub-bullet.
        assert "Robustness: Holds under +/-20%" in output

    def test_uncovered_branch_caveat_when_branches_remain(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            _eval_results(),
            _manifest(),
            _full_outline(),
        )
        assert "Critical caveat: 1 issue-tree branch(es) remain" in output

    def test_no_high_confidence_claims_shows_fallback_message(self) -> None:
        outline = _full_outline().model_copy()
        outline = outline.model_copy(
            update={
                "sections": [
                    s
                    for s in outline.sections
                    if s.section_type != OutlineSectionType.EXECUTIVE_SUMMARY
                ],
            }
        )
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            _eval_results(),
            _manifest(),
            outline,
        )
        assert "No claims reached high confidence" in output


# ---------------------------------------------------------------------------
# Outline-driven rendering — Analytical Framework
# ---------------------------------------------------------------------------


class TestOutlineAnalyticalFramework:
    def test_uses_framework_analysis_section_when_available(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            _eval_results(),
            _manifest(),
            _full_outline(),
        )
        assert "## Analytical Framework" in output
        assert "Estimation (primary): Sizing requires top-down and bottom-up." in output

    def test_falls_back_to_frameworks_list_when_no_section(self) -> None:
        outline = StructuredOutline(
            engagement_id="eng_test",
            client_id="c1",
            engagement_type="sizing",
            frameworks=[
                FrameworkHint(
                    framework=AnalyticalFramework.VALUE_CHAIN,
                    rationale="Value-chain mapping clarifies margin capture.",
                    mandatory=False,
                ),
            ],
        )
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            _eval_results(),
            _manifest(),
            outline,
        )
        assert "## Analytical Framework" in output
        assert "Value Chain" in output
        assert "augmenting" in output

    def test_section_absent_when_neither_section_nor_frameworks(self) -> None:
        outline = StructuredOutline(
            engagement_id="eng_test",
            client_id="c1",
            engagement_type="sizing",
            frameworks=[],
        )
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            _eval_results(),
            _manifest(),
            outline,
        )
        assert "## Analytical Framework" not in output


# ---------------------------------------------------------------------------
# Outline-driven rendering — Key Findings
# ---------------------------------------------------------------------------


class TestOutlineKeyFindings:
    def test_branch_sections_become_subsections(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            _eval_results(),
            _manifest(),
            _full_outline(),
        )
        assert "### Branch: Sizing" in output
        assert "*Applied framework: Estimation*" in output

    def test_claims_have_tier_and_confidence_badges(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            _eval_results(),
            _manifest(),
            _full_outline(),
        )
        assert "**L4+ sensor TAM projected at $12B by 2030** [HIGH, 85%] [1]" in output

    def test_claims_expose_evidence_and_caveats(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            _eval_results(),
            _manifest(),
            _full_outline(),
        )
        assert "Evidence: McKinsey and BCG converge" in output
        assert "Caveats: Assumes regulatory approval timeline holds" in output

    def test_fallback_message_when_no_branches(self) -> None:
        outline = StructuredOutline(
            engagement_id="eng_test",
            client_id="c1",
            engagement_type="sizing",
        )
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            _eval_results(),
            _manifest(),
            outline,
        )
        assert "No research branches produced findings" in output


# ---------------------------------------------------------------------------
# Outline-driven rendering — Areas of Uncertainty
# ---------------------------------------------------------------------------


class TestOutlineUncertainty:
    def test_all_three_tiers_rendered_as_subsections(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            _eval_results(),
            _manifest(),
            _full_outline(),
        )
        assert "### Moderate Confidence (60-80%)" in output
        assert "### Weak Confidence (50-60%)" in output
        assert "### Contested Claims (<50%)" in output

    def test_tier_badges_present_on_claims(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            _eval_results(),
            _manifest(),
            _full_outline(),
        )
        assert "**LiDAR costs declining 20% CAGR** [MODERATE]" in output
        assert "**Solid-state LiDAR dominates by 2028** [WEAK]" in output
        assert "**Camera-only L4 stack will fail** [CONTESTED]" in output

    def test_notes_rendered_as_subitems(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            _eval_results(),
            _manifest(),
            _full_outline(),
        )
        assert "Sensitivity: 10% CAGR pushes timeline +3y" in output
        assert "Key issue: Manufacturing yield uncertainty" in output
        assert "Steelmanned opposing view: Fleet-scale data advantage" in output

    def test_fallback_message_when_uncertainty_empty(self) -> None:
        outline = _full_outline()
        outline = outline.model_copy(
            update={
                "sections": [
                    s
                    for s in outline.sections
                    if s.section_type
                    not in (
                        OutlineSectionType.MODERATE,
                        OutlineSectionType.WEAK,
                        OutlineSectionType.CONTESTED,
                    )
                ],
            }
        )
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            _eval_results(),
            _manifest(),
            outline,
        )
        assert "No moderate, weak, or contested claims identified" in output


# ---------------------------------------------------------------------------
# Outline-driven rendering — Evidence Gaps
# ---------------------------------------------------------------------------


class TestOutlineEvidenceGaps:
    def test_identified_gaps_rendered(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            _eval_results(),
            _manifest(),
            _full_outline(),
        )
        assert "### Identified Gaps" in output
        assert "Chinese OEM adoption trajectory" in output

    def test_insufficient_evidence_rendered_with_badge(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            _eval_results(),
            _manifest(),
            _full_outline(),
        )
        assert "### Insufficient Evidence" in output
        assert "**Insurance industry sensor requirements** [INSUFFICIENT]" in output
        assert "Reason: No English-language sources" in output

    def test_uncovered_branches_rendered(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            _eval_results(),
            _manifest(),
            _full_outline(),
        )
        assert "### Uncovered Issue-Tree Branches" in output
        assert "- branch_adjacent" in output

    def test_fallback_message_when_all_empty(self) -> None:
        outline = StructuredOutline(
            engagement_id="eng_test",
            client_id="c1",
            engagement_type="sizing",
        )
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            _eval_results(),
            _manifest(),
            outline,
        )
        assert "No evidence gaps identified" in output


# ---------------------------------------------------------------------------
# Outline-driven rendering — Absence Report
# ---------------------------------------------------------------------------


class TestOutlineAbsenceReport:
    def test_absence_items_rendered(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            _eval_results(),
            _manifest(),
            _full_outline(),
        )
        assert "## Absence Report" in output
        assert "No L5 deployment timelines found in filings" in output

    def test_absence_section_omitted_when_no_items(self) -> None:
        outline = _full_outline()
        outline = outline.model_copy(
            update={
                "sections": [
                    s for s in outline.sections if s.section_type != OutlineSectionType.ABSENCE
                ],
            }
        )
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            _eval_results(),
            _manifest(),
            outline,
        )
        assert "## Absence Report" not in output


# ---------------------------------------------------------------------------
# Outline-driven rendering — Evaluation Summary
# ---------------------------------------------------------------------------


class TestOutlineEvaluationSummary:
    def test_evaluation_summary_heading_replaces_quality_assessment(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            _eval_results(),
            _manifest(),
            _full_outline(),
        )
        assert "## Evaluation Summary" in output

    def test_dimension_scores_table_when_layer3_present(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            [_eval_result_with_layer3()],
            _manifest(),
            _full_outline(),
        )
        assert "### Dimension Scores (average across tasks)" in output
        assert "| Analytical Depth | 80.0/100 |" in output
        assert "| Source Quality | 82.0/100 |" in output
        assert "| Calibrated Confidence | 70.0/100 |" in output

    def test_no_dimension_table_when_no_layer3(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            _eval_results(),
            _manifest(),
            _full_outline(),
        )
        # _eval_results() fixture has no layer3_results set.
        assert "### Dimension Scores" not in output
        assert "### Per-Task Results" in output

    def test_empty_results_graceful(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            [],
            _manifest(),
            _full_outline(),
        )
        assert "## Evaluation Summary" in output
        assert "No evaluations performed" in output


# ---------------------------------------------------------------------------
# Outline-driven rendering — Inline citations
# ---------------------------------------------------------------------------


class TestOutlineInlineCitations:
    def test_citation_ids_mapped_to_numbered_refs(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            _eval_results(),
            _manifest(),
            _full_outline(),
        )
        # Manifest has CIT-001 first (→ [1]) and CIT-002 second (→ [2]).
        assert "[1][2]" in output  # Executive summary cites both
        assert "[1]" in output  # Branch finding cites only CIT-001

    def test_inline_numbers_align_with_sources_list(self) -> None:
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            _eval_results(),
            _manifest(),
            _full_outline(),
        )
        # The first citation in the manifest must be numbered 1. in Sources.
        sources_section = output.split("## Sources", 1)[1]
        assert "1. [CIT-001]" in sources_section
        assert "2. [CIT-002]" in sources_section

    def test_unknown_citation_falls_back_to_raw_id(self) -> None:
        outline = _full_outline()
        outline = outline.model_copy(
            update={
                "sections": [
                    s.model_copy(
                        update={
                            "items": [
                                item.model_copy(update={"citation_ids": ["CIT-UNKNOWN"]})
                                for item in s.items
                            ],
                        }
                    )
                    if s.section_type == OutlineSectionType.EXECUTIVE_SUMMARY
                    else s
                    for s in outline.sections
                ],
            }
        )
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            _eval_results(),
            _manifest(),
            outline,
        )
        # Citation not in manifest falls back to its raw ID.
        assert "[CIT-UNKNOWN]" in output


# ---------------------------------------------------------------------------
# Outline-driven rendering — Empty outline safety
# ---------------------------------------------------------------------------


class TestOutlineEmpty:
    def test_outline_with_no_sections_still_renders_cleanly(self) -> None:
        outline = StructuredOutline(
            engagement_id="eng_test",
            client_id="c1",
            engagement_type="sizing",
        )
        renderer = MarkdownRenderer()
        output = renderer.render(
            _spec(),
            _findings(),
            _confidence_map(),
            _eval_results(),
            _manifest(),
            outline,
        )
        assert "## Executive Summary" in output
        assert "## Key Findings" in output
        assert "## Areas of Uncertainty" in output
        assert "## Evidence Gaps" in output
        # Absence section drops out when there are no absence items.
        assert "## Absence Report" not in output
        assert "## Evaluation Summary" in output
        assert "## Sources" in output
