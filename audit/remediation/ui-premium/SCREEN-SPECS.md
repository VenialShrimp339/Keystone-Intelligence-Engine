# Screen Specs

Anchored to the last cleared runtime: `65a612d` in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-4b`

This spec defines the eventual MVP analyst surface without implying that Keystone already has governed full-document retrieval, a polished reviewer app, or rich deliverables beyond markdown and artifact bundles.

## Shared Frame

### Primary navigation

- `Research`
- `Analyses`
- `Settings`

Keep `Review` contextual until a real multi-user reviewer workflow exists. In MVP it should appear as a badge, filter, or linked state inside `Analyses`, not as a fully independent product area.
Keep files and outputs contextual until a currently backed artifact-browsing surface is promoted.

### Shared runtime banners

| Banner | Exact copy | When to show it |
|---|---|---|
| `Governed run` | `This analysis follows the current governed research path.` | When the run stayed inside the governed path. |
| `Experimental bypass` | `Experimental path. Do not treat this analysis as canonical MVP evidence.` | When the run used the bypass path. |
| `Lineage unknown` | `Keystone cannot prove this analysis stayed on one runtime path from the current record alone.` | When the current bundle or context cannot prove governed versus bypass lineage. |
| `Docs / demo only` | `This view describes the intended UI. It does not prove a productized runtime surface.` | In documentation demos or mocked examples. |

Reserved future banner:

- `Mixed / non-canonical`: keep reserved until one run record can explicitly prove mixed governed and bypass lineage.

### Shared degraded-state badges

| Badge | Exact copy |
|---|---|
| `Waiting for human` | `This analysis is paused until someone reviews the checkpoint.` |
| `Modified, not auto-applied` | `Review comments were saved, but changes were not applied automatically.` |
| `Retrieval constrained` | `Source support may be limited because governed retrieval did not fetch full documents.` |
| `Evaluation partial` | `Only part of this analysis completed quality review.` |
| `Fabrication halt` | `Citation checks stopped this analysis because a fabrication risk was detected.` |
| `Not rendered` | `The analysis finished, but no brief was rendered.` |
| `Deep research bypassed governance` | `This analysis used the experimental bypass path and is not canonical MVP evidence.` |

### Shared lifecycle statuses

| Status | Supporting copy |
|---|---|
| `Draft` | `Not started yet.` |
| `Plan ready` | `Keystone prepared a research plan and is waiting for your confirmation.` |
| `Needs review` | `Keystone is paused at a review checkpoint.` |
| `Running` | `Keystone is actively working through the plan.` |
| `Complete` | `Results are ready to review.` |
| `Stopped` | `This analysis was stopped before completion.` |
| `Failed` | `This analysis ended before results were ready.` |

### Authoritative pre-run sequence

Use one frozen pre-run sequence across the package:

`Research home -> Plan ready -> Needs review (if post-specification gate opens) -> Running`

Rules:

- `Preview plan` creates `Plan ready`.
- `Plan ready` is analyst confirmation only. It is not a HITL pause.
- If a `post_specification` checkpoint is configured, `Needs review` is the first real runtime pause.
- `Running` begins only after that checkpoint is approved, or immediately after `Plan ready` when no pre-run checkpoint exists.

### Stage labels shown during a run

- `Planning`: `Building the research plan and initial workstreams.`
- `Researching`: `Collecting source material and drafting findings.`
- `Source check`: `Checking citations, liveness, and obvious fabrication issues.`
- `Confidence review`: `Comparing claims, support, and unresolved gaps.`
- `Quality review`: `Running the current Phase 1 quality checks.`
- `Rendering`: `Preparing the brief and output bundle.`
- `Waiting for review`: `Paused until a person reviews this checkpoint.`

## 1. Research Home

### Exact labels

- Page title: `Research`
- Lead line: `Start with the decision you need to make.`
- Supporting line: `Describe the question, what good evidence looks like, and any constraints Keystone should respect.`
- Composer placeholder: `What decision are you trying to make? Include context, constraints, and what a useful answer should cover.`
- Example section label: `Try an example`
- Example prompt 1: `Assess how exposed our Q3 plan is to new EU tariff changes.`
- Example prompt 2: `Compare the top three acquisition targets for speed to market, integration risk, and expected synergies.`
- Example prompt 3: `Review the uploaded board materials and flag assumptions that need external validation.`

### Buttons and controls

- Depth label: `Depth`
- Depth options: `Quick`, `Standard`, `Extended`
- Default helper under `Standard`: `Recommended for most questions`
- File button: `Attach files`
- Speech-to-text button: `Mic`
- Advanced button: `Advanced`
- Primary button: `Preview plan`

### Empty states

- Main empty state: `Ask a research question or attach files to begin.`
- File tray empty state: `No files attached yet.`
- Outputs pane empty state: `Outputs will appear after you start an analysis.`

### Warnings and helper copy

- Input helper: `Best for sourced external research and uploaded documents. Some attached content may not be parsed or cited.`
- Disabled primary helper: `Enter a question or attach files to preview a plan.`
- Speech-to-text helper: `Speech-to-text only fills the prompt box. It does not create a meeting recording or a saved transcript.`

## 2. Plan Preview State

### Exact labels

- Status chip: `Plan ready`
- Card title: `Research Plan`
- Summary line: `Keystone prepared a research plan. Review the plan, warnings, and next step before you continue.`
- Section label: `Question`
- Section label: `What Keystone will test`
- Section label: `Expected workstreams`
- Section label: `Expected effort`
- Section label: `Expected outputs`
- Section label: `Warnings`

### Buttons

- Primary button when no pre-run checkpoint is required: `Start analysis`
- Primary button when a `post_specification` checkpoint is required: `Continue to review`
- Secondary button: `Edit request`
- Secondary button: `Make this quicker`
- Secondary button: `Show full plan details`

### Empty states

- Workstreams empty state: `No workstreams were generated for this plan yet.`
- Outputs empty state: `No output preview is available yet.`
- Fallback empty state: `Plan details are unavailable. Edit the request and try again.`

### Warnings

- Upload warning: `Uploaded files may be used where extraction succeeds. Some attached files may not be parsed or cited.`
- Retrieval warning: `Source support may rely on discovered snippets until governed retrieval expands.`
- Review warning: `If a post-specification review is configured, continuing opens a real review checkpoint before research begins.`

## 3. In-Progress Analysis State

### Exact labels

- Status chip: `Running`
- Title: `Analysis in progress`
- Summary line: `Keystone is running this analysis. Updates appear when a real stage or review state changes.`
- Timeline label: `Current stage`
- Activity section label: `Recent activity`
- Plan link label: `View plan`

### Buttons

- Button: `Open outputs`
- Button: `View plan`
- Button: `Advanced`

### Empty states

- Activity empty state: `No updates yet. This analysis is still starting.`
- Outputs pane empty state: `No outputs yet. Real artifacts will appear here as they are created.`

### Warnings

- General run warning: `Do not treat stage changes as percent complete. Keystone only shows real state transitions.`
- Retrieval warning: `Source support may still be limited even while the analysis is running.`

## 4. Review Checkpoint State

### Exact labels

- Status chip: `Needs review`
- Title: `Review checkpoint`
- Summary line: `Keystone paused this analysis for review before continuing. This can be the first runtime pause when Gate 1 is enabled.`
- Section label: `Why Keystone paused`
- Section label: `What needs a decision`
- Section label: `Materials for review`
- Section label: `Review notes`
- Notes placeholder: `Explain what should change or what you want reviewed more closely.`

### Buttons

- Primary button: `Approve and continue`
- Secondary button: `Request changes`
- Secondary button: `Stop analysis`

### Empty states

- Review materials empty state: `Review materials are unavailable. Open the current outputs and source details before deciding.`

### Warnings

- Review warning: `Requested changes are saved as review instructions. They may require a new plan or a follow-up run rather than editing this run in place.`
- Runtime warning: `This is a real pause state, not a summary card. The analysis will not continue until a decision is made.`

## 5. Completed Analysis State

### Exact labels

- Status chip: `Complete`
- Title: `Analysis complete`
- Summary line: `Results are ready. Review the brief alongside evidence, sources, outputs, and quality notes.`
- Primary tab: `Brief`
- Primary tab: `Evidence`
- Primary tab: `Sources`
- Primary tab: `Outputs`
- Primary tab: `Quality`

### Buttons

- Primary button: `New analysis`
- Secondary button: `Download bundle`
- Secondary button: `Open plan`

### Empty states

- `Brief` empty state: `No brief is available. This analysis finished without a rendered brief.`
- `Evidence` empty state: `No evidence summary is available for this analysis.`
- `Sources` empty state: `No source details are available for this analysis.`
- `Outputs` empty state: `No output bundle was produced for this analysis.`
- `Quality` empty state: `Quality review details are unavailable for this analysis.`

### Warnings

- Partial-evaluation warning: `Some results are shown without full quality review. Check the quality tab before relying on them.`
- Missing-output warning: `Some expected outputs are missing because part of the analysis did not complete or did not render.`

## 6. File Upload Behavior

### Exact labels

- Entry button: `Attach files`
- Drag state label: `Drop files to attach them to this analysis`
- Tray label: `Attached files`
- File status: `Attached`
- File status: `Used in analysis`
- File status: `Not used`
- File status: `Could not read`
- Inline action: `Remove`

### Behavior

- Files appear immediately below the composer after upload.
- Each file keeps a user-visible status for the full life of the analysis.
- Before the analysis starts, users can remove attached files.
- During and after the run, the same files appear in the right-side outputs pane with the same statuses.

### Empty states

- Tray empty state: `No files attached yet.`
- Pane empty state: `Attach files to include supporting materials with this analysis.`

### Warnings

- Attach warning: `Uploads are attached to this analysis. Keystone may use extracted text where available. Some files may not be parsed or cited.`
- Read failure warning: `We couldn't read this file. You can remove it or upload a different version.`

