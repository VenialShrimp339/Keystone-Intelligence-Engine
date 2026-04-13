# Backend Truth Matrix Spec

Date: 2026-04-13  
Applies to: Retrieval MVP Lane D backend-reality proof

## Purpose

Define the closed backend truth matrix that every Retrieval MVP Lane D candidate must produce before any backend-reality claim may clear.

Registry presence and tool descriptions are non-evidence. The matrix must describe executable truth, not planned intent.

## Closed Status Vocabulary

Each surface must resolve to exactly one of these statuses:

- `live_provider_authenticated_fetch`
- `replay_authenticated_fetch`
- `discovery_only`
- `stub_fallback`
- `mock_only`
- `bypass_only`
- `blocked_missing_backend`

If a surface cannot be assigned exactly one status, the matrix is open and the candidate cannot clear.

## Required Matrix Columns

Every candidate matrix must include these columns:

- surface
- canonical role
- invocation surface
- tool name
- backend/server
- status
- evidence artifact path
- approved setup artifact
- candidate commit
- candidate parent anchor
- worktree path
- notes

## Surface Closure Rule

At minimum, the matrix must close these rows:

- article fetch
- EDGAR filing fetch
- PDF fetch
- paper fetch
- Exa discovery
- Brave discovery
- `DEEP_RESEARCH=1`
- `MockMCPClient`
- `SimpleMCPClient` stub fallback

The four canonical fetch rows must have at least one live or provider-authenticated probe artifact each, or the candidate must stop in a blocked checkpoint instead of clearing.

## Baseline Matrix At `65a612d`

This baseline matrix exists to stop false overclaim before Lane D opens.

| Surface | Canonical role | Invocation surface | Tool name | Backend/server | Status | Evidence basis | Notes |
|---|---|---|---|---|---|---|---|
| Article fetch | canonical fetch | default governed path | none canonical today | none canonical today | `blocked_missing_backend` | `WORKSTREAM-HANDOFF.md`, `RETRIEVAL-MVP-ARCHITECTURE-MEMO.md` | Query-shaped discovery exists, but no governed full-article fetch surface is load-bearing on the canonical path at `65a612d`. |
| EDGAR filing fetch | canonical fetch | default governed path | `edgar_filings` | `SimpleMCPClient` fallback | `stub_fallback` | `src/keystone/gateway/simple_client.py`, `WORKSTREAM-HANDOFF.md` | Registered surface exists, but the default executable client returns a stub. |
| PDF fetch | canonical fetch | default governed path | none canonical today | none canonical today | `blocked_missing_backend` | `WORKSTREAM-HANDOFF.md`, `MVP-RETRIEVAL-REQUIREMENTS.md` | No gateway-owned raw PDF fetch/persist surface is load-bearing at `65a612d`. |
| Paper fetch | canonical fetch | default governed path | `paper_search` | `SimpleMCPClient` fallback | `stub_fallback` | `src/keystone/gateway/simple_client.py`, `WORKSTREAM-HANDOFF.md` | The default executable path does not provide a real paper fetch backend. |
| Exa discovery | discovery | default governed path | `exa_search` | Exa API | `discovery_only` | `src/keystone/gateway/simple_client.py`, `ARCHITECTURE-DECISIONS.md` | Real backend exists, but it is discovery-only for MVP truth. |
| Brave discovery | discovery | default governed path | `brave_search` | Brave API | `discovery_only` | `src/keystone/gateway/simple_client.py`, `ARCHITECTURE-DECISIONS.md` | Real backend exists, but it is discovery-only for MVP truth. |
| `DEEP_RESEARCH=1` | bypass lane | provider-native deep mode | n/a | provider-native | `bypass_only` | `WORKSTREAM-HANDOFF.md`, `ARCHITECTURE-DECISIONS.md` | May not satisfy canonical Retrieval MVP acceptance. |
| `MockMCPClient` | test/mocked surface | unit tests | varies | mocked | `mock_only` | `tests/unit/test_gateway.py`, `src/keystone/gateway/mcp_gateway.py` | Unit green lights here are not backend-reality proof. |
| Stub fallback | failure/placeholder surface | default governed path | non-Exa/Brave tools | `SimpleMCPClient` stub path | `stub_fallback` | `src/keystone/gateway/simple_client.py` | Successful canonical fetch claims may not rely on this path. |

## Candidate Clearance Rule

A Lane D candidate may clear backend reality only if:

1. every row in the candidate matrix is closed
2. every successful canonical fetch claim points to live or provider-authenticated evidence
3. `MockMCPClient` and stub fallback are explicitly recorded as non-clearing surfaces
4. Exa and Brave remain classified as `discovery_only`
5. any ambiguous or mixed surface causes a blocked checkpoint instead of a soft pass
