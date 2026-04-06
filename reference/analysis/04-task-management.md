# nano-claude-code: Task Management Analysis

**Source:** `reference/nano-claude-code/task/`
**Scope:** Task schema, persistence, dependency graph, and tool interface -- applicable to Keystone's research-task orchestration
**Date:** 2026-04-05

---

## Summary Verdict

The task system is a solid, thread-safe dependency graph implementation built on JSON persistence. Its core value is the bidirectional blocks/blocked_by edge management, which maps directly to Keystone's pipeline stage sequencing. The schema is thin enough to extend without conflict. Primary gaps: no role-based field access, no priority ordering, and sequential numeric IDs are not safe for distributed agents.

---

## Module Map

| File | Lines | Purpose |
|---|---|---|
| `task/types.py` | 93 | TaskStatus enum, Task dataclass, serialization, display helpers |
| `task/store.py` | 200 | Thread-safe JSON store, CRUD, bidirectional dependency management |
| `task/tools.py` | 266 | Claude-facing tool definitions (TaskCreate, TaskUpdate, TaskGet, TaskList) |

---

## 1. Task Schema (`task/types.py`, lines 1-93)

### TaskStatus Enum

```python
# task/types.py
class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
```

Four states. No terminal review state. No notion of "passed evaluation" vs. "completed output generation." ✅ Verified from source.

### Task Dataclass

```python
# task/types.py
@dataclass
class Task:
    id: int
    subject: str
    description: str
    status: TaskStatus
    active_form: str | None
    owner: str | None
    blocks: list[int]           # IDs of tasks this task blocks
    blocked_by: list[int]       # IDs of tasks that must complete first
    metadata: dict              # arbitrary key-value store
    created_at: datetime
    updated_at: datetime
```

Key fields for Keystone: `owner` (agent assignment), `blocks`/`blocked_by` (pipeline dependency graph), `metadata` (extensible custom fields). ✅ Verified from source.

### Display Helpers

```python
# task/types.py: status_icon() and one_line()
# ○ PENDING  ● IN_PROGRESS  ✓ COMPLETED  ✗ CANCELLED
# one_line() shows pending blockers only -- completed blockers are filtered out
```

`one_line()` resolves completed blockers before display. A task with three blockers all marked COMPLETED shows as unblocked. This is correct behavior: the display reflects actionable state, not historical graph topology. 🟡 Inferred to be intentional UX choice; consistent with how dependency UIs generally work.

### Serialization

`to_dict()` / `from_dict()` with explicit status enum handling. Roundtrips cleanly through JSON. No schema versioning -- a silent gap if the schema evolves. ⚠️ Uncertain whether this is a real risk given the project's scope; meaningful risk for Keystone if we extend the schema in production.

---

## 2. Thread-Safe Store (`task/store.py`, lines 1-200)

### Persistence and Locking

```python
# task/store.py
class TaskStore:
    _lock = threading.Lock()
    _tasks: dict[int, Task] | None = None  # lazy-loaded

    def _load(self):
        # Reads .nano_claude/tasks.json on first access
        # Subsequent reads use in-memory cache
```

Lazy loading means zero disk I/O if no task operations are needed in a session. The `_lock` is a standard threading.Lock -- sufficient for a single-process, multi-threaded environment. ✅ Verified: 20 concurrent creates produce unique IDs with no race conditions (per task notes).

### ID Generation

```python
# task/store.py: create_task()
new_id = max(existing_ids) + 1 if existing_ids else 1
```

Sequential integer IDs. Correct for single-process operation. Not safe for distributed agents writing to a shared store simultaneously -- two agents on separate processes could generate the same ID before either commits. ⚠️ Confirmed gap.

### Bidirectional Dependency Management

The most architecturally significant behavior in the module:

```python
# task/store.py: update_task()
# If adding task B to task A's "blocks" list:
#   → Also adds A to task B's "blocked_by" list
# If adding task B to task A's "blocked_by" list:
#   → Also adds B to task A's "blocks" list
# Symmetric removal on delete
```

The graph is always consistent. No dangling edges. The update operation maintains referential integrity without requiring a separate reconciliation pass. ✅ Verified pattern -- this is correct bidirectional graph management.

### Metadata Merge

```python
# task/store.py: update_task()
# metadata update merges at key level
# setting a key to None deletes it
```

Merge semantics (not replace) allow partial updates. Setting a key to `None` removes it. This is the right API for extensible metadata -- callers don't need to send the full metadata dict to add one field. ✅ Verified from source.

### CRUD Surface

| Method | Behavior |
|---|---|
| `create_task()` | Assigns new ID, writes to disk |
| `get_task(id)` | Returns Task or None |
| `list_tasks()` | Returns all tasks, optionally filtered |
| `update_task(id, **fields)` | Partial update with bidirectional dependency sync |
| `delete_task(id)` | Removes from store, cleans dependency edges |
| `clear_all_tasks()` | Full reset (test/debug use) |

`update_task()` accepts `status="deleted"` as an alias for `delete_task()`. This is a convenience for the Claude-facing tool layer. 🟡 Inferred: exists to simplify TaskUpdate tool (one tool for update + delete rather than two separate tools).

---

## 3. Tool Interface (`task/tools.py`, lines 1-266)

