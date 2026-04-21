# GAP-17: Checkpoint/Resume Design

**Status:** Design  
**Priority:** P2 (robustness, not urgent)  
**Prerequisite for:** UI pause/resume (UI-ARCHITECTURE.md v0.4)  
**Date:** 2026-04-21

## Problem

`Pipeline.run_with_events` (`orchestrator.py:350`) is a single async generator.
All state lives in local variables. If the process crashes after L1 completes
(a 20+ minute deep-research run), the entire pipeline restarts from L0. There
is no intermediate persistence, no resume, no checkpoint.

This also blocks the UI's pause/resume feature: `ReviewGateModified` currently
halts the run because there is no mechanism to apply modifications and re-enter
the pipeline at the correct stage.

---

## 1. Stage Boundary Inventory

### Stage 1 — L0 Specification (`orchestrator.py:372–392`)

| Variable | Type | Serializable | Notes |
|---|---|---|---|
| `spec` | `EngagementSpec` | Yes | `model_dump_json()` round-trips. Inner `ResearchSpec` is `frozen=True` (mutation constraint, not a serialization issue). `issue_tree: dict[str, Any]` must contain only JSON-native values. |
| `eid` | `str` | Yes | Extracted from `spec.research_spec.engagement_id`. |
| `policy` | `ProfileExecutionPolicy` | No | Plain class. Reconstruct from `spec.research_spec.effective_pipeline_profile` + `pipeline_config.l5_low_agreement_threshold`. |
| `governance` | `GovernanceState` | Yes | Pydantic `BaseModel` (`governance/models.py:51`). Fields: `profile`, `degraded`, `halted`, `flags: list[QualityFlag]`, `task_outcomes: dict[str, TaskOutcome]`. All serializable. |

Side-effect: `c.deliberation._effective_pipeline_profile` is patched at L383.
Replayed on resume by passing `spec` to `_build_components()` augmented flow.

### Stage 1b — Retrieval Wiring (`orchestrator.py:394–404`)

No data artifact. The `RetrievalService` is ephemeral — registered on `self._gateway`
and reconstructed on resume via `_wire_retrieval()`. Not checkpointed.

### Stage 2 — L1 Research (`orchestrator.py:406–467`)

| Variable | Type | Serializable | Notes |
|---|---|---|---|
| `findings` | `list[StructuredFinding]` | Yes | Pre-canonical at this point. Overwritten at Stage 3. |
| `events_by_agent` | `dict[str, list[AnyPipelineEvent]]` | Yes* | Not a Pydantic model. Serialize via `envelope_from_event` discriminator pattern (`run_store.py:388`): `{"agent_id": [{"event_type": class_name, **model_dump(mode="json")}]}`. Deserialize via `_CLASS_BY_NAME` lookup from `events.py` union members. |
| `agent_by_task` | `dict[str, AgentInstance]` | Yes | `AgentInstance` is Pydantic. Serialize as `{task_id: agent.model_dump(mode="json")}`. |
| `governance` | `GovernanceState` | Yes | Updated with `record_research_outcome`, `flag_cost_ceiling`, `flag_tool_dead_letter` per task. |

### Stage 3 — CitationProcessor (`orchestrator.py:469–479`)

| Variable | Type | Serializable | Notes |
|---|---|---|---|
| `manifest` | `CitationManifest` | Yes | `Citation` validators (id format, hash format) fire on deserialization — valid data round-trips cleanly. |
| `findings` | `list[StructuredFinding]` | Yes | **REASSIGNED** to `cit_result.canonicalized_findings`. Post-Stage-3, all `citation_ids` are `CAN-*` canonical IDs. |

**Design decision: Stage 2 and Stage 3 are grouped into a single `POST_L1_CITPROC` checkpoint.** Rationale: `findings` is rewritten at the Stage 3 boundary. A checkpoint between Stages 2 and 3 would store pre-canonical findings that must still go through CitationProcessor. Grouping avoids a half-consistent state. If a crash occurs anywhere during L1 or CitProc, the entire L1+CitProc unit reruns from the `POST_SPEC` checkpoint. CitProc is pure Python (no LLM calls), so the rerun cost is dominated by L1.

### Stage 4 — L1.5 Deliberation (`orchestrator.py:481–491`)

