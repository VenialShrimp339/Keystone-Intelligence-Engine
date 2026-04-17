"""Per-task section text assembly for the L4 Evaluator.

Builds the `output_text` string that the Evaluator scores. The text is
structured as a consulting-brief fragment: lede, evidence chain, analytical
significance, and an absence report. Deterministic — no LLM calls.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from keystone.models.confidence import ConfidenceMap
    from keystone.models.research import FindingClaim, StructuredFinding
    from keystone.models.structuring import AnalyticalFramework
    from keystone.models.tasks import ResearchTask


def render_task_section_text(
    *,
    task: ResearchTask,
    finding: StructuredFinding | None,
    framework: AnalyticalFramework | None,
    engagement_type_label: str,
    confidence_map: ConfidenceMap,
) -> str:
    """Assemble the per-task analytical narrative for L4 scoring.

    The text reflects structuring decisions the rubric cares about:
    - A named analytical lede so Narrative Coherence / Analytical Depth
      have a target.
    - Evidence threaded to claims with inline citation refs so Source
      Quality and Layer-2 citation checks have a handle.
    - An "Analytical significance" block that differentiates assertion
      from inference.
    - Explicit caveats and an absence report so Intellectual Honesty
      and Calibrated Confidence can score.
    - Cross-reference to the confidence map (dissent, sensitivity,
      robustness) for claims aggregated into confirmed tiers.
    """
    parts: list[str] = []
    parts.append(f"# {task.deliverable_destination}")
    parts.append("")
    framework_label = framework.value.replace("_", " ").title() if framework else "None"
    parts.append(f"**Framework:** {framework_label}  (engagement_type={engagement_type_label})")
    parts.append(f"**Task:** {task.id}  ")
    parts.append(f"**Category:** {task.effective_category}  ")
    parts.append(f"**Decision-usefulness target:** {task.target_decision_usefulness}/5")
    parts.append("")

    if finding is None:
        parts.append("## Status")
        parts.append("")
        parts.append(
            "No finding was produced for this task. Downstream scoring must "
            "reflect the absence rather than infer content."
        )
        return "\n".join(parts) + "\n"

    sorted_claims = sorted(
        finding.claims,
        key=lambda c: (c.confidence, len(c.citation_ids or c.citations)),
        reverse=True,
    )

    # Lede: the strongest claim, stated as an assertion when confidence is high,
    # otherwise as a qualified assessment.
    if sorted_claims:
        lede = sorted_claims[0]
        parts.append("## Lede")
        parts.append("")
        parts.append(_lede_statement(lede))
        parts.append("")

    parts.append("## Evidence chain")
    parts.append("")
    for idx, claim in enumerate(sorted_claims, start=1):
        parts.append(
            f"{idx}. **{claim.text}** "
            f"[{claim.confidence_tier.value.replace('_', ' ').title()}, "
            f"{claim.confidence:.0%}]"
        )
        parts.append(f"   Evidence: {claim.evidence}")
        citation_refs = _citation_labels(claim)
        if citation_refs:
            parts.append(f"   Citations: {citation_refs}")
        if claim.caveats:
            parts.append(f"   Caveats: {'; '.join(claim.caveats)}")

    parts.append("")

    cross_ref = _confidence_cross_reference(sorted_claims, confidence_map)
    if cross_ref:
        parts.append("## Analytical significance")
        parts.append("")
        for line in cross_ref:
            parts.append(f"- {line}")
        parts.append("")

    if finding.gaps:
        parts.append("## Research gaps for this task")
        parts.append("")
        for gap in finding.gaps:
            parts.append(f"- {gap}")
        parts.append("")

    if finding.absence_report:
        parts.append("## Absence report")
        parts.append("")
        parts.append(
            "*Items the agent actively looked for but did not find. "
            "Analytically significant -- treat as signal, not omission.*"
        )
        parts.append("")
        for item in finding.absence_report:
            parts.append(f"- {item}")
        parts.append("")

    parts.append("## Acceptance criteria (from task)")
    parts.append("")
    for criterion in task.acceptance_criteria:
        parts.append(f"- {criterion}")

    return "\n".join(parts) + "\n"


def _lede_statement(claim: FindingClaim) -> str:
    """Produce a framework-appropriate lede from the strongest claim."""
    if claim.confidence >= 0.8:
        return claim.text
    if claim.confidence >= 0.6:
        return f"The evidence indicates, with moderate confidence, that {claim.text.rstrip('.')}."
    return (
        f"The evidence weakly supports the view that {claim.text.rstrip('.')}. "
        "Confidence framing should be prominent in any downstream use."
    )


def _citation_labels(claim: FindingClaim) -> str:
    """Canonical citation IDs preferred; fall back to source-instance IDs."""
    citation_ids = claim.citation_ids or [c.citation_id for c in claim.citations]
    return ", ".join(citation_ids)


def _confidence_cross_reference(
    claims: list[FindingClaim],
    confidence_map: ConfidenceMap,
) -> list[str]:
    """Surface robustness/dissent/key-issue text from the aggregated confidence map.

    Claims at L1 confidence are pre-aggregation. Once the confidence map
    exists, each tier carries structured metadata (robustness for high,
    dissent+sensitivity for moderate, key_issue for weak, etc.). Match by
    claim text to pull those annotations forward into the evaluator view.
    """
    lines: list[str] = []
    claim_text_set = {c.text.strip().lower() for c in claims}

    for hc in confidence_map.high_confidence_above_80pct:
        if hc.claim.strip().lower() in claim_text_set:
            lines.append(
                f"Robustness (high-confidence): {hc.robustness}. "
                f"Curmudgeon challenge: {hc.curmudgeon_challenge}"
            )
    for mc in confidence_map.moderate_confidence_60_80pct:
        if mc.claim.strip().lower() in claim_text_set:
            lines.append(
                f"Dissent (moderate-confidence): {mc.dissent}. Sensitivity: {mc.sensitivity}"
            )
    for wc in confidence_map.weak_confidence_50_60pct:
        if wc.claim.strip().lower() in claim_text_set:
            lines.append(
                f"Key issue (weak-confidence): {wc.key_issue}. Recommendation: {wc.recommendation}"
            )
    for cc in confidence_map.contested_below_50pct:
        if cc.claim.strip().lower() in claim_text_set:
            lines.append(
                f"Contested: {cc.key_disagreement}. "
                f"Steelmanned opposing view: {cc.steelmanned_opposing_view}"
            )
    return lines
