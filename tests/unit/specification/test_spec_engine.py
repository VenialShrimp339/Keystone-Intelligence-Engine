"""Integration tests for the Specification Engine (L0 orchestrator)."""

from __future__ import annotations

import json

import pytest

from keystone.contracts import SpecificationEngineContract
from keystone.events import AgentDispatched, SpecificationGenerated, TasksDecomposed
from keystone.models.research import EngagementSpec, EngagementType
from keystone.specification.spec_engine import SpecificationEngine
from keystone.specification.template_registry import TemplateRegistry


def _make_lens_tree(prefix: str) -> dict:
    children = []
    for i in range(1, 5):
        children.append({
            "id": f"{prefix}_{i}",
            "name": f"{prefix.title()} Branch {i}",
            "description": f"Investigate {prefix} aspect {i}",
            "children": [],
        })
    return {
        "id": f"{prefix}_root",
        "name": f"{prefix.title()} Analysis",
        "description": f"{prefix.title()} lens decomposition",
        "children": children,
    }


def _make_synthesized_tree() -> dict:
    branches = []
    for i in range(1, 4):
        children = []
        for j in range(1, 5):
            children.append({
                "id": f"branch_{i}.{j}",
                "name": f"Sub-topic {i}.{j}",
                "description": f"Investigate sub-topic {i}.{j}",
                "lens_annotations": {},
                "children": [],
            })
        branches.append({
            "id": f"branch_{i}",
            "name": f"Major Branch {i}",
            "description": f"Top-level branch {i}",
            "lens_annotations": {"financial": "Revenue"},
            "children": children,
        })
    return {
        "root": {
            "id": "root",
            "name": "Luminar competitive position",
            "description": "Unified MECE tree",
            "children": branches,
        },
        "synthesis_rationale": "Merged financial, operational, and market lenses.",
    }


def _make_validation_pass() -> dict:
    return {
        "dimensions": {
            "mutual_exclusivity": True,
            "collective_exhaustiveness": True,
            "tailoring": True,
            "actionability": True,
            "depth_appropriateness": True,
        },
        "feedback": {
            "mutual_exclusivity": "Passes.",
            "collective_exhaustiveness": "Passes.",
            "tailoring": "Passes.",
            "actionability": "Passes.",
            "depth_appropriateness": "Passes.",
        },
    }


def _make_priority_scores() -> dict:
    scores = []
    for i in range(1, 4):
        for j in range(1, 5):
            scores.append({
                "branch_id": f"branch_{i}.{j}",
                "decision_relevance": 0.8,
                "uncertainty_reduction": 0.7,
                "reasoning": "Test score.",
            })
    return {"scores": scores}


def _make_tasks() -> dict:
    tasks = []
    for i in range(1, 13):
        tasks.append({
            "id": f"task_{i:03d}",
            "category": ["market_sizing", "competitive_landscape", "financial_analysis",
                         "technology_assessment", "regulatory", "strategic_positioning",
                         "market_sizing", "competitive_landscape", "financial_analysis",
                         "technology_assessment", "regulatory", "strategic_positioning"][i - 1],
            "type": "estimative" if i % 2 == 0 else "current",
            "target_decision_usefulness": 4,
            "description": f"Investigate Luminar topic {i}",
            "required_sources": ["industry_reports", "news"],
            "acceptance_criteria": [f"Criterion {i}"],
            "deliverable_destination": f"Section {i}",
            "priority": i,
            "anti_confirmatory_framing": f"Evaluate whether topic {i} holds, including evidence both for and against",
            "assigned_tools": ["exa_search", "brave_search", "edgar_filings"],
            "assigned_model": "sonnet",
            "end_product": f"Analysis for topic {i}",
            "dependencies": [f"task_{i - 1:03d}"] if i > 3 else [],
            "issue_tree_branch_id": f"branch_{(i - 1) // 4 + 1}.{(i - 1) % 4 + 1}",
            "custom_category": None,
        })
    return {
        "decomposition_rationale": "Structured by issue tree branches for Luminar analysis.",
        "tasks": tasks,
    }


