"""MVP L3 output: renders pipeline results as structured Markdown.

Stateless renderer. No LLM calls. The production path consumes the L2
``StructuredOutline`` as the source of section structure, with inline
numbered citations keyed to the ``CitationManifest``. The outline's
nine section types (executive summary, framework analysis, branches,
moderate / weak / contested, gaps, insufficient, absence) map directly
onto the consulting-brief layout the Evaluator is calibrated to score.

A legacy path (``outline=None``) preserves the pre-L2 layout for callers
that have not yet wired in Content Structuring.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from keystone.models.citations import CitationManifest, ConfidenceTier
from keystone.models.evaluation import RubricDimension
from keystone.models.structuring import (
    OutlineItem,
    OutlineSectionType,
    StructuredOutline,
    StructuredSection,
)

if TYPE_CHECKING:
    from keystone.models.confidence import ConfidenceMap
    from keystone.models.evaluation import EvaluationResult
    from keystone.models.research import EngagementSpec, FindingClaim, StructuredFinding


_TIER_LABELS: dict[ConfidenceTier, str] = {
    ConfidenceTier.HIGH: "HIGH",
    ConfidenceTier.MODERATE: "MODERATE",
    ConfidenceTier.WEAK: "WEAK",
    ConfidenceTier.CONTESTED: "CONTESTED",
    ConfidenceTier.INSUFFICIENT: "INSUFFICIENT",
}


class MarkdownRenderer:
    """Renders pipeline outputs into structured Markdown.

    Outline-driven section order (production path):

    1. Title + engagement metadata
    2. Executive Summary (headline findings, confidence distribution, caveats)
    3. Analytical Framework (which frameworks and why)
    4. Key Findings (per issue-tree branch, with claim tier + evidence chain)
    5. Areas of Uncertainty (moderate + weak + contested claims)
    6. Evidence Gaps (identified gaps + insufficient evidence)
    7. Absence Report (topics actively investigated with no evidence)
    8. Evaluation Summary (pass rate, scores, dimension averages)
    9. Sources (numbered list, referenced inline as ``[N]``)

    Legacy ``outline=None`` path preserves the previous layout.
    """

    def render(
        self,
        spec: EngagementSpec,
        findings: list[StructuredFinding],
        confidence_map: ConfidenceMap,
        evaluation_results: list[EvaluationResult],
        manifest: CitationManifest,
        outline: StructuredOutline | None = None,
    ) -> str:
        citation_index = self._build_citation_index(manifest)

        if outline is not None:
            sections = [
                self._render_title(spec),
                self._render_exec_summary_outline(outline, citation_index),
                self._render_framework_outline(outline),
                self._render_key_findings_outline(outline, citation_index),
                self._render_uncertainty_outline(outline, citation_index),
                self._render_evidence_gaps_outline(outline, citation_index),
                self._render_absence_outline(outline),
                self._render_evaluation_summary(evaluation_results),
                self._render_sources(manifest),
            ]
        else:
            sections = [
                self._render_title(spec),
                self._render_framework(outline),
                self._render_executive_summary(confidence_map),
                self._render_key_findings(findings, confidence_map),
                self._render_uncertainty(confidence_map),
                self._render_gaps(confidence_map, findings),
                self._render_sources(manifest),
                self._render_quality(evaluation_results),
            ]

        return "\n\n".join(s for s in sections if s) + "\n"

    # ------------------------------------------------------------------
    # Citation index (shared by both paths)
    # ------------------------------------------------------------------

    @staticmethod
    def _build_citation_index(manifest: CitationManifest) -> dict[str, int]:
        """Assign each citation a 1-based number used by inline ``[N]`` refs."""
        return {c.citation_id: idx + 1 for idx, c in enumerate(manifest.citations)}

    @staticmethod
    def _format_inline_citations(
        citation_ids: list[str],
        index: dict[str, int],
    ) -> str:
        if not citation_ids:
            return ""
        labels: list[str] = []
        for cid in citation_ids:
            if cid in index:
                labels.append(f"[{index[cid]}]")
            else:
                # Unknown citation (not in manifest) — fall back to raw ID.
                labels.append(f"[{cid}]")
        return " " + "".join(labels)

    # ------------------------------------------------------------------
    # Title (shared)
    # ------------------------------------------------------------------

    def _render_title(self, spec: EngagementSpec) -> str:
        rs = spec.research_spec
        lines = [
            f"# {rs.title}",
            "",
            f"**Engagement ID:** {rs.engagement_id}  ",
            f"**Client:** {rs.client_id}  ",
            f"**Type:** {rs.engagement_type.value.title()}  ",
            f"**Specification Version:** {rs.specification_version}",
        ]
        if rs.day_1_hypothesis:
            lines.append(f"\n**Day-1 Hypothesis:** {rs.day_1_hypothesis}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Outline-driven sections
    # ------------------------------------------------------------------

    def _render_exec_summary_outline(
        self,
        outline: StructuredOutline,
        citation_index: dict[str, int],
    ) -> str:
        lines = ["## Executive Summary", ""]

        counts = _confidence_counts(outline)
        lines.append(
            "_Confidence distribution — "
            f"high: {counts['high']}, moderate: {counts['moderate']}, "
            f"weak: {counts['weak']}, contested: {counts['contested']}, "
            f"insufficient: {counts['insufficient']}._"
        )
        lines.append("")

        exec_items = [
            item
            for section in _sections_of_type(outline, OutlineSectionType.EXECUTIVE_SUMMARY)
            for item in section.items
        ]
        if exec_items:
            lines.append("**Headline findings (high confidence):**")
            lines.append("")
            for item in exec_items:
                citations = self._format_inline_citations(item.citation_ids, citation_index)
                lines.append(f"- **{item.text}** [HIGH]{citations}")
                if item.note:
                    lines.append(f"  - {item.note}")
        else:
            lines.append("*No claims reached high confidence (>80% methodological agreement).*")

        self._append_exec_caveat(lines, outline)
        return "\n".join(lines)

    @staticmethod
    def _append_exec_caveat(lines: list[str], outline: StructuredOutline) -> None:
        uncovered = len(outline.uncovered_branch_ids)
        if uncovered:
            lines.append("")
            lines.append(
                f"_Critical caveat: {uncovered} issue-tree branch(es) remain "
                "uncovered by the current evidence base._"
            )

    def _render_framework_outline(self, outline: StructuredOutline) -> str:
        # Prefer the L2-built FRAMEWORK_ANALYSIS section when available.
        for section in _sections_of_type(outline, OutlineSectionType.FRAMEWORK_ANALYSIS):
            if section.items:
                lines = ["## Analytical Framework", ""]
                for item in section.items:
                    lines.append(f"- {item.text}")
                return "\n".join(lines)

        # Fall back to the framework hint list (used by callers that build an
        # outline without running the full L2 structurer).
        if not outline.frameworks:
            return ""
        lines = ["## Analytical Framework", ""]
        for hint in outline.frameworks:
            label = hint.framework.value.replace("_", " ").title()
            marker = "primary" if hint.mandatory else "augmenting"
            lines.append(f"- **{label}** ({marker}): {hint.rationale}")
        return "\n".join(lines)

    def _render_key_findings_outline(
        self,
        outline: StructuredOutline,
        citation_index: dict[str, int],
    ) -> str:
        branch_sections = _sections_of_type(outline, OutlineSectionType.BRANCH)
        lines = ["## Key Findings"]
        if not branch_sections:
            lines.append("")
            lines.append("*No research branches produced findings.*")
            return "\n".join(lines)

        for section in branch_sections:
            lines.append("")
            lines.append(f"### {section.title}")
            if section.framework is not None:
                framework_label = section.framework.value.replace("_", " ").title()
                lines.append(f"*Applied framework: {framework_label}*")
            lines.append("")
            for item in section.items:
                lines.extend(self._format_claim_item(item, citation_index))
        return "\n".join(lines)

    def _render_uncertainty_outline(
        self,
        outline: StructuredOutline,
        citation_index: dict[str, int],
    ) -> str:
        lines = ["## Areas of Uncertainty"]
        rendered_any = False

        subsections: list[tuple[OutlineSectionType, str, str | None]] = [
            (
                OutlineSectionType.MODERATE,
                "Moderate Confidence (60-80%)",
                "_Claims with partial methodological agreement; "
                "presented with explicit sensitivity analysis._",
            ),
            (
                OutlineSectionType.WEAK,
                "Weak Confidence (50-60%)",
                "_Claims where disagreement exceeds the noise floor; "
                "how-to-be-wrong analysis included._",
            ),
            (
                OutlineSectionType.CONTESTED,
                "Contested Claims (<50%)",
                "_Claims with steelmanned opposing views; the analytical record "
                "here is the disagreement itself._",
            ),
        ]

        for section_type, heading, preamble in subsections:
            for section in _sections_of_type(outline, section_type):
                if not section.items:
                    continue
                rendered_any = True
                lines.append("")
                lines.append(f"### {heading}")
                if preamble is not None:
                    lines.append(preamble)
                lines.append("")
                tier = _section_type_to_tier(section_type)
                badge = f" [{_TIER_LABELS[tier]}]" if tier is not None else ""
                for item in section.items:
                    citations = self._format_inline_citations(item.citation_ids, citation_index)
                    lines.append(f"- **{item.text}**{badge}{citations}")
                    if item.note:
                        lines.append(f"  - {item.note}")

        if not rendered_any:
            lines.append("")
            lines.append("*No moderate, weak, or contested claims identified.*")
        return "\n".join(lines)

    def _render_evidence_gaps_outline(
        self,
        outline: StructuredOutline,
        citation_index: dict[str, int],
    ) -> str:
        lines = ["## Evidence Gaps"]
        rendered_any = False

        for section in _sections_of_type(outline, OutlineSectionType.GAPS):
            if not section.items:
                continue
            rendered_any = True
            lines.append("")
            lines.append("### Identified Gaps")
            lines.append(
                "_What we looked for but couldn't find. Follow-up research should target these._"
            )
            lines.append("")
            for item in section.items:
                lines.append(f"- {item.text}")

        for section in _sections_of_type(outline, OutlineSectionType.INSUFFICIENT):
            if not section.items:
                continue
            rendered_any = True
            lines.append("")
            lines.append("### Insufficient Evidence")
            lines.append("_Claims where the evidence base is too sparse to assess confidence._")
            lines.append("")
            for item in section.items:
                citations = self._format_inline_citations(item.citation_ids, citation_index)
                lines.append(f"- **{item.text}** [INSUFFICIENT]{citations}")
                if item.note:
                    lines.append(f"  - {item.note}")

        if outline.uncovered_branch_ids:
            rendered_any = True
            lines.append("")
            lines.append("### Uncovered Issue-Tree Branches")
            lines.append("_Branches from the MECE decomposition without renderable evidence._")
            lines.append("")
            for branch_id in outline.uncovered_branch_ids:
                lines.append(f"- {branch_id}")

        if not rendered_any:
            lines.append("")
            lines.append("*No evidence gaps identified.*")
        return "\n".join(lines)

    def _render_absence_outline(self, outline: StructuredOutline) -> str:
        absence_sections = _sections_of_type(outline, OutlineSectionType.ABSENCE)
        items = [item for section in absence_sections for item in section.items]
        if not items:
            return ""
        lines = [
            "## Absence Report",
            "",
            "_Topics actively investigated where no evidence surfaced. "
            "Absence is analytically significant — it narrows the hypothesis space._",
            "",
        ]
        for item in items:
            lines.append(f"- {item.text}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Claim formatting helper
    # ------------------------------------------------------------------

    @staticmethod
    def _format_claim_item(
        item: OutlineItem,
        citation_index: dict[str, int],
    ) -> list[str]:
        """Render a BRANCH-style claim with tier badge, citations, and evidence."""
        tier_badge = ""
        if item.confidence_tier is not None:
            label = _TIER_LABELS[item.confidence_tier]
            if item.confidence is not None:
                tier_badge = f" [{label}, {item.confidence:.0%}]"
            else:
                tier_badge = f" [{label}]"
        citations = MarkdownRenderer._format_inline_citations(item.citation_ids, citation_index)
        lines = [f"- **{item.text}**{tier_badge}{citations}"]
        if item.evidence:
            lines.append(f"  - Evidence: {item.evidence}")
        if item.caveats:
            lines.append(f"  - Caveats: {'; '.join(item.caveats)}")
        if item.note:
            lines.append(f"  - {item.note}")
        return lines

    # ------------------------------------------------------------------
    # Evaluation Summary (outline path)
    # ------------------------------------------------------------------

    def _render_evaluation_summary(
        self,
        results: list[EvaluationResult],
    ) -> str:
        lines = ["## Evaluation Summary"]
        if not results:
            lines.append("")
            lines.append("*No evaluations performed.*")
            return "\n".join(lines)

        total = len(results)
        passed = sum(1 for r in results if r.passed)
        avg_score = sum(r.overall_score for r in results) / total

        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Tasks Evaluated | {total} |")
        lines.append(f"| Tasks Passed | {passed}/{total} |")
        lines.append(f"| Average Score | {avg_score:.1f}/100 |")

        dimension_table = _dimension_score_table(results)
        if dimension_table:
            lines.append("")
            lines.append("### Dimension Scores (average across tasks)")
            lines.append("")
            lines.append("| Dimension | Average Score |")
            lines.append("|-----------|---------------|")
            for row in dimension_table:
                lines.append(f"| {row[0]} | {row[1]:.1f}/100 |")

        lines.append("")
        lines.append("### Per-Task Results")
        lines.append("")
        for r in results:
            status = "PASS" if r.passed else "FAIL"
            feedback = r.feedback[:120]
            lines.append(f"- **{r.task_id}**: {status} ({r.overall_score:.1f}/100) -- {feedback}")
            process_line = _render_process_assessment(r)
            if process_line:
                lines.append(f"  - {process_line}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Sources (shared)
    # ------------------------------------------------------------------

    def _render_sources(self, manifest: CitationManifest) -> str:
        lines = ["## Sources"]
        if not manifest.citations:
            lines.append("\n*No citations in manifest.*")
            return "\n".join(lines)

        lines.append("")
        for i, citation in enumerate(manifest.citations, 1):
            authors = ", ".join(citation.authors) if citation.authors else "Unknown"
            date_str = str(citation.date_published) if citation.date_published else "n.d."
            pub = f" *{citation.publication}*." if citation.publication else ""

            lines.append(
                f"{i}. [{citation.citation_id}] {authors} ({date_str}). "
                f'"{citation.title}".{pub} {citation.url}'
            )
            status_parts = []
            if citation.url_live is not None:
                status_parts.append("live" if citation.url_live else "dead")
            if citation.quality_score is not None:
                status_parts.append(f"quality: {citation.quality_score:.2f}")
            if citation.found_by_agents:
                status_parts.append(f"found by: {', '.join(citation.found_by_agents)}")
            if status_parts:
                lines.append(f"   *({'; '.join(status_parts)})*")

        if manifest.dead_urls:
            lines.append(
                f"\n**Dead URLs:** {len(manifest.dead_urls)} citation(s) with unreachable URLs."
            )

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Legacy path (outline=None) — unchanged output format
    # ------------------------------------------------------------------

    def _render_framework(self, outline: StructuredOutline | None) -> str:
        if outline is None or not outline.frameworks:
            return ""
        lines = ["## Analytical Framework", ""]
        for hint in outline.frameworks:
            label = hint.framework.value.replace("_", " ").title()
            marker = "primary" if hint.mandatory else "augmenting"
            lines.append(f"- **{label}** ({marker}): {hint.rationale}")
        return "\n".join(lines)

    def _render_executive_summary(self, cm: ConfidenceMap) -> str:
        lines = ["## Executive Summary"]
        if not cm.high_confidence_above_80pct:
            lines.append("\n*No claims reached high confidence (>80% methodological agreement).*")
            return "\n".join(lines)

        lines.append("")
        for claim in cm.high_confidence_above_80pct:
            lines.append(f"- **{claim.claim}**")
            lines.append(
                f"  - Agreement: {claim.methodological_agreement} "
                f"| Sources: {claim.sources} "
                f"| Corroboration: {claim.corroboration_count}"
            )
            lines.append(f"  - Robustness: {claim.robustness}")
            lines.append(f"  - Curmudgeon challenge: {claim.curmudgeon_challenge}")

        return "\n".join(lines)

    def _render_key_findings(
        self,
        findings: list[StructuredFinding],
        cm: ConfidenceMap,
    ) -> str:
        lines = ["## Key Findings"]
        if not findings:
            lines.append("\n*No findings were produced by research agents.*")
            return "\n".join(lines)

        for finding in findings:
            lines.append(f"\n### Task: {finding.task_id}")
            lines.append(f"*Agent: {finding.agent_id} ({finding.agent_type})*\n")

            for claim in finding.claims:
                tier_label = claim.confidence_tier.value.replace("_", " ").title()
                lines.append(f"- **{claim.text}** [{tier_label}, {claim.confidence:.0%}]")
                cite_ids = self._claim_citation_labels(claim)
                if cite_ids:
                    lines.append(f"  - Sources: {cite_ids}")
                if claim.caveats:
                    lines.append(f"  - Caveats: {'; '.join(claim.caveats)}")

        # Moderate confidence claims
        if cm.moderate_confidence_60_80pct:
            lines.append("\n### Moderate Confidence Findings (60-80%)")
            for claim in cm.moderate_confidence_60_80pct:
                lines.append(f"- **{claim.claim}** ({claim.methodological_agreement})")
                lines.append(f"  - Dissent: {claim.dissent}")
                lines.append(f"  - Sensitivity: {claim.sensitivity}")

        return "\n".join(lines)

    @staticmethod
    def _claim_citation_labels(claim: FindingClaim) -> str:
        citation_ids = claim.citation_ids or [c.citation_id for c in claim.citations]
        return ", ".join(citation_ids)

    def _render_uncertainty(self, cm: ConfidenceMap) -> str:
        lines = ["## Areas of Uncertainty"]
        has_content = False

        if cm.weak_confidence_50_60pct:
            has_content = True
            lines.append("\n### Weak Confidence (50-60%)")
            for claim in cm.weak_confidence_50_60pct:
                lines.append(f"- **{claim.claim}** ({claim.methodological_agreement})")
                lines.append(f"  - Key issue: {claim.key_issue}")
                lines.append(f"  - Recommendation: {claim.recommendation}")

        if cm.contested_below_50pct:
            has_content = True
            lines.append("\n### Contested Claims (<50%)")
            for claim in cm.contested_below_50pct:
                lines.append(f"- **{claim.claim}** ({claim.methodological_agreement})")
                lines.append(f"  - Key disagreement: {claim.key_disagreement}")
                lines.append(f"  - Opposing view: {claim.steelmanned_opposing_view}")

        if not has_content:
            lines.append("\n*No weak or contested claims identified.*")

        return "\n".join(lines)

    def _render_gaps(self, cm: ConfidenceMap, findings: list[StructuredFinding]) -> str:
        lines = ["## Research Gaps"]
        has_content = False

        if cm.gaps_identified:
            has_content = True
            lines.append("\n### Identified Gaps")
            for gap in cm.gaps_identified:
                lines.append(f"- {gap}")

        if cm.insufficient_evidence:
            has_content = True
            lines.append("\n### Insufficient Evidence")
            for claim in cm.insufficient_evidence:
                lines.append(f"- **{claim.claim}**: {claim.reason} (Priority: {claim.priority})")

        # Absence reports from findings
        absence_items = []
        for f in findings:
            absence_items.extend(f.absence_report)
        if absence_items:
            has_content = True
            lines.append("\n### Absence Reports")
            lines.append("*What was looked for but not found (analytically significant):*\n")
            for item in absence_items:
                lines.append(f"- {item}")

        if not has_content:
            lines.append("\n*No research gaps identified.*")

        return "\n".join(lines)

    def _render_quality(self, results: list[EvaluationResult]) -> str:
        lines = ["## Quality Assessment"]
        if not results:
            lines.append("\n*No evaluations performed.*")
            return "\n".join(lines)

        passed = sum(1 for r in results if r.passed)
        total = len(results)
        avg_score = sum(r.overall_score for r in results) / total if total else 0.0

        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Tasks Evaluated | {total} |")
        lines.append(f"| Tasks Passed | {passed}/{total} |")
        lines.append(f"| Average Score | {avg_score:.1f}/100 |")

        lines.append("\n### Per-Task Results\n")
        for r in results:
            status = "PASS" if r.passed else "FAIL"
            lines.append(
                f"- **{r.task_id}**: {status} ({r.overall_score:.1f}/100) -- {r.feedback[:120]}"
            )
            process_line = _render_process_assessment(r)
            if process_line:
                lines.append(f"  - {process_line}")

        return "\n".join(lines)


# ----------------------------------------------------------------------
# Module-private helpers
# ----------------------------------------------------------------------


def _render_process_assessment(result: EvaluationResult) -> str:
    """One-line Layer 4 process summary for a task, or empty when L4 did not run.

    Output shape::

        "Process Assessment: 72/100 -- Flags: LOW_SOURCE_DIVERSITY, NO_MULTI_ROUND"

    Empty string is returned when ``layer4_results`` is ``None`` so the
    renderer can skip the bullet entirely without scattering conditionals
    through both the outline and legacy code paths.
    """

    layer4 = result.layer4_results
    if layer4 is None:
        return ""
    score = layer4.process_quality_score
    raw_flags = list(layer4.process_flags) if layer4.process_flags else []
    # ``process_flags`` is typed ``list[str]`` but historical emitters
    # have used the ``ProcessFlag`` StrEnum directly, so handle both.
    flags = [getattr(f, "value", f).upper() for f in raw_flags]
    prefix = f"Process Assessment: {score:.0f}/100"
    if flags:
        return f"{prefix} -- Flags: {', '.join(flags)}"
    return f"{prefix} -- no process flags raised"


def _sections_of_type(
    outline: StructuredOutline,
    section_type: OutlineSectionType,
) -> list[StructuredSection]:
    return [s for s in outline.sections if s.section_type == section_type]


def _confidence_counts(outline: StructuredOutline) -> dict[str, int]:
    mapping: dict[OutlineSectionType, str] = {
        OutlineSectionType.EXECUTIVE_SUMMARY: "high",
        OutlineSectionType.MODERATE: "moderate",
        OutlineSectionType.WEAK: "weak",
        OutlineSectionType.CONTESTED: "contested",
        OutlineSectionType.INSUFFICIENT: "insufficient",
    }
    counts: dict[str, int] = {v: 0 for v in mapping.values()}
    for section in outline.sections:
        bucket = mapping.get(section.section_type)
        if bucket is not None:
            counts[bucket] += len(section.items)
    return counts


def _section_type_to_tier(section_type: OutlineSectionType) -> ConfidenceTier | None:
    return {
        OutlineSectionType.MODERATE: ConfidenceTier.MODERATE,
        OutlineSectionType.WEAK: ConfidenceTier.WEAK,
        OutlineSectionType.CONTESTED: ConfidenceTier.CONTESTED,
    }.get(section_type)


def _dimension_score_table(
    results: list[EvaluationResult],
) -> list[tuple[str, float]]:
    """Return [(dimension_label, average_score)] across evaluations with layer3 data."""
    totals: dict[RubricDimension, float] = defaultdict(float)
    counts: dict[RubricDimension, int] = defaultdict(int)
    for result in results:
        if result.layer3_results is None:
            continue
        for ds in result.layer3_results.dimension_scores:
            totals[ds.dimension] += ds.score
            counts[ds.dimension] += 1

    if not counts:
        return []

    rows: list[tuple[str, float]] = []
    for dimension in RubricDimension:
        if counts.get(dimension, 0) == 0:
            continue
        avg = totals[dimension] / counts[dimension]
        label = dimension.value.replace("_", " ").title()
        rows.append((label, avg))
    return rows
