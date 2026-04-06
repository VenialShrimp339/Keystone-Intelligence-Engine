# Claude Code's harness architecture, fully exposed

**The March 31, 2026 leak of 512,000 lines of TypeScript reveals that Claude Code's power comes not from the model but from the harness** — a sophisticated orchestration shell built on React/Ink, Bun, and Zod v4 that manages prompt construction, multi-agent coordination, context compression, and tool dispatch through patterns directly applicable to the Keystone Intelligence Engine. The entire agentic loop is an AsyncGenerator yielding typed Messages, the "orchestration algorithm is a prompt, not code," and parallelism across forked subagents is essentially free via KV cache sharing. Below is every implementation pattern that matters for PydanticAI + Temporal + MCP gateway design.

---

## How the system prompt gets assembled

The system prompt is not a single string — it's a modular, cache-aware composite built from `src/constants/prompts.ts` and `src/context.ts`. A marker called `SYSTEM_PROMPT_DYNAMIC_BOUNDARY` splits the prompt into two halves:

**Before the boundary (static, cached globally across ALL organizations):** base behavioral instructions, tool JSON schemas, safety constraints (`CYBER_RISK_INSTRUCTION` owned by the Safeguards team), and anti-distillation decoy tool definitions. This portion is identical for every user and benefits from aggressive prompt caching.

**After the boundary (dynamic, session-specific):** CLAUDE.md file contents, git status/branch, current date, environment info (OS, shell), loaded skill summaries, and project context. Only this portion busts cache per-session.

The assembly pipeline calls `fetchSystemPromptParts()` which collects: environment context from `getSystemContext()` (memoized per session), user context from `getUserContext()` (CLAUDE.md hierarchy, permissions), tool definitions from `assembleToolPool()`, and skill frontmatter (short summaries only — full skill content loads on invocation). A function explicitly named `DANGEROUS_uncachedSystemPromptSection()` handles volatile sections that must never be cached. The system tracks **14 cache-break vectors** with "sticky latches" that prevent UI toggles from invalidating the 70K+ token prompt prefix.

**CLAUDE.md layering** follows a hierarchical discovery pattern: files from the working directory and parent directories load at launch; files in subdirectories load as the agent works in them. The first **200 lines or 25KB** of MEMORY.md load at session start. When instructions conflict across levels, more specific instructions take precedence. CLAUDE.md content survives compaction because it's re-injected on every API request as part of the system prompt, not the conversation history.

**Settings cascade** (highest to lowest priority for most settings):
1. **Enterprise managed settings** — `/Library/Application Support/ClaudeCode/managed-settings.json` (macOS) or `/etc/claude-code/managed-settings.json` (Linux)
2. **Local project settings** — `.claude/settings.local.json` (git-ignored, always wins locally)
3. **Project settings** — `.claude/settings.json` (committed to source control)
4. **User settings** — `~/.claude/settings.json`

However, overrides vary by subsystem: skills resolve as managed > user > project; subagents as managed > CLI flag > project > user > plugin; MCP servers as local > project > user; and hooks **merge** — all registered hooks fire regardless of source.

Internal A/B testing at `prompts.ts:527` found that explicit word counts ("keep text between tool calls to ≤25 words, keep final responses to ≤100 words") produced a **~1.2% output token reduction** versus qualitative "be concise" instructions.

---

## The two-layer QueryEngine that drives everything

The agentic brain spans two files totaling ~115KB: `QueryEngine.ts` (the outer session manager, **~46KB**) and `query.ts` (the inner turn loop, **~69KB**). Together they handle all LLM API calls, streaming, token accounting, context compression, retry logic, and multi-agent orchestration.

### Outer layer: QueryEngine class

