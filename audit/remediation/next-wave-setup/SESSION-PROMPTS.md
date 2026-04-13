# Session Prompts

Use these prompts as exact next-session launch texts.

## Prompt 1: Control-Plane Promotion Of The Retrieval Fetch Setup Artifact

You are the controller for a docs-only promotion session.
Use GPT-5.4 xhigh fast.

Guardrails:

- Do not modify runtime code.
- The main workspace stays docs-only.
- Treat `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/next-wave-setup/NEXT-WAVE-SETUP-ARTIFACT.md` as the candidate setup checkpoint.
- Do not authorize Wave 5, calibration, parser Lane E, L1 integration Lane F, or UI work.
- Do not treat stale subordinate status prose as live authority.

Task:

- Re-read the control plane, the Wave 4B clearance packet, and the corrected `next-wave-setup/` package.
- Verify that all five required docs-only gate artifacts exist and say `CLEARED` for the reviewed snapshot.
- If coherent, promote the retrieval fetch setup artifact into the live control-plane authority docs.
- Update only the minimum controller docs needed to replace the current `missing setup artifact` hard stop with the exact Retrieval MVP Lane D fetch preparation state.
- Keep the main workspace docs-only and do not open the worktree in this session.

Deliverables:

- One docs-only controller reconcile commit.
- A live control-plane state that points to baseline `65a612d`, branch `codex/retrieval-mvp-fetch`, worktree `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch`, and the exact approved write set.

## Prompt 2: Retrieval MVP Lane D Fetch Implementation

You are working in the clean Retrieval MVP Lane D fetch worktree.
Use GPT-5.4 xhigh fast.

Guardrails:

- Runtime truth is the cleared implementation at commit `65a612d` in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-4b`, not the dirty main workspace.
- Work only on branch `codex/retrieval-mvp-fetch` in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch`.
- Stay inside the exact write set from `NEXT-WAVE-SETUP-ARTIFACT.md` and `ALLOWED-WRITE-SET.md`.
- Do not touch `src/keystone/tool_names.py`.
- Do not widen into parser work, L1 integration, UI work, benchmark execution, or Wave 5.
- Treat Exa and Brave as discovery-only.
- Treat `DEEP_RESEARCH=1` as bypass and non-canonical.
- If `mcp_gateway.py` or `models/research.py` require broader semantic changes than the setup artifact allows, stop and return to the control plane.

Task:

- Implement the fetch-layer seams for article, EDGAR filing, PDF, and paper retrieval.
- Add only the minimal retrieval-model and audit changes needed for fetch identity, coverage, and auditability.
- Make the named test matrix and runtime probes load-bearing.
- Produce a closed backend truth matrix and a live-fetch review proving that successful fetch claims did not use `MockMCPClient` or stub fallback.
- Rebuild graphify after any code-file change.
- Write the candidate packet under `audit/remediation/runs/retrieval-mvp-fetch/`.

Deliverables:

- Candidate code changes inside the approved write set only.
- Graphify collateral.
- `candidate-<commit>-implementation.md`
- `candidate-<commit>-file-manifest.md`
- `candidate-<commit>-backend-truth-matrix.md`
- `candidate-<commit>-live-fetch-review.md`

## Prompt 3: Adversarial Review And Second Opinion For Retrieval Fetch Candidate

You are the reviewer for the Retrieval MVP Lane D fetch candidate.
Use GPT-5.4 xhigh fast.

Guardrails:

- Be hostile to false unlocks and fake backend coverage.
- Treat registry presence and tool descriptions as non-evidence unless the candidate proves real backend behavior.
- Treat any governed-plus-bypass mixing as a blocker for canonical claims.
- Enforce the exact write set and denylist from the setup artifact.
- Treat any indirect tool-assignment change or shared research-model semantic change as blocked scope creep.

Task:

- Review the candidate diff, test evidence, backend truth matrix, live-fetch review, runtime probes, and file manifest.
- Look for scope creep, fake backend support, shallow query-shaped behavior disguised as fetch, missing audit coverage, ambiguous invocation contracts, and any widening into parser or L1 integration seams.
- Produce both an adversarial review and a second-opinion review.

Deliverables:

- `candidate-<commit>-adversarial-review.md`
- `candidate-<commit>-second-opinion.md`

## Prompt 4: Review Synthesis And Clearance Decision

You are the controller for Retrieval MVP Lane D candidate clearance.
Use GPT-5.4 xhigh fast.

Guardrails:

- Do not soften blockers into follow-ups if they widen scope or break fetch-lane truth.
- Do not treat benchmark readiness as part of this lane’s clearance.
- Keep the distinction between lane clearance and later benchmark acceptance explicit.

Task:

- Re-read the setup artifact, file manifest, implementation note, backend truth matrix, live-fetch review, adversarial review, second opinion, test evidence, and runtime probe evidence.
- Decide whether the candidate clears the fetch lane or stops in a blocked checkpoint.
- Record whether the candidate stayed inside the approved write set, whether any allowed-file diff changed shared runtime behavior outside raw fetch transport, fetch identity, fetch coverage, or fetch audit, and whether any follow-on controller checkpoint is now required.

Deliverables:

- `candidate-<commit>-review-synthesis.md`
- `candidate-<commit>-clearance.md` or `candidate-<commit>-blocked-checkpoint.md`
