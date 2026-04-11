# Claude Code's cost architecture: what the leaked source reveals for multi-agent builders

**Claude Code's March 2026 source leak exposed a system where prompt caching is the single most important cost lever — over 90% of tokens in heavy sessions are cache reads at 1/10th normal price, and fork-mode subagent spawning exploits byte-identical prefixes so that running five parallel agents costs barely more than one.** For a system spawning 15–50 parallel research agents, this means the difference between a $50 session and a $500 session hinges entirely on cache architecture. The leak (512,000 lines of TypeScript from v2.1.88) revealed that Anthropic treats cache hit rates as SEV-level metrics — when they drop, engineers get paged. The implications for the Keystone Intelligence Engine are concrete: adopt fork-mode's prefix-sharing pattern, use tiered compaction aggressively, and route 80%+ of agent work to Sonnet or Haiku.

## The leak: 512K lines of agentic infrastructure exposed

On March 31, 2026, security researcher Chaofan Shou discovered that Claude Code v2.1.88's npm package contained a **59.8 MB source map file** referencing a publicly accessible Cloudflare R2 bucket with the full source archive. Two stacked configuration failures — a missing `.npmignore` rule for `*.map` files and an unauthenticated R2 bucket — exposed **1,906 TypeScript files**, 44 feature flags, internal model codenames (Capybara = Claude 4.6, Fennec = Opus 4.6), and the complete agentic harness architecture. The leak did not include model weights, training data, or credentials. Within hours, the original tweet hit 16 million views and GitHub mirrors accumulated 41,500+ forks. Anthropic pulled the package and called it "a release packaging issue caused by human error."

Community analysts rapidly extracted the cost-critical systems: the three-tier compaction pipeline, the fork-mode cache-sharing mechanism, the `AgentTool` schema with per-child model selection, the segmented prompt caching architecture in `services/api/claude.ts` (3,419 lines), and telemetry data showing **250K wasted API calls per day** from autocompact failures before a 3-line fix. The `utils/modelCost.ts` file matched Anthropic's public pricing exactly — no hidden internal rates.

## Prompt caching mechanics and the fork-mode cost breakthrough

Prompt caching is the architectural foundation of Claude Code's economics. The system uses Anthropic's prefix-matching cache with **two TTL tiers**: a default 5-minute ephemeral cache (1.25× base input write cost, **0.1× base input read cost**) and an optional 1-hour extended cache (2× write cost, same 0.1× read cost). Each request supports up to **4 cache breakpoints**, with a 20-block lookback window per breakpoint. Minimum cacheable prompt length varies by model: **1,024 tokens** for Sonnet 4.5/4 and Opus 4.1/4, **2,048 tokens** for Sonnet 4.6 and Haiku 3.5, and **4,096 tokens** for Opus 4.6/4.5 and Haiku 4.5.

**Concrete pricing per million tokens (Opus 4.6):** base input $5, cache write $6.25 (5-min) or $10 (1-hour), cache read **$0.50**, output $25. For Sonnet 4.6: base input $3, cache read **$0.30**, output $15. For Haiku 4.5: base input $1, cache read **$0.10**, output $5.

Claude Code's internal caching architecture uses a segmented design in `services/api/claude.ts`. A static section (model identity, security rules, tool guidelines) is globally cacheable across all users. A `SYSTEM_PROMPT_DYNAMIC_BOUNDARY` marker separates this from a dynamic segment (CWD, git status, MCP instructions) that changes per session. Cache prefixes are created in strict order: `tools` → `system` → `messages`. Dynamic information like dates and file contents goes into `<system-reminder>` tags in user messages, never in the system prompt, specifically to avoid cache invalidation. **Tool lists are locked at startup** — adding or removing tools mid-session would invalidate the entire conversation cache.

### Fork mode: the key to cheap parallel agents

The fork-mode mechanism (feature-gated as `FORK_SUBAGENT`) is the most relevant pattern for Keystone. Defined in `forkSubagent.ts`, it exploits prompt cache sharing between parent and child agents through byte-identical API request prefixes.

