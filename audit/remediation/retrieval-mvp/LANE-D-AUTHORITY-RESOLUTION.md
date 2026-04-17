# Lane D Authority Resolution

Status: historical/provenance packet material retained for lineage only.
Use this file to understand the blocked Lane D authority decision for candidate `f1af7df`.
Do not use this file as live current truth or as the next-action authority for the current repo state.
For live truth, start with `AUTHORITY-INDEX.md`, `SESSION-STANDARD.md`, the control-plane pair, and the promoted Lane E packet under `audit/remediation/retrieval-parse/`.

Date: 2026-04-13  
Controller mode: docs-only authority resolution  
Worktree under review: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch` at candidate `f1af7dfafa2e66b831810d70006ab8295411c61b`

## Controller Recommendation

`ESCALATE_TO_NEW_LANE`

## Explicit Answers

### 1. Is a new gateway-owned `document_fetch` tool surface allowed for Lane D?

No.

Under the current promoted Lane D authority, a new registered and callable `document_fetch` surface is not fetch-local implementation detail. It is a cross-layer tool-contract expansion, and the active setup package explicitly fenced that class of change out of Lane D.

### 2. If yes, what exact authority docs would need amendment?

Not applicable to the current decision because the answer above is no.

Counterfactual note for a later controller: if a later session wants to allow a new callable `document_fetch` surface, it would need a new authority package that amends at minimum:

- `audit/remediation/next-wave-setup/NEXT-WAVE-SETUP-ARTIFACT.md`
- `audit/remediation/next-wave-setup/ALLOWED-WRITE-SET.md`
- `audit/remediation/next-wave-setup/REVIEW-AND-GATE-CHECKLIST.md`
- `audit/remediation/next-wave-setup/TOOL-CONTRACT-GATE.md`
- `audit/remediation/next-wave-setup/GOVERNANCE-GATE.md`
- `audit/remediation/next-wave-setup/RUN-CONTRACT-GATE.md`
- `audit/remediation/retrieval-mvp/IMPLEMENTATION-LANES.md`
- `audit/remediation/retrieval-mvp/RUNTIME-LANE-UNLOCK-MEMO.md`
- `audit/remediation/retrieval-mvp/WORKTREE-AND-REVIEW-GATE-CHECKLIST.md`
- `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
- `audit/remediation/control-plane/ACTIVE-HANDOFF.md`

That later controller package would also need coordinated code-contract ownership for:

- `src/keystone/tool_names.py`
- `src/keystone/specification/prompts/task_generation.md`
- `src/keystone/specification/task_generator.py`
- `src/keystone/models/tasks.py` if membership validation is tightened

Those are not current Lane D surfaces.

### 3. If no, what exact redesign path should replace it?

Replace the current approach with a split decision:

1. Reject `document_fetch` as a Lane D registry/auth surface.
2. Freeze candidate `f1af7df` as authority-blocked. Do not patch it forward in Lane D.
3. Keep Lane D limited to existing authorized tool names only:
   - `edgar_filings` for filing fetch
   - `paper_search` and `doi_verify` for paper fetch and identity support
   - `exa_search` and `brave_search` remain discovery-only
4. Treat generic article/PDF canonical fetch as requiring a new controller-approved lane that owns tool-surface authority expansion.
5. Make that new lane own both the docs authority updates and the cross-layer tool-contract surfaces before any later fetch implementation resumes.

This is the narrowest redesign that matches the current authority stack without pretending the existing Lane D setup already authorized tool-surface widening.

## Why The Answer Is No

### A. Design intent and live lane authority diverged

The retrieval design packet clearly contemplated a future gateway-owned article/PDF fetch backend:

