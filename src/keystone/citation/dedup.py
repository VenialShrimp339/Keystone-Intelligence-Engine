"""Citation deduplication and corroboration detection.

Merges citations referring to the same source (same URL or DOI)
and identifies claims independently discovered by multiple agents.
"""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations

from keystone.models.citations import Citation, CorroborationPair
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


def _merge_group(citations: list[Citation]) -> Citation:
    """Merge a group of citations referring to the same source.

    Rules:
    - Combine found_by_agents lists (deduplicated)
    - Keep highest quality_score
    - Use the most complete record as the base (most non-None optional fields)
    """
    # Score completeness: count non-None optional fields
    def completeness(c: Citation) -> int:
        score = 0
        if c.doi is not None:
            score += 1
        if c.content_hash is not None:
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

    return Citation(
        citation_id=best.citation_id,
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
    )


def deduplicate_citations(citations: list[Citation]) -> list[Citation]:
    """Merge citations referring to the same source (same URL or DOI).

    When merging:
    - Combine found_by_agents lists
    - Keep highest quality_score
    - Preserve all metadata from the most complete record

    Args:
        citations: Raw citation list from all agents.

    Returns:
        Deduplicated citation list.
    """
    if not citations:
        return []

    return [_merge_group(group) for group in _group_duplicates(citations)]


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
