# Reviewer Flow Spec

Authoritative runtime anchor: `65a612d`  
Docs workspace mode: docs-only  
Related docs:

- [RUN-STATE-CONTRACT.md](./RUN-STATE-CONTRACT.md)
- [RUN-INSPECTOR-AND-DEV-MODE.md](./RUN-INSPECTOR-AND-DEV-MODE.md)

## Purpose

This spec defines the exact reviewer-flow contract the UI may describe now, using only the review surfaces the repo actually proves today:

- DB-backed HITL gate state
- five HITL REST endpoints
- gate item schemas for `post_specification` and `post_deliberation`
- current helper semantics for `approved`, `modified`, and `rejected`

It does not assume:

- a separate reviewer web app already exists
- multi-user assignment or inbox routing
- automatic application of requested changes
- a unified live event stream for gate creation, decision, and resume

## Relationship To Plan Preview

Freeze one pre-run boundary across the package:

- `Preview plan` / `Plan ready` is analyst confirmation, not reviewer state.
- If a `post_specification` gate is configured, the next screen after plan confirmation is `Needs review`.
- That `post_specification` checkpoint is the first real runtime pause.
- If no pre-run gate is configured, the run moves from `Plan ready` directly to `Running`.
- Do not merge analyst confirmation and reviewer decision into one step.

## Current Reviewer Truth Surfaces

### Endpoints

| Endpoint | Use |
|---|---|
| `GET /api/hitl/gates` | List pending gates, optionally filtered by `engagement_id` |
| `GET /api/hitl/gates/{engagement_id}` | List all gates for one run |
| `GET /api/hitl/gates/{gate_id}/detail` | Load a full checkpoint with items and decision |
| `POST /api/hitl/gates/{gate_id}/decision` | Submit `approve`, `modify`, or `reject` |
| `POST /api/hitl/gates` | Pipeline-only creation path |

### State machine

| Gate status | Meaning |
|---|---|
| `pending` | Waiting for review |
| `approved` | Approved and resolved |
| `modified` | Changes requested and resolved |
| `rejected` | Stopped and resolved |

Terminal states are final. The current service rejects a second decision on a resolved gate.

## Reviewer Flow

### 1. Checkpoint appears

Entry conditions:

- the pipeline creates a `post_specification` or `post_deliberation` gate
- the gate is stored with `status == pending`

UI state:

- analysis lifecycle becomes `Needs review`
- stage timeline shows `Waiting for review`
- badge `Waiting for human` appears

For `post_specification`, this transition can happen before any L1 research begins.

Current backing:

- `GET /api/hitl/gates`
- `GET /api/hitl/gates/{engagement_id}`

### 2. Reviewer opens checkpoint detail

Entry conditions:

- user opens a pending or resolved gate from the analysis page

UI sections and backing:

| UI section | Backing now |
|---|---|
| `Why Keystone paused` | gate type plus the current stage context from the analysis page |
| `What needs a decision` | gate status and gate type |
| `Materials for review` | `items` array from gate detail |
| `Review notes` | local input plus saved `decision.reasoning` when resolved |
| `Decision summary` | `decision`, `resolved_at`, `resolved_by` when present |

Current detail source:

- `GET /api/hitl/gates/{gate_id}/detail`

### 3. Reviewer chooses an action

Buttons and current action mapping:

| UI action | API call | Payload shape |
|---|---|---|
| `Approve and continue` | `POST /api/hitl/gates/{gate_id}/decision` | `{ "decision": "approve", "decided_by": "...", "reasoning": "..." }` |
| `Request changes` | `POST /api/hitl/gates/{gate_id}/decision` | `{ "decision": "modify", "decided_by": "...", "modifications": { ... }, "reasoning": "..." }` |
| `Stop analysis` | `POST /api/hitl/gates/{gate_id}/decision` | `{ "decision": "reject", "decided_by": "...", "reasoning": "..." }` |

Current validation rules:

- `modify` requires a non-empty `modifications` object
- resolved gates reject further decisions

