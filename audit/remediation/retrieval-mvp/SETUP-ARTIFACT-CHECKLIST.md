# Setup-Artifact Checklist

Date: 2026-04-13  
Purpose: define the exact contents required in the next controller-approved setup artifact before the first Retrieval MVP runtime lane may open

This checklist is for the future setup checkpoint only. It does not itself authorize runtime work.

## 1. Header And Status Block

- [ ] file lives under `audit/remediation/`, not only under `audit/remediation/retrieval-mvp/`
- [ ] states date, active status, and that the main workspace remains controller/docs only
- [ ] names the authorized lane explicitly, not generically
- [ ] names the runtime truth anchor as `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-4b` at `65a612d`
- [ ] states that the setup artifact is subordinate to `CONTROL-PLANE-STATE.yaml` and `ACTIVE-HANDOFF.md`

## 2. Required Reading Order

- [ ] `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
- [ ] `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
- [ ] Wave 4B clearance packet
- [ ] `audit/remediation/retrieval-mvp/WORKSTREAM-HANDOFF.md`
- [ ] `audit/remediation/retrieval-mvp/MVP-RETRIEVAL-REQUIREMENTS.md`
- [ ] `audit/remediation/retrieval-mvp/ARCHITECTURE-DECISIONS.md`
- [ ] `audit/remediation/retrieval-mvp/RETRIEVAL-MVP-ARCHITECTURE-MEMO.md`
- [ ] `audit/remediation/retrieval-mvp/RETRIEVAL-MVP-SEAM-CONTRACT.md`
- [ ] `audit/remediation/retrieval-mvp/RETRIEVAL-MVP-MIGRATION-CHECKLIST.md`
- [ ] `audit/remediation/retrieval-mvp/BENCHMARK-AND-ACCEPTANCE.md`
- [ ] `audit/remediation/retrieval-mvp/RISK-REGISTER.md`
- [ ] `graphify-out/GRAPH_REPORT.md`

## 3. Activation Block

- [ ] baseline commit is `65a612d`
- [ ] candidate parent anchor is `65a612d`
- [ ] controller branch is named
- [ ] planned implementation branch is named
- [ ] planned worktree path is named
- [ ] lane purpose is named in one sentence
- [ ] main workspace policy is repeated as docs-only

Recommended first-lane values:

- planned branch: `codex/retrieval-mvp-fetch`
- planned worktree: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch`
- lane purpose: gateway-owned governed fetch backends for article, filing, PDF, and paper retrieval

## 4. Current-Code Anchors

- [ ] explains what is true today at `65a612d`
- [ ] states that Exa and Brave are the only real default discovery backends
- [ ] states that `edgar_filings`, `paper_search`, `doi_verify`, `fred_data`, and `finnhub_market` are not all real canonical fetch backends in the default client path
- [ ] states that the current path is query-shaped and snippet-heavy
- [ ] states that `DEEP_RESEARCH=1` is a bypass lane
- [ ] states that retrieval truth claims must anchor to the sibling Wave 4B worktree or `git show 65a612d:...`

## 5. Binding Scope In

- [ ] gateway-owned article fetch is in scope
- [ ] gateway-owned EDGAR filing fetch is in scope
- [ ] gateway-owned PDF fetch and persistence is in scope
- [ ] gateway-owned paper metadata plus full-text or authoritative-abstract fetch is in scope
- [ ] canonical URL normalization and explicit coverage reporting are in scope
- [ ] minimal typed retrieval model additions needed for fetch identity, coverage, and audit are in scope
- [ ] gateway audit extension for fetch activity is in scope
- [ ] tests that make the new fetch seams load-bearing are in scope

## 6. Binding Scope Out

- [ ] deterministic parser lane as a separate major slice is out of scope
- [ ] L1 integration and evidence-bundle synthesis migration are out of scope
- [ ] benchmark execution and acceptance claims are out of scope
- [ ] `DEEP_RESEARCH=1` equivalence claims are out of scope
- [ ] semantic retrieval, embeddings, `pgvector`, BM25, RRF, rerank are out of scope
- [ ] internal and cross-engagement retrieval are out of scope
- [ ] true claim-support verification is out of scope
- [ ] UI work is out of scope
- [ ] retrospective control-plane reconciliation is out of scope

## 7. Exact Allowed Write Set

The setup artifact should name an exact write surface. Recommended first-lane write set:

### Runtime code

- [ ] `src/keystone/gateway/audit_log.py`
- [ ] `src/keystone/gateway/mcp_gateway.py`
- [ ] `src/keystone/gateway/servers.py`
- [ ] `src/keystone/gateway/simple_client.py`
- [ ] `src/keystone/gateway/tool_registry.py`
- [ ] `src/keystone/models/research.py`

Additional fencing required if those files stay allowed:

- [ ] `src/keystone/gateway/mcp_gateway.py` is fenced so the lane may not change authorization, rate-limiter use, circuit-breaker use, retry policy, dead-letter behavior, citation extraction sequencing, or HITL-adjacent control flow
- [ ] `src/keystone/models/research.py` is fenced so only an additive isolated retrieval block may be added, with no changes to existing `ResearchSpec`, `EngagementSpec`, `PipelineProfile`, `StructuredFinding`, or `FindingClaim` semantics, fields, validators, defaults, or behavior
- [ ] `src/keystone/tool_names.py` is explicitly out of scope for Lane D
- [ ] the artifact says plainly that any tool-assignment change through an allowed file counts as blocked L1 integration scope creep
- [ ] the artifact says plainly that any shared research-model behavior change through an allowed file counts as broader runtime scope creep

### Tests

- [ ] `tests/unit/gateway/test_auth.py`
- [ ] `tests/unit/gateway/test_gateway.py`
- [ ] `tests/unit/gateway/test_tool_registry.py`
- [ ] `tests/unit/test_auth.py`
- [ ] `tests/unit/test_audit_log.py`
- [ ] `tests/unit/test_gateway.py`
- [ ] `tests/unit/test_research_models.py`
- [ ] `tests/unit/test_tool_registry.py`

### Generated collateral

- [ ] `graphify-out/GRAPH_REPORT.md`
- [ ] `graphify-out/graph.json`

## 8. Mandatory Pre-Promotion Gate Artifacts

Before the setup artifact may be promoted into live control-plane authority, the package should require docs-only gate artifacts with explicit verdicts for:

- [ ] `Backend Reality Gate`
- [ ] `Tool Contract Gate`
- [ ] `Governance Gate`
- [ ] `Run Contract Gate`
- [ ] `Controller Unlock / Worktree Provenance Gate`

Each gate artifact should record:

- [ ] reviewer
- [ ] reviewed snapshot
- [ ] evidence inputs
- [ ] approved setup artifact path
- [ ] unambiguous `CLEARED` or `BLOCKED` verdict

Naming gates in prose is not enough. Promotion should depend on those gate artifacts existing and clearing.

## 9. Explicit Denylist

- [ ] `src/keystone/research/research_agent.py`
- [ ] `src/keystone/pipeline/orchestrator.py`
- [ ] `src/keystone/evaluator/**`
- [ ] `src/keystone/specification/**`
- [ ] `src/keystone/knowledge/**`
- [ ] `src/keystone/tool_names.py`
- [ ] benchmark task packs and judge-only files
- [ ] retrospective control-plane files
- [ ] unrelated main-workspace dirty files

The setup artifact should say plainly that any widening beyond this surface requires a later controller checkpoint.

## 10. Required Test Matrix

The setup artifact should freeze the minimum enforcing suites for the lane:

- [ ] `tests/unit/gateway/test_auth.py`
- [ ] `tests/unit/gateway/test_gateway.py`
- [ ] `tests/unit/gateway/test_tool_registry.py`
- [ ] `tests/unit/test_auth.py`
- [ ] `tests/unit/test_audit_log.py`
- [ ] `tests/unit/test_gateway.py`
- [ ] `tests/unit/test_research_models.py`
- [ ] `tests/unit/test_tool_registry.py`

If broader suites are run, they are extra coverage, not a replacement for the named matrix.

## 11. Required Runtime Probes

The setup artifact should require named probes for:

- [ ] article fetch returns canonical URL, MIME, hash, and explicit coverage
- [ ] EDGAR fetch returns official filing content, not stub text
- [ ] PDF fetch persists raw bytes with explicit coverage and hash
- [ ] paper fetch returns full text when available, else explicit `abstract_only` or `metadata_only`
- [ ] Exa and Brave remain discovery-only on the canonical path
- [ ] stubbed tool behavior cannot be misreported as canonical backend support
- [ ] fetch activity is gateway-audited

The setup artifact should also state plainly that the unit matrix is not sufficient backend-reality evidence on its own and that successful canonical fetch claims require live or provider-authenticated probe artifacts.

## 12. Worktree Bootstrap Section

- [ ] includes the exact `git worktree add` command
- [ ] roots the worktree from `65a612d`
- [ ] uses a clean dedicated branch
- [ ] states that code edits are forbidden in the main workspace
- [ ] states that the shared venv may be reused by absolute path if needed
- [ ] includes the graphify rebuild command after code-file changes

Recommended bootstrap:

```bash
cd /Users/jackriddle/Desktop/Keystone-Intelligence-Engine
git worktree add -b codex/retrieval-mvp-fetch ../Keystone-Intelligence-Engine-retrieval-fetch 65a612d
cd /Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch
```

Graphify rebuild after code-file changes:

```bash
python3 -c "from graphify.watch import _rebuild_code; from pathlib import Path; _rebuild_code(Path('.'))"
```

## 13. Candidate Artifact Requirements

- [ ] `candidate-<commit>-implementation.md`
- [ ] `candidate-<commit>-file-manifest.md`
- [ ] `candidate-<commit>-backend-truth-matrix.md`
- [ ] `candidate-<commit>-live-fetch-review.md`
- [ ] `candidate-<commit>-adversarial-review.md`
- [ ] `candidate-<commit>-second-opinion.md`
- [ ] `candidate-<commit>-review-synthesis.md`
- [ ] `candidate-<commit>-clearance.md` or blocked checkpoint

The setup artifact should require those artifacts to live under a lane-specific run packet root.

## 14. Reopen And Hard-Stop Triggers

- [ ] any need to widen into parser Lane E
- [ ] any need to widen into L1 integration Lane F
- [ ] any need for new persisted infrastructure outside the named surface
- [ ] any governed/bypass mixing on the canonical lane
- [ ] any benchmark claim before replay and provenance gates are satisfied
- [ ] any write-set expansion without a new controller update
- [ ] any review blocker that cannot be resolved inside the lane scope

## 15. Final Authorization Line

The setup artifact should end with an unambiguous controller line:

- [ ] this file authorizes only the named retrieval runtime lane
- [ ] it does not authorize later retrieval lanes
- [ ] it does not authorize benchmark acceptance claims
- [ ] it does not lift the docs-only rule for the main workspace
