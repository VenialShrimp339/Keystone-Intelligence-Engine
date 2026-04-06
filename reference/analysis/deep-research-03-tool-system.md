# Claude Code's tool system: a blueprint for agentic tool architecture

**Claude Code's leaked source reveals a sophisticated, protocol-based tool architecture that treats every capability — from file reads to sub-agent spawning — as a permission-gated, schema-validated tool with fail-closed defaults.** The accidental exposure of 512,000 lines of TypeScript on March 31, 2026, via a misconfigured npm source map, provides the most detailed public reference for building production-grade agentic tool systems. For the Keystone Intelligence Engine, the patterns most directly applicable are the three-tier tool registry assembly, per-call concurrency classification, structural tool isolation for sub-agents, and the MCP-native integration model that treats external tools as first-class citizens alongside built-ins.

The leak occurred when Anthropic shipped Claude Code v2.1.88 with a 59.8 MB `cli.js.map` file containing the full unobfuscated TypeScript source. Security researcher Chaofan Shou discovered it; Anthropic confirmed it as "a release packaging issue caused by human error." The company filed DMCA takedowns against 8,100+ repositories, though clean-room reimplementations like claw-code (105K+ GitHub stars) remain active.

---

## The Tool interface is a protocol, not a class hierarchy

Every capability Claude Code exposes to the model is represented as a structural type `Tool<Input, Output, P>` defined in `Tool.ts` (~29,000 lines). This is a protocol — any object satisfying the interface qualifies as a tool, whether built-in, MCP-sourced, or dynamically generated. The core interface:

```typescript
export type Tool<Input extends AnyObject, Output, P extends ToolProgressData> = {
  name: string                    // primary identifier the model uses
  aliases?: string[]              // legacy names for backward compat
  inputSchema: Input              // Zod v4 schema — source of truth
  maxResultSizeChars: number      // overflow → persist to disk

  call(args, context, canUseTool, parentMessage, onProgress?): Promise<ToolResult<Output>>
  checkPermissions(input, context): Promise<PermissionResult>
  isConcurrencySafe(input): boolean
  isReadOnly(input): boolean
  isDestructive?(input): boolean
  isEnabled(): boolean

  // UI rendering hooks
  renderToolUseMessage(): ReactNode
  renderToolResultMessage(): ReactNode

  // Security and search
  toAutoClassifierInput(): string  // compact repr for security classifier
  interruptBehavior?(): 'cancel' | 'block'

  // Deferred loading control
  shouldDefer?: boolean            // schema omitted from initial prompt
  alwaysLoad?: boolean             // never deferred

  // Context-aware prompt generation
  prompt(options): Promise<string>
}
```

The `buildTool()` factory merges partial definitions with **fail-closed defaults**: `isConcurrencySafe` defaults to `false`, `isReadOnly` defaults to `false`, and `isDestructive` defaults to `false`. This means any tool that fails to declare its safety profile is treated as a stateful, non-concurrent operation. The `ToolResult<T>` type includes an optional `contextModifier` function — this is how tools like `EnterPlanMode` mutate shared state without global variables, but it is only honored for non-concurrent tools, preventing race conditions.

A critical design decision: **`isConcurrencySafe` takes the tool's input as an argument**, making concurrency classification per-call rather than per-tool. A Bash invocation running `ls` can be marked safe for parallel execution while `rm -rf` runs serially. This input-dependent safety classification is directly applicable to Keystone's per-agent tool isolation — tools can enforce different safety profiles depending on what they're being asked to do.

The schema rendering pipeline converts each tool through `toolToAPISchema()`, which generates the model-facing definition: tool name, a context-aware description produced by calling `tool.prompt()`, and a JSON Schema derived from the Zod input schema. These rendered schemas are cached via `toolSchemaCache.ts` for the duration of a session.

---

## Seven-stage dispatch pipeline with streaming execution

Tool dispatch follows a rigorous seven-stage pipeline in `toolExecution.ts`, with the function `checkPermissionsAndCallTool()` as the central orchestrator:

**Stage 1 — Routing.** `findToolByName()` matches the model's requested tool name, falling back to aliases for backward compatibility. An abort-before-start check prevents execution if the user has interrupted.

**Stage 2 — Schema validation.** The tool's Zod `inputSchema.safeParse(input)` runs first. Failure returns an `InputValidationError` immediately, preventing any downstream processing of malformed input.

**Stage 3 — Semantic validation.** `tool.validateInput()` handles custom per-tool checks that go beyond schema validation — for example, checking that a file path exists or that a command is syntactically valid.

**Stage 4 — Input cloning.** `backfillObservableInput` creates a shallow clone, and the system maintains **three distinct input copies**: the API-bound original (preserved for cache integrity), a backfilled clone for hooks and permission checks, and a hook-updated copy for actual execution. This separation prevents hooks from contaminating cached data.

