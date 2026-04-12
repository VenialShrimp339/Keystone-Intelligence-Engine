"""Confidence map builder for L1.5 Deliberation.

Routes aggregated claims to the appropriate confidence tier based on
methodological agreement ratio. Builds the five-tier ConfidenceMap
output defined in models/confidence.py.

Tier routing:
  >80%  agreement -> HighConfidenceClaim (with curmudgeon challenge)
  60-80%          -> ModerateConfidenceClaim (with sensitivity analysis)
  50-60%          -> WeakConfidenceClaim (DiscoUQ features if available)
  <50%            -> ContestedClaim (steelmanned opposing view)
  no analysts     -> InsufficientEvidenceClaim
"""

from __future__ import annotations

from keystone.deliberation.aggregator import AggregatedClaim
from keystone.deliberation.gap_detector import GapReport
from keystone.deliberation.wwhtb import WWHTBResult
from keystone.models.confidence import (
    ConfidenceMap,
    ContestedClaim,
    HighConfidenceClaim,
    InsufficientEvidenceClaim,
    ModerateConfidenceClaim,
    WeakConfidenceClaim,
)


def build_confidence_map(
    aggregated_claims: list[AggregatedClaim],
    wwhtb_results: list[WWHTBResult],
    gap_report: GapReport,
    engagement_id: str,
    client_id: str,
) -> ConfidenceMap:
    """Build the five-tier confidence map from aggregated claims."""
    wwhtb_by_idx = {r.claim_index: r for r in wwhtb_results}

    high: list[HighConfidenceClaim] = []
    moderate: list[ModerateConfidenceClaim] = []
    weak: list[WeakConfidenceClaim] = []
    contested: list[ContestedClaim] = []
    insufficient: list[InsufficientEvidenceClaim] = []
    # aggregated_claim_id -> task_ids for all claims that have an ID
    provenance_index: dict[str, list[str]] = {}

    for claim in aggregated_claims:
        if claim.total_analysts == 0:
            tier_claim = _build_insufficient(claim)
            insufficient.append(tier_claim)
        else:
            ratio = claim.agreement_ratio
            if ratio > 0.8:
                tier_claim = _build_high(claim)
                high.append(tier_claim)
            elif ratio > 0.6:
                tier_claim = _build_moderate(claim, wwhtb_by_idx)
                moderate.append(tier_claim)
            elif ratio >= 0.5:
                tier_claim = _build_weak(claim, wwhtb_by_idx)
                weak.append(tier_claim)
            else:
                tier_claim = _build_contested(claim)
                contested.append(tier_claim)

        # Build provenance index entry for any claim that has an aggregated_claim_id
        if claim.aggregated_claim_id and claim.task_ids:
            provenance_index[claim.aggregated_claim_id] = claim.task_ids

    return ConfidenceMap(
        engagement_id=engagement_id,
        client_id=client_id,
        high_confidence_above_80pct=high,
        moderate_confidence_60_80pct=moderate,
        weak_confidence_50_60pct=weak,
        contested_below_50pct=contested,
        insufficient_evidence=insufficient,
        gaps_identified=gap_report.gaps,
        absence_report=gap_report.absence_items,
        provenance_index=provenance_index,
    )


def _agreement_str(claim: AggregatedClaim) -> str:
    """Format agreement ratio as human-readable string."""
    agreeing = len(claim.agreeing_analysts)
    total = claim.total_analysts
    types = ", ".join(sorted(claim.agreeing_analysts)) if claim.agreeing_analysts else "none"
    return f"{agreeing}/{total} ({types})"


def _build_high(claim: AggregatedClaim) -> HighConfidenceClaim:
    # Curmudgeon challenge from adversarial analyst or strongest dissenter
    curmudgeon = ""
    if "adversarial" in claim.analyst_reasoning:
        curmudgeon = claim.analyst_reasoning["adversarial"]
    elif claim.dissenting_analysts:
        first_dissenter = claim.dissenting_analysts[0]
        curmudgeon = claim.analyst_reasoning.get(
            first_dissenter, "No specific challenge identified"
        )
    else:
        curmudgeon = "No analyst raised significant objections"

    return HighConfidenceClaim(
        claim=claim.claim_text,
        methodological_agreement=_agreement_str(claim),
        sources=claim.source_count,
        corroboration_count=claim.corroboration_count,
        robustness=(
            f"Mean confidence {claim.mean_confidence:.0%} across "
            f"{claim.total_analysts} methodologies"
        ),
        curmudgeon_challenge=curmudgeon,
        aggregated_claim_id=claim.aggregated_claim_id,
        task_ids=list(claim.task_ids),
    )


