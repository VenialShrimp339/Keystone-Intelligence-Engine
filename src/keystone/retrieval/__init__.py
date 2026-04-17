"""Lane E: deterministic article/PDF parsing and evidence normalization.

Sits between Lane H (governed document fetch) and the research pipeline.
Turns fetched artifacts into structured passages and normalized evidence-prep
records that preserve full provenance (artifact_id, canonical URL, content
hash, coverage, parser identity, locator, parse confidence).

All parsing is deterministic -- no LLM calls. Parse quality is expressed
via ParseConfidence and ParseWarning, never by silently inventing text.
"""

from __future__ import annotations

from keystone.retrieval.article_parser import ArticleParser
from keystone.retrieval.artifact_loader import (
    ArtifactLoader,
    ArtifactLoadError,
    ArtifactNotFoundError,
)
from keystone.retrieval.evidence_normalizer import EvidenceNormalizer
from keystone.retrieval.parse_models import (
    Coverage,
    CoverageStatus,
    EvidencePrepRecord,
    FetchedArtifact,
    Locator,
    ParseConfidence,
    ParseConfidenceTier,
    ParsedDocument,
    ParsedPassage,
    ParserIdentity,
    ParseWarning,
    PassageKind,
    SourceFamily,
)
from keystone.retrieval.pdf_parser import (
    BasicPDFTextBackend,
    PDFExtractionResult,
    PDFPageText,
    PDFParser,
    PDFTextBackend,
)

__all__ = [
    "ArtifactLoadError",
    "ArtifactLoader",
    "ArtifactNotFoundError",
    "ArticleParser",
    "BasicPDFTextBackend",
    "Coverage",
    "CoverageStatus",
    "EvidenceNormalizer",
    "EvidencePrepRecord",
    "FetchedArtifact",
    "Locator",
    "PDFExtractionResult",
    "PDFPageText",
    "PDFParser",
    "PDFTextBackend",
    "ParseConfidence",
    "ParseConfidenceTier",
    "ParseWarning",
    "ParsedDocument",
    "ParsedPassage",
    "ParserIdentity",
    "PassageKind",
    "SourceFamily",
]
