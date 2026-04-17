"""MVP L3 output: renders pipeline results as structured Markdown.

Stateless renderer. No LLM calls. Takes structured data from all
pipeline stages and produces a Goldman-grade formatted deliverable.
"""

from __future__ import annotations

from keystone.models.citations import CitationManifest
from keystone.models.confidence import ConfidenceMap
from keystone.models.evaluation import EvaluationResult
from keystone.models.research import EngagementSpec, StructuredFinding
from keystone.models.structuring import StructuredOutline


class MarkdownRenderer:
    """Renders pipeline outputs into structured Markdown.

    Sections (in render order):
    1. Title + metadata
    2. Analytical Framework (when L2 outline provided)
    3. Executive Summary (high-confidence claims)
    4. Key Findings (per-task, with confidence tiers)
    5. Areas of Uncertainty (weak + contested claims)
    6. Research Gaps (gaps + absence reports)
    7. Sources (all citations from manifest)
    8. Quality Assessment (evaluation scores)
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

    def _render_framework(self, outline: StructuredOutline | None) -> str:
        if outline is None or not outline.frameworks:
            return ""
        lines = ["## Analytical Framework", ""]
        for hint in outline.frameworks:
            label = hint.framework.value.replace("_", " ").title()
            marker = "primary" if hint.mandatory else "augmenting"
            lines.append(f"- **{label}** ({marker}): {hint.rationale}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Section renderers
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
    def _claim_citation_labels(claim) -> str:
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

    def _render_quality(self, results: list[EvaluationResult]) -> str:
        lines = ["## Quality Assessment"]
        if not results:
            lines.append("\n*No evaluations performed.*")
            return "\n".join(lines)

        passed = sum(1 for r in results if r.passed)
        total = len(results)
        avg_score = sum(r.overall_score for r in results) / total if total else 0.0

        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Tasks Evaluated | {total} |")
        lines.append(f"| Tasks Passed | {passed}/{total} |")
        lines.append(f"| Average Score | {avg_score:.1f}/100 |")

        lines.append("\n### Per-Task Results\n")
        for r in results:
            status = "PASS" if r.passed else "FAIL"
            lines.append(
                f"- **{r.task_id}**: {status} ({r.overall_score:.1f}/100) -- {r.feedback[:120]}"
            )

        return "\n".join(lines)
