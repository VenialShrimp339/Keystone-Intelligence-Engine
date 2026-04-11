# Claude Code's leaked architecture reveals a five-layer context engine

On March 31, 2026, a 59.8 MB source map file shipped inside Claude Code npm package v2.1.88 exposed **512,000 lines of TypeScript across 1,906 files** — the complete client-side agent harness. The leak, discovered by security researcher Chaofan Shou within hours of publication, revealed that Claude Code is not a chat wrapper but a deeply engineered operating system for AI agents, built around a sophisticated multi-tier context management pipeline, a persistent memory architecture with background consolidation, and at least 44 unreleased features gated behind compile-time flags. The architectural patterns disclosed — particularly the compaction pipeline, the autoDream memory consolidation system, and the KAIROS autonomous daemon — represent the most detailed public documentation of production-grade agent context management ever exposed.

---

## A packaging error repeated thirteen months later

The root cause was a known Bun runtime bug (oven-sh/bun#28001, filed March 11, 2026) that generates source maps in production builds by default. The `.npmignore` file lacked `*.map` exclusion. **This was the second time Anthropic shipped source maps in Claude Code's npm package** — the first occurred on Claude Code's launch day, February 24, 2025, when developer Dave Shoemaker found an 18-million-character inline source map. Anthropic pulled that within two hours. Thirteen months later, same vector, same outcome.

Anthropic confirmed the leak as "a release packaging issue caused by human error, not a security breach." Boris Cherny, head of Claude Code, stated that no one was fired. The leaked codebase accumulated **84,000+ GitHub stars and 82,000+ forks** before DMCA takedowns removed 8,000+ repositories (some unintentionally). Developer Sigrid Jin built a clean-room Python rewrite ("claw-code") overnight that hit 100,000+ stars within days. Decentralized mirrors on IPFS ensured the code could not be fully suppressed.

Primary technical analyses came from alex000kim.com (first-day HN submission with 406 comments), sabrina.dev (comprehensive security analysis with specific file/line references), ccleaks.com (full reverse-engineering), ComeOnOliver's GitHub repository (17-section architectural breakdown), and WaveSpeedAI's multi-part blog series. These sources cite specific TypeScript file paths, line numbers, and code snippets, confirming direct access to the leaked source.

---

## The five-strategy compaction pipeline from micro-trim to full compression

Claude Code's context management operates as a four-stage pipeline defined in `query.ts` (lines 307–1,728) that executes before every API call, escalating from lightweight deterministic cleanup to full LLM-powered summarization only when cheaper strategies prove insufficient. The architecture solves what analysts called "the hardest problem in agent development": sustaining coherent long-running sessions within fixed context windows.

### Stage 1 — Tool result budgeting

Before any compaction logic fires, the system applies per-message budgets to tool outputs. Tools declaring `maxResultSizeChars: Infinity` — including the Read tool — are exempted from budgeting entirely. Once the model reads a file, its content is tracked via a **`seenIds` mechanism** that locks the keep/discard decision for the session's duration. This tracking is what enables intelligent re-injection after compaction: the system knows exactly which files the model has consumed and can selectively restore the most relevant ones.

### Stage 2 — MicroCompact (zero API cost)

MicroCompact is the lightest intervention. It runs before every API call with no LLM involvement. The system maintains a per-session `CachedMCState` tracking every registered tool result's insertion order and deletion status. When tool result count exceeds a configurable `triggerThreshold`, the system identifies the oldest results beyond a `keepRecent` count (retaining the **5 most recent**) and replaces older ones with `[Old tool result content cleared]`.

The critical implementation detail: these edits are **not applied to the local message array**. They are queued as `cache_edits` and applied at the API transport layer via `cache_reference` annotations. This surgical approach preserves the warm prompt cache — a cache miss would cost far more than the context saved. Only tools in the `COMPACTABLE_TOOLS` set are eligible (defined in `services/compact/microCompact.ts`, lines 41–51). **MCP tools, Agent tools, and custom tools are excluded** — their results persist until autocompact fires. MicroCompact is restricted to the main query thread only via an `isMainThreadSource` check; forked agents cannot register tool results in the shared state, which would corrupt the main thread's cache edit sequence.

### Stage 3 — Session memory compact (experimental, feature-flagged)

An intermediate tier operating at the API level with server-side strategies. It handles thinking block clearing and tool result pruning based on token thresholds. The pruning algorithm (`calculateMessagesToKeepIndex`) preserves a minimum of **20 messages with text blocks** and a minimum of **20,000 tokens**, bounded by a 100K token cap. This tier relies on already-extracted session memory rather than re-summarizing the entire conversation.

### Stage 4 — AutoCompact (the 93.5% trigger)

When conversation context approaches the window ceiling, AutoCompact fires a full LLM summarization call. The trigger threshold is computed by `getAutoCompactThreshold()` as **`effectiveContextWindowSize - 13,000`**. For a 200K-token model, this means roughly **187,000 tokens — 93.5% utilization**. The system reserves the 13K-token buffer to ensure enough room for the summary generation call itself.

AutoCompact generates a **structured 9-section summary** of up to 20,000 tokens covering: original intent, technical concepts, files touched, errors and fixes, all user messages (excluding tool results), pending tasks, current work state, key decisions, and next steps. The compaction prompt uses chain-of-thought reasoning inside `<analysis>` tags, which `formatCompactSummary()` strips before injection.

A damning internal comment in the source, dated March 10, 2026, revealed that **1,279 sessions had experienced 50+ consecutive compaction failures** — up to 3,272 retries in a single session — **wasting approximately 250,000 API calls per day globally**. The fix, implemented just 21 days before the leak: a circuit breaker setting `MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES = 3`, after which compaction is disabled for the remainder of the session.

### Stage 5 — Full Compact (nuclear option)

Full compact compresses the entire conversation and then methodically rebuilds the session. The post-compaction reconstruction sequence injects: a boundary marker with pre-compaction metadata, the formatted summary (flagged with `isCompactSummary: true`), the **5 most recently read files** (capped at 5,000 tokens per file, 50,000 tokens total), re-injected skills sorted by recency, re-announced tool definitions, re-run session hooks, and restored CLAUDE.md content. The working budget resets to **50,000 tokens**, and old pre-compaction messages are never deleted from the JSONL transcript — new messages are appended after a compact boundary.

The system also supports **partial compaction** via the `/compact` slash command: `partialCompactConversation` accepts a `pivotIndex` and a `direction` ('from' or 'up_to'), allowing selective summarization of either older or newer portions. Users can provide focus instructions: `/compact focus on the API changes`.

---

## Re-injection uses file tracking, not relevance scoring

The post-compaction re-injection mechanism is deterministic rather than model-scored. The `seenIds` tracking system records every file the model has read during the session. After compaction, the system selects the **5 most recently accessed files** and re-injects their contents, each capped at 5,000 tokens. Active plans and relevant skill schemas are also restored. CLAUDE.md files are reloaded from disk, and `runPostCompactCleanup` resets all cached state — CLAUDE.md caches, session message caches, speculative bash permission checks, classifier approvals, beta tracing state, and microcompact state.

This approach trades sophistication for reliability. There is no learned relevance scoring model deciding what survives — recency serves as the heuristic proxy for relevance. The compaction prompt itself instructs the summarizer to "pay special attention to specific user feedback" and preserve "all user messages that are not tool results," ensuring that user directives have the highest survival probability through compression cycles.

A significant security concern identified by multiple analysts: instruction-like content embedded in repository files (such as a poisoned CLAUDE.md) can survive compaction, get laundered through the summarization step, and emerge in the compressed context as what the model treats as genuine user directives. The model is not jailbroken — it cooperatively follows what it believes are user instructions baked into the summary. AI security firm Straiker warned that attackers can now "study and fuzz exactly how data flows through Claude Code's four-stage context management pipeline and craft payloads designed to survive compaction, effectively persisting a backdoor across an arbitrarily long session."

---

## MEMORY.md is an index, not a knowledge dump

Claude Code's persistent memory operates through a carefully layered architecture centered on a lightweight index file. The memory directory lives at `~/.claude/projects/<project>/memory/`, where `<project>` is derived from the git repository so all worktrees share one memory space. The directory structure follows this pattern:

- **MEMORY.md** — A concise index file where each entry is a single line under ~150 characters pointing to a topic file. Only the **first 200 lines or ~25KB** are loaded at conversation startup.
- **Topic files** (e.g., `debugging.md`, `api-conventions.md`, `build-commands.md`) — Detailed knowledge loaded on demand when relevant.
- **Session transcripts** — Large JSONL files that are never loaded wholesale, only searched via targeted grep.

The auto-memory system captures build commands, debugging insights, architecture decisions, code style preferences, workflow habits, user corrections, and important tool/framework choices. Claude decides what's worth remembering based on whether information would be useful in a future conversation — it does not save something every session.

The CLAUDE.md hierarchy provides five levels of instruction, loaded from lowest to highest priority: system-wide (`/etc/claude-code/CLAUDE.md`), user-global (`~/.claude/CLAUDE.md`), project-specific (`/project-root/CLAUDE.md`), personal project notes (`CLAUDE.local.md`, gitignored), and subdirectory-level files loaded on-demand when Claude accesses those paths. Critically, **CLAUDE.md content is not placed in the system prompt**. It is injected as a `<system-reminder>` XML tag attached to conversation messages, preserving the globally shared prompt cache that makes Claude Code economically viable across millions of users.

The system prompt itself is modular, assembled from **110+ separate prompt strings** through a pipeline that produces a cacheable static prefix (identity, permissions, tool preferences, style rules) and a dynamic per-session suffix (agents, skills, memory, environment, MCP instructions), split by a `__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__` marker. The static prefix uses a 1-hour TTL cache; the dynamic suffix gets a 5-minute TTL. Total baseline overhead before any conversation begins is **~27,000–31,000 tokens** (roughly 15% of a 200K window), with tool definitions alone consuming **14,000–17,600 tokens** — the single largest component. Heavy MCP server usage can push baseline overhead past 40%.

---

## KAIROS and autoDream: the daemon and its sleep cycle

The most architecturally significant unreleased feature is **KAIROS** (named after the Greek concept of "the opportune moment"), referenced over **150 times** in the codebase and gated behind the `feature('KAIROS')` compile-time flag and `tengu_kairos` server-side flag. KAIROS transforms Claude Code from a reactive tool into a **persistent autonomous daemon** — running 24/7 as a background process without user input, receiving periodic `<tick>` messages with current local time context.

On each tick, KAIROS makes a binary decision: act proactively or sleep. Every proactive action operates under a strict **15-second blocking budget** — actions exceeding this are deferred. This creates a natural hierarchy where quick operations (file scanning, notifications, PR monitoring) run automatically while complex operations (refactors, multi-file edits) are queued for user permission. The system is terminal-focus-aware: when the user is away, KAIROS maximizes independent decision-making, pausing only for irreversible actions; when the user is present, it increases collaboration and asks before major commits. KAIROS has exclusive tools unavailable to regular Claude Code: `SleepTool`, `SendUserFile`, `PushNotification`, and `SubscribePR` for real-time pull request monitoring.

**AutoDream** is KAIROS's "sleep cycle" — a background memory consolidation system that fires as a forked subagent. The leaked system prompt states directly: *"You are performing a dream — a reflective pass over your memory files. Synthesize what you've learned recently into durable, well-organized memories so that future sessions can orient quickly."* AutoDream is gated behind server-side flag `tengu_onyx_plover` with a manual trigger available via the `/dream` slash command.

### Triple gate activation

AutoDream requires three simultaneous conditions: a **time gate** (24 hours since last consolidation), a **session gate** (5 sessions accumulated since last dream), and a **lock gate** (exclusive PID lock file acquisition). If KAIROS mode is active, AutoDream skips — KAIROS uses its own disk-skill dream. A scan throttle of 10 minutes prevents repeated scanning when the time gate passes but the session gate does not.

### The four-phase consolidation algorithm

**Phase 1 — Orient**: Inventories the memory directory, reads MEMORY.md, and skims existing topic files to avoid creating duplicates.

**Phase 2 — Gather signal**: Collects new information from three sources in priority order: daily append-only logs, existing memories that have drifted from the current codebase, and targeted transcript searches via grep on JSONL session files. The prompt explicitly constrains: *"grep the JSONL transcripts for narrow terms… Don't exhaustively read transcripts. Look only for things you already suspect matter."* It searches for user corrections, explicit save requests, recurring themes, and important architectural decisions.

**Phase 3 — Consolidate**: Merges new signals into existing topic files rather than creating near-duplicates. Converts relative dates ("yesterday") to absolute dates. **Deletes contradicted facts at the source** — if the project switched from Express to Fastify, the old "API uses Express" entry is removed. Merges overlapping entries across sessions into single clean records.

**Phase 4 — Prune and index**: Updates MEMORY.md to stay under 200 lines and ~25KB. Removes pointers to stale or superseded memories. Demotes verbose entries by keeping the gist in the index and moving detail to topic files. Resolves contradictions between disagreeing files. Files that need no changes are left untouched.

The dream sub-agent receives **bash read-only access** — it can inspect code but never modify it. Write access is limited exclusively to memory files. Observed performance in testing: approximately **8–10 minutes to consolidate 913 sessions**. On failure, the system rolls back the consolidation lock's mtime so the time gate passes again on the next attempt, with the scan throttle serving as natural backoff.

---

## Implications for agent architecture design

The leaked architecture validates several design principles directly relevant to production agent systems. First, **compaction must be a graduated pipeline, not a single strategy** — the five-tier escalation from zero-cost cache edits to full LLM summarization reflects hard-won engineering around the tension between context preservation and token economics. The 250K wasted API calls/day bug demonstrates the cost of getting failure handling wrong at scale.

Second, **persistent memory requires active maintenance, not passive accumulation**. The autoDream pattern — with its explicit contradiction removal, date normalization, and pruning constraints — treats memory as a living document that degrades without curation. The "self-healing memory" principle, where the agent treats its own memories as hints requiring verification against the actual codebase, prevents hallucinations from stale entries.

Third, **system prompt economics drive architectural decisions**. The `__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__` cache split, the decision to place CLAUDE.md in messages rather than the system prompt, and the globally shared static prefix all reflect that prompt caching economics constrain agent design as much as context window size does. With tool definitions alone consuming 14–17.6K tokens, every additional byte in the system prompt has a measurable cost at scale.

For the Keystone Intelligence Engine specifically, the KAIROS tick-based decision loop maps directly to agent session management for long-running investigations. The autoDream four-phase consolidation — Orient, Gather, Consolidate, Prune — provides a battle-tested template for the META-layer Observation Library's skill consolidation workflow. The compaction pipeline's `seenIds` tracking and recency-based re-injection offer a practical alternative to expensive relevance-scoring models for managing agent context across extended sessions. And the security finding that instructions can survive compaction and become "laundered" into post-summary directives is a critical consideration for any system processing untrusted inputs through context compression.