def _build_moderate(
    claim: AggregatedClaim,
    wwhtb_by_idx: dict[int, WWHTBResult],
) -> ModerateConfidenceClaim:
    dissent_parts = []
    for at in claim.dissenting_analysts:
        reason = claim.analyst_reasoning.get(at, "")
        dissent_parts.append(f"{at}: {reason}" if reason else at)
    dissent = "; ".join(dissent_parts) if dissent_parts else "Minor methodological differences"

    wwhtb = wwhtb_by_idx.get(claim.index)
    if wwhtb and wwhtb.assumptions:
        sensitivity = f"Key assumptions: {'; '.join(wwhtb.assumptions[:3])}"
    else:
        sensitivity = "No sensitivity analysis triggers identified"

    return ModerateConfidenceClaim(
        claim=claim.claim_text,
        methodological_agreement=_agreement_str(claim),
        dissent=dissent,
        sources=claim.source_count,
        sensitivity=sensitivity,
        aggregated_claim_id=claim.aggregated_claim_id,
        task_ids=list(claim.task_ids),
    )


def _build_weak(
    claim: AggregatedClaim,
    wwhtb_by_idx: dict[int, WWHTBResult],
) -> WeakConfidenceClaim:
    key_issues = [
        claim.analyst_reasoning.get(at, "")
        for at in claim.dissenting_analysts
        if claim.analyst_reasoning.get(at)
    ]
    key_issue = key_issues[0] if key_issues else "Significant methodological disagreement"

    wwhtb = wwhtb_by_idx.get(claim.index)
    if wwhtb and wwhtb.assumptions:
        recommendation = (
            f"Present with uncertainty framing. "
            f"Assumptions: {'; '.join(wwhtb.assumptions[:2])}"
        )
    else:
        recommendation = "Present with prominent uncertainty framing"

    return WeakConfidenceClaim(
        claim=claim.claim_text,
        methodological_agreement=_agreement_str(claim),
        key_issue=key_issue,
        sources=claim.source_count,
        recommendation=recommendation,
        aggregated_claim_id=claim.aggregated_claim_id,
        task_ids=list(claim.task_ids),
    )


def _build_contested(claim: AggregatedClaim) -> ContestedClaim:
    disagreements = [
        claim.analyst_reasoning.get(at, "")
        for at in claim.dissenting_analysts
        if claim.analyst_reasoning.get(at)
    ]
    key_disagreement = disagreements[0] if disagreements else "Fundamental methodological split"

    # Steelmanned opposing view from strongest dissenter
    dissent_scores = {
        at: claim.analyst_scores.get(at, 0.5) for at in claim.dissenting_analysts
    }
    if dissent_scores:
        strongest_dissenter = min(dissent_scores, key=dissent_scores.get)  # type: ignore[arg-type]
        steelmanned = claim.analyst_reasoning.get(
            strongest_dissenter,
            "Opposing view could not be steelmanned from available evidence",
        )
    else:
        steelmanned = "No clear opposing position identified"

    return ContestedClaim(
        claim=claim.claim_text,
        methodological_agreement=_agreement_str(claim),
        key_disagreement=key_disagreement,
        sources=claim.source_count,
        steelmanned_opposing_view=steelmanned,
        aggregated_claim_id=claim.aggregated_claim_id,
        task_ids=list(claim.task_ids),
    )


def _build_insufficient(claim: AggregatedClaim) -> InsufficientEvidenceClaim:
    return InsufficientEvidenceClaim(
        claim=claim.claim_text,
        reason="No analyst methodology was able to evaluate this claim",
        priority="high" if claim.source_count == 0 else "medium",
        aggregated_claim_id=claim.aggregated_claim_id,
        task_ids=list(claim.task_ids),
    )
