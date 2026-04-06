# LEAK-SYNTHESIS.md
*Cross-synthesis of 10 deep research reports on the Claude Code v2.1.88 leak*
*Produced: 2026-04-05 | Covers 512K-line TypeScript source, March 31, 2026*

---

## 1. Executive Summary

The full 512K-line TypeScript leak validates every major architectural decision already made for Keystone and adds six concrete engineering patterns the Python reimplementation (nano-claude-code) did not expose.

**What the leak validates (no changes needed):**
- Custom orchestration over framework adoption: Claude Code itself proves prompt-driven orchestration works at scale without LangChain/LangGraph
- Filesystem-based agent isolation with advisory locks: directly confirmed at 34M Explore agent runs per week
- Per-agent tool subsetting (3-5 tools): confirmed via `resolveAgentTools()` and `ASYNC_AGENT_ALLOWED_TOOLS` disallow-lists
- Model mixing (Opus/Sonnet/Haiku per role): confirmed as production pattern with hardcoded defaults per subagent type
- MCP as the tool architecture: Computer Use itself runs as `@ant/computer-use-mcp`, not special-cased
- Claim-level handoffs reducing context overhead: confirmed by "effective context engineering" (subagents return 1-2K summaries, not full contexts)

**What the full leak adds that nano-claude-code missed:**

Six patterns are new: (1) KAIROS tick-based daemon architecture; (2) autoDream four-phase memory consolidation; (3) 5-strategy compaction pipeline (nano has 2 layers; full has 5); (4) Tool Search progressive loading (87.9% context reduction); (5) 26-event hooks as universal lifecycle interceptor; (6) fork-mode byte-identical cache sharing for near-zero-cost parallelism. These are covered in detail in Section 5.

**Bottom-line verdict on the full leak:** It is a 6-month head start on production-grade agent engineering. The patterns are not theoretical -- they emerged from internal benchmarks, BigQuery telemetry, and 34M weekly runs. The only major failure mode: the agent harness was built for code editing, and several patterns (compaction re-injection, worktree isolation, KAIROS proactivity) need adaptation before they apply to research pipelines. The adaptation paths are clear and specified below.

**One correction to existing analysis:** The repo analysis (09-implementation-recommendations.md) describes a "two-layer compaction" pattern from nano-claude-code. The full leak reveals a five-strategy pipeline. This changes the compaction design for Component #7 but does not change any other architectural decision.

---

## 2. Agent SDK Assessment

**Verdict: SKIP as primary foundation. ADOPT selectively for L1 research agent subprocess execution.**

### Why not Agent SDK alone

The Agent SDK (formerly Claude Code SDK) bundles the full Claude Code CLI binary (~45MB) and communicates via subprocess/IPC. Three hard constraints make it unsuitable as Keystone's primary orchestration layer:

1. **Single-level subagent nesting only.** The 6-layer Keystone pipeline requires multi-level nesting: L0 spawns L1 agents, CitationProcessor runs sub-verification passes, L4 spawns evaluator critics. SDK's one-level restriction is an architectural ceiling, not a configuration option.

2. **No durable execution.** The SDK has no equivalent to Temporal's crash recovery. A 30-minute research session with 15 parallel agents that crashes at minute 29 re-runs from zero. This is unacceptable for a $12-$100 engagement where token costs are real.

3. **0.x versioning, ~12-second latency overhead per query.** The SDK is pre-1.0 (TypeScript v0.2.92 at time of analysis). Community reports confirm ~12 seconds of subprocess startup overhead per query. For a pipeline stage that may execute dozens of queries, this compounds to minutes of pure overhead.

Evidence quality: Credible (0.x version confirmed in SDK repos, latency overhead reported across multiple community sources, one-level nesting documented in official SDK docs).

### Where the Agent SDK adds value

The SDK's built-in tools (WebSearch, WebFetch, Read, Write, Bash, Agent) and battle-tested context compaction engine are genuinely useful for L1 research agents where the task is bounded: fetch, read, extract, report. Using SDK `query()` calls wrapped as Temporal Activities gives you the compaction engine and 40+ built-in tools without building them, while Temporal provides the durability the SDK lacks.

Specifically: Component #7 (Research Agent Pipeline) can use SDK subprocess calls for individual research agent turns, wrapped in Temporal Activities. Each L1 agent becomes a `query()` invocation with restricted tools and a Sonnet model override. The Activity wrapper provides retries, timeouts, and the heartbeat that Temporal needs for long-running work. This is the hybrid pattern recommended in deep-research-10.

### Patterns to extract from the leaked source vs. SDK

The SDK exposes the runtime. The leak exposes the reasoning. Extract these patterns from the leak directly rather than from the SDK API:

- Fork-mode cache sharing (not in SDK API surface, but the byte-identical prefix pattern is implementable in any framework)
- 5-strategy compaction cascade (implement as Temporal workflow escalation)
- 26-event hooks (implement as Temporal signals/activities at pipeline boundaries)
- autoDream consolidation (implement as scheduled Temporal workflow for Observation Library)

### What the single-level limitation actually closes off

Deep-research-10 frames this as a "hard architectural constraint." It is. The Keystone pipeline has this nesting structure:
```
L0 (orchestrator)
  └─ L1 agent (spawns)
      └─ MCP tool call (not an agent level, but)
  └─ CitationProcessor (stage)
  └─ L1.5 analyst agent (spawns multiple)
  └─ L4 evaluator (spawns critic agents)
```
That is at minimum three levels of agent nesting. SDK cannot express it. PydanticAI + Temporal can.

---

## 3. Community MCP Servers Inventory

