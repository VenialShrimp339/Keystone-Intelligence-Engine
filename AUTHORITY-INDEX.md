# Authority Index

Status: mandatory front door for fresh sessions.
Purpose: explain which documents answer which questions, in what order they should be read, and what must be updated before a session ends.

This file routes.
It does not outrank the live control plane for current truth.

## Fresh-Session Read Order

Claude and Codex use the same read order.
Auto-loading `CLAUDE.md` does not waive it.

1. `AUTHORITY-INDEX.md`
2. `SESSION-STANDARD.md`
3. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
4. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
5. `FOUNDER-INTENT-DOCTRINE.md`
6. `audit/remediation/control-plane/FRESH-ORCHESTRATOR-BOOTSTRAP.md`
7. `audit/remediation/control-plane/FRESH-ORCHESTRATOR-SESSION-PROMPT.md`
8. `CURRENT-STATE.md`
9. `audit/remediation/project-state-reconcile/MVP-REQUIRED-BUILDOUT.md`
10. the task-specific packet, package, or review index relevant to the current work
11. `SESSION-LOG.md` only if historical rationale is needed
12. generated support artifacts such as `graphify-out/GRAPH_REPORT.md` only if present

## Document Classes

### `current_truth`

Use these for live state, authorization, and next-step decisions.

Precedence inside this class:

1. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
2. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
3. `CURRENT-STATE.md`
4. `audit/remediation/control-plane/FRESH-ORCHESTRATOR-BOOTSTRAP.md`
5. `audit/remediation/control-plane/FRESH-ORCHESTRATOR-SESSION-PROMPT.md`
6. `audit/remediation/project-state-reconcile/MVP-REQUIRED-BUILDOUT.md`
7. `audit/remediation/WORKSTREAM-STATUS.md`

Conflict rule:

- scalar live-state conflicts are resolved by `CONTROL-PLANE-STATE.yaml`
- authority-order, packet-stack, and recovery conflicts are resolved by `ACTIVE-HANDOFF.md`
- if the pair disagree materially, stop and reconcile before continuing

### `architecture_intent`

Use these for founder intent and long-horizon architecture.

Precedence inside this class:

1. `FOUNDER-INTENT-DOCTRINE.md`
2. `JACK-ARCHITECTURAL-DIRECTIVES.md`
3. relevant sections of `CAPSTONE-PLAN-v2.md`

Repair rule:

- if the doctrine drifts from the underlying founder sources, repair the doctrine rather than silently treating the drift as canon

### `provenance`

Use these for chronology, review evidence, lineage, and packet history.

Precedence inside this class:

1. `audit/remediation/control-plane/RETROSPECTIVE-LINEAGE-MANIFEST.yaml`
2. `audit/remediation/control-plane/RETROSPECTIVE-REVIEW-LEDGER.yaml`
3. immutable blocked/cleared checkpoints and packet families
4. `audit/remediation/runs/retrieval-parse/package-c9c7a15-review-index.md`
5. `SESSION-LOG.md`

### `derived_narrative`

Use these to explain, route, or summarize.
They do not set live truth.

- `README.md`
- `CLAUDE.md`
- `AGENTS.md`
- `docs/ARCHITECTURE.md`
- `docs/architecture-and-evolution.md`
- `audit/remediation/README.md`

### `archive`

Use these as history, not as live authority.

- superseded wave/setup/process docs
- `audit/archive/`
- `docs/archive/`
- historical setup boundaries retained only for provenance

## Classified Docs

| Document | Class | Use |
|---|---|---|
| `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml` | `current_truth` | machine-readable live state |
| `audit/remediation/control-plane/ACTIVE-HANDOFF.md` | `current_truth` | human-readable live state, authority order, recovery |
| `audit/remediation/control-plane/FRESH-ORCHESTRATOR-BOOTSTRAP.md` | `current_truth` | controller onboarding companion |
| `audit/remediation/control-plane/FRESH-ORCHESTRATOR-SESSION-PROMPT.md` | `current_truth` | controller recovery prompt |
| `CURRENT-STATE.md` | `current_truth` | summary-only current state |
| `audit/remediation/project-state-reconcile/MVP-REQUIRED-BUILDOUT.md` | `current_truth` | gap map only |
| `audit/remediation/WORKSTREAM-STATUS.md` | `current_truth` | orientation only |
| `FOUNDER-INTENT-DOCTRINE.md` | `architecture_intent` | stable founder doctrine |
| `JACK-ARCHITECTURAL-DIRECTIVES.md` | `architecture_intent` | authoritative founder directives |
| `CAPSTONE-PLAN-v2.md` | `architecture_intent` | broader architecture plan and product intent |
| `audit/remediation/control-plane/RETROSPECTIVE-LINEAGE-MANIFEST.yaml` | `provenance` | retrospective checkpoint-chain lineage |
| `audit/remediation/control-plane/RETROSPECTIVE-REVIEW-LEDGER.yaml` | `provenance` | retrospective review-status layer |
| `audit/remediation/runs/retrieval-parse/package-c9c7a15-review-index.md` | `provenance` | pre-promotion provenance for the tracked Lane E package |
| `SESSION-LOG.md` | `provenance` | historical session narrative only |
| `README.md` | `derived_narrative` | repo landing page |
| `CLAUDE.md` | `derived_narrative` | Claude wrapper around shared standards |
| `AGENTS.md` | `derived_narrative` | Codex wrapper around shared standards |
| `docs/ARCHITECTURE.md` | `derived_narrative` | older code-structure snapshot |
| `docs/architecture-and-evolution.md` | `derived_narrative` | derived historical/professor narrative |
| `audit/remediation/README.md` | `derived_narrative` | historical remediation-process narrative |

## Stale-Doc Demotions

| Document | Demotion |
|---|---|
| `SESSION-LOG.md` | provenance-only history, not the complete live chronology |
| `docs/ARCHITECTURE.md` | older scaffold/code-structure snapshot, not live truth |
| `docs/architecture-and-evolution.md` | derived historical/professor narrative, not current-state truth |
| `audit/remediation/README.md` | historical remediation-process narrative, not live status authority |
| `README.md` | front door only, not live authority |

## Session / Provenance Update Standard

`SESSION-STANDARD.md` is the shared mandatory operating rule for both Claude and Codex.
At minimum, any repo-mutating or decision-setting session must leave:

- the required `SESSION-LOG.md` entry
- any required `CURRENT-STATE.md` update
- any required control-plane update
- any required packet or checkpoint doc

If a required artifact is skipped, the session is noncompliant.

## Generated Support Artifacts

- `graphify-out/GRAPH_REPORT.md` and `graphify-out/wiki/index.md` are generated support artifacts.
- If they are present, use them for architecture/codebase orientation.
- If they are absent, continue and note the absence.
- Do not treat generated artifacts as unconditional canonical dependencies for tracked entrypoints.

## Known Anomaly

- `reference/nano-claude-code` is a provenance anomaly, not a front-door dependency.
- Surface it as an unresolved risk when relevant.
- Do not casually repair its git metadata or contents during docs/provenance cleanup.
