# Claude Code's leaked architecture reveals how to enforce quality by design

**Anthropic's accidental publication of 512,664 lines of TypeScript on March 31, 2026 exposed the most detailed blueprint yet for building structurally enforced quality gates in an agentic AI system.** The leak — caused by a source map file left in npm package `@anthropic-ai/claude-code` v2.1.88 — reveals a system where quality enforcement exists on a clear spectrum: hard structural gates in code that cannot be bypassed, soft prompt-based instructions the model chooses to follow, and a hooks system that lets external code inject binary pass/fail decisions at every lifecycle boundary. For the Keystone Intelligence Engine's 5-layer evaluation stack, the hooks architecture and permission model provide directly applicable patterns for sprint contract enforcement at pipeline handoff points.

The source was first discovered by security researcher Chaofan Shou at ~4:23 AM ET, spread across 8,100+ GitHub mirrors within hours, and was analyzed independently by Alex Kim (alex000kim.com), WaveSpeedAI, the ComeOnOliver/claude-code-analysis repo, Kuberwastaken's Rust reimplementation (claurst), and sanbuphy's full source archive (6,300 stars, 12,400 forks). Anthropic confirmed it was "a release packaging issue caused by human error, not a security breach." The root cause was a missing `.npmignore` entry combined with Bun's default source map generation — ironic given Anthropic acquired Bun in late 2025.

---

## The 26-event hooks system is a universal lifecycle interceptor

The hooks system is Claude Code's most architecturally significant pattern for quality enforcement. It exposes **26 distinct lifecycle events** where external code can observe, modify, or block execution — far more than the "18+" initially reported. Four handler types execute at each hook point: **command** (shell scripts receiving JSON on stdin), **HTTP** (POST to URL endpoints), **prompt** (single-turn LLM evaluation), and **agent** (spawned subagent with Read/Grep/Glob tools for deep verification).

The complete event list spans the full agent lifecycle. Session-level events include `SessionStart`, `SessionEnd`, `InstructionsLoaded`, and `ConfigChange`. User interaction events cover `UserPromptSubmit` and `Notification`. The critical tool execution events are `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, and `PermissionDenied`. Agent orchestration events include `SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `TeammateIdle`, and `Stop`/`StopFailure`. Infrastructure events cover `CwdChanged`, `FileChanged`, `WorktreeCreate`, `WorktreeRemove`, `PreCompact`, and `PostCompact`. MCP integration events include `Elicitation` and `ElicitationResult`.

**The critical architectural insight is the decision control model.** `PreToolUse` hooks return a `permissionDecision` field with four possible values: `allow`, `deny`, `ask` (escalate to user), or `defer`. They can also return `updatedInput` to rewrite tool arguments before execution and `additionalContext` to inject information into Claude's context. `PostToolUse`, `Stop`, `SubagentStop`, `TaskCompleted`, and `ConfigChange` hooks support `decision: "block"` with a `reason` string. **Exit code 2 is the universal binary gate** — any hook returning exit code 2 blocks the action, with stderr fed to Claude as an error message. This creates a clean, composable enforcement surface.

The full tool execution lifecycle flows as: Claude decides to use tool → `PreToolUse` fires (can block/modify) → permission rules checked → `PermissionRequest` fires (can auto-allow/deny) → tool executes → on success, `PostToolUse` fires → on failure, `PostToolUseFailure` fires → results fed back to Claude → loop continues until `Stop` fires (which can itself be blocked, forcing continuation).

Configuration is hierarchical across five scopes: user-level (`~/.claude/settings.json`), project-level (`.claude/settings.json`, committable), project-local (`.claude/settings.local.json`, gitignored), managed policy (organization-wide admin), and plugin/skill YAML frontmatter. Enterprise administrators can set `allowManagedHooksOnly` to block all user/project hooks, creating a top-down enforcement model. Hooks run **in parallel** when multiple match, and output injected into context is capped at **10,000 characters**.

---

## Structural enforcement versus prompt compliance: a clear taxonomy

The leaked source reveals a stark divide between what Claude Code enforces structurally (code prevents bad outcomes) and what it enforces through prompt instructions (model chooses to comply). This distinction is the most directly relevant finding for the Keystone Intelligence Engine.

