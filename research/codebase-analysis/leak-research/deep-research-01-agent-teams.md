# Claude Code Agent Teams: architecture patterns from the v2.1.88 source leak

**Anthropic's leaked multi-agent system relies on radical simplicity — file-based coordination, prompt-driven orchestration, and aggressive prompt caching — offering several directly adoptable patterns for the Keystone Intelligence Engine while exposing critical isolation gaps.** The March 31, 2026 npm packaging error in Claude Code v2.1.88 exposed ~1,900 TypeScript files and 512,000 lines of code, revealing three distinct agent execution models (fork, teammate, worktree), a filesystem-only coordination substrate with no message broker, and a coordinator pattern implemented entirely through system prompts rather than code logic. Community analysis across dozens of GitHub repos, blog posts, and Hacker News threads has produced a detailed picture of the internal architecture. The most architecturally significant finding: **spawning parallel agents via fork mode achieves near-zero marginal token cost** through byte-identical prompt cache sharing, while the teammate mode trades that economy for full context isolation at **3–7× token overhead**.

---

## Three execution models serve fundamentally different parallelism needs

The leaked `AgentTool.tsx` routes every agent spawn through one of three paths, selected by the presence of specific parameters in the tool call.

**Fork mode** (`forkSubagent.ts`) creates a byte-identical copy of the parent's conversation context. The `FORK_AGENT` definition specifies `permissionMode: 'bubble'` and `useExactTools: true`, ensuring the forked child's API request prefix matches the parent's exactly. This triggers Anthropic's prompt cache, making the marginal cost of spawning 5 fork agents approximately equal to spawning 1. The `buildForkedMessages()` function clones the parent's last assistant message (including all `tool_use` blocks) and inserts placeholder `tool_results` identical across all fork children. A recursive fork guard detects a boilerplate tag in conversation history to prevent nested forking. Fork agents inherit the parent's full context but cannot themselves fork.

**Teammate mode** spawns entirely separate Claude CLI processes — literally new `claude` binary invocations in tmux or iTerm2 panes. Each teammate gets its own **1M-token context window** and does NOT inherit the lead's conversation history, receiving only CLAUDE.md, MCP server configurations, skills, and a spawn prompt. The `AsyncLocalStorage` context carries `agentId`, `agentName`, `teamName`, `parentSessionId`, `color`, and `planModeRequired`. Routing triggers when both `team_name` and `name` are present in the Agent tool call, delegating to `spawnTeammate()` in `spawnMultiAgent.ts`. The `CLAUDE_CODE_SPAWN_BACKEND` environment variable controls whether teammates run in-process (fastest, no visibility), in tmux panes (visible, persistent), or auto-detected.

