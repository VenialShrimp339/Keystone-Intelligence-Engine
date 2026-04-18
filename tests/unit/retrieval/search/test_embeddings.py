"""Unit tests for the embedding clients."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import pytest

from keystone.retrieval.search.embeddings import (
    VOYAGE_FINANCE_DIM,
    EmbeddingDimensionError,
    EmbeddingError,
    InMemoryEmbeddingClient,
    VoyageEmbeddingClient,
)


class TestInMemoryEmbeddingClient:
    async def test_deterministic(self) -> None:
        client = InMemoryEmbeddingClient(dimension=32)
        a = await client.embed(["hello world"])
        b = await client.embed(["hello world"])
        assert a == b

    async def test_dimension(self) -> None:
        client = InMemoryEmbeddingClient(dimension=64)
        vectors = await client.embed(["alpha", "beta", "gamma"])
        assert len(vectors) == 3
        assert all(len(v) == 64 for v in vectors)

    async def test_unit_norm(self) -> None:
        client = InMemoryEmbeddingClient(dimension=32)
        [vector] = await client.embed(["keystone"])
        norm = math.sqrt(sum(v * v for v in vector))
        assert 0.99 < norm < 1.01

    async def test_distinct_texts_get_distinct_vectors(self) -> None:
        client = InMemoryEmbeddingClient(dimension=32)
        [a] = await client.embed(["alpha"])
        [b] = await client.embed(["beta"])
        assert a != b

    async def test_empty_input_returns_empty(self) -> None:
        client = InMemoryEmbeddingClient()
        vectors = await client.embed([])
        assert vectors == []

    async def test_embed_query_rejects_empty(self) -> None:
        client = InMemoryEmbeddingClient()
        with pytest.raises(EmbeddingError):
            await client.embed_query("   ")

    def test_dimension_must_be_two_or_more(self) -> None:
        with pytest.raises(ValueError):
            InMemoryEmbeddingClient(dimension=1)


# ---------------------------------------------------------------------------
# Voyage: use a fake SDK client so tests don't hit the network.
# ---------------------------------------------------------------------------


@dataclass
class _FakeVoyageResult:
    embeddings: list[list[float]]


class _FakeVoyageClient:
    def __init__(self, dim: int = VOYAGE_FINANCE_DIM) -> None:
        self.dim = dim
        self.calls: list[dict[str, Any]] = []
        self.fail_on_call: bool = False

    def embed(self, texts: list[str], *, model: str, input_type: str) -> _FakeVoyageResult:
        if self.fail_on_call:
            raise RuntimeError("boom")
        self.calls.append({"texts": texts, "model": model, "input_type": input_type})
        return _FakeVoyageResult(
            embeddings=[[0.01 * (i + 1)] * self.dim for i in range(len(texts))]
        )


class TestVoyageEmbeddingClient:
    def test_requires_api_key(self) -> None:
        with pytest.raises(EmbeddingError):
            VoyageEmbeddingClient(api_key="", client=_FakeVoyageClient())

    def test_batch_size_bounds(self) -> None:
        with pytest.raises(ValueError):
            VoyageEmbeddingClient(api_key="k", batch_size=0, client=_FakeVoyageClient())
        with pytest.raises(ValueError):
            VoyageEmbeddingClient(api_key="k", batch_size=1024, client=_FakeVoyageClient())

    async def test_batching(self) -> None:
        fake = _FakeVoyageClient()
        client = VoyageEmbeddingClient(api_key="k", batch_size=2, client=fake)
        vectors = await client.embed(["a", "b", "c", "d", "e"])
        assert len(vectors) == 5
        # 5 texts into batches of 2 -> 3 SDK calls
        assert len(fake.calls) == 3
        assert fake.calls[0]["input_type"] == "document"

    async def test_query_uses_query_input_type(self) -> None:
        fake = _FakeVoyageClient()
        client = VoyageEmbeddingClient(api_key="k", client=fake)
        await client.embed_query("some query")
        assert fake.calls[-1]["input_type"] == "query"

    async def test_upstream_failure_wrapped(self) -> None:
        fake = _FakeVoyageClient()
        fake.fail_on_call = True
        client = VoyageEmbeddingClient(api_key="k", client=fake)
        with pytest.raises(EmbeddingError):
            await client.embed(["anything"])

    async def test_dimension_mismatch_raises(self) -> None:
        fake = _FakeVoyageClient(dim=512)
        client = VoyageEmbeddingClient(api_key="k", client=fake, dimension=VOYAGE_FINANCE_DIM)
        with pytest.raises(EmbeddingDimensionError):
            await client.embed(["anything"])
