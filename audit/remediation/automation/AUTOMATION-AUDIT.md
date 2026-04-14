# Automation Audit

## Scope

This memo records the audit of the `overnight-mvp-push` heartbeat automation after the hardened controller contract was added.

The automation itself lives at:

- `/Users/jackriddle/.codex/automations/overnight-mvp-push/automation.toml`

The durable repo-backed rules it reads live under:

- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/automation/`

## What Was Reviewed

- the saved heartbeat TOML
- the overnight controller contract
- the overnight state machine
- the review-stack standard
- the live control plane
- the active handoff
- the MVP buildout map
- the older agent-team guidance

## High-Risk Findings That Were Fixed

1. The first hardened draft could skip the live Lane H state and jump too early into Lane E planning.
   Fix: the state machine now includes explicit Lane H implementation, review, and reconcile stages, and the prompt now loads the active Lane H authority stack from disk before acting.

2. The first hardened draft still had a precedence ambiguity with the live control plane's generic continuous-checkpoint language.
   Fix: the controller contract now says the control plane wins on lane authority and baseline truth, but stricter pacing and stop rules in the overnight contract still win for this automation.

3. The first hardened draft did not explicitly load the active lane authority packet or lane-specific review requirements.
   Fix: the contract and the saved automation prompt now require the current active lane packet stack, and the review standard now names mandatory Lane H, Lane E, and Lane F review checks.

4. The first hardened draft did not explicitly allow the final professor-demo handoff package.
   Fix: the saved automation prompt now includes the professor-demo handoff package as a valid milestone.

## Current Safety Posture

The current model is:

- one heartbeat controller on a fixed thread
- one milestone per wake
- zero or one code writer
- read-only review fanout
- mandatory blocker file plus self-pause behavior on hard stops

This is materially safer than the earlier loose heartbeat prompt.

## Remaining Limits

This automation is still not a hard-guarantee workflow engine.

Known limits:

- it depends on the Codex app remaining open and able to run
- it is not a durable queue or exact-once scheduler
- it still relies on the model correctly following disk authority and the written contract
- it is designed to reach at most `professor_demo_ready_on_article_pdf_path`, not claim full MVP clearance

## Current Recommendation

- keep the schedule at hourly
- keep the automation paused until you intentionally start the overnight run
- treat the first overnight milestone as a Lane H stale-state reconcile if the control plane is still behind the cleared Lane H packet
- keep SEC, Browser Use implementation, advanced retrieval, UI runtime, and all broader product work deferred