The `buildForkedMessages()` function works as follows: for N parallel fork children to share a cached prefix, every child receives an identical request up to the per-child directive. It clones the parent's full assistant message (all `tool_use` blocks, thinking, text), builds `tool_result` blocks for every `tool_use` with the **identical placeholder text** `"Fork started — processing in background"`, then appends one per-child directive text block — the only part that differs. The fork child uses `useExactTools: true` to inherit the parent's exact tool array (same definitions, same order) and receives the parent's rendered system prompt as exact bytes, not re-rendered.

The result: the parent's entire context (system prompt + tools + conversation history) is a cache hit for each fork child. Each child only pays full input price for the small directive text that differs. **A critical concurrency constraint**: cache entries only become available after the first response begins. Anthropic's documentation explicitly states: "wait for the first response before sending subsequent requests" for cache hits on parallel requests. This means the first fork child must begin streaming before siblings are dispatched.

Fork children cannot recursively fork — a guard checks `toolUseContext.options.querySource === 'agent:builtin:fork'` and falls back to scanning for a `<fork-boilerplate>` tag. Children keep the Agent tool in their pool (for cache-identical tool definitions) but cannot invoke it.

**Cost implication for Keystone**: with a 100K-token parent context, spawning 15 fork children costs approximately 100K × $0.50/MTok × 15 (cache reads) + 15 × ~500 tokens × $5/MTok (fresh directives) + 15 × output tokens × $25/MTok for Opus. Compare this to 15 independent sessions at 100K × $5/MTok × 15 = $7.50 vs $0.75 — a **10× reduction in input costs** from caching alone.

## Model mixing: the parent agent picks, not a router

Claude Code does **not** have automatic AI-driven model routing. The parent LLM agent makes explicit model tier choices when spawning children through the `AgentTool` schema:

```typescript
model: z.enum(['sonnet', 'opus', 'haiku']).optional()
```

The heuristic is embedded in the agent's behavior: search gets Haiku, complex reasoning gets Opus, everything else gets Sonnet. Built-in subagents have hardcoded defaults: **Explore agent → Haiku** (at 34 million runs per week, this saves enormous costs), **Plan agent → inherits session model**, **statusline-setup → Sonnet**, **Claude Code Guide → Haiku**. The `CLAUDE_CODE_SUBAGENT_MODEL` environment variable overrides the default subagent model.

The primary built-in model mixing strategy is the **`opusplan` alias**: Opus 4.6 activates during `/plan` mode for deep reasoning, then automatically switches to Sonnet 4.6 for execution. Provider-specific model mappings are controlled via `ANTHROPIC_DEFAULT_OPUS_MODEL`, `ANTHROPIC_DEFAULT_SONNET_MODEL`, and `ANTHROPIC_DEFAULT_HAIKU_MODEL` environment variables, with `modelOverrides` settings for Bedrock ARNs and Vertex version names.

Third-party routing fills the gap. **Claude Code Router** (26.4K GitHub stars) intercepts requests and routes to different models based on task type, token count, or custom logic across categories: `default`, `background`, `reasoning`, `long-context`. The **claude-router plugin** claims **50–70% cost savings** by routing "What is JSON?" → Haiku (~$0.01), "Run all tests" → Sonnet (~$0.03), "Design architecture" → Opus (~$0.06). **Morph Router** classifies prompts in ~430ms at $0.001/request, claiming 40–60% savings versus all-Sonnet.

**For Keystone**: implement a lightweight complexity classifier at the orchestrator level. Route research synthesis and complex reasoning to Sonnet 4.6 ($3/$15 per MTok), simple web fetches and data extraction to Haiku 4.5 ($1/$5 per MTok), and reserve Opus 4.6 ($5/$25 per MTok) for final cross-agent synthesis only.

## Three-tier compaction pipeline and measured token savings

Claude Code's compaction system operates as a four-stage cascade before each API call: tool result budgeting → MicroCompact → context collapse → AutoCompact.

**MicroCompact** runs before every API request with **zero API calls**. It keeps only the 5 most recent tool results inline; older results are saved to disk and replaced with references. Eligible tools are defined in `COMPACTABLE_TOOLS`: Read, Bash, Grep, Glob, WebSearch, WebFetch, Edit, Write. MCP tool results are never microcompacted. Typical savings: **10–30K tokens per pass**. When the prompt cache is warm, MicroCompact queues `cache_edits` blocks alongside the API request — telling the server to delete specific tool result blocks by `tool_use_id` without touching the cached prefix. The cache stays intact.

