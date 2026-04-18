"""Classify an incoming query as QUANTITATIVE / QUALITATIVE / HYBRID.

Quantitative queries ("What was Apple's 2023 revenue?") are better
served by direct structured-data lookups (XBRL via EDGAR, FRED time
series) than by retrieving prose passages. Qualitative queries ("How is
the company's moat described in their last three 10-Ks?") want the
hybrid prose-retrieval path. Many queries are actually both ("Compare
Microsoft and Google's cloud margins AND describe their strategic
framing") -- we route those to HYBRID so the service runs both pipelines
and merges the results upstream.

The default router is rule-based and cheap (<1 ms). A future LLM-backed
router can replace this without touching callers by implementing the
same :class:`QueryRouter` protocol.
"""

from __future__ import annotations

import re
from typing import Protocol, runtime_checkable

from keystone.retrieval.search.models import QueryClassification, QueryRoute

# --- Signals -----------------------------------------------------------

# Pure numeric / financial patterns that strongly indicate a structured
# answer is available. Each pattern name becomes a signal in the route.
_QUANT_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("currency", re.compile(r"\$\s?\d[\d,]*(\.\d+)?([kKmMbB])?|\d[\d,]*\s?(USD|EUR|GBP|JPY)")),
    ("percent", re.compile(r"\d+(\.\d+)?\s?%")),
    ("ratio", re.compile(r"\b\d+\s?(?:to|:)\s?\d+\b")),
    ("fiscal_year", re.compile(r"\b(?:FY|Q[1-4])[-\s]?\d{2,4}\b", re.IGNORECASE)),
    (
        "metric_term",
        re.compile(
            r"\b(revenue|ebitda|ebit|eps|margin|roe|roa|roic|yoy|cagr|"
            r"p\/e|pe ratio|earnings|net income|gross profit|free cash flow|capex)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "stock_ticker",
        re.compile(r"\b(?:NYSE|NASDAQ):\s?[A-Z]{1,5}\b|\$[A-Z]{1,5}\b"),
    ),
]

_QUAL_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "explanatory",
        re.compile(
            r"\b(why|how|describe|explain|analy[sz]e|compare|discuss|assess|"
            r"summariz[e]|overview|background|context|rationale|strategy)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "qualitative_term",
        re.compile(
            r"\b(moat|competitive advantage|culture|governance|risk factors|"
            r"management|leadership|vision|outlook|sentiment|qualitative)\b",
            re.IGNORECASE,
        ),
    ),
]


@runtime_checkable
class QueryRouter(Protocol):
    """Swappable classifier surface."""

    async def classify(self, query: str) -> QueryRoute: ...


class RuleBasedQueryRouter:
    """Deterministic keyword + regex router.

    Decision logic:
    - At least one quantitative signal **and** one qualitative signal
      -> ``HYBRID``.
    - Only quantitative signals -> ``QUANTITATIVE``.
    - Only qualitative signals (or neither) -> ``QUALITATIVE``.

    Confidence is derived from the number of matching signals: a single
    match lands at 0.6, two or more at 0.9. Zero matches default to
    ``QUALITATIVE`` at 0.5 -- neutral enough that upstream code knows it
    was a best-effort classification.
    """

    async def classify(self, query: str) -> QueryRoute:
        if not query.strip():
            raise ValueError("classify called with empty query")
        quant_hits = _match_patterns(query, _QUANT_PATTERNS)
        qual_hits = _match_patterns(query, _QUAL_PATTERNS)

        quant_total = len(quant_hits)
        qual_total = len(qual_hits)

        if quant_total >= 1 and qual_total >= 1:
            confidence = _confidence_for(max(quant_total, qual_total))
            return QueryRoute(
                classification=QueryClassification.HYBRID,
                confidence=confidence,
                reason="matched both quantitative and qualitative signals",
                signals=sorted({*quant_hits, *qual_hits}),
            )
        if quant_total >= 1:
            return QueryRoute(
                classification=QueryClassification.QUANTITATIVE,
                confidence=_confidence_for(quant_total),
                reason="matched quantitative signals only",
                signals=sorted(quant_hits),
            )
        if qual_total >= 1:
            return QueryRoute(
                classification=QueryClassification.QUALITATIVE,
                confidence=_confidence_for(qual_total),
                reason="matched qualitative signals only",
                signals=sorted(qual_hits),
            )
        return QueryRoute(
            classification=QueryClassification.QUALITATIVE,
            confidence=0.5,
            reason="no explicit signals; default to qualitative search",
            signals=[],
        )


def _match_patterns(query: str, patterns: list[tuple[str, re.Pattern[str]]]) -> set[str]:
    hits: set[str] = set()
    for name, pattern in patterns:
        if pattern.search(query):
            hits.add(name)
    return hits


def _confidence_for(n: int) -> float:
    if n >= 2:
        return 0.9
    if n == 1:
        return 0.6
    return 0.5
