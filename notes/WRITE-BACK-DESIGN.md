# Write-Back Design: GAP-03 + GAP-13 + GAP-05 First Slice

**Branch:** `codex/owner-triage-normalization`
**Scope:** Design the shared write-back pattern, then three connected fixes.

---

## The shared question

The pipeline is read-once, write-never. Every run builds fresh components, produces a `PipelineResult`, returns it, and forgets everything. Three gaps share this root cause:

- **GAP-03** — evidence goes *in* unfiltered (all records, every task)
- **GAP-13** — evaluation outcomes come *out* but are discarded
- **GAP-05** — the Observation Library that would connect outputs back to inputs doesn't exist

One pattern closes all three: **filter what goes in, persist what comes out, and let accumulated outcomes inform future runs.**

---

## 1. Shared write-back pattern

### What gets written

Two categories of data, stored separately because their query patterns differ.

**Category A: Observation records** (structured, SQL-queryable)

One record per evaluated task. Each captures the evaluator's verdict and the governance context around it. This is the first slice of the Observation Library.

| Field | Source | Purpose |
|-------|--------|---------|
| `observation_id` | Minted: `OBS-{eid_short}-{task_short}-{seq}` | Primary key |
| `client_id` | `PipelineResult.client_id` | Client namespacing |
| `engagement_id` | `PipelineResult.engagement_id` | Run traceability |
| `engagement_type` | `spec.research_spec.engagement_type` | Pattern grouping |
| `task_id` | `EvaluationResult.task_id` | Task traceability |
| `type` | `"rejection"` if `not result.passed`, else `"success"` | Observation classification |
| `category` | Derived from failure layer (see below) | Severity tier (1/2/3) |
| `dimension` | Lowest-scoring rubric dimension | What failed or excelled |
| `composite_score` | `EvaluationResult.composite_score` | Numeric outcome |
| `dimension_scores` | JSON of `{dim: score}` | Full rubric snapshot |
| `governance_flags` | Flags that fired for this task | Governance context |
| `recorded_at` | UTC now | Temporal ordering |

Category derivation: `1` (STRUCTURAL) if citation gate failed, `2` (ANALYTICAL) if a Tier 1 floor failed, `3` (JUDGMENT) otherwise. Maps to the existing `ObservationCategory` enum in `models/observations.py`.

**Category B: High-confidence finding claims** (text, vector-searchable)

One chunk per passed `FindingClaim` with `confidence >= 0.8`. Goes into the retrieval store as client-namespaced institutional memory so future agents benefit from accumulated research.

**Deferred to Phase 2.** Reason: `ChunkMetadata` (`retrieval/search/models.py:57`) is frozen with `extra="forbid"` and its fields are Lane-E-specific (`artifact_id`, `canonical_url`, `content_hash`, `source_family`, `locator`, `parse_confidence`). Ingesting pipeline outputs requires extending the metadata model, which is a cross-cutting change to the retrieval stack. Category A (observations) is higher value and independent — start there.

### Where it's stored

**Observations** → new `ObservationStore` backed by aiosqlite. Same `db_session_factory` opt-in pattern the HITL gates use. Separate from the vector store because the access pattern is structured queries (filter by `client_id` + `engagement_type` + `dimension` + `type`), not semantic similarity.

**Schema:**

```sql
CREATE TABLE IF NOT EXISTS observations (
    observation_id  TEXT PRIMARY KEY,
    client_id       TEXT NOT NULL,
    engagement_id   TEXT NOT NULL,
    engagement_type TEXT NOT NULL,
    task_id         TEXT NOT NULL,
    type            TEXT NOT NULL CHECK (type IN ('rejection', 'success')),
    category        INTEGER NOT NULL CHECK (category IN (1, 2, 3)),
    dimension       TEXT NOT NULL,
    composite_score REAL NOT NULL,
    dimension_scores TEXT NOT NULL,  -- JSON
    governance_flags TEXT NOT NULL,  -- JSON list
    recorded_at     TEXT NOT NULL    -- ISO 8601
);
CREATE INDEX IF NOT EXISTS idx_obs_client_type ON observations(client_id, type);
CREATE INDEX IF NOT EXISTS idx_obs_dim ON observations(client_id, dimension, type);
CREATE INDEX IF NOT EXISTS idx_obs_etype ON observations(client_id, engagement_type);
```

