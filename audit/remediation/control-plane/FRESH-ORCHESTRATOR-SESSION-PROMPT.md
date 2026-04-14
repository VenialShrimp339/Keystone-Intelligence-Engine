Use this in a brand-new Codex app session when you want a fresh controller/orchestrator to take over from disk without relying on any prior chat history.

```md
You are a fresh controller/orchestrator session for the Keystone Intelligence Engine.

Use GPT-5.4 xhigh fast.

Hard rules:
- Treat disk state as authoritative.
- Do not trust prior chat history, pasted summaries, or remembered context.
- The main workspace stays docs-only unless the live control plane explicitly authorizes a code lane.
- Before mutating any live controller doc, obey the lease-takeover rule in `CONTROL-PLANE-STATE.yaml`.
- Do not reopen the paused heartbeat/automation in this session.
- Do not reopen Retrieval MVP Lane D.
- Do not reopen Lane H coding just because its worktree exists.
- Do not start SEC / EDGAR work, Browser Use implementation, UI work, benchmark acceptance, Wave 5, or calibration.

Read in this exact order:
1. `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
2. `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/ACTIVE-HANDOFF.md`
3. `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/FRESH-ORCHESTRATOR-BOOTSTRAP.md`
4. `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/CURRENT-STATE.md`
5. `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/project-state-reconcile/MVP-REQUIRED-BUILDOUT.md`
6. `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/WORKSTREAM-HANDOFF.md`
7. `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/AUTHORITY-EXPANSION-DECISION.md`
8. `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/NEW-LANE-SETUP-ARTIFACT.md`
9. `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/ALLOWED-WRITE-SET.md`
10. `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/TOOL-CONTRACT-CHANGES.md`
11. `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/PROMOTION-DECISION.md`
12. `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-review-synthesis.md`
13. `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-blocked-or-cleared-checkpoint.md`

Current live truth you should expect to confirm from disk:
- Lane H is cleared at `93a5ca8406dc0c46c96f0c6285f56ec0ab6601ea`
- that is the current runtime truth for governed article/PDF fetch
- no retrieval code lane is currently authorized
- the next controller-priority workstream is docs-only `Professor-Demo Narrow Lane E Setup`

Your first job:
- verify whether that live truth is coherent on disk

If coherent, your only milestone this session is:
- create the docs-only narrow Lane E setup package rooted from `93a5ca8406dc0c46c96f0c6285f56ec0ab6601ea`

The narrow Lane E setup package must stay limited to:
- deterministic parse for article/PDF path
- evidence normalization
- source-shaped locators / parse confidence handling if needed
- no SEC / EDGAR
- no Lane F integration
- no UI
- no benchmark acceptance claims

Write the package under:
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-parse/`

Expected package files:
- `WORKSTREAM-HANDOFF.md`
- `NEW-LANE-SETUP-ARTIFACT.md`
- `ALLOWED-WRITE-SET.md`
- `REVIEW-AND-GATE-CHECKLIST.md`
- `LANE-CHOICE-RATIONALE.md`
- `SESSION-PROMPTS.md`

Use read-only subagents for:
1. scope/write-set design
2. stale-doc/conflict detection
3. MVP usefulness / professor-demo path sanity check

If you only create docs, you may make one docs-only commit.

Stop with:
- whether the live disk state was coherent
- exact files changed
- exact commit created if any
- the exact next review sessions that should be launched against the Lane E package
```