- `audit/remediation/retrieval-mvp/RETRIEVAL-MVP-ARCHITECTURE-MEMO.md` proposes `document_fetch` for article and PDF rows.
- `audit/remediation/retrieval-mvp/RETRIEVAL-MVP-MIGRATION-CHECKLIST.md` says to add a gateway-owned article/PDF fetch backend, for example `document_fetch`.
- `audit/remediation/retrieval-mvp/RETRIEVAL-MVP-SEAM-CONTRACT.md` uses `document_fetch` as an example backend hint.

But those docs are design direction, not the final live forward-lane authority.

The live authority for the actual Lane D code lane is the next-wave setup package under `audit/remediation/next-wave-setup/` plus the control plane. That promoted package intentionally narrowed the lane after adversarial review.

### B. The promoted Lane D package froze tool-surface expansion out of scope

The current live setup package says all of the following:

- `src/keystone/tool_names.py` is out of scope for Lane D.
- tool-assignment changes through allowed files count as blocked L1 integration scope creep.
- `src/keystone/specification/**` is denied.
- the Tool Contract Gate cleared on the explicit theory that fencing out `src/keystone/tool_names.py` prevented quiet rewrites of shared tool grouping or default assignment behavior.

That means the active lane may implement fetch transport and audit inside allowed files, but it may not introduce a new callable tool surface whose contract has not been promoted through the canonical tool-authority stack.

### C. In this repo, a registered tool surface is not just a backend helper

The candidate adds `document_fetch` in `src/keystone/gateway/servers.py` and updates registry tests from 7 to 8 surfaces.

That is controller-significant because the current canonical tool stack still says:

- `src/keystone/tool_names.py` is the single source of truth for registered MCP tool identifiers and says adding a new MCP server means adding a new enum member there first.
- `src/keystone/specification/prompts/task_generation.md` hardcodes the exact allowed tool list and excludes `document_fetch`.
- `src/keystone/specification/task_generator.py` filters LLM-provided tool lists against `ALL_TOOLS`.

So a registry-only `document_fetch` does not stay local to the fetch seam. It creates drift across:

- gateway registry
- tool-name authority
- task-generation prompt contract
- task-generator filtering
- per-agent authorization semantics

That is exactly the sort of cross-layer tool-surface widening the current Lane D setup package said not to do.

### D. Candidate `f1af7df` therefore fails on authority before venue

The candidate packet honestly records the SEC `403` and does not claim clearance. That is good.

But the candidate is still blocked even if the SEC host had returned `200`, because the packet makes article and PDF canonical claims through `document_fetch`, which the current Lane D authority did not permit as a new registered/callable tool surface.

## SEC `403` Classification

The SEC `403 Forbidden` is a real separate issue, but it is not the deciding issue for this controller question.

Controller ordering:

1. Resolve whether Lane D may introduce a new callable tool surface at all.
2. Only after that is settled, resolve whether the SEC probe failure is:
   - venue-specific access policy,
   - implementation defect inside the allowed lane, or
   - evidence that official filing access needs a different execution venue.

So the SEC issue matters after the authority issue, not before it.

## Consequences For The Current Candidate

- Candidate status: `BLOCKED`
- Blocking reason: tool-surface authority failure first, SEC venue issue second
- `document_fetch` status for current Lane D: rejected
- More Lane D coding in this session: not authorized

## Why This Is An Escalation, Not A Small Lane D Rework

Allowing `document_fetch` cleanly would require ownership of surfaces that the current Lane D package explicitly classified as outside the fetch seam:

- canonical tool-name authority
- task-generation prompt authority
- task-generator registration filtering
- possibly task-model membership validation

That is a lane-boundary change, not just a fetch-helper implementation detail. The honest controller move is therefore `ESCALATE_TO_NEW_LANE`, not to pretend the current Lane D write set already covered it.

## Decision Record

- Controller recommendation: `ESCALATE_TO_NEW_LANE`
- New gateway-owned `document_fetch` for current Lane D: `REJECTED`
- SEC `403` relevance: separate venue question, after the authority question
- More Lane D coding now: `NO`
