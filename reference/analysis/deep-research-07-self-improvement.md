# Claude Code leak reveals a self-improving agent architecture

**On March 31, 2026, Anthropic accidentally published the entire Claude Code source — 512,000 lines of TypeScript — via a source map file left in an npm package.** The leak exposed the complete "agentic harness" wrapping Claude's LLM: a sophisticated system of persistent memory, background consolidation, autonomous daemon capabilities, and multi-agent orchestration. For teams building production agent systems, the leaked architecture provides the most detailed public blueprint of how a top-tier AI coding agent manages knowledge accumulation, self-improvement, and long-running autonomy. This report extracts every implementation pattern relevant to the Keystone Intelligence Engine, with evidence quality clearly labeled for each finding.

## How the leak happened and what it exposed

Security researcher Chaofan Shou discovered that Claude Code v2.1.88 shipped with a **59.8 MB source map file** (`cli.js.map`) in its npm package. The `.map` file pointed to a zip archive on Anthropic's Cloudflare R2 bucket containing the full, unobfuscated TypeScript source. Root cause: a missing `*.map` entry in `.npmignore` combined with Bun (Anthropic's JavaScript runtime) generating source maps by default. A relevant Bun bug (oven-sh/bun#28001) had been filed March 11 and remained open.

The exposure included **~1,906 files**, **44 feature flags** (20+ unshipped features), **108 feature-gated modules**, and the entire client-side orchestration layer. Model weights, training data, customer data, and API credentials were not exposed. Anthropic confirmed it was "a release packaging issue caused by human error, not a security breach." GitHub mirrors accumulated **50,000 stars in under two hours** before DMCA takedowns hit ~8,100 repositories (later narrowed to 96 containing actual leaked source).

What follows is a systematic extraction of implementation patterns organized by the six research targets, with evidence quality rated as **confirmed in code**, **reported by credible analyst**, or **speculative**.

## KAIROS: the always-on daemon with a tick-driven heartbeat

KAIROS (Ancient Greek for "the right time") is the most architecturally significant unreleased feature, referenced **over 150 times** in the source. It transforms Claude Code from a request-response tool into a persistent background agent. Evidence quality: **confirmed in code** with specific file paths and line numbers verified by multiple independent analysts.

**The tick loop** is the core mechanism. When the message queue empties — normally triggering wait-for-user-input — the system instead injects a `<tick>` message containing the current timestamp. Located at `src/cli/print.ts:L1834-L1856`, the implementation uses `setTimeout(0)` to yield to the event loop, letting pending stdin messages preempt the tick. The system prompt instructs the model: *"You are running autonomously. You will receive `<tick>` prompts that keep you alive between turns — just treat them as 'you're awake, what now?'"*

**The SleepTool** prevents burning API calls on empty ticks. The model explicitly balances cost versus responsiveness: *"Each wake-up costs an API call, but the prompt cache expires after 5 minutes of inactivity — balance accordingly."* If the agent has nothing useful to do, it **must** call Sleep — responding with a status message wastes tokens.

**A 15-second blocking budget** (`ASSISTANT_BLOCKING_BUDGET_MS = 15_000` at `src/tools/BashTool/BashTool.tsx:L57`) auto-backgrounds any shell command exceeding the limit. The `.unref()` call on the timer prevents it from keeping Node alive. When auto-backgrounded, the agent receives a notification with the background task ID and output path, and continues processing other work.

**Append-only daily logs** replace MEMORY.md rewrites in KAIROS mode. Located at `src/memdir/memdir.ts:L319-L348`, the implementation writes observations to date-stamped files following the pattern `logs/YYYY/MM/YYYY-MM-DD.md`. These logs cannot be self-erased, creating an audit trail. When the date rolls over mid-session, a new file begins. A separate nightly `/dream` skill distills logs into topic files and MEMORY.md.

KAIROS also introduces exclusive tools: **SendUserMessage** (BriefTool) for delivering replies through a filtered channel, **SendUserFile** for pushing files, **PushNotification** for device notifications, and **SubscribePR** for monitoring pull request activity. The `status` field on messages distinguishes `'normal'` replies from `'proactive'` unsolicited updates, affecting notification routing. Schema extensions give KAIROS agents the ability to specify their own working directory and run in isolated git worktrees — without KAIROS, these fields are stripped from the schema so the model never sees them.

**The full runtime cycle**: tick fires → agent checks for work → runs commands (auto-backgrounds anything >15s) → logs observations to append-only daily log → sends results through SendUserMessage → queue empties → next tick scheduled → agent sleeps or acts again.

## autoDream consolidates memory through a four-phase cycle

autoDream is the background memory consolidation engine, located in `src/memdir/autoDream.ts` within the `memdir/` directory. It runs as a **forked subagent** — a deliberate architectural choice to prevent the main agent's reasoning from being corrupted by maintenance routines. Evidence quality: **confirmed in code** with the actual source file available in a public gist and the full consolidation prompt reproduced by multiple sources.

**Three gates must pass** before a dream cycle triggers, checked in order of computational cost:

1. **Time gate**: ≥24 hours since `lastConsolidatedAt` (configurable via `minHours`)
2. **Session gate**: ≥5 sessions with modification time after last consolidation (configurable via `minSessions`)
3. **Lock gate**: Filesystem lock acquired (`tryAcquireConsolidationLock`) to prevent concurrent dreams

A scan throttle of **10 minutes** (`SESSION_SCAN_INTERVAL_MS = 10 * 60 * 1000`) prevents repeated scanning when the time gate passes but the session gate doesn't. The function returns early if KAIROS mode is active (KAIROS uses its own "disk-skill dream" instead), if running in remote mode, or if auto memory is disabled. The feature flag `tengu_onyx_plover` controls scheduling knobs.

**The four-phase consolidation process** is defined in `services/autoDream/consolidationPrompt.ts`:

- **Phase 1 — Orient**: `ls` the memory directory, read MEMORY.md to understand the current index, skim existing topic files to avoid creating duplicates. If `logs/` or `sessions/` subdirectories exist (KAIROS layout), review recent entries.
- **Phase 2 — Gather recent signal**: Search sources in priority order: daily logs, memories that have drifted from codebase reality, then transcript search via targeted grep (`grep -rn "<narrow term>" <project-transcripts>/ --include="*.jsonl" | tail -50`). Explicitly instructed: *"Don't exhaustively read transcripts. Look only for things you already suspect matter."*
- **Phase 3 — Consolidate**: Merge new signal into existing topic files, avoiding near-duplicates. **Convert relative dates to absolute** ("yesterday we decided to use Redis" becomes "On 2026-03-15 we decided to use Redis"). Delete contradicted facts at source. Remove stale memories referencing deleted files. Merge overlapping entries.
- **Phase 4 — Prune and index**: Keep MEMORY.md under **200 lines** and **~25KB**. Remove stale pointers to nonexistent files. Demote verbose entries (keep gist in index, move detail to topic file). Add pointers to newly important memories. Resolve contradictions between files.

Safety constraints are strict: the dream subagent gets **read-only bash** (limited to `ls`, `find`, `grep`, `cat`, `stat`, `wc`, `head`, `tail`), can only write to memory files (`~/.claude/projects/<project>/memory/`), and operates behind a filesystem lock preventing concurrent runs. On failure, the lock rolls back so the time gate passes again on the next attempt. One observed case consolidated **913 sessions in ~8-9 minutes**.

The key data structures are: `AutoDreamConfig` (`{ minHours: number, minSessions: number }`), `DreamTask` for progress tracking via `makeDreamProgressWatcher()`, and the consolidation lock managed through `readLastConsolidatedAt`, `listSessionsTouchedSince`, `tryAcquireConsolidationLock`, and `rollbackConsolidationLock`.

## MEMORY.md is a three-tier pointer architecture, not a knowledge dump

Claude Code's persistent memory is a **three-layer system** designed to solve "context entropy" — the degradation of useful context over time. Evidence quality: **confirmed in both official Anthropic documentation and leaked source code**.

**Tier 1 — MEMORY.md (always loaded)**: A plain markdown file containing lightweight pointers of approximately **~150 characters per line**. It stores locations, not data. Loaded into every session at startup, capped at the first **200 lines or 25KB**, whichever comes first. Content beyond that threshold is silently truncated with a warning appended. Functions as a table of contents for the agent's knowledge.

**Tier 2 — Topic files (loaded on demand)**: Separate markdown files like `debugging.md`, `api-conventions.md`, `build-commands.md` containing actual project knowledge. These are never loaded at startup — Claude reads them using standard file tools when it determines the information is needed. The MEMORY.md index provides enough context for Claude to know which topic file to open. If a fact can be re-derived directly from the codebase, it is not stored.

**Tier 3 — Raw transcripts (grep-only archive)**: JSONL files logging session activity. Never loaded into active context. Only searched with targeted grep for specific identifiers.

A critical design principle is **"strict write discipline"**: the agent updates the index only after a confirmed successful file write. The agent is instructed to treat its own memory as a *"hint"* and verify against the actual codebase before acting. Cisco security research confirmed that in early versions, the first 200 lines of MEMORY.md were loaded directly into the system prompt (high authority), but after a memory poisoning vulnerability was discovered, Anthropic moved user memories out of the system prompt in v2.1.50.

**Directory structure** (confirmed):
```
~/.claude/projects/<project>/memory/
├── MEMORY.md              # Concise index, loaded every session
├── debugging.md           # Topic file
├── api-conventions.md     # Topic file
└── ...
```

The `<project>` path derives from the git repository, so all worktrees and subdirectories within the same repo share one memory directory. Relevance determination relies entirely on Claude's contextual judgment — there is no vector search or embedding-based retrieval in the native system.

**Memory creation** happens automatically (enabled by default since v2.1.59). Claude decides what's worth remembering based on whether information would be useful in a future conversation. It records build commands, test conventions, code style preferences, debugging insights, architecture notes, and user preferences. At session end, a fire-and-forget forked agent (`EXTRACT_MEMORIES` system) pulls durable insights from the conversation and writes them to persistent memory, with a manifest of existing memories pre-injected to avoid rediscovery.

## ECC's instinct-to-skill pipeline is a community project, not native Claude Code

A critical distinction: the "instinct-to-skill pipeline" is implemented in **ECC (Everything Claude Code)**, a community-built configuration framework by Affaan Mustafa — not in Claude Code's own source. ECC has approximately **100K GitHub stars** and works on top of Claude Code's hook infrastructure. The "112K stars" figure in the research brief actually refers to OpenCode (anomalyco/opencode), a different project. Evidence quality: **confirmed in ECC's public repository**.

**The v2 Continuous Learning system** achieves **100% observation reliability** by using Claude Code's `PreToolUse` and `PostToolUse` hooks rather than skills (which fire only 50-80% of the time based on Claude's judgment). Hooks fire deterministically — every tool call is observed.

