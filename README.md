# The Keystone Intelligence Engine

Spec-driven, multi-agent consulting research system for Keystone Group.

## Start Here

Read these first:

1. [AUTHORITY-INDEX.md](AUTHORITY-INDEX.md)
2. [SESSION-STANDARD.md](SESSION-STANDARD.md)
3. [audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml](audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml)
4. [audit/remediation/control-plane/ACTIVE-HANDOFF.md](audit/remediation/control-plane/ACTIVE-HANDOFF.md)

## Current Truth Snapshot

- Historical implementation remains cleared through Wave 4B at `65a612d`.
- Current cleared runtime truth anchor: Lane H commit `93a5ca8406dc0c46c96f0c6285f56ec0ab6601ea` in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface`.
- Treat runtime truth as pinned commit plus worktree path. Path alone is not enough.
- No retrieval code lane is currently authorized from the main control plane.
- The tracked narrow Lane E setup package exists at `c9c7a1596d68171881023ce832412b74b2ee5c7c`.
- Cleared pre-promotion Lane E reviews are persisted on the current branch at `8e002a77e149aba86ef5f0520e16e58b5647a551`.
- Live control-plane promotion of that package is still pending.
- The main workspace is in docs/provenance scope for this session. That is a scope policy, not a cleanliness claim.

## Canon Stack

| Layer | Use |
|---|---|
| `AUTHORITY-INDEX.md` | front door and doc routing |
| `SESSION-STANDARD.md` | shared Claude/Codex session discipline |
| control-plane pair | live operational truth |
| `FOUNDER-INTENT-DOCTRINE.md` | stable founder doctrine |
| `JACK-ARCHITECTURAL-DIRECTIVES.md` + `CAPSTONE-PLAN-v2.md` | detailed founder intent and architecture plan |
| `CURRENT-STATE.md` | summary-only current state |
| `SESSION-LOG.md` | provenance-only history |

## Project Narrative

- Founder-intent doctrine: [FOUNDER-INTENT-DOCTRINE.md](FOUNDER-INTENT-DOCTRINE.md)
- Founder source docs: [JACK-ARCHITECTURAL-DIRECTIVES.md](JACK-ARCHITECTURAL-DIRECTIVES.md), [CAPSTONE-PLAN-v2.md](CAPSTONE-PLAN-v2.md)
- Current state summary: [CURRENT-STATE.md](CURRENT-STATE.md)
- Gap map: [audit/remediation/project-state-reconcile/MVP-REQUIRED-BUILDOUT.md](audit/remediation/project-state-reconcile/MVP-REQUIRED-BUILDOUT.md)
- Historical narrative: [docs/architecture-and-evolution.md](docs/architecture-and-evolution.md) as derived/professor history only
- Older code-structure snapshot: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Scope Note

This landing page is for truthful orientation.
It does not certify MVP completeness, runtime readiness, or lane authorization by itself.
For those questions, use the control-plane pair.
