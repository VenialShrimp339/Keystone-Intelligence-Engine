"""URL liveness verification for citations.

Checks whether citation URLs are reachable. Uses HEAD with
fallback to GET. Supports concurrent batch checking with
configurable concurrency limits.
"""

from __future__ import annotations

import asyncio

import httpx

from keystone.models.citations import Citation

# Many sites (Wikipedia, SEC, Reuters) block requests without a polite
# User-Agent.  Including a project URL satisfies the Wikimedia policy
# and similar automated-access policies.
USER_AGENT = (
    "Keystone-Intelligence-Engine/1.0 "
    "(https://github.com/keystone-intelligence; citation-verification)"
)


async def check_url_liveness(url: str, timeout: float = 10.0) -> bool:
    """Check if a URL is reachable. HEAD request with fallback to GET.

    A URL is considered live if it returns any 2xx or 3xx status code.
    If HEAD fails (4xx/5xx or connection error), falls back to GET.

    Args:
        url: The URL to check.
        timeout: Request timeout in seconds.

    Returns:
        True if the URL is reachable, False otherwise.
    """
    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=False,
        headers={"User-Agent": USER_AGENT},
    ) as client:
        # Try HEAD first (lightweight)
        try:
            resp = await client.head(url)
            if resp.status_code < 400:
                return True
        except httpx.HTTPError:
            return False

        # HEAD returned 4xx/5xx -- fallback to GET
        try:
            resp = await client.get(url)
            return resp.status_code < 400
        except httpx.HTTPError:
            return False


async def batch_check_urls(citations: list[Citation], concurrency: int = 10) -> dict[str, bool]:
    """Check URL liveness for all citations concurrently.

    Args:
        citations: Citations to check.
        concurrency: Maximum concurrent requests.

    Returns:
        Dict mapping citation_id -> is_live.
    """
    if not citations:
        return {}

    semaphore = asyncio.Semaphore(concurrency)

    async def _check(cit: Citation) -> tuple[str, bool]:
        async with semaphore:
            is_live = await check_url_liveness(cit.url)
            return cit.citation_id, is_live

    results = await asyncio.gather(*[_check(c) for c in citations])
    return dict(results)
