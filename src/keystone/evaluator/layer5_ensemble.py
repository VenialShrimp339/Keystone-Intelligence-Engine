"""Layer 5: Cross-model ensemble L3 evaluator with dissenter veto.

Single-LLM rubric judges have systematic biases: SOS-Bench (ICLR 2025) showed
holistic LLM judging penalizes TONE seven times more than FACTUAL ERRORS, and
the Play Favorites phenomenon drives a model to score its own outputs higher
due to lower perplexity. Single-judge agreement with human experts plateaus
at 60-68%.

Layer 5 runs multiple ``ThreePassEvaluator`` instances in parallel (the PoLL
pattern), aggregates per-dimension scores by median, and applies a dissenter
veto on Tier 1 dimensions so a biased majority cannot hide a legitimate
concern raised by any one judge. The veto fires on ANY dissent below floor,
not only a numeric minority — one judge is enough to force human review.

Inert when a single-judge evaluator is constructed (``ensemble_llms=None``);
skipped entirely for LIGHT_TOUCH intensity (Layer 3 itself is skipped there).
"""

from __future__ import annotations

import asyncio
import logging
import statistics
from dataclasses import dataclass
from typing import TYPE_CHECKING

from keystone.evaluator.layer3_rubric import _apply_dimension_emphasis, weighted_geometric_mean
from keystone.evaluator.rubric_config import (
    TIER_1_DIMENSIONS,
    TIER_1_FLOOR_THRESHOLDS,
    EvaluationProfile,
    get_profile_weights,
)
from keystone.evaluator.three_pass import ThreePassEvaluator
from keystone.models.evaluation import (
    DimensionScore,
    JudgeScore,
    Layer3Result,
    Layer5Result,
    RubricDimension,
    VetoEvent,
)

if TYPE_CHECKING:
    from keystone.evaluator.retry import LLMCallable
    from keystone.models.evaluation import SprintContract

logger = logging.getLogger(__name__)

# Agreement is "high" when all judges' scores on a dimension fall within this
# many points. Matches the +/- 10 gestalt clamp width so a single gestalt-sized
# deviation still counts as concordant.
_AGREEMENT_THRESHOLD = 10.0


@dataclass(frozen=True)
class _JudgeRun:
    """Internal result of running one judge: success yields a Layer3Result, failure
    captures the exception short description."""

    judge_id: str
    judge_tier: str
    layer3_result: Layer3Result | None
    error: str | None