### Events emitted

Each ingested observation yields `ObservationRecorded` (already declared in `events.py:432`, never emitted until now).

---

## 2. GAP-03: Evidence filtering

**Current state:** `EvidenceContextProvider.records_for_task(task)` returns all records when `task_filter is None` (`evidence_context.py:235`). Every task sees the same 20 passages regardless of what it's investigating.

**Fix:** Two-stage selection, both deterministic, no API calls.

### Stage 1: Source-family filter

When `task.required_sources` is populated (the field already exists on `ResearchTask` at `tasks.py:99`), exclude records whose `source_family` doesn't match.

Mapping table:

| `required_sources` value | Allowed `SourceFamily` |
|--------------------------|------------------------|
| `"industry_reports"` | `REPORT` |
| `"financial_data"` | `PDF`, `REPORT` |
| `"academic"` | `ARTICLE` (academic URL patterns) |
| `"news"` | `ARTICLE` (news URL patterns) |
| `"government"` | `PDF`, `REPORT` (gov URL patterns) |

When a `required_sources` value has no mapping, or the list is empty, all families pass (backward compat). URL-pattern matching reuses the existing `_URL_PATTERNS` table in `evidence_context.py:54`.

### Stage 2: Relevance ranking

After the source-family filter, rank surviving records by text similarity to `task.description`. Simple token-overlap score (Jaccard index on whitespace-tokenized, lowercased, stopword-removed text). No embeddings, no LLM calls — runs in-process, deterministic, O(n) in record count.

The existing `max_passages_per_task` cap (default 20) then takes the top-ranked subset.

### Implementation

New public function `build_default_task_filter()` in `evidence_context.py` that returns a `TaskFilter` callable. New private function `_relevance_score(task_description, record_text)` for the ranking. The orchestrator passes the filter when constructing `EvidenceContextProvider` in `_build_components`:

```python
evidence_provider = EvidenceContextProvider(
    self._evidence_records,
    task_filter=build_default_task_filter(),
)
```

Existing `EvidenceContextProvider.records_for_task` already supports `task_filter` — no structural change needed there. Add a `sort_key` parameter or sort after filtering before the cap to implement ranking.

---

## 3. GAP-13: Post-run ingest hook

**Current state:** After `PipelineResult` is assembled at `orchestrator.py:647`, `run_with_events` returns. Nothing persists.

