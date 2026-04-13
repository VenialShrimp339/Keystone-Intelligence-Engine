# UI Premium Workstream Handoff

Date: 2026-04-12  
Controller mode: docs-only orchestration  
Status: design/spec lane open; implementation blocked  
Authoritative runtime anchor: `65a612d` in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-4b`

## Mission

Design a premium, intuitive, analyst-friendly future UI for Keystone without pretending the current product surface is already a polished web app.

This lane is allowed to specify:

- the future MVP UI
- the analyst chat surface
- progressive disclosure rules
- run transparency and dev mode
- safe later implementation decomposition

This lane is not allowed to start:

- runtime UI implementation
- retrieval contract changes
- retrospective-audit work
- any claim that the current checkout is the canonical product runtime

## Hard Guardrails

- Keep all outputs under `audit/remediation/ui-premium/`.
- Do not modify runtime code.
- Do not interfere with the active retrospective audit lane.
- Do not interfere with the active retrieval-MVP lane.
- Treat nontechnical analysts as the primary user.
- Stay familiar to ChatGPT, Claude, and Codex-style apps without shallow copying.
- Keep progressive disclosure explicit: clean top-level UX, deeper pipeline/run/agent/debug visibility underneath.
- Do not let premium styling create false trust.

## Ground Truth

- The current checkout is a docs/control-plane workspace, not a clean product repo.
- The last cleared runtime is `65a612d` in the sibling Wave 4B worktree.
- Real UI-relevant surfaces exist today as:
  - CLI/test launch flow
  - in-process typed pipeline events
  - HITL REST endpoints and DB-backed gate state
  - markdown output plus JSON artifact bundles
  - filesystem wiki/raw artifact storage
- Not yet productized in this repo:
  - committed web UI
  - packaged pipeline API surface
  - websocket/live event bridge
  - practical HITL reviewer app
  - governed full-document retrieval
  - stable run-history product surface
  - calibrated five-layer evaluator
- `DEEP_RESEARCH=1` is real but bypasses gateway governance and cannot anchor MVP truth claims.

## Executive Judgment

- Is this a good third workstream right now: yes, as a docs-only honest-UX contract lane.
- Is this a good third implementation workstream right now: no.
- Should any UI implementation start now: no. Remain blocked until retrieval seams lock and one canonical runtime surface is promoted.
- Should later authoritative docs be updated: yes, but only after retrieval architecture locks and a controller-approved UI implementation lane exists.

Recommended later authoritative updates:

- `CURRENT-STATE.md`
- `docs/system-diagram.md`
- `docs/architecture-and-evolution.md`
- `audit/remediation/project-state-reconcile/DOCS-CONTRADICTIONS-AND-SOURCE-OF-TRUTH.md`
- `README.md`

## What This Package Decides

### What the eventual MVP UI should include

- A familiar chat-like research launcher with a calm default surface.
- File upload and speech-to-text as first-class input actions.
- One plain-language research-depth control, not a model zoo.
- A visible research-plan preview before heavy work begins.
- Run history with truthful statuses.
- A run inspector with stage, task, evidence, citation, gate, and artifact drill-down.
- Honest banners for governed, experimental bypass, mixed, or docs/demo-only runs.
- A clear split between analyst mode, advanced analyst controls, and dev mode.

### What the eventual MVP UI should not include

- Polished dashboard theatrics that imply more certainty than the backend warrants.
- Fake ETAs or fake percent-complete bars.
- "Verified" language that implies claim support rather than citation existence/liveness.
- One-click deep research presented as a canonical path.
- L2/L3, cross-engagement memory, or Observation Library surfaces as if they are live product depth.

### What must explicitly wait for retrieval architecture lock

- Source-scope controls that promise more than snippet discovery.
- Fetch-level provenance UI for full documents and passages.
- Unified governed-versus-bypass history semantics.
- Coverage metrics that distinguish discovered, fetched, parsed, anchored, and claim-supported evidence.
- Any final source drawer taxonomy that depends on the retrieval seam contract.

## Recommended Parallel UI Sub-Workstreams

### Docs-only lanes that can run now

1. Analyst surface and IA contract.
2. Run inspector, reviewer-flow, and dev-mode truth surface.
3. Honest-copy, disclosure, and adversarial review lane.

### Runtime lanes that can start later in parallel once unlocked

1. Frontend shell and navigation.
2. Run timeline, history, and artifact browser.
3. HITL reviewer surface.
4. Evidence and citation panels.

## Exact First 3 Session Prompts

The exact prompts are in [SESSION-PROMPTS.md](./SESSION-PROMPTS.md).

Recommended order:

1. Screen and interaction spec refinement.
2. Run-inspector and reviewer-state contract.
3. Adversarial review before any implementation unlock request.

## Package Map

- [DESIGN-PRINCIPLES.md](./DESIGN-PRINCIPLES.md): non-negotiable UX rules
- [REFERENCE-PATTERN-AUDIT.md](./REFERENCE-PATTERN-AUDIT.md): external pattern synthesis
- [INFORMATION-ARCHITECTURE.md](./INFORMATION-ARCHITECTURE.md): navigation, objects, onboarding
- [CHAT-SURFACE-AND-CONTROLS.md](./CHAT-SURFACE-AND-CONTROLS.md): chat launcher and control model
- [RUN-INSPECTOR-AND-DEV-MODE.md](./RUN-INSPECTOR-AND-DEV-MODE.md): transparency and debug surfaces
- [MVP-UI-SCOPE.md](./MVP-UI-SCOPE.md): now vs later vs blocked
- [IMPLEMENTATION-LANES.md](./IMPLEMENTATION-LANES.md): safe work decomposition
- [SESSION-PROMPTS.md](./SESSION-PROMPTS.md): exact next-session launch texts
- [RISK-REGISTER.md](./RISK-REGISTER.md): failure modes and mitigations

## Controller Notes For The Next Session

- Anchor every runtime claim to the current authority chain, not to this dirty checkout.
- Treat chat as a control surface and summary layer, not as the truth surface.
- Keep governed retrieval, bypass retrieval, and docs/demo flows visibly distinct.
- Require adversarial review before treating any UI spec as stable enough for implementation.
- If a future session tries to start UI runtime code before retrieval seams lock, stop and re-check the retrieval-MVP handoff first.
