# Token economics in agent harnesses, April 2026

Agent harnesses now compete on a single metric: how many cents per agent-turn they burn against Anthropic's prompt-cache pricing. **Claude Code's leaked source (March 31, 2026) revealed a named sentinel — `__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__` — that explicitly splits globally-cacheable static content from session-scoped dynamic content**, alongside a `promptCacheBreakDetection.ts` module that tracks exactly 14 invalidation vectors. This report synthesizes the mechanics across five layers: Claude Code's prompt structure, its Fork/Teammate/Worktree subagent models, Anthropic's `cache_control` API surface, the MCP transport choices that determine cache eligibility, and the OpenClaw gateway's failover and cost-aggregation patterns. The thread running through all five is the same: **agent economics collapses to keeping a byte-identical prefix hashable against a 0.1× cache-read rate** rather than re-paying the 1.25× or 2× cache-write premium. Where evidence rests on community reverse-engineering of leaked source, that provenance is flagged inline.

## How Claude Code structures its prompt for cache locality

Claude Code's v2.1.88 source map leak (npm `@anthropic-ai/claude-code`, 59.8 MB `cli.js.map`, subsequently DMCA'd but widely mirrored) exposed the constant **`export const SYSTEM_PROMPT_DYNAMIC_BOUNDARY = '__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__'`** in `constants/prompts.ts`. The marker is a client-side sentinel stripped before API dispatch; its role is to tell the request builder (`splitSysPromptPrefix` in `src/utils/api.ts`) where to cut the system prompt into two scopes: content before the marker carries `cacheScope: 'global'` (shareable across all customers for a given CC version + model combination) with a **1-hour `ephemeral` TTL**, while content after carries session scope with a **5-minute TTL**. The static prefix alone runs ~4,000 tokens, comfortably clearing the 1,024-token minimum for Sonnet and the newer 4,096-token minimum for Opus 4.5+ and Haiku 4.5.

The static prefix is assembled in a fixed order by `buildEffectiveSystemPrompt()`: identity and cyber-risk instruction, markdown/permission/hooks rules, task-execution guidance (YAGNI, security), the reversibility/blast-radius taxonomy, tool-usage norms, tone and style, and output-efficiency rules. The dynamic tail is a registry of memoized sections (`systemPromptSection(...)`) — `memory` (CLAUDE.md hierarchy capped at 200 lines / 25,000 bytes), `env_info_simple` (cwd, git status, shell), `language`, `output_style`, `token_budget` — plus exactly one volatile section, `mcp_instructions`, wrapped in `DANGEROUS_uncachedSystemPromptSection` because MCP servers can connect or disconnect mid-session. **Tool definitions live in the separate API `tools[]` parameter but sit between `tools` and `system` in the cache hierarchy `tools → system → messages`**; v2.1.89 added `toolSchemaCache` (minified names `Ibq/xbq/eD8`), a session-lifetime Map keyed on `tool.name + JSON.stringify(inputJSONSchema)`, closing a regression where `tool.prompt()` was re-invoked every request and caused the `AgentTool` dynamic agent list alone to burn **~10.2% of fleet cache-creation tokens** per a quoted internal comment.

### The 14 cache-break vectors in `promptCacheBreakDetection.ts`

The module is telemetry-only (event `tengu_prompt_cache_break`, fires when `cache_read` drops >5% and >2,000 tokens turn-over-turn, Haiku excluded). The enumerated fields, reconstructed from multiple independent leak analyses (Marianski, kubesimplify, Alex Kim, claudefa.st), are:

| # | Field | Signal |
|---|---|---|
| 1 | `systemPromptChanged` | Hash of `system[]` minus `cache_control` |
| 2 | `toolSchemasChanged` | Hash of `tools[]` minus `cache_control` |
| 3 | `modelChanged` | Model string swap (e.g., `sonnet-4-6` → `opus-4-6`) |
| 4 | `fastModeChanged` | Fast-mode boolean |
| 5 | `cacheControlChanged` | Hash of cache_control fields (scope + TTL flips) |
| 6 | `globalCacheStrategyChanged` | Enum `tool_based \| system_prompt \| none` |
| 7 | `betasChanged` | Sorted `anthropic-beta` header diff |
| 8 | `autoModeChanged` | Auto-mode toggle; **sticky-latched** to avoid mid-session busts |
| 9 | `overageChanged` | Quota state; also sticky-latched |
| 10 | `cachedMCChanged` | CACHED_MICROCOMPACT toggle |
| 11 | `effortChanged` | Extended-thinking effort level |
| 12 | `extraBodyChanged` | Hash of `CLAUDE_CODE_EXTRA_BODY` env JSON |
| 13 | `addedTools`/`removedTools` | Per-tool name set diff |
| 14 | `changedToolSchemas` | Per-tool schema hash (which tool changed) |

