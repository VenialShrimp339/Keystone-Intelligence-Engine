"""Content hashing utilities for provenance tracking.

SHA-256 based hashing for the Karpathy compiled wiki pattern.
Every proposition in compiled/ traces back to a content-hash
in raw/, enabling full provenance from claim -> proposition -> source.
"""

from __future__ import annotations

import hashlib


def compute_content_hash(content: str) -> str:
    """SHA-256 hash of source content for provenance tracking.

    Args:
        content: The source content text to hash.

    Returns:
        64-character lowercase hex string (SHA-256 digest).
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def compute_proposition_hash(proposition: str, source_content_hash: str) -> str:
    """Hash linking a specific proposition to its source content.

    Combines the proposition text with the source content hash
    to create a unique identifier for this proposition-source pair.

    Args:
        proposition: The proposition text.
        source_content_hash: SHA-256 hash of the source content.

    Returns:
        64-character lowercase hex string.
    """
    combined = f"{proposition}:{source_content_hash}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def verify_content_hash(content: str, expected_hash: str) -> bool:
    """Verify content hasn't changed since hash was computed.

    Args:
        content: The current content text.
        expected_hash: The previously computed SHA-256 hash.

    Returns:
        True if the content matches the expected hash.
    """
    return compute_content_hash(content) == expected_hash
