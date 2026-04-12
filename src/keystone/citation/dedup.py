"""Citation deduplication and corroboration detection.

Merges citations referring to the same source (same URL or DOI)
and identifies claims independently discovered by multiple agents.
"""

from __future__ import annotations

import hashlib
import uuid
from collections import defaultdict
from itertools import combinations

from keystone.models.citations import Citation, CitationAlias, CorroborationPair
from keystone.models.research import StructuredFinding


def _group_duplicates(citations: list[Citation]) -> list[list[Citation]]:
    """Group citations that share a URL or a non-None DOI.

    Uses union-find so that transitive matches are captured:
    if A shares a URL with B and B shares a DOI with C, all three merge.
    """
    n = len(citations)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj

    # Index by URL and DOI
    url_map: dict[str, int] = {}
    doi_map: dict[str, int] = {}

    for i, c in enumerate(citations):
        if c.url in url_map:
            union(i, url_map[c.url])
        else:
            url_map[c.url] = i

        if c.doi is not None:
            if c.doi in doi_map:
                union(i, doi_map[c.doi])
            else:
                doi_map[c.doi] = i

    groups: dict[int, list[Citation]] = defaultdict(list)
    for i, c in enumerate(citations):
        groups[find(i)].append(c)

    return list(groups.values())


def _group_hash(citations: list[Citation]) -> str:
    """Compute a stable 8-char hash identifying this group of citations."""
    key = "|".join(sorted(c.url for c in citations))
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:8]


def _merge_group(
    citations: list[Citation],
    engagement_id: str = "",
) -> Citation:
    """Merge a group of citations referring to the same source.

    Rules:
    - Mint a fresh canonical citation_id (CAN-{engagement_id}-{group_hash})
      so the canonical ID is never the same as any source-instance ID.
    - Combine found_by_agents lists (deduplicated)
    - Keep highest quality_score
    - Use the most complete record as the base (most non-None optional fields)
    - Preserve any real content_hash already attached to one of the citations
    - Migrate url:title hashes to metadata_hash (not content_hash)
    """
    # Score completeness: count non-None optional fields
    def completeness(c: Citation) -> int:
        score = 0
        if c.doi is not None:
            score += 1
        if c.content_hash is not None:
            score += 1
        if c.metadata_hash is not None:
            score += 1
        if c.url_live is not None:
            score += 1
        if c.crossref_verified is not None:
            score += 1
        if c.date_published is not None:
            score += 1
        if c.authors:
            score += 1
        if c.publication:
            score += 1
        return score

    # Sort: highest quality first, then most complete
    ranked = sorted(citations, key=lambda c: (c.quality_score, completeness(c)), reverse=True)
    best = ranked[0]

    # Mint a fresh canonical ID — distinct from all source-instance IDs
    eid = engagement_id or best.engagement_id
    canonical_id = f"CAN-{eid}-{_group_hash(citations)}"

    # Combine all agents
    all_agents: list[str] = []
    seen_agents: set[str] = set()
    for c in citations:
        for agent in c.found_by_agents:
            if agent not in seen_agents:
                all_agents.append(agent)
                seen_agents.add(agent)

    # Take highest quality score
    max_quality = max(c.quality_score for c in citations)

    # Merge optional fields from other records if best is missing them
    doi = best.doi
    content_hash = best.content_hash
    metadata_hash = best.metadata_hash
    url_live = best.url_live
    crossref_verified = best.crossref_verified
    date_published = best.date_published
    authors = best.authors
    publication = best.publication

    for c in ranked[1:]:
        if doi is None and c.doi is not None:
            doi = c.doi
        if content_hash is None and c.content_hash is not None:
            content_hash = c.content_hash
        if metadata_hash is None and c.metadata_hash is not None:
            metadata_hash = c.metadata_hash
        if url_live is None and c.url_live is not None:
            url_live = c.url_live
        if crossref_verified is None and c.crossref_verified is not None:
            crossref_verified = c.crossref_verified
        if date_published is None and c.date_published is not None:
            date_published = c.date_published
        if not authors and c.authors:
            authors = c.authors
        if not publication and c.publication:
            publication = c.publication

    # All source-instance IDs (including the winner) become aliases
    merged_from_ids = sorted({c.citation_id for c in citations})

    return Citation(
        citation_id=canonical_id,
        engagement_id=best.engagement_id,
        client_id=best.client_id,
        url=best.url,
        doi=doi,
        title=best.title,
        authors=authors,
        publication=publication,
        date_published=date_published,
        access_date=best.access_date,
        source_type=best.source_type,
        quality_score=max_quality,
        url_live=url_live,
        crossref_verified=crossref_verified,
        found_by_agents=all_agents,
        content_hash=content_hash,
        metadata_hash=metadata_hash,
        merged_from_ids=merged_from_ids,
    )


