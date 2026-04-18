"""Three-pass evaluation architecture (Section 5.10).

Pass 1: Dimensional scoring (10-dimension rubric via Layer3RubricScorer)
Pass 2: Gestalt overlay (integrated in Layer3RubricScorer)
Pass 3: Observation Library negative-space scan (Phase 2 stub)
"""

from __future__ import annotations

from keystone.evaluator.layer3_rubric import Layer3RubricScorer
from keystone.evaluator.retry import LLMCallable
from keystone.evaluator.rubric_config import EvaluationProfile
from keystone.models.evaluation import Layer3Result, SprintContract


class ThreePassEvaluator:
    """Implements the three-pass evaluation architecture (Section 5.10).

    Phase 1: Pass 1 (dimensional) + Pass 2 (gestalt) are active.
    Phase 2 will add Pass 3: Observation Library scan against the full
    library of known failure patterns and success patterns. Interface:

        observation_scan = await observation_library.query(
            output_text=output_text,
            match_type="negative_space",  # Heuer disconfirmation
        )
        # Returns list of matching ObservationEntry IDs
        # Scoring adjustment: each matched failure pattern -> -1 to -3 points
        # Each matched success pattern -> +0.5 to +1 points (positive reinforcement)

    The data flow (ten scores -> Tier 1 gate -> geometric mean -> composite)
    is identical in Phase 1 and Phase 2. Pass 3 adds a post-composite
    adjustment, not a pipeline change.
    """

    def __init__(
        self,
        llm: LLMCallable,
        profile: EvaluationProfile,
        judge_id: str | None = None,
    ) -> None:
        self._scorer = Layer3RubricScorer(llm=llm, profile=profile, judge_id=judge_id)
        self._judge_id = judge_id

    async def run(self, output_text: str, contract: SprintContract) -> Layer3Result:
        # Pass 1 + Pass 2: Dimensional scoring + gestalt overlay
        dimensional_result = await self._scorer.score_all_dimensions(output_text, contract)

        # Pass 3: Observation Library scan (STUB for Phase 2)
        # In Phase 2, this queries ObservationLibraryContract.query()
        # for known patterns matching the current output and adjusts
        # scoring accordingly. For now: no-op, returns Pass 1+2 unchanged.
        _observation_scan = None  # Phase 2: ObservationLibraryContract.query()

        return dimensional_result