**Stage 5 — PreToolUse hooks.** Async generators that can yield progress updates, modify input, set permission results, or halt execution entirely. For Bash commands, a speculative security classifier starts running in parallel *before* hooks complete, optimizing latency.

**Stage 6 — Permission gate.** `canUseTool()` evaluates always-allow/deny rules, runs the auto-classifier if configured, and falls back to an interactive user prompt. This is the critical enforcement point.

**Stage 7 — Execution and result processing.** `tool.call()` runs with a progress callback, followed by PostToolUse hooks. Results pass through `mapToolResultToToolResultBlockParam()` with size-budget processing — oversized results are persisted to disk rather than stuffed into context.

The `StreamingToolExecutor` starts executing tools as response blocks stream in from the API, before the full model response finishes. Tool lifecycle states are `'queued' | 'executing' | 'completed' | 'yielded'`. Results are emitted in the order the model requested them (paired by tool_use ID), even though execution may complete out of order. Only **Bash tool errors cascade to sibling tools** via a `siblingAbortController` — all other tool failures are independent, preventing one failing web fetch from aborting a parallel file read.

The concurrency partitioning algorithm in `toolOrchestration.ts` is straightforward: consecutive tools where `isConcurrencySafe(input)` returns `true` batch into a parallel group, with a ceiling of **10 concurrent executions** (configurable via `CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY`). Any non-safe tool breaks the batch and runs alone.

---

## Permission model enforces defense-in-depth at every boundary

The permission system is among the most sophisticated components, centered on a `DeepImmutable<ToolPermissionContext>` that prevents accidental mutation:

```typescript
export type ToolPermissionContext = DeepImmutable<{
  mode: PermissionMode       // 'default' | 'plan' | 'bypassPermissions' | 'dontAsk'
  alwaysAllowRules: ToolPermissionRulesBySource
  alwaysDenyRules:  ToolPermissionRulesBySource
  alwaysAskRules:   ToolPermissionRulesBySource
  shouldAvoidPermissionPrompts?: boolean  // background agents: auto-deny
}>
```

**Five permission modes** govern behavior: `default` (prompts user for non-approved tools), `acceptEdits` (auto-approves file edits but NOT MCP tools), `dontAsk` (converts any prompt into a denial — tools pre-approved by rules run, everything else is blocked), `bypassPermissions` (auto-approves everything), and `plan` (prevents all tool execution, allowing only analysis).

Permission rules use a **glob-based syntax** that acts as the universal governance vocabulary: `Bash(git *)` allows all git commands, `FileEdit(/src/*)` allows edits within src, `mcp__puppeteer__*` grants all tools from a specific MCP server, and `Agent(my-custom-agent)` controls which sub-agents can be spawned. Rules cascade from managed (enterprise) → project → user → local settings, with managed rules taking precedence.

The **BashTool security subsystem** alone spans 9,707 lines across three files (`bashSecurity.ts`, `bashParser.ts`, `ast.ts`), running 25+ validators using regex matching, `shell-quote` parsing, and a Tree-sitter WASM parser for AST analysis of every command. The validator chain follows a specific order, with early-allow short circuits for known-safe patterns like `git commit`. Security researcher Jun Zhou identified a parser differential vulnerability where `shell-quote` and Bash disagree on carriage return tokenization — a reminder that even deeply layered permission models have edge cases.

For Keystone's MCP gateway design, the most transferable pattern is the **rule-based permission syntax with per-source cascading**. Rather than embedding permission logic in each tool, Claude Code externalizes it into declarative rules that stack across configuration sources. This decouples permission policy from tool implementation.

---

## Sub-agents get structurally isolated tool pools

Claude Code's approach to tool subsetting for sub-agents directly validates Keystone's per-agent tool assignment architecture. The `AgentTool` spawns sub-agents as regular tool calls — no separate orchestration framework — and each sub-agent receives an **independently assembled tool pool**.

The isolation mechanism works through three layers:

- **`ALL_AGENT_DISALLOWED_TOOLS`** strips dangerous tools from all agents
- **`CUSTOM_AGENT_DISALLOWED_TOOLS`** adds restrictions for non-built-in agent types  
- **`ASYNC_AGENT_ALLOWED_TOOLS`** further restricts background agents that run without user supervision
- MCP tools (prefixed `mcp__`) pass through these filters, preserving external tool access

`resolveAgentTools()` in `agentToolUtils.ts` refines each agent's pool based on its definition's tool allowlist/denylist, supporting wildcards. The SDK exposes this directly:

```yaml
agents:
  code-reviewer:
    tools: [Read, Grep, Glob]    # 3 focused tools
  test-runner:
    tools: [Bash, Read]          # 2 focused tools
```