The pipeline follows four stages:

1. **Capture**: Hooks capture every prompt and tool use. Project context is auto-detected from git remote. Observations are stored in `~/.claude/homunculus/projects/<project-hash>/observations.jsonl`.
2. **Pattern detection**: A background observer agent (running on the cheaper **Haiku model**) reads observations and detects user corrections, error resolutions, and repeated workflows. It makes a scope decision: project-specific or global.
3. **Instinct creation**: The observer creates atomic instincts with confidence scores ranging from **0.3** (tentative, suggested but not enforced) to **0.9** (near-certain, core behavior). Instincts are stored as markdown files with YAML frontmatter containing: `id`, `trigger`, `confidence`, `domain`, `source`, `scope`, `project_id`, and `project_name`.
4. **Evolution**: The `/evolve` command clusters related instincts into skills, commands, or agents. Auto-promotion from project to global scope triggers when the same instinct ID appears in **2+ projects** with average confidence **≥0.8**.

Confidence increases when patterns are repeatedly observed and users don't correct them. Confidence decreases when users explicitly correct, patterns go unobserved for extended periods, or contradicting evidence appears. Default decay rate is **0.05**.

The `/instinct-status` command shows learned instincts with confidence scores. `/instinct-export` and `/instinct-import` enable sharing across teams. The system represents a genuine instinct-to-skill promotion mechanism — but it is external infrastructure built by the community, not something found in Claude Code's leaked source.

