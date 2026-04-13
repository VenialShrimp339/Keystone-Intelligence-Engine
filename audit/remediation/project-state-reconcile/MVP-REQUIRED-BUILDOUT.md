# MVP Required Buildout

## Scope rule

This file answers a narrow question: what still must be built, proven, or cleaned up before the project can claim a credible MVP without fooling itself.

- Baseline capability surface: cleared commit `65a612d`.
- Branch reality: current branch `codex/remediation-program` does not itself contain that runtime.
- Policy note: several next steps below are currently blocked from implementation until a later control-plane setup artifact authorizes a new code lane.

## Must build

1. One authoritative MVP runtime surface.
   The repo currently has a cleared implementation baseline in `codex/remediation-wave-4b`, but not one canonical mainline runtime surface. A credible MVP needs a single branch, release, or worktree that the docs point to without caveat.
2. One reproducible MVP run path.
   The core pipeline exists, but there is no single committed, repo-front-door run contract that makes a fresh reviewer confident about how to execute the cleared spine end to end.
3. One practical human-review workflow if HITL is part of the MVP claim.
   The backend/API gates are real. What is still unresolved is whether API-only review is acceptable for the MVP, or whether a minimal reviewer UI must exist before the claim is credible.

## Must validate

1. Re-run the cleared `65a612d` runtime from a clean worktree and confirm the default snippet-based path still works end to end.
2. Prove the multi-round loop on a real run, including round-state persistence, follow-up task generation, thin L2 outline construction, post-synthesis filtering, and markdown rendering.
3. Prove the per-engagement wiki/context path on a real iterative run so the knowledge-accumulation claims are not just unit-test-deep.
4. Prove the HITL backend through both gates in a real DB-backed run.
5. Decide whether deep research stays inside the MVP story.
   If yes, validate it explicitly as a gateway-bypass experimental lane.
   If no, remove or soften any MVP language that implies it is the normal governed path.
6. Produce a small exemplar package of stable outputs and review them manually.
   The project can claim “built” without this.
   It cannot credibly claim “pressure-tested MVP” without this.

## Must clean up

1. Align source-of-truth docs with the control plane and the cleared runtime surface.
2. Stop local modified/untracked docs from silently redefining what counts as built.
3. Make the branch/worktree split explicit everywhere.
   `codex/remediation-program` is docs/control-plane.
   `codex/remediation-wave-4b` contains the last cleared runtime.
4. Quarantine or reconcile the dirty worktree so local code/test drift does not masquerade as accepted capability.
5. Rewrite readiness language that currently overclaims:
   full retrieval,
   active Observation Library,
   five-layer calibrated evaluator,
   polished web UI,
   product-ready deployment.

## Not required for MVP

1. The planned production retrieval stack: `pgvector`, Voyage embeddings, BM25/RRF, reranking, Docling, and multi-source federation.
2. Governed full-document parity for filings/articles/PDFs on the main gateway path.
3. Semantic retrieval and relevance scoring over accumulated knowledge.
4. Observation Library runtime, CBR, cross-engagement promotion, trajectory learning, and prompt evolution.
5. Rich L3 output generation: PowerPoint, Excel, PDF, export/redraft stack.
6. A polished consultant-facing web app if API-backed HITL review is accepted for the MVP.
7. Wave 5 calibration, Layers 4-5 evaluator work, and human-aligned score tuning.
8. Full production infrastructure: Temporal workflows, auth, multi-tenancy, hardened deployment shape.

## Bottom line

The core analytical spine is close enough that the remaining MVP gap is no longer “invent the architecture.” It is “prove the cleared runtime, package it honestly, and stop the repo from telling three different stories at once.”
