"""Step 1: Engagement classification and pipeline profile selection.

Examines 5 signals to classify the engagement type and route to the
appropriate pipeline depth (Light/Standard/Deep per Directive 11).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from keystone.evaluator.retry import LLMCallable, retry_llm_call
from keystone.llm.parsing import safe_llm_json
from keystone.models.research import EngagementType, PipelineProfile
from keystone.specification._prompts import load_prompt


class ClassificationResult(BaseModel):
    """Output of the engagement classifier."""

    engagement_type: EngagementType
    pipeline_profile: PipelineProfile
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str


# Default profile mapping -- LLM can override based on question complexity
_DEFAULT_PROFILES: dict[EngagementType, PipelineProfile] = {
    EngagementType.SIZING: PipelineProfile.STANDARD,
    EngagementType.DIAGNOSTIC: PipelineProfile.STANDARD,
    EngagementType.EVALUATIVE: PipelineProfile.STANDARD,
    EngagementType.EXPLORATORY: PipelineProfile.LIGHT,
    EngagementType.STRATEGIC: PipelineProfile.DEEP,
}


class EngagementClassifier:
    """Classify engagement type and select pipeline profile.

    Examines 5 signals:
    1. Specificity of deliverable
    2. Presence of testable hypothesis
    3. Known analytical framework
    4. Scope boundedness
    5. Decision type
    """

    def __init__(self, llm: LLMCallable) -> None:
        self._llm = llm

    async def classify(
        self,
        question: str,
        client_context: str | None = None,
    ) -> ClassificationResult:
        """Classify the engagement and select pipeline profile."""
        prompt = load_prompt(
            "classification",
            question=question,
            client_context=client_context or "No additional context provided.",
        )

        raw = await retry_llm_call(self._llm, prompt, description="engagement_classification")
        data = safe_llm_json(raw, required_keys=("engagement_type",))

        engagement_type = EngagementType(data.get("engagement_type"))
        profile_raw = data.get("pipeline_profile")

        if profile_raw and profile_raw in PipelineProfile.__members__.values():
            pipeline_profile = PipelineProfile(profile_raw)
        else:
            pipeline_profile = _DEFAULT_PROFILES[engagement_type]

        return ClassificationResult(
            engagement_type=engagement_type,
            pipeline_profile=pipeline_profile,
            confidence=float(data.get("confidence", 0.8)),
            reasoning=data.get("reasoning", ""),
        )
