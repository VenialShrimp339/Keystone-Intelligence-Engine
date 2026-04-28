"""Tests for Layer 1 deterministic evaluator."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from keystone.evaluator.layer1_deterministic import (
    Layer1Evaluator,
    _split_text_into_chunks,
)
from keystone.models.citations import Citation, CitationManifest, SourceType


def _make_citation(cid: str, url: str = "https://example.com", doi: str | None = None) -> Citation:
    return Citation(
        citation_id=cid,
        engagement_id="ENG-001",
        client_id="CLT-001",
        url=url,
        doi=doi,
        title=f"Test Source {cid}",
        source_type=SourceType.REPORT,
        quality_score=0.8,
        access_date=datetime.now(UTC),
    )


def _make_manifest(*citations: Citation) -> CitationManifest:
    return CitationManifest(
        manifest_id="MAN-001",
        engagement_id="ENG-001",
        client_id="CLT-001",
        citations=list(citations),
    )


class TestFactDecomposition:
    """FActScore decomposition produces atomic claims from mock LLM."""

    @pytest.mark.asyncio
    async def test_decomposes_claims(self) -> None:
        mock_response = json.dumps(
            [
                {
                    "claim": "Revenue was $50M",
                    "status": "SUPPORTED",
                    "citation_id": "CIT-001",
                    "reasoning": "Matches source",
                },
                {
                    "claim": "Growth was 20%",
                    "status": "NOT_SUPPORTED",
                    "citation_id": None,
                    "reasoning": "No citation",
                },
                {
                    "claim": "Market is shrinking",
                    "status": "CONTRADICTED",
                    "citation_id": "CIT-002",
                    "reasoning": "Source says growing",
                },
            ]
        )
        llm = AsyncMock(return_value=mock_response)
        evaluator = Layer1Evaluator(llm=llm)
        cit = _make_citation("CIT-001")
        manifest = _make_manifest(cit)

        result = await evaluator.evaluate("Some research text about revenue.", manifest)
        assert result.facts_verified == 1
        assert result.facts_failed == 2

    @pytest.mark.asyncio
    async def test_retry_is_in_call_path(self) -> None:
        """Verify retry_llm_call is invoked (mock LLM call count)."""
        call_count = 0

        async def counting_llm(prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            if "Fact Decomposition" in prompt:
                return json.dumps([])
            return json.dumps({"numerical_claims": [], "inconsistencies": []})

        evaluator = Layer1Evaluator(llm=counting_llm)
        manifest = _make_manifest(_make_citation("CIT-001"))
        await evaluator.evaluate("Some text.", manifest)
        assert call_count == 2  # fact_decomposition + numerical_consistency


class TestNumericalConsistency:
    @pytest.mark.asyncio
    async def test_catches_contradictions(self) -> None:
        mock_fact = json.dumps([])
        mock_num = json.dumps(
            {
                "numerical_claims": [
                    {"value": "15%", "metric": "revenue growth", "location": "paragraph 2"},
                    {"value": "12.3%", "metric": "revenue growth", "location": "table row 4"},
                ],
                "inconsistencies": [
                    {
                        "metric": "revenue growth",
                        "value_a": "15%",
                        "location_a": "paragraph 2",
                        "value_b": "12.3%",
                        "location_b": "table row 4",
                        "severity": "high",
                        "explanation": "Same metric, contradictory values",
                    },
                ],
            }
        )

        call_idx = 0

        async def mock_llm(prompt: str) -> str:
            nonlocal call_idx
            call_idx += 1
            if call_idx == 1:
                return mock_fact
            return mock_num

        evaluator = Layer1Evaluator(llm=mock_llm)
        manifest = _make_manifest(_make_citation("CIT-001"))
        result = await evaluator.evaluate("Revenue grew 15% but table shows 12.3%.", manifest)
        assert len(result.numerical_inconsistencies) == 1
        assert "revenue growth" in result.numerical_inconsistencies[0]


class TestURLLiveness:
    @pytest.mark.asyncio
    async def test_integrates_with_batch_check(self) -> None:
        """URL liveness integrates with batch_check_urls (mocked)."""
        cit1 = _make_citation("CIT-001", url="https://live.com")
        cit2 = _make_citation("CIT-002", url="https://dead.com")
        manifest = _make_manifest(cit1, cit2)

        async def mock_llm(prompt: str) -> str:
            return (
                json.dumps([])
                if "[" in prompt
                else json.dumps({"numerical_claims": [], "inconsistencies": []})
            )

        with patch(
            "keystone.evaluator.layer1_deterministic.batch_check_urls",
            new_callable=AsyncMock,
            return_value={"CIT-001": True, "CIT-002": False},
        ):
            evaluator = Layer1Evaluator(llm=mock_llm)
            result = await evaluator.evaluate("Test text.", manifest)
            assert result.dead_urls == ["CIT-002"]


class TestEdgeCases:
    @pytest.mark.asyncio
    async def test_empty_output_handled_gracefully(self) -> None:
        llm = AsyncMock(return_value="[]")
        evaluator = Layer1Evaluator(llm=llm)
        manifest = _make_manifest()
        result = await evaluator.evaluate("", manifest)
        assert result.facts_verified == 0
        assert result.facts_failed == 0
        assert result.numerical_inconsistencies == []
        assert result.dead_urls == []
        llm.assert_not_called()

    @pytest.mark.asyncio
    async def test_layer1_result_fields_populated(self) -> None:
        async def mock_llm(prompt: str) -> str:
            if "Fact Decomposition" in prompt:
                return json.dumps(
                    [
                        {
                            "claim": "X",
                            "status": "SUPPORTED",
                            "citation_id": "CIT-001",
                            "reasoning": "ok",
                        },
                    ]
                )
            return json.dumps({"numerical_claims": [], "inconsistencies": []})

        manifest = _make_manifest(_make_citation("CIT-001"))
        with patch(
            "keystone.evaluator.layer1_deterministic.batch_check_urls",
            new_callable=AsyncMock,
            return_value={"CIT-001": True},
        ):
            evaluator = Layer1Evaluator(llm=mock_llm)
            result = await evaluator.evaluate("Some research.", manifest)
            assert result.facts_verified == 1
            assert result.facts_failed == 0
            assert result.numerical_inconsistencies == []
            assert result.dead_urls == []


class TestTextChunking:
    """Tests for _split_text_into_chunks."""

    def test_short_text_single_chunk(self) -> None:
        text = "A short paragraph."
        chunks = _split_text_into_chunks(text)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_splits_on_paragraph_boundary(self) -> None:
        paragraphs = [f"Paragraph {i} " + "word " * 200 for i in range(5)]
        text = "\n\n".join(paragraphs)
        chunks = _split_text_into_chunks(text, max_words=300)
        assert len(chunks) > 1
        recombined = "\n\n".join(chunks)
        for p in paragraphs:
            assert p.strip() in recombined

    def test_empty_text_returns_original(self) -> None:
        chunks = _split_text_into_chunks("")
        assert len(chunks) == 1


class TestChunkedFactDecomposition:
    """Fact decomposition chunking for large outputs."""

    @pytest.mark.asyncio
    async def test_small_output_single_call(self) -> None:
        mock_response = json.dumps(
            [
                {
                    "claim": "Revenue was $50M",
                    "status": "SUPPORTED",
                    "citation_id": "CIT-001",
                    "reasoning": "ok",
                },
            ]
        )
        call_count = 0

        async def counting_llm(prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            if "Fact Decomposition" in prompt:
                return mock_response
            return json.dumps({"numerical_claims": [], "inconsistencies": []})

        evaluator = Layer1Evaluator(llm=counting_llm)
        manifest = _make_manifest(_make_citation("CIT-001"))
        result = await evaluator.evaluate("Revenue was $50M.", manifest)
        assert result.facts_verified == 1
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_large_output_multiple_chunks(self) -> None:
        chunk_calls = 0

        async def mock_llm(prompt: str) -> str:
            nonlocal chunk_calls
            if "Fact Decomposition" in prompt:
                chunk_calls += 1
                return json.dumps(
                    [
                        {
                            "claim": f"Fact from chunk {chunk_calls}",
                            "status": "SUPPORTED",
                            "citation_id": "CIT-001",
                            "reasoning": "ok",
                        },
                        {
                            "claim": f"Another fact from chunk {chunk_calls}",
                            "status": "NOT_SUPPORTED",
                            "citation_id": None,
                            "reasoning": "missing",
                        },
                    ]
                )
            return json.dumps({"numerical_claims": [], "inconsistencies": []})

        long_text = "\n\n".join(f"Paragraph {i}: " + "word " * 250 + "[CIT-001]" for i in range(10))
        evaluator = Layer1Evaluator(llm=mock_llm)
        manifest = _make_manifest(_make_citation("CIT-001"))
        result = await evaluator.evaluate(long_text, manifest)
        assert chunk_calls > 1
        assert result.facts_verified == chunk_calls
        assert result.facts_failed == chunk_calls

    @pytest.mark.asyncio
    async def test_aggregate_metrics_across_chunks(self) -> None:
        chunk_idx = 0

        async def mock_llm(prompt: str) -> str:
            nonlocal chunk_idx
            if "Fact Decomposition" in prompt:
                chunk_idx += 1
                if chunk_idx == 1:
                    return json.dumps(
                        [
                            {
                                "claim": "A",
                                "status": "SUPPORTED",
                                "citation_id": "CIT-001",
                                "reasoning": "ok",
                            },
                            {
                                "claim": "B",
                                "status": "SUPPORTED",
                                "citation_id": "CIT-001",
                                "reasoning": "ok",
                            },
                        ]
                    )
                return json.dumps(
                    [
                        {
                            "claim": "C",
                            "status": "CONTRADICTED",
                            "citation_id": "CIT-002",
                            "reasoning": "wrong",
                        },
                    ]
                )
            return json.dumps({"numerical_claims": [], "inconsistencies": []})

        long_text = "\n\n".join(
            f"Section {i}: " + "word " * 500 + f"[CIT-00{i % 2 + 1}]" for i in range(4)
        )
        cit1 = _make_citation("CIT-001")
        cit2 = _make_citation("CIT-002")
        evaluator = Layer1Evaluator(llm=mock_llm)
        manifest = _make_manifest(cit1, cit2)
        result = await evaluator.evaluate(long_text, manifest)
        assert result.facts_verified == 2
        assert result.facts_failed >= 1
