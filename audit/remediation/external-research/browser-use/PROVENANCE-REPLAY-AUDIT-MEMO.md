# Browser Use Provenance / Replay / Audit-Adjacent Memo

Audited repo: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use`

Upstream commit inspected: `5970007d86b99c073307ac78150eaff6631de807`

## Bottom Line

Browser Use has materially more provenance and replay value than the first pass credited.

The strongest undercredited surfaces are:

- HAR capture with embedded or attached response bodies
- saved per-step agent history plus screenshot files
- DOM-fingerprint-based history rerun and element rematching
- cloud session, message-history, and cost-monitoring surfaces

Those are real operational provenance and replay features.

They are still not enough for Keystone's governed evidence model.

## Genuinely Useful Provenance Surfaces

### 1. HAR and network capture

- `browser_use/browser/watchdogs/har_recording_watchdog.py:158-205` enables Network/Page CDP domains on browser connect, registers request/response/lifecycle handlers, and writes HAR on browser stop.
- `browser_use/browser/watchdogs/har_recording_watchdog.py:210-425` captures HTTPS request and response metadata, headers, protocol, server IP/port, TLS/security details, and fetches response bodies via `Network.getResponseBody`.
- `browser_use/browser/watchdogs/har_recording_watchdog.py:489-669` writes HAR 1.2 output with `record_har_content` modes (`omit` / `embed` / `attach`) and `record_har_mode` (`full` / `minimal`).
- `browser_use/browser/watchdogs/har_recording_watchdog.py:496-543` writes sidecar payload files in attach mode.
- `browser_use/browser/watchdogs/har_recording_watchdog.py:688-701` filters entries by HTTPS and by full vs same-origin minimal mode.

Why this matters:

- This is Browser Use's closest thing to acquisition-grade provenance.
- It is useful for explaining what the browser actually fetched on hard pages.
- It is especially useful for JS-heavy acquisition debugging, redirect/content-type issues, and postmortem analysis of browser fallback runs.

Where it still falls short for Keystone:

- It only records HTTPS traffic right now: `browser_use/browser/watchdogs/har_recording_watchdog.py:214-215`, `:688-690`.
- Timing breakdown is partial; DNS/connect/SSL are zero-filled because this implementation does not recover those timings from CDP: `browser_use/browser/watchdogs/har_recording_watchdog.py:715-745`.
- HAR output is written at session stop, not as a Keystone evidence bundle with stable identity and downstream locator semantics.
- It does not map network responses to claim-support units or citation anchors.

### 2. Download and PDF acquisition event trail

- `browser_use/browser/events.py:544-579` defines `DownloadStartedEvent`, `DownloadProgressEvent`, and `FileDownloadedEvent` with `guid`, `url`, `path`, `file_name`, `file_size`, `file_type`, `mime_type`, `from_cache`, and `auto_download`.
- `browser_use/browser/watchdogs/downloads_watchdog.py:272-322` emits start and progress events from CDP download callbacks.
- `browser_use/browser/watchdogs/downloads_watchdog.py:917-926`, `:1016-1028`, `:1340-1350` emits `FileDownloadedEvent` once a file lands.
- `browser_use/browser/watchdogs/downloads_watchdog.py:1177-1354` can pull a PDF out of Chrome's PDF viewer with a browser-context fetch and records cache/network status plus saved path.

Why this matters:

- Browser Use does keep a meaningful trail of "did we actually get the artifact, what path did it land at, and was it a normal or auto PDF download?"
- That is useful for Keystone fallback acquisition debugging.

Where it still falls short for Keystone:

- There is no first-class governed artifact record or mandatory content hash on the downloaded bytes.
- Some event branches are operational rather than canonical. For example, one local tracking branch uses the local file path as the event URL: `browser_use/browser/watchdogs/downloads_watchdog.py:825-836`.
- PDF detection and download rely on heuristics and browser-context fetch behavior; the code explicitly notes header visibility limits after navigation: `browser_use/browser/watchdogs/downloads_watchdog.py:1144-1169`.

### 3. Browser state persistence for authenticated replay

- `browser_use/browser/watchdogs/storage_state_watchdog.py:49-87` auto-loads and saves storage state on browser start and stop.
- `browser_use/browser/watchdogs/storage_state_watchdog.py:167-228` writes storage state atomically and emits counts of cookies and origins.
- `browser_use/browser/session.py:1356-1399` exports browser cookies to a Playwright-style `storage_state` JSON.
- `browser_use/browser/profile.py:474-475`, `:734-745` exposes `storage_state` at the profile level and warns about collisions with `user_data_dir`.

Why this matters:

- This is useful for authenticated-site access continuity, session reuse, and reproducible browser fallback runs.

Where it still falls short for Keystone:

- `export_storage_state()` exports cookies but leaves `origins` empty: `browser_use/browser/session.py:1373-1389`.
- This is access/session provenance, not evidence provenance.
- It does not provide a governance layer around which auth state may be reused or how it should be audited.

### 4. Step history, screenshots, and rerun support

- `browser_use/agent/views.py:488-589` stores `AgentHistory` with model output, action results, `BrowserStateHistory`, `StepMetadata`, and `state_message`.
- `browser_use/browser/views.py:113-149` stores per-step browser history with URL, title, tabs, interacted elements, and screenshot path.
- `browser_use/screenshots/service.py:13-36` persists step screenshots to disk.
- `browser_use/agent/views.py:627-699` saves and reloads history JSON.
- `browser_use/agent/views.py:767-803`, `:837-915` exposes URLs, screenshot paths, screenshots, action history, results, and readable step summaries.
- `browser_use/dom/views.py:975-1040` stores interacted-element fingerprints including `x_path`, `element_hash`, `stable_hash`, bounds, and `ax_name`.
- `browser_use/agent/service.py:3061-3237` reruns saved histories with saved step timing, retries, skip-failure mode, and a final rerun summary.
- `browser_use/agent/service.py:3356-3636` remaps historical element targets onto the current DOM using exact hash, stable hash, XPath, accessibility name, and attribute fallback matching.

Why this matters:

- This is real replay value, not just logging.
- Browser Use can persist an execution trace, reload it, substitute variables, and rerun it against a changed site.
- That makes it useful for regression replay, fallback acquisition debugging, and benchmark/control-arm evaluation.

This is the biggest place where the first pass undersold Browser Use.

Where it still falls short for Keystone:

- This is action replay, not evidence replay.
- Replay depends on the current DOM and site behavior, so it is not deterministic in the Keystone sense.
- Extract steps are explicitly re-run via AI rather than deterministic parsing: `browser_use/agent/service.py:3416-3435`.
- The final rerun summary is AI-generated from a fresh screenshot, not a governed comparison against a stable evidence bundle: `browser_use/agent/service.py:2865-2943`.

### 5. Judge and benchmark/control-arm support

- `browser_use/agent/service.py:1580-1655` runs a structured `JudgementResult` over the trace using final output, step text, and screenshots.
- `browser_use/agent/judge.py:44-225` builds the judge prompt from the task, agent trajectory, final result, and up to 10 screenshots.

Why this matters:

- This is useful for eval harnesses and benchmark/control-arm workflows.
- It helps answer "did the browser fallback actually complete the task?" in a structured way.

Where it still falls short for Keystone:

- The judge is another LLM layer, not deterministic verification.
- It does not ground outputs to canonical artifact spans or citation anchors.

### 6. Cloud session, message-history, and live-monitoring surfaces

- `browser_use/browser/cloud/views.py:74-83` returns cloud browser session IDs plus `liveUrl`, `cdpUrl`, and timing.
- `browser_use/browser/cloud/cloud.py:27-95` creates cloud browser sessions and surfaces the `liveUrl`.
- `browser_use/agent/cloud_events.py:117-184` defines `CreateAgentStepEvent` with step reasoning, actions, page URL, and screenshot as a data URL.
- `browser_use/agent/cloud_events.py:230-272` defines `CreateAgentSessionEvent` with browser session identifiers and session/browser metadata.
- `browser_use/sync/service.py:29-105` sends events to Browser Use Cloud when sync is enabled and authenticated.
- `skills/cloud/references/api-v3.md:86-157`, `:245-257` documents `live_url`, session messages, files, token counts, and total cost fields.
- `skills/cloud/references/sessions.md:46-53` documents live view and public share links.
- `skills/cloud/references/features.md:199-216` documents human takeover via `liveUrl`.

Why this matters:

- If Browser Use Cloud is in play, there is a meaningful operator observability surface: live session viewing, public share links, session messages, file listings, and cost breakdowns.

Where it still falls short for Keystone:

- This is vendor-hosted monitoring, not Keystone-owned governed provenance.
- Much of it is cloud-only and outside the OSS local execution path.
- The local code comments mention event-bus WAL persistence, but the WAL path is commented out rather than actively used: `browser_use/agent/service.py:584-587`.
- Related WAL update code is also commented out: `browser_use/sync/service.py:107-139`.
- `CloudSync` is network push, not durable local audit storage, and it intentionally fails quietly when sync is unavailable: `browser_use/sync/service.py:29-105`.

### 7. Token and cost tracking

- `browser_use/tokens/service.py:48-80`, `:212-238`, `:328-372` wraps model calls, records token usage, and can calculate costs.
- `browser_use/tokens/service.py:388-458` builds `UsageSummary`.
- `browser_use/tokens/views.py:94-109` defines the summary schema.
- `browser_use/agent/service.py:2620-2624` stores usage summary on the returned history object.

Why this matters:

- This is useful for benchmarking fallback strategies and understanding operational cost.

Where it still falls short for Keystone:

- Token and cost metrics say nothing about evidence quality or provenance.
- They are operational metrics, not evidence artifacts.

### 8. Optional tracing and product telemetry

- `browser_use/observability.py:42-55`, `:87-183` integrates with `lmnr` only if it is installed; otherwise the decorators are no-ops.
- `browser_use/telemetry/service.py:23-91` sends anonymized product telemetry to PostHog.
- `browser_use/telemetry/views.py:25-58` defines telemetry fields including URLs visited, action history, errors, token totals, and judge outputs.
- `browser_use/agent/service.py:2175-2225` assembles and sends the agent telemetry payload.

Why this matters:

- This is useful for product analytics and optional debug tracing inside the Browser Use ecosystem.

Where it still falls short for Keystone:

- This is not a governed audit ledger.
- The `lmnr` path is optional and may be inactive.
- PostHog telemetry is outbound analytics, not Keystone-owned provenance.

## Surfaces That Look Stronger Than They Are

### `traces_dir` appears underimplemented in OSS

- `browser_use/browser/profile.py:413-416` defines `traces_dir`.
- `browser_use/browser/session.py:202-212`, `:255-267` accepts it in the session constructor.
- `skills/open-source/references/browser.md:92-99` documents it as "Complete trace files."

I did not find an actual trace writer or trace-watchdog in the OSS codepath. In practice, the implemented provenance surfaces are HAR, screenshots, recordings, saved history, and cloud/live monitoring, not a full local trace artifact pipeline.

## Not Enough For Governed Evidence

Browser Use still does not provide what Keystone needs on the canonical retrieval path:

- no Keystone-style evidence bundle with stable artifact identity and content hashes
- no anchored locators into article text, DOM text, or PDF text suitable for canonical citations
- no separation between raw artifact, derived parse, extracted claim support, and judge commentary
- no deterministic parse contract
- no citation manifest or governed citation object model
- no immutable audit chain tying final claims back to specific artifact bytes and anchored spans

Its strongest replay surfaces are about re-executing browser behavior.

Keystone needs governed evidence surfaces that survive without rerunning the browser.

## Updated Assessment

Browser Use does have deeper provenance and replay value than the first pass credited.

The most undercredited capabilities were:

- HAR capture with embedded or attached bodies
- persisted step histories plus screenshot files
- DOM-fingerprint-based `rerun_history()` with element rematching
- cloud session, message-history, and cost-monitoring surfaces

That does not change the architectural conclusion for Keystone:

- Browser Use has meaningful value as a fallback acquisition debugger.
- Browser Use has meaningful value as a benchmark/control-arm replay harness.
- Browser Use still does not qualify as Keystone's governed evidence layer.

Net: Browser Use provenance is operational and replay-oriented, not citation-governance-grade.
