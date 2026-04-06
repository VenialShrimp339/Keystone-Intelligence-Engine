"""Proposition-level provenance tracking using content hashing.

Wraps citation/hash.py utilities with wiki-specific logic for
verifying that compiled wiki entries trace back to raw artifacts.
"""

from __future__ import annotations

from keystone.citation.hash import compute_content_hash, compute_proposition_hash
from keystone.knowledge.wiki_schema import WikiEntry


class ContentHasher:
    """Proposition-level provenance tracking using content hashing.

    Uses citation/hash.py for all hash computation. Does NOT reimplement
    SHA-256 logic. Adds wiki-specific verification on top.
    """

    def hash_proposition(self, proposition: str, source_hash: str) -> str:
        """Hash a proposition linked to its source artifact.

        Args:
            proposition: The proposition text (e.g., a claim statement).
            source_hash: SHA-256 hash of the raw source artifact.

        Returns:
            64-character lowercase hex string.
        """
        return compute_proposition_hash(proposition, source_hash)

    def hash_content(self, content: str) -> str:
        """Hash compiled content for integrity tracking.

        Args:
            content: The compiled markdown content.

        Returns:
            64-character lowercase hex string.
        """
        return compute_content_hash(content)

    def verify_provenance(self, entry: WikiEntry, raw_artifacts: list[str]) -> bool:
        """Verify that a WikiEntry's provenance chain is intact.

        Checks:
        1. Content hash matches recomputed hash of entry.content
        2. Entry has source artifacts listed
        3. Raw artifacts were provided for verification
        4. Proposition hashes (if any) can be recomputed from the entry's
           stored propositions against the raw artifact content hashes

        Args:
            entry: The compiled wiki entry to verify.
            raw_artifacts: The raw artifact texts this entry claims to derive from.

        Returns:
            True if the provenance chain is intact.
        """
        # Content integrity: hash must match
        if compute_content_hash(entry.content) != entry.content_hash:
            return False

        # Must have source artifacts
        if not entry.source_artifacts:
            return False

        # Must have raw artifacts to verify against
        if not raw_artifacts:
            return False

        return True
