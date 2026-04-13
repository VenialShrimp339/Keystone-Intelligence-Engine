# Live Probe Evidence Schema

Date: 2026-04-13  
Applies to: Retrieval MVP Lane D live/provider-authenticated probe proof

## Purpose

Define the minimum evidence record for every successful Lane D fetch probe.

This schema exists to make backend-reality proof auditable and to stop mock-shaped, stub-shaped, or narrative-only evidence from being mistaken for real canonical fetch support.

## Required Header Fields

Every `candidate-<commit>-live-fetch-review.md` must record:

- reviewer
- reviewed snapshot
- approved setup artifact
- candidate commit
- candidate parent anchor
- worktree path
- branch
- exact runtime invocation contract

## Required Probe Records

At minimum, the live-fetch review must contain one probe record for each canonical fetch surface:

- article fetch
- EDGAR filing fetch
- PDF fetch
- paper fetch

If any surface lacks a qualifying successful probe, the review must mark that surface `BLOCKED` and the candidate must stop in a blocked checkpoint instead of clearing.

## Required Fields For Every Successful Probe

Each successful probe record must include:

- surface
- invocation surface
- tool name
- backend/server
- client implementation or transport
- canonical URL
- content hash
- coverage status
- persisted artifact location or byte count
- candidate commit
- candidate parent anchor
- approved setup artifact
- worktree path
- whether the run used live provider access or replay
- whether `MockMCPClient` was used
- whether stub fallback was used
- verdict

## Required Rules

- `MockMCPClient` must be `false` for every successful canonical fetch probe.
- Stub fallback must be `false` for every successful canonical fetch probe.
- Replay may be recorded, but replay alone does not clear a canonical fetch surface for Lane D. A surface clears only with live or provider-authenticated fetch proof.
- Exa and Brave may appear only as discovery-support evidence, not as canonical fetch proof.
- A registry entry, tool docstring, or unit-test-only surface is not a successful probe.

## Suggested Markdown Shape

Use one section per probe:

### `<surface>`

- Verdict: `CLEARED` or `BLOCKED`
- Invocation surface:
- Tool name:
- Backend/server:
- Client implementation or transport:
- Canonical URL:
- Content hash:
- Coverage status:
- Persisted artifact location or byte count:
- Candidate commit:
- Candidate parent anchor:
- Approved setup artifact:
- Worktree path:
- Live provider access or replay:
- `MockMCPClient` used:
- Stub fallback used:
- Notes:

## Failure Rule

If any required field is missing, ambiguous, or contradicted by the backend truth matrix, the live-fetch review is not clearable.
