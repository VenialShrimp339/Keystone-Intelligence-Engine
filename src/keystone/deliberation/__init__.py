"""Deliberation (L1.5) pipeline stage for the Keystone Intelligence Engine.

Two-phase deliberation between CitationProcessor and Content Structuring:
Phase 1: Independent parallel analysis (3-5 methodology-diverse analysts)
Phase 2: Claim-level SELECTION aggregation + confidence map building

Key design choices:
- Selection, not synthesis: judge picks best-supported claim (81% win rate)
- Methodological diversity replaces persona diversity (DMAD, ICLR 2025)
- WWHTB for low-confidence claims (<0.6)
- Five-tier confidence map grounded in DiscoUQ (AUROC 0.802)
"""

from keystone.deliberation.aggregator import AggregatedClaim, Aggregator
from keystone.deliberation.analyst import (
    Analyst,
    AnalystOutput,
    InputClaim,
    ScoredClaim,
    extract_claims,
)
from keystone.deliberation.confidence_builder import build_confidence_map
from keystone.deliberation.deliberation import Deliberation
from keystone.deliberation.gap_detector import GapReport, detect_gaps
from keystone.deliberation.wwhtb import WWHTBResult, run_wwhtb

__all__ = [
    "AggregatedClaim",
    "Aggregator",
    "Analyst",
    "AnalystOutput",
    "Deliberation",
    "GapReport",
    "InputClaim",
    "ScoredClaim",
    "WWHTBResult",
    "build_confidence_map",
    "detect_gaps",
    "extract_claims",
    "run_wwhtb",
]
