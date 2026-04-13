# Information Architecture

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
- `Library`
- `Review`
- `Settings`

### Notes

- `Research` is the default home.
- `Review` should be contextual until a real multi-user reviewer workflow exists. If it is not real yet, keep it as a badge/filter inside `Analyses`.
- `Settings` stays secondary.

## Screen Layout

### Default layout

- Left rail: recent analyses, pinned files, pending reviews.
- Center: main working surface.
- Right drawer: collapsible context pane for files, outputs, and later deeper run detail.

### Center-surface states

- Empty state: prompt examples, file attach, mic, default depth selector.
- Plan preview: what Keystone plans to test, expected outputs, estimated effort, warnings.
- Running: stage timeline, workstream updates, wait states.
- Checkpoint: review card with approve/refine/reject actions.
- Complete: `Brief`, `Evidence`, `Sources`, `Outputs`, `Quality`.

## Onboarding

## Empty-state message

Lead with:

`Start with the decision you need to make.`

## First-run guidance

- Show 3 analyst-style example prompts.
- Default to `Standard` with `Recommended for most questions`.
- Keep `Attach files` and `Mic` visible immediately.
- Add an honest note:
  - `Best for sourced external research and uploaded documents. Extended research options are experimental.`

## First successful launch tour

Use a four-step lightweight tour:

1. `Research Plan`
2. `Research`
3. `Review checkpoint`
4. `Brief`

## Run Lifecycle Statuses

Recommended user-facing statuses:

- `Draft`
- `Running`
- `Needs review`
- `Complete`
- `Stopped`
- `Failed`
- `Experimental`

Recommended supporting banners:

- `Governed run`
- `Experimental bypass`
- `Mixed / non-canonical`
- `Docs / demo only`

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
- No internal IDs or raw logs

### Advanced analyst mode

- Plan details
- checkpoint details
- source and evidence drill-down
- excluded content and degraded-state visibility
- experimental controls with warnings

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