## Decision logging exists across multiple subsystems

No single "trajectory storage" system exists in Claude Code, but decision logging is distributed across several confirmed mechanisms.

**The append-only message array** serves as primary state. The full agent state is reconstructible from message history, enabling persistence (save session), replay (debugging), and compression (context trimming). As one analyst noted: *"One append-only structure solves multiple problems."*

**KAIROS append-only daily logs** create an immutable audit trail of autonomous decisions and observations, stored in date-stamped files that cannot be self-erased.

**Telemetry signals** function as behavioral logging: a **frustration metric** using regex-based detection of user swearing (in `userPromptKeywords.ts`), a **"continue" counter** tracking how often users type "continue" mid-session as a proxy for agent stalls, and **denial tracking** recording when users refuse tool permissions.

**Session-end memory extraction** via `EXTRACT_MEMORIES` pulls durable insights after each query loop, writing to persistent memory with deduplication checks. The `/remember` skill reviews auto-extracted memories and proposes promotions across four layers: CLAUDE.md, CLAUDE.local.md, team memory, or auto-memory.

An Anthropic spokesperson confirmed to Axios that leaked feature flags include *"the ability for Claude to review what was done in its latest session to study for improvements in the future while transferring learnings across conversations."* Evidence quality: **confirmed as planned capability, not yet shipped**.

## Prompt evolution uses modular construction and A/B testing

The system prompt is not a monolithic string — it's built from **modular, cached sections** split by a `SYSTEM_PROMPT_DYNAMIC_BOUNDARY` marker. Evidence quality: **confirmed in code**.