| Variable | Type | Serializable | Notes |
|---|---|---|---|
| `confidence_map` | `ConfidenceMap` | Yes | `models/confidence.py`. Two `@property` fields (`total_claims`, `tiers_populated`) are computed on access, not serialized. Nests `DiscoUQFeatures`, `ACHDiagnosticity`, `ACHMatrix` — all clean. |

### Stage 5 — L2 Content Structuring (`orchestrator.py:493–538`)

| Variable | Type | Serializable | Notes |
|---|---|---|---|
| `outline` | `StructuredOutline` | Yes | `models/structuring.py`. Nests `StructuredSection` → `OutlineItem`. |
| `eval_tasks` | `list[ResearchTask]` | Yes | `ResearchTask` is Pydantic with `frozen=False`. Filtered from `spec.task_decomposition.tasks` by `governance.task_outcomes[task.id].renderable`, optionally capped by `_max_eval_tasks`. |

**Hidden state inside `ContentStructurer` (`structuring/content_structuring.py:82–88`):**

| Attribute | Type | Serializable | Notes |
|---|---|---|---|
| `_section_texts` | `dict[str, str]` | Yes | Per-task section text produced during `structure()`. Consumed in Stage 6 via `get_task_section_text(task.id)`. |
| `_sprint_contracts` | `dict[str, SprintContract]` | Yes | Per-task sprint contracts. `SprintContract` is Pydantic. `dimension_emphasis: dict[RubricDimension, float]` uses StrEnum keys (round-trips via Pydantic v2 coercion). |
| `_fallback_task_ids` | `set[str]` | Yes | Task IDs whose contract came from fallback path. Serialized as `list[str]`. |
| `_outline` | `StructuredOutline \| None` | Yes | Same as `outline` above. |

A fresh `ContentStructurer` on resume has empty dicts. These must be populated
directly from checkpoint data before Stage 6 runs.

### Stage 6 — L4 Evaluation (`orchestrator.py:540–612`)

| Variable | Type | Serializable | Notes |
|---|---|---|---|
| `evaluation_results` | `list[EvaluationResult]` | Yes | `models/evaluation.py`. Nests Layer1–5 results. `evaluated_at: datetime` serialized as ISO 8601. |
| `governance` | `GovernanceState` | Yes | Updated with `record_evaluation_outcome` per task, `evaluate_coverage` after loop. |

Per-task `Evaluator` instances are constructed and consumed within the loop — no cross-task state.

### Stage 7 — Render (`orchestrator.py:614–670`)

Output: `PipelineResult` (Pydantic, `orchestrator.py:80`). Fully serializable —
confirmed by `_result_to_dto` calling `model_dump(mode="json")`.

Not checkpointed. Render is a pure synchronous function. Rerun cost is negligible.

### Stage 8 — Write-back (`orchestrator.py:672–675`)

Persists to `ObservationStore`. Uses `INSERT OR REPLACE` — idempotent on rerun.

Not checkpointed.

### Non-serializable infrastructure (must be re-provided on resume)

| Object | Location | Role |
|---|---|---|
| `_llm_factory` | `Pipeline.__init__` | Resolves LLM callables per tier/layer. Holds `AppConfig`, semaphores, HTTP session pool. |
| `_gateway` | `Pipeline.__init__` | MCP tool execution. Holds `ToolAuthorizer`, `InMemoryRateLimiter`, `CircuitBreaker`. |
| `_db_session_factory` | `Pipeline.__init__` | Database session factory for HITL gates and ObservationStore. |
| `_retrieval_service_factory` | `Pipeline.__init__` | Builds per-engagement `RetrievalService`. |

These are constructor parameters. A resuming `Pipeline` is constructed with the
same four objects, identically to how a fresh `Pipeline` is built. The checkpoint
stores only serializable stage data, never infrastructure.

---

## 2. Checkpoint Storage

### Technology

aiosqlite — already a project dependency, used by `ObservationStore` (`observation/store.py`)
and `HITLService`. Follow the identical pattern: `__init__(db_path)`,
`async initialize()`, `async close()`, `_conn()` guard.

### Schema