**Hard structural gates that cannot be bypassed by the model:**

The **Zod v4 schema validation** on every tool runs `validateInput()` before any permission check — malformed inputs are rejected at the code layer, not by model judgment. The **23-check bash security system** in `bashSecurity.ts` (2,592 lines) catches Zsh `=cmd` expansion attacks, `zmodload` kernel module loading, heredoc injection, ANSI-C quoting obfuscation, process substitution in untrusted contexts, Unicode zero-width space injection, `ztcp` network exfiltration, and compound attacks through line-by-line content matching. **Compile-time dead code elimination** via Bun's `feature()` intrinsic physically removes 108 modules from the npm package — features gated this way literally do not exist in the binary. The **autocompact circuit breaker** (`MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES = 3`) prevents runaway retry loops that were burning **~250,000 API calls/day globally** before the fix. The **path traversal prevention** system handles URL-encoded traversals, Unicode normalization attacks, backslash injection, and case-insensitive path manipulation in code.

**Soft prompt-based enforcement the model can theoretically ignore:**

The coordinator mode's quality gates are entirely prompt-based: "Never write 'based on your findings' — these phrases delegate understanding to workers" and "Do not rubber-stamp weak work." Safety rules for destructive operations are **embedded in tool descriptions**, not enforced by code: "NEVER run destructive git commands (push --force, reset --hard)" and "CRITICAL: Always create NEW commits rather than amending." The memory system's write discipline — treating its own memory as a "hint" and verifying against actual codebase — is a prompt instruction, not a structural constraint. The Undercover Mode prompt tells the model to "Write commit messages as a human developer would" — compliance depends entirely on model behavior.

**The hybrid middle ground — hooks as externalized structural enforcement:**

Hooks bridge the gap. A `Stop` hook running `npm test && npm run lint || exit 2` creates a **structurally enforced quality gate** that prevents Claude from completing work until tests and linting pass — but the enforcement mechanism is external code, not internal architecture. A `PreToolUse` hook blocking destructive bash commands converts what would be prompt-based guidance into a binary gate. This pattern — **externalizing enforcement to hook scripts while keeping the hook invocation mechanism structural** — is the most transferable pattern for pipeline boundary enforcement.

---

## The tool permission model uses five escalating trust tiers

Every tool invocation passes through a multi-stage permission pipeline that demonstrates defense-in-depth. The flow is: tool call request → `validateInput()` (reject invalid inputs) → `PreToolUse` hooks (user-defined gates) → permission rules (`alwaysAllowRules`, `alwaysDenyRules`, `alwaysAskRules` matched by tool name/pattern) → interactive prompt if no rule matches → `checkPermissions()` for tool-specific logic (e.g., path sandboxing) → approved → `tool.call()`.

Five permission modes control this pipeline's behavior. **Default mode** asks before writes, bash, and MCP calls. **AcceptEdits mode** auto-approves file edits but asks for bash. **DontAsk mode** approves everything. **BypassPermissions mode** (`--dangerously-skip-permissions`) skips all checks. **Auto mode** is the most architecturally interesting: each tool invocation triggers a **separate Sonnet 4.6 classifier call** that evaluates whether the proposed action matches the user's stated intent. This "critic" pattern — using a cheaper, faster model as a structural gate on a more capable model's actions — adds real latency and cost but provides adaptive, context-aware security that replaces brittle allowlists.

Each tool in the ~40-tool registry exposes a rich interface: `validateInput()` for early rejection, `checkPermissions()` for tool-specific authorization, `isEnabled()` for feature gating, `isConcurrencySafe()` for parallel execution decisions, `isReadOnly()` for side-effect classification, `isDestructive()` for irreversibility marking, and `interruptBehavior()` for cancel-or-block decisions. Risk classification tags every action as LOW, MEDIUM, or HIGH. Protected files (`.gitconfig`, `.bashrc`, `.zshrc`, `.mcp.json`, `.claude.json`) are guarded from automatic editing. The auto-mode classifier includes a **circuit breaker**: 3 consecutive or 20 total blocks pauses to manual mode, preventing infinite denial loops.