Status as of April 2026. Phase 1 targets: Exa, Brave Search, EdgarTools, FRED, Academix. Eventual targets: CrossRef, Semantic Scholar, OpenAlex.

| Service | Community MCP Server | Status | Official? | Transport | Build vs. Integrate |
|---------|---------------------|--------|-----------|-----------|---------------------|
| **Exa** | `exa-labs/exa-mcp-server` | Production | Yes (official) | stdio + hosted HTTP | INTEGRATE directly. Official server, hosted endpoint, includes `research_paper_search` tool. |
| **Brave Search** | `brave/brave-search-mcp-server` | Production | Yes (official) | stdio + HTTP | INTEGRATE directly. Official, hosted endpoint, free tier ~1,000 queries/month. |
| **EdgarTools** | `dgunning/edgartools` with built-in MCP server | Production | Yes (library author) | stdio + HTTP | INTEGRATE directly. `edgartools` has 2.3M+ PyPI downloads, 1000+ tests, MIT license, ships its own MCP server and Claude Code skills. This is the most mature financial data server in the ecosystem. |
| **FRED** | `stefanoamorelli/fred-mcp-server` | Production | Community (high quality) | stdio + Docker | INTEGRATE directly. Covers all 800,000+ FRED time series, has a citable Zenodo DOI, Docker support reduces ops burden. |
| **Academix** | `xingyulu23/Academix` | Production | Community | stdio | INTEGRATE. Aggregates OpenAlex, DBLP, Semantic Scholar, arXiv, and CrossRef behind a single interface with smart ID resolution. This is exactly the multi-source academic aggregator Keystone needs, and it eliminates the need to integrate five separate servers. |
| **CrossRef** | `botanicastudios/crossref-mcp` (TypeScript) | Beta | Community | stdio | SKIP standalone. Academix covers CrossRef. If standalone CrossRef is needed for DOI verification specifically, use `tfscharff/doi-mcp` (verifies across 9 databases in parallel). |
| **Semantic Scholar** | `zongmin-yu/semantic-scholar-fastmcp-mcp-server` | Good | Community | stdio | SKIP standalone. Academix aggregates it. Integrate standalone only if Academix has gaps on Semantic Scholar-specific features. |
| **OpenAlex** | `oksure/openalex-research-mcp` | Good | Community | stdio | SKIP standalone. Academix aggregates it. |
| **Citation verification** | `tfscharff/doi-mcp` | Beta | Community | stdio | INVESTIGATE. Verifies citations across 9 databases in parallel. Directly addresses Layer 2 of the Evaluator stack (citation gate). May reduce or replace the CrossRef/Semantic Scholar API calls in `layer2_citation_gate.py`. |

### Build-vs-integrate decisions for Phase 1

All five Phase 1 targets have usable community or official servers. **Component #4 (MCP Gateway) scope is reduced:** you are not building MCP server integrations from scratch, you are building the gateway layer that wraps existing servers. The spec already says "build the gateway, not the servers," but the inventory above confirms this for all five targets.

**Implications for Component #4 scope:**
- Exa, Brave, EdgarTools: integrate hosted HTTP endpoints (no local process management needed)
- FRED: integrate stdio with Docker (one `docker run` command in startup)
- Academix: integrate stdio (requires local Python environment)
- Gateway needs to handle two transport types from day one: hosted HTTP (Exa, Brave, EdgarTools) and stdio (FRED, Academix)

**One finding changes the citation verification approach:** `doi-mcp` verifies across 9 databases in parallel, which is more comprehensive than calling CrossRef and Semantic Scholar separately. Include it in the MCP gateway as the citation verification backend for Layer 2 of the evaluator stack. This is additive, not a change to existing design.

**Contradiction between reports:** deep-research-06 lists `stefanoamorelli/sec-edgar-mcp` alongside `dgunning/edgartools`. Both exist. EdgarTools is substantially more mature (2.3M PyPI downloads, official MCP support, Claude Code skills). Use EdgarTools, not the community sec-edgar-mcp. This is a SKIP for sec-edgar-mcp.

---

## 4. Cost Model Refinement

### Prompt caching mechanics

**Two TTL tiers exist (Verified -- confirmed in source code `services/api/claude.ts`):**
- Default 5-minute ephemeral cache: write at 1.25x base input, read at 0.1x base input
- Extended 1-hour cache: write at 2x base input, same 0.1x read

**Minimum cacheable token lengths vary by model:**
- Sonnet 4.5/4 and Opus 4.1/4: 1,024 tokens minimum
- Sonnet 4.6 and Haiku 3.5: 2,048 tokens minimum
- Opus 4.6/4.5 and Haiku 4.5: 4,096 tokens minimum

**Maximum cache breakpoints:** 4 per request, with a 20-block lookback window per breakpoint.

**Fork-mode cache sharing mechanics (Verified):** The `buildForkedMessages()` function creates byte-identical API request prefixes by: (1) cloning parent's full assistant message including all `tool_use` blocks; (2) inserting placeholder `tool_result` blocks with identical text "Fork started -- processing in background" for each `tool_use`; (3) appending only the per-child directive as the differentiating element. The result: system prompt + tool definitions + conversation history = cache hits for all fork children. Cache entries become available only after the first response begins streaming. Implication: launch agent #1, wait for first token, then dispatch remaining agents in parallel.

**Cache architecture in practice:** The system tracks 14 cache-break vectors. The `SYSTEM_PROMPT_DYNAMIC_BOUNDARY` marker splits prompts into: (before boundary) tools, base instructions, security rules -- globally cacheable; (after boundary) CLAUDE.md content, git status, current date, MCP instructions -- per-session. CLAUDE.md content goes into `<system-reminder>` tags in messages, not the system prompt, to avoid breaking the globally shared cache.