```sql
CREATE TABLE IF NOT EXISTS checkpoints (
    engagement_id  TEXT    NOT NULL,
    stage_name     TEXT    NOT NULL,
    written_at     TEXT    NOT NULL,   -- ISO 8601
    schema_version INTEGER NOT NULL DEFAULT 1,
    payload        TEXT    NOT NULL,   -- JSON blob
    PRIMARY KEY (engagement_id, stage_name)
);
CREATE INDEX IF NOT EXISTS idx_chk_eid
    ON checkpoints(engagement_id);
CREATE INDEX IF NOT EXISTS idx_chk_written
    ON checkpoints(written_at);
```

### Key structure

`(engagement_id, stage_name)` composite primary key. Named stages (`POST_SPEC`,
`POST_L1_CITPROC`, etc.) are self-documenting in SQL queries and debug inspection.
`INSERT OR REPLACE` handles idempotency: if a stage reruns on resume, the existing
checkpoint row is silently overwritten.

### Payload format

A single `TEXT` column containing a JSON object. Top-level keys vary by stage
(see Section 3). Schema validation happens at read time via `model_validate_json()`
on each sub-field. This avoids schema migrations as checkpoint contents evolve —
new fields are added to the JSON, old checkpoints that lack them are handled
via `model_validate(..., strict=False)` or explicit defaults during deserialization.

### Retention

Checkpoints for completed runs (where `PipelineResult` was successfully produced)
are eligible for deletion immediately — the result is the durable artifact.

For incomplete runs:
- Default TTL: 7 days from `written_at`.
- Cleanup: `DELETE FROM checkpoints WHERE written_at < ?` via a periodic call in
  the server startup or a dedicated maintenance task.
- Configurable via `PipelineConfig.checkpoint_retention_days`.

---

## 3. Checkpoint Write Points

### Checkpoint sequence

| # | Name | Written after line | Contains |
|---|---|---|---|
| 1 | `POST_SPEC` | `orchestrator.py:392` | `spec`, `governance` |
| 2 | `POST_L1_CITPROC` | `orchestrator.py:479` | `findings` (canonical), `manifest`, `events_by_agent`, `agent_by_task`, `governance` |
| 3 | `POST_DELIBERATION` | `orchestrator.py:491` | `confidence_map`, `governance` |
| 4 | `POST_STRUCTURING` | `orchestrator.py:538` | `outline`, `eval_tasks`, `section_texts`, `sprint_contracts`, `fallback_task_ids`, `governance` |
| 5 | `POST_EVALUATION` | `orchestrator.py:612` | `evaluation_results`, `governance` |

### Write mechanics

All writes are `async`. Gated on `self._checkpoint_store is not None`:

```python
# After Stage 1 (line 392):
if self._checkpoint_store is not None:
    await self._checkpoint_store.save(
        eid, "POST_SPEC",
        _serialize_post_spec(spec, governance),
    )
```

**Fire-and-log pattern.** Checkpoint write failure must never crash the pipeline:

```python
async def save(self, engagement_id: str, stage_name: str, payload: dict) -> None:
    try:
        await self._conn().execute(
            "INSERT OR REPLACE INTO checkpoints ..."
        )
        await self._conn().commit()
    except Exception:
        logger.warning(
            "Checkpoint write failed for %s/%s — run continues without checkpoint",
            engagement_id, stage_name, exc_info=True,
        )
```

### Serialization functions (per checkpoint)

**`POST_SPEC`:**
```python
{
    "spec": spec.model_dump_json(),
    "governance": governance.model_dump_json(),
}
```

**`POST_L1_CITPROC`:**
```python
{
    "findings": [f.model_dump_json() for f in findings],
    "manifest": manifest.model_dump_json(),
    "events_by_agent": _serialize_events_by_agent(events_by_agent),
    "agent_by_task": {tid: a.model_dump_json() for tid, a in agent_by_task.items()},
    "governance": governance.model_dump_json(),
}
```

Where `_serialize_events_by_agent` produces:
```json
{
    "<agent_id>": [
        {"event_type": "SourceFound", "event_id": "...", ...},
        {"event_type": "CitationExtracted", ...}
    ]
}
```

Using the same `event.__class__.__name__` + `model_dump(mode="json")` pattern
as `envelope_from_event` in `run_store.py:388`.