`QueryEngine` is the stateful, multi-turn session object. Its constructor takes a `QueryEngineConfig` including: `tools`, `commands`, `mcpClients`, `agents`, a `canUseTool` permission function, app state getter/setter, `thinkingConfig`, `maxTurns`, `maxBudgetUsd`, `taskBudget`, and optional `jsonSchema` for structured output. The primary method is `submitMessage()`, implemented as an **AsyncGenerator** — it yields `SDKMessage` objects, supports backpressure and cancellation via `AbortController`, and returns void on completion.

```typescript
class QueryEngine {
  async *submitMessage(
    prompt: string | ContentBlockParam[],
    options?: { uuid?: string; isMeta?: boolean }
  ): AsyncGenerator<SDKMessage, void, unknown> { ... }
}
```

`submitMessage()` first creates a `ProcessUserInputContext`, checks if the input is a local-only slash command (yielding output directly without LLM), then enters the inner loop via `queryLoop()`.

### Inner layer: queryLoop()

`queryLoop()` is a `while(true)` loop driving multi-turn behavior. Each iteration follows: **context preparation → model call → tool execution → continuation decision**. All mutable state is consolidated into a single `State` object (query.ts lines 204-217).

**The complete flow from user query to response:**
1. User input → `normalizeMessagesForAPI()`
2. System prompt assembly via `fetchSystemPromptParts()`
3. Streaming API call via `deps.callModel()` (injected through `QueryDeps` for testability)
4. Parse streaming response for `tool_use` content blocks
5. Permission check per tool + file overlay snapshot
6. Execute tools (parallel reads, serial writes via `StreamingToolExecutor`)
7. Append `tool_result` to messages → loop until quiet

**Stop conditions** — the loop terminates when:
- Model returns text-only response (no `tool_use` blocks) → `success`
- Hit `maxTurns` limit → `error_max_turns`
- Hit `maxBudgetUsd` → `error_max_budget_usd`
- API failure or cancelled request → `error_during_execution`
- **Diminishing returns detection**: `DIMINISHING_THRESHOLD = 500` tokens, `COMPLETION_THRESHOLD = 0.9`. If **3+ consecutive continuations** each produce <500 additional tokens, the engine infers the model is stuck and stops
- In auto mode: **3 consecutive denials** or **20 total denials** from the safety classifier triggers escalation to the human
- Structured output validation exhausts retry limit → `error_max_structured_output_retries`

**Speculative execution** is a key performance pattern: read-only tools start executing during model streaming, before the response completes. The `StreamingToolExecutor` partitions tools by safety — reads run concurrently, writes serialize. This makes the agent feel significantly faster.

**Output slot reservation**: default **8K output cap**, automatically escalating to **64K on hit** — this saves context in 99% of requests while allowing long-form output when needed.

---

## The 4-stage context compression pipeline

Context management is where Claude Code's engineering shines. Four compression stages fire in sequence (query.ts lines 307-1728), each progressively more expensive:

**Stage 1 — Tool result budgeting** (query.ts:379): Caps individual tool output size via `maxResultSizeChars`. Large results get saved to temp files with a reference. This is the cheapest gate.

**Stage 2 — MicroCompact** (query.ts:413): Edits cached content locally with **zero API calls**. Old tool outputs from `COMPACTABLE_TOOLS` get trimmed directly; MCP tools, Agent tools, and custom tools are exempt. Uses the `cache_edits` API to remove messages without invalidating prompt cache. Returns a 30-word `FILE_UNCHANGED_STUB` for re-read files.

**Stage 3 — Context Collapse** (query.ts:440): Projects a collapsed view over a "commit log" of conversation segments. Fires at 90% capacity; spawns block at 95%.

**Stage 4 — AutoCompact** (query.ts:453): Full LLM-powered conversation compression. Triggers at `effectiveContextWindowSize - 13,000` tokens (~93.5% utilization on a 200K model). Generates up to a **20,000-token structured summary**. Has a **circuit breaker**: `MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES = 3`. A BigQuery analysis from March 10, 2026 found 1,279 sessions with 50+ consecutive compaction failures (up to 3,272 per session), wasting ~250K API calls/day globally before this limit was added.

