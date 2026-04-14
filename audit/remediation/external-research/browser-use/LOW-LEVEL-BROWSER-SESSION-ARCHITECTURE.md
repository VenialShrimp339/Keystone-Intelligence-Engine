# Browser Use Low-Level Browser/Session Architecture

## Bottom Line

The low-level Browser Use stack is materially more valuable than the high-level `Agent` framing suggests.

There is a real reusable browser-control substrate under the agent loop:

- event-driven Chromium/CDP session orchestration
- direct tab/frame/node access
- rendered DOM fusion across DOM + AX + DOMSnapshot
- shadow DOM and cross-origin iframe handling
- network/HAR/download/session-state sidecars
- imperative `Page` / `Element` control without adopting the planner/agent layer

For Keystone, that increases Browser Use's value as a browser-native acquisition subsystem.

It still does not make Browser Use a canonical evidence or citation layer.

## 1. Core Architecture Map

- `BrowserSession` is the center of gravity. It is a two-layer design: event-driven browser orchestration plus direct CDP access, built on `bubus.EventBus` and `cdp_use.CDPClient` rather than a pure Playwright-style control path. See `browser_use/browser/session.py:100-230`, `browser_use/browser/session.py:641-669`, `browser_use/browser/session.py:1712-1899`.

- `SessionManager` is the real target/session registry. It auto-discovers page and iframe targets, listens for `Target.attachedToTarget` / `detachedFromTarget`, keeps target-to-session mappings, and does focus recovery when the active target disappears. This is not superficial glue; it is the single source of truth for live browser targets. See `browser_use/browser/session_manager.py:18-29`, `browser_use/browser/session_manager.py:56-112`, `browser_use/browser/session_manager.py:369-467`, `browser_use/browser/session_manager.py:497-748`.

- `BrowserSession.attach_all_watchdogs()` composes a browser runtime from specialized watchdogs: downloads, storage state, local browser launch, security policy, screenshots, DOM capture, HAR recording, captcha waiting, popup handling, and default browser actions. This is effectively Browser Use's browser middleware layer. See `browser_use/browser/session.py:1561-1710`.

- `DomService` builds an enhanced DOM model by fusing three CDP views of the page: DOM tree, accessibility tree, and DOM snapshot/layout data. It then recursively reconstructs iframe/shadow-root structure into `EnhancedDOMTreeNode`. See `browser_use/dom/service.py:376-652`, `browser_use/dom/service.py:653-1030`, `browser_use/dom/views.py:373-930`.

- `DOMTreeSerializer` turns that fused tree into a reduced, interaction-oriented representation with a `selector_map` keyed by backend node id, plus text/eval serializations. It contains a lot of pruning heuristics, shadow-DOM exceptions, scrollability logic, and stable-ish element hashing. See `browser_use/dom/serializer/serializer.py:41-148`, `browser_use/dom/serializer/serializer.py:435-540`, `browser_use/dom/serializer/serializer.py:617-838`, `browser_use/dom/views.py:930-1041`.

- The imperative actor layer is separate from the agent loop. `Page` and `Element` expose direct navigation, JS evaluation, CSS querying, clicking, typing, screenshots, and extraction. Keystone would not need to adopt the high-level `Agent` loop to use these surfaces. See `browser_use/actor/page.py:39-190`, `browser_use/actor/page.py:367-390`, `browser_use/actor/element.py:93-351`, `browser_use/actor/element.py:353-507`, `browser_use/actor/element.py:711-1175`.

## 2. Potentially Valuable Low-Level Surfaces For Keystone

- Direct browser/session control is reusable. `BrowserSession.connect()`, `get_or_create_cdp_session()`, `cdp_client_for_target()`, `cdp_client_for_frame()`, `cdp_client_for_node()`, `set_extra_headers()`, `take_screenshot()`, and `downloaded_files` give Keystone a low-level browser acquisition surface without the planner loop. See `browser_use/browser/session.py:1401-1487`, `browser_use/browser/session.py:1489-1510`, `browser_use/browser/session.py:3585-3825`, `browser_use/browser/session.py:3879-3965`, `browser_use/browser/session.py:3253-3259`.