**Worktree mode** creates an isolated git worktree per agent via `EnterWorktreeTool`/`ExitWorktreeTool`, giving each agent its own branch and working directory at `.claude/worktrees/<name>/`. Worktrees share repository history without full duplication. Auto-cleanup removes worktrees with no changes; those with modifications persist for review. A significant **known bug** (GitHub issue #33045) means `isolation: "worktree"` is silently ignored for team agents — they run in the main repo instead. This works correctly only for standalone subagents.

**Tradeoff matrix for Keystone mapping:**

| Dimension | Fork | Teammate | Worktree |
|-----------|------|----------|----------|
| Token cost | **~1× parent** (cache shared) | **3–7× baseline** (independent contexts) | Same as mode it wraps |
| Context inheritance | Full parent context | None (fresh start) | Mode-dependent |
| Communication | Return-to-parent only | Peer-to-peer mailbox | Mode-dependent |
| Isolation | Shared filesystem | Shared filesystem | Separate git branch |
| Spawn latency | Sub-second (in-process) | **20–30 seconds** (tmux process) | Seconds (git worktree create) |
| Best for | Parallel exploration of same problem | Independent long-running workstreams | Conflict-free file editing |

**→ Keystone assessment:**
- Fork mode → **ADOPT** for Component #7 (Research Agent Pipeline). Byte-identical prefix sharing maps directly to parallel research agents exploring different aspects of the same query. Use for the "fan-out" phase where multiple L1 agents investigate different facets of a decomposed research question.
- Teammate mode → **ADAPT** for Component #5 (Specification Engine). The coordinator-teammate pattern maps to L0 task decomposition and dispatch, but Keystone should use PydanticAI's structured agent spawning via Temporal workflows rather than tmux processes. The mailbox pattern needs adaptation for claim-level intermediate representations.
- Worktree mode → **SKIP** for Phase 1. Git worktree isolation solves code-editing conflicts, not research artifact conflicts. Keystone's filesystem-based agent isolation with advisory locks addresses the same problem domain more directly.

---

## The coordination substrate is entirely filesystem-based

The most striking architectural decision in Agent Teams is the absence of any background process, message broker, or shared memory. **All coordination happens through plain JSON files on disk**, with `flock()` providing the only concurrency primitive.

The **shared task list** stores individual JSON files at `~/.claude/tasks/{team-name}/`, one per task. Each task carries an `id` (auto-incremented via a `.highwatermark` counter file), `subject`, `description`, `activeForm` (present-continuous verb for the UI spinner), `owner`, `status`, and dependency arrays `blocks[]` and `blockedBy[]`. Tasks move through three states: `pending` → `in_progress` → `completed` (or `deleted`). When a blocking task completes, all downstream tasks with that ID in their `blockedBy` array automatically become claimable — no central scheduler orchestrates this; it emerges from the shared file state. A 0-byte `.lock` file in each task directory provides `flock()`-based mutual exclusion for task claiming, with teammates preferring lowest-ID-first ordering.

The **JSON inbox system** places per-agent mailbox files at `~/.claude/teams/{team-name}/inboxes/{agent-name}.json`. Each message is a JSON envelope: `{ from: string, text: string, timestamp: string, read: boolean }`, where `text` contains a JSON-in-JSON encoded payload. The protocol defines seven message types: `task_assignment` (lead → teammate), `message` (any → any direct message), `broadcast` (lead → all), `shutdown_request`/`shutdown_response` (graceful shutdown handshake), `plan_approval_request`/`plan_approval_response` (quality gate), and `idle_notification` (auto-sent by teammate after every LLM turn). The `SendMessageTool` supports direct addressing (`to: "teammate-name"`) and broadcast (`to: "*"`). As community analyst @klement_gunndu noted: "This is the simplest possible multi-agent communication protocol. You can `cat` the mailbox."

**File locking** uses `flock()` exclusively — advisory, not mandatory. Of 42 task directories examined on disk by reverse-engineer nwyin, only 5 contained actual task JSON files; the remaining 37 had only `.lock` and `.highwatermark`, suggesting aggressive cleanup after task completion.

**→ Keystone assessment:**
- Shared task list with dependency tracking → **ADOPT** for Component #5 (Specification Engine L0). The `blocks`/`blockedBy` dependency graph maps directly to Keystone's task decomposition. Replace JSON files with Temporal workflow state for durability, but keep the dependency resolution logic.
- JSON inbox system → **ADAPT** for Component #7 (Research Agent Pipeline). File-based messaging is too fragile for production (no delivery guarantees, race conditions on reads). Replace with Temporal signals or a lightweight Redis pub/sub, but preserve the message type taxonomy — especially `plan_approval_request/response` for L1.5 deliberation gates.
- File locking via `flock()` → **ADOPT** for Phase 1 filesystem-based agent isolation. Advisory locks match Keystone's planned approach exactly. The 0-byte lock file pattern is proven at Claude Code's scale (34M Explore agent runs/week).
- Automatic unblocking → **ADOPT** for Component #5. The pattern of downstream tasks unblocking when blockers complete maps directly to Temporal's workflow signal patterns.

---

## Coordination through prompts, not code, defines the orchestrator

The leaked `coordinatorMode.ts` (369 lines) reveals that **multi-agent orchestration is implemented entirely as a system prompt**, not branching code logic. The `getCoordinatorSystemPrompt()` function generates natural-language instructions that direct the LLM to act as a coordinator, making frameworks like LangChain "look like solutions in search of a problem" (HN user @simianwords).

The coordinator prompt establishes a **four-phase workflow**: Research (workers investigate in parallel) → Synthesis (coordinator reads and understands all findings) → Implementation (workers execute targeted changes) → Verification (workers test). The prompt explicitly bans the phrase "based on your findings" to prevent lazy delegation — the coordinator must include specific file paths, line numbers, and exactly what to change. Workers receive self-contained prompts because they cannot see the coordinator's conversation.

Three **quality gate hooks** enforce standards. `TeammateIdle` fires when a teammate finishes its turn — returning exit code 2 sends feedback and keeps the teammate working (use case: auto-assign follow-up tasks, run linters on recent changes). `TaskCompleted` fires when a task is marked complete — exit code 2 prevents completion and sends feedback (use case: require tests to pass before acceptance). `TaskCreated` validates task descriptions before creation. Hook handlers can be shell commands, single-turn LLM evaluations, or multi-turn subagent evaluations (up to 50 turns).

The coordinator has explicit rules about **spawn vs. reuse decisions**: continue workers via `SendMessage` to leverage loaded context; spawn new workers only for genuinely independent tasks. Concurrency rules: read-only tasks run freely in parallel; write-heavy tasks are serialized per file set. The lead can enter **delegate mode** (Shift+Tab) to restrict itself to coordination-only tools, preventing it from grabbing implementation work — a pattern community users reported as a common failure mode.

**→ Keystone assessment:**
- Prompts-as-orchestration → **INVESTIGATE** for Component #5 (Specification Engine). Claude Code proves that prompt-driven coordination works at scale for code tasks. However, Keystone's research context demands more structured orchestration (claim-level IRs, citation tracking, deduplication) that pure prompt engineering cannot enforce. The hybrid approach — Temporal for workflow guarantees, prompts for judgment calls — remains correct. Extract the four-phase workflow pattern and quality gate directives for L0 system prompts.
- Quality gate hooks → **ADOPT** for Component #9 (Basic Deliberation L1.5). The `TaskCompleted` hook pattern maps directly to Keystone's deliberation gates where independent parallel analyses must pass quality checks before synthesis. Implement as Temporal activity callbacks rather than shell scripts.
- Delegate mode → **ADAPT** for Component #5. Restricting the orchestrator to coordination-only tools prevents scope creep. Implement via tool allow-lists in PydanticAI agent definitions.

---

## Prompt caching strategy makes parallelism economically viable

The caching architecture, called "arguably the most valuable thing in the entire leak" by multiple analysts, splits the system prompt at `SYSTEM_PROMPT_DYNAMIC_BOUNDARY`. Everything before — instructions, tool definitions — caches globally across all organizations. Everything after — CLAUDE.md, git status, current date — varies per session. The ordering is deliberate: **Tools → Static System Prompt → Dynamic System Prompt → Messages**, maximizing the cacheable prefix length.

**Fourteen cache-break vectors** are tracked in `promptCacheBreakDetection.ts` with "sticky latches" that prevent mode toggles from oscillating cache invalidation. A function literally named `DANGEROUS_uncachedSystemPromptSection()` warns developers against adding volatile content to cacheable sections. Plan mode preserves cache by keeping ALL tools loaded and adding `EnterPlanMode`/`ExitPlanMode` as tools rather than swapping tool sets. MCP tool loading uses `defer_loading: true` stubs instead of removing unused tools (which would break cache). Model switching routes through subagents because **caches are per-model** — switching Opus→Haiku mid-session forces a full cold-start cache build.

The economics are dramatic. Anthropic's cache read pricing for Opus is **$0.50/MTok** (10% of the $5/MTok base input price), while cache writes cost **$6.25/MTok** (125% of base). Over 90% of tokens in a typical heavy session are cache reads. The compaction routine itself uses the fork pattern — identical prefix as the parent session, so KV cache is reused even when context is being compressed. Three compression strategies operate at different scales: **MicroCompact** edits cached content locally with zero API calls, **AutoCompact** fires near the context ceiling with a 13,000-token buffer, and **Full Compaction** generates a boundary marker with AI summary.

A critical limitation: **after compaction, the team lead completely loses awareness of its team** (GitHub issue #23620). Team state is not re-injected after summarization, causing the lead to become unable to message teammates or coordinate tasks.

**→ Keystone assessment:**
- System prompt boundary splitting → **ADOPT** for all pipeline layers. Structure Keystone agent system prompts with stable instructions first, variable context last. This directly reduces costs for Component #7's parallel research agents.
- Cache-break tracking → **ADAPT** for Component #4 (MCP Gateway). Track cache invalidation vectors at the gateway level. When routing requests to different models (Opus for judgment, Sonnet for throughput, Haiku for extraction), ensure per-model cache isolation is respected. Route model-specific work through dedicated agent instances.
- Fork-based cache sharing → **ADOPT** for Component #7. When fanning out research agents from L0, ensure the shared prefix (system prompt + tool definitions + research context) is byte-identical across all L1 agents. This is the single highest-impact cost optimization available.
- Compaction strategies → **INVESTIGATE** for long-running research sessions. The MicroCompact/AutoCompact/Full hierarchy is elegant but the team-awareness-loss bug suggests fragility. Keystone's claim-level IRs at handoff boundaries may be a safer approach than mid-session compaction.

---

## Isolation guarantees have a critical gap at inter-agent channels

Claude Code's isolation model operates at three levels. **Context isolation**: each teammate has an independent 1M-token context window, receiving only the spawn prompt, CLAUDE.md, and MCP configurations — no conversation history inheritance. **Filesystem isolation**: git worktrees provide per-agent branches (when working correctly; see bug #33045). **Permission isolation**: teammates inherit the lead's permission settings at spawn time, including the dangerous `--dangerously-skip-permissions` flag.

The **AgentLeak benchmark** (arXiv:2602.11510, Polytechnique Montreal, February 2026) provides the most rigorous external assessment of multi-agent isolation. Testing 1,000 scenarios across four domains with 4,979 execution traces, AgentLeak measured seven leakage channels (C1: final output, C2: inter-agent messages, C3: tool I/O, C4: tool output, C5: shared memory, C6: system logs, C7: artifacts). The headline finding: **inter-agent messages (C2) leak at 68.8%**, the highest of any channel. Multi-agent configurations actually reduce per-channel output leakage (C1: **27.2% vs. 43.2%** in single-agent) but introduce unmonitored internal channels that raise total system exposure to **68.9%** when OR-aggregated across C1, C2, and C5. The pattern C2 ≥ C1 holds consistently across all five tested models and four domains.

Critically, **Claude 3.5 Sonnet achieved the lowest leakage**: 3.3% external (C1) and 28.1% internal (C2), suggesting safety alignment training partially transfers to internal channels. But no model eliminates leakage entirely. The tested frameworks — LangChain, CrewAI, AutoGPT, MetaGPT — all propagate complete task contexts between agents during delegation. Claude Code's Agent Teams were not directly tested, but the file-based mailbox system creates C2-type channels and the shared task list creates C5-type channels.

AgentLeak recommends **message-level sanitization** (apply output redaction to inter-agent communication), **selective disclosure** (share only minimum necessary fields per subtask), **memory access controls** (field-level permissions), and **full-channel auditing** across all internal pathways.

**→ Keystone assessment:**
- Context window isolation → **ADOPT** for Component #7. Each L1 research agent should receive only its specific research question and relevant context, never the full L0 decomposition or other agents' findings. This is both a privacy measure and a quality measure (prevents anchoring bias).
- Inter-agent message sanitization → **ADOPT** for Component #8 (CitationProcessor). When agents pass findings to the deliberation layer, sanitize intermediate reasoning and pass only structured claim-level representations. This addresses the C2 leakage vector directly and aligns with Keystone's planned claim-level IRs.
- Advisory file locking → **ADOPT** as planned. Claude Code proves `flock()` works for coordination at scale. But supplement with **per-agent working directories** rather than depending on the buggy worktree isolation.
- Full-channel auditing → **ADOPT** for Component #4 (MCP Gateway). Log all inter-agent communications at the gateway level, not just final outputs. The AgentLeak finding that output-only audits miss 41.7% of violations is directly actionable.

---

## Known failure modes reveal production hardening requirements

Community bug reports reveal several systemic issues in Agent Teams. **Zombie/orphan agents** are the most persistent: subagent-created teams persist on disk after session ends, blocking future team creation (#32730); dead teammates persist in `config.json` across sessions, causing the lead to spawn duplicates (#29271); `TeamDelete` blocks indefinitely on hung agents with no force-kill or timeout (#31788). **Context loss after compaction** (#23620) causes the lead to forget its team exists mid-session. A **race condition** in snapshot capture (#40270) means `getTeammateModeFromSnapshot` is called before the snapshot is captured, causing all Agent tool calls with `team_name` to fail. Teammates **ignore `bypassPermissions`** for Bash and don't inherit project-local settings (#26479), requiring dozens of manual approvals per session.

The community has converged on a recommended configuration: **3–5 teammates with 5–6 tasks each**, using delegate mode to prevent the lead from grabbing implementation work, and enforcing strict file-domain separation to prevent overwrites. Token consumption runs **3–7× baseline** depending on team size, with an additional ~33% coordination overhead beyond the raw agent multiplier. Anthropic's internal C compiler benchmark used 16 agents across ~2,000 sessions with ~2 billion input tokens at under $20,000 total cost.

**→ Keystone assessment:**
- Zombie agent cleanup → **ADOPT** defensive pattern for Component #7. Implement Temporal workflow timeouts and heartbeat-based liveness detection. Never rely on agent self-cleanup — use Temporal's built-in cancellation and timeout mechanisms.
- Context loss after compaction → **SKIP** the problem. Keystone's architecture uses claim-level IRs at handoff boundaries rather than long-running sessions. Each L1 agent produces a structured output and terminates; no mid-session compaction needed.
- Race conditions in initialization → **ADOPT** the lesson, not the pattern. Use Temporal's workflow-started guarantee rather than async snapshot capture. Ensure all agent context is fully materialized before the agent begins execution.
- Permission inheritance → **ADAPT** for Component #4 (MCP Gateway). Enforce tool authorization at the gateway level, not through agent inheritance. Each agent gets an explicit tool allow-list based on its role in the pipeline, not inherited from a parent.

---

## Consolidated mapping to Keystone Intelligence Engine

**Component #5 — Specification Engine (L0):** ADOPT the four-phase coordinator workflow (Research → Synthesis → Implementation → Verification, adapted as Decompose → Research → Deliberate → Synthesize). ADOPT dependency-tracked task lists with `blocks`/`blockedBy` semantics via Temporal workflow state. ADAPT the coordinator system prompt pattern — use structured prompts for task decomposition judgment while maintaining Temporal for workflow guarantees.

**Component #7 — Research Agent Pipeline (L1):** ADOPT fork-mode cache sharing as the primary cost optimization — ensure byte-identical system prompt prefixes across all parallel research agents. ADOPT context window isolation (each agent gets only its research question, not other agents' work). ADOPT advisory file locking for artifact management. Target **3–5 parallel research agents** per decomposed query, matching Claude Code's empirically validated sweet spot.

**Component #4 — MCP Gateway:** ADOPT full-channel auditing across all inter-agent communication. ADAPT per-agent tool allow-lists (Claude Code's `useExactTools: true` pattern). ADOPT cache-break tracking at the gateway level to prevent inadvertent cost spikes from model switching or context modifications. Implement **rate limiting per-agent** rather than per-session.

**Component #8 — CitationProcessor:** ADOPT message-level sanitization at agent boundaries to address the C2 leakage vector. The claim-level IR approach already planned for Keystone directly addresses AgentLeak's recommendation of "selective disclosure" — agents share only structured claims, not raw reasoning chains. ADAPT the broadcast message pattern for cross-agent finding deduplication.

**Component #9 — Basic Deliberation (L1.5):** ADOPT the `TaskCompleted` hook pattern as quality gates on research agent outputs. ADOPT the mandatory reflection prompt pattern ("What specifically failed? What one change would fix it?") with a maximum retry count to prevent infinite loops. ADAPT the `plan_approval_request/response` protocol for deliberation consensus-building between independent parallel analyses.

**Cross-cutting — Model mixing:** Claude Code's explicit model routing (parent chooses Haiku/Sonnet/Opus per child) validates Keystone's planned Opus-for-judgment, Sonnet-for-throughput, Haiku-for-extraction strategy. **ADOPT** the per-model cache isolation principle — never switch models within an agent session; spawn dedicated agent instances per model tier. ADOPT the `defer_loading` stub pattern for MCP tools to maximize cache hit rates across agents sharing the same model tier.