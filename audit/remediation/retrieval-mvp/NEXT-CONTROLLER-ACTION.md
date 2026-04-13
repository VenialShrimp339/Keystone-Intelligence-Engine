# Next Controller Action

Date: 2026-04-13

## Decision To Carry Forward

- Use `audit/remediation/retrieval-mvp/LANE-D-AUTHORITY-RESOLUTION.md` as the controller answer for candidate `f1af7df`.
- Treat the Lane D authority question as resolved for this session.
- Do not authorize more Lane D coding from the current worktree.

## Immediate Status

- Controller recommendation: `ESCALATE_TO_NEW_LANE`
- Current Lane D answer on `document_fetch`: `NO`
- SEC `403` ordering: separate venue question to revisit only after tool-surface authority is settled
- Candidate `f1af7df`: remains `BLOCKED`

## Required Next Step

Open a new docs-only controller lane for tool-surface authority expansion if article/PDF canonical fetch remains mandatory for Retrieval MVP.

That new controller lane must decide and document:

1. whether article/PDF canonical fetch gets a new callable tool surface such as `document_fetch`, or
2. whether article/PDF fetch is deferred and the Retrieval MVP scope is narrowed to existing tool names only

Do not let that decision be made implicitly inside `src/keystone/gateway/servers.py` again.

## Minimum Scope Of The New Lane

If the controller wants a new callable tool surface later, the new lane must own:

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

The later implementation lane would also need explicit ownership of these code-contract surfaces:

- `src/keystone/tool_names.py`
- `src/keystone/specification/prompts/task_generation.md`
- `src/keystone/specification/task_generator.py`
- `src/keystone/models/tasks.py` if tool-membership validation is tightened

## If The Controller Refuses A New Lane

Then the fallback is to re-scope Lane D downward:

- remove `document_fetch` as a registry/auth surface
- keep Lane D on `edgar_filings`, `paper_search`, and fetch-local audit/identity work only
- leave Exa and Brave discovery-only
- explicitly defer generic article/PDF canonical fetch

That fallback is a Retrieval MVP scope reduction and should be recorded as such. It should not be smuggled in as a small Lane D patch.

## Review Hygiene Note

The requested candidate file `candidate-f1af7df-review-synthesis.md` was absent from the reviewed packet. The authority decision above relied on the blocked checkpoint, adversarial review, and second-opinion files that were present.

Before any future clearance attempt, the required review-synthesis artifact should exist again.
