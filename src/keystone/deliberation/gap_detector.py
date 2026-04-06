"""Research gap detection for L1.5 Deliberation.

Identifies missing evidence from absence reports and low-confidence claims.
Produces a gap report that feeds into the ConfidenceMap and can trigger
additional research rounds.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from keystone.deliberation.aggregator import AggregatedClaim
from keystone.models.research import StructuredFinding

LOW_CONFIDENCE_GAP_THRESHOLD = 0.4


class GapReport(BaseModel):
    """Research gaps identified during deliberation."""

    gaps: list[str] = Field(default_factory=list)
    absence_items: list[str] = Field(default_factory=list)


def detect_gaps(
    findings: list[StructuredFinding],
    aggregated_claims: list[AggregatedClaim],
) -> GapReport:
    """Identify research gaps from absence reports and low-confidence claims.

    Sources of gaps:
    1. Absence reports from L1 agents (what was looked for but not found)
    2. Claims with very low confidence (<0.4) suggest areas needing research
    3. Claims flagged as inconsistent by the consistency check
    4. Explicit gaps reported by L1 agents
    """
    absence_items: list[str] = []
    for finding in findings:
        absence_items.extend(finding.absence_report)

    gaps: list[str] = []
    for claim in aggregated_claims:
        if claim.mean_confidence < LOW_CONFIDENCE_GAP_THRESHOLD:
            gaps.append(
                f"Low confidence ({claim.mean_confidence:.0%}): {claim.claim_text}"
            )
        if not claim.consistency_passed:
            gaps.append(f"Consistency issue: {claim.claim_text}")

    for finding in findings:
        for gap in finding.gaps:
            if gap not in gaps:
                gaps.append(gap)

    return GapReport(gaps=gaps, absence_items=absence_items)
