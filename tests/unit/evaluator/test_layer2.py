"""Tests for Layer 2 citation gate."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from keystone.evaluator.layer2_citation_gate import (
    DOIVerificationResult,
    DOIVerifier,
    HTTPDOIVerifier,
    Layer2CitationGate,
)
from keystone.models.citations import Citation, CitationManifest, SourceType


def _cit(
    cid: str,
    doi: str | None = None,
    url: str = "https://example.com",
) -> Citation:
    return Citation(
        citation_id=cid,
        engagement_id="ENG-001",
        client_id="CLT-001",
        url=url,
        doi=doi,
        title=f"Test Source {cid}",
        source_type=SourceType.ACADEMIC,
        quality_score=0.9,
        access_date=datetime.now(UTC),
    )


def _manifest(*citations: Citation) -> CitationManifest:
    return CitationManifest(
        manifest_id="MAN-001",
        engagement_id="ENG-001",
        client_id="CLT-001",
        citations=list(citations),
    )


class MockDOIVerifier:
    """Mock DOI verifier for testing."""

    def __init__(self, results: dict[str, DOIVerificationResult]) -> None:
        self._results = results

    async def verify(self, doi: str) -> DOIVerificationResult:
        return self._results.get(doi, DOIVerificationResult(exists=False))


class TestDOIVerification:
    @pytest.mark.asyncio
    async def test_valid_doi_passes(self) -> None:
        verifier = MockDOIVerifier({
            "10.1234/real.2024": DOIVerificationResult(exists=True),
        })
        gate = Layer2CitationGate(doi_verifier=verifier)
        manifest = _manifest(_cit("CIT-001", doi="10.1234/real.2024"))
        result = await gate.evaluate(manifest)
        assert result.gate_passed is True
        assert result.citations_verified == 1
        assert result.citations_fabricated == []

    @pytest.mark.asyncio
    async def test_fabricated_doi_fails(self) -> None:
        verifier = MockDOIVerifier({
            "10.9999/fake.2024.0001": DOIVerificationResult(exists=False),
        })
        gate = Layer2CitationGate(doi_verifier=verifier)
        manifest = _manifest(_cit("CIT-001", doi="10.9999/fake.2024.0001"))
        result = await gate.evaluate(manifest)
        assert result.gate_passed is False
        assert result.citations_fabricated == ["CIT-001"]

    @pytest.mark.asyncio
    async def test_mixed_citations_one_fabricated_fails(self) -> None:
        verifier = MockDOIVerifier({
            "10.1234/real.1": DOIVerificationResult(exists=True),
            "10.1234/real.2": DOIVerificationResult(exists=True),
            "10.9999/fake.1": DOIVerificationResult(exists=False),
        })
        gate = Layer2CitationGate(doi_verifier=verifier)
        manifest = _manifest(
            _cit("CIT-001", doi="10.1234/real.1"),
            _cit("CIT-002", doi="10.1234/real.2"),
            _cit("CIT-003", doi="10.9999/fake.1"),
        )
        result = await gate.evaluate(manifest)
        assert result.gate_passed is False
        assert "CIT-003" in result.citations_fabricated
        assert result.citations_verified == 2


class TestURLOnlyCitations:
    @pytest.mark.asyncio
    async def test_no_doi_uses_url_check(self) -> None:
        with patch(
            "keystone.evaluator.layer2_citation_gate.batch_check_urls",
            new_callable=AsyncMock,
            return_value={"CIT-001": True},
        ):
            gate = Layer2CitationGate()
            manifest = _manifest(_cit("CIT-001", doi=None, url="https://live.com"))
            result = await gate.evaluate(manifest)
            assert result.gate_passed is True
            assert result.citations_verified == 1


class TestEdgeCases:
    @pytest.mark.asyncio
    async def test_empty_manifest_passes(self) -> None:
        gate = Layer2CitationGate()
        manifest = _manifest()
        result = await gate.evaluate(manifest)
        assert result.gate_passed is True
        assert result.citations_checked == 0
        assert result.citations_verified == 0

    @pytest.mark.asyncio
    async def test_gate_passed_invariant(self) -> None:
        """gate_passed must be True iff citations_fabricated is empty."""
        verifier = MockDOIVerifier({
            "10.1234/a": DOIVerificationResult(exists=True),
        })
        gate = Layer2CitationGate(doi_verifier=verifier)
        manifest = _manifest(_cit("CIT-001", doi="10.1234/a"))
        result = await gate.evaluate(manifest)
        assert result.gate_passed == (len(result.citations_fabricated) == 0)


class TestProtocolCompliance:
    def test_mock_satisfies_protocol(self) -> None:
        verifier = MockDOIVerifier({})
        assert isinstance(verifier, DOIVerifier)

    def test_http_verifier_satisfies_protocol(self) -> None:
        verifier = HTTPDOIVerifier()
        assert isinstance(verifier, DOIVerifier)
