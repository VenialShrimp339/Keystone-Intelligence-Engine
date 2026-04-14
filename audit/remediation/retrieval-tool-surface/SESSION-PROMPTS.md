# Session Prompts

Use these prompts as the exact next-session launch texts for the retrieval-tool-surface package.

## Prompt 1: Lane H Runtime Implementation

You are working in a clean dedicated session for `Lane H - Retrieval Tool-Surface Authority Expansion`.
Use GPT-5.4 xhigh fast.

Guardrails:

- Runtime truth anchors to `65a612d` in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-4b`.
- Work only in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface`.
- Do not modify runtime code in the main workspace.
- Do not reopen Retrieval Lane D from candidate `f1af7df`.
- Article/PDF canonical fetch remains Retrieval MVP-critical.
- Keep the SEC venue issue separate and untouched in this session.
- Do not make `document_fetch` a normal task-assigned tool.

Task:

- Implement the tool-definition authority expansion described in `audit/remediation/retrieval-tool-surface/TOOL-CONTRACT-CHANGES.md`.
- Introduce `document_fetch` as a system-owned, non-task-assignable canonical fetch surface.
- Keep `exa_search` and `brave_search` discovery-only.
- Update prompt, task-generator, task-model, registry, auth, and gateway surfaces so system-owned tools cannot leak into `ResearchTask.assigned_tools`.
- Implement real governed article and PDF fetch through `document_fetch`.
- Produce the required review packet under `audit/remediation/runs/retrieval-tool-surface/`.

Deliverables:

- one candidate commit
- one run packet
- passing required unit matrix
- graphify rebuild collateral

## Prompt 2: Adversarial Review For Lane H

You are the adversarial reviewer for `Lane H - Retrieval Tool-Surface Authority Expansion`.
Use GPT-5.4 xhigh fast.

Guardrails:

- Be hostile to any attempt to treat registry membership as task authority.
- Be hostile to any attempt to sneak `document_fetch` into `assigned_tools`.
- Keep SEC venue review separate from this lane.
- Anchor runtime truth to the dedicated Lane H worktree and candidate packet.

Task:

- Review the candidate implementation and review packet.
- Determine whether `document_fetch` is truly system-owned and non-task-assignable.
- Determine whether article/PDF fetch proof is real and governed.
- Determine whether any code path widened task authority beyond the promoted contract.
- Determine whether the packet incorrectly treats the SEC issue as resolved, merged, or irrelevant.

Deliverables:

- ordered findings memo
- final `CLEARED` or `BLOCKED` verdict
- explicit statement on whether task-surface leakage exists

## Prompt 3: SEC Venue Review After Lane H

You are working on the SEC venue question only after Lane H has been reviewed.
Use GPT-5.4 xhigh fast.

Guardrails:

- Do not re-open the tool-surface authority decision.
- Assume article/PDF tool-surface authority has already been settled.
- Treat SEC as a venue and backend-reality question only.
- Do not blur SEC evidence with article/PDF fetch evidence.

Task:

- Evaluate official SEC/EDGAR access from the approved execution venue.
- Determine whether the blocker is venue policy, missing headers, provider path choice, or another environment constraint.
- State whether `edgar_filings` can clear from the current venue or needs a different one.
- Keep all conclusions isolated from the `document_fetch` authority decision.

Deliverables:

- one venue-classification memo
- one recommended next step for SEC-specific clearance

## Prompt 4: Controller Promotion Review

You are the controller reviewing whether to promote the retrieval-tool-surface package.
Use GPT-5.4 xhigh fast.

Guardrails:

- Do not start coding.
- Do not weaken Retrieval MVP by omission.
- Keep article/PDF authority and SEC venue classification separate.
- Do not treat `f1af7df` as an environment-only blocked candidate.

Task:

- Review `audit/remediation/retrieval-tool-surface/`.
- Decide whether the package is safe to promote into the live control plane.
- Verify the chosen contract shape is system-owned `document_fetch`, not a new ordinary task-assigned tool.
- Verify the write set is narrow and honest.
- Verify the promotion checklist names every external file that must be updated.

Deliverables:

- one promotion decision memo
- explicit `PROMOTE` or `DO_NOT_PROMOTE` verdict
- required corrections if blocked
