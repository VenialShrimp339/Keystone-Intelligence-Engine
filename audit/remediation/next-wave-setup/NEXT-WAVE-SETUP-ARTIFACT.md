# Post-Wave-4B Retrieval Fetch Setup Artifact

*Date: 2026-04-13 | Status: controller-authored next-wave setup checkpoint candidate | main workspace stays controller/docs only; any code must run in a clean worktree rooted at cleared Wave 4B baseline `65a612d`*

---

## What This File Is For

This file is the missing post-Wave-4B authority/setup artifact required before any forward code lane may open.

Use it only after reading:

1. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
2. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
3. `audit/remediation/control-plane/RETROSPECTIVE-REVIEW-LEDGER.yaml`
4. `audit/remediation/runs/wave-4b/candidate-65a612d-clearance.md`
5. `audit/remediation/retrieval-mvp/WORKSTREAM-HANDOFF.md`
6. `audit/remediation/retrieval-mvp/RUNTIME-LANE-UNLOCK-MEMO.md`
7. `audit/remediation/retrieval-mvp/SETUP-ARTIFACT-CHECKLIST.md`
8. `audit/remediation/retrieval-mvp/WORKTREE-AND-REVIEW-GATE-CHECKLIST.md`
9. `audit/remediation/retrieval-mvp/IMPLEMENTATION-LANES.md`
10. `audit/remediation/retrieval-mvp/RISK-REGISTER.md`
11. `audit/remediation/project-state-reconcile/EXECUTIVE-RECONCILIATION-SUMMARY.md`
12. `graphify-out/GRAPH_REPORT.md`

This file defines the only narrowly bounded forward lane this package is willing to unlock: Retrieval MVP Lane D fetch.

This file does not:

- authorize Wave 5
- authorize calibration
- authorize parser Lane E
- authorize L1 integration Lane F
- authorize UI implementation
- authorize benchmark acceptance claims
- rewrite the core control-plane authority docs by itself

Retrospective `CLEARED` statuses remain prerequisite proof only. They do not, by themselves, lift the forward hard stop.

## Activation Block

- Last cleared code commit: `65a612dc1400abbedcfbdda1f173cd72a3a90c06` (`65a612d`)
- Execution baseline commit: `65a612dc1400abbedcfbdda1f173cd72a3a90c06`
- Candidate parent anchor: `65a612dc1400abbedcfbdda1f173cd72a3a90c06`
- Controller branch: `codex/remediation-program`
- Planned implementation branch: `codex/retrieval-mvp-fetch`
- Planned implementation worktree: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch`
- Planned run-packet root: `audit/remediation/runs/retrieval-mvp-fetch/`
- Main workspace policy: controller/docs only
- Lane purpose: gateway-owned governed fetch backends for article, filing, PDF, and paper retrieval

## Current-Code Anchors

Retrieval fetch setup is based on cleared `65a612d`, which has these relevant properties:

1. The default governed path is still mostly `task -> Exa/Brave snippet search -> LLM synthesis`.
2. `SimpleMCPClient` has real default backends only for `exa_search` and `brave_search`.
3. Registered tools such as `edgar_filings`, `paper_search`, `doi_verify`, `fred_data`, and `finnhub_market` must not be overstated as real canonical fetch backends on the default path.
4. The engagement wiki is a local knowledge-accumulation surface, not external full-document retrieval.
5. `DEEP_RESEARCH=1` is a bypass lane and must remain non-canonical for MVP acceptance.
6. Runtime truth claims for this lane must anchor to the sibling Wave 4B worktree or `git show 65a612d:...`, never to the dirty main workspace.

## Binding Scope In

This setup artifact authorizes only the following fetch-layer slice:

1. Gateway-owned article fetch.
2. Gateway-owned EDGAR filing fetch.
3. Gateway-owned PDF fetch and raw-byte persistence.
4. Gateway-owned paper metadata plus full text or authoritative abstract fetch.
5. Canonical URL normalization.
6. Explicit fetch coverage reporting.
7. Minimal typed retrieval-model additions required for fetch identity, coverage, and audit.
8. Gateway audit extension for fetch activity.
9. Tests that make the new fetch seams load-bearing.

## Binding Scope Out

The following remain explicitly out of scope:

1. Deterministic parser lane work as a major slice.
2. L1 integration, evidence-bundle migration, or citation anchoring migration.
3. Benchmark execution or benchmark acceptance claims.
4. `DEEP_RESEARCH=1` equivalence or publishability claims.
5. Semantic retrieval, embeddings, `pgvector`, BM25, RRF, rerank, or hybrid federation.
6. Internal-document or cross-engagement retrieval.
7. Claim-support verification as a formal runtime capability.
8. UI work.
9. Retrospective control-plane reconciliation.
10. Wave 5, calibration, or broader repo cleanup.

## Retrieval Fetch Control Rule

This artifact freezes the authority model for the next forward lane as follows:

1. The main workspace remains controller/docs only.
2. Any code change must run in a clean worktree rooted at `65a612d`.
3. The implementation lane must stay inside the gateway fetch seam and the exact write set below.
4. If the lane needs parser work, L1 integration work, new persistent infrastructure outside the named seam, or policy expansion beyond fetch truth and audit, stop and return to the control plane.
5. Do not bundle Wave 5, calibration, semantic retrieval, or benchmark acceptance under the label of "retrieval MVP fetch."
6. Do not treat registry breadth, bypass-mode output, or replay-independent artifacts as proof that governed full-document retrieval is complete.
7. The allowed files below are not blanket permission for broad refactors; they authorize additive-only fetch-specific edits inside those files.

## Hard Fetch Output Boundary

The only new runtime output surface this lane may create is:

- raw fetched bytes or raw fetched text
- source identity
- canonical URL
- MIME type
- content hash
- explicit coverage flag
- gateway audit record

This lane must not introduce:

- chunking
- parser quality work
- section or sentence locators
- evidence bundles
- citation anchoring
- synthesis changes
- research-agent integration
- orchestrator integration

## Exact Allowed Write Set

No path outside this list is authorized for the future code lane.

### Runtime code

- `src/keystone/gateway/audit_log.py`
- `src/keystone/gateway/mcp_gateway.py`
- `src/keystone/gateway/servers.py`
- `src/keystone/gateway/simple_client.py`
- `src/keystone/gateway/tool_registry.py`
- `src/keystone/models/research.py`
- `src/keystone/tool_names.py`

Allowed change kinds inside those files are limited to:

- fetch-tool registration and dispatch
- fetch audit fields
- fetch artifact identity metadata
- explicit discovery-only treatment for Exa and Brave on the canonical path

### Tests

- `tests/unit/gateway/test_auth.py`
- `tests/unit/gateway/test_gateway.py`
- `tests/unit/gateway/test_tool_registry.py`
- `tests/unit/test_auth.py`
- `tests/unit/test_audit_log.py`
- `tests/unit/test_gateway.py`
- `tests/unit/test_research_models.py`
- `tests/unit/test_tool_registry.py`

### Review collateral

- `audit/remediation/runs/retrieval-mvp-fetch/`

### Generated collateral

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`