### Model mixing economics

Current pricing (April 2026, Anthropic API):

| Model | Input | Cache Write (5min) | Cache Read | Output |
|-------|-------|-------------------|------------|--------|
| Opus 4.6 | $5/MTok | $6.25/MTok | $0.50/MTok | $25/MTok |
| Sonnet 4.6 | $3/MTok | $3.75/MTok | $0.30/MTok | $15/MTok |
| Haiku 4.5 | $1/MTok | $1.25/MTok | $0.10/MTok | $5/MTok |

**Token distribution in production (Verified -- from Kyle Redelinghuys 8-month dataset, ~10B tokens):** >90% cache reads, ~6% cache writes, <1% combined fresh input and output. Cache delivers ~90% savings on input costs.

**Model mixing cost reduction:** At 80% Sonnet / 15% Haiku / 5% Opus distribution, blended effective input cost drops ~40% versus all-Opus. Blended output cost drops ~35%. The existing Change 10 (model mixing: Opus for L0/L4, Sonnet for L1, Haiku for extraction) is correct and conservative -- the research confirms it. The leak adds that this isn't just a design choice; it's hardcoded in Claude Code (Explore agent runs on Haiku at 34M/week specifically for cost reasons).

**Extended thinking is the largest hidden cost driver (Verified):** Default thinking budget is 31,999 tokens per request, billed at output rates ($25/MTok for Opus). Setting `MAX_THINKING_TOKENS` to 10,000 yields ~70% reduction in thinking cost. Most research synthesis tasks do not need 32K tokens of reasoning. Set thinking budget explicitly.

### Compaction token savings

**MicroCompact (zero API cost):** Keeps 5 most recent tool results inline, replaces older results with `[Old tool result content cleared]`. Typical savings: 10-30K tokens per pass. Applied via `cache_edits` at the API transport layer -- does not invalidate the prompt cache. Eligible tools (COMPACTABLE_TOOLS): Read, Bash, Grep, Glob, WebSearch, WebFetch, Edit, Write. MCP tools are never microcompacted (deliberate choice, creates context poisoning risk).

**AutoCompact (LLM-powered, 5-strategy):** Triggers at `effectiveContextWindowSize - 13,000` tokens (~93.5% utilization on 200K model). Generates up to 20,000-token structured 9-section summary. Circuit breaker after 3 consecutive failures. Measured savings: 50-150K tokens freed, compressing 100K+ conversations to 3-5K summaries (95-97% reduction).

**Setting auto-compact threshold at 50% instead of default 83.5%:** Community recommendation for research pipelines. Research agents often front-load context (reading many documents early) and produce sparse output. Compacting at 50% preserves more working memory for the synthesis phase.

**Full Compact re-injects 5 most recently accessed files** (capped at 5,000 tokens each, 50,000 tokens total) plus active plans and skill schemas. Working budget resets to 50,000 tokens.

### Batch API (not used by Claude Code but relevant to Keystone)

**50% cost reduction across all models (Verified -- Anthropic published pricing).** Batch discounts stack with prompt caching: batch (50% off) + cache reads (90% off) = up to 95% savings on cached input tokens. At Opus 4.6 rates: $5/MTok base → $0.25/MTok effective for cached batch input. Maximum batch: 100,000 requests or 256 MB. Most complete in under 1 hour. Directly relevant for non-interactive background research tasks.

### Updated estimate for Keystone's $12-$100/engagement target

The existing Change 16 cost model ($7-$85/engagement) was based on 16 research reports. The leak adds three refinements:

1. **Fork-mode cache sharing for L1 fan-out reduces input costs by ~10x vs. naive parallelism.** For a 10-task engagement with 10 research agents sharing a 50K-token shared prefix at Sonnet 4.6 cache-read rates: 10 agents x 50K tokens x $0.30/MTok = $0.15 in shared-prefix input costs. Without cache sharing: 10 x 50K x $3/MTok = $1.50. The savings compound as parallelism increases.

2. **Cap thinking budgets at 10,000 tokens for L1 Sonnet agents** (not 31,999 default). This reduces thinking cost ~70% for the highest-volume pipeline stage.

3. **Use Batch API for non-interactive research tasks.** Background research queries, document indexing, and citation verification are all latency-tolerant. Routing them through the Batch API achieves 50% discount stacked with cache savings.

With these optimizations applied: a 10-task engagement with 10 parallel L1 agents (Sonnet), Opus for L0/L4, Haiku for extraction, fork-mode cache sharing, 10K thinking budget, and Batch API for background tasks should land in the $8-$45 range. The $12-$100 target holds. The lower end is now achievable for standard engagements without heroic optimization.

**Contradiction flagged:** deep-research-08 gives auto-compact threshold trigger as "167,000 tokens (83.5% utilization)" while deep-research-04 gives it as "93.5% utilization." These are different interpretations of the same formula: `effectiveContextWindowSize - 13,000`. For a 200K model: 187K/200K = 93.5%. For a 200K model with 8K reserved for output: (187K-13K)/200K = 87%. The discrepancy is the output reservation. Use `effectiveContextWindowSize - 13,000` as the formula; the exact percentage depends on model configuration.

---

## 5. New Patterns Not in Repo Analysis

The nano-claude-code Python reimplementation (11.8K lines, 56 files) was the basis for the 09-implementation-recommendations.md repo analysis. It captures the agent loop, tool dispatch, two-layer compaction, MCP client, and SubAgentManager patterns. It does not capture the following patterns from the full 512K-line leak:

### KAIROS daemon architecture

**Evidence quality: Confirmed in code (referenced 150+ times, specific file paths verified by multiple analysts).**

KAIROS converts Claude Code from request-response to persistent daemon. Core mechanism: when the message queue empties, instead of waiting for user input, the system injects a `<tick>` message containing the current timestamp. Located at `src/cli/print.ts:L1834-L1856`, implemented with `setTimeout(0)` to yield to the event loop.

Key behaviors:
- **15-second blocking budget** (`ASSISTANT_BLOCKING_BUDGET_MS = 15_000` at `src/tools/BashTool/BashTool.tsx:L57`): any action exceeding 15 seconds is auto-backgrounded
- **SleepTool**: model explicitly calls sleep when there is nothing useful to do; responding with a status message wastes an API call
- **Append-only daily logs** (KAIROS mode): `logs/YYYY/MM/YYYY-MM-DD.md` pattern, cannot be self-erased
- **Terminal-focus awareness**: when user is away, maximizes independent decision-making; when user is present, increases collaboration
- **Exclusive tools**: `SleepTool`, `SendUserFile`, `PushNotification`, `SubscribePR`
- Gated behind compile-time `feature('KAIROS')` and server-side `tengu_kairos` flag

**Keystone mapping:** KAIROS does not map directly (Keystone has no persistent daemon). The pattern that maps is the append-only log for the Observation Library: every observation should be written to an immutable date-stamped log file before being processed. This creates an audit trail and enables the autoDream consolidation pattern below.

The 15-second blocking budget maps to Temporal Activity timeouts: any activity exceeding its heartbeat timeout should be cancelled and retried, not left hanging.

### autoDream memory consolidation

**Evidence quality: Confirmed in code (source file available in public gist, full consolidation prompt reproduced by multiple independent analysts).**

autoDream runs as a forked subagent to prevent its maintenance operations from corrupting the main agent's reasoning. Located at `src/memdir/autoDream.ts` (KAIROS) and `src/services/autoDream/` (main).

**Triple gate activation (checked cheapest first):**
1. Time gate: >= 24 hours since last consolidation (`lastConsolidatedAt`)
2. Session gate: >= 5 sessions with modification time after last consolidation
3. Lock gate: exclusive PID file lock acquired; lock's mtime doubles as `lastConsolidatedAt`

Scan throttle of 10 minutes prevents repeated gate checks when time gate passes but session gate does not. On failure, lock rolls back so time gate passes again on next attempt.

**Four-phase consolidation:**
- Phase 1 (Orient): `ls` memory directory, read MEMORY.md index, skim existing topic files
- Phase 2 (Gather signal): search in priority order: daily logs > drifted memories > targeted transcript grep (`grep -rn "<narrow term>" <transcripts>/ --include="*.jsonl" | tail -50`). Explicit constraint: "Don't exhaustively read transcripts."
- Phase 3 (Consolidate): merge into existing files, convert relative dates to absolute, delete contradicted facts at source, merge overlapping entries
- Phase 4 (Prune and index): keep MEMORY.md under 200 lines / 25KB, remove stale pointers, resolve contradictions between files

The dream subagent has read-only bash only (ls, find, grep, cat, stat, wc, head, tail) and write access exclusively to memory files. Consolidating 913 sessions takes approximately 8-10 minutes.

**Keystone mapping -- ADOPT for META layer Observation Library:** The four-phase consolidation cycle (Orient, Gather, Consolidate, Prune) is the correct algorithm for the Observation Library's periodic consolidation. The triple-gate trigger (time + sessions + lock) is the correct scheduling primitive. Run consolidation as a scheduled Temporal workflow with a file-based advisory lock. The read-only sandbox constraint for the consolidation agent is directly applicable: Observation Library consolidation agents should read freely but write only to the observation files, never to the main research artifacts.

The "convert relative dates to absolute" principle is critical: every Observation Library entry should record absolute dates, not relative references that become ambiguous across sessions.

### 5-strategy compaction pipeline

**Evidence quality: Confirmed in code (query.ts lines 307-1,728 cited with specific stage descriptions).**

The nano-claude-code analysis documented a 2-layer compaction (Snip + Compact). The full leak reveals five strategies in a cascade:

| Strategy | Trigger | API cost | Notes |
|----------|---------|----------|-------|
| 1. Tool result budgeting | Before every API call | Zero | Per-message output caps, `seenIds` file tracking |
| 2. MicroCompact | Before every API call | Zero | `cache_edits` API transport layer edits; only COMPACTABLE_TOOLS eligible |
| 3. Session memory compact | AutoCompact trigger | Zero (uses cached session memory) | Rebuilds from session memory + recent messages; bypasses Full Compact if sufficient |
| 4. AutoCompact | ~93.5% context utilization | One summarization call | 9-section structured summary up to 20K tokens; circuit breaker after 3 failures |
| 5. Full Compact | `/compact` command or AutoCompact failure | One summarization call | Forked subagent; re-injects 5 most recent files; working budget resets to 50K |

**Key engineering detail:** MicroCompact applies edits via `cache_edits` at the API transport layer, not to the local message array. This preserves the warm prompt cache -- a cache miss would cost more than the context saved. The `seenIds` tracking mechanism makes re-injection after Full Compact deterministic (recency-based, not relevance-scored).

