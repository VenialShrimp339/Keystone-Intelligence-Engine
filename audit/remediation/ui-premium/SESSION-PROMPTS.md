# Session Prompts

Use these prompts as exact next-session launch texts.

## Prompt 1: Screen Spec And Interaction Contract

You are working in a docs-only session for the UI Premium workstream.
Use GPT-5.4 xhigh fast.

Guardrails:

- Do not modify runtime code.
- Do not interfere with the retrospective audit lane.
- Do not interfere with the retrieval-MVP lane.
- Keep all outputs under `audit/remediation/ui-premium/`.
- Treat `65a612d` in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-4b` as the last cleared runtime anchor.
- Do not design as if governed full-document retrieval, polished reviewer UI, or rich deliverables already exist.

Task:

- Refine the current UI premium package into a screen-by-screen interaction spec for:
- the `Research` home
- the plan-preview state
- the in-progress analysis state
- the review-checkpoint state
- the completed analysis state
- file upload and speech-to-text behaviors
- default versus advanced controls
- the right-side outputs pane
- Produce exact labels, empty states, warnings, button text, and status copy.

Deliverables:

- One `SCREEN-SPECS.md` doc under `audit/remediation/ui-premium/`
- Targeted updates to `INFORMATION-ARCHITECTURE.md` and `CHAT-SURFACE-AND-CONTROLS.md`
- One short `COPY-GUARDRAILS.md` appendix for labels and warnings

## Prompt 2: Run Inspector And Reviewer State Contract

You are working in a docs-only observability session for the UI Premium workstream.
Use GPT-5.4 xhigh fast.

Guardrails:

- Do not modify runtime code.
- Anchor all runtime claims to current code/docs reality.
- Keep outputs under `audit/remediation/ui-premium/`.
- Do not pretend L2, L3, or cross-engagement memory are active current-state product surfaces.
- Keep governed retrieval, bypass retrieval, and docs/demo flows visibly separate.

Task:

- Define the exact UI state contract for:
- analysis lifecycle states
- stage states
- workstream/task states
- review checkpoint states
- evidence and citation states
- degraded-mode badges
- analyst mode, advanced mode, and dev mode
- Specify which current artifacts and endpoints power each inspector section now, and which sections must stay provisional until retrieval seams lock.

Deliverables:

- One `RUN-STATE-CONTRACT.md` doc
- One `REVIEWER-FLOW-SPEC.md` doc
- Targeted updates to `RUN-INSPECTOR-AND-DEV-MODE.md`

## Prompt 3: Adversarial Review Before Any Unlock Request

You are the adversarial reviewer for the UI Premium workstream.
Use GPT-5.4 xhigh fast.

Guardrails:

- Be hostile to false green flags.
- Assume future sessions will try to smuggle progress by using premium visuals to hide retrieval and evaluator limitations.
- Treat `DEEP_RESEARCH=1` as a bypass lane, not canonical MVP evidence.
- Do not approve any implementation unlock unless the package stays honest about runtime authority, retrieval scope, HITL reality, and evaluation limits.

Task:

- Review the entire `audit/remediation/ui-premium/` package.
- Find overclaims, unstable assumptions, blocked dependencies, shallow-copy patterns, and misleading labels.
- Explicitly test whether the package cleanly separates:
- governed versus bypass research
- discovery versus evidence
- analyst mode versus dev mode
- current artifact reality versus future product ambition
- docs-only design work versus implementation unlock

Deliverables:

- One adversarial findings memo ordered by severity
- One required-corrections checklist
- One final yes-or-no judgment on whether the UI package is safe to use as a controller handoff
