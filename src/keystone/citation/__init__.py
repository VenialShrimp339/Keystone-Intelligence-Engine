"""Citation processing pipeline for the Keystone Intelligence Engine.

Implements the CitationProcessor stage between L1 (Research Agents)
and L1.5 (Deliberation). Handles:
- Content hashing for provenance tracking (Karpathy pattern)
- Citation deduplication across agents
- Corroboration detection
- URL liveness verification
"""

from keystone.citation.dedup import deduplicate_citations, find_corroboration_pairs
from keystone.citation.hash import (
    compute_content_hash,
    compute_proposition_hash,
    verify_content_hash,
)
from keystone.citation.processor import CitationProcessor
from keystone.citation.url_check import batch_check_urls, check_url_liveness

__all__ = [
    "CitationProcessor",
    "batch_check_urls",
    "check_url_liveness",
    "compute_content_hash",
    "compute_proposition_hash",
    "deduplicate_citations",
    "find_corroboration_pairs",
    "verify_content_hash",
]