**Circuit breaker finding (Verified -- internal BigQuery data cited in source):** Before `MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES = 3` was added, 1,279 sessions had 50+ consecutive failures (one hit 3,272 retries) wasting ~250,000 API calls per day globally. Three lines of code eliminated this. The lesson: any retry logic in Keystone needs a circuit breaker.

**Keystone mapping:** The existing two-layer compaction plan (from nano-claude-code analysis) should be upgraded to the five-strategy cascade. The critical insight is MicroCompact at zero API cost: research agents reading many documents early in their session should have MicroCompact applied continuously, keeping only the 5 most recent tool outputs inline and persisting the rest to disk with references.

### Tool Search progressive loading

**Evidence quality: Confirmed in code (ENABLE_TOOL_SEARCH setting, before/after token measurements cited).**

When the total MCP tool description size would exceed ~10% of the context window, Claude Code switches to a two-phase loading approach: Phase 1 loads only tool names and one-line descriptions (~100 tokens per tool); Phase 2 fetches full JSON schemas on-demand when the agent determines it needs a specific tool.

**Measured impact:** Testing showed context consumption dropping from ~72,000 tokens to ~8,700 tokens for the same tool set -- an 87.9% reduction.

The `ToolSearchTool` itself is marked `alwaysLoad: true` (never deferred). Tools marked `alwaysLoad: true` (like `AgentTool`) are also never deferred. MCP tools are always deferred by default.

**Keystone mapping -- ADOPT for Component #4 (MCP Gateway):** Keystone's eventual target of 8+ MCP servers with multiple tools each could easily exceed 40 tools. At 100+ tokens per tool description, this approaches the threshold. Implement progressive loading: serve stub descriptions in `tools/list` responses and fetch full schemas via `ToolSearch` on demand. This is especially important for L1 research agents that use only 3-5 of the 8+ available servers per task.

### 26-event hooks system

**Evidence quality: Confirmed in code (full event list documented by multiple independent analysts with file paths).**

The hooks system exposes 26 distinct lifecycle events where external code can observe, modify, or block execution. Four handler types: command (shell script receiving JSON on stdin), HTTP (POST to URL), prompt (single-turn LLM evaluation), agent (spawned subagent with Read/Grep/Glob tools).

Full event taxonomy:
- Session: `SessionStart`, `SessionEnd`, `InstructionsLoaded`, `ConfigChange`
- User: `UserPromptSubmit`, `Notification`
- Tool execution: `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, `PermissionDenied`
- Agent orchestration: `SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `TeammateIdle`, `Stop`, `StopFailure`
- Infrastructure: `CwdChanged`, `FileChanged`, `WorktreeCreate`, `WorktreeRemove`, `PreCompact`, `PostCompact`
- MCP: `Elicitation`, `ElicitationResult`

**Exit code 2 is the universal binary gate:** any hook returning exit code 2 blocks the action, with stderr fed to Claude as an error message.

**The architectural insight:** hooks separate the "when to check" (structurally guaranteed invocation) from the "what to check" (externalized, configurable logic). `PreToolUse` fires before every tool execution -- that is structural. What the hook evaluates and whether it returns 0 or 2 -- that is configurable. This is the same principle Keystone's sprint contracts should use: structurally guaranteed evaluation invocation at every stage handoff, with pluggable quality gate logic.

**Keystone mapping:** The `TaskCompleted` and `Stop` hook patterns map directly to pipeline boundary gates in Keystone. Implement as Temporal Activity callbacks:
- `TaskCompleted` equivalent: Evaluator check before CitationProcessor consumes L1 outputs
- `Stop` equivalent: Sprint contract enforcement before L2 Content Structuring consumes Deliberation outputs
- `PreCompact` equivalent: Observation Library capture before any context compression

Hooks run in parallel when multiple match -- implement pipeline boundary checks as parallel Temporal Activities, not sequential.

### Fork-mode cache sharing for cheap parallelism

**Evidence quality: Confirmed in code (forkSubagent.ts, buildForkedMessages() function, specific fields documented).**

This pattern was mentioned in the existing repo analysis but not fully detailed. The complete mechanism:

1. Parent agent reaches a fan-out point (e.g., L0 dispatching L1 research agents)
2. `buildForkedMessages()` clones parent's last assistant message (all `tool_use` blocks, thinking, text)
3. For each `tool_use` block, a placeholder `tool_result` is inserted with identical text "Fork started -- processing in background" across ALL fork children
4. Each child gets one additional directive text block as the only differentiating element
5. Fork children use `useExactTools: true` to inherit exact tool array and definitions
6. Parent's rendered system prompt is passed as exact bytes, not re-rendered

Result: system prompt + tool definitions + conversation history = cache hits for all children. Each child pays full input price only for the small directive block.

**Critical implementation constraint:** Cache entries are available only after the first child's response starts streaming. Dispatch child #1, wait for first token confirmation, then dispatch remaining children in parallel. This stagger adds ~100-500ms before mass dispatch but is required for cache hits on siblings.

**A guard prevents recursive forking:** `toolUseContext.options.querySource === 'agent:builtin:fork'` check, with fallback scanning for a `<fork-boilerplate>` tag.

**Cost math for Keystone (Sonnet 4.6):**
- 10 agents sharing a 50K-token prefix: 10 x 50K x $0.30/MTok = $0.15 in shared-prefix costs
- Same 10 agents without cache sharing: 10 x 50K x $3/MTok = $1.50
- 10x reduction in input costs from caching alone
- For 50-agent parallelism with a 100K-token shared context: $1.50 cached vs. $15 uncached