- Cross-origin iframe handling is stronger than expected. Browser Use explicitly builds a unified frame map across page and iframe targets, marks OOPIFs, resolves parent frame metadata, and can route CDP operations to the correct frame target. That matters for modern news/article sites, embedded readers, paywall/login widgets, and vendor-hosted document panes. See `browser_use/browser/session.py:3585-3819`, `browser_use/dom/service.py:908-999`, `browser_use/browser/profile.py:628-640`.

- Rendered DOM capture is a genuine acquisition asset. `DomService` captures shadow roots, iframe content documents, AX names, layout bounds, scroll info, click-listener hints, and absolute positions. `HTMLSerializer` then reconstructs HTML including shadow DOM and iframe content before markdown conversion. For JS-heavy articles this is substantially better than naive `requests + Readability` on the hardest pages. See `browser_use/dom/service.py:653-1030`, `browser_use/dom/serializer/html_serializer.py:6-156`, `browser_use/dom/markdown_extractor.py:22-113`.

- The DOM state has low-level reuse beyond agent prompting. `EnhancedDOMTreeNode` carries `target_id`, `frame_id`, `session_id`, bounds, AX names, xpath, element hash, stable hash, and scroll info. That is not Keystone-ready evidence, but it is useful metadata for acquisition diagnostics, repeat interaction, or internal browser fallback tooling. See `browser_use/dom/views.py:373-899`, `browser_use/dom/views.py:976-1041`.

- PDF and file acquisition is better than a superficial read implies. `DownloadsWatchdog` does more than watch filesystem downloads: it can detect downloadable responses via `Network.responseReceived`, trigger generic file download via browser-context `fetch(..., cache: 'force-cache')`, detect Chrome PDF viewer cases, and auto-download a PDF from the browser session into a real file while emitting `FileDownloadedEvent`. See `browser_use/browser/watchdogs/downloads_watchdog.py:440-641`, `browser_use/browser/watchdogs/downloads_watchdog.py:643-790`, `browser_use/browser/watchdogs/downloads_watchdog.py:1048-1178`, `browser_use/browser/watchdogs/downloads_watchdog.py:1177-1371`.

- Session/auth persistence is reusable. `StorageStateWatchdog` loads/saves cookies plus local/session storage, merges state files, restores storage via init scripts scoped to origin, and can keep state across browser runs. That matters for authenticated retrieval and dynamic portals. See `browser_use/browser/watchdogs/storage_state_watchdog.py:49-86`, `browser_use/browser/watchdogs/storage_state_watchdog.py:167-345`.

- HAR capture is good enough to be useful as acquisition telemetry. `HarRecordingWatchdog` records HTTPS traffic, response bodies, request bodies, minimal page timing, server IP/TLS details, and can embed or sidecar content. This is not a governed evidence model, but it is meaningful provenance sidecar material for fallback acquisition debugging. See `browser_use/browser/watchdogs/har_recording_watchdog.py:144-205`, `browser_use/browser/watchdogs/har_recording_watchdog.py:210-425`, `browser_use/browser/watchdogs/har_recording_watchdog.py:489-669`.

- Browser state summaries can help a fallback acquisition controller. `DOMWatchdog` can assemble a `BrowserStateSummary` with DOM state, screenshot, page geometry, pagination hints, recent events, and pending network requests. Keystone should not treat this as evidence, but it is useful operational state for deciding whether browser escalation succeeded. See `browser_use/browser/watchdogs/dom_watchdog.py:91-239`, `browser_use/browser/watchdogs/dom_watchdog.py:241-536`, `browser_use/browser/views.py:17-112`.

- Security and access controls exist, but only at browser-session scope. `SecurityWatchdog` enforces allowed/prohibited domain policies and blocks redirects/new tabs outside the configured set. That is useful for sandboxing a fallback browser worker, but it is not a substitute for Keystone's own control-plane authority model. See `browser_use/browser/watchdogs/security_watchdog.py:22-232`.

## 3. Major Limitations And Risks

- This stack is still acquisition-first, not evidence-first. The low-level DOM/markdown path is designed for operability and LLM usability, not for deterministic evidence bundles, anchored offsets, or canonical citation locators. `extract_clean_markdown()` reconstructs HTML, runs `markdownify`, removes JSON-like blobs, and can chunk markdown by structure; none of that yields Keystone-grade anchors. See `browser_use/dom/markdown_extractor.py:22-178`, `browser_use/dom/views.py:930-1041`.

