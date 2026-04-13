# Chat Surface And Controls

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
- primary `Start analysis` button
- `More` menu

### Suggested top row

`Quick | Standard | Extended | Attach files | Mic | More`

Notes:

- `Standard` is the default and recommended option.
- Do not lead with model names.
- Do not put experimental deep research in the default row.

## Plan Preview Before Execution

Before heavy work starts, Keystone should return a `Research Plan` card with:

- what it will test
- likely workstreams
- expected outputs
- expected effort
- warnings and limitations

Primary actions:

- `Start`
- `Refine`
- `Make this quicker`

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

Place `Experimental deep research` behind `More options` with a clear warning:

`Experimental. May bypass governed retrieval controls and should not be treated as canonical MVP evidence.`

## Default Vs Advanced Controls

| Control | Default | Advanced | Dev only |
|---|---|---|---|
| Depth (`Quick/Standard/Extended`) | Yes | Yes | Yes |
| Attach files | Yes | Yes | Yes |
| Mic dictation | Yes | Yes | Yes |
| Start / Refine | Yes | Yes | Yes |
| Research plan details | Summary only | Full | Full |
| Experimental deep research | No | Yes, with warning | Yes |
| Engagement-type override | No | Yes | Yes |
| Model choice | No | Rarely | Yes |
| Evaluation intensity | No | Yes | Yes |
| Raw run IDs / debug traces | No | No | Yes |

## File Upload

File upload is first-class.

Recommended behavior:

- files appear as pills immediately below the composer
- each file shows a truthful status:
  - `Attached to this analysis`
  - `Used in run`
  - `Not indexed`
  - `Ignored`
- the right drawer should show the full file list and later extraction metadata

Do not bury file upload in settings.

## Speech-To-Text

Speech-to-text is first-class, but only as prompt dictation in MVP UI scope.

Recommended behavior:

- mic icon in the composer
- transcribe to editable text before launch
- no always-on voice mode
- no implied meeting intelligence unless later explicitly built

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

Advanced tabs:

- `Plan`
- `Tasks`
- `Citations`
- `Gates`
- `Artifacts`

## Honesty Rules

- Every run must display whether it is governed, experimental bypass, mixed, or docs/demo-only.
- Citation UI must distinguish source discovery from stronger support levels.
- If only part of the run was evaluated, say so directly.
- If the deliverable filtered out tasks or claims, expose that in the surface.