def _make_full_mock_llm():
    """Create a mock LLM that handles all pipeline steps in sequence."""
    call_count = 0

    async def llm(prompt: str) -> str:
        nonlocal call_count
        call_count += 1

        # Step 1: Classification
        if call_count == 1:
            return json.dumps({
                "engagement_type": "strategic",
                "pipeline_profile": "deep",
                "confidence": 0.92,
                "reasoning": "Complex multi-variable strategic question about competitive positioning.",
            })

        # Step 2: Intent clarification
        if call_count == 2:
            return json.dumps({
                "day_1_hypothesis": "Luminar's 1550nm lidar technology lead is sustainable through 2028 due to manufacturing complexity barriers and existing OEM design wins",
                "intent_clear": True,
                "unstated_constraints": ["3-week timeline", "Growth equity fund perspective"],
                "scope_boundaries": ["No investment recommendation", "No DCF valuation"],
                "decision_context": "Growth equity fund evaluating $200M position in LAZR",
                "surprising_finding": "Evidence that Chinese competitors have already closed the technology gap",
            })

        # Steps 3a-3c: Lens decompositions (calls 3, 4, 5)
        if call_count in (3, 4, 5):
            prefix = ["fin", "ops", "mkt"][call_count - 3]
            return json.dumps(_make_lens_tree(prefix))

        # Step 3d: Synthesis (call 6)
        if call_count == 6:
            return json.dumps(_make_synthesized_tree())

        # Step 4: MECE validation (call 7)
        if call_count == 7:
            return json.dumps(_make_validation_pass())

        # Step 5: Priority scoring (call 8)
        if call_count == 8:
            return json.dumps(_make_priority_scores())

        # Step 7: Task generation (call 9)
        if call_count == 9:
            return json.dumps(_make_tasks())

        # Fallback
        return json.dumps({"error": f"Unexpected call {call_count}"})

    return llm