**Session Memory Compact** fires when auto-compact triggers, attempting to rebuild context from the session memory file plus recent messages with **no model call needed**. If it succeeds, it bypasses Full Compact entirely.

**Full Compact** invokes a forked agent that receives the entire message history and produces a structured summary with 7 mandatory sections (Primary Request, Key Technical Concepts, Files and Code Sections, Errors and Fixes, Current State, Outstanding Questions, Working Hypotheses). The summary is capped at **20,000 tokens**. A circuit breaker stops retrying after **3 consecutive failures**. Measured savings: **50–150K tokens freed**, compressing 100K+ conversations into 3–5K summaries — a **95–97% reduction**. The Anthropic cookbook example showed 12,847 → 1,526 tokens (**88% reduction** in one event).

The auto-compact threshold formula is `effectiveContextWindowSize - 13,000 tokens`. For a 200K window, this triggers at approximately **167,000 tokens** (83.5% utilization). The `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` environment variable (values 1–100) controls the percentage threshold, though community analysis recommends setting it to **50** rather than the default — at 95% you've already filled 190K of 200K window, wasting tokens on bloated context for many turns before compaction fires.

Full Compact's summarization call **reuses the exact same system prompt, tools, model, and message prefix** as the main conversation. Testing an alternative approach produced a **98% cache miss rate**. This is a critical design lesson: compaction must preserve cache prefixes.

## Real-world costs and the 90% cache-read reality

Anthropic's official data reports an average cost of **$6 per developer per day**, with 90% of users below $12/day and monthly averages of **$100–200 with Sonnet 4.6**. The most detailed public dataset comes from Kyle Redelinghuys, who tracked 8 months of daily use totaling approximately **10 billion tokens**. His July 2025 peak: 2.4 billion tokens across 201 sessions and 45+ projects, an API equivalent of $5,623 — paid as ~$100 on the Max plan. His single busiest day (January 22, 2026): 8,930 messages, 9 sessions, 2,169 tool calls.

The token distribution is striking: **over 90% of all tokens are cache reads**, approximately 6% are cache writes, and **less than 1% combined are actual input and output tokens**. At Opus rates, his 4.5 billion cache reads would have cost $67,500 at fresh input prices versus $6,750 at cache-read rates — prompt caching delivered roughly **90% savings** on input costs.

Extended thinking is the **largest hidden cost driver**. The default thinking budget is **31,999 tokens per request**, billed as output tokens. Setting `MAX_THINKING_TOKENS` to 10,000 yields approximately **70% reduction** in thinking cost per request, and most coding tasks don't require 32K of reasoning.

### Multi-agent overhead: the numbers that matter for Keystone

- **Subagents (Task tool)**: near-neutral (~1×) overhead versus single sessions, because they use fork-mode cache sharing
- **3-agent team**: 3–4× tokens of a single session (coordination messages add overhead beyond raw 3× multiplier)
- **5-agent team**: 5–7× tokens
- **Agent teams in plan mode**: approximately **7× more tokens** than standard sessions (each maintains own context window)
- **Agent teams at scale (experimental)**: one analysis measured **~15× standard usage**

Each subagent starts with approximately **20,000 tokens of context overhead** before actual work begins (system prompt, tool definitions, CLAUDE.md). Anthropic's flagship C compiler demo used **16 Opus agents across 2,000 sessions over two weeks** at a total cost of **$20,000**, building ~100,000 lines of Rust. The hard maximum for agent teams is 16 teammates, with a practical sweet spot of **3–5 teammates** — beyond 5, coordination overhead erodes speed gains.

For 15–50 parallel agents, no direct public data exists at that scale. Extrapolating from fork-mode economics: with a shared 100K-token context prefix and Sonnet 4.6 pricing, 50 fork children would cost approximately 50 × 100K × $0.30/MTok (cache reads) = **$1.50 in input costs** for the shared prefix, plus 50 × directive + output token costs. Without cache sharing, the same 50 agents would cost 50 × 100K × $3/MTok = **$15 in input costs** — a 10× difference. Output tokens (where most cost accumulates for reasoning-heavy tasks) are unaffected by caching.

