"""Tests for the intent clarifier (Step 2)."""

from __future__ import annotations

import json

from keystone.models.research import EngagementType
from keystone.specification.intent_clarifier import (
    IntentClarificationResult,
    IntentClarifier,
)


def _make_llm(
    day_1_hypothesis: str = "The market will grow 15% annually",
    intent_clear: bool = True,
    decision_context: str = "Investment committee deciding on a $200M position",
    surprising_finding: str = "The market is actually shrinking",
):
    async def llm(prompt: str) -> str:
        return json.dumps({
            "day_1_hypothesis": day_1_hypothesis,
            "intent_clear": intent_clear,
            "unstated_constraints": ["3-week timeline", "Budget under $50K"],
            "scope_boundaries": ["No implementation planning", "North America only"],
            "decision_context": decision_context,
            "surprising_finding": surprising_finding,
        })
    return llm


class TestIntentClarifier:

    async def test_well_specified_question(self):
        llm = _make_llm(intent_clear=True)
        clarifier = IntentClarifier(llm)
        result = await clarifier.clarify(
            "Evaluate the competitive position of Luminar in AV lidar",
            EngagementType.EVALUATIVE,
            client_context="Growth equity fund considering $200M position",
        )
        assert result.intent_clear is True
        assert len(result.day_1_hypothesis) > 0
        assert isinstance(result, IntentClarificationResult)

    async def test_vague_question(self):
        llm = _make_llm(
            intent_clear=False,
            day_1_hypothesis="AI will continue to be important",
        )
        clarifier = IntentClarifier(llm)
        result = await clarifier.clarify(
            "Tell me about AI",
            EngagementType.EXPLORATORY,
        )
        assert result.intent_clear is False

    async def test_day_1_hypothesis_is_testable(self):
        llm = _make_llm(
            day_1_hypothesis="Luminar's 1550nm lidar lead is sustainable through 2028 due to manufacturing barriers"
        )
        clarifier = IntentClarifier(llm)
        result = await clarifier.clarify(
            "Evaluate Luminar's competitive position",
            EngagementType.EVALUATIVE,
        )
        # Hypothesis should be a claim, not a question
        assert not result.day_1_hypothesis.endswith("?")
        assert len(result.day_1_hypothesis) > 20

    async def test_decision_context_from_client_context(self):
        captured: list[str] = []
        async def llm(prompt: str) -> str:
            captured.append(prompt)
            return json.dumps({
                "day_1_hypothesis": "Test hypothesis",
                "intent_clear": True,
                "unstated_constraints": [],
                "scope_boundaries": [],
                "decision_context": "Fund manager deciding on allocation",
                "surprising_finding": "No surprise",
            })

        clarifier = IntentClarifier(llm)
        await clarifier.clarify(
            "Should we invest?",
            EngagementType.STRATEGIC,
            client_context="PE fund evaluating portfolio company",
        )
        assert "PE fund evaluating portfolio company" in captured[0]

    async def test_constraints_passed(self):
        captured: list[str] = []
        async def llm(prompt: str) -> str:
            captured.append(prompt)
            return json.dumps({
                "day_1_hypothesis": "Test",
                "intent_clear": True,
                "unstated_constraints": [],
                "scope_boundaries": [],
                "decision_context": "Test",
                "surprising_finding": "Test",
            })

        clarifier = IntentClarifier(llm)
        await clarifier.clarify(
            "Test question",
            EngagementType.SIZING,
            constraints=["Focus on North America", "Exclude government contracts"],
        )
        assert "Focus on North America" in captured[0]
        assert "Exclude government contracts" in captured[0]

    async def test_unstated_constraints_populated(self):
        llm = _make_llm()
        clarifier = IntentClarifier(llm)
        result = await clarifier.clarify("Test question", EngagementType.SIZING)
        assert len(result.unstated_constraints) > 0
        assert len(result.scope_boundaries) > 0
