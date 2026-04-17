# Handover

Last updated: 2026-04-17
Session: Lane E -> research pipeline bridge

## What Changed

- Added the Lane E -> L1 research bridge under `src/keystone/research/evidence_context.py` (1 new file, 277 lines) and `tests/unit/research/test_evidence_context.py` (31 new tests).
- Extended `ResearchAgent` (shallow + deep modes) and `AgentPool` to accept an optional `EvidenceContextProvider`.
- 913 unit tests pass (was 882; +31 new). Full suite runs in ~7.5s. No regressions.
- `ruff check` / `mypy --strict` are clean on the new `evidence_context.py`; pre-existing ruff (30) / mypy (14) counts in `src/keystone/research/` are unchanged.

## Bridge Components

| File | Role |
|---|---|
| `src/keystone/research/evidence_context.py` | `EvidenceContextProvider` (holds records, `records_for_task`, `build_reference_table`, `render_passages_for_prompt`). `evidence_to_citation()` free function maps `EvidencePrepRecord` -> `Citation`. `infer_source_type()` URL-first + `SourceFamily` fallback. |
| `src/keystone/research/research_agent.py` | New `evidence_provider` kwarg. `_prepare_evidence_context` builds the task EV table once; shallow rounds render `EV-NNN` alongside `SRC-NNN`; `_attach_citations_from_refs` lazy-mints Citations from evidence table (shared agent citation counter). New `SourceFound`/`CitationExtracted` events fire per newly-resolved EV ref. Deep-mode prompt gets a read-only "parsed evidence" block. |
| `src/keystone/research/agent_pool.py` | New `evidence_provider` kwarg, propagated into each `ResearchAgent`. |
| `src/keystone/research/__init__.py` | Exports `EvidenceContextProvider`, `evidence_to_citation`, `infer_source_type`, `TaskFilter`. |

## Design Choices

- **Bridge, not a new stage.** No new pipeline component, no orchestrator changes, no gateway changes. Evidence records are an additional context source for existing agents; the citation/dedup/evaluator layers handle everything else.
- **EV-NNN references in shallow mode.** Parallel to the existing SRC-NNN table. LLM cites by ref; agent resolves to `Citation` with full Lane E provenance (`content_hash`, `canonical_url`, `source_family`, `parse_confidence.tier` -> quality_score, `fetched_at` -> access_date).
- **Lazy Citation minting + caching.** First `EV-NNN` reference mints a `Citation`; subsequent references return the same cached instance so two claims citing the same record share one citation and one `SourceFound` event.
- **Deep-mode: read-only background.** Deep mode uses a single `claude -p` call with its own JSON output format (`sources` arrays with URLs). Evidence passages appear as a background section so the LLM can cite them via URL, but we do not enforce EV-NNN in deep output.
- **Selection stays pluggable.** Default provider returns all records for every task. `task_filter` predicate + `max_passages_per_task` cap give topic-match / context-budget control without the bridge growing a DSL.
- **Provenance carried forward.** Citation minted from a record preserves SHA-256, canonical URL, fetched_at, and source family so CitationProcessor's dedup/corroboration still works on Lane E-sourced citations.
- **Source-type inference is URL-first, family fallback.** Mirrors the existing `_SOURCE_TYPE_PATTERNS` in `research_agent.py` so parsed evidence and search-tool citations classify the same URL the same way.

## Key Commands

```bash
source .venv/bin/activate
pytest tests/unit/research/test_evidence_context.py -q   # 31 new bridge tests
pytest tests/unit/research/ -q                           # 113 tests (was 82)
pytest tests/unit/ -q                                    # 913 tests (was 882)
ruff check src/keystone/research/evidence_context.py tests/unit/research/test_evidence_context.py
mypy src/keystone/research/evidence_context.py           # clean
```

## Integration Shape (how to use this)

```python
from keystone.research import AgentPool, EvidenceContextProvider
from keystone.retrieval import ArtifactLoader, ArticleParser, EvidenceNormalizer

# After Lane E runs:
records = normalizer.normalize_many([(art, parsed) for art, parsed in pairs])
provider = EvidenceContextProvider(records, max_passages_per_task=20)

pool = AgentPool(
    llm=llm,
    gateway=gateway,
    evidence_provider=provider,
)
results = await pool.execute_all(assignments)
```

## Gotchas

- `_attach_citations_from_refs` signature changed: now returns `(claims, newly_minted_ev_citations)` and takes `engagement_id`/`client_id`/`agent_id` kwargs. Only called from within `_execute_shallow`; no public API break.
- Shared citation counter between SRC and EV refs. `_citation_counter` increments for every EV that actually gets cited (not for every record in the table). Uncited records do not produce Citations.
- `sources_consulted` now includes one entry per distinct Lane E record a claim cites (`tool: "lane_e_evidence"` source entries). Numbers will rise when Lane E output is piped in.
- Lane E tests and Lane H are untouched.

## Next Steps

- Orchestrator wiring: have the pipeline pass a provider into `AgentPool` (needs decisions about when Lane E runs relative to task dispatch).
- Task-aware selection: replace the default "all records" behavior with topic or category filtering once a signal is available (e.g. `ResearchTask.required_sources` intersect with `source_family`).
- Deep-mode EV-ref enforcement: only useful if we want deep-mode Citations to include the Lane E SHA-256 and locator. Requires output-format migration.
- Still open from prior session: fix stale import in `tests/integration/test_evaluator_live.py`. Not blocking.

## What Did Not Change

- No modifications to Lane E (`src/keystone/retrieval/`).
- No changes to orchestrator, deliberation, evaluator, citation processor, gateway, or renderer.
- No new dependencies.
