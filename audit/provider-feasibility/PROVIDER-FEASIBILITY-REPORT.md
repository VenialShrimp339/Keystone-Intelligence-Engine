# Provider Feasibility Report

Date: 2026-05-24

## Bottom Line

The subscription-first path is feasible, but it needs provider adapters and artifact contracts rather than a direct swap from `claude -p` to `codex exec`. The best target architecture is:

| Work type | Primary provider path | Why |
| --- | --- | --- |
| Structured orchestration, parsing, classification, gating | `codex exec` through ChatGPT-authenticated Codex | Non-interactive, local CLI, schema output, JSONL events, usage accounting. |
| Hosted broad web research | ChatGPT web Deep Research | Uses Pro subscription surface, exposed in Chrome, produces cited structured reports. |
| Secondary hosted web research / rate-limit spillover | Claude web Research | Uses Max subscription surface, exposed in Chrome, independent provider family. |
| Deterministic public data | Local connectors and source-specific code | SEC/EDGAR and filings should be pulled deterministically. |
| Paid API | Fallback/control/benchmark | Strong observability and structured outputs, but not the owner's default cost path. |

## Official Source Findings

| Source | Finding | Link |
| --- | --- | --- |
| OpenAI Help: Codex with ChatGPT plan | Codex is included with eligible ChatGPT plans. Usage depends on plan and counts toward agentic usage. Larger codebases and extended sessions consume more per message. | https://help.openai.com/en/articles/11369540-codex-in-chatgpt-faq |
| OpenAI Help: Deep Research | ChatGPT Deep Research starts from the tools menu, asks for task/source choices, creates a research plan, runs with progress, and returns a cited report. | https://help.openai.com/en/articles/10500283-research-faq |
| OpenAI Help: ChatGPT Pro tiers | Pro includes Pro models, Codex, Deep Research, file uploads, and high usage allowances, subject to Terms of Use and abuse guardrails. | https://help.openai.com/en/articles/9793128-what-is-chatgpt-pro |
| OpenAI model docs | GPT-5.5 is a current frontier model with structured output support, web search support, and a 1,050,000 token context window in API docs. | https://developers.openai.com/api/docs/models/gpt-5.5/ |
| Anthropic Help: Agent SDK with Claude plan | Starting June 15, 2026, Claude Agent SDK and `claude -p` no longer count toward Claude plan usage and instead draw from a separate monthly credit before extra usage. | https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan |
| Anthropic Help: Research on Claude | Claude Research is available on paid plans, requires web search, works agentically across searches, and returns cited answers. | https://support.claude.com/en/articles/11088861-using-research-on-claude-ai |

## Local Probe Findings

| Probe | Result | Artifact |
| --- | --- | --- |
| `codex --version` | Local CLI is `codex-cli 0.128.0`. | terminal evidence |
| `codex exec --help` | Supports `--json`, `--output-schema`, `--output-last-message`, model selection, sandboxing, and working directory selection. | terminal evidence |
| Structured Codex call | Succeeded with schema output and JSONL events. Usage reported 28,492 input tokens, 130 output tokens, 74 reasoning tokens. | `audit/provider-feasibility/artifacts/codex-exec-structured-events.jsonl` |
| `codex debug models` | Local catalog includes `gpt-5.5` as selectable in Codex on this machine. | terminal evidence |
| ChatGPT Chrome probe | Logged in as Pro. Deep Research can be selected from the tools menu. Pro mode appears in model menu. | `chatgpt-*.png`, `chatgpt-*.txt` |
| Claude Chrome probe | Logged in as Max. Research and Web Search controls appear in Claude tools menu. | `claude-*.png`, `claude-*.txt` |

## Implementation Path: Codex CLI

Use Codex CLI for non-browser LLM calls where Keystone needs structured outputs and local orchestration:

| Requirement | Route |
| --- | --- |
| Provider auth | Use current ChatGPT-authenticated Codex login. Avoid API keys by default. |
| Structured output | Call `codex exec --output-schema <schema> --json --output-last-message <file>`. |
| Usage observability | Parse JSONL `turn.completed.usage` events. |
| Context control | Run from narrow working directories, use explicit prompts, and avoid loading repo-wide context unless needed. |
| Safety | Use `--sandbox read-only` for analysis and parsing calls; only use write modes inside explicit implementation tasks. |
| Model selection | Use `--model` only after local catalog validation. Current local catalog exposes `gpt-5.5`. |

