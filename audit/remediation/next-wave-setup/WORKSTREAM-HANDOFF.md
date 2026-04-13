# Next-Wave Setup Workstream Handoff

Date: 2026-04-13  
Mode: docs-only controller packaging  
Status: corrected setup-package candidate for later controller promotion review; core control-plane promotion intentionally deferred from this session

## Mission

Produce the missing post-Wave-4B authority/setup package required before any forward code lane may open, without mutating runtime code, without mutating the live control-plane authority docs, and without pretending the main workspace is a valid implementation lane.

## Executive Judgment

- The retrospective audit program is complete under the authoritative review ledger.
- The active forward hard stop remains real until a later controller reconcile promotes a controller-grade setup package into the live control plane.
- The only forward lane this package is willing to prepare is Retrieval MVP Lane D fetch:
  - purpose: gateway-owned governed fetch backends for article, filing, PDF, and paper retrieval
  - baseline: `65a612dc1400abbedcfbdda1f173cd72a3a90c06` (`65a612d`)
  - runtime truth anchor: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-4b` at `65a612d`
  - branch: `codex/retrieval-mvp-fetch`
  - worktree: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch`
- Parser Lane E, L1 integration Lane F, UI implementation, benchmark acceptance claims, Wave 5, and calibration remain blocked.

## Artifact Naming Decision

The control plane requires a post-Wave-4B next-wave authority/setup artifact, but it does not pin an authoritative filename yet.

This package names the artifact:

- file: `audit/remediation/next-wave-setup/NEXT-WAVE-SETUP-ARTIFACT.md`
- title: `Post-Wave-4B Retrieval Fetch Setup Artifact`

This avoids falsely implying that a Wave 5 or calibration lane is already authorized.

## Authority Order

Read in this order:

1. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
2. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
3. `audit/remediation/control-plane/RETROSPECTIVE-REVIEW-LEDGER.yaml`
4. `audit/remediation/runs/wave-4b/candidate-65a612d-clearance.md`
5. `audit/remediation/retrieval-mvp/WORKSTREAM-HANDOFF.md`
6. `audit/remediation/retrieval-mvp/MVP-RETRIEVAL-REQUIREMENTS.md`
7. `audit/remediation/retrieval-mvp/ARCHITECTURE-DECISIONS.md`
8. `audit/remediation/retrieval-mvp/RETRIEVAL-MVP-ARCHITECTURE-MEMO.md`
9. `audit/remediation/retrieval-mvp/RETRIEVAL-MVP-SEAM-CONTRACT.md`
10. `audit/remediation/retrieval-mvp/RETRIEVAL-MVP-MIGRATION-CHECKLIST.md`
11. `audit/remediation/retrieval-mvp/BENCHMARK-AND-ACCEPTANCE.md`
12. `audit/remediation/retrieval-mvp/RUNTIME-LANE-UNLOCK-MEMO.md`
13. `audit/remediation/retrieval-mvp/SETUP-ARTIFACT-CHECKLIST.md`
14. `audit/remediation/retrieval-mvp/WORKTREE-AND-REVIEW-GATE-CHECKLIST.md`
15. `audit/remediation/retrieval-mvp/IMPLEMENTATION-LANES.md`
16. `audit/remediation/retrieval-mvp/RISK-REGISTER.md`
17. `graphify-out/GRAPH_REPORT.md`
18. `audit/remediation/next-wave-setup/NEXT-WAVE-SETUP-ARTIFACT.md`
19. `audit/remediation/next-wave-setup/ALLOWED-WRITE-SET.md`
20. `audit/remediation/next-wave-setup/REVIEW-AND-GATE-CHECKLIST.md`
21. `audit/remediation/next-wave-setup/BACKEND-TRUTH-MATRIX-SPEC.md`
22. `audit/remediation/next-wave-setup/LIVE-PROBE-EVIDENCE-SCHEMA.md`
23. `audit/remediation/next-wave-setup/BACKEND-REALITY-GATE.md`
24. `audit/remediation/next-wave-setup/TOOL-CONTRACT-GATE.md`
25. `audit/remediation/next-wave-setup/GOVERNANCE-GATE.md`
26. `audit/remediation/next-wave-setup/RUN-CONTRACT-GATE.md`
27. `audit/remediation/next-wave-setup/CONTROLLER-UNLOCK-WORKTREE-PROVENANCE-GATE.md`
28. `audit/remediation/next-wave-setup/LANE-CHOICE-RATIONALE.md`
29. `audit/remediation/next-wave-setup/SESSION-PROMPTS.md`

If a lower-order file conflicts with the control plane, the control plane wins. The setup package is explicitly subordinate to `CONTROL-PLANE-STATE.yaml` and `ACTIVE-HANDOFF.md`.

## Current Decision Boundary

- Immediate next work item in this session: correct the docs-only setup package and re-review it adversarially.
- First forward code lane after a later promotion session: Retrieval MVP Lane D fetch only.
- This package is not self-promoting and does not lift the hard stop by narrative intent.
- Later controller promotion is contingent on the required docs-only gate artifacts in this package existing and remaining `CLEARED`.
- The supporting retrieval packet remains subordinate planning material and cannot self-authorize a forward lane.
- The main workspace stays docs-only until a later controller reconcile says otherwise.

## Package Map

- `NEXT-WAVE-SETUP-ARTIFACT.md`: controller-grade setup artifact for the narrow fetch lane
- `ALLOWED-WRITE-SET.md`: exact allowed write set, frozen surfaces, and indirect-scope fences
- `REVIEW-AND-GATE-CHECKLIST.md`: mandatory gate-artifact, candidate-review, and clearance requirements
- `BACKEND-TRUTH-MATRIX-SPEC.md`: closed backend-reality matrix requirements plus the `65a612d` baseline matrix
- `LIVE-PROBE-EVIDENCE-SCHEMA.md`: required probe fields for later live/provider-authenticated fetch proof
- `BACKEND-REALITY-GATE.md`: docs-only gate artifact for backend-reality hardening
- `TOOL-CONTRACT-GATE.md`: docs-only gate artifact for typed retrieval-contract hardening
- `GOVERNANCE-GATE.md`: docs-only gate artifact for scope and governance hardening
- `RUN-CONTRACT-GATE.md`: docs-only gate artifact for runtime-truth and invocation-contract hardening
- `CONTROLLER-UNLOCK-WORKTREE-PROVENANCE-GATE.md`: docs-only gate artifact for baseline/worktree/provenance hardening
- `LANE-CHOICE-RATIONALE.md`: why Lane D remains next and why broader lanes stay blocked
- `SESSION-PROMPTS.md`: exact follow-on prompts for later promotion, implementation, and review sessions

## Notes For The Next Controller Session

- Treat `65a612d` in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-4b` as the only forward implementation anchor until a later cleared code commit exists.
- Do not rename this package into `WAVE-5-SETUP.md` unless the control plane explicitly advances the program into a true Wave 5 authority state.
- Promote nothing unless every required gate artifact in this package still exists, is current for the reviewed snapshot, and says `CLEARED`.
- If the artifact is promoted, authorize only Retrieval MVP Lane D fetch and nothing broader.