The `Edit` tool requires a prior `Read` — structurally preventing blind file overwrites. The `Write` tool requires prior `Read` for existing files. These are code-level gates, not prompt suggestions.

---

## Error handling follows a three-tier model with circuit breakers

Claude Code's error handling architecture operates at three distinct levels. **Exit code 0** means success, with JSON output processed for structured control signals. **Exit code 2** is a blocking error — the action is prevented, and stderr is shown to Claude as context. **Any other exit code** is a non-blocking error, logged in verbose mode but allowing execution to continue. For HTTP hooks, non-2xx responses, connection failures, and timeouts are all non-blocking — to actually block, the hook must return 2xx with appropriate JSON decision fields.

The retry strategy centers on the **QueryEngine** (`QueryEngine.ts`, 46,000 lines), which handles exponential backoff for API errors and rate limits. The autocompact system exemplifies the circuit breaker pattern: before the 3-failure limit was added, **1,279 sessions experienced 50+ consecutive compaction failures** (one session hit 3,272 consecutive failures), wasting ~250K API calls/day globally. Three lines of code — `MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES = 3` — eliminated this waste. Bridge-layer connections use exponential backoff from 2 seconds to 2 minutes; generation retries backoff from 500ms to 30 seconds.

The context compression system provides graceful degradation through three layers. **MicroCompact** edits cached content locally with zero API calls. **AutoCompact** fires when approaching the context window ceiling, reserves a **13,000-token buffer**, and generates up to **20,000-token structured summaries**. **Full Compact** compresses the entire conversation, re-injects recently accessed files (capped at 5,000 tokens per file), active plans, and skill schemas, resetting the post-compression budget to 50,000 tokens. The `PermissionDenied` hook can return `{ retry: true }` to signal that a denied action should be retried — enabling transient-condition handling.

---

## Anti-distillation reveals three layers of structural DRM

The leaked code exposes Anthropic's approach to preventing competitors from training on Claude Code's API traffic, implemented as **speed bumps rather than walls** — a philosophy Alex Kim characterized as "anyone serious about distilling would find workarounds in about an hour of reading the source."

**Layer 1: Fake tool injection.** In `claude.ts` (lines 301-313), the `ANTI_DISTILLATION_CC` compile-time flag enables sending `anti_distillation: ['fake_tools']` in API requests. The server silently injects **decoy tool definitions** into the system prompt, corrupting any training data captured by traffic interception. Activation requires all four conditions: compile-time flag enabled, CLI entrypoint (not SDK), first-party API provider, and GrowthBook feature flag `tengu_anti_distill_fake_tool_injection` returning true. A MITM proxy stripping the `anti_distillation` field bypasses it entirely.

**Layer 2: Connector-text summarization.** In `betas.ts` (lines 279-298), the server buffers assistant text between tool calls, summarizes it, and returns the summary with a **cryptographic signature**. On subsequent turns, original text can be restored from the signature. API traffic recorders capture only summaries, not full reasoning chains. This is Anthropic-internal-only (`USER_TYPE === 'ant'`).

**Layer 3: Native client attestation.** In `system.ts` (lines 59-95), API requests include a `cch=00000` placeholder in the `x-anthropic-billing-header`. Before the request leaves the process, **Bun's native HTTP stack (written in Zig)** overwrites the five zeros with a computed hash. The server validates the hash to confirm the request came from a real Claude Code binary. The computation happens below the JavaScript runtime — invisible to JS-layer inspection. The placeholder maintains the same byte length to avoid Content-Length changes. This is effectively DRM for API calls and likely why third-party tools like OpenCode were blocked at the API level. Weaknesses: running the JS bundle on stock Bun/Node leaves literal zeros; the server-side parser "tolerates unknown extra fields."

The frustration detection system in `userPromptKeywords.ts` uses a hardcoded regex matching profanity and frustration phrases (wtf, ffs, shit, "so frustrating", "this sucks", etc.) as a **product health metric** — not for behavior modification. As Kim noted: "An LLM company using regexes for sentiment analysis is peak irony" but pragmatic — regex runs in microseconds versus seconds for a model call.

