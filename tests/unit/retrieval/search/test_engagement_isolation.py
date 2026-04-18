"""Inter-agent isolation invariant: exclude_engagement_id filter.

During an active engagement, the retrieval service must NOT surface
chunks ingested by other agents in the same engagement (Founder Intent
Doctrine: Inter-Agent Isolation). Chunks from prior engagements
(``engagement_id=None``) are institutional memory and stay visible.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable

    from keystone.retrieval.parse_models import EvidencePrepRecord
from keystone.retrieval.search.bm25_index import InMemoryBM25Index
from keystone.retrieval.search.chunker import SemanticChunker
from keystone.retrieval.search.embeddings import InMemoryEmbeddingClient
from keystone.retrieval.search.models import SearchQuery
from keystone.retrieval.search.retrieval_service import RetrievalService
from keystone.retrieval.search.vector_store import InMemoryVectorStore


def _make_service(*, dimension: int = 32) -> RetrievalService:
    return RetrievalService(
        chunker=SemanticChunker(
            target_tokens=80,
            max_tokens=120,
            overlap_tokens=16,
            add_contextual_preamble=False,
        ),
        embedder=InMemoryEmbeddingClient(dimension=dimension),
        vector_store=InMemoryVectorStore(dimension=dimension),
        bm25_index=InMemoryBM25Index(),
    )


class TestEngagementExclusion:
    async def test_chunker_stamps_engagement_id(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        chunker = SemanticChunker(
            target_tokens=50,
            max_tokens=100,
            overlap_tokens=10,
            add_contextual_preamble=False,
        )
        records = [make_record(artifact_id="art-A", text="some text for testing")]
        chunks = chunker.chunk(records, engagement_id="eng-1")
        assert all(c.metadata.engagement_id == "eng-1" for c in chunks)

    async def test_chunker_explicit_none_is_institutional(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        # Passing engagement_id=None explicitly tags the chunk as
        # institutional memory. There is no implicit default -- the
        # caller must opt into this behavior so untagged ingest cannot
        # happen accidentally.
        chunker = SemanticChunker(add_contextual_preamble=False)
        chunks = chunker.chunk([make_record(text="some text")], engagement_id=None)
        assert all(c.metadata.engagement_id is None for c in chunks)

    async def test_ingest_stamps_engagement_id_on_chunks(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        service = _make_service()
        records = [
            make_record(
                artifact_id="art-A",
                text="Apple iPhone sales " + " ".join(f"w{i}" for i in range(100)),
            )
        ]
        await service.ingest(records, engagement_id="eng-1")
        # Read back via the in-memory vector store directly.
        # ``_chunks`` is a private view we rely on only in tests.
        store = service.vector_store
        assert hasattr(store, "_chunks")
        stored = list(store._chunks.values())  # type: ignore[attr-defined]
        assert stored
        assert all(c.metadata.engagement_id == "eng-1" for c in stored)

    async def test_exclude_engagement_drops_current_engagement_chunks(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        service = _make_service()
        # Prior engagement: institutional memory (engagement_id=None).
        await service.ingest(
            [
                make_record(
                    artifact_id="inst-target",
                    text=(
                        "Apple iPhone sales fell in the latest quarter as "
                        "consumers held onto older models longer."
                    ),
                ),
            ],
            engagement_id=None,
        )
        # Current engagement, other agent's parallel ingest that this
        # query must NOT see.
        await service.ingest(
            [
                make_record(
                    artifact_id="cur-secret",
                    text=(
                        "Apple iPhone sales jumped dramatically on the "
                        "new model launch, opposite of the prior quarter."
                    ),
                ),
            ],
            engagement_id="eng-active",
        )

        results = await service.search("iPhone sales", top_k=5, exclude_engagement_id="eng-active")
        ids = {r.chunk.metadata.artifact_id for r in results}
        assert "cur-secret" not in ids, "current-engagement chunk leaked to another agent"
        assert "inst-target" in ids, "institutional memory should remain visible"

    async def test_exclusion_preserves_other_engagements(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        service = _make_service()
        # A chunk from a DIFFERENT engagement should still be visible.
        await service.ingest(
            [
                make_record(
                    artifact_id="other-eng",
                    text="iPhone sales report from " + " ".join(f"w{i}" for i in range(40)),
                )
            ],
            engagement_id="eng-other",
        )
        await service.ingest(
            [
                make_record(
                    artifact_id="cur-secret",
                    text="iPhone sales current engagement " + " ".join(f"w{i}" for i in range(40)),
                )
            ],
            engagement_id="eng-active",
        )
        results = await service.search("iPhone sales", top_k=5, exclude_engagement_id="eng-active")
        ids = {r.chunk.metadata.artifact_id for r in results}
        assert "other-eng" in ids
        assert "cur-secret" not in ids

    async def test_no_exclusion_returns_everything(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        service = _make_service()
        await service.ingest(
            [
                make_record(
                    artifact_id="art-A",
                    text="iPhone sales grew " + " ".join(f"w{i}" for i in range(40)),
                )
            ],
            engagement_id="eng-active",
        )
        await service.ingest(
            [
                make_record(
                    artifact_id="art-B",
                    text="iPhone sales fell " + " ".join(f"w{i}" for i in range(40)),
                )
            ],
            engagement_id=None,
        )
        results = await service.search("iPhone sales", top_k=5)
        ids = {r.chunk.metadata.artifact_id for r in results}
        assert {"art-A", "art-B"} <= ids

    async def test_search_query_exclude_engagement_id_respected(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        # Passing via the SearchQuery model directly (rather than the
        # search kwarg) also works.
        service = _make_service()
        await service.ingest(
            [
                make_record(
                    artifact_id="cur",
                    text="iPhone sales from " + " ".join(f"w{i}" for i in range(40)),
                )
            ],
            engagement_id="eng-active",
        )
        await service.ingest(
            [
                make_record(
                    artifact_id="inst",
                    text="iPhone report stored " + " ".join(f"w{i}" for i in range(40)),
                )
            ],
            engagement_id=None,
        )
        q = SearchQuery(
            text="iPhone sales",
            top_k=3,
            candidate_pool=20,
            exclude_engagement_id="eng-active",
        )
        results = await service.search(q)
        ids = {r.chunk.metadata.artifact_id for r in results}
        assert "cur" not in ids
        assert "inst" in ids


class TestRequiredEngagementId:
    """Structural guarantees: the dangerous (untagged) path is deliberate."""

    def test_chunker_chunk_requires_engagement_id_kwarg(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        chunker = SemanticChunker(add_contextual_preamble=False)
        with pytest.raises(TypeError):
            chunker.chunk([make_record(text="x")])  # type: ignore[call-arg]

    async def test_service_ingest_requires_engagement_id_kwarg(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        service = _make_service()
        with pytest.raises(TypeError):
            await service.ingest([make_record(text="x")])  # type: ignore[call-arg]

    async def test_ingest_institutional_tags_none(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        service = _make_service()
        records = [
            make_record(
                artifact_id="inst-A",
                text="institutional " + " ".join(f"w{i}" for i in range(60)),
            )
        ]
        await service.ingest_institutional(records)
        store = service.vector_store
        assert hasattr(store, "_chunks")
        stored = list(store._chunks.values())  # type: ignore[attr-defined]
        assert stored
        assert all(c.metadata.engagement_id is None for c in stored)


class TestEngagementContext:
    """Default-on isolation via service-level engagement_context."""

    def _make_service_with_context(
        self, engagement_context: str, *, dimension: int = 32
    ) -> RetrievalService:
        return RetrievalService(
            chunker=SemanticChunker(
                target_tokens=80,
                max_tokens=120,
                overlap_tokens=16,
                add_contextual_preamble=False,
            ),
            embedder=InMemoryEmbeddingClient(dimension=dimension),
            vector_store=InMemoryVectorStore(dimension=dimension),
            bm25_index=InMemoryBM25Index(),
            engagement_context=engagement_context,
        )

    async def test_context_exposed_on_property(self) -> None:
        service = self._make_service_with_context("eng-X")
        assert service.engagement_context == "eng-X"
        assert _make_service().engagement_context is None

    async def test_string_form_search_inherits_context(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        service = self._make_service_with_context("eng-active")
        await service.ingest(
            [
                make_record(
                    artifact_id="cur-secret",
                    text="iPhone sales current " + " ".join(f"w{i}" for i in range(40)),
                )
            ],
            engagement_id="eng-active",
        )
        await service.ingest_institutional(
            [
                make_record(
                    artifact_id="inst-target",
                    text=(
                        "Apple iPhone sales fell in the latest quarter as "
                        "consumers held onto older models longer."
                    ),
                )
            ],
        )

        # No explicit exclude_engagement_id -- context auto-applies.
        results = await service.search("iPhone sales", top_k=5)
        ids = {r.chunk.metadata.artifact_id for r in results}
        assert "cur-secret" not in ids, "engagement_context did not auto-apply"
        assert "inst-target" in ids

    async def test_explicit_kwarg_overrides_context(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        service = self._make_service_with_context("eng-context")
        await service.ingest(
            [
                make_record(
                    artifact_id="art-ctx",
                    text="iPhone context " + " ".join(f"w{i}" for i in range(40)),
                )
            ],
            engagement_id="eng-context",
        )
        await service.ingest(
            [
                make_record(
                    artifact_id="art-other",
                    text="iPhone other " + " ".join(f"w{i}" for i in range(40)),
                )
            ],
            engagement_id="eng-other",
        )
        # Explicit kwarg points at a different engagement -- it must win
        # over the service's context. Context-engagement chunk is now
        # visible; the explicitly-excluded eng-other is hidden.
        results = await service.search("iPhone", top_k=5, exclude_engagement_id="eng-other")
        ids = {r.chunk.metadata.artifact_id for r in results}
        assert "art-other" not in ids
        assert "art-ctx" in ids

    async def test_raw_search_query_none_is_opt_out(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        service = self._make_service_with_context("eng-active")
        await service.ingest(
            [
                make_record(
                    artifact_id="cur-secret",
                    text="iPhone raw " + " ".join(f"w{i}" for i in range(40)),
                )
            ],
            engagement_id="eng-active",
        )
        # Caller built their own SearchQuery with exclude_engagement_id
        # left unset. By docstring contract this is "opt out of
        # isolation", so the service-level context must NOT be
        # substituted. The current-engagement chunk stays visible.
        q = SearchQuery(text="iPhone", top_k=5, candidate_pool=20)
        results = await service.search(q)
        ids = {r.chunk.metadata.artifact_id for r in results}
        assert "cur-secret" in ids

    async def test_raw_search_query_with_field_set_is_honored(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        service = self._make_service_with_context("eng-context")
        await service.ingest(
            [
                make_record(
                    artifact_id="art-ctx",
                    text="iPhone ctx " + " ".join(f"w{i}" for i in range(40)),
                )
            ],
            engagement_id="eng-context",
        )
        await service.ingest(
            [
                make_record(
                    artifact_id="art-other",
                    text="iPhone other " + " ".join(f"w{i}" for i in range(40)),
                )
            ],
            engagement_id="eng-other",
        )
        # Raw SearchQuery with its OWN exclude wins (caller's intent).
        q = SearchQuery(
            text="iPhone",
            top_k=5,
            candidate_pool=20,
            exclude_engagement_id="eng-other",
        )
        results = await service.search(q)
        ids = {r.chunk.metadata.artifact_id for r in results}
        assert "art-other" not in ids
        assert "art-ctx" in ids

    async def test_no_context_means_string_form_sees_everything(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        # System-level caller: no engagement_context on the service.
        # String-form search returns the full corpus.
        service = _make_service()
        await service.ingest(
            [
                make_record(
                    artifact_id="art-A",
                    text="iPhone A " + " ".join(f"w{i}" for i in range(40)),
                )
            ],
            engagement_id="eng-1",
        )
        await service.ingest(
            [
                make_record(
                    artifact_id="art-B",
                    text="iPhone B " + " ".join(f"w{i}" for i in range(40)),
                )
            ],
            engagement_id="eng-2",
        )
        results = await service.search("iPhone", top_k=5)
        ids = {r.chunk.metadata.artifact_id for r in results}
        assert {"art-A", "art-B"} <= ids


class TestFilterHelpers:
    def test_pgvector_where_clause_includes_engagement_guard(self) -> None:
        from keystone.retrieval.search.vector_store import _build_filters

        where_sql, args = _build_filters({"exclude_engagement_id": "eng-1"})
        assert "engagement_id" in where_sql
        # Institutional memory (NULL) must always pass.
        assert "IS NULL" in where_sql
        assert args == ["eng-1"]

    def test_pgvector_where_clause_combines_with_other_filters(self) -> None:
        from keystone.retrieval.search.vector_store import _build_filters

        where_sql, args = _build_filters(
            {
                "artifact_id": "art-A",
                "exclude_engagement_id": "eng-1",
            }
        )
        assert "artifact_id IN ($2)" in where_sql
        assert "engagement_id" in where_sql
        assert args == ["art-A", "eng-1"]
