"""Unit tests for the Markdown renderer."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

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
    EvaluationIntensity,
    EvaluationResult,
    Layer1Result,
    Layer2Result,
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