Practical warning: the trivial schema probe used 28.5K input tokens. This likely reflects global instructions, skill/plugin context, and CLI harness overhead. Keystone must avoid spawning Codex as a high-volume inner loop for tiny operations. Codex CLI is good for high-value structured decisions and parsing, not for thousands of small micro-calls.

## Implementation Path: ChatGPT Web Deep Research

Use ChatGPT web automation for hosted research reports:

| Step | Route |
| --- | --- |
| Open session | Use Chrome extension browser automation with the user's logged-in profile. |
| Select tool | Click `Add files and more`, select `Deep research`. Probe confirms this selector path. |
| Select model/mode | Use model button to choose available mode, including Pro/Extended where appropriate. Probe confirms the model menu exposes Pro. |
| Submit public prompt | Generate a branch-specific research brief from L0. Prompt should include public-data scope, source preferences, exclusion criteria, desired report structure, and citation requirements. |
| Handle preflight plan | Deep Research may ask for confirmation or source choices. The adapter should surface this as a HITL approval event or apply pre-approved public-web defaults. |
| Detect completion | Monitor DOM state for the transition from running/progress UI to final report controls and stable final answer text. Persist screenshots and DOM snapshots at state changes. |
| Export/copy/save | First route: use built-in copy/download/share controls when available. Second route: capture rendered report DOM/Markdown plus source links. Third route: use browser download events or clipboard readback. |
| Ingest | Normalize into `ResearchReportArtifact`, then run local citation processor and source extraction. |

This is an implementation plan, not a yes/no feasibility gate. The missing proof is an end-to-end micro-probe that submits one small public Deep Research task and records the selectors for completion and export. The current probe stopped before submission to avoid launching an unnecessary long-running report during the audit.

## Implementation Path: Claude Web Research

Use Claude web automation as a secondary hosted-research provider and rate-limit spillover:

| Step | Route |
| --- | --- |
| Open session | Chrome automation with logged-in Claude Max profile. Probe confirms access. |
| Select tools | Open `Add files, connectors, and more`, select `Research`, keep `Web search` enabled. Probe confirms both controls. |
| Select model | Use model selector. Probe shows `Opus 4.7 Adaptive`. |
| Submit public prompt | Same branch-specific brief format as ChatGPT, with provider-specific phrasing. |
| Detect completion | Monitor running state and final response controls. |
| Export/copy/save | Use copy/share/download if present; otherwise capture response DOM and links. |
| Ingest | Normalize into the same `ResearchReportArtifact` contract. |

Claude web remains valuable for research breadth and cross-provider comparison. Claude CLI should no longer be the primary automation backend for this project because the June 15, 2026 billing model split removes the old subscription-limit assumption for `claude -p`.

## Implementation Path: Deterministic Public Data

Public company financial work should avoid hosted Deep Research unless the task truly needs synthesis across many web sources. SEC filings, company facts, 10-Ks, 10-Qs, earnings releases, and financial tables should flow through deterministic connectors first.

| Workflow | Preferred route |
| --- | --- |
| Pull SEC filings | SEC/EDGAR connector or local downloader. |
| Extract financial statements | Deterministic parser plus LLM-assisted mapping only where labels are ambiguous. |
| Build workbook | Local spreadsheet generation with formulas and audit sheet. |
| Analyze trends | Codex/LLM for narrative interpretation after data table is built. |
| Verify | Foot every number to filing/source line or extracted table cell. |

This matters because Deep Research is excellent for breadth and synthesis, but deterministic filings workflows need precision, repeatability, and workbook artifacts.

## Capability Assessment