**Keystone mapping -- ADOPT for Component #7 (Research Agent Pipeline):** Ensure the shared prefix across all L1 research agents is byte-identical: same system prompt, same tool definitions (frozen at spawn time, never modified per-agent), same RESEARCH.md context. Only the per-task directive should differ. Stagger launch: dispatch agent #1, confirm first token of streaming response, then fan out remaining agents in parallel.

---

## 6. Consolidated Pattern Catalog

All ADOPT/ADAPT/SKIP/INVESTIGATE verdicts from both the repo analysis (09-implementation-recommendations.md) and the 10 deep research reports, unified and deduplicated.

| Pattern | Source | Verdict | Keystone Component | Rationale |
|---------|--------|---------|-------------------|-----------|
| Generator-based agent loop | nano-claude-code `agent.py` | **ADOPT** | #5, #7, all stages | 175-line loop handles full agent lifecycle; yield typed events at every stage |
| AgentDefinition from markdown | nano-claude-code `multi_agent/subagent.py` | **ADOPT** | #7 | Specialized per-agent type definitions with tool lists and model overrides |
| ToolDef dataclass + central registry | nano-claude-code `tool_registry.py` | **ADOPT** | #4 | Per-agent tool subsetting via explicit allowlists |
| MCP client architecture (3 transports) | nano-claude-code `mcp/` | **ADOPT** | #4 | Complete working reference; add rate limiting and caching on top |
| Per-agent working directories + advisory locks | Claude Code `flock()` pattern | **ADOPT** | #7 | Proven at 34M Explore agent runs/week; structural isolation |
| Fork-mode byte-identical prefix caching | Claude Code `forkSubagent.ts` | **ADOPT** | #7 | 10x input cost reduction for parallel L1 agents; stagger launch by one response-start |
| System prompt boundary split (static/dynamic) | Claude Code `SYSTEM_PROMPT_DYNAMIC_BOUNDARY` | **ADOPT** | #4, #5, #7 | Cache the base instructions + tool schemas; regenerate only session-specific context |
| Tool filtering before model context | Claude Code `filterToolsByDenyRules()` | **ADOPT** | #4 | Model never sees unauthorized tools; prevents wasted reasoning and prompt injection |
| Per-call concurrency classification (`isConcurrencySafe(input)`) | Claude Code `toolOrchestration.ts` | **ADOPT** | #4, #7 | Read-only tool calls in parallel; writes serialized; evaluated per-call not per-tool-type |
| Exit code 2 binary gate convention | Claude Code hooks system | **ADOPT** | #6, #9 | Universal blocking mechanism for quality gates at pipeline boundaries |
| `TaskCompleted` hook as quality gate | Claude Code hooks, `coordinatorMode.ts` | **ADOPT** | #6, #9 | Maps to Temporal Activity callbacks before pipeline stage consumption |
| Fail-closed tool defaults | Claude Code `buildTool()` factory | **ADOPT** | #4 | `isConcurrencySafe` defaults false, `isReadOnly` defaults false; assume unsafe unless declared |
| Mandatory `Read` before `Edit`/`Write` | Claude Code structural gate | **ADOPT** | #7 | Code-level prevention of blind overwrites; implement as pre-condition check |
| MEMORY.md pointer architecture (3 tiers) | Claude Code memory system | **ADOPT** | META, CitationProcessor | Index (always loaded) + topic files (on-demand) + transcripts (grep-only); never bulk-load |
| autoDream four-phase consolidation (ADAPT) | Claude Code `autoDream.ts` | **ADOPT** | META, Observation Library | Orient-Gather-Consolidate-Prune cycle with triple-gate trigger; run as scheduled Temporal workflow |
| Append-only daily logs (KAIROS pattern) | Claude Code KAIROS system | **ADOPT** | META | Immutable date-stamped logs create audit trail; consolidation reads logs, not live memory |
| Five-strategy compaction cascade | Claude Code `query.ts` | **ADOPT** | #7 | Upgrade from 2-layer (nano) to 5-layer; zero-cost MicroCompact first, LLM summarization last |
| Circuit breaker on retry logic | Claude Code AutoCompact circuit breaker | **ADOPT** | #7, #6 | After 3 consecutive failures, stop retrying; prevents 250K wasted API calls/day at scale |
| FastMCP proxy + middleware pipeline | Community (FastMCP, IBM ContextForge) | **ADOPT** | #4 | Production gateway pattern for 8+ MCP servers; ErrorHandling → Auth → AgentToolFilter → RateLimit → CircuitBreaker → AuditLog |
| JWT scope-based tool filtering on `tools/list` | Community (CodiLime FastMCP pattern) | **ADOPT** | #4 | Agents never see unauthorized tools; prevents wasted reasoning and information leakage |
| CHUK Tool Processor for rate limiting | IBM `chuk-tool-processor` | **ADOPT** | #4 | Per-tool rate limits, bulkhead isolation, Redis-backed distributed state; `tool_rate_limits={"service": (n, window)}` |
| Tool Search progressive loading | Claude Code `ToolSearchTool` | **ADOPT** | #4 | 87.9% context reduction for tool-heavy sessions; stub descriptions in `tools/list`, full schemas on demand |
| `doi-mcp` for citation verification | Community `tfscharff/doi-mcp` | **ADOPT** | #8, #6 Layer 2 | Verifies across 9 databases in parallel; directly addresses Evaluator Layer 2 citation gate |
| Speculative tool execution (read-only during streaming) | Claude Code `StreamingToolExecutor` | **ADAPT** | #7 | Start read-only Temporal Activities as soon as tool_use blocks appear in stream; before full turn completes |
| Coordinator prompt as four-phase workflow | Claude Code `coordinatorMode.ts` | **ADAPT** | #5 | Research-Synthesis-Implementation-Verification adapted as Decompose-Research-Deliberate-Synthesize; prompts define strategy, Temporal enforces workflow |
| Delegate mode (coordination-only tools) | Claude Code coordinator | **ADAPT** | #5 | Implement via PydanticAI tool allow-lists per role; L0 orchestrator restricted to dispatch tools, not research tools |
| Message-level inter-agent sanitization | AgentLeak benchmark (C2 channel) | **ADAPT** | #8, #9 | Pass only structured claim-level representations between agents, not raw reasoning; directly addresses 68.8% C2 leakage |
| Plan approval request/response protocol | Claude Code mailbox system | **ADAPT** | #9, #6 | Map to Temporal Signal for L1.5 deliberation quality gates; agents submit to coordinator inbox, not each other |
| Two-layer retrieval (keyword filter + LLM ranker) | nano-claude-code `memory/context.py` | **ADAPT** | #3 | Replace LLM ranker with pgvector dense search; keep the cheap-filter-first pattern |
| SubAgentManager with depth limiting | nano-claude-code `multi_agent/subagent.py` | **ADAPT** | #7 | Replace ThreadPoolExecutor with Temporal child workflows; add process-level isolation via per-agent working directories |
| ECC instinct-to-skill pipeline | Community (ECC by Affaan Mustafa) | **ADAPT** | META | Not in Claude Code source; hook-based observation (100% reliability) + Haiku pattern detector + instinct confidence scoring; adapt for Observation Library's positive-pattern capture |
| ULTRAPLAN remote planning | Claude Code feature flag | **INVESTIGATE** | #5 | Offloads L0 spec generation to Opus in a cloud container for up to 30 minutes; directly maps to Keystone's complex spec generation; worth testing when Opus 4.6 is available |
| UDS_INBOX Unix Domain Socket messaging | Claude Code feature flag | **INVESTIGATE** | #4, #9 | Zero-network-overhead inter-session messaging; worth investigating as alternative to Redis pub/sub for local deployments |
| LODESTONE cross-session persistent memory | Claude Code feature flag (unreleased) | **INVESTIGATE** | META | If released, may inform Observation Library's cross-engagement knowledge transfer; monitor for release |
| Worktree mode per-agent git branches | Claude Code `EnterWorktreeTool` | **SKIP** | #7 | Solves code-editing conflicts, not research artifact conflicts; has known bug #33045; per-agent working directories achieve same isolation more reliably |
| Teammate mode (tmux process spawning) | Claude Code `spawnTeammate()` | **SKIP** | #7 | 20-30 second spawn latency; PydanticAI + Temporal child workflows achieve same isolation with better observability |
| Undercover mode | Claude Code `undercover.ts` | **SKIP** | -- | Anthropic-internal only; no applicability to Keystone |
| Anti-distillation fake tool injection | Claude Code `ANTI_DISTILLATION_CC` flag | **SKIP** | -- | Legal protection, not architectural; estimated to be bypassable in ~1 hour by any serious actor |
| React Ink terminal UI | Claude Code UI layer | **SKIP** | -- | Keystone does not need a terminal REPL interface; outputs are structured files and APIs |