**`POST_DELIBERATION`:**
```python
{
    "confidence_map": confidence_map.model_dump_json(),
    "governance": governance.model_dump_json(),
}
```

**`POST_STRUCTURING`:**
```python
{
    "outline": outline.model_dump_json(),
    "eval_tasks": [t.model_dump_json() for t in eval_tasks],
    "section_texts": content_structurer._section_texts,  # dict[str, str]
    "sprint_contracts": {
        tid: c.model_dump_json()
        for tid, c in content_structurer._sprint_contracts.items()
    },
    "fallback_task_ids": sorted(content_structurer.get_fallback_task_ids()),
    "governance": governance.model_dump_json(),
}
```

**`POST_EVALUATION`:**
```python
{
    "evaluation_results": [r.model_dump_json() for r in evaluation_results],
    "governance": governance.model_dump_json(),
}
```

### Accessing `ContentStructurer` internals

Stage 5 checkpoint reads `_section_texts`, `_sprint_contracts`, and calls
`get_fallback_task_ids()` (public method). The first two are private attributes.
Options:

1. **Add public read-only accessors** (preferred): `get_section_texts() -> dict[str, str]`
   and `get_sprint_contracts_map() -> dict[str, SprintContract]`. The class already
   has `get_sprint_contracts() -> list[SprintContract]` but not the task-keyed dict form.
2. **Access `_` attributes directly from orchestrator** — acceptable given the
   orchestrator already accesses `c.deliberation._effective_pipeline_profile`
   (line 383), establishing precedent for reaching into component internals.

Recommendation: option 1 for cleanliness, with option 2 as acceptable fallback.

---

## 4. Resume Mechanism

### Entry point

```python
async def resume_with_events(
    self,
    engagement_id: str,
    question: str,
    client_id: str,
    client_context: str | None = None,
) -> AsyncIterator[AnyPipelineEvent]:
```

Same return type as `run_with_events`. Requires `self._checkpoint_store` to be
set (constructor parameter). Raises `ValueError` if no checkpoints exist for the
engagement.

### Resume flow

**Step 1: Load checkpoints.**
```python
checkpoints = await self._checkpoint_store.load(engagement_id)
# Returns: {"POST_SPEC": {...}, "POST_L1_CITPROC": {...}, ...}
```

**Step 2: Determine resume point.**
```python
STAGE_ORDER = [
    "POST_SPEC", "POST_L1_CITPROC", "POST_DELIBERATION",
    "POST_STRUCTURING", "POST_EVALUATION",
]
last_completed = max(
    (s for s in STAGE_ORDER if s in checkpoints),
    key=STAGE_ORDER.index,
)
```

**Step 3: Deserialize boundary variables.**

All variables present in `checkpoints[last_completed]` and earlier checkpoints
are deserialized. Variables for stages not yet completed remain uninitialized.

Cumulative deserialization: each checkpoint carries only its own stage's output
plus `governance`. Earlier-stage artifacts (like `spec`, `findings`) are loaded
from their respective checkpoint rows.

Example: resuming from `POST_DELIBERATION` loads:
- From `POST_SPEC`: `spec`
- From `POST_L1_CITPROC`: `findings`, `manifest`, `events_by_agent`, `agent_by_task`
- From `POST_DELIBERATION`: `confidence_map`, `governance`

**Step 4: Reconstruct non-serializable state.**

```python
c = self._build_components()

# Patch deliberation profile (mirrors orchestrator.py:383)
c.deliberation._effective_pipeline_profile = (
    spec.research_spec.effective_pipeline_profile
)

# Reconstruct policy (mirrors orchestrator.py:384–387)
policy = ProfileExecutionPolicy(
    spec.research_spec.effective_pipeline_profile,
    low_agreement_threshold=self._pipeline_config.l5_low_agreement_threshold,
)

# Governance is deserialized from checkpoint, not reconstructed
# (it carries accumulated task outcomes from prior stages)
```

**Step 5: Populate `ContentStructurer` if resuming at Stage 6+.**