## Exact Denylist

Every path outside the allowed write set is denied. High-risk denied surfaces include:

- auth changes
- rate-limiting changes
- circuit-breaker changes
- HITL behavior changes
- existing Exa or Brave semantics beyond explicitly preserving them as discovery-only
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
- benchmark task packs, judge-only files, and replay-pack data
- unrelated dirty files in the main workspace

Any widening beyond the exact allowed write set requires a later controller checkpoint.

## Required Test Matrix

At minimum, a future Retrieval MVP Lane D candidate must run:

1. `tests/unit/gateway/test_auth.py`
2. `tests/unit/gateway/test_gateway.py`
3. `tests/unit/gateway/test_tool_registry.py`
4. `tests/unit/test_auth.py`
5. `tests/unit/test_audit_log.py`
6. `tests/unit/test_gateway.py`
7. `tests/unit/test_research_models.py`
8. `tests/unit/test_tool_registry.py`

Broader suites are extra coverage, not a replacement for this matrix.

## Required Runtime Probes

The future candidate artifact set must name probes for these invariants:

1. Article fetch returns canonical URL, MIME, content hash, and explicit coverage.
2. EDGAR fetch returns official filing content rather than placeholder or stub text.
3. PDF fetch persists raw bytes with explicit coverage and hash.
4. Paper fetch returns full text when available, else explicit `abstract_only` or `metadata_only`.
5. Exa and Brave remain discovery-only on the canonical path.
6. Stubbed tool behavior cannot be misreported as canonical backend support.
7. Fetch activity is gateway-audited.

## Worktree Bootstrap

When this setup artifact is promoted and the fetch lane is ready, begin from the cleared baseline:

```bash
cd /Users/jackriddle/Desktop/Keystone-Intelligence-Engine
git worktree add -b codex/retrieval-mvp-fetch ../Keystone-Intelligence-Engine-retrieval-fetch 65a612dc1400abbedcfbdda1f173cd72a3a90c06
cd /Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch
```

If the clean worktree lacks its own virtual environment, reuse the shared repository venv by absolute path while keeping the working directory on the clean lane.

After any code-file changes in the worktree, rebuild graphify before ending the implementation session:

```bash
python3 -c "from graphify.watch import _rebuild_code; from pathlib import Path; _rebuild_code(Path('.'))"
```

## Candidate Artifact Requirements

Candidate artifacts must live under `audit/remediation/runs/retrieval-mvp-fetch/` and include:

- `candidate-<commit>-implementation.md`
- `candidate-<commit>-file-manifest.md`
- `candidate-<commit>-adversarial-review.md`
- `candidate-<commit>-second-opinion.md`
- `candidate-<commit>-review-synthesis.md`
- `candidate-<commit>-clearance.md` or `candidate-<commit>-blocked-checkpoint.md`

Every candidate packet must record:

- `candidate_commit`
- `candidate_parent_anchor`
- `approved_setup_artifact`
- `worktree_path`
- `worktree_clean`
- `branch`

## Reopen And Hard-Stop Triggers

Stop and return to the control plane if any of these happen:

1. The lane needs to widen into parser Lane E.
2. The lane needs to widen into L1 integration Lane F.
3. The lane needs new persisted infrastructure outside the named fetch seam.
4. The lane needs a schema migration, new dependency, or new file outside the exact allowlist.
5. The lane mixes governed and bypass retrieval for canonical claims.
6. The lane makes benchmark or publishability claims before replay and provenance gates are satisfied.
7. The lane needs any write-set expansion without a committed controller update.
8. A review finds a blocker that cannot be resolved inside the approved fetch slice.
9. The lane requires Jack's judgment or a new architecture decision not already settled by current authority docs.
10. Repo state or authority docs become contradictory enough that safe reconciliation is no longer possible.

## Final Authorization Line

This file is the exact setup artifact for the next forward lane.

It authorizes only Retrieval MVP Lane D fetch from baseline `65a612d`, and nothing broader.

It does not authorize parser work, L1 integration, UI work, Wave 5, calibration, or benchmark acceptance claims.

Because the core control-plane authority docs are intentionally not mutated in this session, a later controller reconcile must promote this artifact before the lane is formally open.