Sub-agents **cannot spawn further sub-agents**, preventing recursion loops. They operate with high permissions within their scope but automatic blocking outside it. The `shouldAvoidPermissionPrompts` flag on background agents converts any would-be user prompt into an automatic denial — meaning background agents fail closed rather than blocking on unavailable human input.

The SDK's `tools` option controls which built-in tools appear in context, `allowedTools` pre-approves tools to run without prompts, and `disallowedTools` blocks tool calls while keeping the tool visible to the model. Setting `tools: []` removes all built-ins entirely, leaving only MCP tools — enabling the pattern where a specialized agent operates exclusively through a curated MCP tool surface.

This architecture directly supports the principle that **specialized agents with 5 focused tools outperform generalist agents with 50**. Claude Code's own verification agent (`verificationAgent.ts`) demonstrates this — it receives a narrow tool set and explicit instructions to resist rationalizations like "the code looks correct based on my reading."

---

## Three-tier registry merges built-ins with MCP tools seamlessly

The tool registry follows a three-stage assembly pipeline that cleanly separates concerns:

**Stage 1: `getAllBaseTools()`** returns every tool that *could* exist in the current build. Feature flags using Bun's compile-time `feature()` function gate conditional tools — `SleepTool` only loads when `PROACTIVE` or `KAIROS` flags are active, `REPLTool` requires `USER_TYPE === 'ant'`. This uses dead-code elimination, so gated tools are physically absent from production builds.

**Stage 2: `getTools()`** filters by runtime context. Simple mode (`CLAUDE_CODE_SIMPLE`) reduces to Bash, Read, and Edit. Deny rules prune tools matching `alwaysDenyRules`. Each tool's `isEnabled()` can veto itself based on environment.

**Stage 3: `assembleToolPool()`** merges built-ins with MCP tools:

```typescript
export function assembleToolPool(permissionContext, mcpTools): Tools {
  const builtInTools = getTools(permissionContext)
  const allowedMcpTools = filterToolsByDenyRules(mcpTools, permissionContext)
  const byName = (a, b) => a.name.localeCompare(b.name)
  return uniqBy(
    [...builtInTools].sort(byName).concat(allowedMcpTools.sort(byName)),
    'name',
  )
}
```

Built-in and MCP tools are sorted as **two separate alphabetical groups** concatenated together. This preserves Anthropic's server-side prompt cache breakpoint between the tool definition sections — a subtle but important optimization that prevents tool discovery from invalidating cached prompt prefixes.

MCP tools follow the naming convention `mcp__{server_name}__{tool_name}` (e.g., `mcp__github__list_issues`). They support all four MCP transport types: HTTP (recommended), SSE, stdio (local processes), and WebSocket. The `MCPConnectionManager` handles server discovery from configuration, lifecycle management (connect → initialize → list tools), OAuth 2.0 authentication, and reconnection with backoff.

**Deferred tool loading** solves the "too many tools" problem. Tools with `shouldDefer: true` have their schemas omitted from the initial system prompt. The model must call `ToolSearchTool` to discover and load deferred tools on demand. MCP tools are **always deferred** by default since there can be hundreds. The `ToolSearchTool` itself and tools marked `alwaysLoad: true` (like `AgentTool`) are never deferred. Tool descriptions are truncated at 2KB each, with a warning at 10,000 tokens and a hard limit of 25,000 tokens for MCP tool output.

---

## Conclusion: patterns directly applicable to Keystone

Claude Code's tool architecture offers several patterns that map directly to Keystone's design needs. For the **MCP gateway** (Component #4), the three-tier assembly pipeline with separate built-in and MCP sorting provides a clean model — external tools integrate through the same interface as built-ins, with permission rules applied uniformly via glob syntax. The deferred loading pattern with `ToolSearchTool` solves tool discovery at scale without bloating context.

For **per-agent tool assignment** (Component #7), Claude Code validates the structural isolation approach. Each sub-agent gets an independently assembled tool pool, with cascading disallow lists preventing dangerous tools from leaking into agent contexts. The `tools: []` option that strips all built-ins, leaving only MCP tools, enables the exact pattern Keystone needs — agents operating exclusively through a curated MCP surface with 3-5 focused tools.

The most nuanced insight is the **per-call concurrency classification** via `isConcurrencySafe(input)`. Rather than declaring tools globally safe or unsafe for parallel execution, Claude Code evaluates safety based on what the tool is actually being asked to do. This enables Keystone's research agents to run read-only operations in parallel while serializing writes — at the tool-call level, not the tool-type level.

Finally, the fail-closed default philosophy — assume writes, assume not concurrent, assume destructive — provides the correct security posture for a multi-agent system where tools cross trust boundaries. Permission rules externalized as declarative, cascading glob patterns decouple policy from implementation, enabling Keystone's MCP gateway to enforce tool isolation without modifying individual tool code.