**Full Compact** (triggered by `/compact` command) compresses the entire conversation via a forked sub-agent that uses chain-of-thought reasoning inside `<analysis>` tags, then `formatCompactSummary()` strips the reasoning before re-injection. Post-compaction, the system re-injects: recently accessed files (capped at **5,000 tokens/file**), active plans, and relevant skill schemas. Working budget resets to **50,000 tokens**.

Messages use JSONL with filtering flags: `isCompactSummary: true` marks AI-generated summaries, `isVisibleInTranscriptOnly: true` prevents messages from being sent to the API, and `getMessagesAfterCompactBoundary()` returns only post-compaction messages for API calls.

---

## Bootstrap sequence and layered architecture

The entry point is `src/entrypoints/cli.tsx`, not `main.tsx`. The full boot path:

```
cli.tsx (fast paths: --version, daemon, ps, logs)
  → seedEarlyInput()           // Buffer keystrokes until Ink mounts
  → Dynamic import → main.tsx  // 4,683 lines
       → startMdmRawRead()     // MDM policy prefetch
       → macOS keychain warm-up (parallel)
       → Bun DCE feature() evaluation
       → Commander.js CLI argument parsing
       → Authentication (API key, OAuth, Bedrock, Vertex, Azure)
       → GrowthBook init (A/B testing, feature flags)
       → Policy limits + remote managed settings
       → Tool, command, skill, MCP server registration
       → stopCapturingEarlyInput()
       → Ink root render → REPL.tsx → PromptInput → MessageList
```

The architecture stacks six layers:

| Layer | Key Files | Responsibility |
|-------|-----------|---------------|
| **Entry points** | `cli.tsx`, `sdk/` | Fast paths, early input capture, dynamic import |
| **Bootstrap** | `main.tsx`, `bootstrap/state.ts` (1,758 lines) | Auth, flags, settings, tool assembly — singleton state |
| **Setup** | `setup.ts` (21KB) | Node validation, git root detection, UDS server, hooks snapshot |
| **UI** | React + custom Ink fork (389 files, 32 subdirs) | Terminal rendering with Yoga flexbox, `Int32Array` ASCII pool, bitmask styles |
| **QueryEngine** | `QueryEngine.ts` + `query.ts` | Session management, agentic loop, compression, streaming |
| **Tools + Services** | `tools/` (184 files), `services/` (130 files) | Tool execution, API client, MCP, analytics, compaction, autoDream |

**Dependency injection** is handled through three mechanisms: Bun's compile-time `feature()` intrinsic for dead-code elimination (108 feature-gated modules stripped from external builds), React Context providers for runtime DI, and `QueryDeps` injection for testability of the model call path. GrowthBook polls `/api/claude_code/settings` hourly for runtime A/B testing. Circular dependencies use lazy `require()` calls: `const getTeammateUtils = () => require('./utils/teammate.js')`.

For the Keystone project, the bootstrap/state.ts singleton pattern maps directly to a Temporal workflow state object, and the `QueryDeps` injection pattern maps to PydanticAI's dependency injection system.

---

## Effort levels reshape the entire behavior profile

Claude Code defaults to **medium** effort (not high), diverging from the raw API default. Four levels exist:

| Level | Thinking behavior | Tool usage | Availability |
|-------|------------------|------------|-------------|
| **low** | May skip thinking entirely | Fewer calls, terse confirmations, combined operations | Opus 4.6, Sonnet 4.6 |
| **medium** | Thinks on harder problems, skips on simple ones | Balanced | Opus 4.6, Sonnet 4.6 (CC default) |
| **high** | Almost always thinks | Full exploration, detailed explanations | Opus 4.6, Sonnet 4.6 |
| **max** | Maximum thinking, no token constraints | Exhaustive | **Opus 4.6 only** |