- **Static sections** (tool definitions, core instructions) are cacheable across all organizations
- **Dynamic sections** (CLAUDE.md content, git status, current date) are user/session-specific
- A `DANGEROUS_uncachedSystemPromptSection()` function marks volatile sections that should break cache

This architecture allows modifications to dynamic content without invalidating the global prompt cache. A/B testing of prompt variants is confirmed: an internal comment at `src/constants/prompts.ts:527` reads *"research shows ~1.2% output token reduction vs qualitative 'be concise'."* The internal build uses hard numerical limits ("keep text between tool calls to ≤25 words") rather than qualitative instructions.

**GrowthBook feature flags** (44 named flags controlling 108 gated modules) enable remote experimentation. Flags prefixed with `tengu_` (Claude Code's internal project codename) can be flipped for specific users, regions, or percentages without pushing updates. The remote settings endpoint is polled every 60 minutes. Anthropic originally used Statsig before switching to GrowthBook after OpenAI acquired Statsig in September 2025.

There is **no evidence** of autonomous prompt self-modification. The autoDream system modifies memory files that feed into context, but the core system prompt itself is not self-modifying.

## Saturation detection relies on circuit breakers and regression tracking

The most direct saturation mechanism is the **AutoCompact circuit breaker**. An internal comment citing BigQuery data from March 10, 2026 reveals: *"1,279 sessions had 50+ consecutive failures (up to 3,272) in a single session, wasting ~250K API calls/day globally."* The fix: `MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES = 3` — stop retrying after three failures. Evidence quality: **confirmed in code** with the exact BigQuery date reference.

Claude Code uses a **five-layer context compression strategy** to prevent context saturation:

1. **Snip**: Prunes older messages for quick headroom (fast, lossy)
2. **MicroCompact**: Edits cached tool outputs locally with zero API calls; large file reads saved to disk with model seeing summary plus reference
3. **AutoCompact**: Fires near context window ceiling, reserves **13,000-token buffer**, generates up to **20,000-token** structured summary, with the circuit breaker after 3 failures
4. **Full Compact**: Compresses entire conversation, re-injects recently accessed files (capped at **5,000 tokens per file**), active plans, and relevant skills; working budget resets to **50,000 tokens**
5. **Oldest-message truncation**: Final fallback

Internal benchmarks reveal **active regression detection**: Capybara (Claude 4.6 variant) v8 showed a **29-30% false claims rate** — a regression from v4's 16.7%. An "assertiveness counterweight" was designed to prevent the model from being too aggressive in refactors. These metrics suggest Anthropic tracks performance plateaus at the model level, though no automated plateau-detection system was found in the agent harness code.

## Conclusion: patterns worth implementing in Keystone

The Claude Code architecture reveals five patterns directly applicable to building self-improving multi-agent systems:

**The pointer-not-payload memory pattern** is the most transferable insight. MEMORY.md stores locations, not data — keeping the always-loaded context tiny while enabling access to deep knowledge through on-demand retrieval. The 200-line/25KB cap and strict write discipline (update index only after confirmed file write) prevent memory corruption.

**The forked-subagent consolidation pattern** (autoDream) demonstrates how to run maintenance routines without corrupting active reasoning. The three-gate trigger (time + sessions + lock), four-phase consolidation cycle, and read-only sandbox for the consolidation agent are production-ready architectural choices. The key implementation detail: converting relative dates to absolute during consolidation prevents temporal drift across sessions.

**The tick-driven daemon pattern** (KAIROS) shows how to build proactive agents that balance responsiveness against cost. The `setTimeout(0)` yield, 15-second blocking budget with auto-backgrounding, and explicit sleep/wake cost modeling are concrete engineering solutions to the "always-on agent" problem.

**The hook-based observation pattern** (from ECC, not Claude Code itself) demonstrates how to achieve 100% observation reliability. Deterministic hooks on every tool call feed a background observer running a cheap model (Haiku), which creates atomic instincts with confidence scores that cluster into permanent skills. This is the closest implementation to a genuine instinct-to-skill promotion pipeline in the current ecosystem.

**The circuit-breaker saturation pattern** is simple but effective: track consecutive failures, stop retrying after a threshold, and use tiered compression strategies before reaching hard limits. The BigQuery-driven approach of measuring actual failure rates (250K wasted API calls/day) to calibrate thresholds is worth replicating.

What the leak does *not* reveal: autonomous prompt self-modification, explicit plateau detection beyond circuit breakers, or a named "trajectory storage" system. The architecture relies on the LLM's own judgment for relevance determination rather than vector search — a choice that trades retrieval precision for architectural simplicity. For Keystone, the leaked patterns provide a production-validated foundation, but the instinct-to-skill pipeline and saturation detection will need to be designed beyond what Claude Code currently implements.