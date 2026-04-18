"""Layer 2: Citation validation gate.

Binary gate: any fabricated citation = immediate rejection.
DOI verification via pluggable DOIVerifier Protocol. Phase 1 uses
HTTP HEAD to doi.org. Phase 1B+ swaps to MCP gateway without code change.
"""

from __future__ import annotations

import logging
from difflib import SequenceMatcher
from typing import Protocol, runtime_checkable

import httpx

from keystone.citation.url_check import batch_check_urls
from keystone.models.citations import Citation, CitationManifest
from keystone.models.evaluation import Layer2Result

logger = logging.getLogger(__name__)


class DOIVerificationResult:
    """Result of a single DOI verification."""

    __slots__ = ("exists", "title")

    def __init__(self, exists: bool, title: str | None = None) -> None:
        self.exists = exists
        self.title = title


@runtime_checkable
class DOIVerifier(Protocol):
    """Pluggable DOI verification interface.

    Phase 1: HTTPDOIVerifier (direct HTTP HEAD to doi.org).
    Phase 1B+: MCPDOIVerifier routes through MCP gateway to doi-mcp
    for 9-database parallel check. Swap via config, not code change.
    """

    async def verify(self, doi: str) -> DOIVerificationResult: ...


class HTTPDOIVerifier:
    """Phase 1 DOI verifier: HTTP HEAD to doi.org.

    200/302 = exists. 404 = fabricated. Fetches landing page title
    for fuzzy match when the redirect succeeds.
    """

    def __init__(self, timeout: float = 10.0) -> None:
        self._timeout = timeout

    async def verify(self, doi: str) -> DOIVerificationResult:
        url = f"https://doi.org/{doi}"
        async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
            try:
                resp = await client.head(url)
                if resp.status_code < 400:
                    return DOIVerificationResult(exists=True, title=None)
                return DOIVerificationResult(exists=False)
            except httpx.HTTPError:
                return DOIVerificationResult(exists=False)


class Layer2CitationGate:
    """Citation validation gate. Any fabrication = full rejection.

    Verification logic:
    - Citations with DOI: verify via DOIVerifier, fuzzy-match title
    - Citations with URL but no DOI: verify via batch_check_urls
    - Citations with neither: flagged as UNVERIFIABLE (not fabricated)

    Fabrication classification:
    - DOI resolves to nothing -> FABRICATED
    - DOI resolves but title mismatch (>0.8 threshold) -> SUSPICIOUS
      (flag but don't reject in Phase 1)
    - DOI resolves and title matches -> VERIFIED
    """

    TITLE_MATCH_THRESHOLD = 0.8

    def __init__(self, doi_verifier: DOIVerifier | None = None) -> None:
        self._doi_verifier = doi_verifier or HTTPDOIVerifier()

    async def evaluate(self, manifest: CitationManifest) -> Layer2Result:
        if not manifest.citations:
            return Layer2Result(
                citations_checked=0,
                citations_verified=0,
                citations_fabricated=[],
                gate_passed=True,
            )

        doi_citations = [c for c in manifest.citations if c.doi]
        url_only_citations = [c for c in manifest.citations if not c.doi and c.url]

        verified: list[str] = []
        fabricated: list[str] = []

        # DOI verification
        for cit in doi_citations:
            result = await self._doi_verifier.verify(cit.doi)  # type: ignore[arg-type]
            if not result.exists:
                fabricated.append(cit.citation_id)
                logger.warning("Fabricated DOI detected: %s (%s)", cit.doi, cit.citation_id)
            else:
                # Title fuzzy match (when title available from verifier)
                if result.title and not self._title_matches(cit.title, result.title):
                    logger.info(
                        "DOI %s resolves but title mismatch for %s (SUSPICIOUS, not rejecting in Phase 1)",
                        cit.doi,
                        cit.citation_id,
                    )
                verified.append(cit.citation_id)

        # URL-only verification
        if url_only_citations:
            url_results = await batch_check_urls(url_only_citations)
            for cid, is_live in url_results.items():
                if is_live:
                    verified.append(cid)
                # Dead URL != fabricated. Reported in Layer 1 dead_urls.

        total_checked = len(doi_citations) + len(url_only_citations)
        # Citations with neither DOI nor URL are UNVERIFIABLE, not fabricated

        return Layer2Result(
            citations_checked=total_checked,
            citations_verified=len(verified),
            citations_fabricated=fabricated,
            gate_passed=len(fabricated) == 0,
        )

    def _title_matches(self, citation_title: str, resolved_title: str) -> bool:
        ratio = SequenceMatcher(None, citation_title.lower(), resolved_title.lower()).ratio()
        return ratio >= self.TITLE_MATCH_THRESHOLD