| Capability | Primary route | Status | Proof |
| --- | --- | --- | --- |
| Non-interactive structured LLM call | Codex CLI | PROVEN | Schema probe succeeded. |
| Usage accounting for CLI calls | Codex CLI JSONL | PROVEN | `turn.completed.usage` present. |
| ChatGPT Deep Research selection | ChatGPT web | PROVEN | `chatgpt-deep-research-selected-dom.txt`. |
| ChatGPT Pro mode access | ChatGPT web | PROVEN | `chatgpt-model-menu-dom.txt`. |
| Claude Research selection | Claude web | PROVEN | `claude-tools-menu-dom.txt`. |
| Submit hosted research job | ChatGPT/Claude web | PROVEN | Live public prompt submitted to both providers. |
| Detect hosted research completion | Browser adapter | PROVEN | Claude completion captured; ChatGPT completion captured with `Research completed in 17m · 10 citations · 246 searches`. |
| Export/copy/download hosted report | Browser adapter | PROVEN | Claude artifact panel extracted to Markdown; ChatGPT exported to Markdown and Word. |
| Manual/browser report ingestion | Local ingestion | PROVEN | Claude and ChatGPT completed reports ingested into durable artifacts. |
| API fallback | OpenAI/Anthropic APIs | AVAILABLE | Official docs and SDKs, but out of default cost path. |

## ChatGPT Lifecycle Update

The live ChatGPT Deep Research probe completed and was captured on 2026-05-28.

| Evidence | Result |
| --- | --- |
| Completion card | `Research completed in 17m · 10 citations · 246 searches`. |
| Markdown export | Succeeded; saved as `live-probe-2026-05-24/chatgpt-live-completed-report.md`. |
| Word export | Succeeded; saved as `live-probe-2026-05-24/chatgpt-live-completed-report.docx`. |
| Source-link recovery | Required the DOCX export. Native Markdown preserved opaque citation markers but not source URLs. |
| Ingestion run | `live-probe-2026-05-24/ingested-artifacts/live-provider-probe-2026-05-24-chatgpt/`. |
| Ingestion result | 10 sources, 24 candidate claims, 11 cited claims, 13 citation-gap flags, 4/4 local evaluation checks passed. |

Implementation implication: the ChatGPT web adapter should prefer a two-export route when source fidelity matters: Markdown for body structure, DOCX for source URL recovery. If a future UI export includes source URLs directly in Markdown, the adapter can collapse back to one export.

## Terms And Risk Notes

OpenAI's Pro help article notes usage is subject to Terms of Use and abuse guardrails, including restrictions on abusive automated extraction, credential sharing, reselling, or powering third-party services through an individual account. The project should stay in a personal development and internal testing posture until firm policy and account terms are explicitly reviewed.

Claude's Agent SDK credit article distinguishes interactive Claude Code, web Claude, and `claude -p`/SDK usage. The repo's old assumption that `claude -p` can freely consume Max-plan capacity is stale as of the June 15, 2026 policy.

## Recommended Provider Architecture

```text
ProviderAdapter
  CodexExecAdapter
    use: structured orchestration, parsing, evaluation, small synthesis
    artifact: LLMCallArtifact

  ChatGPTWebResearchAdapter
    use: primary hosted public-web Deep Research
    artifact: ResearchReportArtifact

  ClaudeWebResearchAdapter
    use: secondary hosted Research, cross-provider challenge reports
    artifact: ResearchReportArtifact

  ManualUploadAdapter
    use: first working version and fallbacks
    artifact: ResearchReportArtifact

  DeterministicSourceAdapter
    use: SEC/EDGAR, filings, datasets, PDFs
    artifact: SourceBundleArtifact

  ApiFallbackAdapter
    use: fallback/control/evals when subscription path is insufficient
    artifact: LLMCallArtifact or ResearchReportArtifact
```

## Immediate Next Experiments

Status update, 2026-05-28:

- `src/keystone/providers/browser_provider.py` now implements the provider ledger, interleaved watcher loop, DOM-signal integration, ChatGPT Markdown plus DOCX export-route enforcement, Claude artifact/report export-route enforcement, and completion-only ingestion control.
- The first artifact-centered vertical slice used a fixture controller to run two branch-level provider jobs and wrote the provider ledger under `audit/vertical-slices/2026-05-28-artifact-centered/run/provider-ledger.json`.
- The remaining gap is live browser control: replacing the fixture controller with a Chrome/plugin controller that can submit provider jobs and trigger native exports in logged-in sessions.

Next experiments:

1. Implement a live Chrome/plugin-backed `BrowserProviderController`.
2. Exercise real ChatGPT Markdown+DOCX and Claude artifact exports from approved `IssueTreePackage.leaf_tasks[]`.
3. Add per-provider concurrency controls and source/depth budget prompts before launching large issue-tree waves.
4. Add a provider ledger UI or review view that records provider, account surface, submitted prompt, start/end timestamps, DOM snapshots, completion status, artifact paths, and usage if available.
