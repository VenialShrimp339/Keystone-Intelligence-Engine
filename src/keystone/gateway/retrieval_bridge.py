"""Bridge between the MCP gateway's IN_PROCESS transport and the RetrievalService.

The gateway dispatches tool calls through a pluggable
:func:`MCPGateway.register_in_process_handler` hook. This module wires
the ``semantic_search`` and ``hybrid_search`` tool names to a
:class:`RetrievalService`, translating the gateway's generic parameter
dict into a :class:`SearchQuery` and converting the returned
:class:`RetrievalResult` objects back into JSON-serializable payloads
that the gateway's citation extractor and audit logger can consume.

Every handler call emits a :class:`SearchCompleted` pipeline event
through the optional ``event_sink`` callback, so Layer 4's
process-trajectory metrics can pick up internal-corpus usage and
distinguish it from external MCP tool calls.

``semantic_search`` calls ``RetrievalService.search_semantic``, which
embeds the query and queries the vector store directly — no BM25, no
RRF fusion, no reranking. Use it for conceptual / semantic queries where
dense similarity is the right signal.

``hybrid_search`` calls ``RetrievalService.search``, which runs the full
vector + BM25 → RRF → Cohere rerank pipeline with graceful degradation.
Use it when exact-term recall matters alongside semantic relevance.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from keystone.events import SearchCompleted
from keystone.retrieval.search.models import RetrievalResult, SearchQuery
from keystone.tool_names import ToolName

if TYPE_CHECKING:
    from keystone.gateway.mcp_gateway import InProcessHandler, MCPGateway, ToolCall
    from keystone.retrieval.search.retrieval_service import RetrievalService

EventSink = Callable[[SearchCompleted], None]
"""Callback invoked once per retrieval-tool call with the emitted event."""

# Maximum characters of the user's query preserved on the emitted event.
# Longer queries are truncated so a 10 KB prompt does not bloat the
# observability stream.
_QUERY_PREVIEW_CHARS = 120


def build_retrieval_handlers(
    service: RetrievalService,
    *,
    event_sink: EventSink | None = None,
) -> dict[str, InProcessHandler]:
    """Return ``{tool_name: handler}`` for the retrieval tools.

    Handlers translate the incoming :class:`ToolCall` into a
    :class:`SearchQuery`, run it against ``service``, and return a plain
    dict payload shaped like an MCP search result so the gateway's
    citation extractor picks up ``url`` / ``title`` fields from each hit.

    When ``event_sink`` is supplied, the handler emits a
    :class:`SearchCompleted` event per call. The sink is called
    synchronously from the handler so failures surface immediately; pass
    ``None`` to suppress event emission.
    """

    async def semantic_search(call: ToolCall) -> dict[str, Any]:
        return await _run_search(
            service=service,
            call=call,
            tool_name=ToolName.SEMANTIC_SEARCH.value,
            event_sink=event_sink,
            use_semantic=True,
        )

    async def hybrid_search(call: ToolCall) -> dict[str, Any]:
        return await _run_search(
            service=service,
            call=call,
            tool_name=ToolName.HYBRID_SEARCH.value,
            event_sink=event_sink,
            use_semantic=False,
        )

    return {
        ToolName.SEMANTIC_SEARCH.value: semantic_search,
        ToolName.HYBRID_SEARCH.value: hybrid_search,
    }


def register_retrieval_handlers(
    gateway: MCPGateway,
    service: RetrievalService,
    *,
    event_sink: EventSink | None = None,
) -> None:
    """Attach the retrieval handlers to ``gateway`` in one call."""

    for tool_name, handler in build_retrieval_handlers(service, event_sink=event_sink).items():
        gateway.register_in_process_handler(tool_name, handler)


async def _run_search(
    *,
    service: RetrievalService,
    call: ToolCall,
    tool_name: str,
    event_sink: EventSink | None,
    use_semantic: bool = False,
) -> dict[str, Any]:
    query = _build_query(call.parameters)
    # Structural inter-agent isolation: unless the caller already specified
    # an exclusion, hide chunks tagged with the caller's own engagement_id.
    # Lane E passages are ingested as institutional memory
    # (engagement_id=None) so they survive the filter; mid-research chunks
    # produced by sibling agents in the same engagement do not.
    if query.exclude_engagement_id is None:
        query = query.model_copy(update={"exclude_engagement_id": call.engagement_id})
    start = time.monotonic()
    if use_semantic:
        results = await service.search_semantic(query)
    else:
        results = await service.search(query)
    latency_ms = (time.monotonic() - start) * 1000
    payload = _serialize_results(results)
    if event_sink is not None:
        event_sink(
            SearchCompleted(
                event_id=f"evt-{uuid4().hex[:12]}",
                engagement_id=call.engagement_id,
                client_id=call.client_id,
                agent_id=call.agent_id,
                tool_name=tool_name,
                query_preview=_preview(query.text),
                result_count=len(results),
                latency_ms=latency_ms,
            )
        )
    return payload


def _build_query(parameters: dict[str, Any]) -> SearchQuery:
    text = parameters.get("query") or parameters.get("text") or ""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("retrieval tool call requires non-empty 'query' or 'text' parameter")
    top_k_raw = parameters.get("top_k", 10)
    try:
        top_k = int(top_k_raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"top_k must be an int, got {top_k_raw!r}") from exc
    if top_k < 1:
        raise ValueError(f"top_k must be >= 1, got {top_k}")
    exclude = parameters.get("exclude_engagement_id")
    if exclude is not None and not isinstance(exclude, str):
        raise ValueError(f"exclude_engagement_id must be str or None, got {type(exclude).__name__}")
    candidate_pool = max(top_k, 150)
    return SearchQuery(
        text=text,
        top_k=top_k,
        candidate_pool=candidate_pool,
        exclude_engagement_id=exclude,
    )


def _serialize_results(results: list[RetrievalResult]) -> dict[str, Any]:
    return {
        "results": [_result_to_dict(r) for r in results],
        "result_count": len(results),
    }


def _result_to_dict(result: RetrievalResult) -> dict[str, Any]:
    chunk = result.chunk
    meta = chunk.metadata
    return {
        "chunk_id": chunk.chunk_id,
        "text": chunk.raw_text,
        "score": result.score,
        "source": result.source.value,
        "rank": result.rank,
        "url": meta.canonical_url,
        "title": meta.title,
        "artifact_id": meta.artifact_id,
        "content_hash": meta.content_hash,
        "locator": meta.locator.model_dump(mode="json"),
        "source_family": meta.source_family.value,
        "parse_confidence": meta.parse_confidence.tier.value,
    }


def _preview(text: str) -> str:
    if len(text) <= _QUERY_PREVIEW_CHARS:
        return text
    return text[: _QUERY_PREVIEW_CHARS - 1].rstrip() + "\u2026"
