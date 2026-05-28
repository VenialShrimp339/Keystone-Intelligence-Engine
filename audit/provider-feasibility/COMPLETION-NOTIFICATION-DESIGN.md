# Completion Notification Design

Date: 2026-05-24

## Decision

Keystone should treat provider-native notifications as useful UX and treat its own browser watcher as the control-plane source of truth.

The completed-report trigger is:

1. Provider job state is `export_ready`.
2. Full report text, download, copy, artifact panel, or equivalent export surface is available.
3. `ProviderJobArtifact` is updated with completion/export evidence.
4. Report ingestion starts.

Partial research cards, source-count panels, progress summaries, and "sources and counting" states must not enter ingestion.

## Evidence

OpenAI's current Deep Research help page says completed ChatGPT reports include citations/source links, a sources-used section, activity history, and download options including Markdown, Word, and PDF. It also says progress can be viewed in real time and interrupted while running.

OpenAI's launch post says ChatGPT Deep Research can take 5 to 30 minutes and users get a notification when research is complete.

Anthropic's Claude Research help page says Research is enabled from the chat interface and can use web/internal context. It also says Research can use message limits faster because it retrieves multiple sources and produces comprehensive responses.

Live probe observations:

- ChatGPT accepted a public Deep Research job and stayed in `Thinking` after several minutes.
- Claude accepted a public Research-mode job, exposed a `Notify` button, gathered 257 sources, then surfaced `Research complete`, `Boom! Research report is ready`, and an artifact panel containing the full report.
- Clicking `Notify` during the Claude run did not block the browser flow and coincided with a visible `Notifications (F8)` region after completion.
- Browser-exposed `Notification.permission` was not available through the current Codex Chrome wrapper, so browser push cannot be the only machine-readable completion path.

## Recommended Architecture

Use three layers:

1. **Provider-native notification layer**
   - Enable provider `Notify` controls when available.
   - If Chrome asks for notification permission, the human can approve once.
   - Treat this as a human/operator alert, not as the durable job-completion event.

2. **Keystone browser watcher layer**
   - Each `ProviderJobArtifact` owns a browser tab/session ref, provider kind, prompt, selected model/tool evidence, and lifecycle state.
   - A watcher polls DOM/title/URL at a modest cadence, e.g. 15-30 seconds per live job.
   - Provider-specific detectors normalize DOM text into `running`, `export_ready`, `blocked`, `failed`, or `unknown`.
   - Only `export_ready` schedules export/copy/download and ingestion.

3. **Run orchestration layer**
   - The issue tree scheduler launches many provider jobs in parallel up to provider-specific concurrency limits.
   - The watcher emits completion events into the run ledger.
   - Completed reports flow into `ResearchReportArtifact`, `SourceBundleArtifact`, and `EvidenceBundleArtifact`.
   - Synthesis/evaluation decides whether another issue-tree wave is required.

## Current Implementation

`src/keystone/providers/browser_watch.py` now contains pure DOM-state detectors:

- `detect_chatgpt_deep_research_state`
- `detect_claude_research_state`

These return `ProviderCompletionSignal` with `should_ingest == True` only when the provider surface is export-ready.

The live Claude completed report was ingested under:

`audit/provider-feasibility/artifacts/live-probe-2026-05-24/ingested-artifacts/live-provider-probe-2026-05-24-claude/`

## Build Status

Implemented on 2026-05-28:

1. `ProviderJobRecord` persists provider, prompt, branch ID, URL, snapshots, status, export paths, source recovery, and ingestion state.
2. `BrowserProviderAdapter.watch_until_terminal` polls multiple active jobs in an interleaved loop with provider-specific detectors.
3. `export_and_ingest` allows ingestion only when the latest signal is `export_ready` and the provider export route is complete.
4. ChatGPT requires the body-plus-source route: Markdown report body plus DOCX source-link path.
5. Claude requires an artifact/report export path.
6. Running, blocked, failed, completed, exported, and rejected-incomplete states are ledgered.

Remaining build step:

1. Implement a live Chrome/plugin-backed controller for `BrowserProviderController`.
2. Trigger native provider exports from logged-in ChatGPT and Claude sessions.
3. Preserve source URL recovery from real DOCX/artifact exports, then reconcile those URLs into the evidence bundle.