Effort is a **behavioral signal, not a strict token budget**. It affects all tokens — text, tool calls, and extended thinking. On Claude 4.6 models, `thinking: {type: "adaptive"}` lets the model dynamically decide thinking depth based on query complexity and effort level. Setting `CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING=1` reverts to fixed budgets controlled by `MAX_THINKING_TOKENS`.

**Priority order for effort**: environment variable (`CLAUDE_CODE_EFFORT_LEVEL`) > configured level > model default. Skill and subagent frontmatter can override per-invocation via an `effort:` field. The keyword "ultrathink" in a prompt triggers high effort for one turn.

**ULTRAPLAN** goes further: it offloads planning to a remote Cloud Container Runtime session running Opus 4.6 for up to **30 minutes** of thinking, polling every 3 seconds (`POLL_INTERVAL_MS = 3000`). A "teleport sentinel" (`__ULTRAPLAN_TELEPORT_LOCAL__`) detects completion and beams the result back.

---

## Tool system: registration, dispatch, and permission gating

Each tool implements a standard interface:

```typescript
interface Tool {
  name: string
  description: string
  inputSchema: JSONSchema7        // Zod v4-validated
  isEnabled(context): boolean     // Feature-gated visibility
  call(input, context: ToolUseContext): Promise<ToolResult>
  render(): ReactComponent        // Ink terminal component
  maxResultSizeChars: number      // Large results → temp file
}
```

**Registration pipeline**: `getAllBaseTools()` assembles the complete list → `getTools(permissionCtx)` filters by feature gates, user type, and environment flags → `assembleToolPool()` merges built-in tools with MCP tools. A `toolSchemaCache.ts` caches JSON schemas for prompt efficiency.

**Dispatch** partitions tools by safety class: read-only tools (`FileRead`, `Glob`, `Grep`, `WebSearch`, read-only MCP) run concurrently; state-modifying tools (`FileEdit`, `FileWrite`, `Bash`) serialize. Custom tools default to serial but can be marked `readOnly` for parallel execution.

**Permission check order** is a 4-stage pipeline:
1. Check **deny rules** (from `disallowed_tools` and settings) — blocks even in `bypassPermissions`
2. Check **hooks** — can allow, deny, or modify tool requests
3. Check **allow rules** (from `allowed_tools`, settings, built-in safe-tool allowlist)
4. Apply **active permission mode** (default/acceptEdits/plan/auto/dontAsk/bypassPermissions)

Auto mode runs a **separate LLM classifier call** on Claude Sonnet 4.6 for each proposed action, separating "what should I do" reasoning from "is this allowed" reasoning. This reduces permission prompts by **84%**. Results feed back to the orchestration loop as `tool_result` content blocks, and the loop continues until no more `tool_use` blocks appear.

**BashTool security** spans 9,707 lines across three files with **22 unique security validators** using tree-sitter WASM to build an AST of every command. A documented parser differential vulnerability exists where `splitCommand_DEPRECATED` (still active in 8+ security-critical files) treats `\r` as a word separator (JS `\s` includes CR), but bash's IFS doesn't — enabling injection via carriage return characters.

---

## Three-layer memory with background dream consolidation

The memory system is a deliberate hierarchy trading completeness for context efficiency:

**Layer 1 — MEMORY.md**: A lightweight index of pointers (~150 chars per entry). Always loaded. Stores *locations*, not data. Functions as a table of contents, not the book.

**Layer 2 — Topic files**: Actual project knowledge in `~/.claude/memory/`, fetched on-demand based on relevance. Never fully in context simultaneously. An LLM side-query on Sonnet selects relevant memories — not keyword matching.

**Layer 3 — Raw transcripts**: Session logs stored as JSONL in `~/.claude_code/sessions/`. Never loaded wholesale, only `grep`'d for specific identifiers.

**Write discipline**: The agent updates its memory index only after a confirmed successful file write. It treats its own memory as a "hint" and verifies facts against the actual codebase before acting.

