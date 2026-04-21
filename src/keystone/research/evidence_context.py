"""Bridge between Lane E parsed evidence and L1 research agents.

Lane E (``keystone.retrieval``) turns fetched artifacts into
``EvidencePrepRecord`` objects that carry a full provenance chain
(artifact_id, canonical_url, content_hash, coverage, parser identity,
locator, parse confidence). This module lets a research agent use
those parsed passages as part of its per-round synthesis context
alongside its normal MCP tool search results.

Two public surfaces:

* ``EvidenceContextProvider`` -- holds the records available for an
  engagement, exposes the subset relevant to a given ``ResearchTask``,
  builds an ``EV-NNN`` reference table, and renders passages as a block
  the LLM can cite from.
* ``evidence_to_citation`` -- converts a referenced ``EvidencePrepRecord``
  into a ``Citation`` so claims citing parsed passages flow through the
  existing citation/dedup pipeline.

Selection is intentionally simple in this first iteration: a provider
with no ``task_filter`` returns every record for every task. Callers
that want topic-match or category-match filtering pass in a predicate;
the Citation pipeline owns dedup and corroboration, not this bridge.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import UTC, datetime

from keystone.models.citations import Citation, SourceType
from keystone.models.tasks import ResearchTask
from keystone.retrieval.parse_models import (
    EvidencePrepRecord,
    ParseConfidenceTier,
    SourceFamily,
)

TaskFilter = Callable[[ResearchTask, EvidencePrepRecord], bool]
"""Predicate deciding whether a record is relevant to a task."""

TaskRanker = Callable[[ResearchTask, EvidencePrepRecord], float]
"""Score function for ranking records by relevance to a task."""

# Map Lane E's coarse source_family to the research pipeline's SourceType.
# URL-based inference (below) takes precedence when it matches.
_FAMILY_TO_SOURCE_TYPE: dict[SourceFamily, SourceType] = {
    SourceFamily.ARTICLE: SourceType.NEWS,
    SourceFamily.PDF: SourceType.REPORT,
    SourceFamily.REPORT: SourceType.REPORT,
    SourceFamily.UNKNOWN: SourceType.REPORT,
}

# URL-domain patterns -> SourceType, ordered by specificity.
# Kept parallel to research_agent._SOURCE_TYPE_PATTERNS so parsed evidence
# and tool-search citations classify the same URL the same way.
_URL_PATTERNS: list[tuple[str, SourceType]] = [
    ("sec.gov", SourceType.FILING),
    ("edgar", SourceType.FILING),
    (".gov", SourceType.GOVERNMENT),
    ("arxiv.org", SourceType.ACADEMIC),
    ("scholar.google", SourceType.ACADEMIC),
    ("doi.org", SourceType.ACADEMIC),
    ("pubmed", SourceType.ACADEMIC),
    ("reuters", SourceType.NEWS),
    ("bloomberg", SourceType.NEWS),
    ("wsj.com", SourceType.NEWS),
    ("ft.com", SourceType.NEWS),
    ("cnbc.com", SourceType.NEWS),
    ("techcrunch", SourceType.NEWS),
]

# Parse-confidence tier -> Citation.quality_score default.
# Admiralty-style quality starts from the parse quality signal; downstream
# evaluator layers can revise after cross-source corroboration.
_TIER_TO_QUALITY: dict[ParseConfidenceTier, float] = {
    ParseConfidenceTier.HIGH: 0.75,
    ParseConfidenceTier.MEDIUM: 0.6,
    ParseConfidenceTier.LOW: 0.4,
}

# Maximum characters of passage text rendered in the LLM synthesis prompt.
# Full text is still carried on the resulting Citation.content_snippet.
_PASSAGE_PREVIEW_CHARS = 360

# Maximum characters of passage text stored on Citation.content_snippet.
# Keeps manifest size bounded; full text lives in the originating record.
_CITATION_SNIPPET_CHARS = 500

# ---------------------------------------------------------------------------
# GAP-03: Task-aware evidence filtering + relevance ranking
# ---------------------------------------------------------------------------

_REQUIRED_TO_INFERRED: dict[str, frozenset[SourceType]] = {
    "industry_reports": frozenset({SourceType.REPORT}),
    "financial_data": frozenset({SourceType.FILING, SourceType.REPORT}),
    "academic": frozenset({SourceType.ACADEMIC}),
    "news": frozenset({SourceType.NEWS}),
    "government": frozenset({SourceType.GOVERNMENT}),
}

_STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "has",
        "have",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "shall",
        "can",
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "not",
        "no",
        "nor",
    }
)


def _tokenize(text: str) -> set[str]:
    """Lowercase, split on whitespace, drop stopwords and single chars."""
    return {w for w in text.lower().split() if w not in _STOP_WORDS and len(w) > 1}


def _relevance_score(task_description: str, record_text: str) -> float:
    """Jaccard index between task description and record text tokens."""
    task_tokens = _tokenize(task_description)
    record_tokens = _tokenize(record_text)
    if not task_tokens or not record_tokens:
        return 0.0
    intersection = task_tokens & record_tokens
    union = task_tokens | record_tokens
    return len(intersection) / len(union)


def _record_matches_required_source(record: EvidencePrepRecord, required: str) -> bool:
    """Check if a record matches a ``required_sources`` value."""
    allowed = _REQUIRED_TO_INFERRED.get(required)
    if allowed is None:
        return True
    inferred = infer_source_type(record.canonical_url, record.source_family)
    return inferred in allowed


def build_default_task_filter() -> TaskFilter:
    """Source-family filter keyed off ``task.required_sources``.

    When ``required_sources`` is empty, all records pass.  When populated,
    a record passes if it matches ANY of the required source types (OR
    semantics).  Unknown source type strings are treated as wildcards so
    newly-added source types don't silently drop all evidence.
    """

    def _filter(task: ResearchTask, record: EvidencePrepRecord) -> bool:
        if not task.required_sources:
            return True
        return any(_record_matches_required_source(record, src) for src in task.required_sources)

    return _filter


def build_default_task_ranker() -> TaskRanker:
    """Jaccard relevance ranking against ``task.description``."""

    def _ranker(task: ResearchTask, record: EvidencePrepRecord) -> float:
        return _relevance_score(task.description, record.text)

    return _ranker


def infer_source_type(url: str, source_family: SourceFamily) -> SourceType:
    """Pick a SourceType using URL domain first, then source_family fallback."""

    lower = url.lower()
    for pattern, stype in _URL_PATTERNS:
        if pattern in lower:
            return stype
    return _FAMILY_TO_SOURCE_TYPE.get(source_family, SourceType.REPORT)


def _format_locator(record: EvidencePrepRecord) -> str:
    """Human-readable locator suffix for prompt rendering."""

    loc = record.locator
    parts: list[str] = []
    if loc.page_number is not None:
        parts.append(f"p.{loc.page_number}")
    if loc.section_path:
        parts.append(" > ".join(loc.section_path))
    parts.append(f"para {loc.paragraph_index}")
    return ", ".join(parts)


def _preview(text: str, limit: int) -> str:
    """Trim ``text`` to ``limit`` chars, collapsing internal whitespace."""

    collapsed = " ".join(text.split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 1].rstrip() + "\u2026"


def evidence_to_citation(
    record: EvidencePrepRecord,
    *,
    citation_id: str,
    engagement_id: str,
    client_id: str,
    agent_id: str,
    access_date: datetime | None = None,
) -> Citation:
    """Convert an ``EvidencePrepRecord`` into a ``Citation``.

    Preserves the Lane E provenance chain on the Citation:

    * ``url`` <- ``record.canonical_url``
    * ``content_hash`` <- ``record.content_hash`` (SHA-256 of source bytes)
    * ``content_snippet`` <- passage text (trimmed to the snippet cap)
    * ``access_date`` <- ``record.fetched_at``
    * ``quality_score`` <- default for the record's parse-confidence tier
    * ``found_by_agents`` <- ``[agent_id]``

    The resulting Citation's title falls back to a descriptive string
    when the artifact had no title so downstream rendering never shows
    an empty heading.
    """

    title = record.title or f"{record.source_family.value.title()} passage ({record.record_id})"
    source_type = infer_source_type(record.canonical_url, record.source_family)
    quality_score = _TIER_TO_QUALITY[record.parse_confidence.tier]
    snippet = _preview(record.text, _CITATION_SNIPPET_CHARS)
    access = access_date if access_date is not None else record.fetched_at
    if access.tzinfo is None:
        access = access.replace(tzinfo=UTC)

    return Citation(
        citation_id=citation_id,
        engagement_id=engagement_id,
        client_id=client_id,
        url=record.canonical_url,
        title=title,
        access_date=access,
        source_type=source_type,
        quality_score=quality_score,
        content_snippet=snippet,
        content_hash=record.content_hash,
        found_by_agents=[agent_id],
    )


class EvidenceContextProvider:
    """Expose Lane E parsed passages to research agents.

    The provider is constructed with a collection of
    ``EvidencePrepRecord`` instances (typically the full normalized
    output Lane E produced for an engagement). It is read-only after
    construction; callers that need a different record set build a
    fresh provider.

    Selection contract:

    * ``records_for_task`` returns the relevant records in the order
      they were supplied, deduplicated by ``record_id``. When the
      provider was constructed with a ``task_filter`` predicate, only
      records for which it returns True are included.
    * ``max_passages_per_task`` caps the rendered EV table so a flood
      of parsed passages cannot push the synthesis prompt over the
      model's context window. Records past the cap are dropped from
      the table, not from the underlying store.

    Nothing here re-scores or re-chunks records. Parse confidence,
    coverage, source family, and locator are carried forward onto the
    ``Citation`` when the LLM references a passage, so the evaluator's
    confidence logic remains the single source of truth for how
    evidence is weighted.
    """

    def __init__(
        self,
        records: Iterable[EvidencePrepRecord],
        *,
        task_filter: TaskFilter | None = None,
        task_ranker: TaskRanker | None = None,
        max_passages_per_task: int = 20,
    ) -> None:
        if max_passages_per_task < 1:
            raise ValueError(f"max_passages_per_task must be >= 1, got {max_passages_per_task}")

        deduped: dict[str, EvidencePrepRecord] = {}
        for record in records:
            deduped.setdefault(record.record_id, record)
        self._records: tuple[EvidencePrepRecord, ...] = tuple(deduped.values())
        self._task_filter = task_filter
        self._task_ranker = task_ranker
        self._max_per_task = max_passages_per_task

    @property
    def record_count(self) -> int:
        """Number of records held by this provider (post dedup)."""

        return len(self._records)

    def all_records(self) -> list[EvidencePrepRecord]:
        """Return a copy of every record, in construction order."""

        return list(self._records)

    def records_for_task(self, task: ResearchTask) -> list[EvidencePrepRecord]:
        """Return the records that should be visible for ``task``.

        Applies the ``task_filter`` predicate when one was supplied,
        ranks by ``task_ranker`` when one was supplied (most relevant
        first), then caps the result to ``max_passages_per_task``.
        """

        if not self._records:
            return []

        if self._task_filter is None:
            selected = list(self._records)
        else:
            selected = [r for r in self._records if self._task_filter(task, r)]

        if self._task_ranker is not None:
            selected.sort(key=lambda r: self._task_ranker(task, r), reverse=True)

        if len(selected) > self._max_per_task:
            selected = selected[: self._max_per_task]
        return selected

    def build_reference_table(
        self, records: list[EvidencePrepRecord]
    ) -> dict[str, EvidencePrepRecord]:
        """Build the ``EV-NNN -> EvidencePrepRecord`` table for one round.

        Numbering starts at 001 and is stable for the input ordering.
        Returns an empty dict when ``records`` is empty.
        """

        return {f"EV-{i + 1:03d}": record for i, record in enumerate(records)}

    def render_passages_for_prompt(self, table: dict[str, EvidencePrepRecord]) -> str:
        """Render ``table`` as a block the LLM can reference by EV ref.

        Empty table returns an empty string so callers can inline the
        result without conditional concatenation surprises.
        """

        if not table:
            return ""

        lines: list[str] = ["Parsed evidence passages (reference with EV-NNN refs):"]
        for ref, record in table.items():
            title = record.title or record.record_id
            tier = record.parse_confidence.tier.value
            family = record.source_family.value
            locator = _format_locator(record)
            preview = _preview(record.text, _PASSAGE_PREVIEW_CHARS)
            lines.append(
                f"- {ref} | [{family} | parse={tier}] {title} | {record.canonical_url}"
                f' | {locator} | "{preview}"'
            )
        return "\n".join(lines)
