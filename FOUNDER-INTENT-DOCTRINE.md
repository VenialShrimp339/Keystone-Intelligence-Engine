# Founder Intent Doctrine

Status: stable founder-intent canon.
Use this file for product doctrine only.

If this file conflicts with live operational truth, the live control plane wins for current state.
If this file drifts from `JACK-ARCHITECTURAL-DIRECTIVES.md` or the relevant intent sections of `CAPSTONE-PLAN-v2.md`, repair this file instead of silently treating the drift as intentional.

## Source Basis

- `JACK-ARCHITECTURAL-DIRECTIVES.md`
- `CAPSTONE-PLAN-v2.md`
- authoritative founder clarifications preserved during the 2026-04-16 canon-and-reconciliation pass
- authoritative founder clarifications from 2026-05-24 through 2026-05-28 on subscription-first provider routing, browser Deep Research acquisition, artifact-centered execution, and the issue-tree/problem-decomposition skill

## Intended Product Shape

- Keystone is a spec-driven, issue-tree-based, multi-agent deep-research system for real consulting work.
- It is not a retrieval-only tool, not a narrow lane artifact, and not a small demo scaffold pretending to be the full product.
- Retrieval, parse, evidence normalization, citation grounding, audit, and evaluation are trust infrastructure inside that larger research system.
- The system is meant to support broad consulting engagements across operations, growth, M&A, restructuring, and adjacent research-heavy workstreams.

## Runtime Doctrine

- The old Claude CLI-first doctrine is stale.
- Founder-preferred runtime path is subscription-first and provider-agnostic: Codex CLI for structured local orchestration, ChatGPT web Deep Research as the primary hosted research acquisition surface, Claude web Research as a secondary/cross-check surface while available, manual upload as fallback, deterministic public-source connectors where precision matters, and API only as fallback or control.
- Exact commit pins, worktrees, live lane status, and approved write sets belong to live operational truth, not to founder doctrine.

## Interaction Model

- Work begins from user intent and decision context, not from a generic search or prompt template.
- The system should decompose work through a specification layer and issue trees before major research fan-out.
- Issue-tree generation should use the portable problem-decomposition methodology and should expose the problem frame, candidate axes, full tree, pruned decision tree, pruning rationale, branch logic, and leaf evidence requirements before major research spend.
- The system should behave like a proactive research associate: it should surface hidden assumptions, rival hypotheses, and adjacent lines of inquiry, but it must not override or ignore the user’s requested scope.
- Human review is profile- and ambiguity-dependent:
  - Light work may use compressed approval.
  - Standard and Deep work require explicit scoping approval before major fan-out.
  - Deliverable-grade output requires final confidence-map review.

## Replanning Policy

- Adaptive replanning is allowed.
- The engagement objective stays anchored to user intent.
- Plan and branch structure may adapt as evidence changes.
- Expansion is additive by default.
- Cancellation is conservative.
- Material reframing requires approval.

## Inter-Agent Isolation

- Strict inter-agent isolation is a founder-level architectural invariant.
- Agents do not see each other’s intermediate work.
- Convergence, branch changes, and replanning happen centrally at the orchestrator/specification layer rather than through agent-to-agent sharing.

## Lane Interpretation

- Lanes are implementation and hardening tracks.
- A lane may constrain live scope locally.
- A lane may not redefine founder intent, the overall product vision, or the system’s long-horizon boundaries.
- Retrieval lanes are subsystem-hardening tracks only. They do not replace the full-system doctrine.

## UI Stance

- The final product requires a first-class analyst-facing UI.
- Near-term capstone and remediation deliveries may use rough terminal or operator surfaces.
- During the current phase, backend correctness, trustworthy provenance, and control-plane discipline outrank polish.

## Boundary To Live Operational Truth

Founder intent answers:

- what Keystone is for
- which runtime family it should prefer
- what interaction model it should follow
- what architectural invariants must remain intact

Live operational truth answers:

- which commit and worktree are currently authoritative
- which lane is cleared, blocked, pending, or unauthorized
- what the next authorized action is
- what write set is currently approved

Use the live control plane for operational truth:

- `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
- `audit/remediation/control-plane/ACTIVE-HANDOFF.md`

## Boundary To Provenance And History

Founder intent is not:

- a chronology ledger
- a packet index
- a record of historical blocked candidates
- a record of local dirty-state reality

Use provenance layers for history and evidence:

- `SESSION-LOG.md`
- retrospective lineage and review ledgers
- packet families and review indexes