## 7. Speech-To-Text Behavior

### Exact labels

- Entry button: `Mic`
- Tooltip: `Dictate prompt`
- Active state: `Listening...`
- Processing state: `Transcribing...`
- Stop button: `Stop`

### Behavior

- Speech-to-text only fills the prompt box.
- The transcript is editable before plan preview or launch.
- No always-on voice mode appears in MVP.
- No meeting recording or persistent transcript is implied anywhere in the UI.

### Empty and success states

- Idle helper: `Dictate your prompt, then review the transcript before continuing.`
- Success note: `Transcript added to your prompt. Review it before continuing.`

### Warnings

- Primary warning: `Speech-to-text only fills the prompt box. It does not create a meeting recording or a saved transcript.`
- Failure warning: `We couldn't transcribe that recording. Try again or type your request.`

## 8. Default Versus Advanced Controls

### Default controls

These stay visible in the composer row:

- `Quick`
- `Standard`
- `Extended`
- `Attach files`
- `Mic`
- `Advanced`
- `Preview plan`

### Advanced controls

- Panel title: `Advanced controls`
- Panel helper: `Use these only when you need to change how the analysis is routed or reviewed.`
- Control label: `Use experimental deep research`
- Control warning: `Experimental. May bypass governed retrieval controls and should not be treated as canonical MVP evidence.`
- Control label: `Evaluation intensity`
- Control helper: `Controls how much of the current quality review stack Keystone tries to run.`
- Control label: `Analysis type`
- Control helper: `Leave on Auto unless you need a specific workflow.`
- Control label: `Show full plan details`

