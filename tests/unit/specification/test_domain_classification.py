"""Tests for domain classification and domain-aware pipeline behavior.

Covers: EngagementType DESIGN/SYNTHESIS, ClassificationResult.domain,
domain-aware methodology/source selection, domain-aware non-goals,
technical_researcher template, EDGAR cleanup, _resolve_category,
_engagement_type_fit completeness, and framework_selector domain awareness.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from keystone.evaluator.rubric_config import ENGAGEMENT_PROFILE_MAP
from keystone.models.research import (
    EngagementType,
    PipelineProfile,
    ResearchQuestion,
    ResearchSpec,
)
from keystone.models.structuring import AnalyticalFramework
from keystone.models.tasks import ModelTier, ResearchTask, TaskCategory, TaskType
from keystone.specification.engagement_classifier import (
    _DEFAULT_PROFILES,
    ClassificationResult,
    EngagementClassifier,
)
from keystone.specification.spec_engine import (
    _DEFAULT_METHODOLOGY,
    _classify_domain_group,
    _resolve_methodology,
    _resolve_sources,
)
from keystone.specification.task_generator import TaskGenerator
from keystone.specification.template_registry import TemplateRegistry
from keystone.structuring.framework_selector import (
    frameworks_for_engagement,
    primary_framework,
)
from keystone.tool_names import ToolName


class TestNewEngagementTypes:
    def test_design_type_exists(self):
        assert EngagementType("design") == EngagementType.DESIGN

    def test_synthesis_type_exists(self):
        assert EngagementType("synthesis") == EngagementType.SYNTHESIS

    def test_design_default_profile_is_deep(self):
        assert _DEFAULT_PROFILES[EngagementType.DESIGN] == PipelineProfile.DEEP

    def test_synthesis_default_profile_is_standard(self):
        assert _DEFAULT_PROFILES[EngagementType.SYNTHESIS] == PipelineProfile.STANDARD

    def test_design_has_evaluation_profile(self):
        assert EngagementType.DESIGN in ENGAGEMENT_PROFILE_MAP

    def test_synthesis_has_evaluation_profile(self):
        assert EngagementType.SYNTHESIS in ENGAGEMENT_PROFILE_MAP

    def test_design_has_default_methodology(self):
        assert EngagementType.DESIGN in _DEFAULT_METHODOLOGY
        assert len(_DEFAULT_METHODOLOGY[EngagementType.DESIGN]) >= 1

    def test_synthesis_has_default_methodology(self):
        assert EngagementType.SYNTHESIS in _DEFAULT_METHODOLOGY
        assert len(_DEFAULT_METHODOLOGY[EngagementType.SYNTHESIS]) >= 1


class TestClassificationResultDomain:
    def test_accepts_domain_field(self):
        result = ClassificationResult(
            engagement_type=EngagementType.EVALUATIVE,
            pipeline_profile=PipelineProfile.STANDARD,
            confidence=0.9,
            reasoning="test",
            domain="technology_architecture",
        )
        assert result.domain == "technology_architecture"

    def test_domain_defaults_to_business_strategy(self):
        result = ClassificationResult(
            engagement_type=EngagementType.EVALUATIVE,
            pipeline_profile=PipelineProfile.STANDARD,
            confidence=0.9,
            reasoning="test",
        )
        assert result.domain == "business_strategy"

    async def test_classifier_parses_domain_from_llm(self):
        async def llm(prompt: str) -> str:
            return json.dumps(
                {
                    "engagement_type": "design",
                    "domain": "technology_architecture",
                    "pipeline_profile": "deep",
                    "confidence": 0.92,
                    "reasoning": "Design engagement for technical architecture.",
                }
            )

        classifier = EngagementClassifier(llm)
        result = await classifier.classify("Design a multi-agent research pipeline")
        assert result.engagement_type == EngagementType.DESIGN
        assert result.domain == "technology_architecture"

    async def test_classifier_defaults_domain_when_missing(self):
        async def llm(prompt: str) -> str:
            return json.dumps(
                {
                    "engagement_type": "strategic",
                    "pipeline_profile": "deep",
                    "confidence": 0.85,
                    "reasoning": "Complex strategic question.",
                }
            )

        classifier = EngagementClassifier(llm)
        result = await classifier.classify("Should we acquire Company Y?")
        assert result.domain == "business_strategy"


class TestDomainGroupClassification:
    @pytest.mark.parametrize(
        ("domain", "expected"),
        [
            ("technology_architecture", "technical"),
            ("technical_evaluation", "technical"),
            ("software_engineering", "technical"),
            ("system_design", "technical"),
            ("scientific_research", "scientific"),
            ("literature_synthesis", "scientific"),
            ("academic_review", "scientific"),
            ("business_strategy", "business"),
            ("financial_analysis", "business"),
            ("market_research", "business"),
            ("m_and_a", "business"),
            ("organizational_design", "business"),
            (None, "unknown"),
            ("something_novel", "unknown"),
        ],
    )
    def test_domain_group_mapping(self, domain: str | None, expected: str):
        assert _classify_domain_group(domain) == expected


class TestDomainAwareMethodology:
    def test_technical_evaluative_gets_tradeoff(self):
        methodology = _resolve_methodology(EngagementType.EVALUATIVE, "technical_evaluation")
        assert any("Trade-off" in m.framework for m in methodology)
        assert not any("Porter" in m.framework for m in methodology)

    def test_business_evaluative_gets_porters(self):
        methodology = _resolve_methodology(EngagementType.EVALUATIVE, "business_strategy")
        assert any("Porter" in m.framework for m in methodology)

    def test_scientific_exploratory_gets_systematic_review(self):
        methodology = _resolve_methodology(EngagementType.EXPLORATORY, "scientific_research")
        assert any("Systematic" in m.framework or "Literature" in m.framework for m in methodology)

    def test_none_domain_falls_back_to_default(self):
        methodology = _resolve_methodology(EngagementType.STRATEGIC, None)
        assert any("Scenario" in m.framework for m in methodology)

    def test_design_methodology_exists(self):
        methodology = _resolve_methodology(EngagementType.DESIGN, None)
        assert len(methodology) >= 1

    def test_synthesis_methodology_exists(self):
        methodology = _resolve_methodology(EngagementType.SYNTHESIS, None)
        assert len(methodology) >= 1


class TestDomainAwareSources:
    def test_business_domain_gets_news_and_reports(self):
        sources = _resolve_sources("financial_analysis")
        source_types = {s.source_type for s in sources}
        assert "news" in source_types or "industry_reports" in source_types

    def test_technical_domain_gets_tech_docs(self):
        sources = _resolve_sources("technology_architecture")
        source_types = {s.source_type for s in sources}
        assert "technical_documentation" in source_types

    def test_scientific_domain_gets_academic(self):
        sources = _resolve_sources("scientific_research")
        source_types = {s.source_type for s in sources}
        assert "academic" in source_types
        assert sources[0].minimum_count >= 5

    def test_unknown_domain_gets_generic(self):
        sources = _resolve_sources(None)
        source_types = {s.source_type for s in sources}
        assert "web" in source_types


class TestResearchSpecDomain:
    def test_research_spec_accepts_domain(self):
        spec = ResearchSpec(
            engagement_id="eng_test",
            client_id="client_test",
            title="Test",
            created_at=datetime.now(UTC),
            specification_version=1,
            decision_context="Test context",
            surprising_finding="Test finding",
            questions=[ResearchQuestion(question="Test?", is_primary=True)],
            output_format="markdown",
            engagement_type=EngagementType.DESIGN,
            domain="technology_architecture",
        )
        assert spec.domain == "technology_architecture"

    def test_research_spec_domain_defaults_to_none(self):
        spec = ResearchSpec(
            engagement_id="eng_test",
            client_id="client_test",
            title="Test",
            created_at=datetime.now(UTC),
            specification_version=1,
            decision_context="Test context",
            surprising_finding="Test finding",
            questions=[ResearchQuestion(question="Test?", is_primary=True)],
            output_format="markdown",
            engagement_type=EngagementType.EVALUATIVE,
        )
        assert spec.domain is None


class TestTechnicalResearcherTemplate:
    def test_template_exists(self):
        registry = TemplateRegistry()
        templates = registry.get_seed_templates()
        names = [t.name for t in templates]
        assert "technical_researcher" in names

    def test_no_edgar_in_technical_researcher(self):
        registry = TemplateRegistry()
        templates = registry.get_seed_templates()
        tech = next(t for t in templates if t.name == "technical_researcher")
        assert ToolName.EDGAR_FILINGS not in tech.tools
        assert ToolName.FINNHUB_MARKET not in tech.tools

    def test_no_edgar_in_academic_researcher(self):
        registry = TemplateRegistry()
        templates = registry.get_seed_templates()
        acad = next(t for t in templates if t.name == "academic_researcher")
        assert ToolName.EDGAR_FILINGS not in acad.tools

    def test_no_edgar_in_generalist(self):
        registry = TemplateRegistry()
        templates = registry.get_seed_templates()
        gen = next(t for t in templates if t.name == "generalist_researcher")
        assert ToolName.EDGAR_FILINGS not in gen.tools
        assert ToolName.FINNHUB_MARKET not in gen.tools

    def test_no_edgar_in_contrarian(self):
        registry = TemplateRegistry()
        templates = registry.get_seed_templates()
        con = next(t for t in templates if t.name == "contrarian_analyst")
        assert ToolName.EDGAR_FILINGS not in con.tools
        assert ToolName.FINNHUB_MARKET not in con.tools

    def test_no_edgar_in_historical(self):
        registry = TemplateRegistry()
        templates = registry.get_seed_templates()
        hist = next(t for t in templates if t.name == "historical_analyst")
        assert ToolName.EDGAR_FILINGS not in hist.tools
        assert ToolName.FINNHUB_MARKET not in hist.tools

    def test_edgar_preserved_in_financial_templates(self):
        registry = TemplateRegistry()
        templates = registry.get_seed_templates()
        quant = next(t for t in templates if t.name == "quantitative_analyst")
        market = next(t for t in templates if t.name == "market_researcher")
        reg = next(t for t in templates if t.name == "regulatory_analyst")
        assert ToolName.EDGAR_FILINGS in quant.tools
        assert ToolName.EDGAR_FILINGS in market.tools
        assert ToolName.EDGAR_FILINGS in reg.tools


class TestEngagementTypeFitCompleteness:
    def test_all_engagement_types_have_fit_entries(self):
        registry = TemplateRegistry()
        task = ResearchTask(
            id="task_001",
            engagement_id="eng_test",
            client_id="client_test",
            category=TaskCategory.STRATEGIC_POSITIONING,
            type=TaskType.ESTIMATIVE,
            target_decision_usefulness=3,
            description="Test",
            acceptance_criteria=["Test"],
            deliverable_destination="Section 1",
            priority=1,
            anti_confirmatory_framing=(
                "Evaluate whether this is the case, including evidence both for and against"
            ),
            assigned_tools=["exa_search", "brave_search", "paper_search"],
            assigned_model=ModelTier.STANDARD,
            end_product="Analysis",
        )
        for et in EngagementType:
            result = registry.match(task, et)
            assert result.similarity >= 0.0

    def test_design_favors_technical_researcher(self):
        registry = TemplateRegistry()
        task = ResearchTask(
            id="task_001",
            engagement_id="eng_test",
            client_id="client_test",
            category=TaskCategory.TECHNOLOGY_ASSESSMENT,
            type=TaskType.ESTIMATIVE,
            target_decision_usefulness=3,
            description="Design the system architecture",
            acceptance_criteria=["Test"],
            deliverable_destination="Section 1",
            priority=1,
            anti_confirmatory_framing=(
                "Evaluate whether this is the case, including evidence both for and against"
            ),
            assigned_tools=["exa_search", "brave_search", "paper_search"],
            assigned_model=ModelTier.STANDARD,
            end_product="Architecture specification",
        )
        result = registry.match(task, EngagementType.DESIGN)
        assert result.template.name == "technical_researcher"


class TestResolveCategoryGraceful:
    def _make_generator(self):
        async def llm(prompt: str) -> str:
            return "{}"

        return TaskGenerator(llm, TemplateRegistry())

    def test_known_category_passes_through(self):
        gen = self._make_generator()
        assert gen._resolve_category("market_sizing") == TaskCategory.MARKET_SIZING

    def test_tech_keyword_maps_to_technology_assessment(self):
        gen = self._make_generator()
        assert gen._resolve_category("architecture_design") == TaskCategory.TECHNOLOGY_ASSESSMENT

    def test_software_keyword_maps_to_technology_assessment(self):
        gen = self._make_generator()
        assert gen._resolve_category("software_evaluation") == TaskCategory.TECHNOLOGY_ASSESSMENT

    def test_financial_keyword_maps_to_financial(self):
        gen = self._make_generator()
        assert gen._resolve_category("revenue_analysis") == TaskCategory.FINANCIAL_ANALYSIS

    def test_regulatory_keyword_maps_to_regulatory(self):
        gen = self._make_generator()
        assert gen._resolve_category("compliance_review") == TaskCategory.REGULATORY

    def test_unknown_falls_back_to_strategic(self):
        gen = self._make_generator()
        assert gen._resolve_category("something_novel") == TaskCategory.STRATEGIC_POSITIONING

    def test_market_keyword_maps_to_market_sizing(self):
        gen = self._make_generator()
        assert gen._resolve_category("tam_estimation") == TaskCategory.MARKET_SIZING

    def test_competitive_keyword_maps_to_competitive(self):
        gen = self._make_generator()
        assert gen._resolve_category("competitive_analysis") == TaskCategory.COMPETITIVE_LANDSCAPE


class TestFrameworkSelectorDomainAware:
    def test_evaluative_business_gets_porters(self):
        hints = frameworks_for_engagement(EngagementType.EVALUATIVE, domain="business_strategy")
        frameworks = [h.framework for h in hints]
        assert AnalyticalFramework.PORTERS_FIVE_FORCES in frameworks

    def test_evaluative_technical_gets_tradeoff(self):
        hints = frameworks_for_engagement(
            EngagementType.EVALUATIVE, domain="technology_architecture"
        )
        frameworks = [h.framework for h in hints]
        assert AnalyticalFramework.TRADE_OFF_ANALYSIS in frameworks
        assert AnalyticalFramework.PORTERS_FIVE_FORCES not in frameworks

    def test_strategic_technical_avoids_swot(self):
        hints = frameworks_for_engagement(EngagementType.STRATEGIC, domain="technical_evaluation")
        frameworks = [h.framework for h in hints]
        assert AnalyticalFramework.SWOT not in frameworks
        assert AnalyticalFramework.TRADE_OFF_ANALYSIS in frameworks

    def test_design_gets_tradeoff(self):
        fw = primary_framework(EngagementType.DESIGN)
        assert fw == AnalyticalFramework.TRADE_OFF_ANALYSIS

    def test_synthesis_gets_systematic_review(self):
        fw = primary_framework(EngagementType.SYNTHESIS)
        assert fw == AnalyticalFramework.SYSTEMATIC_REVIEW

    def test_override_takes_precedence_over_domain(self):
        from keystone.models.structuring import FrameworkHint

        override = [
            FrameworkHint(
                framework=AnalyticalFramework.SWOT,
                rationale="Custom override",
                mandatory=True,
            )
        ]
        hints = frameworks_for_engagement(
            EngagementType.EVALUATIVE,
            override=override,
            domain="technology_architecture",
        )
        assert len(hints) == 1
        assert hints[0].framework == AnalyticalFramework.SWOT

    def test_none_domain_uses_default(self):
        hints = frameworks_for_engagement(EngagementType.EVALUATIVE, domain=None)
        frameworks = [h.framework for h in hints]
        assert AnalyticalFramework.PORTERS_FIVE_FORCES in frameworks


class TestQualityBarDefault:
    def test_quality_bar_is_domain_neutral(self):
        spec = ResearchSpec(
            engagement_id="eng_test",
            client_id="client_test",
            title="Test",
            created_at=datetime.now(UTC),
            specification_version=1,
            decision_context="Test context",
            surprising_finding="Test finding",
            questions=[ResearchQuestion(question="Test?", is_primary=True)],
            output_format="markdown",
            engagement_type=EngagementType.EVALUATIVE,
        )
        assert "Goldman" not in spec.quality_bar
        assert "Expert-grade" in spec.quality_bar