## Batch API: 50% savings exist but Claude Code doesn't use them

Claude Code uses the **streaming Messages API** for all operations — the Batch API's asynchronous nature (up to 24-hour processing) is incompatible with interactive agent loops. The `/batch` slash command is a parallel multi-agent orchestrator using Git worktrees, not the Batch API.

The Batch API offers **50% cost reduction** across all models: Opus 4.6 drops to $2.50/$12.50 per MTok, Sonnet 4.6 to $1.50/$7.50, Haiku 4.5 to $0.50/$2.50. Maximum batch size is **100,000 requests or 256 MB**. Most batches complete in under 1 hour. Critically, **batch discounts stack with prompt caching**: batch (50% off) + cache reads (90% off) = up to **95% savings** on cached input tokens.

For Keystone, the Batch API is highly relevant for non-latency-sensitive research tasks. A 50-agent research batch with shared prompt prefixes using 1-hour cache TTL could achieve: $2.50/MTok × 0.1 (cache read) = **$0.25/MTok effective input cost** for Opus 4.6, versus $5/MTok standard — a 20× reduction. The community `claude-batch-toolkit` MCP server demonstrates this pattern, routing non-urgent work (code reviews, architecture analysis) to the Batch API.

## Architecture recommendations for Keystone's 15–50 agent system

Based on the leaked source analysis, the optimal cost architecture for a multi-agent research system combines five patterns from Claude Code:

**First, adopt fork-mode's prefix-sharing pattern.** Construct a byte-identical prompt prefix across all agents: static system prompt → tool definitions (frozen at spawn time) → shared research context. Only the per-agent directive should differ. This converts the bulk of input tokens to cache reads at 0.1× cost. Stagger agent launches: dispatch agent #1, wait for its first streaming token (confirming cache write), then dispatch remaining agents in parallel.

**Second, implement tiered model routing.** Use Haiku 4.5 for web fetching, data extraction, and simple summarization ($1/$5 per MTok). Use Sonnet 4.6 for research synthesis, analysis, and most agent work ($3/$15 per MTok). Reserve Opus 4.6 for final cross-agent synthesis and complex reasoning ($5/$25 per MTok). At 80% Sonnet / 15% Haiku / 5% Opus distribution, effective blended cost drops roughly 40% versus all-Opus.

**Third, use the Batch API for background research.** Route non-latency-sensitive research queries through the Batch API for 50% savings. Stack with prompt caching and 1-hour TTL for maximum discount. Reserve streaming API only for interactive or time-critical agent coordination.

**Fourth, implement aggressive compaction.** Set auto-compact thresholds at 50% rather than the default ~83%. Use MicroCompact's pattern of keeping only 5 recent tool results inline. For research agents with heavy web fetch outputs, this alone can free 30–50K tokens per compaction cycle at zero API cost.

**Fifth, cap extended thinking budgets.** Set `MAX_THINKING_TOKENS` to 10,000 for research agents (versus 31,999 default). Most research synthesis tasks don't require 32K tokens of reasoning, and thinking tokens are billed at output rates ($15–25/MTok depending on model).

## Conclusion

The Claude Code leak revealed a system engineered around a single insight: **prompt caching transforms multi-agent economics from multiplicative to near-additive cost scaling**. The fork-mode pattern — byte-identical prefixes, placeholder tool results, exact tool inheritance — enables N parallel agents to share a single cached context at 0.1× input price per agent. For Keystone's 15–50 agent architecture, this means input costs scale at roughly **$0.03–0.15 per agent per 100K shared context** (Sonnet cache reads) rather than $0.30 per agent without caching. Combined with model tiering (80% Sonnet, 15% Haiku, 5% Opus), Batch API routing for non-interactive work (additional 50% off), and aggressive compaction (95% context reduction when needed), a 50-agent research session's input costs can be held to roughly **$2–5** rather than the $50–75 that naive parallel spawning would incur. The critical implementation constraint: cache entries become available only after the first response begins streaming, so agent launches must be staggered by one response-start latency (~100–500ms) to guarantee cache hits across the fleet.