A critical documented blind spot: **the 14 vectors hash `system[]` and `tools[]` but not `messages[]`**, so the resume-mode attachment relocation bug (GitHub issue #40524, introduced v2.1.69 via `deferred_tools_delta`) silently breaks cache while the telemetry logs "prompt unchanged, likely server-side." Anthropic's own quoted BigQuery comment in the source estimates ~90% of breaks under those conditions are server-side routing or eviction. Other real invalidators outside the 14-vector taxonomy include midnight date rollover via `getLocalISODate()` in `getUserContext` (fixed post-v2.1.68 by keeping the stale date and emitting a `date_change` tail attachment), the WebSearch tool's monthly `getLocalMonthYear()` description churn (fixed by `toolSchemaCache`), `/login` account switching (new `account_uuid` → new cache key), and the universal Anthropic rules: image add/remove, `tool_choice.type` change, and non-tool-result user content inserted after thinking blocks (strips thinking).

## Fork, Teammate, and Worktree: three subagent economics

The "Fork / Teammate / Worktree" taxonomy is a community synthesis of leak filenames (`forkSubagent.ts`, `spawnMultiAgent.ts`, `AgentTool.tsx` with `createAgentWorktree`), user-facing frontmatter (`context: fork` in skills, `isolation: worktree` in agents), and the experimental flag `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` introduced in v2.1.32 on February 5, 2026. Anthropic has not published this taxonomy as a unified term, but the three code paths are distinct.

**Fork** is the cache-preserving path. When the Agent (née Task) tool is invoked without a `subagent_type` and the `FORK_SUBAGENT` feature gate is active, `AgentTool.tsx` routes to `forkSubagent.ts` which constructs a `FORK_AGENT` with `permissionMode: 'bubble'` and `useExactTools: true`. The mechanism that makes cache inheritance work is explicit in the leaked source: **`renderedSystemPrompt` is threaded from parent to child as already-rendered bytes rather than being regenerated**, because a single-bit drift (from a feature flag that warmed up between parent build and fork spawn) would bust the prefix hash. `buildForkedMessages()` clones the parent's last assistant message verbatim including all `tool_use`, thinking, and text blocks, then replaces every `tool_result` with the identical placeholder `"Fork started — processing in background"`, and appends exactly one per-child directive. The result: N parallel forks differ only in the trailing directive, so all N pay cache-read at **0.1× base input** on the entire shared prefix. The `model` parameter is explicitly ignored because model swaps break cache — a constraint enforced in code, not policy. Recursion guards prevent fork-of-fork via a `query.source` marker and a `<fork-boilerplate>` tag that survives compaction.

**Teammate** spawns via `spawnTeammate()` when both `team_name` and agent `name` are resolved. It is an **out-of-process worker** with auto-detected backend priority (tmux-inside > tmux-on-PATH > iTerm2 > in-process AsyncLocalStorage). Crucially, the worker receives `messages: []` — it does not inherit conversation history and builds its own system prompt with a teammate addendum plus the custom agent prompt. Result: **full cache-write at 1.25× (5-minute) on first request**, with each teammate maintaining an independent cache; no sharing with the leader. Teammates stay on 5-minute TTL by design because writing at 2× for a subagent that may never hit again is a net loss. Communication uses file-based JSON mailboxes at `~/.claude/teams/{team_name}/inboxes/{agent_name}.json` with advisory locks (10 retries, 5–100ms exponential backoff) and a structured protocol (shutdown_request/approved/rejected, permission_request/response, plan_approval, task_assignment).

**Worktree** is an isolation *modifier* rather than a third execution model — it is orthogonal and can be combined with either Fork or Teammate. Triggered by `isolation: worktree` frontmatter, `--worktree` CLI flag, or the `/batch` slash command, `createAgentWorktree(slug)` runs before `runAgent()`, creating `.claude/worktrees/{slug}/` with branch `claude-wt-{timestamp}-{slug}`. Heavy directories (`node_modules`, `.next`) are symlinked; `.worktreeinclude` files are copied; cleanup uses `hasWorktreeChanges()` diffed against pre-spawn HEAD and is **fail-closed** (any git error preserves the worktree). **Worktree has no direct prompt-cache effect** because cache keys hash bytes, not filesystem state, and CWD-dependent strings land in the dynamic suffix rather than the cached static prefix. A Fork-in-worktree injects a `worktreeNotice` as a user message after the cache breakpoint, so the prefix stays intact.

The token-economics contrast is sharp. Anthropic's own published figures on multi-agent workflows cite **~4–7× token usage versus single-agent for teammate-style parallelism, and ~15× for full Agent Teams**. Fork, by contrast, amortizes: running five fork children against a 50,000-token parent context costs roughly the parent's cache-write once, plus five cache-reads at 0.1× — the widely-cited community claim that "five fork agents cost barely more than one" is consistent with the mechanics under maximum-cache-hit conditions (same TTL window, identical prefix preserved, small per-child directive). Compaction itself is architecturally a fork: it reuses system + tools + CLAUDE.md verbatim and only replaces the message portion with a "summarize" directive, keeping the cache warm.

## Anthropic's prompt caching API, exactly as specified

The canonical docs now live at `docs.claude.com/en/docs/build-with-claude/prompt-caching` (the `docs.anthropic.com` URL 302s there; `platform.claude.com` mirrors identical content). The `cache_control` object accepts only `"type": "ephemeral"`; there is no persistent type. TTL is selected via an optional `ttl` field accepting exactly `"5m"` or `"1h"`:

```json
{"cache_control": {"type": "ephemeral", "ttl": "1h"}}
```

Placement is permitted on content blocks in `tools`, `system` array entries, `messages[].content` (user and assistant, including `tool_use` and `tool_result` blocks), images, and documents. **A 2026 addition allows a single top-level `cache_control` on the request body** — the system auto-applies it to the last cacheable block and advances automatically with conversation, but consumes one of the **four explicit breakpoints-per-request cap**; exceeding four returns HTTP 400. Thinking blocks cannot carry `cache_control` directly but are implicitly cached alongside other assistant content and count as input tokens when read.

The pricing multipliers are universal across models: **5-minute cache write at 1.25× base input**, **1-hour cache write at 2× base input**, **cache read at 0.1× base input (a 90% discount)**. TTL refreshes on every successful hit at no additional cost — sliding-window behavior. Mixing TTLs in one request is allowed but 1-hour breakpoints must appear *before* 5-minute ones in the prefix; billing splits into three positions (cache-read for tokens up to the highest hit, 1h-write for the 1h segment, 5m-write for the tail). **No beta header is required on the current Anthropic direct API** — 1-hour TTL is documented as GA — though `anthropic-beta: extended-cache-ttl-2025-04-11` is still accepted and is still injected by some older integrations (notably Spring AI).

Minimum cacheable tokens were raised in the 2026 refresh. **Opus 4.5+ and Haiku 4.5 now require 4,096 tokens minimum**; Sonnet 4.6 sits at 2,048; Sonnet 4.5, Sonnet 4, Opus 4.1, Opus 4, and legacy Sonnet 3.7 remain at 1,024. Requests below threshold succeed silently without caching — both `cache_creation_input_tokens` and `cache_read_input_tokens` return 0. Note the newly-surfaced "Claude Mythos Preview" model listed with a 4,096 minimum and linking to anthropic.com/glasswing; treat as preview until confirmed.

The `usage` response object returns:

```json
{
  "input_tokens": 2048,
  "cache_read_input_tokens": 1800,
  "cache_creation_input_tokens": 248,
  "output_tokens": 503,
  "cache_creation": {
    "ephemeral_5m_input_tokens": 456,
    "ephemeral_1h_input_tokens": 100
  }
}
```

Critically, `input_tokens` counts **only tokens after the last cache breakpoint** — the uncached suffix — so total input processed equals `cache_read + cache_creation + input_tokens`. Cache-prefix matching uses a **20-block automatic lookback window**; conversations that grow past that without an explicit breakpoint will miss. Tool-use blocks with unstable JSON key ordering (Swift/Go hash-map randomization is the common culprit) will silently break cache despite semantic equivalence. **Workspace-level cache isolation** shipped February 5, 2026 on the Claude API and Azure AI Foundry preview (Bedrock and Vertex remain org-level), and cache hits do not count against rate limits — a meaningful argument for 1-hour TTL on high-QPS harnesses.

One April 2026 community report (GitHub issue `anthropics/claude-code` #46829) alleges a silent default-TTL regression from 1h to 5m for Claude Code paths. **This is not reflected in official docs** and should be treated as community claim pending Anthropic confirmation.

## MCP transport choices as cache economics

The Model Context Protocol spec at modelcontextprotocol.io defines three transports across recent versions, and the choice directly determines whether an agent's tool prefix remains byte-identical turn-over-turn. **Agent-side prompt caching hashes `tools → system → messages` in order**, so any byte reorder in the emitted tool array cascades invalidation through every downstream layer.

**stdio** (newline-delimited JSON-RPC over subprocess stdin/stdout, stderr reserved for logs, no embedded newlines) offers the cleanest cache properties: a long-lived subprocess with tools registered at import time via `@mcp.tool` decorators produces a deterministic, bit-stable `tools/list` response across turns. **HTTP+SSE** (the 2024-11-05 dual-endpoint model — GET `/sse` for the stream, POST to an `endpoint`-event URL for messages) was deprecated in 2025-03-26 primarily because sticky-session requirements broke standard load balancers. **Streamable HTTP** is the current standard: a single `/mcp` endpoint supporting both POST and GET, with the client MUST-sending `Accept: application/json, text/event-stream`. Server responses are either `202 Accepted` (for notifications), `application/json` (single response), or `text/event-stream` (streamed JSON-RPC).

Session management uses the **`Mcp-Session-Id` response header** issued on `InitializeResult` (ASCII 0x21–0x7E, cryptographically secure UUID/JWT/hash), which the client MUST echo on every subsequent request; 400 if missing, 404 if terminated. The 2025-06-18 spec additionally mandates the **`MCP-Protocol-Version` header** on all post-initialization HTTP requests (default inference is contested — spec says 2025-06-18, tracked bug #854 argues 2025-03-26, so implementers should send explicitly). Resumability uses SSE `id` fields and `Last-Event-ID` on reconnect, with servers replaying only from the disconnected stream. Security MUSTs: validate `Origin` (DNS rebinding defense) and bind local servers to 127.0.0.1.

The caching consequences sort cleanly:

| Transport | Tool-list byte-stability | Cache friendliness |
|---|---|---|
| stdio | High — single process, deterministic registration | Excellent |
| Streamable HTTP + `Mcp-Session-Id` (stateful) | High when session pins to one server instance | Good |
| Streamable HTTP stateless (no session) | At risk — LB-spread replicas may order tools non-deterministically | Fragile |
| HTTP+SSE | Same risks as stateless Streamable HTTP | Deprecated |

### FastMCP patterns that shape token cost

FastMCP (jlowin/fastmcp, integrated as `mcp.server.fastmcp` in Anthropic's python-sdk) registers tools via `@mcp.tool` decorators where the function name becomes `tool.name`, the docstring becomes the tool description shipped verbatim on every request, and type hints compile to JSON Schema with `$ref`s **dereferenced at serve-time** — meaning every use of a shared Pydantic model is inlined as a full copy. A long docstring ships every turn; dynamic interpolation (timestamps, user IDs) is catastrophic because it invalidates the entire tools prefix. Issue #1756 in the FastMCP repo tracks a `use_docstrings=True` flag for `FastMCP.from_fastapi()` precisely because the auto-generated verbose descriptions combining `description=` + Query Parameters + Responses were bloating token counts.

The core MCP method signatures matter for planning cache strategy. `tools/list` and `resources/list` are cursor-paginated — `{"cursor": "opaque-string"}` request, `{"nextCursor": "..."}` response — so aggregator implementations merging multiple upstream servers must sort deterministically across pages. `resources/subscribe` emits `notifications/resources/updated` with URI only (content fetched on demand via `resources/read`), which is token-efficient. `notifications/tools/list_changed` is a double-edged capability: it enables dynamic tool availability but each fire triggers a fresh `tools/list`, new tool-block bytes, and total hierarchy invalidation — **so dynamic enable/disable mid-conversation should be avoided**.

The 2025-06-18 spec added **structured tool output** (`outputSchema` on `tools/list` entries, `structuredContent` on `tools/call` results) and the `resource_link` content type — the latter is a major token win because tools can return URIs instead of inlined blobs, letting the client fetch only when needed. The spec also removed JSON-RPC batching (breaking change from 2025-03-26) and introduced elicitation (`elicitation/create` with `accept/decline/cancel` actions, primitives-only schema).

The practical server-side rules reduce to: sort `tools/list` alphabetically; never interpolate dynamic content into tool descriptions or input schemas; push bulky context to `@mcp.resource` (application-controlled, lazy) rather than `@mcp.tool` (model-controlled, eagerly shipped); use `resource_link` returns for large results; avoid `list_changed` during active conversation; prefer stdio for local agents; for remote, use Streamable HTTP with `Mcp-Session-Id` to pin sessions to one server instance. OpenClaw's live regression study (`docs.openclaw.ai/reference/prompt-caching`) reports MCP-style tool transcripts plateau around 4,096–4,608 tokens of cached reads with 0.85–0.89 hit rates when prefixes are held stable, dropping sharply with dynamic churn.

## OpenClaw's failover and cost-aggregation model

OpenClaw is a real, actively developed self-hosted agent runtime and gateway (MIT-licensed Node.js, with a `clawdotnet/openclaw.net` NativeAOT .NET port), rebranded from prior `clawdbot` / `moltbot` — legacy directory fallbacks are still visible in `~/.openclaw/agents/` path resolution. It is a **personal-assistant-first local runtime** rather than a multi-tenant commercial gateway (closer in positioning to OpenCode than to LiteLLM Proxy or Portkey), though it ships gateway, failover, and cost-tracking features. The control plane is a WebSocket server on default port **18789** (dev `19001`), bind modes `loopback` (default, and enforced unless auth is configured) / `lan` / `tailnet` / `auto` / `custom`, supervised by systemd on Linux or the `ai.openclaw.gateway` LaunchAgent on macOS. Config lives at `~/.openclaw/openclaw.json` with **strict schema validation — the gateway refuses to start on unknown keys**.

### The two-stage failover chain

Failure handling is split between auth-profile rotation within a provider and model fallback across a configured chain:

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "anthropic/claude-sonnet-4-6",
        "fallbacks": [
          "openai-codex/gpt-5.2",
          "anthropic/claude-sonnet-4-5"
        ],
        "failover": {
          "enabled": true,
          "retryPrimaryAfterSeconds": 900,
          "on": ["rate_limit", "auth_cooldown", "provider_unavailable", "timeout"]
        }
      }
    }
  }
}
```

The runtime tries auth-profile rotation inside the current candidate before advancing to the next model — **auth-profile exhaustion is required to move down the chain**. Rate-limit detection is broad and matches patterns beyond plain HTTP 429: `ThrottlingException`, "concurrency limit reached", "workers_ai quota limit exceeded", "throttled", "resource exhausted", weekly/monthly limit text. Failover-worthy provider errors include `Unhandled stop reason: error`, Anthropic's bare "An unknown error occurred", `api_error` with transient markers ("internal server error", "520", "upstream error", "backend error"), and OpenRouter-specific "Provider returned error" (only when provider context is OpenRouter). **Context-overflow errors explicitly do not trigger fallback** — they remain in compaction/retry logic: `request_too_large`, `INVALID_ARGUMENT: input exceeds the maximum number of tokens`, "ollama error: context length exceeded".

Rate-limit cooldowns can be model-scoped via a recorded `cooldownModel`, so a sibling model on the same provider remains usable. **Sessions pin the chosen auth profile to keep provider caches warm** — profiles are reused until `/new`, `/reset`, compaction completes, or the profile enters cooldown/disabled. One known broken interaction (Issue #64961, April 11, 2026): **tool schemas are not re-normalized on fallback**, so when primary `azure/gpt-5.4` fails over to `azure/grok-4-1-fast-reasoning` the new provider rejects the payload — `cleanToolSchemaForGemini` and `normalizeStrictOpenAIJsonSchema` exist but apply once upstream, not per-attempt.

### Retry policies and a documented bug

Channel-level retries for Telegram and Discord are configurable with defaults `{attempts: 3, minDelayMs: ~400, maxDelayMs: 30000, jitter: 0.1}`, retrying on 429, timeout, connect/reset/closed, and "temporarily unavailable", honoring `retry_after` headers when present. Retries execute per HTTP request, not per multi-step flow, to preserve ordering.

The auth-profile cooldown is documented as exponential backoff **1 min → 5 min → 25 min → 1 hour cap**, stored in `~/.openclaw/agents/<agentId>/agent/auth-profiles.json` as `{usageStats: {"provider:profile": {cooldownUntil, errorCount}}}`. **Issue #5159 (closed as "not planned") confirms the documented 1/5/25/60-minute intervals do not match actual behavior** — users observed 1–27 second intervals. Workaround guidance points to LiteLLM proxy in front for proper retry handling. Billing failures (e.g., "insufficient credits") are not transient cooldowns but hard disables written as `{disabledUntil, disabledReason: "billing"}` with a default 5-hour duration doubling per failure, capped at 24 hours (keys: `auth.cooldowns.billingBackoffHours`, `auth.cooldowns.billingBackoffHoursByProvider`, `auth.cooldowns.billingMaxHours`, `auth.cooldowns.failureWindowHours`).

**LLM-provider-level retry is not natively implemented** — Issue #24321 (February 23, 2026, still open) proposes a `providers.<name>.retry` schema with `{attempts, minDelayMs, maxDelayMs, jitter, timeoutMs}` but it has not shipped; the earlier Issue #8894 requesting automatic 429 backoff was closed as "not planned". `DEFAULT_AGENT_TIMEOUT_SECONDS = 600` caps agent runs at 10 minutes. There is no request-level circuit breaker with half-open probes; the auth-profile cooldown state acts as the functional equivalent.

### Cost and token aggregation

OpenClaw normalizes provider-specific token fields into a unified vocabulary: **`input`, `output`, `cacheRead`, `cacheWrite`, `reasoning`**. Anthropic's `cache_creation_input_tokens` maps to `cacheWrite`; `cache_read_input_tokens` maps to `cacheRead`. OpenAI Responses aliases (both `input_tokens`/`output_tokens` and `prompt_tokens`/`completion_tokens`) are accepted; Gemini CLI `stats.cached` maps to `cacheRead`, with `stats.input_tokens - stats.cached` filling in missing explicit input. Session totals fall back to `input + output` when `total_tokens` is absent. Usage is persisted as JSONL transcripts at `~/.openclaw/agents/<agentId>/sessions/<SessionId>.jsonl`:

```json
{"type":"message","message":{"role":"assistant","usage":{"input":1660,"output":55,"cacheRead":108928,"cost":{"total":0.02}},"timestamp":1769753935279}}
```

Pricing is configured per model under `models.providers.<provider>.models[].cost` as USD per 1M tokens for `input`, `output`, `cacheRead`, `cacheWrite`. **OAuth-authenticated profiles never show dollar cost — only API-key auth gets $ estimates**, because Anthropic's OAuth rate windows differ from metered API pricing. Aggregation surfaces include `/status` (emoji card with session model, context usage, last response tokens, estimated cost), `/usage off|tokens|full` (per-response footer, persisted per session), `/usage cost` (local summary), and `openclaw status --usage` for normalized provider quota windows (Anthropic, GitHub Copilot, Gemini CLI, OpenAI Codex, MiniMax, Xiaomi, z.ai). Per-org or per-team aggregation is absent — OpenClaw is single-tenant by design.

Prompt-caching is configured via `OpenClaw:Llm:PromptCaching` (.NET port) or per-model profile, with dialects `openai | anthropic | gemini | none` (dynamic `openai-compatible` providers must opt in). `cache-ttl pruning` prunes the session once the cache TTL expires, and a **`heartbeat` field keeps the cache warm** (e.g., `every: "55m"` for a 1h TTL window). Per-agent `agents.list[].params.cacheRetention` allows tuning. Context management uses `agents.defaults.contextPruning.mode = "cache-ttl"` with `{ttl, keepLastAssistants, softTrim: {maxChars, headChars, tailChars}, hardClear: {enabled}}`, plus `agents.defaults.bootstrapMaxChars` (default 20,000) for AGENTS.md / SOUL.md truncation. Routing is capability-tag based (`local`, `private`, `cheap`, `tool-reliable`, `vision`) rather than latency- or cost-optimized — OpenClaw explicitly defers price-based routing to OpenRouter (`sort: "price"`, `max_price: {prompt, completion}`) or a LiteLLM proxy upstream.

## Conclusion: the optimization surface is smaller than it looks

Five layers, one unifying rule: **preserve byte-identical prefix bytes up to the furthest breakpoint, or pay the 1.25×/2× premium**. Everything else is instrumentation. Claude Code's `__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__` makes the static/dynamic split explicit at the source-code level; its Fork path weaponizes this by threading `renderedSystemPrompt` verbatim and replacing `tool_result` blocks with literal placeholder strings so N parallel children hash to the same prefix. Teammate and Agent Teams give up this property and accept 4–15× token multipliers for the ability to run genuinely independent workers. Anthropic's four-breakpoint, 20-block-lookback, 0.1× cache-read pricing creates the hard incentive; MCP transports determine whether that incentive can actually be captured (stdio and session-pinned Streamable HTTP preserve tool-list bytes; stateless HTTP or dynamic `list_changed` fires destroy them). OpenClaw's real contribution to the economics is the normalized `cacheRead`/`cacheWrite` accounting and the session-sticky auth-profile pinning that keeps provider caches warm — its retry story, by contrast, has a publicly-acknowledged gap between documented and actual backoff intervals that shifts real retry responsibility upstream to LiteLLM.

The non-obvious insight across all five areas is that **cache invalidation is almost entirely self-inflicted through dynamic content leakage into static prefixes** — timestamps in tool descriptions, non-sorted tool lists from parallel replicas, re-rendered system prompts whose feature flags warmed up between parent and child spawn, tool schemas with randomized JSON key order, and `notifications/tools/list_changed` fires during active conversations. The engineering discipline required is not algorithmic sophistication but paranoid determinism: sort every list, freeze every schema, thread rendered bytes rather than regenerating them, and put an `anthropic-beta` header in exactly one place. The harnesses that are winning on cost in April 2026 are the ones that treat the cache prefix as an append-only immutable data structure.