- DOM serialization is heuristic-heavy and may discard exactly the kind of detail Keystone cares about. The serializer applies visibility thresholds, paint-order filtering, bounding-box containment pruning, shadow-DOM exceptions, and "interactive only" indexing. Great for agent control; risky for canonical evidence capture. See `browser_use/dom/serializer/serializer.py:100-148`, `browser_use/dom/serializer/serializer.py:542-880`.

- Cross-origin iframe support is real but bounded. It is gated by visibility, minimum size, max iframe count, and max recursion depth. Small, hidden, or not-yet-registered dynamic iframes may be skipped. See `browser_use/dom/service.py:908-999`, `browser_use/browser/profile.py:628-640`.

- The imperative actor layer and the event-driven session layer are not perfectly unified. `Page._ensure_session()` can directly `Target.attachToTarget` and enable domains on its own, rather than always flowing through `SessionManager`. That is powerful, but it also means Keystone would need to choose one control style and integrate carefully. See `browser_use/actor/page.py:53-68`.

- File/PDF download logic is practical, but not fully deterministic. It relies heavily on network heuristics and browser-context `fetch()` to pull response bytes from the active session/cache. That is useful for acquisition, but it is still susceptible to auth token expiry, JS fetch restrictions, odd POST/download flows, and website-specific viewer behavior. See `browser_use/browser/watchdogs/downloads_watchdog.py:466-618`, `browser_use/browser/watchdogs/downloads_watchdog.py:706-790`, `browser_use/browser/watchdogs/downloads_watchdog.py:1262-1361`.

- HAR capture is helpful but incomplete for audit-grade transport reconstruction. It is HTTPS-only, filters favicon traffic, approximates DNS/connect/SSL timings as zero, and fetches response bodies asynchronously on `loadingFinished`. Good sidecar, not a complete deterministic network provenance layer. See `browser_use/browser/watchdogs/har_recording_watchdog.py:1-5`, `browser_use/browser/watchdogs/har_recording_watchdog.py:214-215`, `browser_use/browser/watchdogs/har_recording_watchdog.py:381-413`, `browser_use/browser/watchdogs/har_recording_watchdog.py:688-746`.

- Storage-state support is uneven depending on which surface Keystone uses. `StorageStateWatchdog` handles cookies plus `localStorage`/`sessionStorage`, but `BrowserSession.export_storage_state()` currently exports cookies and leaves `origins` empty. That is a real integration footgun if Keystone assumes one storage-state surface equals the other. See `browser_use/browser/watchdogs/storage_state_watchdog.py:167-345`, `browser_use/browser/session.py:1356-1399`.

- The launch/runtime profile is nontrivial and can materially alter page behavior. Browser Use launches Chromium with a large flag set, default extensions, optional proxying, optional disabled security, and optional anti-deterministic or anti-bot-related tweaks. `deterministic_rendering=True` is explicitly warned as not recommended because it breaks sites and raises block risk. This is not a "lightweight fetch helper." See `browser_use/browser/profile.py:27-186`, `browser_use/browser/profile.py:579-666`, `browser_use/browser/profile.py:771-777`, `browser_use/browser/profile.py:844-922`.

- Captcha handling is mainly a cloud/proxy-side integration, not an open-source universal superpower. The `CaptchaWatchdog` only becomes useful when the browser emits BrowserUse-specific captcha solver events. That is meaningful, but it is not a generic OSS answer to protected sites by itself. See `browser_use/browser/watchdogs/captcha_watchdog.py:1-10`, `browser_use/browser/watchdogs/captcha_watchdog.py:80-155`.

## 4. Surprising / High-Value Findings

- The strongest surprise is that Browser Use has a credible low-level browser acquisition layer even if Keystone ignores the agent loop entirely. `BrowserSession`, `SessionManager`, `DomService`, `Page`, `Element`, `DownloadsWatchdog`, `StorageStateWatchdog`, and `HarRecordingWatchdog` are each individually reusable.

