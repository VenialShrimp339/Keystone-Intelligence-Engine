# Information Architecture

See also:

- [SCREEN-SPECS.md](./SCREEN-SPECS.md)
- [COPY-GUARDRAILS.md](./COPY-GUARDRAILS.md)

## Primary User Objects

- `Analysis`: the main user-visible run object.
- `Research Plan`: the plan preview produced before heavy work starts.
- `Workstream`: the user-facing label for backend task/agent work.
- `Review checkpoint`: the user-facing label for HITL gates.
- `Brief`: the primary markdown-style output.
- `Outputs`: downloadable workpapers and bundles.

## Top-Level Navigation

### Recommended primary nav

- `Research`
- `Analyses`
- `Settings`

### Notes

- `Research` is the default home.
- Keep files, outputs, and other artifact browsing contextual until a currently backed surface is promoted. Do not use `Library` as primary nav on the current package.
- `Review` should be contextual until a real multi-user reviewer workflow exists. If it is not real yet, keep it as a badge/filter inside `Analyses`.
- `Settings` stays secondary.

## Screen Layout

### Default layout

- Left rail: recent analyses, pinned files, pending reviews.
- Center: main working surface.
- Right pane: collapsible `Outputs` pane for files, available artifacts, and run-status context.

### Center-surface states

- `Research` home: prompt examples, file attach, mic, depth selector, `Preview plan`.
- Plan preview: `Research Plan`, expected workstreams, expected effort, expected outputs, warnings, and analyst confirmation before the next step.
- Review checkpoint: review card with `Approve and continue`, `Request changes`, `Stop analysis`.
- Running: stage timeline, real activity updates, truthful warnings, no fake percent complete.
- Complete: `Brief`, `Evidence`, `Sources`, `Outputs`, `Quality`.

### Canonical state stack

The main `Research` surface should move through one authoritative pre-run sequence:

`Research home -> Plan ready -> Needs review -> Running -> Complete`

Rules:

- `Plan ready` is the analyst confirmation step after `Preview plan`. It is not a HITL state.
- If a `post_specification` gate opens, `Needs review` is the first real runtime pause and it happens before `Running`.
- If no pre-run gate is required, the surface moves from `Plan ready` directly to `Running`.
- Do not merge analyst confirmation and reviewer decision into one state.

Supporting end states:

- `Stopped`
- `Failed`

## Onboarding

## Empty-state message

Lead with:

`Start with the decision you need to make.`

Support with:

`Describe the question, what good evidence looks like, and any constraints Keystone should respect.`

## First-run guidance

- Show 3 analyst-style example prompts.
- Default to `Standard` with `Recommended for most questions`.
- Keep `Attach files` and `Mic` visible immediately.
- Keep `Preview plan` as the first primary action. The next-step launch action only appears after plan preview.
- Add an honest note:
  - `Best for sourced external research and uploaded documents. Some attached content may not be parsed or cited.`

## First successful launch tour

Use a four-step lightweight tour:

1. `Research Plan`
2. `Review checkpoint`
3. `Research`
4. `Brief`

## Run Lifecycle Statuses

Recommended user-facing statuses:

- `Draft`
- `Plan ready`
- `Needs review`
- `Running`
- `Complete`
- `Stopped`
- `Failed`

Recommended supporting banners:

- `Governed run`
- `Experimental bypass`
- `Lineage unknown`
- `Docs / demo only`

Reserved future banner:

- `Mixed / non-canonical`

Recommended degraded-state badges:

- `Waiting for human`
- `Modified, not auto-applied`
- `Retrieval constrained`
- `Evaluation partial`
- `Fabrication halt`
- `Not rendered`
- `Deep research bypassed governance`

## Terminology Mapping

| Backend reality | User-facing label |
|---|---|
| Run | Analysis |
| Specification | Research Plan |
| Task / Agent | Workstream |
| HITL gate | Review checkpoint |
| CitationProcessor | Source check |
| Confidence map | Evidence strength |
| Evaluator | Quality review |
| Artifact | Output or Workpaper |

## Progressive Disclosure Model

### Default analyst mode

- Calm launcher
- Plain-language statuses
- Brief, evidence, source, outputs, quality tabs
- Right-side `Outputs` pane
- No internal IDs or raw logs

### Advanced analyst mode

- Full plan details
- Review-checkpoint details
- Source and evidence drill-down
- Excluded content and degraded-state visibility
- Experimental controls with warnings

### Dev mode

- raw event JSON
- alias/provenance internals
- audit traces
- retries, dead letters, tool latency
- model and fallback detail

## IA Constraints From Current Reality

- The current repo proves a HITL backend, not a committed reviewer web app.
- The current repo proves JSON/markdown run artifacts, not a productized history API.
- The current repo proves a markdown brief, not rich deliverables.
- Retrieval scope must stay honest about snippet discovery versus full-document evidence.
- The right pane can list files and artifacts that exist, but must not imply slides, polished exports, or a stable document package beyond current outputs.
