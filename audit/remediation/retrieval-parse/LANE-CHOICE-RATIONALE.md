# Lane Choice Rationale

Date: 2026-04-14

## Decision

The next forward runtime lane should be a narrow Lane E only, but only after this setup package is later reviewed and promoted through the control plane.

That means:

- the immediate next work item is review and promotion of this docs-only package
- the first forward runtime lane after promotion is narrow article/PDF parse and evidence normalization
- no broader lane should open first

## Why Narrow Lane E Is The Right Next Lane

1. The control plane now says Lane H is cleared at `93a5ca8` and article/PDF governed fetch is real.
2. The remaining honest gap on the article/PDF path is deterministic parse and normalized evidence-prep, not fetch authority.
3. Lane E is the smallest runtime slice that can turn raw fetched artifacts into source-shaped, reviewable passages without reopening gateway or research-agent surfaces.
4. Graphify reinforces that boundary:
   - `MCP Gateway` is a god node and should stay frozen after Lane H
   - `CitationManifest` is a god node and should not be reopened casually in a narrow parser lane
   - `StructuredFinding` and downstream citation flow are broader integration surfaces than this lane should own

## Why This Is Not Lane H Again

Lane H already settled the disputed question:

- `document_fetch` is real
- `document_fetch` is system-owned
- `document_fetch` is not task-assignable
- governed article/PDF fetch is cleared separately from SEC

Reopening any of that inside Lane E would destroy the point of Lane H.
Lane E should treat those invariants as frozen input.

## Why This Lane Must Stay Narrower Than The Older Retrieval Docs

Older Retrieval MVP docs still describe the broader end-state path across filings, papers, `EvidenceBundle`, `AnchoredCitation`, and benchmark acceptance.
That design intent is still useful, but it is too broad for the live controller instruction on 2026-04-14.
For live Lane E scope and boundary questions, this narrow retrieval-parse package outranks those broader Retrieval MVP design docs.
Those docs are future-state design references only until a later controller promotion says otherwise.

The live boundary for this package is narrower:

- article/PDF only
- deterministic parse only
- evidence normalization only
- source-shaped locators and parse confidence only

This package therefore excludes:

- filing locators
- paper/DOI flows
- claim-scoped anchored citation flow
- `EvidenceBundle` promotion as the new L1 contract
- benchmark acceptance work

## Why Not Lane F

Lane F reopens exactly the surfaces narrow Lane E should avoid:

- `ResearchAgent`
- orchestration
- synthesis input contracts
- citation-schema and manifest migration

That is too broad for the next honest lane.
Lane E should end with parse-local normalized evidence, not with synthesis integration.

## Why Not SEC / EDGAR, UI, Or Benchmark Work

### Not SEC / EDGAR

- SEC remains explicitly separate and later.
- Article/PDF progress must not be blurred with filing progress.

### Not UI

- UI work adds reviewer/runtime surfaces before retrieval seams are stable.

### Not benchmark acceptance

- Benchmark claims remain later than the core retrieval seam.
- Lane E must not imply acceptance proof simply because parse is improved.

## End-Of-Day Target Judgment

As of 2026-04-14, Lane E alone does not satisfy the "working article/PDF retrieval layer" target.

Why not:

- today only a docs-only package is authorized
- even after Lane E implementation, the canonical path would still stop short of a usable internal handoff into selected passages or equivalent retrieval output
- downstream citation and synthesis integration remain intentionally blocked

## Thin Post-E Bridge Judgment

One thin post-E bridge is still needed later.

Smallest honest shape:

- an internal retrieval coordinator or equivalent adapter
- consumes promoted discovery/task context plus cleared Lane H fetch output
- runs Lane E parse and evidence normalization
- emits a selected-passage or equivalent internal payload with:
  - artifact identity
  - canonical URL
  - coverage
  - locator
  - parse confidence

That bridge must remain:

- internal, not a new public tool
- separate from full Lane F
- separately reviewed after Lane E clears

## Final Judgment

- immediate next checkpoint: review and promotion of this narrow Lane E package
- first forward runtime lane after later promotion: narrow Lane E only
- Lane E alone satisfies the parser/evidence-prep gap: yes
- Lane E alone satisfies the full working article/PDF retrieval-layer target: no
- thin post-E bridge still needed later: yes