class TestSpecificationEngine:

    async def test_full_pipeline_luminar(self):
        """Full pipeline with Luminar test case (mock all LLM calls)."""
        llm = _make_full_mock_llm()
        engine = SpecificationEngine(llm)

        events = []
        async for event in engine.generate_spec(
            question="Evaluate the competitive position of Luminar Technologies in the autonomous vehicle lidar market",
            client_id="client_keystone",
            client_context="Growth equity fund considering $200M position in LAZR",
        ):
            events.append(event)

        # Should yield SpecificationGenerated, TasksDecomposed, and AgentDispatched events
        spec_events = [e for e in events if isinstance(e, SpecificationGenerated)]
        task_events = [e for e in events if isinstance(e, TasksDecomposed)]
        agent_events = [e for e in events if isinstance(e, AgentDispatched)]

        assert len(spec_events) == 1
        assert len(task_events) == 1
        assert len(agent_events) >= 10

    async def test_yields_spec_then_tasks(self):
        """SpecificationGenerated comes before TasksDecomposed."""
        llm = _make_full_mock_llm()
        engine = SpecificationEngine(llm)

        events = []
        async for event in engine.generate_spec(
            question="Test question",
            client_id="client_test",
        ):
            events.append(event)

        spec_idx = next(i for i, e in enumerate(events) if isinstance(e, SpecificationGenerated))
        task_idx = next(i for i, e in enumerate(events) if isinstance(e, TasksDecomposed))
        assert spec_idx < task_idx

    async def test_engagement_spec_validates(self):
        """EngagementSpec validates against all Pydantic models."""
        llm = _make_full_mock_llm()
        engine = SpecificationEngine(llm)

        async for _ in engine.generate_spec(
            question="Test question",
            client_id="client_test",
        ):
            pass

        spec = await engine.get_spec()
        assert isinstance(spec, EngagementSpec)
        assert spec.research_spec is not None
        assert spec.task_decomposition is not None
        assert spec.validation_report is not None
        assert spec.issue_tree is not None

    async def test_research_spec_fields(self):
        """ResearchSpec has all required fields populated."""
        llm = _make_full_mock_llm()
        engine = SpecificationEngine(llm)

        async for _ in engine.generate_spec(
            question="Test question",
            client_id="client_test",
        ):
            pass

        spec = await engine.get_spec()
        rs = spec.research_spec
        assert rs.engagement_type == EngagementType.STRATEGIC
        assert rs.day_1_hypothesis is not None
        assert len(rs.day_1_hypothesis) > 0
        assert len(rs.decision_context) > 0
        assert len(rs.surprising_finding) > 0
        assert len(rs.questions) >= 1
        assert any(q.is_primary for q in rs.questions)

    async def test_get_spec_raises_before_generate(self):
        """get_spec() raises RuntimeError before generate_spec() is called."""
        llm = _make_full_mock_llm()
        engine = SpecificationEngine(llm)
        with pytest.raises(RuntimeError, match="generate_spec"):
            await engine.get_spec()

    async def test_contract_compliance(self):
        """SpecificationEngine satisfies SpecificationEngineContract Protocol."""
        llm = _make_full_mock_llm()
        engine = SpecificationEngine(llm)
        assert isinstance(engine, SpecificationEngineContract)

    async def test_event_fields_populated(self):
        """All yielded events have required fields."""
        llm = _make_full_mock_llm()
        engine = SpecificationEngine(llm)

        async for event in engine.generate_spec(
            question="Test question",
            client_id="client_test",
        ):
            assert event.event_id is not None
            assert event.engagement_id is not None
            assert event.client_id == "client_test"
            assert event.layer == "L0"

            if isinstance(event, SpecificationGenerated):
                assert event.spec_version >= 1
                assert event.question_count >= 1
            elif isinstance(event, TasksDecomposed):
                assert event.task_count >= 1
                assert len(event.categories) >= 1
            elif isinstance(event, AgentDispatched):
                assert len(event.agent_id) > 0
                assert len(event.task_id) > 0
                assert len(event.tools) >= 3

    async def test_research_md_schema_compliance(self):
        """ResearchSpec output validates against research_md.schema.json structure."""
        llm = _make_full_mock_llm()
        engine = SpecificationEngine(llm)

        async for _ in engine.generate_spec(
            question="Test question",
            client_id="client_test",
        ):
            pass

        spec = await engine.get_spec()
        rs_dict = spec.research_spec.model_dump(mode="json")

        # Verify required fields from schema
        assert "engagement_id" in rs_dict
        assert "client_id" in rs_dict
        assert "title" in rs_dict
        assert "created_at" in rs_dict
        assert "specification_version" in rs_dict
        assert "engagement_type" in rs_dict
        assert "decision_context" in rs_dict
        assert "surprising_finding" in rs_dict
        assert "questions" in rs_dict
        assert "output_format" in rs_dict
        assert "non_goals" in rs_dict
        assert len(rs_dict["non_goals"]) >= 1

    async def test_research_tasks_schema_compliance(self):
        """TaskDecomposition output validates against research_tasks.schema.json structure."""
        llm = _make_full_mock_llm()
        engine = SpecificationEngine(llm)

        async for _ in engine.generate_spec(
            question="Test question",
            client_id="client_test",
        ):
            pass

        spec = await engine.get_spec()
        td_dict = spec.task_decomposition.model_dump(mode="json")

        # Verify required fields from schema
        assert "project" in td_dict
        assert "engagement_id" in td_dict
        assert "client_id" in td_dict
        assert "research_md_path" in td_dict
        assert "specification_version" in td_dict
        assert "decomposition_rationale" in td_dict
        assert "tasks" in td_dict
        assert len(td_dict["tasks"]) >= 1

        for task in td_dict["tasks"]:
            assert "id" in task
            assert "anti_confirmatory_framing" in task
            assert "end_product" in task
            assert "dependencies" in task
            assert "assigned_tools" in task
            assert 3 <= len(task["assigned_tools"]) <= 5
