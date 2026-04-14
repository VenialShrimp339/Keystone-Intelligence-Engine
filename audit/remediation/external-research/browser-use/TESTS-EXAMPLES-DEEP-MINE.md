# Browser Use Deep Mine: Tests, Examples, and Repo Docs

## Bottom Line

The deeper pass did find materially important capabilities that were easy to underweight in a surface skim.

The biggest updates are:

- Browser Use is more stateful than it first appears.
- It has more replay, recovery, and observability machinery than the README alone suggests.
- It has a real file/document workflow, not just "click around a browser."
- It has explicit patterns for being used either as a black-box browsing subagent or as a lower-level browser tool surface.

That said, none of the newly surfaced capabilities change the core Keystone classification:

- `FALLBACK_ONLY` still looks right for governed Keystone retrieval.
- `BENCHMARK_OR_CONTROL_ARM_ONLY` is also stronger than I first gave it credit for, especially for replay/evaluation work.

## How This Pass Was Done

This pass focused on high-signal sources that often reveal more than the marketing surface:

- `tests/`
- `examples/`
- `README.md`
- `skills/open-source/references/*`
- `skills/cloud/references/*`
- `CLOUD.md`

The aim was not "what can the package theoretically do," but "what capabilities are documented, demoed, and/or directly exercised in tests."

## Rating Scale

- `VERY_HIGH`: likely directly useful to Keystone research/retrieval work
- `HIGH`: clearly useful, but probably at a bounded seam
- `MEDIUM`: useful in sidecar or operator workflows, but not core architecture
- `LOW`: interesting, but low direct leverage for Keystone

## Findings

### 1. Stateful follow-up browsing is a first-class pattern, not a one-shot demo

- Likely value to Keystone: `VERY_HIGH`
- What seems supported:
  - persistent browser/session state across tasks
  - cookies/localStorage reuse
  - follow-up task queuing on the same agent/browser
- Concrete evidence:
  - `examples/features/follow_up_tasks.py:15-28` uses `BrowserProfile(keep_alive=True)` and `agent.add_new_task(...)`
  - `examples/features/follow_up_task.py:11-18` reuses one browser and runs a second task against existing state
  - `skills/open-source/references/examples.md:73-98` explicitly documents follow-up tasks and says browser state is preserved
  - `skills/cloud/references/sessions.md:24-43` documents running multiple tasks in the same cloud session
  - `skills/cloud/references/guides/subagent.md:99-105` shows login in one run and extraction in a later run using the same session
- Why this matters for Keystone:
  - This is genuinely relevant for authenticated or interaction-gated acquisition.
  - It makes Browser Use more credible as a fallback acquisition layer for hard sites.
  - It still does not solve deterministic evidence extraction or citation anchoring.

### 2. Replay/rerun support is deeper than expected and is actually quite interesting for benchmark/control use

- Likely value to Keystone: `VERY_HIGH`
- What seems supported:
  - save agent history
  - detect variables in prior runs
  - rerun with substituted values
  - preserve/replay initial URL actions
  - AI re-evaluation for replayed extract actions
  - AI completion summary after rerun
  - step timing metadata for replay pacing
- Concrete evidence:
  - `examples/features/rerun_history.py:1-49` describes variable detection, substituted reruns, and AI summary
  - `examples/features/rerun_history.py:73-135` saves history, detects variables, reruns with substitutions, and prints summary
  - `tests/ci/test_rerun_ai_summary.py:12-52` tests successful AI rerun summary generation
  - `tests/ci/test_rerun_ai_summary.py:57-96` tests error-aware summary generation
  - `tests/ci/test_rerun_ai_summary.py:99-126` tests fallback summary behavior if summary LLM fails
  - `tests/ci/test_rerun_ai_summary.py:174-252` tests skip behavior for originally failed steps
  - `tests/ci/test_history_wait_time.py:23-37` shows preserved `step_interval` timing metadata
- Why this matters for Keystone:
  - This is not governed replay, but it is very relevant for evaluation harnesses, benchmark control arms, and debugging acquisition workflows.
  - If Keystone wants "same browsing trajectory, different inputs/site states" experiments, Browser Use already has machinery in this direction.
  - This strengthens the `BENCHMARK_OR_CONTROL_ARM_ONLY` case.

### 3. Structured extraction is more real than "LLM output prettification"

