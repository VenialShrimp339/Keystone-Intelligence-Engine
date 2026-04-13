# Chat Surface And Controls

See the canonical screen-by-screen copy in [SCREEN-SPECS.md](./SCREEN-SPECS.md).

## Recommended Surface

The top-level experience should feel like a premium analyst workbench:

- familiar bottom composer
- left sidebar for history
- center conversation and run updates
- right pane for durable outputs, files, and later inspector detail

The chat surface is the launch and summary layer. The run record remains the truth layer.

## Composer Layout

### Always visible

- multi-line prompt box
- `Attach files`
- `Mic`
- depth selector
- primary `Preview plan` button
- `Advanced` button

### Suggested top row

`Quick | Standard | Extended | Attach files | Mic | Advanced`

Notes:

- `Standard` is the default and recommended option.
- Do not lead with model names.
- Do not put experimental deep research in the default row.
- Use the exact helper under `Standard`: `Recommended for most questions`.
- Keep the composer placeholder exact: `What decision are you trying to make? Include context, constraints, and what a useful answer should cover.`

## Plan Preview Before Execution

Before heavy work starts, Keystone should return a `Research Plan` card with:

- what it will test
- likely workstreams
- expected effort
- expected outputs
- warnings and limitations

Semantic rule:

- `Plan ready` is analyst confirmation, not a HITL state.
- If a `post_specification` gate is configured, the first real runtime pause is the review checkpoint immediately after plan confirmation.
- If no pre-run gate is configured, the run moves directly into `Running`.

Primary actions:

- `Start analysis` when no pre-run checkpoint is required
- `Continue to review` when a `post_specification` checkpoint is required
- `Edit request`
- `Make this quicker`
- `Show full plan details`

This keeps the UI familiar while preserving the real plan/review character of Keystone.

## Research Depth Controls

## Default labels

- `Quick`: faster scan, lighter sourcing
- `Standard`: balanced research and review
- `Extended`: broader search, slower, more exhaustive

## Rules

- Only one depth control should be visible by default.
- Keystone may recommend a depth, but the labels stay plain-English.
- Depth is not the same thing as experimental deep research bypass.

## Experimental mode handling

Place `Use experimental deep research` behind `Advanced controls` with a clear warning:

`Experimental. May bypass governed retrieval controls and should not be treated as canonical MVP evidence.`

## Default Vs Advanced Controls

| Control | Default | Advanced | Dev only |
|---|---|---|---|
| Depth (`Quick/Standard/Extended`) | Yes | Yes | Yes |
| Attach files | Yes | Yes | Yes |
| Mic dictation | Yes | Yes | Yes |
| `Preview plan` / next-step action | Yes | Yes | Yes |
| Research plan details | Summary only | Full | Full |
| Use experimental deep research | No | Yes, with warning | Yes |
| Analysis type override | No | Yes | Yes |
| Model choice | No | Rarely | Yes |
| Evaluation intensity | No | Yes | Yes |
| Raw run IDs / debug traces | No | No | Yes |

## File Upload

File upload is first-class.

Recommended behavior:

- files appear as pills immediately below the composer
- each file shows a truthful status:
  - `Attached`
  - `Used in analysis`
  - `Not used`
  - `Could not read`
- the right-side `Outputs` pane should show the full file list and later extraction metadata
- use the exact warning:
  - `Uploads are attached to this analysis. Keystone may use extracted text where available. Some files may not be parsed or cited.`

Do not bury file upload in settings.

## Speech-To-Text

Speech-to-text is first-class, but only as prompt dictation in MVP UI scope.

Recommended behavior:

- mic icon in the composer
- transcribe to editable text before launch
- no always-on voice mode
- no implied meeting intelligence unless later explicitly built
- use the exact warning:
  - `Speech-to-text only fills the prompt box. It does not create a meeting recording or a saved transcript.`

Later-only candidate:

- `Record note` or `Record session` as a separate action from the mic button

## What The Chat Surface Should Show During A Run

- current stage
- elapsed time
- pending review state if blocked
- compact activity feed in plain English
- warnings for degraded or experimental behavior

Do not show:

- fake percentages
- fake agent-terminal streams
- green trust badges

## What The Chat Surface Should Show After A Run

Default tabs:

- `Brief`
- `Evidence`
- `Sources`
- `Outputs`
- `Quality`

If a tab has no real data, use a direct empty state rather than hiding it.

Advanced tabs:

- `Plan`
- `Tasks`
- `Citations`
- `Gates`
- `Artifacts`

## Honesty Rules

- Every run must display whether it is governed, experimental bypass, lineage unknown, or docs/demo-only.
- Reserve `Mixed / non-canonical` until lineage is explicitly recorded.
- Citation UI must distinguish source discovery from stronger support levels.
- If only part of the run was evaluated, say so directly.
- If the deliverable filtered out tasks or claims, expose that in the surface.
- The right-side pane may list only files and artifacts that actually exist. Do not imply polished exports or full-document packages beyond current outputs.
