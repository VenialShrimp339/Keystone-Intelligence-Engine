"""CitationProcessor: orchestrates dedup, corroboration, URL checks, and manifest building.

Sits between L1 (Research Agents) and L1.5 (Deliberation). Receives
StructuredFindings from multiple agents and produces a deduplicated,
verified CitationManifest. All operations are deterministic (no LLM calls).
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from collections.abc import AsyncIterator

from keystone.citation.dedup import deduplicate_citations, find_corroboration_pairs
from keystone.citation.hash import compute_content_hash
from keystone.citation.url_check import batch_check_urls
from keystone.events import (
    AnyPipelineEvent,
    CitationDeduped,
    CorroborationScored,
    ManifestProduced,
    URLVerified,
)
from keystone.models.citations import Citation, CitationManifest
from keystone.models.research import StructuredFinding


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

        # 2. Deduplicate citations by URL/DOI
        # Track originals for merge event emission
        originals_by_url: dict[str, list[str]] = defaultdict(list)
        originals_by_doi: dict[str, list[str]] = defaultdict(list)
        for c in all_citations:
            originals_by_url[c.url].append(c.citation_id)
            if c.doi:
                originals_by_doi[c.doi].append(c.citation_id)

        deduped = deduplicate_citations(all_citations)

        for citation in deduped:
            merged_ids = set(originals_by_url.get(citation.url, []))
            if citation.doi:
                merged_ids |= set(originals_by_doi.get(citation.doi, set()))
            if len(merged_ids) > 1:
                yield CitationDeduped(
                    event_id=_uid(),
                    engagement_id=engagement_id,
                    client_id=client_id,
                    citation_id=citation.citation_id,
                    merged_from=sorted(merged_ids),
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

        # 6. Build manifest
        manifest_id = f"MAN-{_uid()[:8]}"
        self._manifest = CitationManifest(
            manifest_id=manifest_id,
            engagement_id=engagement_id,
            client_id=client_id,
            citations=final_citations,
            corroboration_pairs=pairs,
            dead_urls=dead_url_ids,
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


def _uid() -> str:
    return str(uuid.uuid4())