class EnsembleL3Evaluator:
    """Run N ThreePassEvaluator judges in parallel and aggregate with dissenter veto.

    Judges run independently (no judge sees another's scores). Per-dimension
    aggregation is median across surviving judges. Tier 1 dissenter veto: if
    any surviving judge scored any Tier 1 dimension below its floor, the
    ensemble's aggregated Layer3Result.final_score is forced to 0.0 (the
    per-dimension median is preserved for audit).

    Graceful degradation: ``asyncio.gather(..., return_exceptions=True)``.
    Exceptions are recorded as failed JudgeScores; aggregation runs over the
    survivors. When all judges fail, the ensemble returns a zero-result and
    sets ``Layer5Result.all_judges_failed=True``.
    """

    def __init__(
        self,
        judges: list[tuple[str, LLMCallable]],
        profile: EvaluationProfile,
        pass_threshold: float = 60.0,
    ) -> None:
        if len(judges) < 1:
            msg = "EnsembleL3Evaluator requires at least 1 judge"
            raise ValueError(msg)
        # Each judge gets its own ThreePassEvaluator so Phase 2 Observation
        # Library scan (currently a stub inside ThreePass) gets applied per-judge.
        self._profile = profile
        self._weights = get_profile_weights(profile)
        self._judges: list[tuple[str, ThreePassEvaluator]] = [
            (
                judge_id,
                ThreePassEvaluator(
                    llm=llm, profile=profile, judge_id=judge_id, pass_threshold=pass_threshold
                ),
            )
            for judge_id, llm in judges
        ]

    async def run(
        self,
        output_text: str,
        contract: SprintContract,
    ) -> tuple[Layer3Result, Layer5Result]:
        """Run all judges in parallel and aggregate.

        Returns a pair: (aggregated_Layer3Result suitable for the existing
        Evaluator flow, full Layer5Result with per-judge detail).
        """
        weights = _apply_dimension_emphasis(self._weights, contract.dimension_emphasis)

        judge_runs = await self._run_judges(output_text, contract)

        judge_scores = [self._to_judge_score(run) for run in judge_runs]
        judges_used = [judge_id for judge_id, _ in self._judges]
        failed_judge_ids = [run.judge_id for run in judge_runs if run.layer3_result is None]

        survivors = [run for run in judge_runs if run.layer3_result is not None]

        if not survivors:
            logger.warning(
                "All %d ensemble judges failed; returning zero Layer3Result "
                "and marking Layer5Result.all_judges_failed=True",
                len(judge_runs),
            )
            zero_l3 = Layer3Result(
                dimension_scores=[],
                weighted_total=0.0,
                gestalt_adjustment=0.0,
                final_score=0.0,
            )
            layer5 = Layer5Result(
                judges_used=judges_used,
                judge_scores=judge_scores,
                aggregated_dimension_scores=[],
                ensemble_weighted_total=0.0,
                ensemble_gestalt_adjustment=0.0,
                ensemble_final_score=0.0,
                tier1_vetoed=False,
                veto_events=[],
                agreement_level=0.0,
                all_judges_failed=True,
                failed_judge_ids=failed_judge_ids,
            )
            return zero_l3, layer5

        aggregated_dimension_scores = self._aggregate_dimension_scores(survivors)
        veto_events = self._check_tier1_vetoes(survivors)
        tier1_vetoed = bool(veto_events)

        survivor_l3_results = [
            run.layer3_result for run in survivors if run.layer3_result is not None
        ]
        if tier1_vetoed:
            # Keep the per-dimension median scores (observable truth) but force
            # the composite to zero so downstream governance rejects the output.
            weighted_total = 0.0
            gestalt = 0.0
            final_score = 0.0
        else:
            weighted_total = weighted_geometric_mean(aggregated_dimension_scores, weights)
            gestalt = statistics.median(r.gestalt_adjustment for r in survivor_l3_results)
            gestalt = max(-10.0, min(10.0, gestalt))
            final_score = max(0.0, min(100.0, weighted_total + gestalt))

        agreement_level = self._agreement_level(survivors)

        aggregated_l3 = Layer3Result(
            dimension_scores=aggregated_dimension_scores,
            weighted_total=round(weighted_total, 2),
            gestalt_adjustment=round(gestalt, 2),
            final_score=round(final_score, 2),
        )

        layer5 = Layer5Result(
            judges_used=judges_used,
            judge_scores=judge_scores,
            aggregated_dimension_scores=aggregated_dimension_scores,
            ensemble_weighted_total=round(weighted_total, 2),
            ensemble_gestalt_adjustment=round(gestalt, 2),
            ensemble_final_score=round(final_score, 2),
            tier1_vetoed=tier1_vetoed,
            veto_events=veto_events,
            agreement_level=round(agreement_level, 4),
            all_judges_failed=False,
            failed_judge_ids=failed_judge_ids,
        )
        return aggregated_l3, layer5

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _run_judges(
        self,
        output_text: str,
        contract: SprintContract,
    ) -> list[_JudgeRun]:
        results = await asyncio.gather(
            *(judge.run(output_text, contract) for _, judge in self._judges),
            return_exceptions=True,
        )

        runs: list[_JudgeRun] = []
        for (judge_id, _), result in zip(self._judges, results, strict=True):
            # judge_id is treated as the tier string by callers that pass
            # ModelTier-aligned identifiers; it is also safe when the caller
            # wants custom labels.
            if isinstance(result, Layer3Result):
                runs.append(
                    _JudgeRun(
                        judge_id=judge_id,
                        judge_tier=judge_id,
                        layer3_result=result,
                        error=None,
                    )
                )
                continue
            if isinstance(result, BaseException):
                logger.warning("Ensemble judge %s failed: %s", judge_id, result)
                runs.append(
                    _JudgeRun(
                        judge_id=judge_id,
                        judge_tier=judge_id,
                        layer3_result=None,
                        error=_short_error(result),
                    )
                )
                continue
            # Defensive: asyncio.gather(return_exceptions=True) only yields
            # the coroutine's return value or an exception; any other value
            # signals a contract break.
            msg = f"Unexpected judge result type: {type(result).__name__}"
            raise TypeError(msg)
        return runs

    def _to_judge_score(self, run: _JudgeRun) -> JudgeScore:
        return JudgeScore(
            judge_id=run.judge_id,
            judge_tier=run.judge_tier,
            layer3_result=run.layer3_result,
            succeeded=run.layer3_result is not None,
            error=run.error,
        )

    def _aggregate_dimension_scores(
        self,
        survivors: list[_JudgeRun],
    ) -> list[DimensionScore]:
        """Per-dimension median across surviving judges.

        Skipping Tier 2 when a judge bailed out after Tier 1 failure is already
        encoded in each judge's Layer3Result.dimension_scores list (length 4
        when that judge saw a Tier 1 failure, 10 when it passed). Aggregate
        over whatever dimensions each judge reports; dimensions covered by at
        least one judge appear in the aggregate.
        """
        by_dim: dict[RubricDimension, list[tuple[str, DimensionScore]]] = {}
        for run in survivors:
            assert run.layer3_result is not None  # narrowed by caller
            for ds in run.layer3_result.dimension_scores:
                by_dim.setdefault(ds.dimension, []).append((run.judge_id, ds))

        aggregated: list[DimensionScore] = []
        # Deterministic order for downstream RubricDimensionScored events
        for dim in sorted(by_dim.keys(), key=lambda d: d.value):
            pairs = by_dim[dim]
            median_score = statistics.median(ds.score for _, ds in pairs)
            feedback_parts = [f"[{jid}] {ds.feedback}" for jid, ds in pairs if ds.feedback]
            feedback = (
                "; ".join(feedback_parts)
                if feedback_parts
                else "No per-judge feedback provided for this dimension."
            )
            # Preserve per-judge attribution on sub-criteria notes so downstream
            # audit can trace a concern back to the judge that raised it, mirroring
            # the ``[judge_id] ...`` prefix applied to ``feedback`` above.
            notes: list[str] = []
            for jid, ds in pairs:
                notes.extend(f"[{jid}] {note}" for note in ds.sub_criteria_notes)
            aggregated.append(
                DimensionScore(
                    dimension=dim,
                    score=round(median_score, 2),
                    feedback=feedback,
                    sub_criteria_notes=notes,
                )
            )
        return aggregated

    def _check_tier1_vetoes(
        self,
        survivors: list[_JudgeRun],
    ) -> list[VetoEvent]:
        """Collect a VetoEvent per Tier 1 dimension where any judge was below floor."""
        events: list[VetoEvent] = []
        for dim in sorted(TIER_1_DIMENSIONS, key=lambda d: d.value):
            floor = TIER_1_FLOOR_THRESHOLDS[dim]
            judge_scores: dict[str, float] = {}
            dissenting: list[str] = []
            for run in survivors:
                assert run.layer3_result is not None
                for ds in run.layer3_result.dimension_scores:
                    if ds.dimension == dim:
                        judge_scores[run.judge_id] = ds.score
                        if ds.score < floor:
                            dissenting.append(run.judge_id)
                        break
            if dissenting:
                events.append(
                    VetoEvent(
                        dimension=dim,
                        floor_threshold=floor,
                        min_score=min(judge_scores.values()),
                        dissenting_judge_ids=dissenting,
                        judge_scores=judge_scores,
                    )
                )
        return events

    def _agreement_level(self, survivors: list[_JudgeRun]) -> float:
        """Fraction of dimensions where max-min judge score <= _AGREEMENT_THRESHOLD.

        With a single survivor, agreement is trivially 1.0 (nothing to disagree
        with). With zero survivors, caller has already returned before reaching
        this function.
        """
        if len(survivors) <= 1:
            return 1.0

        by_dim: dict[RubricDimension, list[float]] = {}
        for run in survivors:
            assert run.layer3_result is not None
            for ds in run.layer3_result.dimension_scores:
                by_dim.setdefault(ds.dimension, []).append(ds.score)

        if not by_dim:
            return 1.0

        concordant = 0
        total = 0
        for _, scores in by_dim.items():
            if len(scores) < 2:
                # Only one judge saw this dimension (other bailed at Tier 1).
                # Count as concordant: no disagreement possible.
                concordant += 1
                total += 1
                continue
            spread = max(scores) - min(scores)
            if spread <= _AGREEMENT_THRESHOLD:
                concordant += 1
            total += 1
        return concordant / total if total else 1.0


def _short_error(exc: BaseException) -> str:
    """Single-line error description for storage in JudgeScore.error."""
    name = type(exc).__name__
    msg = str(exc).strip().splitlines()[0] if str(exc).strip() else ""
    return f"{name}: {msg}" if msg else name
