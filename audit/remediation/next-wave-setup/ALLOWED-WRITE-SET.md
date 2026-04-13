# Allowed Write Set

Date: 2026-04-13  
Lane: Retrieval MVP Lane D fetch  
Baseline: `65a612dc1400abbedcfbdda1f173cd72a3a90c06`

## Rule

The future Retrieval MVP Lane D code lane may touch only the paths listed here.

Any path not listed here is denied.

## Exact Allowed Paths

### Runtime code

- `src/keystone/gateway/audit_log.py`
- `src/keystone/gateway/mcp_gateway.py`
- `src/keystone/gateway/servers.py`
- `src/keystone/gateway/simple_client.py`
- `src/keystone/gateway/tool_registry.py`
- `src/keystone/models/research.py`

Allowed edits inside those files are limited to:

- raw fetch transport
- fetch-tool registration and dispatch
- fetch audit fields
- fetch artifact identity metadata
- fetch coverage metadata
- explicit discovery-only treatment for Exa and Brave on the canonical path
- additive isolated retrieval DTOs only if they do not alter existing shared model semantics

## Frozen Cross-Cutting Surfaces

The two cross-cutting files in the allowed set are not open refactor surfaces.

### `src/keystone/gateway/mcp_gateway.py`

This file may be touched only for fetch-local routing or fetch-audit extensions.

It may not change:

- authorization logic or assigned-tool enforcement
- rate-limiter invocation, provider naming, or token-consumption behavior
- circuit-breaker acquisition, state use, or recovery behavior
- retry counts, backoff settings, retry sequencing, or exception policy
- dead-letter append/logging behavior
- citation extraction sequencing
- HITL-adjacent control flow

### `src/keystone/models/research.py`

This file may be touched only if an isolated additive retrieval block is unavoidable for fetch identity, fetch coverage, or fetch audit metadata.

It may not change existing semantics, fields, validators, defaults, or behavior for:

- `ResearchSpec`
- `EngagementSpec`
- `PipelineProfile`
- `StructuredFinding`
- `FindingClaim`

If an implementation task cannot stay inside an isolated additive block, it is broader runtime scope creep and must stop.

## Explicitly Blocked Indirect Scope Creep

The allowed files above do not authorize:

- auth changes
- rate-limiting changes
- circuit-breaker changes
- retry-policy changes
- dead-letter behavior changes
- HITL behavior changes
- parser work
- evidence normalization
- citation locator work
- research-agent call-site changes
- orchestrator call-site changes
- synthesis behavior changes
- schema migration work
- new dependency introduction outside the exact fetch seam
- tool-assignment changes through any allowed file
- shared research-model behavior changes through any allowed file

Tool-assignment changes through allowed files count as blocked L1 integration scope creep.

Shared research-model behavior changes through allowed files count as broader runtime scope creep.

## Tests

- `tests/unit/gateway/test_auth.py`
- `tests/unit/gateway/test_gateway.py`
- `tests/unit/gateway/test_tool_registry.py`
- `tests/unit/test_auth.py`
- `tests/unit/test_audit_log.py`
- `tests/unit/test_gateway.py`
- `tests/unit/test_research_models.py`
- `tests/unit/test_tool_registry.py`

## Review Packet Root

- `audit/remediation/runs/retrieval-mvp-fetch/`

Only the candidate packet family for this lane may be written there.

## Generated Collateral

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`

These collateral files are allowed only when regenerated from code changes inside the approved lane.

## Exact Denylist

The following are explicitly denied:

- every path outside the exact allowed paths above
- any new file outside `audit/remediation/runs/retrieval-mvp-fetch/`
- any edit that changes auth, rate limiting, circuit breaking, retry policy, dead-letter behavior, or HITL behavior
- any edit that changes existing Exa or Brave semantics beyond keeping them discovery-only
- any edit that changes tool assignment, `DEFAULT_TOOLS`, `ALL_TOOLS`, or existing tool semantic groupings
- any edit that changes shared research-model semantics
- `src/keystone/tool_names.py`
- `src/keystone/research/research_agent.py`
- `src/keystone/pipeline/orchestrator.py`
- `src/keystone/evaluator/**`
- `src/keystone/specification/**`
- `src/keystone/knowledge/**`
- `src/keystone/deliberation/**`
- `audit/remediation/control-plane/**`
- `audit/remediation/workstream-retro/**`
- `audit/remediation/retrieval-mvp/**`
- `audit/remediation/next-wave-setup/**`
- benchmark task packs, replay-pack data, judge-only artifacts, and scoreboard inputs
- unrelated dirty files already present in the main workspace

## Write-Set Expansion Rule

If any implementation task requires touching a denied path, stop immediately and return to the control plane.

No "small exception," "one-line fix," or "related cleanup" is pre-authorized.

If a proposed change cannot be described as raw fetch transport, fetch identity, fetch coverage, or fetch audit, it is out of scope for Lane D.

## Review Expectation

The candidate file manifest must classify every touched path as one of:

- expected in-scope file
- legitimate generated collateral
- blocked scope creep
- quarantined unrelated change

The file manifest must also state whether any allowed-file diff changed shared runtime behavior outside raw fetch transport, fetch identity, fetch coverage, or fetch audit.

Lane clearance requires an explicit statement that no unresolved scope creep remains.
