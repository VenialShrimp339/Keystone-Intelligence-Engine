# Session Prompts

Use these prompts as exact next-session launch texts for the narrow Lane E package.

## Immediate Next Review Sessions

### Prompt 1: Scope And Write-Set Review For The Lane E Package

You are the read-only reviewer for the narrow Lane E package.
Use GPT-5.4 xhigh fast.

Guardrails:

- Do not edit files.
- Treat Lane H at `93a5ca8` as already cleared runtime truth.
- Treat `document_fetch` ownership as settled and frozen.
- Be hostile to any attempt to widen into gateway, task-assignment, SEC, Lane F, UI, or benchmark work.

Task:

- Review `audit/remediation/retrieval-parse/`.
- Determine whether the setup artifact and allowed write set are the narrowest honest article/PDF parse lane.
- Verify the write set does not reopen Lane H or Lane F surfaces.
- State whether any blocked path is missing from the denylist.

Deliverables:

- one scope/write-set review memo
- explicit `CLEARED` or `BLOCKED` verdict

### Prompt 2: Stale-Doc And Conflict Review For The Lane E Package

You are the read-only stale-doc and conflict reviewer for the narrow Lane E package.
Use GPT-5.4 xhigh fast.

Guardrails:

- Do not edit files.
- Treat control-plane docs and the cleared Lane H packet as authoritative.
- Be hostile to any historical doc that still implies Lane H is pending, Lane D is next, or broad Retrieval MVP scope is already authorized.

Task:

- Review `audit/remediation/retrieval-parse/`.
- Check whether the package clearly subordinates stale retrieval docs to the live control plane.
- Check whether the package clearly says SEC / EDGAR remains separate and later.
- Check whether the package clearly says Lane E does not re-decide `document_fetch`.

Deliverables:

- one stale-doc/conflict review memo
- explicit `CLEARED` or `BLOCKED` verdict

### Prompt 3: Usefulness And EOD-Target Sanity Review For The Lane E Package

You are the read-only usefulness reviewer for the narrow Lane E package.
Use GPT-5.4 xhigh fast.

Guardrails:

- Do not edit files.
- Treat the target as a truthful article/PDF retrieval layer only.
- Do not quietly convert Lane E into Lane F.

Task:

- Review `audit/remediation/retrieval-parse/`.
- Determine what concrete value narrow Lane E adds beyond cleared Lane H.
- Decide whether Lane E alone would satisfy the end-of-day article/PDF retrieval-layer target.
- If not, name the smallest honest post-E bridge and confirm it remains separate from Lane F.

Deliverables:

- one usefulness sanity memo
- explicit `CLEARED` or `BLOCKED` verdict
- explicit yes/no answer on whether a thin post-E bridge is still needed

### Prompt 4: Controller Promotion Review For The Lane E Package

You are the controller reviewing whether to promote the narrow Lane E package.
Use GPT-5.4 xhigh fast.

Guardrails:

- Do not start coding.
- Keep the main workspace docs-only.
- Do not weaken Lane H invariants.
- Do not authorize SEC / EDGAR, Lane F, UI, or benchmark acceptance work.

Task:

- Re-read the control plane, the cleared Lane H packet, and `audit/remediation/retrieval-parse/`.
- Verify the package is coherently rooted from `93a5ca8`.
- Verify the package stays article/PDF-only and parse-only.
- Verify the package states clearly that one thin post-E bridge is later and separate.
- Decide whether the package is safe to promote into the live control plane.

Deliverables:

- one promotion decision memo
- explicit `PROMOTE` or `DO_NOT_PROMOTE` verdict

## Follow-On Runtime Sessions After Promotion

### Prompt 5: Lane E Runtime Implementation

You are working in the clean narrow Lane E worktree.
Use GPT-5.4 xhigh fast.

Guardrails:

- Runtime truth anchors to `93a5ca8` in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface`.
- Work only in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-parse`.
- Stay inside `audit/remediation/retrieval-parse/ALLOWED-WRITE-SET.md`.
- Do not touch gateway, task-generation, `document_fetch`, citation-schema, or research-agent surfaces.
- Stay article/PDF only.

Task:

- Implement deterministic article/PDF parse and evidence normalization from persisted Lane H artifacts.
- Emit source-shaped locators and parse confidence where needed.
- Produce the required review packet under `audit/remediation/runs/retrieval-parse/`.
- If graphify is available, rebuild its collateral after code-file changes; otherwise continue and record that graphify was unavailable.

Deliverables:

- one candidate commit
- one run packet
- passing required test matrix
- optional graphify collateral if generated, or an explicit absence note if graphify is unavailable

### Prompt 6: Adversarial Review And Second Opinion For Lane E Candidate

You are the reviewer for the narrow Lane E candidate.
Use GPT-5.4 xhigh fast.

Guardrails:

- Be hostile to scope creep into Lane H or Lane F.
- Be hostile to invented locators, non-deterministic parse, or silent degradation.
- Treat any gateway, task-assignment, or citation-schema diff as presumptively blocked.

Task:

- Review the candidate diff, tests, parse probes, file manifest, and review packet.
- Determine whether article and PDF parse are truly deterministic from persisted artifacts.
- Determine whether evidence normalization preserves upstream artifact truth.
- Determine whether any code path widened the lane into fetch or integration work.

Deliverables:

- `candidate-<commit>-adversarial-review.md`
- `candidate-<commit>-second-opinion.md`

### Prompt 7: Review Synthesis And Clearance Decision For Lane E Candidate

You are the controller for narrow Lane E candidate clearance.
Use GPT-5.4 xhigh fast.

Guardrails:

- Do not soften lane-boundary violations into follow-ups.
- Keep Lane E clearance separate from the later thin bridge and from Lane F.
- Do not treat broad retrieval MVP design intent as live scope authority.

Task:

- Re-read the setup artifact, allowed write set, implementation note, file manifest, parse-truth matrix, deterministic-parse review, evidence-normalization review, adversarial review, second opinion, and parse-probe evidence.
- Decide whether the candidate clears the narrow parse lane or stops in a blocked checkpoint.

Deliverables:

- `candidate-<commit>-review-synthesis.md`
- `candidate-<commit>-blocked-or-cleared-checkpoint.md`

## Later Separate Follow-On

### Prompt 8: Thin Post-E Bridge Design Review

You are the controller for the thin post-E bridge design only.
Use GPT-5.4 xhigh fast.

Guardrails:

- Assume Lane H is cleared.
- Assume narrow Lane E is already cleared or under final review.
- Do not open full Lane F.
- Do not create a new public tool.
- Keep SEC / EDGAR separate.

Task:

- Define the smallest internal bridge that turns cleared fetch plus parse outputs into a usable selected-passage handoff.
- Keep the bridge internal and separate from full citation-schema migration.
- State the exact write-set and review burden required for that bridge.

Deliverables:

- one bridge-design memo
- explicit statement on whether the bridge can remain thinner than Lane F