### Dev-only controls

- `Model choice`
- `Show run internals`

Do not place model names, raw IDs, or developer diagnostics in the default analyst surface.

## 9. Source And Evidence Labels

### Exact chips for current reality

- Discovery chip: `Discovered only`
- Citation chip: `Cited in claim`
- Liveness chip: `URL checked`
- Content chip: `Snippet only`
- Anchoring chip: `Not passage anchored`

### Rules

- Show these as separate chips, not as one rolled-up trust label.
- `Discovered only` means the source was found, not that it supports a claim.
- `Cited in claim` means a claim references the source, not that the claim is supported.
- `URL checked` means liveness was checked, not that the content supports the claim.
- `Snippet only` and `Not passage anchored` describe content limits, not evidence strength.
- Claim support belongs in the `Evidence` view, not in source-row chips.

### Shared warning

- `These source labels show discovery, citation presence, liveness, and content limits. They do not prove claim support.`

## 10. Right-Side Outputs Pane

### Exact labels

- Collapsed trigger: `Open outputs`
- Pane title: `Outputs`
- Section label: `Files`
- Section label: `Available outputs`
- Section label: `Status`
- Inline action: `Open`
- Inline action: `Download`
- Inline action: `Hide`

### Cross-state behavior

- On `Research` home, the pane can open, but `Available outputs` stays empty until a run exists.
- On `Plan ready`, the pane shows attached files and planned status, but not finished artifacts.
- During `Running`, the pane shows only artifacts that actually exist.
- During `Needs review`, the pane stays available so reviewers can inspect current materials without leaving the screen.
- On `Complete`, the pane lists the brief and any available bundle files. It must not imply slides, polished exports, or full document packages.

### Empty states

- Home empty state: `Outputs will appear after you start an analysis.`
- Plan state empty state: `Outputs are not available until the analysis starts.`
- Running empty state: `No outputs yet. Real artifacts will appear here as they are created.`
- Review state empty state: `This analysis is paused. Any current outputs remain available here.`
- Completed empty state: `No outputs are available for this analysis.`

### Warnings

- Missing-output warning: `Some expected outputs are missing because part of the analysis did not complete or did not render.`
- Scope warning: `The outputs pane lists current artifacts. It does not imply polished deliverables beyond the files that actually exist.`
