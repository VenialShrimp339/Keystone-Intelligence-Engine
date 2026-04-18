"""Step 2: Decision-First Chain-of-Thought and Day-1 Hypothesis formation.

Uses a 5-step structured prompt to extract the decision context,
form a testable Day-1 Hypothesis, and identify unstated constraints
and scope boundaries. This prevents the AutoGPT infinite-loop failure
mode by anchoring research to a falsifiable claim.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from keystone.evaluator.retry import LLMCallable, retry_llm_call
from keystone.llm.parsing import safe_llm_json
from keystone.models.research import EngagementType
from keystone.specification._prompts import load_prompt


class IntentClarificationResult(BaseModel):
    """Output of the intent clarifier."""

    day_1_hypothesis: str = Field(description="Testable claim anchoring the engagement")
    intent_clear: bool = Field(
        description="Whether the question is sufficiently specified for research"
    )
    unstated_constraints: list[str] = Field(default_factory=list)
    scope_boundaries: list[str] = Field(default_factory=list)
    decision_context: str = Field(description="What decision this research informs")
    surprising_finding: str = Field(description="What a surprising finding would look like")


class IntentClarifier:
    """Run Decision-First CoT to clarify intent and form Day-1 Hypothesis.

    5-step structured prompt:
    1. What decision does this research inform?
    2. What would a surprising finding look like?
    3. What constraints aren't stated?
    4. What evidence would change the client's mind?
    5. What is explicitly out of scope?
    """

    def __init__(self, llm: LLMCallable) -> None:
        self._llm = llm

    async def clarify(
        self,
        question: str,
        engagement_type: EngagementType,
        client_context: str | None = None,
        constraints: list[str] | None = None,
    ) -> IntentClarificationResult:
        """Clarify intent and produce a Day-1 Hypothesis."""
        prompt = load_prompt(
            "intent_clarification",
            question=question,
            engagement_type=engagement_type.value,
            client_context=client_context or "No additional context provided.",
            constraints="\n".join(f"- {c}" for c in constraints)
            if constraints
            else "None specified.",
        )

        raw = await retry_llm_call(self._llm, prompt, description="intent_clarification")
        data = safe_llm_json(
            raw,
            required_keys=(
                "day_1_hypothesis",
                "intent_clear",
                "decision_context",
                "surprising_finding",
            ),
            bool_keys=frozenset(["intent_clear"]),
        )

        return IntentClarificationResult(
            day_1_hypothesis=data.get("day_1_hypothesis"),
            intent_clear=data.get("intent_clear"),
            unstated_constraints=data.get("unstated_constraints", []),
            scope_boundaries=data.get("scope_boundaries", []),
            decision_context=data.get("decision_context"),
            surprising_finding=data.get("surprising_finding"),
        )
