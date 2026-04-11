"""Builds StructuredFinding from raw agent output.

Structural enforcement (not prompt-based):
- Every claim MUST have at least one Citation
- Every claim MUST have a confidence score (0-1)
- Absence report MUST be non-empty
- Condensed output: 1000-2000 tokens
- Full artifact written to raw/ directory
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from keystone.models.citations import Citation, ConfidenceTier
from keystone.models.research import FindingClaim, FindingStatus, StructuredFinding

logger = logging.getLogger(__name__)

CHARS_PER_TOKEN = 4
MIN_CONDENSED_TOKENS = 1000
MAX_CONDENSED_TOKENS = 2000


class FindingValidationError(Exception):
    """Raised when a finding fails structural validation."""

    def __init__(self, issues: list[str]) -> None:
        self.issues = issues
        super().__init__(f"Finding validation failed: {'; '.join(issues)}")


def _tier_from_confidence(confidence: float) -> ConfidenceTier:
    """Map numerical confidence to the five-tier taxonomy."""
    if confidence >= 0.8:
        return ConfidenceTier.HIGH
    if confidence >= 0.6:
        return ConfidenceTier.MODERATE
    if confidence >= 0.5:
        return ConfidenceTier.WEAK
    if confidence > 0.0:
        return ConfidenceTier.CONTESTED
    return ConfidenceTier.INSUFFICIENT


class FindingWriter:
    """Builds and validates StructuredFinding from raw agent output."""

    def __init__(self, artifact_dir: Path | None = None) -> None:
        self._artifact_dir = artifact_dir

    def build_finding(
        self,
        *,
        task_id: str,
        agent_id: str,
        engagement_id: str,
        client_id: str,
        agent_type: str,
        raw_claims: list[dict],
        absence_report: list[str],
        sources_consulted: int,
        tokens_consumed: int,
        status: FindingStatus = FindingStatus.COMPLETE,
        gaps: list[str] | None = None,
    ) -> StructuredFinding:
        """Build a StructuredFinding from raw agent output.

        raw_claims: list of dicts with keys:
            text: str
            evidence: str
            citations: list[Citation]  (already-built Citation objects)
            confidence: float (0-1)
            caveats: list[str] (optional)

        Validates claims individually. Valid claims are kept; invalid claims
        are recorded in dropped_claims with their reasons. Only raises
        FindingValidationError when the finding is entirely unsalvageable
        (no valid claims AND no absence report).
        """
        finding_issues: list[str] = []

        if not absence_report:
            finding_issues.append("Absence report must be non-empty")

        claims: list[FindingClaim] = []
        dropped_claims: list[dict] = []

        for i, raw in enumerate(raw_claims):
            claim_issues = self._validate_raw_claim(raw, i)
            if claim_issues:
                dropped_claims.append({
                    "index": i,
                    "text": raw.get("text", ""),
                    "reasons": claim_issues,
                })
                logger.debug(
                    "Dropped claim %d: %s", i, "; ".join(claim_issues)
                )
                continue

            claim_id = f"{engagement_id}_{task_id}_{uuid.uuid4().hex[:8]}"
            citation_ids = [cit.citation_id for cit in raw["citations"]]

            claims.append(
                FindingClaim(
                    text=raw["text"],
                    evidence=raw["evidence"],
                    citations=raw["citations"],
                    confidence=raw["confidence"],
                    confidence_tier=_tier_from_confidence(raw["confidence"]),
                    caveats=raw.get("caveats", []),
                    claim_id=claim_id,
                    citation_ids=citation_ids,
                )
            )

        if dropped_claims:
            logger.warning(
                "Agent %s task %s: dropped %d/%d claims during validation",
                agent_id,
                task_id,
                len(dropped_claims),
                len(raw_claims),
            )

        # Finding-level validation: absence report is always required
        if finding_issues:
            raise FindingValidationError(finding_issues)

        # When ALL claims failed validation there is nothing to salvage -- fail loudly
        if not claims:
            reasons = "; ".join(
                d["reasons"][0] for d in dropped_claims if d.get("reasons")
            )
            raise FindingValidationError(
                [f"All {len(dropped_claims)} claims failed validation: {reasons}"]
            )

        # Downgrade status to PARTIAL when some claims were salvaged (dropped > 0)
        effective_status = status
        if dropped_claims and claims:
            effective_status = FindingStatus.PARTIAL

        artifact_path = None
        if self._artifact_dir:
            artifact_path = str(
                self._artifact_dir
                / engagement_id
                / "memory"
                / "raw"
                / f"{agent_id}_{task_id}.md"
            )

        return StructuredFinding(
            task_id=task_id,
            agent_id=agent_id,
            engagement_id=engagement_id,
            client_id=client_id,
            agent_type=agent_type,
            claims=claims,
            status=effective_status,
            gaps=gaps or [],
            artifact_path=artifact_path,
            absence_report=absence_report,
            sources_consulted=sources_consulted,
            tokens_consumed=tokens_consumed,
            dropped_claims=dropped_claims,
        )

    def write_artifact(self, finding: StructuredFinding) -> str | None:
        """Write the full artifact to raw/ directory. Returns the path."""
        if not self._artifact_dir or not finding.artifact_path:
            return None

        artifact = Path(finding.artifact_path)
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(self._render_artifact(finding))
        return finding.artifact_path

    def validate_condensed_size(self, finding: StructuredFinding) -> bool:
        """Check that the condensed output is within 1000-2000 tokens."""
        text = self._condensed_text(finding)
        tokens = len(text) // CHARS_PER_TOKEN
        return MIN_CONDENSED_TOKENS <= tokens <= MAX_CONDENSED_TOKENS

    def _validate_raw_claim(self, raw: dict, index: int) -> list[str]:
        """Validate a single raw claim dict."""
        issues: list[str] = []
        prefix = f"Claim {index}"

        if not raw.get("text"):
            issues.append(f"{prefix}: missing 'text'")
        if not raw.get("evidence"):
            issues.append(f"{prefix}: missing 'evidence'")
        if not raw.get("citations"):
            issues.append(f"{prefix}: must have at least one citation")
        if "confidence" not in raw:
            issues.append(f"{prefix}: missing 'confidence'")
        elif not (0.0 <= raw["confidence"] <= 1.0):
            issues.append(f"{prefix}: confidence must be 0.0-1.0")

        return issues

    def _condensed_text(self, finding: StructuredFinding) -> str:
        """Render the condensed summary text for token counting."""
        parts: list[str] = []
        for claim in finding.claims:
            parts.append(f"- {claim.text} (confidence: {claim.confidence})")
            parts.append(f"  Evidence: {claim.evidence}")
        for absence in finding.absence_report:
            parts.append(f"- [NOT FOUND] {absence}")
        return "\n".join(parts)

    def _render_artifact(self, finding: StructuredFinding) -> str:
        """Render the full markdown artifact."""
        lines = [
            f"# Research Finding: {finding.task_id}",
            f"Agent: {finding.agent_id} ({finding.agent_type})",
            f"Status: {finding.status.value}",
            "",
            "## Claims",
        ]
        for i, claim in enumerate(finding.claims, 1):
            lines.append(f"\n### Claim {i}")
            lines.append(claim.text)
            lines.append(f"\n**Evidence:** {claim.evidence}")
            lines.append(
                f"**Confidence:** {claim.confidence} ({claim.confidence_tier.value})"
            )
            if claim.caveats:
                lines.append(f"**Caveats:** {', '.join(claim.caveats)}")
            lines.append(f"**Citations:** {len(claim.citations)} sources")

        lines.extend(["", "## Absence Report"])
        for item in finding.absence_report:
            lines.append(f"- {item}")

        if finding.gaps:
            lines.extend(["", "## Gaps"])
            for gap in finding.gaps:
                lines.append(f"- {gap}")

        lines.extend(
            [
                "",
                "## Metadata",
                f"- Sources consulted: {finding.sources_consulted}",
                f"- Tokens consumed: {finding.tokens_consumed}",
            ]
        )
        return "\n".join(lines)
