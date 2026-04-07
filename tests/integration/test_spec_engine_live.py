"""L0 Specification Engine -- Real LLM Pressure Test (Wave 4a, Session 9).

Calls REAL GPT-5.4 via Codex OAuth. Every test makes live API calls.
Run with: pytest tests/integration/test_spec_engine_live.py -v -m integration -s

Diagnostic goal: find what breaks when mocks are replaced with real LLMs.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any

import pytest
from dotenv import load_dotenv

from keystone.events import (
    AgentDispatched,
    AnyPipelineEvent,
    SpecificationGenerated,
    TasksDecomposed,
)
from keystone.llm_client import _client_cache, get_llm_for_tier
from keystone.models.config import AppConfig
from keystone.models.research import EngagementSpec, EngagementType
from keystone.models.tasks import ModelTier, ResearchTask, TaskDecomposition
from keystone.specification._prompts import extract_json, load_prompt
from keystone.specification.decomposer import IssueTree
from keystone.specification.engagement_classifier import (
    ClassificationResult,
    EngagementClassifier,
)
from keystone.specification.intent_clarifier import IntentClarifier
from keystone.specification.spec_engine import SpecificationEngine

# Load .env so OPENAI_AUTH_TYPE and CODEX_AUTH_FILE are in os.environ
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

pytestmark = pytest.mark.integration

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Metrics tracking
# ---------------------------------------------------------------------------

_metrics: dict[str, Any] = {
    "total_llm_calls": 0,
    "total_elapsed_seconds": 0.0,
    "tests": {},
}


def _record(test_name: str, llm_calls: int, elapsed: float, extra: dict | None = None):
    """Record metrics for a test."""
    _metrics["total_llm_calls"] += llm_calls
    _metrics["total_elapsed_seconds"] += elapsed
    entry = {"llm_calls": llm_calls, "elapsed_s": round(elapsed, 2)}
    if extra:
        entry.update(extra)
    _metrics["tests"][test_name] = entry


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _fresh_client():
    _client_cache.clear()
    yield
    _client_cache.clear()


@pytest.fixture()
def config() -> AppConfig:
    return AppConfig()


@pytest.fixture()
def llm(config: AppConfig):
    """Return a FLAGSHIP-tier LLM callable for direct sub-component tests."""
    return get_llm_for_tier(ModelTier.FLAGSHIP, config)


@pytest.fixture()
def engine(llm) -> SpecificationEngine:
    """Return a SpecificationEngine wired to the real LLM."""
    return SpecificationEngine(llm=llm)


AV_SENSOR_QUESTION = (
    "Estimate the total addressable market for Level 4+ autonomous vehicle "
    "sensors in North America through 2030"
)

SIZING_QUESTION = (
    "What is the market size for electric vehicle charging infrastructure "
    "in the US, segmented by Level 2 vs DC fast charging?"
)

DIAGNOSTIC_QUESTION = (
    "Why has employee turnover at mid-size SaaS companies increased 30% "
    "since 2024, and what interventions are most cost-effective?"
)

STRATEGIC_QUESTION = (
    "Should a regional auto body shop chain expand into the Dallas-Fort "
    "Worth metropolitan area given current competitive dynamics?"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _collect_events(engine: SpecificationEngine, question: str) -> list[AnyPipelineEvent]:
    """Run the full spec engine and collect all events."""
    events: list[AnyPipelineEvent] = []
    async for event in engine.generate_spec(
        question=question,
        client_id="test_client",
        client_context="Pressure test -- Wave 4a Session 9",
    ):
        events.append(event)
    return events


def _get_spec(engine: SpecificationEngine) -> EngagementSpec:
    """Synchronously retrieve the spec (call after generate_spec completes)."""
    return asyncio.get_event_loop().run_until_complete(engine.get_spec())


# =========================================================================
# 1. BASIC FUNCTIONALITY -- AV Sensor TAM question
# =========================================================================


_basic_spec: EngagementSpec | None = None
_basic_events: list[AnyPipelineEvent] = []
_basic_elapsed: float = 0.0


async def _ensure_basic_pipeline_ran(config: AppConfig):
    """Run the full pipeline exactly once (module-level cache)."""
    global _basic_spec, _basic_events, _basic_elapsed
    if _basic_spec is not None:
        return
    llm = get_llm_for_tier(ModelTier.FLAGSHIP, config)
    engine = SpecificationEngine(llm=llm)
    start = time.monotonic()
    _basic_events = await _collect_events(engine, AV_SENSOR_QUESTION)
    _basic_spec = await engine.get_spec()
    _basic_elapsed = time.monotonic() - start
    _record("basic_functionality", llm_calls=9, elapsed=_basic_elapsed,
            extra={"task_count": len(_basic_spec.task_decomposition.tasks)})


class TestBasicFunctionality:
    """Full pipeline run with the AV sensor question (runs once, shared)."""

    @pytest.fixture(autouse=True)
    async def _run_pipeline(self, config):
        await _ensure_basic_pipeline_ran(config)

    async def test_engagement_spec_produced(self):
        assert _basic_spec is not None
        assert isinstance(_basic_spec, EngagementSpec)

    async def test_research_spec_fields_populated(self):
        rs = _basic_spec.research_spec
        assert rs.engagement_id.startswith("eng_")
        assert rs.client_id == "test_client"
        assert rs.title
        assert rs.decision_context
        assert rs.surprising_finding
        assert len(rs.questions) >= 1
        assert rs.engagement_type in EngagementType
        assert rs.day_1_hypothesis

    async def test_task_count_in_range(self):
        tasks = _basic_spec.task_decomposition.tasks
        print(f"\n  Task count: {len(tasks)}")
        assert 15 <= len(tasks) <= 50, f"Expected 15-50 tasks, got {len(tasks)}"

    async def test_dag_validation_passes(self):
        """TaskDecomposition model_validator already runs Kahn's algo; if we got
        here without ValidationError the DAG is acyclic with no dangling refs."""
        td = _basic_spec.task_decomposition
        assert isinstance(td, TaskDecomposition)
        task_ids = {t.id for t in td.tasks}
        for t in td.tasks:
            for dep in t.dependencies:
                assert dep in task_ids, f"Dangling dependency: {t.id} -> {dep}"

    async def test_every_task_has_3_to_5_tools(self):
        for t in _basic_spec.task_decomposition.tasks:
            assert 3 <= len(t.assigned_tools) <= 5, (
                f"Task {t.id} has {len(t.assigned_tools)} tools: {t.assigned_tools}"
            )

    async def test_every_task_has_anti_confirmatory_framing(self):
        for t in _basic_spec.task_decomposition.tasks:
            assert t.anti_confirmatory_framing, f"Task {t.id} missing anti-confirmatory framing"
            lower = t.anti_confirmatory_framing.lower()
            for bad_start in ["find evidence for", "prove that", "confirm that", "show that"]:
                assert not lower.startswith(bad_start), (
                    f"Task {t.id} has confirmatory framing: {t.anti_confirmatory_framing[:80]}"
                )

    async def test_every_task_has_acceptance_criteria(self):
        for t in _basic_spec.task_decomposition.tasks:
            assert t.acceptance_criteria, f"Task {t.id} missing acceptance_criteria"
            assert len(t.acceptance_criteria) >= 1

    async def test_issue_tree_present_and_deep(self):
        tree = _basic_spec.issue_tree
        assert tree is not None
        root = tree.get("root", tree)
        assert "children" in root or "name" in root
        # Check at least 2 levels of depth
        children = root.get("children", [])
        assert len(children) >= 2, f"Issue tree too shallow: {len(children)} top-level branches"
        has_grandchildren = any(c.get("children") for c in children)
        assert has_grandchildren, "Issue tree lacks 2nd level of depth"

    async def test_events_emitted(self):
        event_types = {type(e).__name__ for e in _basic_events}
        assert "SpecificationGenerated" in event_types
        assert "TasksDecomposed" in event_types
        assert "AgentDispatched" in event_types
        # Should have one AgentDispatched per task
        dispatched = [e for e in _basic_events if isinstance(e, AgentDispatched)]
        assert len(dispatched) == len(_basic_spec.task_decomposition.tasks)

    async def test_pipeline_timing(self):
        print(f"\n  Full pipeline elapsed: {_basic_elapsed:.1f}s")
        # Warn but don't fail if very slow
        if _basic_elapsed > 120:
            logger.warning("Pipeline took over 2 minutes: %.1fs", _basic_elapsed)


# =========================================================================
# 2. ENGAGEMENT TYPE COVERAGE
# =========================================================================


class TestEngagementTypeRouting:
    """Verify the classifier routes questions to correct engagement types."""

    @pytest.fixture()
    def classifier(self, llm):
        return EngagementClassifier(llm)

    async def test_sizing_question(self, classifier):
        start = time.monotonic()
        async with asyncio.timeout(60):
            result = await classifier.classify(SIZING_QUESTION)
        elapsed = time.monotonic() - start
        _record("classify_sizing", 1, elapsed, {"type": result.engagement_type.value})

        print(f"\n  Type: {result.engagement_type}, Confidence: {result.confidence}")
        assert result.engagement_type == EngagementType.SIZING, (
            f"Expected SIZING, got {result.engagement_type}: {result.reasoning}"
        )
        assert result.confidence > 0.5

    async def test_diagnostic_question(self, classifier):
        start = time.monotonic()
        async with asyncio.timeout(60):
            result = await classifier.classify(DIAGNOSTIC_QUESTION)
        elapsed = time.monotonic() - start
        _record("classify_diagnostic", 1, elapsed, {"type": result.engagement_type.value})

        print(f"\n  Type: {result.engagement_type}, Confidence: {result.confidence}")
        assert result.engagement_type == EngagementType.DIAGNOSTIC, (
            f"Expected DIAGNOSTIC, got {result.engagement_type}: {result.reasoning}"
        )

    async def test_strategic_question(self, classifier):
        start = time.monotonic()
        async with asyncio.timeout(60):
            result = await classifier.classify(STRATEGIC_QUESTION)
        elapsed = time.monotonic() - start
        _record("classify_strategic", 1, elapsed, {"type": result.engagement_type.value})

        print(f"\n  Type: {result.engagement_type}, Confidence: {result.confidence}")
        assert result.engagement_type == EngagementType.STRATEGIC, (
            f"Expected STRATEGIC, got {result.engagement_type}: {result.reasoning}"
        )


# =========================================================================
# 3. JSON PARSING ROBUSTNESS -- per-prompt verification
# =========================================================================


class TestJSONParsingRobustness:
    """For each LLM call, capture raw output and verify JSON validity."""

    async def test_classification_json(self, llm):
        prompt = load_prompt(
            "classification",
            question=AV_SENSOR_QUESTION,
            client_context="No additional context provided.",
        )
        start = time.monotonic()
        async with asyncio.timeout(60):
            raw = await llm(prompt)
        elapsed = time.monotonic() - start
        _record("json_classification", 1, elapsed)

        self._verify_json(raw, ["engagement_type", "pipeline_profile", "confidence", "reasoning"])

    async def test_intent_clarification_json(self, llm):
        prompt = load_prompt(
            "intent_clarification",
            question=AV_SENSOR_QUESTION,
            engagement_type="sizing",
            client_context="No additional context provided.",
            constraints="None specified.",
        )
        start = time.monotonic()
        async with asyncio.timeout(60):
            raw = await llm(prompt)
        elapsed = time.monotonic() - start
        _record("json_intent", 1, elapsed)

        self._verify_json(
            raw,
            ["day_1_hypothesis", "intent_clear", "unstated_constraints",
             "scope_boundaries", "decision_context", "surprising_finding"],
        )

    async def test_decompose_market_lens_json(self, llm):
        prompt = load_prompt(
            "decompose_market_lens",
            question=AV_SENSOR_QUESTION,
            engagement_type="sizing",
            day_1_hypothesis="The L4+ AV sensor TAM in NA will reach $15-20B by 2030.",
            client_context="No additional context provided.",
        )
        start = time.monotonic()
        async with asyncio.timeout(60):
            raw = await llm(prompt)
        elapsed = time.monotonic() - start
        _record("json_market_lens", 1, elapsed)

        data = self._verify_json(raw, ["id", "name", "description", "children"])
        assert data["id"].startswith("mkt_"), f"Expected mkt_ prefix, got: {data['id']}"

    async def test_decompose_financial_lens_json(self, llm):
        prompt = load_prompt(
            "decompose_financial_lens",
            question=AV_SENSOR_QUESTION,
            engagement_type="sizing",
            day_1_hypothesis="The L4+ AV sensor TAM in NA will reach $15-20B by 2030.",
            client_context="No additional context provided.",
        )
        start = time.monotonic()
        async with asyncio.timeout(60):
            raw = await llm(prompt)
        elapsed = time.monotonic() - start
        _record("json_financial_lens", 1, elapsed)

        data = self._verify_json(raw, ["id", "name", "description", "children"])
        assert data["id"].startswith("fin_"), f"Expected fin_ prefix, got: {data['id']}"

    async def test_decompose_operational_lens_json(self, llm):
        prompt = load_prompt(
            "decompose_operational_lens",
            question=AV_SENSOR_QUESTION,
            engagement_type="sizing",
            day_1_hypothesis="The L4+ AV sensor TAM in NA will reach $15-20B by 2030.",
            client_context="No additional context provided.",
        )
        start = time.monotonic()
        async with asyncio.timeout(60):
            raw = await llm(prompt)
        elapsed = time.monotonic() - start
        _record("json_operational_lens", 1, elapsed)

        data = self._verify_json(raw, ["id", "name", "description", "children"])
        assert data["id"].startswith("ops_"), f"Expected ops_ prefix, got: {data['id']}"

    async def test_mece_validation_json(self, llm):
        # Provide a minimal synthetic tree to test the validation prompt
        synthetic_tree = {
            "root": {
                "id": "root", "name": "AV Sensor TAM",
                "description": "Issue tree", "children": [
                    {"id": "b1", "name": "Market Size", "description": "TAM estimation",
                     "lens_annotations": {}, "children": [
                         {"id": "b1.1", "name": "Current market", "description": "2024 baseline",
                          "lens_annotations": {}, "children": []},
                         {"id": "b1.2", "name": "Growth drivers", "description": "CAGR factors",
                          "lens_annotations": {}, "children": []},
                     ]},
                    {"id": "b2", "name": "Supply Chain", "description": "Key players",
                     "lens_annotations": {}, "children": [
                         {"id": "b2.1", "name": "Lidar", "description": "Lidar manufacturers",
                          "lens_annotations": {}, "children": []},
                     ]},
                ],
                "lens_annotations": {},
            },
            "metadata": {"depth": 2, "leaf_count": 3, "lenses_used": ["market"],
                         "synthesis_rationale": "test"},
        }
        prompt = load_prompt(
            "mece_validation",
            question=AV_SENSOR_QUESTION,
            engagement_type="sizing",
            issue_tree=json.dumps(synthetic_tree, indent=2),
            leaf_count="3",
            depth="2",
        )
        start = time.monotonic()
        async with asyncio.timeout(60):
            raw = await llm(prompt)
        elapsed = time.monotonic() - start
        _record("json_mece_validation", 1, elapsed)

        data = self._verify_json(raw, ["dimensions", "feedback"])
        dims = data["dimensions"]
        for expected_dim in [
            "mutual_exclusivity", "collective_exhaustiveness",
            "tailoring", "actionability", "depth_appropriateness",
        ]:
            assert expected_dim in dims, f"Missing dimension: {expected_dim}"

    async def test_priority_scoring_json(self, llm):
        leaves = [
            {"id": "b1.1", "name": "Current AV sensor market size", "description": "2024 baseline"},
            {"id": "b1.2", "name": "Growth drivers for AV sensors", "description": "CAGR factors"},
        ]
        prompt = load_prompt(
            "priority_scoring",
            day_1_hypothesis="The L4+ AV sensor TAM in NA will reach $15-20B by 2030.",
            engagement_type="sizing",
            leaves=json.dumps(leaves, indent=2),
        )
        start = time.monotonic()
        async with asyncio.timeout(60):
            raw = await llm(prompt)
        elapsed = time.monotonic() - start
        _record("json_priority_scoring", 1, elapsed)

        data = self._verify_json(raw, ["scores"])
        assert len(data["scores"]) == 2, f"Expected 2 scores, got {len(data['scores'])}"
        for score in data["scores"]:
            assert "branch_id" in score
            assert "decision_relevance" in score
            assert "uncertainty_reduction" in score
            assert 0.0 <= score["decision_relevance"] <= 1.0
            assert 0.0 <= score["uncertainty_reduction"] <= 1.0

    async def test_xml_tags_not_echoed(self, llm):
        """Verify the model doesn't echo <analytical_contract> or <completeness_check>
        tags back in its output."""
        prompt = load_prompt(
            "classification",
            question=AV_SENSOR_QUESTION,
            client_context="No additional context provided.",
        )
        async with asyncio.timeout(60):
            raw = await llm(prompt)
        if "<analytical_contract>" in raw:
            logger.warning("Model echoed <analytical_contract> tag in output")
        if "<completeness_check>" in raw:
            logger.warning("Model echoed <completeness_check> tag in output")
        # Not a hard failure, but log it
        print(f"\n  XML tags in output: "
              f"analytical_contract={'<analytical_contract>' in raw}, "
              f"completeness_check={'<completeness_check>' in raw}")

    def _verify_json(self, raw: str, expected_keys: list[str]) -> dict:
        """Verify raw LLM output contains valid JSON with expected keys."""
        assert raw, "Empty LLM response"
        # Check for truncation
        stripped = raw.rstrip()
        if not stripped.endswith("}") and not stripped.endswith("]"):
            logger.warning("Response may be truncated (doesn't end with } or ]): ...%s", stripped[-50:])

        data = extract_json(raw)
        for key in expected_keys:
            assert key in data, f"Missing expected key '{key}' in JSON. Keys present: {list(data.keys())}"
        return data


# =========================================================================
# 4. EDGE CASES
# =========================================================================


class TestEdgeCases:
    """Edge case inputs that stress the pipeline."""

    async def test_very_short_question(self, engine):
        """Minimal input: 'Analyze Tesla'"""
        start = time.monotonic()
        async with asyncio.timeout(300):
            events = await _collect_events(engine, "Analyze Tesla")
        spec = await engine.get_spec()
        elapsed = time.monotonic() - start
        _record("edge_short", 9, elapsed, {"task_count": len(spec.task_decomposition.tasks)})

        assert spec is not None
        print(f"\n  Short question: {len(spec.task_decomposition.tasks)} tasks, {elapsed:.1f}s")
        # Even a vague question should produce a valid spec
        assert spec.research_spec.engagement_type in EngagementType

    async def test_very_long_question(self, engine):
        """500+ word question with detailed context."""
        long_question = (
            "We are a mid-market private equity firm evaluating a potential acquisition "
            "of SensorTech Corp, a manufacturer of lidar and radar sensor modules "
            "primarily serving the autonomous vehicle industry. SensorTech has $180M in "
            "annual revenue (FY2025), EBITDA margins of 22%, and holds 47 patents across "
            "solid-state lidar, FMCW radar, and sensor fusion algorithms. They have "
            "supply agreements with three of the top ten autonomous vehicle programs "
            "including Waymo, Cruise, and Aurora. However, we have concerns about: "
            "(1) the timeline for L4 autonomy reaching mass-market adoption, which "
            "directly impacts their addressable market, (2) competitive pressure from "
            "vertically integrated players like Tesla who are developing proprietary "
            "sensor stacks, (3) the sustainability of their margins given increasing "
            "commoditization of lidar components, and (4) regulatory uncertainty around "
            "autonomous vehicle certification requirements across different US states "
            "and the EU. We need to understand the total addressable market for L4+ "
            "autonomous vehicle sensors in North America through 2030, segmented by "
            "sensor type (lidar, radar, camera, ultrasonic), by application tier "
            "(passenger vehicles, commercial trucking, robotaxis, last-mile delivery), "
            "and by geographic concentration. We also need a competitive landscape "
            "analysis showing market share, technology differentiation, and strategic "
            "partnerships for the top 15 players. Finally, we need a financial model "
            "showing SensorTech's addressable market share under three scenarios: "
            "base case (current trajectory), bull case (accelerated L4 adoption), and "
            "bear case (delayed adoption + increased competition). The investment "
            "committee meets on 2026-06-15 and needs this analysis by 2026-05-30."
        )
        start = time.monotonic()
        async with asyncio.timeout(300):
            events = await _collect_events(engine, long_question)
        spec = await engine.get_spec()
        elapsed = time.monotonic() - start
        _record("edge_long", 9, elapsed, {"task_count": len(spec.task_decomposition.tasks)})

        assert spec is not None
        print(f"\n  Long question: {len(spec.task_decomposition.tasks)} tasks, {elapsed:.1f}s")
        assert len(spec.task_decomposition.tasks) >= 15

    async def test_ambiguous_question(self, engine):
        """Vague, ambiguous question."""
        start = time.monotonic()
        async with asyncio.timeout(300):
            events = await _collect_events(engine, "What should we do about the market?")
        spec = await engine.get_spec()
        elapsed = time.monotonic() - start
        _record("edge_ambiguous", 9, elapsed)

        assert spec is not None
        print(f"\n  Ambiguous question: type={spec.research_spec.engagement_type}, "
              f"tasks={len(spec.task_decomposition.tasks)}, {elapsed:.1f}s")

    async def test_non_english_terms(self, engine):
        """Question with non-English specialized terms."""
        start = time.monotonic()
        async with asyncio.timeout(300):
            events = await _collect_events(
                engine,
                "Analyze the Mittelstand companies' approach to Industry 4.0 "
                "adoption and its impact on their competitiveness in global markets",
            )
        spec = await engine.get_spec()
        elapsed = time.monotonic() - start
        _record("edge_non_english", 9, elapsed)

        assert spec is not None
        print(f"\n  Non-English terms: type={spec.research_spec.engagement_type}, "
              f"tasks={len(spec.task_decomposition.tasks)}, {elapsed:.1f}s")


# =========================================================================
# 5. CONSISTENCY -- run same question twice
# =========================================================================


class TestConsistency:
    """Run the basic AV sensor question twice and compare outputs."""

    async def test_classification_consistency(self, llm):
        """Same question should classify to the same type."""
        classifier = EngagementClassifier(llm)

        start = time.monotonic()
        async with asyncio.timeout(60):
            r1 = await classifier.classify(AV_SENSOR_QUESTION)
        async with asyncio.timeout(60):
            r2 = await classifier.classify(AV_SENSOR_QUESTION)
        elapsed = time.monotonic() - start
        _record("consistency_classification", 2, elapsed)

        print(f"\n  Run 1: {r1.engagement_type} (conf={r1.confidence:.2f})")
        print(f"  Run 2: {r2.engagement_type} (conf={r2.confidence:.2f})")
        assert r1.engagement_type == r2.engagement_type, (
            f"Classification inconsistency: {r1.engagement_type} vs {r2.engagement_type}"
        )

    async def test_intent_consistency(self, llm):
        """Day-1 hypotheses should be thematically similar."""
        clarifier = IntentClarifier(llm)

        start = time.monotonic()
        async with asyncio.timeout(120):
            r1 = await clarifier.clarify(AV_SENSOR_QUESTION, EngagementType.SIZING)
        async with asyncio.timeout(120):
            r2 = await clarifier.clarify(AV_SENSOR_QUESTION, EngagementType.SIZING)
        elapsed = time.monotonic() - start
        _record("consistency_intent", 2, elapsed)

        print(f"\n  Hypothesis 1: {r1.day_1_hypothesis[:100]}")
        print(f"  Hypothesis 2: {r2.day_1_hypothesis[:100]}")
        # Both should mention AV sensor domain concepts -- not a strict match
        # Accept domain synonyms: "TAM" = "market", "AV" = "autonomous"
        combined = (r1.day_1_hypothesis + r2.day_1_hypothesis).lower()
        domain_concepts = [
            (["sensor"], "sensor technology"),
            (["vehicle", "av ", "automotive"], "vehicles/AV"),
            (["market", "tam", "revenue", "demand", "billion"], "market/TAM"),
        ]
        for synonyms, concept_name in domain_concepts:
            assert any(s in combined for s in synonyms), (
                f"Neither hypothesis mentions {concept_name} (checked: {synonyms})"
            )


# =========================================================================
# 6. TOKEN / TIMING MEASUREMENT (implicit in all tests via _record)
# =========================================================================


class TestTokenMeasurement:
    """Measure token consumption per operation type."""

    async def test_single_classification_cost(self, llm):
        """Measure a single classification call."""
        prompt = load_prompt(
            "classification",
            question=AV_SENSOR_QUESTION,
            client_context="No additional context provided.",
        )
        prompt_chars = len(prompt)

        start = time.monotonic()
        async with asyncio.timeout(60):
            raw = await llm(prompt)
        elapsed = time.monotonic() - start
        response_chars = len(raw)
        _record("token_classification", 1, elapsed, {
            "prompt_chars": prompt_chars,
            "response_chars": response_chars,
        })

        print(f"\n  Prompt: ~{prompt_chars} chars")
        print(f"  Response: ~{response_chars} chars")
        print(f"  Latency: {elapsed:.2f}s")

    async def test_decomposition_trio_cost(self, llm):
        """Measure the 3 parallel lens decompositions."""
        from keystone.specification.decomposer import Decomposer

        decomposer = Decomposer(llm)
        start = time.monotonic()
        async with asyncio.timeout(300):
            tree = await decomposer.decompose(
                question=AV_SENSOR_QUESTION,
                engagement_type=EngagementType.SIZING,
                day_1_hypothesis="L4+ AV sensor TAM in NA is $15-20B by 2030.",
            )
        elapsed = time.monotonic() - start
        _record("token_decomposition", 4, elapsed, {
            "leaf_count": tree.metadata.leaf_count,
            "depth": tree.metadata.depth,
        })

        print(f"\n  3 lenses + synthesis: {elapsed:.2f}s")
        print(f"  Leaves: {tree.metadata.leaf_count}, Depth: {tree.metadata.depth}")


# =========================================================================
# 7. PROMPT-MODEL FIT -- verify each prompt produces expected format
# =========================================================================


class TestPromptModelFit:
    """Verify GPT-5.4 follows the structural directives in each prompt."""

    async def test_classification_format_compliance(self, llm):
        prompt = load_prompt(
            "classification",
            question=AV_SENSOR_QUESTION,
            client_context="No additional context provided.",
        )
        raw = await llm(prompt)
        data = extract_json(raw)

        # Check all 4 required fields
        assert data["engagement_type"] in ["sizing", "diagnostic", "evaluative", "exploratory", "strategic"]
        assert data["pipeline_profile"] in ["light", "standard", "deep"]
        assert isinstance(data["confidence"], (int, float))
        assert isinstance(data["reasoning"], str)
        assert len(data["reasoning"]) > 50, "Reasoning too short to reference 3 signals"

    async def test_intent_format_compliance(self, llm):
        prompt = load_prompt(
            "intent_clarification",
            question=AV_SENSOR_QUESTION,
            engagement_type="sizing",
            client_context="No additional context provided.",
            constraints="None specified.",
        )
        raw = await llm(prompt)
        data = extract_json(raw)

        assert isinstance(data["day_1_hypothesis"], str)
        assert isinstance(data["intent_clear"], bool)
        assert isinstance(data["unstated_constraints"], list)
        assert len(data["unstated_constraints"]) >= 2
        assert isinstance(data["scope_boundaries"], list)
        assert len(data["scope_boundaries"]) >= 2

    async def test_synthesis_format_compliance(self, llm):
        """Verify the synthesis prompt produces root + synthesis_rationale."""
        # First generate 3 lens trees
        from keystone.specification.decomposer import Decomposer

        decomposer = Decomposer(llm)
        tree = await decomposer.decompose(
            question=AV_SENSOR_QUESTION,
            engagement_type=EngagementType.SIZING,
            day_1_hypothesis="L4+ AV sensor TAM in NA is $15-20B by 2030.",
        )

        # The tree should have root and metadata
        assert tree.root is not None
        assert tree.root.id
        assert tree.root.children, "Root has no children"
        assert tree.metadata.leaf_count >= 8, (
            f"Too few leaves: {tree.metadata.leaf_count} (expected 8-20)"
        )
        assert tree.metadata.leaf_count <= 20, (
            f"Too many leaves: {tree.metadata.leaf_count} (expected 8-20)"
        )

    async def test_completeness_checklist_fields_produced(self, llm):
        """Run classification and verify every field from the completeness_check
        section is actually in the response."""
        prompt = load_prompt(
            "classification",
            question=DIAGNOSTIC_QUESTION,
            client_context="No additional context provided.",
        )
        raw = await llm(prompt)
        data = extract_json(raw)

        checklist = ["engagement_type", "pipeline_profile", "confidence", "reasoning"]
        missing = [k for k in checklist if k not in data]
        assert not missing, f"Missing completeness checklist fields: {missing}"


# =========================================================================
# ADDITIONAL TESTS (beyond baseline)
# =========================================================================


class TestMarkdownWrappedJSON:
    """Probe whether the model wraps JSON in markdown fences and whether
    extract_json handles it correctly."""

    async def test_extract_json_handles_fenced_output(self, llm):
        """Intentionally ask for JSON output and verify extract_json works
        regardless of whether the model uses fences."""
        prompt = (
            "Return a JSON object with exactly two keys: "
            '"name" (value: "test") and "count" (value: 42). '
            "Return ONLY the JSON, no other text."
        )
        async with asyncio.timeout(60):
            raw = await llm(prompt)
        print(f"\n  Raw output starts with: {raw[:50]!r}")
        has_fences = "```" in raw
        print(f"  Has markdown fences: {has_fences}")

        data = extract_json(raw)
        assert data["name"] == "test"
        assert data["count"] == 42


class TestTaskQuality:
    """Verify generated tasks are specific, not generic. Uses shared pipeline result."""

    @pytest.fixture(autouse=True)
    async def _ensure_pipeline(self, config):
        await _ensure_basic_pipeline_ran(config)

    async def test_task_descriptions_are_specific(self):
        """Tasks should reference specifics from the question, not be generic."""
        generic_phrases = [
            "research the market",
            "analyze the industry",
            "gather data",
            "collect information",
            "study the topic",
        ]
        generic_count = 0
        for t in _basic_spec.task_decomposition.tasks:
            desc_lower = t.description.lower()
            if any(phrase in desc_lower for phrase in generic_phrases):
                generic_count += 1
                logger.warning("Generic task: %s -- %s", t.id, t.description[:80])

        total = len(_basic_spec.task_decomposition.tasks)
        generic_pct = generic_count / total if total > 0 else 0
        print(f"\n  Generic tasks: {generic_count}/{total} ({generic_pct:.0%})")
        assert generic_pct < 0.3, f"Too many generic tasks: {generic_count}/{total}"

    async def test_no_duplicate_tasks(self):
        """No two tasks should have identical descriptions."""
        descriptions = [t.description for t in _basic_spec.task_decomposition.tasks]
        unique = set(descriptions)
        dupes = len(descriptions) - len(unique)
        print(f"\n  Tasks: {len(descriptions)}, Unique: {len(unique)}, Dupes: {dupes}")
        assert dupes == 0, f"Found {dupes} duplicate task descriptions"


class TestCommentaryAfterJSON:
    """Verify extract_json handles cases where the model adds commentary
    after the JSON block."""

    async def test_extract_json_ignores_trailing_text(self):
        """Synthetic test: JSON followed by commentary."""
        raw_with_commentary = '{"key": "value"}\n\nHere is some additional commentary.'
        data = extract_json(raw_with_commentary)
        assert data["key"] == "value"

    async def test_extract_json_handles_leading_text(self):
        """Synthetic test: commentary before JSON."""
        raw_with_leading = 'Here is the result:\n\n{"key": "value"}'
        data = extract_json(raw_with_leading)
        assert data["key"] == "value"

    async def test_extract_json_handles_nested_braces(self):
        """Synthetic test: nested JSON objects."""
        raw = '{"outer": {"inner": "value"}, "list": [1, 2, 3]}'
        data = extract_json(raw)
        assert data["outer"]["inner"] == "value"
        assert data["list"] == [1, 2, 3]


class TestErrorRecoveryInPipeline:
    """Test that the retry mechanisms in the pipeline handle transient issues."""

    async def test_decomposition_retry_on_validation_failure(self, llm):
        """The Decomposer has built-in retry logic for synthesis.
        Verify it produces a valid tree even if an intermediate step is shaky."""
        from keystone.specification.decomposer import Decomposer

        decomposer = Decomposer(llm)
        start = time.monotonic()
        async with asyncio.timeout(180):
            tree = await decomposer.decompose(
                question="What is the impact of tariffs on US semiconductor manufacturing capacity?",
                engagement_type=EngagementType.DIAGNOSTIC,
                day_1_hypothesis="Recent tariffs have accelerated US fab investment but at 2-3x cost.",
            )
        elapsed = time.monotonic() - start

        assert tree.root is not None
        assert tree.metadata.leaf_count >= 3
        print(f"\n  Retry test: {tree.metadata.leaf_count} leaves, {elapsed:.1f}s")


# =========================================================================
# Metrics summary (printed after all tests)
# =========================================================================


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Print metrics summary after all tests complete."""
    terminalreporter.write_sep("=", "SPEC ENGINE PRESSURE TEST METRICS")
    terminalreporter.write_line(f"Total LLM calls: {_metrics['total_llm_calls']}")
    terminalreporter.write_line(f"Total elapsed: {_metrics['total_elapsed_seconds']:.1f}s")
    terminalreporter.write_line("")
    for test_name, data in _metrics.get("tests", {}).items():
        line = f"  {test_name}: {data['elapsed_s']}s, {data['llm_calls']} calls"
        extras = {k: v for k, v in data.items() if k not in ("elapsed_s", "llm_calls")}
        if extras:
            line += f" | {extras}"
        terminalreporter.write_line(line)