**Fix:** New method `Pipeline._write_back_outcomes()`, called after `PipelineResult` is assembled and before the generator exhausts. Gated on `self._observation_store is not None` (same opt-in as retrieval wiring — tests and callers that don't provide a store see zero behavior change).

### Orchestrator integration

```python
# After self._result assignment (~line 659), before run_with_events returns
if self._observation_store is not None:
    async for event in self._write_back_outcomes(
        self._result, spec, governance,
    ):
        yield event
```

### `_write_back_outcomes` logic

For each `EvaluationResult` in `self._result.evaluation_results`:

1. Determine `type` (`"rejection"` / `"success"`) from `result.passed`
2. Determine `category` from failure layer:
   - Citation gate failed → `STRUCTURAL` (1)
   - Any Tier 1 dimension below floor → `ANALYTICAL` (2)
   - Otherwise → `JUDGMENT` (3)
3. Find lowest-scoring dimension for the `dimension` field
4. Build `ObservationEntry` (existing model in `models/observations.py`)
5. Call `self._observation_store.record(entry)` — async, single row INSERT
6. Yield `ObservationRecorded` event

### Constructor change

`Pipeline.__init__` gains `observation_store: ObservationStore | None = None`. When `None`, `_write_back_outcomes` is skipped. No existing tests or callers break.

---

## 4. GAP-05: First slice

**The post-run ingest hook IS the first slice of the Observation Library.** It implements the "Light phase" from the OpenClaw dreaming pattern: raw data capture on every run, no processing, no promotion.

### What's built now (this PR)

- `ObservationStore` — aiosqlite-backed, `record()` + `query_by_client()` + `query_by_dimension()`
- `_write_back_outcomes` in the orchestrator
- `ObservationRecorded` events emitted (first time these fire)
- Data accumulates silently across runs

### What's deferred (future PRs, in order)

| Phase | What | Unblocked by | Maps to |
|-------|------|-------------|---------|
| REM | `ObservationStore.detect_patterns(client_id, dimension, min_count=N)` — find recurring failures | Data accumulation (this PR) | OpenClaw REM phase |
| Pass 3 | `ThreePassEvaluator` queries the store for prior failures matching `engagement_type + dimension`, applies -1 to -3 scoring adjustment | This PR + REM | `three_pass.py:53` stub |
| Deep | `PatternPromoted` / `ConstraintEncoded` events — write validated patterns back into prompt files | Pass 3 + prompt audit (GAP-10) | OpenClaw Deep phase |
| Findings ingest | High-confidence claims → retrieval store as institutional memory | `ChunkMetadata` extension | GAP-13 Category B |

---

## 5. How the three connect

```
                  ┌─────────────────────────────────────┐
                  │        Retrieval Store               │
                  │  (Lane E institutional memory)       │
                  └──────────────┬──────────────────────┘
                                 │
                    GAP-03: filtered by required_sources
                    + relevance ranking, capped at 20
                                 │
                                 ▼
                  ┌─────────────────────────────────────┐
                  │     L1 Research Agents               │
                  └──────────────┬──────────────────────┘
                                 │
                   pipeline evaluates + renders
                                 │
                                 ▼
                  ┌─────────────────────────────────────┐
                  │     GAP-13: _write_back_outcomes     │
                  │     stores evaluation results        │
                  └──────────────┬──────────────────────┘
                                 │
                                 ▼
                  ┌─────────────────────────────────────┐
                  │     GAP-05: ObservationStore         │
                  │     (accumulates across runs)        │
                  └──────────────┬──────────────────────┘
                                 │
                    Future: Pass 3 queries store
                    Future: pattern detection → constraints
                    Future: findings → retrieval store
                                 │
                                 ▼
                         ┌───────┴───────┐
                         │  Next run's   │
                         │  evaluation   │
                         │  is informed  │
                         └───────────────┘
```

The loop: evidence goes in filtered (GAP-03), outcomes come out stored (GAP-13), accumulated outcomes inform future evaluation (Pass 3 via GAP-05), and eventually promoted patterns improve future evidence selection.

---

## File changes summary

| File | Change | Gap |
|------|--------|-----|
| `src/keystone/research/evidence_context.py` | Add `build_default_task_filter()`, `_relevance_score()`, `_resolve_source_families()` | GAP-03 |
| `src/keystone/pipeline/orchestrator.py` | Accept `observation_store`, add `_write_back_outcomes()` post-run hook | GAP-13 |
| New: `src/keystone/observation/__init__.py` | Package init | GAP-05 |
| New: `src/keystone/observation/store.py` | `ObservationStore` with `record()`, `query_by_client()`, `query_by_dimension()` | GAP-05 |
| `tests/unit/research/test_evidence_context.py` | Tests for filter + ranking | GAP-03 |
| New: `tests/unit/observation/test_store.py` | Tests for ObservationStore | GAP-05 |
| `tests/unit/pipeline/test_orchestrator.py` | Test write-back hook fires and skips correctly | GAP-13 |

### Not touched

- `models/observations.py` — existing `ObservationEntry` model is sufficient
- `events.py` — `ObservationRecorded` already declared
- `contracts.py` — `ObservationLibraryContract` stays as Protocol; concrete impl comes in Pass 3 phase
- `evaluator/three_pass.py` — Pass 3 stub remains until the store has accumulated data