---

## 7. Build-Order Implications

Does the deep research change the Phase 1 build order or approach for any of the 11 components?

**Short answer: No changes to build order. Five additive changes to component scope and approach.**

### #4: MCP Gateway -- scope reduced

All five Phase 1 targets (Exa, Brave, EdgarTools, FRED, Academix) have production-quality or official MCP servers with available endpoints. Component #4 scope is the gateway layer (rate limiting, circuit breaking, auth, audit), not MCP server construction.

**Change:** Remove "initial MCP server integrations" from the #4 build list. Replace with "configure integrations to existing servers." Add `doi-mcp` as a sixth integration for citation verification in Layer 2. The gateway now connects to six servers, not five.

**Additive to spec, not a change to existing decisions.**

### #4: MCP Gateway -- add Tool Search progressive loading

The current spec does not include deferred tool loading. For 8+ MCP servers with multiple tools each, this is needed to prevent context window bloat.

**Change:** Add `tool_loader.py` to `src/gateway/` implementing stub-first loading: `tools/list` returns name + one-line description; full schemas fetched on-demand. Threshold: trigger deferred loading when total MCP tool token count exceeds 10% of the model's context window.

**Additive to spec.**

### #6: Evaluator Stack -- Layer 2 citation gate uses doi-mcp

The current spec calls for CrossRef/Semantic Scholar existence checks. `doi-mcp` verifies across 9 databases in parallel and is an MCP server, not a direct API call.

**Change:** Layer 2's `layer2_citation_gate.py` should route citation verification through the MCP gateway to `doi-mcp` rather than calling CrossRef and Semantic Scholar APIs directly. This makes the citation gate consistent with the gateway architecture and gains parallel 9-database verification at no additional integration cost.

**Additive to spec.**

### #7: Research Agent Pipeline -- upgrade compaction from 2-layer to 5-strategy

The existing spec references "two-layer compaction" from the nano-claude-code analysis. The full leak reveals a five-strategy cascade that is significantly more efficient.

**Change:** In `src/agents/`, replace the planned two-layer compaction with the five-strategy cascade: (1) tool result budgeting (per-output caps); (2) MicroCompact (cache_edits, zero API cost, keep 5 most recent); (3) session memory compact (rebuild from cached session memory if available); (4) AutoCompact (circuit-broken, 3-failure limit, structured summary); (5) Full Compact (forked agent, re-injects 5 most recent files). Set auto-compact threshold at 50% rather than the default ~83.5% for research agents that front-load document reading.