Four Claude-facing tools registered via ToolDef:

| Tool | Purpose |
|---|---|
| `TaskCreate` | Creates a new task with optional owner, blockers, metadata |
| `TaskUpdate` | Partial update; `status="deleted"` triggers deletion |
| `TaskGet` | Retrieves a single task by ID |
| `TaskList` | Lists all tasks; resolves completed blockers in display |

`TaskList` resolves completed blockers before returning output -- a task whose all blockers are COMPLETED shows as ready to start. This is the correct behavior for an orchestrator deciding what to dispatch next. ✅ Verified from source.

---

## Keystone Layer Connections

### L0 -- Specification Engine

The TaskStore is the natural home for Keystone's research task queue. L0 decomposes a client question into a RESEARCH.md specification, then materializes that specification as a set of Task objects. Each subtopic becomes a task. The dependency graph encodes the pipeline sequence.

Example mapping for a standard Keystone engagement:

```
Task 1: Generate RESEARCH.md spec          (owner: L0)
Task 2-8: Parallel research subtopics      (owner: L1_agent_{n}, blocked_by: [1])
Task 9: CitationProcessor                  (owner: CitationProcessor, blocked_by: [2,3,4,5,6,7,8])
Task 10: Deliberation                      (owner: L1.5, blocked_by: [9])
Task 11: Content Structuring               (owner: L2, blocked_by: [10])
Task 12: Draft Generation                  (owner: L3, blocked_by: [11])
Task 13: Evaluation                        (owner: L4, blocked_by: [12])
```

The blocks/blocked_by edges enforce pipeline sequencing without any additional coordination layer. The orchestrator polls `list_tasks()`, identifies tasks with all blockers COMPLETED, and dispatches them. ✅ This is a direct structural match to our DPVI pipeline.

### L1 -- Parallel Research Agents

`owner` field maps to agent assignment. Each L1 research agent receives a task ID and claims ownership via `update_task(id, owner="L1_agent_3", status="in_progress")`. The task store acts as a shared coordination surface without requiring direct agent-to-agent communication.

**Isolation note:** Agents should only update their own tasks. The task store has no enforcement of this -- any agent can update any task. Role-based field access control is a gap we must close.

### L4 -- Evaluator

The standard TaskStatus (PENDING, IN_PROGRESS, COMPLETED, CANCELLED) has no state for evaluation outcomes. An L3 agent completing output generation would mark a task COMPLETED, but Keystone needs to distinguish "generation done, pending evaluation" from "passed evaluation." The Evaluator must be the only agent authorized to set a task to a "passed" state.

**Required extension:** Add `EVALUATING` and `REJECTED` to TaskStatus. Add `passes` field (int, default 0) that only the Evaluator role can increment. TaskStore.update_task() should enforce: if `status=EVALUATING`, caller must have role `evaluator`.

### META -- Trajectory Storage

`metadata` dict can carry trajectory fields without schema changes:

```python
metadata = {
    "task_type": "estimative",              # or "current"
    "anti_confirmatory_framing": True,
    "assigned_tools": ["exa", "firecrawl"],
    "tool_calls_count": 23,
    "latency_ms": 4200,
    "observation_ids": ["obs_42", "obs_17"] # links to Observation Library
}
```

This gives META layer access to per-task execution data without requiring a separate trajectory table -- at least for early development.

---

## Gap Analysis

| Gap | Severity | Fix |
|---|---|---|
| No role-based field access | HIGH -- Evaluator exclusivity requires it | Add `role` param to `update_task()`; enforce in store |
| No `passes` field | HIGH -- Core to L4 integration | Add to Task dataclass with write-protect logic |
| Sequential integer IDs | HIGH for distributed agents | Replace with UUID4 |
| No priority field | MEDIUM -- Needed for task ordering in large engagements | Add `priority: int` to Task dataclass (default 0) |
| No schema versioning | LOW for now | Add `schema_version` to tasks.json header |
| Threading.Lock scope is single-process | MEDIUM for multi-process | Replace with PostgreSQL advisory locks or Redis distributed lock |

---

## Verdict Summary

| Component | Source | Verdict | Keystone Layer |
|---|---|---|---|
| Task dataclass (blocks/blocked_by) | `task/types.py` | ADOPT -- extend with passes, priority, role fields | L0, L1, L4 |
| Bidirectional dependency management | `task/store.py` | ADOPT -- exactly the pipeline sequencing pattern | L0, L1, L1.5 |
| Thread-safe JSON store | `task/store.py` | ADAPT -- replace with PostgreSQL for durability; keep API shape | All layers |
| Metadata merge semantics | `task/store.py` | ADOPT -- enables trajectory fields without schema changes | META |
| TaskStatus enum | `task/types.py` | ADAPT -- add EVALUATING and REJECTED states | L4 |
| Claude-facing tool definitions | `task/tools.py` | ADOPT as pattern -- rewrite for Keystone agent roles | L0, L1 |
| Sequential numeric IDs | `task/store.py` | SKIP -- use UUID4 for distributed safety | All layers |
| Status icon display | `task/types.py` | ADOPT for monitoring/debugging dashboards | META |
| `status="deleted"` alias | `task/tools.py` | SKIP -- separate Update and Delete is cleaner at Keystone scale | L0 |
