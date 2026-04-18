"""Layer 3: Multi-rubric scoring via 10-dimension rubric.

One prompt per dimension (SOS-Bench: never score multiple dimensions
in a single prompt). Tier 1 gate check between tiers. Geometric mean
aggregation (Directive 7). Gestalt overlay for emergent quality signals.
"""

from __future__ import annotations

import asyncio
import logging
import math
from pathlib import Path

from keystone.evaluator.retry import LLMCallable, retry_llm_call
from keystone.llm.parsing import ParseError, safe_llm_json
from keystone.evaluator.rubric_config import (
    TIER_1_DIMENSIONS,
    TIER_2_DIMENSIONS,
    EvaluationProfile,
    get_profile_weights,
    get_tier1_passed,
)
from keystone.models.evaluation import (
    DimensionScore,
    Layer3Result,
    RubricDimension,
    SprintContract,
)

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).parent / "prompts"
_GEOMETRIC_MEAN_EPSILON = 0.01

# Map RubricDimension enum values to prompt file names
_DIMENSION_PROMPT_FILES: dict[RubricDimension, str] = {
    RubricDimension.INTENT_ALIGNMENT: "intent_alignment.md",
    RubricDimension.INTELLECTUAL_HONESTY: "intellectual_honesty.md",
    RubricDimension.COMPLETENESS: "completeness.md",
    RubricDimension.NARRATIVE_COHERENCE: "narrative_coherence.md",
    RubricDimension.ANALYTICAL_DEPTH: "analytical_depth.md",
    RubricDimension.SOURCE_QUALITY: "source_quality.md",
    RubricDimension.QUANTITATIVE_RIGOR: "quantitative_rigor.md",
    RubricDimension.ACTIONABILITY: "actionability.md",
    RubricDimension.EVALUATIVE_SURPRISE: "evaluative_surprise.md",
    RubricDimension.CALIBRATED_CONFIDENCE: "calibrated_confidence.md",
}


def weighted_geometric_mean(
    scores: list[DimensionScore],
    weights: dict[RubricDimension, float],
) -> float:
    """Weighted geometric mean prevents dimension compensation (Directive 7).

    A near-zero score on any dimension drags the composite toward zero.
    Formula: exp(sum(w_i * ln(x_i)) / weight_sum) when scoring a subset,
    or exp(sum(w_i * ln(x_i))) when weights sum to 1.0.

    Scores are floored at 0.01 to avoid log(0). A score near 0/100 is
    effectively zero in the geometric mean.
    """
    log_sum = 0.0
    weight_sum = 0.0
    for s in scores:
        w = weights.get(s.dimension, 0.0)
        if w > 0:
            log_sum += w * math.log(max(s.score, _GEOMETRIC_MEAN_EPSILON))
            weight_sum += w
    if weight_sum == 0:
        return 0.0
    if weight_sum < 1.0 - 1e-9:
        # Scoring only a subset: normalize by weight_sum
        return math.exp(log_sum / weight_sum)
    return math.exp(log_sum)


def _format_sprint_contract_context(contract: SprintContract) -> str:
    """Render sprint contract fields into prompt-ready evaluation context."""
    sections: list[str] = []

    def _append_list_section(title: str, items: list[str]) -> None:
        sections.append(title)
        if items:
            sections.extend(f"- {item}" for item in items)
        else:
            sections.append("- None specified")

    _append_list_section("Acceptance criteria:", contract.acceptance_criteria)
    _append_list_section("Mandatory elements:", contract.mandatory_elements)
    _append_list_section("Anti-patterns:", contract.anti_patterns)

    return "\n".join(sections)


def _apply_dimension_emphasis(
    base_weights: dict[RubricDimension, float],
    emphasis: dict[RubricDimension, float],
) -> dict[RubricDimension, float]:
    """Apply per-sprint emphasis multipliers and renormalize the weights."""
    adjusted = dict(base_weights)
    for dimension, multiplier in emphasis.items():
        if dimension in adjusted:
            adjusted[dimension] *= max(0.7, min(1.5, multiplier))

    total = sum(adjusted.values())
    if total <= 0:
        return adjusted

    return {dimension: weight / total for dimension, weight in adjusted.items()}