- Likely value to Keystone: `HIGH`
- What seems supported:
  - JSON-schema-to-Pydantic conversion
  - schema-enforced structured extraction
  - structured result tagging and metadata
  - graceful fallback to free text on unsupported schema constructs
  - extraction schema injection through tool plumbing
- Concrete evidence:
  - `skills/open-source/references/agent.md:38-46` documents `output_model_schema` and `page_extraction_llm`
  - `examples/features/custom_output.py:22-49` returns typed Hacker News post data
  - `tests/ci/test_structured_extraction.py:372-425` verifies `<structured_result>` output, parsed JSON, and metadata
  - `tests/ci/test_structured_extraction.py:451-480` verifies fallback to free text on unsupported schema
  - `tests/ci/test_structured_extraction.py:511-580` verifies injected extraction schema and precedence behavior
  - `tests/ci/test_structured_extraction.py:26-255` exercises schema conversion behavior in depth
- Why this matters for Keystone:
  - This is meaningful if Keystone wants Browser Use to return typed acquisition payloads from a fallback lane.
  - But the contract is still "schema-shaped LLM extraction," not a governed evidence bundle with anchors.
  - Useful for sidecar extraction; not sufficient for canonical evidence production.

### 4. Browser-native file and document handling is a real capability cluster

- Likely value to Keystone: `HIGH`
- What seems supported:
  - download files through browsing flows
  - save current pages as PDF
  - read and write sandboxed files during runs
  - read external images and DOCX files
  - move file outputs back to the caller as attachments/output files
- Concrete evidence:
  - `examples/features/download_file.py:21-30` downloads files through the browser
  - `examples/features/save_as_pdf.py:1-42` saves arbitrary pages as PDFs and surfaces attachments
  - `tests/ci/test_action_save_as_pdf.py:104-257` verifies default naming, custom naming, duplicate naming, paper formats, landscape, and background rendering
  - `examples/file_system/file_system.py:20-42` writes, appends, reads, and shares files during an agent task
  - `examples/file_system/alphabet_earnings.py:16-30` opens a PDF, extracts data points, and writes/shares a file
  - `examples/use-cases/extract_pdf_content.py:25-33` reads a public PDF and answers a page-specific query
  - `tests/ci/test_file_system_docx.py:17-189` shows DOCX write/read support
  - `tests/ci/test_file_system_images.py:24-183` shows external image ingestion as base64 payloads
  - `tests/ci/test_file_system_llm_integration.py:19-176` shows images and DOCX content flowing into LLM-visible message state
  - `skills/cloud/references/patterns.md:94-120` documents download retrieval and upload via presigned URLs
- Why this matters for Keystone:
  - This is one of the strongest acquisition-side arguments for Browser Use.
  - It can plausibly help with "get the PDF" and "interact until the file is available" problems.
  - It still does not make the resulting file governed, normalized, or citation-ready by itself.

### 5. The repo has explicit lower-level retrieval helpers beyond the high-level agent loop

- Likely value to Keystone: `HIGH`
- What seems supported:
  - page text search with regex, CSS scoping, and case control
  - DOM element discovery with selector queries and attribute extraction
  - absolute `src` resolution for images
  - direct page and CDP access in hooks/tools
  - legacy direct actor API
- Concrete evidence:
  - `tests/ci/test_search_find.py:166-288` tests `search_page` with regex, CSS scopes, limits, and memory summaries
  - `tests/ci/test_search_find.py:293-442` tests `find_elements` with attributes, nested selectors, element counts, and absolute image URLs
  - `skills/open-source/references/tools.md:101-139` enumerates default browser tools
  - `skills/open-source/references/agent.md:202-248` documents hooks and direct CDP access from hooks
  - `skills/open-source/references/actor.md:41-69` documents page methods including `extract_content(...)`
- Why this matters for Keystone:
  - If Keystone ever wants Browser Use at a narrow seam, these lower-level capabilities are more relevant than the "autonomous agent" wrapper.
  - This supports a bounded integration strategy better than I first assumed.

### 6. Authenticated browsing support is more operationally serious than a simple "use cookies" story

- Likely value to Keystone: `VERY_HIGH`
- What seems supported:
  - local Chrome profile reuse
  - export of storage state
  - cloud profiles preserving cookies/localStorage/passwords
  - profile sync from local browser to cloud
  - secrets scoped to allowed domains
  - 1Password/TOTP workflows in docs
