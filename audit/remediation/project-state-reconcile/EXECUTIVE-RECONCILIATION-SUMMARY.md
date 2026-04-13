# Executive Reconciliation Summary

## What is truly built now

There is a real analytical engine here, but it is not a clean product repo yet. Using the control plane, the last cleared implementation is commit `65a612d` on 2026-04-11 in the sibling Wave 4B worktree. That cleared runtime can take a question through specification, agent research, citation handling, deliberation, thin structuring, evaluation, and markdown output with provenance controls.

### Top 10 capabilities truly built now

1. L0 Specification Engine that turns a question into a structured engagement spec and task set.
2. MCP Gateway governance for normal tool calls: authorization, rate limiting, circuit breaking, and audit logging.
3. Default live research path using Exa and Brave snippet retrieval.
4. Citation processing with deduplication, canonicalization, and URL liveness checks.
5. Deliberation that builds a confidence map and contradiction/uncertainty surface.
6. Minimum viable multi-round orchestration with round-state persistence and follow-up task generation.
7. Per-engagement wiki compilation plus round-to-round context reuse.
8. Thin Pipeline-L2 outline construction.
9. Evaluator Layers 1-3 with profile-aware scoring and render gating.
10. Markdown deliverable generation with post-synthesis filtering and provenance sidecar support.

## What still must be built or proven for MVP

The main gap is no longer “invent the system.” The gap is “prove and package the cleared system honestly.”

### Top 10 capabilities still required for MVP

1. One authoritative MVP runtime surface that clearly points to the cleared implementation, not just the docs/control-plane branch.
2. One reproducible run contract with pinned environment assumptions and a clean front-door entrypoint.
3. A clean end-to-end validation run on the cleared runtime using the default research path.
4. Proof that the multi-round loop, wiki context reuse, thin L2, evaluator, and markdown path work together on real inputs.
5. Proof that the HITL backend works end to end in a real DB-backed flow.
6. A decision on whether deep research is inside the MVP story.
7. If deep research stays in the MVP story, explicit validation and labeling of it as a gateway-bypass lane.
8. A small set of stable exemplar outputs that can be manually reviewed.
9. Source-of-truth doc cleanup so the repo stops overstating full retrieval, self-improvement, evaluator completeness, and UI maturity.
10. Dirty-worktree cleanup or quarantine so local drift stops distorting project status.

## What belongs to the fuller long-term version

The long-term vision is still much larger than the current MVP spine.

### Top 10 deferred or fuller-version items

1. Production retrieval stack with hybrid search, embeddings, reranking, and document parsing.
2. Governed full-document retrieval for filings, articles, PDFs, and other primary sources.
3. Semantic retrieval over accumulated knowledge rather than loading everything.
4. Internal-document federation with secure access control.
5. Observation Library runtime with real recording, query, and promotion behavior.
6. Cross-engagement memory, client calibration, and trajectory-driven learning.
7. Richer adaptive replanning and semantic novelty search.
8. Rich L2/L3 deliverable generation beyond markdown, including PPT/Excel/PDF-style outputs.
9. Consultant-facing web UI and a practical full HITL reviewer experience.
10. Wave 5 calibration, higher evaluator layers, and production deployment infrastructure.

## Where we were at risk of fooling ourselves

### The 5 most dangerous documentation contradictions

1. The control plane says `65a612d` is the cleared runtime, but the current branch does not contain that code.
2. The local README and local architecture docs read like a ready product repo, while the control plane says the main workspace is docs/control-plane only.
3. Retrieval language can imply full-document and broad source coverage, but the default committed runtime is still mostly Exa/Brave snippets plus stubs.
4. Evaluator docs can imply a calibrated five-layer quality stack, but the committed runtime is a three-layer evaluator and Wave 5 is deferred.
5. Observation-library and self-improvement language can imply active learning, but the real operational surface today is only an engagement-scoped wiki plus a stubbed Observation Library seam.

## Final judgment

The repo currently both overstates readiness and understates readiness.

- It overstates readiness because local modified or untracked docs can make the system sound more productized, more deeply retrieved, more self-improving, and more calibrated than it really is.
- It understates readiness because the checked-out main branch and older committed architecture docs do not themselves show the later cleared Wave 3-4B runtime.

If forced to choose the more dangerous error, overstatement is the bigger risk. The project has a real analytical core, but it is not yet honest or durable enough in its presentation to claim the full long-term system is already here.
