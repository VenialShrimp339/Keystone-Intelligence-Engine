"""CitationProcessor: orchestrates dedup, corroboration, URL checks, and manifest building.

Sits between L1 (Research Agents) and L1.5 (Deliberation). Receives
StructuredFindings from multiple agents and produces a deduplicated,
verified CitationManifest. All operations are deterministic (no LLM calls).
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from collections.abc import AsyncIterator

from keystone.citation.dedup import deduplicate_with_aliases, find_corroboration_pairs
from keystone.citation.hash import compute_content_hash
from keystone.citation.url_check import batch_check_urls
from keystone.events import (
    AnyPipelineEvent,
    CitationDeduped,
    CorroborationScored,
    ManifestProduced,
    URLVerified,
)
from keystone.models.citations import Citation, CitationAlias, CitationManifest
from keystone.models.research import FindingClaim, StructuredFinding
from pydantic import BaseModel


class CitationProcessorResult(BaseModel):
    """Output of CitationProcessor with both manifest and canonicalized findings.

    Callers that only need the manifest use get_manifest() (backward-compatible).
    Callers that need canonicalized findings (with citation IDs rewritten to
    canonical form) use get_result().
    """

    manifest: CitationManifest
    canonicalized_findings: list[StructuredFinding]


class CitationProcessor:
    """Orchestrates citation processing between L1 and L1.5.

    Satisfies CitationProcessorContract Protocol.
    No LLM dependency -- all operations are deterministic.

    Usage:
        processor = CitationProcessor()
        async for event in processor.process(findings, engagement_id, client_id):
            # Handle events
            pass
        manifest = await processor.get_manifest()
    """

    def __init__(self) -> None:
        self._manifest: CitationManifest | None = None
        self._canonicalized_findings: list[StructuredFinding] | None = None

    async def process(
        self,
        findings: list[StructuredFinding],
        engagement_id: str,
        client_id: str,
    ) -> AsyncIterator[AnyPipelineEvent]:
        """Process all agent findings into a citation manifest.

        Steps:
        1. Collect all citations from all findings
        2. Deduplicate by URL/DOI
        3. Find corroboration pairs
        4. Check URL liveness
        5. Ensure content hashes on all citations
        6. Build and store CitationManifest

        Yields CitationDeduped, CorroborationScored, URLVerified,
        ManifestProduced events.
        """
        # 1. Collect all citations from all findings
        all_citations: list[Citation] = []
        for finding in findings:
            for claim in finding.claims:
                all_citations.extend(claim.citations)

        if not all_citations:
            manifest_id = f"MAN-{_uid()[:8]}"
            self._manifest = CitationManifest(
                manifest_id=manifest_id,
                engagement_id=engagement_id,
                client_id=client_id,
            )
            self._canonicalized_findings = findings
            yield ManifestProduced(
                event_id=_uid(),
                engagement_id=engagement_id,
                client_id=client_id,
                manifest_id=manifest_id,
                total_citations=0,
                dead_urls=0,
                fabrication_flags=0,
                corroboration_pairs=0,
            )
            return

        # 2. Build provenance maps for alias construction
        task_id_by_citation: dict[str, str] = {}
        agent_id_by_citation: dict[str, str] = {}
        for finding in findings:
            for claim in finding.claims:
                for cit in claim.citations:
                    task_id_by_citation[cit.citation_id] = finding.task_id
                    agent_id_by_citation[cit.citation_id] = finding.agent_id

        # 3. Deduplicate with alias map
        deduped, aliases = deduplicate_with_aliases(
            all_citations,
            engagement_id=engagement_id,
            task_id_by_citation=task_id_by_citation,
            agent_id_by_citation=agent_id_by_citation,
        )

        # Emit CitationDeduped events for merged groups
        for citation in deduped:
            if citation.merged_from_ids:
                yield CitationDeduped(
                    event_id=_uid(),
                    engagement_id=engagement_id,
                    client_id=client_id,
                    citation_id=citation.citation_id,
                    merged_from=citation.merged_from_ids,
                    agents_involved=citation.found_by_agents,
                )

        # 3. Corroboration pairs
        pairs = find_corroboration_pairs(findings)
        for pair in pairs:
            yield CorroborationScored(
                event_id=_uid(),
                engagement_id=engagement_id,
                client_id=client_id,
                citation_a=pair.citation_a,
                citation_b=pair.citation_b,
                overlap_score=pair.overlap_score,
            )

        # 4. URL liveness checks
        url_results = await batch_check_urls(deduped)
        dead_url_ids: list[str] = []

        updated_citations: list[Citation] = []
        for citation in deduped:
            is_live = url_results.get(citation.citation_id, False)
            yield URLVerified(
                event_id=_uid(),
                engagement_id=engagement_id,
                client_id=client_id,
                citation_id=citation.citation_id,
                url=citation.url,
                is_live=is_live,
            )
            if not is_live:
                dead_url_ids.append(citation.citation_id)
            updated_citations.append(
                citation.model_copy(update={"url_live": is_live})
            )

        # 5. Ensure content hashes on all citations
        final_citations: list[Citation] = []
        for citation in updated_citations:
            if citation.content_hash is None:
                hash_input = f"{citation.url}:{citation.title}"
                citation = citation.model_copy(
                    update={"content_hash": compute_content_hash(hash_input)}
                )
            final_citations.append(citation)

        # 6. Build manifest with alias map
        manifest_id = f"MAN-{_uid()[:8]}"
        self._manifest = CitationManifest(
            manifest_id=manifest_id,
            engagement_id=engagement_id,
            client_id=client_id,
            citations=final_citations,
            corroboration_pairs=pairs,
            dead_urls=dead_url_ids,
            aliases=aliases,
        )

        # Rewrite findings so claim.citation_ids reference canonical IDs
        self._canonicalized_findings = self._rewrite_findings_to_canonical(
            findings, aliases
        )

        yield ManifestProduced(
            event_id=_uid(),
            engagement_id=engagement_id,
            client_id=client_id,
            manifest_id=manifest_id,
            total_citations=len(final_citations),
            dead_urls=len(dead_url_ids),
            fabrication_flags=0,
            corroboration_pairs=len(pairs),
        )

    async def get_manifest(self) -> CitationManifest:
        """Return the produced citation manifest."""
        if self._manifest is None:
            msg = "process() must be called before get_manifest()"
            raise RuntimeError(msg)
        return self._manifest

    async def get_result(self) -> CitationProcessorResult:
        """Return both the manifest and canonicalized findings."""
        if self._manifest is None or self._canonicalized_findings is None:
            msg = "process() must be called before get_result()"
            raise RuntimeError(msg)
        return CitationProcessorResult(
            manifest=self._manifest,
            canonicalized_findings=self._canonicalized_findings,
        )

    def _rewrite_findings_to_canonical(
        self,
        findings: list[StructuredFinding],
        aliases: list[CitationAlias],
    ) -> list[StructuredFinding]:
        """Rewrite claim.citation_ids from source-instance IDs to canonical IDs.

        Builds a lookup from source_instance_id -> canonical_citation_id,
        then produces new StructuredFinding/FindingClaim objects with updated
        citation_ids. Original citations list on each claim is preserved as-is
        (it contains the canonical Citation objects after dedup).
        """
        alias_map: dict[str, str] = {
            a.source_instance_id: a.canonical_citation_id for a in aliases
        }

        rewritten: list[StructuredFinding] = []
        for finding in findings:
            new_claims: list[FindingClaim] = []
            for claim in finding.claims:
                canonical_ids = [
                    alias_map.get(cid, cid) for cid in claim.citation_ids
                ]
                # Deduplicate while preserving order
                seen: set[str] = set()
                deduped_ids: list[str] = []
                for cid in canonical_ids:
                    if cid not in seen:
                        seen.add(cid)
                        deduped_ids.append(cid)
                new_claims.append(claim.model_copy(update={"citation_ids": deduped_ids}))
            rewritten.append(finding.model_copy(update={"claims": new_claims}))
        return rewritten


def _uid() -> str:
    return str(uuid.uuid4())
