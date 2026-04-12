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
    gap_provenance: dict[str, list[str]] = Field(default_factory=dict)


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
    gap_provenance: dict[str, list[str]] = {}
    for claim in aggregated_claims:
        if claim.mean_confidence < LOW_CONFIDENCE_GAP_THRESHOLD:
            _record_gap(
                gaps,
                gap_provenance,
                f"Low confidence ({claim.mean_confidence:.0%}): {claim.claim_text}",
                claim.task_ids,
            )
        if not claim.consistency_passed:
            _record_gap(
                gaps,
                gap_provenance,
                f"Consistency issue: {claim.claim_text}",
                claim.task_ids,
            )

    for finding in findings:
        for gap in finding.gaps:
            _record_gap(gaps, gap_provenance, gap, [finding.task_id])

    return GapReport(
        gaps=gaps,
        absence_items=absence_items,
        gap_provenance=gap_provenance,
    )


def _record_gap(
    gaps: list[str],
    gap_provenance: dict[str, list[str]],
    gap_text: str,
    task_ids: list[str],
) -> None:
    """Append a gap once while preserving all originating task IDs."""
    if gap_text not in gaps:
        gaps.append(gap_text)

    existing = gap_provenance.setdefault(gap_text, [])
    for task_id in task_ids:
        if task_id and task_id not in existing:
            existing.append(task_id)