---

## Undercover mode strips AI provenance from all outputs

Located in `undercover.ts` (~90 lines), this feature activates automatically for Anthropic employees (`USER_TYPE === 'ant'`) working in non-internal repositories. It injects a system prompt section marked "CRITICAL" that instructs Claude to never include internal model codenames (Capybara, Tengu, Fennec, Numbat), unreleased model versions (Opus 4.7, Sonnet 4.8), internal Slack channels or short links (`go/cc`, `#claude-code-…`), the phrase "Claude Code," any mention that the author is an AI, or `Co-Authored-By` lines.

The activation logic follows a one-way door design. `CLAUDE_CODE_UNDERCOVER=1` forces it ON. Otherwise, it activates automatically unless the repo remote matches an internal allowlist. **No force-OFF exists** — "if we're not confident we're in an internal repo, we stay undercover." In external builds, the entire function is dead-code-eliminated to trivial returns. The community reaction split three ways: reasonable IP protection, concerning AI-authorship concealment (undermining Developer Certificate of Origin compliance), and pragmatic acceptance that every company has unusual internal tooling.

For the Keystone Intelligence Engine, this reveals a pattern for **metadata management at output boundaries** — the system structurally controls what provenance information survives into external-facing artifacts, with the enforcement mechanism being prompt injection rather than output filtering code.

---

## Multi-agent orchestration uses mailbox isolation and three execution models

The coordinator mode demonstrates how Claude Code isolates parallel agent work. Three subagent execution models serve different use cases. **Fork** creates a byte-identical copy of the parent context, hitting the prompt cache so spawning 5 agents costs barely more than 1 in token cost — parallel work where cache reuse makes parallelism essentially free. **Teammate** runs in a separate tmux/iTerm pane, communicating via file-based mailbox — loose coordination between independent workstreams. **Worktree** creates an isolated git branch per agent — exploratory or risky work that shouldn't touch the main context.

The mailbox pattern enforces a critical structural gate: **worker agents cannot independently approve high-risk operations**. Workers send approval requests to the coordinator's mailbox and block until approved. An **atomic claim mechanism** prevents two workers from handling the same approval simultaneously. Read-only operations run concurrently; mutating operations run serially. This architecture — prompt-based orchestration logic with structurally enforced permission escalation — maps directly to pipeline boundary enforcement where stage N's outputs require validation before stage N+1 can consume them.

---

## Conclusion: patterns that transfer to pipeline boundary enforcement

The Claude Code leak reveals that Anthropic's quality enforcement operates on a **three-tier model** directly applicable to the Keystone Intelligence Engine's evaluation stack.

**Tier 1 (Structural/Code):** Input schema validation via Zod, compile-time feature elimination, circuit breakers with hard failure limits, path traversal prevention, and the exit-code-2 binary gate convention. These cannot be bypassed by model behavior and should correspond to Keystone's pipeline boundary validators — hard gates that block progression when contracts are violated.

**Tier 2 (Externalized Enforcement via Hooks):** The hooks system converts what would be prompt-based guidance into structural gates by delegating enforcement decisions to external code. The `Stop` hook pattern — running tests/linting and blocking completion on failure — is the direct analog to sprint contract enforcement at handoff points. The four handler types (command, HTTP, prompt, agent) provide a spectrum from fast binary checks to deep AI-powered verification.

**Tier 3 (Prompt Compliance):** Coordinator instructions, safety guidance in tool descriptions, and memory write discipline rely on model cooperation. These are appropriate for soft quality preferences but insufficient for critical pipeline boundaries.

The most transferable insight is that **the hooks architecture separates the "when to check" (structural, guaranteed invocation) from the "what to check" (externalized, configurable logic)**. Claude Code guarantees `PreToolUse` fires before every tool execution — that's structural. What the hook script evaluates and whether it returns exit code 0 or 2 — that's configurable. This separation principle, applied to Keystone's pipeline boundaries, would mean structurally guaranteed evaluation invocation at every stage handoff with pluggable, configurable quality gate logic that can evolve independently of the pipeline infrastructure.