If `last_completed` is `POST_STRUCTURING` or later:
```python
c.content_structurer._outline = StructuredOutline.model_validate_json(
    checkpoints["POST_STRUCTURING"]["outline"]
)
c.content_structurer._section_texts = checkpoints["POST_STRUCTURING"]["section_texts"]
c.content_structurer._sprint_contracts = {
    tid: SprintContract.model_validate_json(v)
    for tid, v in checkpoints["POST_STRUCTURING"]["sprint_contracts"].items()
}
c.content_structurer._fallback_task_ids = set(
    checkpoints["POST_STRUCTURING"]["fallback_task_ids"]
)
```

**Step 6: Wire retrieval (unconditional).**

`_wire_retrieval()` is always called. It is idempotent and fast when no
`evidence_records` are present. It registers tool handlers on `self._gateway`.

**Step 7: Execute remaining stages via guard chain.**

```python
def _should_run(stage: str, last_completed: str) -> bool:
    return STAGE_ORDER.index(stage) > STAGE_ORDER.index(last_completed)
```

The orchestrator code path proceeds through its normal stage sequence, but each
stage is wrapped:

```python
if _should_run("POST_SPEC", last_completed):
    # Stage 1: L0 Specification
    async for event in c.spec_engine.generate_spec(...):
        yield event
    spec = await c.spec_engine.get_spec()
    ...

if _should_run("POST_L1_CITPROC", last_completed):
    # Stage 2+3: L1 Research + CitationProcessor
    ...

# etc.
```

Stages before and including `last_completed` are skipped entirely — no events
emitted, no computation, no LLM calls.

### Alternative considered: refactoring into callable stages

Extracting each stage into a named coroutine and iterating a stage list would be
cleaner but requires restructuring the 300-line `run_with_events` body. Each stage
freely reads local variables assigned by prior stages; extracting them means either
passing 10+ parameters per stage or introducing a `RunState` context object. That
is a significant refactor with risk of breaking existing tests. The guard-chain
approach is additive and leaves `run_with_events` untouched.

This refactoring may be warranted later but is not necessary for the checkpoint
feature.

---

## 5. Interaction with the UI

### Two distinct resume scenarios

**Crash-resume (automatic):**
1. Pipeline process dies mid-run (OOM, host restart, unhandled exception).
2. Server restarts and queries `RunStore` for runs with `status = "failed"`.
3. For each failed run, server checks `CheckpointStore.load(engagement_id)`.
4. If checkpoints exist, the run is marked `resumable` in the `RunStore`.
5. Server (or operator) triggers `Pipeline.resume_with_events(engagement_id, ...)`.
6. Events stream from the resumed stage forward. The UI receives them via WebSocket.

**User-pause-resume (intentional):**
1. HITL gate fires `ReviewGateCreated` at spec or deliberation stage.
2. Server marks run as `PAUSED` in `RunStore`, records `resume_phase`.
3. User reviews artifacts in the HITL modal (UI-ARCHITECTURE.md lines 320–357).
4. User submits decision:
   - **Approve**: server calls `resume_with_events` from the gate's checkpoint.
   - **Modify**: (requires GAP-04 Phase 2) modifications are applied to the
     checkpointed data, then `resume_with_events` is called with the modified state.
   - **Reject**: run transitions to `FAILED`. Checkpoints preserved for audit.

### How `RunStore` determines resumability

A run is resumable when:
- `status` is `"failed"` or `"paused"`, AND
- `CheckpointStore.load(engagement_id)` returns at least one checkpoint row.

A run is NOT resumable when:
- `status` is `"complete"` (result already exists), OR
- No checkpoints exist (nothing to resume from — must restart), OR
- Checkpoint `schema_version` exceeds the current code's supported version.

### Event stream behavior on resume

The pipeline emits **fresh events from the resumed stage only**. It does not
replay events from completed stages.

Prior-stage events are already stored in `RunStore.events` from the original run.
The UI retrieves them via `GET /api/runs/{id}/events`. On WebSocket reconnect,
the `RunSnapshotMessage` includes `recent_events` from the stored history.

This keeps the pipeline as a pure computation generator and the server as the
durability boundary. No new pipeline-to-server coupling is introduced.

### Server-layer integration point

`resume_controller.py` (named in UI-ARCHITECTURE.md line 1115, not yet built)
would implement:

```python
class ResumeController:
    async def attempt_resume(self, run_id: str) -> bool:
        """Check if a run is resumable and trigger resume if so."""

    async def resume_run(self, run_id: str) -> None:
        """Load checkpoints, construct Pipeline, call resume_with_events."""
```

The `PipelineRunner` gains a `resume()` method that mirrors `start_run()` but
calls `pipeline.resume_with_events()` instead of `pipeline.run_with_events()`.

---

## 6. What NOT to Checkpoint

### In-flight tool calls

Both Claude Code and OpenClaw struggle with in-flight tool calls at process
boundaries (DR report section 4; Claude Code issue #3003; OpenClaw issue #62442).
The core problem: a tool call issued to an LLM but not yet returned cannot be
serialized without also serializing the HTTP connection, the pending response
buffer, and the LLM's internal state.

**Decision: checkpoints fire at stage BOUNDARIES only, never mid-stage.**

A crash during L1 (mid-agent research) means L1 reruns entirely from the
`POST_SPEC` checkpoint. A crash during L4 evaluation (mid-task loop) means L4
reruns entirely from the `POST_STRUCTURING` checkpoint.

### LLM call state

LLM calls within a stage (e.g., the 4 parallel analyst methodologies in L1.5)
hold state in the `aiohttp` session, the OpenAI SDK's streaming buffer, and the
model's KV cache. None of this is serializable. Checkpointing only after the
stage fully completes avoids this entirely.

### Irreducible rerun costs

| Crash during | Reruns from | Rerun cost |
|---|---|---|
| L0 Specification | Start | Low (1 LLM call chain) |
| L1 Research | `POST_SPEC` | **High** (15–50 parallel research agents, 20+ min for DEEP) |
| CitationProcessor | `POST_SPEC` | **High** (L1 reruns; CitProc itself is fast) |
| L1.5 Deliberation | `POST_L1_CITPROC` | Medium (4 analyst LLM calls) |
| L2 Structuring | `POST_DELIBERATION` | Medium (1 LLM call per task for sprint contracts) |
| L4 Evaluation | `POST_STRUCTURING` | Medium-high (3-layer eval per task, Flagship LLM) |
| Render | `POST_EVALUATION` | Negligible (pure function) |

The L1 rerun cost is irreducible without intra-stage checkpointing. Intra-stage
checkpointing for L1 would require serializing per-agent state mid-research-loop,
which introduces the in-flight tool call problem. This is explicitly out of scope.

### What about partial L4 evaluation?

L4 processes tasks serially in a for-loop. A crash after evaluating 15 of 20 tasks
loses those 15 results. A future optimization could checkpoint after each task
iteration within Stage 6 (writing `evaluation_results` incrementally). This is
safe because each task's evaluation is independent. However, it adds complexity
(the checkpoint key would need a sub-stage index) and the per-task evaluation
takes ~30 seconds, making the maximum waste ~10 minutes. Deferred to v2.

---

## 7. Schema Versioning and Migration

### Version field

Every checkpoint row includes `schema_version INTEGER NOT NULL DEFAULT 1` as a
column (not buried in the JSON payload). This allows SQL-level filtering:

```sql
SELECT * FROM checkpoints
WHERE engagement_id = ? AND schema_version <= ?
ORDER BY ...
```

### Forward compatibility

When loading a checkpoint:

1. If `schema_version > CURRENT_SCHEMA_VERSION`: raise `CheckpointVersionError`.
   The checkpoint was written by a newer code version and cannot be safely loaded.
2. If `schema_version == CURRENT_SCHEMA_VERSION`: deserialize normally.
3. If `schema_version < CURRENT_SCHEMA_VERSION`: apply migration functions
   in sequence: `migrate_v1_to_v2(payload)`, `migrate_v2_to_v3(payload)`, etc.

### Handling model field changes

Pydantic v2 `model_validate_json()` with default `strict=False` tolerates:
- **Extra fields in the JSON**: silently ignored (unless `model_config` has `extra="forbid"`).
  Only `ResearchSpec` and `Citation` use `frozen=True`; neither uses `extra="forbid"`.
- **Missing optional fields**: filled with their default values.

It does NOT tolerate:
- **Missing required fields without defaults**: raises `ValidationError`.
- **Type changes on existing fields**: raises `ValidationError`.

Mitigation: when adding a required field to a checkpoint model, bump
`CURRENT_SCHEMA_VERSION` and add a migration function that inserts the default
value for the new field into the JSON payload before deserialization.

### Event class evolution

`events_by_agent` serializes event class names as the `event_type` discriminator.
If an event class is renamed or removed, the deserializer's `_CLASS_BY_NAME`
lookup will fail. Mitigation:

```python
_CLASS_ALIASES = {
    "OldEventName": NewEventName,  # Renamed in v2
}
_CLASS_BY_NAME = {
    cls.__name__: cls for cls in _ALL_EVENT_CLASSES
} | _CLASS_ALIASES
```

If an event class is removed entirely, the deserializer should skip the event
(with a warning) rather than failing — `events_by_agent` is consumed for L4
process context metrics, and a missing event degrades the metric slightly but
does not break evaluation.

---

## Appendix A: New Files

| File | Purpose |
|---|---|
| `src/keystone/checkpoint/__init__.py` | Package marker |
| `src/keystone/checkpoint/store.py` | `CheckpointStore` class (aiosqlite) |
| `src/keystone/checkpoint/serialization.py` | `_serialize_events_by_agent`, `_deserialize_events_by_agent`, and per-stage serialize/deserialize helpers |

## Appendix B: Modified Files

| File | Change |
|---|---|
| `src/keystone/pipeline/orchestrator.py` | Add `checkpoint_store` constructor param. Add checkpoint writes after each stage boundary. Add `resume_with_events()` method. |
| `src/keystone/structuring/content_structuring.py` | Add `get_section_texts()` and `get_sprint_contracts_map()` public accessors (optional — can access `_` attrs directly). |
| `src/keystone/server/pipeline_runner.py` | Add `resume()` method that calls `resume_with_events()`. |
| `src/keystone/models/config.py` | Add `checkpoint_retention_days: int = 7` to `PipelineConfig`. |

## Appendix C: External Evidence

- **DR report S2, section 4** (`research/external-sources/openclaw-claude-code/s2-prompt-versioning/deep-research-report.md`): Claude Code's `/rewind` with 4 restore modes; OpenClaw's append-only JSONL with `firstKeptEntryId` compaction boundary. Key architectural lesson: treat checkpoint data as append-only, never mutate earlier entries.
- **GAP-AUDIT.md, GAP-17** (`research/external-sources/nate-jones/2026-02-to-04-audit/GAP-AUDIT.md:282`): "resuming a conversation is not the same thing as resuming a workflow. Without workflow state, your agent can't survive a crash mid-tool-execution without potentially duplicating a write."
- **UI-ARCHITECTURE.md, pause/resume state machine** (`notes/UI-ARCHITECTURE.md:965`): `PAUSED` phase, `resume_phase` server-side, `resume_controller.py` named but not built.
- **DR report validation caveat** (`HANDOFF.md:75`): GitHub issue numbers cited in DR reports are decorative — described behaviors are likely real but numbers may be fabricated.

## Appendix D: `CheckpointStore` API

```python
class CheckpointStore:
    def __init__(self, db_path: str = ":memory:") -> None: ...

    async def initialize(self) -> None:
        """Open database and ensure schema exists."""

    async def close(self) -> None:
        """Close database connection."""

    async def save(
        self,
        engagement_id: str,
        stage_name: str,
        payload: dict[str, Any],
    ) -> None:
        """Write a checkpoint. INSERT OR REPLACE. Fire-and-log on failure."""

    async def load(
        self,
        engagement_id: str,
    ) -> dict[str, dict[str, Any]]:
        """Load all checkpoints for an engagement.
        Returns {stage_name: payload} ordered by stage sequence."""

    async def load_stage(
        self,
        engagement_id: str,
        stage_name: str,
    ) -> dict[str, Any] | None:
        """Load a single stage's checkpoint, or None if not found."""

    async def is_resumable(self, engagement_id: str) -> bool:
        """True if at least one checkpoint exists for this engagement."""

    async def delete(self, engagement_id: str) -> None:
        """Delete all checkpoints for an engagement."""

    async def cleanup_expired(self, max_age_days: int = 7) -> int:
        """Delete checkpoints older than max_age_days. Returns count deleted."""
```