def deduplicate_citations(
    citations: list[Citation],
    engagement_id: str = "",
) -> list[Citation]:
    """Merge citations referring to the same source (same URL or DOI).

    When merging:
    - Mint a fresh canonical citation_id
    - Combine found_by_agents lists
    - Keep highest quality_score
    - Preserve all metadata from the most complete record

    Args:
        citations: Raw citation list from all agents.
        engagement_id: Used to mint stable canonical IDs.

    Returns:
        Deduplicated citation list.
    """
    if not citations:
        return []

    return [_merge_group(group, engagement_id) for group in _group_duplicates(citations)]


def deduplicate_with_aliases(
    citations: list[Citation],
    engagement_id: str,
    task_id_by_citation: dict[str, str],
    agent_id_by_citation: dict[str, str],
) -> tuple[list[Citation], list[CitationAlias]]:
    """Deduplicate citations and build the source-instance -> canonical alias map.

    Returns a tuple of (deduped_citations, aliases). Each alias maps one
    source-instance citation ID to the canonical citation ID that survived dedup.

    Args:
        citations: Raw citation list from all agents.
        engagement_id: Parent engagement.
        task_id_by_citation: Maps citation_id -> task_id for provenance.
        agent_id_by_citation: Maps citation_id -> agent_id for provenance.

    Returns:
        (deduped, aliases) where aliases covers every source-instance ID
        including those that were chosen as canonical (self-aliases).
    """
    if not citations:
        return [], []

    groups = _group_duplicates(citations)
    deduped: list[Citation] = []
    aliases: list[CitationAlias] = []

    for group in groups:
        canonical = _merge_group(group, engagement_id)
        deduped.append(canonical)
        # Every source-instance ID (including the winner) aliases to the fresh
        # canonical ID. The canonical ID is never a source-instance ID.
        for source_cit in group:
            aliases.append(
                CitationAlias(
                    source_instance_id=source_cit.citation_id,
                    canonical_citation_id=canonical.citation_id,
                    engagement_id=engagement_id,
                    task_id=task_id_by_citation.get(source_cit.citation_id, ""),
                    agent_id=agent_id_by_citation.get(source_cit.citation_id, ""),
                )
            )

    return deduped, aliases


def find_corroboration_pairs(
    findings: list[StructuredFinding],
) -> list[CorroborationPair]:
    """Identify claims independently discovered by 2+ agents.

    Two claims corroborate if they reference the same citation
    (after deduplication) AND come from different agents.
    Corroboration is detected at the citation-URL level: if two
    agents independently cite the same source, that's corroboration.

    Args:
        findings: Structured findings from L1 research agents.

    Returns:
        List of corroboration pairs with overlap scores.
    """
    if not findings:
        return []

    # Build map: source URL -> list of (agent_id, citation_id) tuples
    url_agents: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for finding in findings:
        for claim in finding.claims:
            for cit in claim.citations:
                url_agents[cit.url].append((finding.agent_id, cit.citation_id))

    pairs: list[CorroborationPair] = []
    seen: set[tuple[str, str]] = set()

    for url, agent_cits in url_agents.items():
        # Group by agent to find cross-agent corroboration
        by_agent: dict[str, list[str]] = defaultdict(list)
        for agent_id, cit_id in agent_cits:
            by_agent[agent_id].append(cit_id)

        agents = list(by_agent.keys())
        if len(agents) < 2:
            continue

        # Create pairs for each combination of agents sharing this source
        for agent_a, agent_b in combinations(agents, 2):
            for cit_a in by_agent[agent_a]:
                for cit_b in by_agent[agent_b]:
                    pair_key = (min(cit_a, cit_b), max(cit_a, cit_b))
                    if pair_key not in seen:
                        seen.add(pair_key)
                        pairs.append(
                            CorroborationPair(
                                citation_a=cit_a,
                                citation_b=cit_b,
                                overlap_score=1.0,
                            )
                        )

    return pairs
