# Allowed Write Set

Date: 2026-04-13  
Lane: Retrieval Tool-Surface Authority Expansion (`Lane H`)  
Baseline anchor: `65a612dc1400abbedcfbdda1f173cd72a3a90c06`

## Rule

The future Lane H runtime work may touch only the paths listed here.

Any path not listed here is denied.

## Exact Allowed Paths

### Runtime code

- `src/keystone/tool_names.py`
- `src/keystone/gateway/auth.py`
- `src/keystone/gateway/servers.py`
- `src/keystone/gateway/simple_client.py`
- `src/keystone/gateway/tool_registry.py`
- `src/keystone/gateway/mcp_gateway.py`
- `src/keystone/models/tasks.py`
- `src/keystone/models/research.py`
- `src/keystone/specification/prompts/task_generation.md`
- `src/keystone/specification/task_generator.py`

Allowed edit kinds inside those files are limited to:

- canonical tool-definition metadata
- explicit task-assignable versus system-owned tool distinctions
- registration of system-owned `document_fetch`
- article/PDF fetch request and response DTOs
- article/PDF fetch routing, dispatch, and audit
- task-surface leakage prevention
- compatibility-preserving prompt and validation updates that keep `document_fetch` out of `ResearchTask.assigned_tools`

### Tests

- `tests/unit/gateway/test_auth.py`
- `tests/unit/gateway/test_gateway.py`
- `tests/unit/gateway/test_tool_registry.py`
- `tests/unit/specification/test_task_generator.py`
- `tests/unit/test_auth.py`
- `tests/unit/test_gateway.py`
- `tests/unit/test_research_models.py`
- `tests/unit/test_tool_registry.py`

### Review collateral

- `audit/remediation/runs/retrieval-tool-surface/`

### Generated collateral

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`

## Frozen Cross-Cutting Surfaces

### `src/keystone/tool_names.py`

This file may be changed only to express the richer authoritative tool-definition contract and to add `document_fetch` as system-owned and non-task-assignable.

It may not:

- silently widen the task-assignable set beyond the existing seven tools
- change default task-tool behavior for unrelated tools
- redefine search tools as canonical evidence surfaces

### `src/keystone/specification/prompts/task_generation.md`

This file may be changed only to preserve the exact task-assignable list and explicitly forbid system-owned surfaces in `assigned_tools`.

It may not:

- add `document_fetch` to the task-generation tool list
- loosen the "do not invent tools" rule
- rewrite broader decomposition policy

### `src/keystone/specification/task_generator.py` and `src/keystone/models/tasks.py`

These files may be changed only to enforce the assignable/system-owned distinction and validate assigned-tool membership correctly.

They may not:

- alter broader task-priority logic
- alter template matching semantics beyond tool validation
- introduce L1 integration behavior

### `src/keystone/gateway/auth.py` and `src/keystone/gateway/mcp_gateway.py`

These files may be changed only to support an explicit system-owned call path for `document_fetch` and to audit it.

They may not change:

- authorization semantics for unrelated tools
- rate limiting
- circuit breaking
- retry policy
- dead-letter behavior
- HITL behavior
- citation extraction sequencing

### `src/keystone/gateway/servers.py`, `src/keystone/gateway/simple_client.py`, and `src/keystone/gateway/tool_registry.py`

These files may be changed only for:

- `document_fetch` registration
- article/PDF fetch implementation
- canonical URL normalization
- fetch audit fields
- explicit discovery-only preservation for Exa and Brave

They may not:

- change `edgar_filings` semantics
- change `paper_search` or `doi_verify` semantics
- smuggle parser or evidence-bundle logic into the fetch surface

## Explicitly Blocked

The allowed files above do not authorize:

- SEC venue remediation or host-specific workaround logic
- `src/keystone/research/research_agent.py`
- `src/keystone/pipeline/orchestrator.py`
- `src/keystone/citation/**`
- `src/keystone/evaluator/**`
- `src/keystone/knowledge/**`
- `src/keystone/deliberation/**`
- `src/keystone/specification/spec_engine.py`
- benchmark task packs, scoreboard artifacts, or replay-pack data
- `audit/remediation/control-plane/**`
- `audit/remediation/retrieval-mvp/**`
- `audit/remediation/next-wave-setup/**`
- any new runtime path outside the exact list above

## Write-Set Expansion Rule

If a candidate requires touching a blocked path:

1. stop immediately
2. record the blocked path in the run packet
3. return to the controller for a lane-boundary decision

No "small exception" is pre-authorized.

## Review Expectation

The candidate file manifest must classify each touched file as one of:

- expected in-scope file
- expected generated collateral
- blocked scope creep
- unrelated dirty file left untouched

Lane clearance requires an explicit statement that:

- `document_fetch` never became task-assignable
- article/PDF fetch proof is real
- SEC remained separate