**autoDream** (`src/services/autoDream/`) is the background memory consolidation engine. It has a triple-gated trigger (cheapest checks first): (1) ≥24 hours since last consolidation, (2) ≥5 sessions accumulated, (3) file-based advisory lock acquired (file's mtime doubles as `lastConsolidatedAt`, PID in body, stale after 1 hour even if PID alive). Four phases execute: Orient → Gather Recent Signal → Consolidate → Prune and Index. The dream subagent gets **read-only bash only** and keeps MEMORY.md under **200 lines / ~25KB**.

---

## Multi-agent orchestration patterns for Keystone

Three sub-agent execution models exist, each with different isolation/cost tradeoffs:

**Fork agents** share byte-identical prompt prefixes with the parent via KV cache. Spawning 5 agents costs barely more than 1. Fresh `messages[]` array, shared cache. This is the default for parallel work — **parallelism is essentially free**.

**Teammate agents** run in separate tmux/iTerm panes or in-process, communicating via a file-based mailbox pattern. Workers can't independently approve high-risk operations; they send requests to the coordinator's mailbox and wait. An atomic claim mechanism prevents two workers handling the same approval.

**Worktree agents** get isolated git worktrees per agent for risky/exploratory work that shouldn't touch main context.

**Coordinator Mode** (`src/coordinator/coordinatorMode.ts`) implements four phases: Research (parallel workers) → Synthesis (coordinator reads findings) → Implementation (workers make changes) → Verification (workers test). The orchestration algorithm is entirely prompt-driven: "Do not rubber-stamp weak work" and "You must understand findings before directing follow-up work. Never hand off understanding to another worker."

**Verification Agent** (`verificationAgent.ts:54`) has a built-in list of rationalizations to resist: "The implementer is an LLM. Verify independently." / "reading is not verification. Run it." / "probably is not verified. Run it."

For the Keystone project, the fork-agent pattern maps to Temporal child workflows sharing cached context; the mailbox pattern maps to Temporal signals for inter-workflow approval; and the coordinator prompt-as-algorithm pattern means your PydanticAI orchestration can encode strategy in system prompts rather than hard-coded control flow, making it updatable without redeployment.

---

## Conclusion: patterns to extract for Keystone

The most transferable implementation patterns from Claude Code's harness architecture are:

**AsyncGenerator as agent loop** — yields typed messages with natural backpressure, cancellation, and streaming. In PydanticAI + Temporal, implement as an async generator within a Temporal activity that yields intermediate results via heartbeats.

**Prompt cache boundary design** — split system prompts at a static/dynamic boundary. For Keystone's MCP gateway, cache the tool schema and base instructions; regenerate only user-specific context per session.

**4-stage compression cascade** — cheapest intervention first (trim tool outputs), then local edits (zero LLM cost), then semantic collapse, then full LLM summarization with circuit breaker. Implement as a Temporal workflow that escalates through stages.

**Fork-join via shared cache prefix** — subagents inherit parent context at near-zero marginal cost. Design Keystone's multi-agent system so child workflows share the parent's system prompt verbatim, hitting the prompt cache.

**QueryDeps injection for testability** — inject the model call function through a deps object, not as a hardcoded import. Maps directly to PydanticAI's dependency injection system.

**Speculative tool execution** — start read-only tools while the model is still streaming. In Temporal, fire read-only activities as soon as tool_use blocks appear in the stream, before the full turn completes.

**Prompt-as-algorithm for orchestration** — coordinator behavior is defined in system prompts, not code. This means orchestration strategy can be updated via configuration (CLAUDE.md equivalent) without redeployment — a pattern perfectly suited to MCP-served dynamic prompts in the Keystone gateway.

**Settings cascade with merge semantics for hooks** — highest-priority source wins for most settings, but hooks from all sources merge. Implement in Keystone as a layered config resolver where managed policies always win, but event handlers accumulate across all config layers.