- Concrete evidence:
  - `examples/browser/save_cookies.py:1-45` exports storage state from a real Chrome profile
  - `skills/open-source/references/browser.md:173-187` documents connecting to a real browser profile
  - `skills/cloud/references/sessions.md:55-95` documents persistent profiles and profile sync
  - `skills/cloud/references/sessions.md:97-155` documents profile sync, domain-scoped secrets, profiles-plus-secrets, and 1Password
  - `skills/open-source/references/examples.md:99-134` documents sensitive data placeholders and storage-state preference
- Why this matters for Keystone:
  - This is probably Browser Use's strongest strategic value for Keystone: hard, login-gated, stateful acquisition.
  - It does not remove governance work; it just improves access to sites Keystone's governed fetch layer may struggle to reach directly.

### 7. Security/guardrail machinery is stronger than typical browser-agent projects

- Likely value to Keystone: `HIGH`
- What seems supported:
  - domain allowlists with anti-bypass logic
  - prohibited domain blocklists
  - optional IP blocking
  - large blocklist optimization
  - domain-scoped secrets
- Concrete evidence:
  - `tests/ci/security/test_domain_filtering.py:4-255` covers auth-credential URL bypass attempts, glob semantics, browser-internal URLs, and root-domain handling
  - `tests/ci/security/test_ip_blocking.py:14-260` covers IPv4/IPv6/public/private/loopback blocking and precedence against allowlists
  - `examples/features/large_blocklist.py:1-109` demonstrates a 439k-domain blocklist with optimized lookup
  - `examples/features/restrict_urls.py:19-37` shows runtime domain restriction in practice
  - `examples/features/secure.py:67-76` shows allowed domains plus sensitive placeholders
- Why this matters for Keystone:
  - This makes Browser Use more acceptable as a constrained fallback browser.
  - It is still not the same thing as Keystone control-plane authority enforcement, but it reduces operational risk at the browser boundary.

### 8. Observability is broader than screenshots: conversation logs, traces, HAR, video, live monitoring, public share

- Likely value to Keystone: `MEDIUM`
- What seems supported:
  - saved conversation transcripts
  - local traces/HAR/video paths
  - live session view
  - public share URLs
  - cloud output-file retrieval
  - task logs in cloud
- Concrete evidence:
  - `skills/open-source/references/browser.md:92-99` documents `record_video_dir`, `record_har_path`, and `traces_dir`
  - `examples/features/video_recording.py:9-21` records browser session video
  - `examples/features/process_agent_output.py:21-49` uses `traces_dir` and inspects history/model actions/thoughts
  - `tests/ci/browser/test_output_paths.py:141-173` verifies saved conversation paths
  - `skills/cloud/references/sessions.md:39-52` documents `live_url` and public share links
  - `skills/cloud/references/patterns.md:94-120` documents retrieval of downloaded task files by presigned URL
  - `skills/cloud/references/guides/subagent.md:181-199` documents create-task, poll, get-result workflow returning steps and output files
- Why this matters for Keystone:
  - This is useful for operator visibility and debugging.
  - It is not enough for governed provenance. HAR/traces/live URLs are operational artifacts, not Keystone evidence bundles.

### 9. Browser Use explicitly supports two very different integration modes, which matters for Keystone boundary design

- Likely value to Keystone: `VERY_HIGH`
- What seems supported:
  - black-box delegated subagent mode
  - lower-level tool-integration mode where the host agent stays in control
  - local MCP and cloud MCP patterns
  - CLI daemon for action-by-action browser control
  - CDP reuse from external tools like Playwright/Puppeteer
- Concrete evidence:
  - `skills/cloud/references/guides/subagent.md:17-29` says when to use Browser Use as a delegated subagent
  - `skills/cloud/references/guides/tools-integration.md:16-38` says when to use Browser Use as a tool surface instead
  - `skills/cloud/references/guides/tools-integration.md:41-92` documents CLI command flow with persistent daemon and `state`
  - `skills/cloud/references/guides/tools-integration.md:132-153` documents MCP-native browser tools
  - `skills/cloud/references/guides/tools-integration.md:156-185` documents "zero code change" stealth-browser reuse for existing Playwright/Puppeteer
  - `examples/browser/playwright_integration.py:1-257` shows shared CDP control plus custom Playwright-backed tools
  - `examples/browser/using_cdp.py:1-45` shows direct Browser Use use over CDP
- Why this matters for Keystone:
  - This strongly supports using Browser Use, if at all, as a bounded acquisition adapter rather than as a replacement retrieval architecture.
  - The deeper pass made this boundary clearer and more defensible.

