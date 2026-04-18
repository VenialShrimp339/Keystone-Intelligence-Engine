"""Simple MCP client that makes real HTTP calls to search APIs.

Implements the MCPClient Protocol from mcp_gateway.py. Direct REST
calls to Exa and Brave Search APIs (not full MCP protocol). Other
tools fall back to empty results with a warning.

Created for Wave 4a pressure testing (Session 10).
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Tool-to-API mapping
_EXA_TOOLS = {"exa_search"}
_BRAVE_TOOLS = {"brave_search"}


class SimpleMCPClient:
    """Makes real HTTP calls to Exa and Brave Search APIs.

    Implements the MCPClient Protocol::

        async def call_tool(
            self, server: str, tool: str, params: dict[str, Any]
        ) -> Any

    For tools without a real API backend (edgar, fred, etc.),
    returns a stub result with a warning log.
    """

    def __init__(
        self,
        *,
        exa_api_key: str | None = None,
        brave_api_key: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._exa_key = exa_api_key or os.environ.get("EXA_API_KEY", "")
        self._brave_key = brave_api_key or os.environ.get("BRAVE_SEARCH_API_KEY", "")
        self._timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
        self.call_count: int = 0
        self.exa_calls: int = 0
        self.brave_calls: int = 0

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def call_tool(self, server: str, tool: str, params: dict[str, Any]) -> Any:
        """Execute a tool call via the appropriate API."""
        self.call_count += 1

        if tool in _EXA_TOOLS:
            return await self._call_exa(params)
        if tool in _BRAVE_TOOLS:
            return await self._call_brave(params)

        # Stub for tools without real API backends
        logger.warning(
            "No real API backend for tool '%s' (server '%s'). Returning stub.",
            tool,
            server,
        )
        return {
            "status": "stub",
            "tool": tool,
            "server": server,
            "data": f"Stub result for {tool} -- no real API configured",
            "results": [],
        }

    async def _call_exa(self, params: dict[str, Any]) -> Any:
        """Call the Exa search API (POST api.exa.ai/search)."""
        if not self._exa_key:
            raise ValueError("EXA_API_KEY not set")

        query = params.get("query", "")
        self.exa_calls += 1

        response = await self._client.post(
            "https://api.exa.ai/search",
            headers={
                "x-api-key": self._exa_key,
                "Content-Type": "application/json",
            },
            json={
                "query": query,
                "numResults": 5,
                "type": "neural",
                "useAutoprompt": True,
                "contents": {
                    "text": {"maxCharacters": 1000},
                },
            },
        )
        response.raise_for_status()
        data = response.json()

        # Normalize to a standard format with URLs and titles
        results = []
        for item in data.get("results", []):
            results.append(
                {
                    "url": item.get("url", ""),
                    "title": item.get("title", ""),
                    "text": item.get("text", ""),
                    "score": item.get("score", 0.0),
                    "published_date": item.get("publishedDate", ""),
                }
            )

        return {
            "status": "ok",
            "tool": "exa_search",
            "query": query,
            "results": results,
            "result_count": len(results),
        }

    async def _call_brave(self, params: dict[str, Any]) -> Any:
        """Call the Brave Search API (GET api.search.brave.com/res/v1/web/search)."""
        if not self._brave_key:
            raise ValueError("BRAVE_SEARCH_API_KEY not set")

        query = params.get("query", "")
        self.brave_calls += 1

        response = await self._client.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={
                "X-Subscription-Token": self._brave_key,
                "Accept": "application/json",
            },
            params={
                "q": query,
                "count": 5,
            },
        )
        response.raise_for_status()
        data = response.json()

        # Normalize to standard format
        results = []
        for item in data.get("web", {}).get("results", []):
            results.append(
                {
                    "url": item.get("url", ""),
                    "title": item.get("title", ""),
                    "text": item.get("description", ""),
                }
            )

        return {
            "status": "ok",
            "tool": "brave_search",
            "query": query,
            "results": results,
            "result_count": len(results),
        }
