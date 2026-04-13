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
- `src/keystone/tool_names.py`

Allowed edits inside those files are additive-only and limited to:

- fetch-tool registration and dispatch
- fetch audit fields
- fetch artifact identity metadata
- explicit discovery-only treatment for Exa and Brave on the canonical path

The allowed files above do not authorize:

- auth changes
- rate-limiting changes
- circuit-breaker changes
- HITL behavior changes
- parser work
- evidence normalization
- citation locator work
- research-agent call-site changes
- orchestrator call-site changes
- synthesis behavior changes
- schema migration work
- new dependency introduction outside the exact fetch seam

### Tests

- `tests/unit/gateway/test_auth.py`
- `tests/unit/gateway/test_gateway.py`
- `tests/unit/gateway/test_tool_registry.py`
- `tests/unit/test_auth.py`
- `tests/unit/test_audit_log.py`
- `tests/unit/test_gateway.py`
- `tests/unit/test_research_models.py`
- `tests/unit/test_tool_registry.py`

### Review packet root

- `audit/remediation/runs/retrieval-mvp-fetch/`

Only the candidate packet family for this lane may be written there.

### Generated collateral

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`

These collateral files are allowed only when regenerated from code changes inside the approved lane.

## Exact Denylist

The following are explicitly denied:

- every path outside the exact allowed paths above
- any new file outside `audit/remediation/runs/retrieval-mvp-fetch/`
- any edit that changes auth, rate limiting, circuit breaking, or HITL behavior
- any edit that changes existing Exa or Brave semantics beyond keeping them discovery-only
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

Lane clearance requires an explicit statement that no unresolved scope creep remains.
