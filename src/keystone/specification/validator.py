"""Step 4: MECE verification with 5 binary dimensions.

Validates the issue tree using Opus as judge on five dimensions.
If validation fails, the orchestrator retries decomposition (max 2 retries).
The retry loop lives in spec_engine.py, not here.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from keystone.evaluator.retry import LLMCallable, retry_llm_call
from keystone.models.research import EngagementType
from keystone.specification._prompts import extract_json, load_prompt
from keystone.specification.decomposer import IssueTree


class ValidationDimension(StrEnum):
    """Five binary dimensions for MECE verification."""

    MUTUAL_EXCLUSIVITY = "mutual_exclusivity"
    COLLECTIVE_EXHAUSTIVENESS = "collective_exhaustiveness"
    TAILORING = "tailoring"
    ACTIONABILITY = "actionability"
    DEPTH_APPROPRIATENESS = "depth_appropriateness"


class MECEValidationResult(BaseModel):
    """Result of MECE validation on an issue tree."""

    dimensions: dict[ValidationDimension, bool]
    feedback: dict[ValidationDimension, str]
    all_passed: bool = Field(
        description="True only if all 5 dimensions pass"
    )
    regeneration_needed: bool = Field(
        description="True if the tree should be regenerated"
    )


class MECEValidator:
    """Validate an issue tree on 5 binary dimensions using Opus as judge."""

    def __init__(self, llm: LLMCallable) -> None:
        self._llm = llm

    async def validate(
        self,
        tree: IssueTree,
        question: str,
        engagement_type: EngagementType,
    ) -> MECEValidationResult:
        """Validate the issue tree. Returns pass/fail per dimension."""
        import json

        prompt = load_prompt(
            "mece_validation",
            question=question,
            engagement_type=engagement_type.value,
            issue_tree=json.dumps(tree.model_dump(), indent=2),
            leaf_count=str(tree.metadata.leaf_count),
            depth=str(tree.metadata.depth),
        )

        raw = await retry_llm_call(
            self._llm, prompt, description="mece_validation"
        )
        data = extract_json(raw)

        dims_raw = data.get("dimensions", {})
        feedback_raw = data.get("feedback", {})

        dimensions: dict[ValidationDimension, bool] = {}
        feedback: dict[ValidationDimension, str] = {}

        for dim in ValidationDimension:
            dimensions[dim] = bool(dims_raw.get(dim.value, False))
            feedback[dim] = feedback_raw.get(dim.value, "")

        all_passed = all(dimensions.values())

        return MECEValidationResult(
            dimensions=dimensions,
            feedback=feedback,
            all_passed=all_passed,
            regeneration_needed=not all_passed,
        )
