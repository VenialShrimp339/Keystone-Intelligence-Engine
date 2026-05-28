"""Phase 2 model-tier fix coverage.

Per the audit: Layer 1 evaluator uses a dedicated extraction LLM
(STANDARD/Sonnet) so Opus is not wasted on fact decomposition; the
Decomposer takes separate lens / synthesis LLMs so lenses can run at
STANDARD while the synthesis step runs at FLAGSHIP; the Specification
Engine accepts per-step LLMs so the orchestrator can mix tiers without
patching source.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from keystone.evaluator.evaluator import Evaluator
from keystone.evaluator.rubric_config import EvaluationProfile
from keystone.models.research import EngagementType
from keystone.specification.decomposer import Decomposer, IssueTree
from keystone.specification.spec_engine import SpecificationEngine
from keystone.specification.template_registry import TemplateRegistry

# ---- Evaluator extraction_llm (Fix B) ------------------------------------


class TestEvaluatorExtractionLLM:
    def test_layer1_receives_extraction_llm_when_provided(self):
        """Distinct extraction LLM flows into Layer1Evaluator."""
        judge_llm: AsyncMock = AsyncMock(return_value="ok")
        extraction_llm: AsyncMock = AsyncMock(return_value="ok")

        ev = Evaluator(
            llm=judge_llm,
            profile=EvaluationProfile.DEFAULT,
            extraction_llm=extraction_llm,
        )
        # Internals: layer1 holds the extraction LLM, three_pass + layer4 hold
        # the rubric-judgment LLM. No accidental sharing.
        assert ev._layer1._llm is extraction_llm
        # ThreePassEvaluator wraps the scorer, which holds the rubric LLM.
        assert ev._three_pass._scorer._llm is judge_llm
        assert ev._layer4._llm is judge_llm

    def test_extraction_llm_falls_back_to_primary_llm(self):
        """Backward compat: when extraction_llm is omitted, Layer 1 shares llm."""
        primary: AsyncMock = AsyncMock(return_value="ok")

        ev = Evaluator(llm=primary, profile=EvaluationProfile.DEFAULT)
        assert ev._layer1._llm is primary
        assert ev._three_pass._scorer._llm is primary


# ---- Decomposer split (Fix D) -------------------------------------------


def _make_lens_tree(prefix: str) -> dict:
    return {
        "id": f"{prefix}_root",
        "name": f"{prefix.title()} Analysis",
        "description": f"{prefix.title()} lens decomposition",
        "children": [
            {
                "id": f"{prefix}_{i}",
                "name": f"{prefix.title()} Branch {i}",
                "description": f"Investigate {prefix} aspect {i}",
                "children": [],
            }
            for i in range(1, 5)
        ],
    }


def _make_synth_tree() -> dict:
    branches = []
    for i in range(1, 4):
        branches.append(
            {
                "id": f"branch_{i}",
                "name": f"Major Branch {i}",
                "description": "top",
                "children": [
                    {
                        "id": f"branch_{i}.{j}",
                        "name": f"Sub {i}.{j}",
                        "description": "sub",
                        "children": [],
                    }
                    for j in range(1, 5)
                ],
            }
        )
    return {
        "root": {
            "id": "root",
            "name": "Root",
            "description": "merged",
            "children": branches,
        },
        "synthesis_rationale": "Merged three lenses.",
    }


class TestDecomposerTierSplit:
    async def test_lens_and_synth_call_distinct_llms(self):
        """Each lens call goes to lens_llm; synthesis goes to synth_llm."""
        lens_calls: list[str] = []
        synth_calls: list[str] = []

        async def lens_llm(prompt: str) -> str:
            lens_calls.append(prompt[:40])
            # Return a lens tree — the prompt filename in the debug log
            # is enough to prove this path ran; we don't depend on
            # prefix in the tree content.
            return json.dumps(_make_lens_tree(f"lens{len(lens_calls)}"))

        async def synth_llm(prompt: str) -> str:
            synth_calls.append(prompt[:40])
            return json.dumps(_make_synth_tree())

        d = Decomposer(lens_llm=lens_llm, synth_llm=synth_llm)
        tree = await d.decompose(
            "Probe question",
            EngagementType.STRATEGIC,
            "hypothesis",
        )
        assert isinstance(tree, IssueTree)
        # Three lens decompositions + one synthesis call.
        assert len(lens_calls) == 3
        assert len(synth_calls) == 1

    async def test_legacy_single_llm_still_works(self):
        """``Decomposer(llm)`` remains valid — lens and synth share one LLM."""
        all_calls: list[str] = []

        async def llm(prompt: str) -> str:
            all_calls.append(prompt[:40])
            if len(all_calls) <= 3:
                return json.dumps(_make_lens_tree(f"lens_{len(all_calls)}"))
            return json.dumps(_make_synth_tree())

        d = Decomposer(llm)
        await d.decompose("q", EngagementType.STRATEGIC, "h")
        assert len(all_calls) == 4  # 3 lenses + 1 synthesis

    def test_constructor_rejects_all_none(self):
        with pytest.raises(ValueError, match="at least one LLM"):
            Decomposer()  # type: ignore[call-arg]

    def test_constructor_requires_both_on_split(self):
        # Passing only one of lens/synth without a fallback ``llm`` raises.
        async def fake(_prompt: str) -> str:
            return "{}"

        with pytest.raises(ValueError, match="both lens and synthesis"):
            Decomposer(lens_llm=fake)


# ---- Specification Engine per-step tiers (Fix C) -------------------------


class TestSpecEnginePerStepLLMs:
    def test_constructor_accepts_per_step_llms(self):
        """SpecificationEngine stores each step's LLM in its sub-component."""
        flagship: AsyncMock = AsyncMock(return_value="{}")
        standard: AsyncMock = AsyncMock(return_value="{}")
        lens: AsyncMock = AsyncMock(return_value="{}")
        synth: AsyncMock = AsyncMock(return_value="{}")
        validator: AsyncMock = AsyncMock(return_value="{}")
        scorer: AsyncMock = AsyncMock(return_value="{}")
        task_gen: AsyncMock = AsyncMock(return_value="{}")
        clarifier: AsyncMock = AsyncMock(return_value="{}")

        engine = SpecificationEngine(
            llm=flagship,
            template_registry=TemplateRegistry(),
            classifier_llm=standard,
            clarifier_llm=clarifier,
            decomposer_lens_llm=lens,
            decomposer_synth_llm=synth,
            mece_validator_llm=validator,
            priority_scorer_llm=scorer,
            task_generator_llm=task_gen,
        )

        # Each sub-component wraps the tier-appropriate LLM.
        assert engine._classifier._llm is standard
        assert engine._clarifier._llm is clarifier
        assert engine._decomposer._lens_llm is lens
        assert engine._decomposer._synth_llm is synth
        assert engine._validator._llm is validator
        assert engine._scorer._llm is scorer
        assert engine._task_generator._llm is task_gen

    def test_legacy_single_llm_still_works(self):
        """Passing only ``llm`` drives every step through the same callable."""
        flagship: AsyncMock = AsyncMock(return_value="{}")
        engine = SpecificationEngine(
            llm=flagship,
            template_registry=TemplateRegistry(),
        )
        assert engine._classifier._llm is flagship
        assert engine._clarifier._llm is flagship
        assert engine._decomposer._lens_llm is flagship
        assert engine._decomposer._synth_llm is flagship
        assert engine._validator._llm is flagship
        assert engine._scorer._llm is flagship
        assert engine._task_generator._llm is flagship
