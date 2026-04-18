"""Tests for the engagement classifier (Step 1)."""

from __future__ import annotations

import json

import pytest

from keystone.models.research import EngagementType
from keystone.specification.engagement_classifier import (
    ClassificationResult,
    EngagementClassifier,
    PipelineProfile,
)


def _make_llm(engagement_type: str, pipeline_profile: str = "standard", confidence: float = 0.9):
    """Create a mock LLM that returns a classification response."""

    async def llm(prompt: str) -> str:
        return json.dumps(
            {
                "engagement_type": engagement_type,
                "pipeline_profile": pipeline_profile,
                "confidence": confidence,
                "reasoning": f"Classified as {engagement_type} with {pipeline_profile} profile.",
            }
        )

    return llm


class TestEngagementClassifier:
    async def test_evaluative_classification(self):
        llm = _make_llm("evaluative", "standard")
        classifier = EngagementClassifier(llm)
        result = await classifier.classify("Evaluate competitive position of Company X")
        assert result.engagement_type == EngagementType.EVALUATIVE
        assert result.pipeline_profile == PipelineProfile.STANDARD
        assert isinstance(result, ClassificationResult)

    async def test_sizing_classification(self):
        llm = _make_llm("sizing", "standard")
        classifier = EngagementClassifier(llm)
        result = await classifier.classify("Estimate TAM for autonomous vehicle sensors")
        assert result.engagement_type == EngagementType.SIZING
        assert result.pipeline_profile == PipelineProfile.STANDARD

    async def test_exploratory_classification(self):
        llm = _make_llm("exploratory", "light")
        classifier = EngagementClassifier(llm)
        result = await classifier.classify("What's happening in the EV market?")
        assert result.engagement_type == EngagementType.EXPLORATORY
        assert result.pipeline_profile == PipelineProfile.LIGHT

    async def test_strategic_classification(self):
        llm = _make_llm("strategic", "deep")
        classifier = EngagementClassifier(llm)
        result = await classifier.classify("Should we acquire Company Y?")
        assert result.engagement_type == EngagementType.STRATEGIC
        assert result.pipeline_profile == PipelineProfile.DEEP

    async def test_diagnostic_classification(self):
        llm = _make_llm("diagnostic", "standard")
        classifier = EngagementClassifier(llm)
        result = await classifier.classify("What caused the Q3 revenue decline?")
        assert result.engagement_type == EngagementType.DIAGNOSTIC
        assert result.pipeline_profile == PipelineProfile.STANDARD

    async def test_default_profile_fallback(self):
        """When LLM doesn't return a valid profile, falls back to default."""

        async def llm(prompt: str) -> str:
            return json.dumps(
                {
                    "engagement_type": "strategic",
                    "confidence": 0.85,
                    "reasoning": "Complex multi-variable question.",
                }
            )

        classifier = EngagementClassifier(llm)
        result = await classifier.classify("Should we enter the Japanese market?")
        assert result.engagement_type == EngagementType.STRATEGIC
        assert result.pipeline_profile == PipelineProfile.DEEP  # default for strategic

    async def test_confidence_preserved(self):
        llm = _make_llm("sizing", "standard", confidence=0.72)
        classifier = EngagementClassifier(llm)
        result = await classifier.classify("How big is the widget market?")
        assert result.confidence == pytest.approx(0.72)

    async def test_client_context_passed_to_prompt(self):
        """Verify client_context makes it into the prompt."""
        captured_prompts: list[str] = []

        async def llm(prompt: str) -> str:
            captured_prompts.append(prompt)
            return json.dumps(
                {
                    "engagement_type": "evaluative",
                    "pipeline_profile": "standard",
                    "confidence": 0.9,
                    "reasoning": "Test.",
                }
            )

        classifier = EngagementClassifier(llm)
        await classifier.classify("Test question", client_context="Fortune 500 client")
        assert "Fortune 500 client" in captured_prompts[0]