### 10. Search/research support exists in more than one layer, including a separate cloud Search API

- Likely value to Keystone: `MEDIUM`
- What seems supported:
  - browser-based search through the normal tool surface
  - custom web search tool injection
  - cloud Search API that browses multiple sites or a target URL with depth control
- Concrete evidence:
  - `skills/open-source/references/tools.md:101-123` includes built-in `search`
  - `examples/custom-functions/advanced_search.py:36-65` replaces default search with a custom Serper-backed search tool
  - `examples/getting_started/04_multi_step_task.py:35-54` shows multi-step research across search, article selection, and source visits
  - `examples/cloud/05_search_api.py:1-12` describes multi-site and target-URL browsing search
  - `examples/cloud/05_search_api.py:35-77` implements multi-site search
  - `examples/cloud/05_search_api.py:80-122` implements target URL search with depth
  - `examples/cloud/README.md:88-110` documents Search API cost/depth patterns and says it browses real sites rather than cached results
- Why this matters for Keystone:
  - This is potentially useful for sidecar exploration and competitor/control-arm comparison.
  - It is cloud-specific and black-box enough that it does not belong in Keystone's governed canonical path.

### 11. Evaluation and benchmark infrastructure is more substantial than I initially gave it credit for

- Likely value to Keystone: `HIGH`
- What seems supported:
  - task-pack style evaluation
  - per-task judge criteria
  - subprocess isolation for parallel task execution
  - in-run judging / ground-truth comparisons
- Concrete evidence:
  - `tests/ci/evaluate_tasks.py:1-185` runs agent tasks in isolated subprocesses and judges outputs
  - `tests/agent_tasks/README.md:1-29` defines contributed task format with `judge_context`
  - `tests/agent_tasks/amazon_laptop.yaml:1-7` and `tests/agent_tasks/browser_use_pip.yaml:1-5` show benchmark task specs
  - `examples/features/judge_trace.py:21-43` shows run-time judging against `ground_truth`
- Why this matters for Keystone:
  - This makes Browser Use more attractive as a control arm or benchmark subject than as a production canonical retriever.
  - The deeper pass strengthened the `BENCHMARK_OR_CONTROL_ARM_ONLY` secondary classification.

### 12. Reliability/resilience features are explicit and tested

- Likely value to Keystone: `MEDIUM`
- What seems supported:
  - retry logic with exponential backoff
  - fallback LLM switching on provider failures
  - inline planning/replanning
  - step history timing
- Concrete evidence:
  - `skills/open-source/references/agent.md:45-46` documents fallback LLM switching behavior
  - `examples/features/fallback_model.py:1-52` demonstrates fallback model usage
  - `tests/ci/test_fallback_llm.py:1-257` covers fallback switching on 429/401/402/500/502/503
  - `tests/ci/test_llm_retries.py:20-179` covers exponential backoff and timeout retries
  - `tests/ci/test_agent_planning.py:49-220` covers plan generation, step advancement, replanning, and replan nudges
- Why this matters for Keystone:
  - Useful for a sidecar browser acquisition lane.
  - Still not a substitute for Keystone's own deterministic retrieval governance.

## Most Important "Missable" Takeaways

- The rerun/replay subsystem is probably the single most under-advertised capability for Keystone-adjacent work.
- The profile/session/auth stack is stronger than a quick skim suggests and is the clearest reason Browser Use could help Keystone.
- The file/PDF/document pathway is real and tested enough to matter for acquisition.
- The repo itself nudges integrators toward either:
  - black-box delegation, or
  - narrow browser-tool integration,
  not toward replacing a governed evidence pipeline.

## What This Still Does Not Change

Even after the deeper pass, Browser Use still does not appear to provide the things Keystone most critically needs from the canonical retrieval path:

- governed evidence bundles
- deterministic parse contracts for evidence
- stable anchored citation production
- canonical provenance semantics at Keystone's standard
- control-plane authority enforcement at Keystone's standard

So the deeper pass raises Browser Use's value as:

- fallback browser-native acquisition
- authenticated/dynamic-site access layer
- benchmark/control arm
- replay/debugging sidecar

It does not raise it to:

- canonical governed retrieval path

## Updated Keystone Read

- Best fit: `FALLBACK_ONLY`
- Strong secondary fit: `BENCHMARK_OR_CONTROL_ARM_ONLY`
- Still not supported by this evidence: `CANONICAL_CANDIDATE`