### 4. System resolves the checkpoint

| Resolution | Current runtime consequence | UI treatment |
|---|---|---|
| `approved` | Pipeline resumes | Show `Approved`; remove `Waiting for human` |
| `modified` | Current helper treats `patch_applied` as false and does not auto-apply changes | Show `Modified, not auto-applied`; do not imply the run was edited in place |
| `rejected` | Pipeline halts | Treat run as `Stopped` rather than `Complete` |

## Checkpoint Types And Materials

### Post-specification checkpoint

Gate type:

- `post_specification`

Materials currently supported:

- `issue_tree`
- `agent_config`
- optional `sprint_contract`

What the reviewer can honestly inspect now:

- issue-tree structure
- planned workstreams/agent configs
- optional sprint contract if the pipeline provided one
- the first real runtime checkpoint before research begins when Gate 1 is enabled

What must stay provisional:

- plan diff views against a previous spec version
- true pre-run plan-preview persistence
- automated application of requested plan changes

### Post-deliberation checkpoint

Gate type:

- `post_deliberation`

Materials currently supported:

- `confidence_map`
- optional `divergence_points`

What the reviewer can honestly inspect now:

- confidence-tier distribution
- insufficient-evidence and gap items
- disagreement summary when divergence points are present

What must stay provisional:

- claim-to-passage support review
- fetched-document/source locator review
- reviewer edits applied directly back into claim state

## Reviewer Screen Contract

### Analyst mode

Show:

- checkpoint title and status
- why the run paused
- plain-language material summaries
- action buttons
- saved decision summary after resolution

Hide:

- raw gate IDs by default
- raw JSON item payloads
- internal DB semantics

### Advanced mode

Show:

- full gate-type label
- all review items with structured summaries
- modification keys summary after a `modify` decision
- timestamp, resolver, and reasoning

Hide:

- raw event plumbing
- prompt or credential data

### Dev mode

Show:

- full gate JSON from the detail endpoint
- item payloads without truncation
- decision payload and terminal status
- exact file or artifact references when gate items point at them

Still hide:

- secrets and credentials

## Reviewer Status Copy Contract

| Status chip | Exact meaning now |
|---|---|
| `Needs review` | The gate exists and `status == pending`. |
| `Approved` | A reviewer submitted `approve`. |
| `Changes requested` | A reviewer submitted `modify`. |
| `Stopped` | A reviewer submitted `reject`. |

Supporting warnings:

- `Requested changes are saved as review instructions. They are not auto-applied to this run in the current phase.`
- `This is a real pause state. The analysis does not continue until the checkpoint resolves.`
- `For Gate 1, this pause can happen before research begins.`

## Event And Timeline Limits

The UI must not overclaim reviewer-flow streaming.

Current reality:

- HITL event classes exist
- `gate.py` can append gate events to an optional collector
- the current pipeline path does not pass that collector through
- `ReviewDecisionSubmitted` is not emitted on the authoritative runtime path

UI consequence:

- reviewer state should be driven by HITL endpoints
- do not promise that the main event timeline will show a fully faithful gate-by-gate stream
- a later websocket or unified event bridge is a separate implementation unlock

## Retrieval-Lock Boundaries

Reviewer flow itself does not need retrieval seam lock, but review materials that imply source proof do.

Safe now:

- issue tree review
- planned workstream review
- confidence-map review
- divergence review
- artifact/file availability review

Must stay provisional until retrieval seams lock:

- fetched-document viewer inside the checkpoint
- exact passage support panes
- source-scope controls that imply governed full-document evidence
- any checkpoint language that treats snippet discovery as passage-level support

## Non-Negotiable Honesty Rules

- Do not present `modify` as "Keystone updated the analysis" on the current runtime.
- Do not describe a separate reviewer app as if it already ships.
- Do not rely on event streaming for reviewer truth when the endpoint is the actual source of truth.
- Do not blur checkpoint review of confidence claims with full-document evidence review.
