# Provider Experiment Log

Date: 2026-05-24

## Experiment 1: Local Codex CLI Surface

Command:

```bash
codex --version
codex exec --help
```

Result:

| Observation | Result |
| --- | --- |
| CLI path | `/opt/homebrew/bin/codex` |
| Version | `codex-cli 0.128.0` |
| Non-interactive command | `codex exec` present |
| Structured output | `--output-schema <FILE>` present |
| JSONL events | `--json` present |
| Last message output | `--output-last-message <FILE>` present |
| Sandbox controls | `--sandbox read-only/workspace-write/danger-full-access` present |

Verdict: PROVEN for structured local orchestration.

## Experiment 2: Codex Structured Output Probe

Command:

```bash
codex exec --json \
  --output-schema audit/provider-feasibility/artifacts/codex-output-schema.json \
  --output-last-message audit/provider-feasibility/artifacts/codex-exec-structured-last-message.json \
  --sandbox read-only \
  --cd /Users/jackriddle/Desktop/Keystone-Intelligence-Engine-owner-triage-normalization \
  "Return a JSON object matching the schema..."
```

Artifacts:

| File | Meaning |
| --- | --- |
| `audit/provider-feasibility/artifacts/codex-output-schema.json` | Probe schema. |
| `audit/provider-feasibility/artifacts/codex-exec-structured-last-message.json` | Structured final output. |
| `audit/provider-feasibility/artifacts/codex-exec-structured-events.jsonl` | JSONL event stream and usage. |

Result:

```json
{"ok":true,"provider":"openai","surface":"codex_exec_subscription_or_current_login","capabilities_observed":["non_interactive_exec","output_schema_flag","json_events_flag"],"limits_observed":[]}
```

Usage event:

| Metric | Value |
| --- | --- |
| Input tokens | 28,492 |
| Cached input tokens | 2,432 |
| Output tokens | 130 |
| Reasoning output tokens | 74 |

Interpretation: the route works, but Keystone must reserve Codex CLI for high-value structured calls and keep prompts/context minimal.

## Experiment 3: Local Codex Model Catalog

Command:

```bash
codex debug models
```

Result:

The model catalog output includes `gpt-5.5` with `low`, `medium`, `high`, and `xhigh` reasoning levels. This validates the user's point that current Codex CLI can expose models that were absent from older project assumptions.

Verdict: PROVEN locally, though model availability remains account/catalog dependent.

## Experiment 4: Chrome Extension Browser Control

Method:

Used the Chrome browser automation skill and the installed Codex Chrome Extension through `node_repl`.

Result:

| Observation | Result |
| --- | --- |
| Browser connection | Succeeded. |
| Selected profile | `Your Chrome`. |
| Open tabs at start | None reported through extension. |

Verdict: PROVEN.

## Experiment 5: ChatGPT Web Surface

URL: `https://chatgpt.com/`

Artifacts:

| File | Meaning |
| --- | --- |
| `chatgpt-home.png` | Initial logged-in ChatGPT surface. |
| `chatgpt-home-dom.txt` | Initial DOM snapshot. |
| `chatgpt-composer.png` | Composer after closing modal. |
| `chatgpt-composer-dom.txt` | Composer DOM snapshot. |
| `chatgpt-model-menu.png` | Model menu screenshot. |
| `chatgpt-model-menu-dom.txt` | Model menu DOM snapshot. |
| `chatgpt-tools-menu.png` | Tools menu screenshot. |
| `chatgpt-tools-menu-dom.txt` | Tools menu DOM snapshot. |
| `chatgpt-deep-research-selected.png` | Deep Research selected screenshot. |
| `chatgpt-deep-research-selected-dom.txt` | Deep Research selected DOM snapshot. |

Observed selectors:

| UI element | Observed name |
| --- | --- |
| Composer | `textbox "Chat with ChatGPT"` |
| Tools button | `button "Add files and more"` |
| Deep Research option | `menuitemradio "Deep research"` |
| Web Search option | `menuitemradio "Web search"` |
| Model button | `button "Heavy"` before tool selection |
| Pro model option | `menuitemradio "Pro • Extended"` |
| Deep Research selected chip | `button "Deep research, click to remove"` |

Verdict: PROVEN through pre-submission selection. Lifecycle submission/export remains next experiment.

## Experiment 6: Claude Web Surface

URL: `https://claude.ai/new`

Artifacts:

| File | Meaning |
| --- | --- |
| `claude-home.png` | Initial logged-in Claude surface. |
| `claude-home-dom.txt` | Initial DOM snapshot. |
| `claude-tools-menu.png` | Tools menu screenshot. |
| `claude-tools-menu-dom.txt` | Tools menu DOM snapshot. |

Observed selectors:

| UI element | Observed name |
| --- | --- |
| Composer | `textbox "Write your prompt to Claude"` |
| Tools button | `button "Add files, connectors, and more"` |
| Research option | `menuitemcheckbox "Research"` |
| Web Search option | `menuitemcheckbox "Web search"` |
| Model button | `button "Model: Opus 4.7 Adaptive"` |

Verdict: PROVEN through pre-submission selection. Lifecycle submission/export remains next experiment.

## Deliberately Not Run

I did not submit a live Deep Research job in this audit. The next provider track should do that with a tiny public prompt and record the full lifecycle. This audit was designed to answer architecture feasibility and avoid unnecessary long-running provider usage while still proving access to the relevant controls.

## Experiment 7: Live Hosted Research Lifecycle Probe

Date: 2026-05-24

Prompt:

