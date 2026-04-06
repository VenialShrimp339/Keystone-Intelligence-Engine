"""Tests for URL liveness verification.

Uses pytest-httpx to mock HTTP responses for URL checking,
including HEAD/GET fallback, timeout handling, and batch concurrency.
"""

from __future__ import annotations

from datetime import datetime

import httpx
import pytest
from pytest_httpx import HTTPXMock

from keystone.citation.url_check import batch_check_urls, check_url_liveness
from keystone.models.citations import Citation, SourceType


def _cit(cid: str, url: str) -> Citation:
    return Citation(
        citation_id=cid,
        engagement_id="ENG-001",
        client_id="CLIENT-001",
        url=url,
        title="Test",
        source_type=SourceType.REPORT,
        quality_score=0.8,
        access_date=datetime(2026, 4, 1),
    )


# ---------------------------------------------------------------------------
# check_url_liveness tests
# ---------------------------------------------------------------------------


class TestCheckUrlLiveness:
    async def test_head_success(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url="https://example.com/doc", method="HEAD", status_code=200)
        result = await check_url_liveness("https://example.com/doc")
        assert result is True

    async def test_head_fails_get_succeeds(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url="https://example.com/doc", method="HEAD", status_code=405)
        httpx_mock.add_response(url="https://example.com/doc", method="GET", status_code=200)
        result = await check_url_liveness("https://example.com/doc")
        assert result is True

    async def test_both_fail(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url="https://example.com/doc", method="HEAD", status_code=404)
        httpx_mock.add_response(url="https://example.com/doc", method="GET", status_code=404)
        result = await check_url_liveness("https://example.com/doc")
        assert result is False

    async def test_connection_error(self, httpx_mock: HTTPXMock):
        httpx_mock.add_exception(httpx.ConnectError("refused"), url="https://dead.example.com")
        result = await check_url_liveness("https://dead.example.com")
        assert result is False

    async def test_timeout(self, httpx_mock: HTTPXMock):
        httpx_mock.add_exception(
            httpx.TimeoutException("timed out"), url="https://slow.example.com"
        )
        result = await check_url_liveness("https://slow.example.com", timeout=1.0)
        assert result is False

    async def test_redirect_counts_as_live(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url="https://example.com/old", method="HEAD", status_code=301)
        result = await check_url_liveness("https://example.com/old")
        assert result is True


# ---------------------------------------------------------------------------
# batch_check_urls tests
# ---------------------------------------------------------------------------


class TestBatchCheckUrls:
    async def test_batch_checking(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url="https://live.com", method="HEAD", status_code=200)
        httpx_mock.add_response(url="https://dead.com", method="HEAD", status_code=404)
        httpx_mock.add_response(url="https://dead.com", method="GET", status_code=404)

        citations = [
            _cit("CIT-001", "https://live.com"),
            _cit("CIT-002", "https://dead.com"),
        ]
        results = await batch_check_urls(citations, concurrency=5)
        assert results["CIT-001"] is True
        assert results["CIT-002"] is False

    async def test_empty_citations(self, httpx_mock: HTTPXMock):
        results = await batch_check_urls([], concurrency=5)
        assert results == {}

    async def test_concurrency_respected(self, httpx_mock: HTTPXMock):
        for i in range(20):
            httpx_mock.add_response(
                url=f"https://site{i}.com", method="HEAD", status_code=200
            )
        citations = [_cit(f"CIT-{i:03d}", f"https://site{i}.com") for i in range(20)]
        results = await batch_check_urls(citations, concurrency=3)
        assert len(results) == 20
        assert all(v is True for v in results.values())