**This is a change to existing design, not additive.** The scope of `compaction.py` expands from 2 strategies to 5.

### #7: Research Agent Pipeline -- implement fork-mode cache sharing

The current spec does not specify how to share context across parallel L1 agents. Fork-mode cache sharing is the mechanism.

**Change:** Add `fork_manager.py` to `src/agents/`. Responsibilities: (1) build the shared byte-identical prefix (base system prompt + tool definitions frozen at spawn time + RESEARCH.md context); (2) dispatch agent #1 and confirm first streaming token before dispatching remaining agents in parallel; (3) append per-task directive as the only differentiating element; (4) enforce recursive fork guard (L1 agents cannot spawn sub-agents that fork).

**Additive to spec.**

### META layer -- autoDream consolidation informs Observation Library design

The current spec defers Observation Library design to Phase 2. The autoDream pattern is specific enough to inform the data structures now.

**Change (design-level, not build-order):** Add to the Observation Library design notes: (1) observations stored as append-only date-stamped log files (`YYYY-MM-DD.md`); (2) consolidation runs as scheduled Temporal workflow with triple-gate trigger (time + sessions + lock); (3) consolidation agent has read-only access to all research artifacts, write access only to observation files; (4) consolidation phases: Orient-Gather-Consolidate-Prune; (5) MEMORY.md equivalent (index) kept under 200 lines / 25KB.

**Design-only change; does not affect Phase 1 build order.**

### What does NOT change

- Build order (#1-#11 sequence) is unchanged
- PydanticAI + Temporal + MCP stack decision is unchanged and further validated
- Per-agent tool specialization (3-5 tools) is unchanged
- Agent isolation via filesystem/working directories is unchanged
- Five-layer evaluator stack is unchanged
- Claim-level intermediate representations are unchanged
- Model mixing strategy is unchanged
- $12-$100/engagement cost target is unchanged and achievable

---

## Implementation Spec Impact

The following items in PHASE-1-IMPLEMENTATION-SPEC.md should be updated when the spec is next revised:

### #4 (MCP Gateway) -- file list change

**Current:** "Initial MCP server integrations: Exa, Brave Search, EdgarTools, FRED, Academix"

**Revised:** "Configure integrations to existing MCP servers: Exa (exa-labs/exa-mcp-server, hosted HTTP), Brave (brave/brave-search-mcp-server, hosted HTTP), EdgarTools (dgunning/edgartools built-in MCP, stdio+HTTP), FRED (stefanoamorelli/fred-mcp-server, stdio+Docker), Academix (xingyulu23/Academix, stdio), doi-mcp (tfscharff/doi-mcp, stdio -- for Layer 2 citation verification). Add `tool_loader.py` implementing progressive Tool Search loading (stub descriptions first, full schemas on demand, threshold at 10% of context window)."

**Acceptance criteria addition:** "Tool Search: with 8+ MCP servers connected, tool descriptions total under 10,000 tokens in context at session start."

### #4 (MCP Gateway) -- transport note

The gateway must handle two transport types from day one: hosted HTTP (Exa, Brave, EdgarTools) and stdio with subprocess management (FRED, Academix, doi-mcp). The spec mentions "at least 3 MCP servers (Exa, Brave, EdgarTools) operational" but does not specify transport diversity. Update acceptance criteria to include: "At least one hosted HTTP server and one stdio server operational."

### #6 (Evaluator Stack Layer 2) -- citation gate routing

**Current:** `layer2_citation_gate.py` -- "CrossRef/Semantic Scholar existence checks"

**Revised:** Route citation verification through MCP gateway to `doi-mcp` (9-database parallel verification). Direct CrossRef and Semantic Scholar API calls are no longer needed in this component. The MCP gateway integration covers both.

### #7 (Research Agent Pipeline) -- compaction upgrade

**Current:** Two-layer compaction (Snip + Compact), with reference to nano-claude-code `compaction.py`

**Revised:** Five-strategy cascade. Add to `src/agents/`: `micro_compact.py` (zero-API cache_edits implementation), `session_memory_compact.py` (session memory rebuild), `auto_compact.py` (circuit-broken LLM summarization with 3-failure limit), and `full_compact.py` (forked agent, re-inject 5 most recent files). Set auto-compact threshold at 50% via configuration. Add `fork_manager.py` for byte-identical prefix construction and launch staggering.

**Scope change:** Component #7 expands from L to XL. Recommend splitting into two parallel sub-tracks: (a) agent definition + isolation + finding writer (L scope, can build first); (b) compaction pipeline + fork manager (M scope, can build in parallel). Both sub-tracks feed #8.

### Priority additions (not in current spec, no build-order change needed)

1. **Circuit breakers on ALL retry logic:** Whenever the spec says "retry," add a maximum retry count. The AutoCompact bug (250K wasted API calls/day) was caused by uncircuit-broken retries. Add to acceptance criteria for #4, #6, #7: "All retry loops have a maximum attempt count and dead-letter path."

2. **Observation Library log format (design now, build Phase 2):** Add `schemas/observation_entry.schema.json` to the #1 parallel track. Design the autoDream-informed structure now (append-only log + index pointer + topic files) so Phase 2 can implement without redesign.

3. **Thinking budget cap:** Add to the agent configuration for #5 and #7: `MAX_THINKING_TOKENS = 10000` for Sonnet agents, `MAX_THINKING_TOKENS = 15000` for Opus agents (L0/L4). Default of 31,999 will inflate costs ~3x unnecessarily.