class Layer3RubricScorer:
    """10-dimension rubric scorer with Tier 1/Tier 2 gating.

    Flow:
    1. Score Tier 1 dimensions (4 parallel LLM calls)
    2. Check Tier 1 floors -- if any fail, return early
    3. Score Tier 2 dimensions (6 parallel LLM calls)
    4. Compute geometric mean of ALL 10 dimensions
    5. Apply gestalt overlay (1 more LLM call)
    6. Return Layer3Result
    """

    def __init__(
        self,
        llm: LLMCallable,
        profile: EvaluationProfile,
        judge_id: str | None = None,
    ) -> None:
        self._llm = llm
        self._weights = get_profile_weights(profile)
        self._judge_id = judge_id

    async def score_all_dimensions(
        self,
        output_text: str,
        contract: SprintContract,
    ) -> Layer3Result:
        criteria_text = _format_sprint_contract_context(contract)
        weights = _apply_dimension_emphasis(self._weights, contract.dimension_emphasis)

        # Step 1: Score Tier 1 dimensions in parallel
        tier1_scores = await asyncio.gather(
            *(
                self._score_dimension(dim, output_text, criteria_text)
                for dim in sorted(TIER_1_DIMENSIONS, key=lambda d: d.value)
            )
        )
        tier1_list = list(tier1_scores)

        # Step 2: Check Tier 1 gates
        if not get_tier1_passed(tier1_list):
            return Layer3Result(
                dimension_scores=tier1_list,
                weighted_total=0.0,
                gestalt_adjustment=0.0,
                final_score=0.0,
            )

        # Step 3: Score Tier 2 dimensions in parallel
        tier2_scores = await asyncio.gather(
            *(
                self._score_dimension(dim, output_text, criteria_text)
                for dim in sorted(TIER_2_DIMENSIONS, key=lambda d: d.value)
            )
        )
        all_scores = tier1_list + list(tier2_scores)

        # Step 4: Compute geometric mean
        geo_mean = weighted_geometric_mean(all_scores, weights)

        # Step 5: Gestalt overlay
        gestalt_adj = await self._gestalt_overlay(output_text)
        gestalt_adj = max(-10.0, min(10.0, gestalt_adj))

        # Step 6: Compute final score (clamped to [0, 100])
        final = max(0.0, min(100.0, geo_mean + gestalt_adj))

        return Layer3Result(
            dimension_scores=all_scores,
            weighted_total=round(geo_mean, 2),
            gestalt_adjustment=round(gestalt_adj, 2),
            final_score=round(final, 2),
        )

    async def _score_dimension(
        self,
        dimension: RubricDimension,
        output_text: str,
        criteria_text: str,
    ) -> DimensionScore:
        """Score a single dimension using its dedicated prompt template."""
        prompt_file = _DIMENSION_PROMPT_FILES[dimension]
        template = (_PROMPTS_DIR / prompt_file).read_text()
        prompt = template.replace("{{output_text}}", output_text).replace(
            "{{sprint_contract_criteria}}", criteria_text
        )

        description = (
            f"rubric_{dimension.value}[{self._judge_id}]"
            if self._judge_id is not None
            else f"rubric_{dimension.value}"
        )
        raw = await retry_llm_call(self._llm, prompt, description=description)
        # ParseError propagates -- callers must not silently default to score=50
        parsed = safe_llm_json(raw, required_keys=("score",))

        return DimensionScore(
            dimension=dimension,
            score=max(0.0, min(100.0, float(parsed.get("score")))),
            feedback=parsed.get("feedback", "No feedback provided"),
            sub_criteria_notes=parsed.get("sub_criteria_notes", []),
        )

    async def _gestalt_overlay(self, output_text: str) -> float:
        """Pass 2: holistic quality adjustment."""
        template = (_PROMPTS_DIR / "gestalt_overlay.md").read_text()
        prompt = template.replace("{{output_text}}", output_text)

        description = (
            f"gestalt_overlay[{self._judge_id}]"
            if self._judge_id is not None
            else "gestalt_overlay"
        )
        raw = await retry_llm_call(self._llm, prompt, description=description)
        try:
            parsed = safe_llm_json(raw)
            return float(parsed.get("adjustment", 0))
        except ParseError:
            logger.warning("Failed to parse gestalt overlay JSON, defaulting to 0 adjustment")
            return 0.0