`Using only public web sources, produce a concise research report on the current state of the U.S. auto body repair industry consolidation trend. Include 5 cited factual claims, source links, and a short note on evidence gaps. Keep the report compact.`

### ChatGPT Deep Research

Artifacts:

| File | Meaning |
| --- | --- |
| `live-probe-2026-05-24/chatgpt-live-deep-research-selected-dom.txt` | Deep Research selected. |
| `live-probe-2026-05-24/chatgpt-live-submitted-prompt.txt` | Submitted public prompt. |
| `live-probe-2026-05-24/chatgpt-live-after-submit-url.txt` | Created conversation URL. |
| `live-probe-2026-05-24/chatgpt-live-poll-*.txt/png` | Running-state evidence. |
| `live-probe-2026-05-24/chatgpt-live-completed-report-fullpage.png` | Completed report screenshot evidence. |
| `live-probe-2026-05-24/chatgpt-live-completed-report.md` | Native Markdown export. |
| `live-probe-2026-05-24/chatgpt-live-completed-report.docx` | Native Word export, used to recover actual source links. |
| `live-probe-2026-05-24/chatgpt-live-completed-report-normalized-with-sources.md` | Ingestion-friendly normalized report with DOCX-derived source references. |
| `live-probe-2026-05-24/chatgpt-live-completed-report-source-links.json` | Extracted source URL inventory and numeric citation map. |
| `live-probe-2026-05-24/ingested-artifacts/live-provider-probe-2026-05-24-chatgpt/` | Keystone run ledger and ingested artifacts. |

Observed selectors:

| UI element | Observed name |
| --- | --- |
| Deep Research selected chip | `button "Deep research, click to remove"` |
| Running state | `button "Thinking"` and `button "Stop answering"` |
| Conversation title | `US Auto Body Repair Trends` |
| Conversation URL | `https://chatgpt.com/c/6a137bbc-82d0-83ea-a457-fbfa6d56e3de` |
| Completion banner | `Research completed in 17m · 10 citations · 246 searches` |
| Export menu | `Copy contents`, `Export to Markdown`, `Export to Word`, `Export to PDF` |

Outcome:

- ChatGPT completed the hosted report and exposed export controls.
- Markdown export succeeded, but it preserved opaque ChatGPT citation markers rather than actual source URLs.
- Word export succeeded and exposed the ten actual source URLs in DOCX relationships/document XML.
- The normalized report was ingested into `ProviderJobArtifact`, `ResearchReportArtifact`, `SourceBundleArtifact`, `EvidenceBundleArtifact`, `SynthesisArtifact`, `EvaluationArtifact`, and `DeliverableArtifact`.
- The ingested source bundle has 10 sources, 24 extracted candidate claims, 11 cited claims, and 13 citation-gap flags. The local first-slice evaluation passed 4/4 deterministic checks.
- Partial/running poll artifacts were preserved as lifecycle evidence but were not ingested.

Verdict: FULL LIFECYCLE PROVEN for ChatGPT Deep Research through browser automation, native export, source-link recovery, and local ingestion.

### Claude Research

Artifacts:

| File | Meaning |
| --- | --- |
| `live-probe-2026-05-24/claude-live-research-selected-dom.txt` | Research mode selected. |
| `live-probe-2026-05-24/claude-live-submitted-prompt.txt` | Submitted public prompt. |
| `live-probe-2026-05-24/claude-live-after-submit-url.txt` | Created conversation URL. |
| `live-probe-2026-05-24/claude-live-research-panel-dom.txt` | Research panel while running. |
| `live-probe-2026-05-24/claude-live-after-notify-dom.txt` | Notify/completion state. |
| `live-probe-2026-05-24/claude-live-completed-report-dom.txt` | Completed report artifact panel. |
| `live-probe-2026-05-24/claude-live-completed-report.md` | Saved completed report text plus extracted source URLs. |
| `live-probe-2026-05-24/ingested-artifacts/` | Keystone run ledger and ingested artifacts. |

Observed selectors:

| UI element | Observed name |
| --- | --- |
| Research mode | `button "Research mode" [pressed]` |
| Model | `button "Model: Opus 4.7 Adaptive"` |
| Running state | `sources and counting`, then `Writing and citing report...` |
| Native notify | `button "Notify"` |
| Completion state | `Research complete`, `Boom! Research report is ready` |
| Export surface | `Artifact panel: U.S. Collision Repair Consolidation: State of Play, Late 2025 to Mid-2026` |

Outcome:

- Claude gathered 257 sources and produced a full report.
- The report was saved to Markdown and ingested into `ResearchReportArtifact`, `SourceBundleArtifact`, `EvidenceBundleArtifact`, `SynthesisArtifact`, `EvaluationArtifact`, `DeliverableArtifact`, and `ProviderJobArtifact`.
- Partial research card text was deliberately ignored.

Verdict: FULL LIFECYCLE PROVEN for Claude Research through browser automation and local ingestion.

## Experiment 8: Completion Notification / Watcher Probe

Official docs and live UI both support a watcher-based architecture:

- OpenAI says ChatGPT Deep Research can take 5-30 minutes and users receive a notification when research completes.
- OpenAI says completed ChatGPT reports can be downloaded as Markdown, Word, and PDF.
- Claude's live Research UI exposes a `Notify` button, source-count progress, completion text, and an artifact panel.

Implementation added:

- `src/keystone/providers/browser_watch.py`
- `tests/unit/providers/test_browser_watch.py`
- `audit/provider-feasibility/COMPLETION-NOTIFICATION-DESIGN.md`

Watcher rule:

Only provider state `export_ready` is ingestable. Running/source-count/partial states are never sent to report ingestion.