- Cross-origin iframe support is a bigger differentiator than it looked on first pass. If Keystone eventually needs browser fallback for embedded readers, third-party hosted article panes, or interaction-gated vendor documents, Browser Use already has a meaningful OOPIF story instead of a same-origin-only toy DOM walker. See `browser_use/browser/session.py:3585-3819`, `browser_use/dom/service.py:908-999`.

- The PDF/download path is genuinely useful for retrieval fallback, not just agent demos. In sandbox smoke testing, direct low-level `BrowserSession` navigation to a public W3C dummy PDF triggered network-based download detection and saved a real PDF file without using the high-level agent loop. This matched the code path in `DownloadsWatchdog`. Runtime evidence was collected in the isolated sandbox only.

- The rendered-content extraction path is better framed as "browser-assisted acquisition text" than "agent output." The HTML reconstruction includes shadow DOM and iframe content, which means Browser Use can recover content that plain source fetchers miss. That is meaningful for hard article acquisition even though it is still not a canonical evidence parser. See `browser_use/dom/serializer/html_serializer.py:6-156`, `browser_use/dom/markdown_extractor.py:22-113`.

- The session sidecars are better than expected for fallback audit trails. Between HAR, screenshots, recent browser events, pending network requests, download metadata, and storage state, Browser Use can produce a useful acquisition trace package for debugging or post-hoc review. See `browser_use/browser/watchdogs/har_recording_watchdog.py:489-669`, `browser_use/browser/watchdogs/dom_watchdog.py:241-536`, `browser_use/browser/events.py:499-579`.

- The biggest surprise on the negative side is how much browser behavior Browser Use intentionally changes by default. Extensions, large Chrome flag sets, and browser-profile mutations may improve operability, but they also make this a poor fit for Keystone's canonical governed fetch path, where page semantics and artifact fidelity matter more than agent convenience. See `browser_use/browser/profile.py:601-616`, `browser_use/browser/profile.py:844-938`.

## 5. Concrete File Refs To Revisit

- Browser/session core:
  `browser_use/browser/session.py:100-230`, `browser_use/browser/session.py:1401-1510`, `browser_use/browser/session.py:1561-1710`, `browser_use/browser/session.py:1712-1899`, `browser_use/browser/session.py:3585-3965`

- Target/session registry:
  `browser_use/browser/session_manager.py:18-29`, `browser_use/browser/session_manager.py:56-112`, `browser_use/browser/session_manager.py:369-467`, `browser_use/browser/session_manager.py:497-900`

- DOM fusion and serialization:
  `browser_use/dom/service.py:376-652`, `browser_use/dom/service.py:653-1087`, `browser_use/dom/views.py:373-1041`, `browser_use/dom/serializer/serializer.py:41-148`, `browser_use/dom/serializer/serializer.py:435-880`

- Markdown / rendered extraction:
  `browser_use/dom/serializer/html_serializer.py:6-156`, `browser_use/dom/markdown_extractor.py:22-178`

- Downloads / PDFs:
  `browser_use/browser/watchdogs/downloads_watchdog.py:237-438`, `browser_use/browser/watchdogs/downloads_watchdog.py:440-790`, `browser_use/browser/watchdogs/downloads_watchdog.py:1048-1371`

- Session persistence / telemetry:
  `browser_use/browser/watchdogs/storage_state_watchdog.py:49-345`, `browser_use/browser/watchdogs/har_recording_watchdog.py:144-746`, `browser_use/browser/watchdogs/dom_watchdog.py:91-860`

- Direct imperative API:
  `browser_use/actor/page.py:39-190`, `browser_use/actor/page.py:367-564`, `browser_use/actor/element.py:93-1175`

- Launch/runtime behavior:
  `browser_use/browser/profile.py:27-186`, `browser_use/browser/profile.py:579-922`, `browser_use/browser/watchdogs/local_browser_watchdog.py:93-217`, `browser_use/browser/watchdogs/security_watchdog.py:22-232`

## Keystone Implication

This deeper pass raises Browser Use's ceiling for Keystone as a fallback acquisition subsystem.

It does not change the architectural boundary:

- stronger supplement than the first pass may have implied
- still not a canonical governed retrieval replacement
- best use remains browser-native acquisition fallback with Keystone-owned normalization afterward
