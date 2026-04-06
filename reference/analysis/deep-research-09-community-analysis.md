# The Claude Code leak: 512K lines that rewrote the agent playbook

**Anthropic's accidental exposure of Claude Code's entire TypeScript source on March 31, 2026 revealed the most sophisticated production agent harness ever built — and the community's response was equally unprecedented.** Within 24 hours, the codebase spawned the fastest-growing GitHub repo in history (claw-code, 100K+ stars), exposed 44 unreleased features behind compile-time flags, and gave every competitor a free masterclass in production agent architecture. The leak's significance extends far beyond embarrassment: it effectively standardized design patterns for multi-agent systems and revealed that Anthropic's orchestration strategy relies on prompts, not frameworks — validating the "no LangChain" philosophy and directly informing how production systems like the Keystone Intelligence Engine should be built.

The incident began when a misconfigured `.npmignore` shipped a 59.8 MB source map file (`cli.js.map`) in Claude Code v2.1.88 to npm. Security researcher Chaofan Shou discovered it and posted on X (34M views). Anthropic confirmed "a release packaging issue caused by human error" — their second leak in five days, following a CMS misconfiguration that exposed internal assets about the unreleased Mythos model.

---

## The architecture: an agent harness, not a wrapper

The community's most important consensus finding is that **Claude Code is not a thin LLM wrapper — it is an agent operating system**. At 512,000 lines across ~1,906 TypeScript files, with 41 tools, 101 command modules, and 130+ UI components, it dwarfs what most practitioners expected. The shareAI-lab educational repo (48.3K stars) distilled the core formula:

```
Claude Code = one agent loop + tools + on-demand skill loading + context compression
            + subagent spawning + task system with dependency graph
            + team coordination with async mailboxes + worktree isolation
            + permission governance
```

The technology stack is TypeScript compiled with **Bun** (which enables compile-time feature flags via `bun:bundle`), **React + Ink** for terminal rendering, the `@anthropic-ai/sdk` for API access, `@modelcontextprotocol/sdk` for MCP, **Zod v4** for validation, and a Zustand-style state store. The three largest files each rival entire open-source projects: **`QueryEngine.ts` at 46,000 lines** (the heart of the system — message management, streaming, auto-compaction, retry logic, token tracking, and tool orchestration), `Tool.ts` at 29,000 lines, and `commands.ts` at 25,000 lines.

**The core agent loop** is deceptively simple: user input enters a message array, goes to the Claude API, and if the response's `stop_reason` is `tool_use`, the system executes the requested tools, appends results, and loops back. Everything complex — orchestration, memory, compression, security — hangs off this loop. The entry point (`main.tsx`, ~4,683 lines) bootstraps feature flags, authentication, GrowthBook A/B testing, tool registration, MCP setup, and the REPL.

**Mapping to Keystone**: The agent loop pattern directly validates the L1 Parallel Research Agent design. Claude Code proves that a single tight loop with tool dispatch is sufficient — no framework middleware needed. The `AgentTool` makes sub-agents first-class tool calls, meaning your L0→L1 spawning can be implemented as just another tool invocation rather than a separate orchestration layer.

---

## Multi-agent orchestration runs on prompts, not code

The finding that generated the most HN commentary was that **Claude Code's multi-agent coordinator is prompt-driven, not framework-driven**. One commenter crystallized it: "The whole orchestration algorithm is a prompt, not code. So much for LangChain and LangGraph! If Anthropic themselves aren't using it, what's the big deal about langchain." The coordinator system prompt includes instructions like "Do not rubber-stamp weak work" and "Never hand off understanding to another worker" — behavioral constraints enforced entirely through natural language.

The multi-agent system uses what the source calls a **"swarm" architecture**, gated behind the `tengu_amber_flint` feature flag. It supports four spawn modes: **default** (in-process, shared conversation), **fork** (child process, fresh messages but shared file cache), **worktree** (isolated git worktree + fork), and **remote** (bridge to container). The **mailbox pattern** coordinates agents: workers cannot independently approve high-risk operations — they send requests to the coordinator's mailbox and wait. An atomic claim mechanism prevents duplicate handling.

Sebastian Raschka highlighted a critical efficiency insight: **KV cache fork-join makes parallelism "basically free."** Forked subagents inherit the parent's KV cache state, so spawning 5 agents costs barely more than 1 in terms of context setup. This is the single most significant architectural pattern for multi-agent systems discovered in the leak.

**Mapping to Keystone**: This directly validates using PydanticAI + Temporal for orchestration rather than LangChain/LangGraph. Your L1.5 Deliberation layer (independent parallel analysis) maps to Claude Code's fork mode with isolated message histories. The mailbox pattern is worth adopting for your L4 Evaluator — workers submit results to a coordinator inbox rather than directly influencing each other. The worktree isolation mode maps to your filesystem isolation requirement for L1 agents. However, the KV cache fork-join optimization requires API-level support and may not be available with all providers.

---

## Three-layer memory and three-layer compression

The leaked memory architecture is one of the most innovative patterns discovered. It operates across three tiers:

**Tier 1 (MEMORY.md)** is always loaded into context — but crucially, it stores only pointers (~150 chars per line), not data. It is a lightweight index that tells the agent where to look. **Tier 2 (Topic Files)** contains actual project knowledge in distributed Markdown files, fetched on demand. **Tier 3 (JSON Transcripts)** stores raw session logs that are never fully loaded — only searched via grep for specific identifiers. The agent treats its own memory as a **"hint"** and must verify facts against the actual codebase before acting — a design the WaveSpeedAI analysis called "self-healing memory."

Context compression uses three escalating strategies. **MicroCompact** edits cached content locally with zero API calls, trimming old tool outputs. **AutoCompact** fires when approaching the context window ceiling, reserving a **13,000-token buffer** and generating structured summaries up to **20,000 tokens**, with a circuit breaker after 3 consecutive failures. **Full Compact** compresses the entire conversation, re-injects recently accessed files (capped at 5,000 tokens each), adds active plans and skill schemas, and resets the working budget to **50,000 tokens**. A comment in `autoCompact.ts` revealed that before the circuit breaker fix, a bug was wasting approximately **250,000 API calls per day** globally across sessions with 50+ consecutive compression failures.

The `autoDream` feature (gated, unreleased) runs as a forked sub-agent during idle periods to consolidate memory: merging observations across sessions, removing logical contradictions, converting vague insights into absolute facts, with read-only bash access. It runs in a separate process to prevent corrupting the main agent's reasoning.

**Mapping to Keystone**: The three-tier memory maps directly to your CitationProcessor's needs. Tier 1 (index) = your cross-agent dedup index. Tier 2 (topic files) = your corroboration scoring database. Tier 3 (transcripts) = raw research output from L1 agents. The "memory as hint, verify before acting" principle should be adopted for your L4 Evaluator's citation gate — never trust cached claims, always re-verify against source. The autoDream pattern could inform an offline consolidation step between research rounds.

---

## The 44 gated features reveal Anthropic's roadmap

The New Stack's definitive article documented **44 compile-time feature flags** plus **80+ GrowthBook runtime flags** (prefixed `tengu_*`). The compile-time flags use Bun's dead code elimination — when a flag is off, the model literally cannot see or call the gated functionality. The most significant unreleased features, grouped by relevance:

**Autonomous operation**: **KAIROS** (referenced 150+ times) is a persistent daemon mode receiving periodic `<tick>` prompts, maintaining append-only daily logs, with GitHub webhook subscriptions and push notifications. **autoDream** consolidates memory during idle time. **DAEMON** enables background sessions via tmux that survive terminal closure. **PROACTIVE** allows the agent to act without explicit user prompts.

**Multi-agent orchestration**: **COORDINATOR_MODE** implements structured research-synthesis-implementation phases across parallel workers. **FORK_SUBAGENT** enables isolated subagent spawning. **ULTRAPLAN** offloads complex planning to a cloud container running **Opus 4.6** for up to 30 minutes, with a "teleport to terminal" feature that archives the remote session and begins local execution. **UDS_INBOX** provides Unix Domain Socket inter-session messaging with zero network overhead.

**Context and memory**: **LODESTONE** adds cross-session persistent memory separate from CLAUDE.md. **HISTORY_SNIP** optimizes context windows. **TRANSCRIPT_CLASSIFIER** auto-analyzes conversation records. **ABLATION_BASELINE** enables evaluation baseline testing for memory approaches.

**Tools and MCP**: **WEB_BROWSER_TOOL** adds full Playwright browser control. **MCP_SKILLS** integrates the MCP skill system. **WORKFLOW_SCRIPTS** enables automation scripting.

**Security**: **ANTI_DISTILLATION_CC** injects fake tool definitions to poison competitor training data. **NATIVE_CLIENT_ATTESTATION** uses Zig-compiled hashes in the Bun binary to cryptographically prove requests originate from genuine Claude Code binaries — effectively DRM for API calls.

**Mapping to Keystone**: COORDINATOR_MODE's research-synthesis-implementation phases map almost exactly to your L0→L1→L1.5→L4 pipeline. ULTRAPLAN's remote planning with extended think time could inform your L0 Specification Engine — offloading complex spec generation to a more powerful model. UDS_INBOX's zero-overhead inter-session messaging is worth investigating for your agent communication layer. ABLATION_BASELINE suggests Anthropic is already systematically testing memory approaches — your L4 Evaluator should include similar ablation capabilities.

---

## Security findings expose structural challenges in agent systems

### Anti-distillation: clever but fragile

Two anti-distillation mechanisms were found. The primary one (`ANTI_DISTILLATION_CC` in `claude.ts`, lines 301-313) sends `anti_distillation: ['fake_tools']` in API requests, instructing the server to inject decoy tool definitions into the system prompt to poison competitor training data. The secondary mechanism (`tengu_slate_prism` in `betas.ts`) summarizes assistant reasoning between tool calls with cryptographic signatures, so anyone intercepting traffic captures only summaries. Alex Kim estimated both could be bypassed "in about an hour" — the real protection is legal, not technical.

### The 50-subcommand vulnerability

The most critical security finding came from Adversa AI: **commands with more than 50 subcommands bypass all security checks**. In `bashPermissions.ts` (lines 2162-2178), security analysis is capped at 50 subcommands for performance reasons — anything above falls back to a generic "ask" prompt, skipping deny rules, validators, and injection detection. The fix (a tree-sitter parser checking deny rules first regardless of count) was already built in the codebase but never deployed. A malicious `CLAUDE.md` file could instruct the AI to generate a 50+ subcommand pipeline that looks legitimate, enabling exfiltration of SSH keys, AWS credentials, and tokens.

### Undercover mode: the feature that leaked itself

The `undercover.ts` file (~90 lines) injects the system prompt instruction "Do not blow your cover," strips all `Co-Authored-By` attribution for external repos, and activates for Anthropic employees. Critically, there is **no force-off switch** — only a force-on via `CLAUDE_CODE_UNDERCOVER=1`. The mode also leaked 22 private Anthropic repository names from its allowlist. As one analyst noted: "The mode designed to prevent leaking internal info leaked internal info."

### Malware campaigns exploited the leak within hours

Threat actors moved fast. Typosquatting npm packages (`audio-capture-napi`, `color-diff-napi`, etc.) appeared within 24 hours, targeting developers trying to compile the leaked code. Zscaler ThreatLabz found trojanized GitHub repos distributing **Vidar Stealer v18.7** and **GhostSocks** malware disguised as leaked source. A concurrent (unrelated) **axios supply chain attack** injected a RAT into npm's axios package during a 3-hour window on the same day, compounding the chaos.

**Mapping to Keystone**: The 50-subcommand vulnerability demonstrates that **performance optimization in security enforcement creates exploitable gaps** — a direct warning for your L1 agents' tool execution sandboxing. CLAUDE.md as a trust boundary (context poisoning) is the most relevant attack vector for your system: any tool that reads project configuration files as trusted instructions is vulnerable. Your MCP gateway should treat all external configuration as untrusted input. The parser differential vulnerability (three bash parsers with different edge-case behavior) argues for using a single canonical parser in your tool execution layer.

---

## Community rewrites and what they changed

### claw-code: 100K stars in 24 hours

Created by Sigrid Jin (Columbia student, previously profiled by WSJ for consuming 25 billion Claude Code tokens), **claw-code** hit 100K GitHub stars faster than any repo in history. It is a clean-room rewrite in **Rust (72.9%) + Python (27.1%)**, built overnight using OpenAI's Codex with xAI/Grok providing credits. Key architectural decisions: Python handles orchestration and LLM integration; Rust handles performance-critical paths. It drops React Ink entirely, eliminates the npm dependency chain, and is **model-agnostic** (works with Claude, GPT, Gemini, local models via Ollama). A unique `parity_audit.py` explicitly tracks implementation gaps versus the original.

### nano-claude-code: research-first with novel features

SafeRL-Lab's **nano-claude-code** grew from 900 to 11,600 lines in 5 days, adding features Claude Code doesn't have: **task dependency graphs** with `blocks`/`blocked_by` edges for structured multi-step planning, offline voice input via faster-whisper, Jupyter notebook editing without a kernel, and diagnostics chaining (pyright → mypy → flake8 → py_compile) with zero config. The agent loop uses Python generators yielding typed events (`TextChunk`, `ToolStart`, `ToolEnd`, `TurnDone`), which is cleaner than the original's streaming approach. It supports 20+ model providers.

### claurst: legally defensive spec-driven Rust

Kuberwastaken's **claurst** (4,900 stars) uses a two-phase clean-room process citing Phoenix Technologies v. IBM (1984): Phase 1 generates behavioral specifications from the leaked source, Phase 2 implements from specs alone without referencing original code. The Rust binary starts in <100ms with 50MB peak memory versus 200MB+ for Node.js ports.

### claw-code-agent: zero-dependency Python for local models

HarnessLab's **claw-code-agent** targets local open-source models exclusively, with zero external dependencies and a manifest-based plugin runtime. It includes a nested agent lineage tracker via `agent_manager.py` for managing hierarchical agent relationships.

Every rewrite made the same four changes: dropped React Ink, eliminated npm, added model agnosticism, and made tool/provider registration pluggable. Every rewrite kept the same core patterns: the agent loop, tool dispatch table, context compression, permission governance, and CLAUDE.md discovery.

---

## Derivative projects adopted the mailbox and swarm patterns

**Ruflo** (formerly Claude Flow, by ruvnet) is the most substantial derivative: an enterprise AI agent orchestration platform with 100+ specialized agents across 8 categories, 313 MCP tools across 31 modules, and swarm topologies (hierarchical, mesh, pipeline). Its v3.5 incorporated patterns visible in the leaked architecture: hierarchical agent spawning with capability-based security, filesystem-based inter-agent communication (mirroring Claude Code's mailbox system), memory consolidation across sessions (similar to autoDream), and MCP as primary tool interface. It claims an **84.8% SWE-Bench solve rate** and uses WASM kernels written in Rust for its policy engine.

**Multiclaude** (by dlorenc) is a Go-based multi-agent orchestrator supporting "singleplayer" (auto-merge PRs) and "multiplayer" (team review) modes with a supervisor agent. **Shipyard.build** is not a derivative but rather a DevOps ephemeral environment platform that publishes educational content about Claude Code multi-agent patterns, including articles on Agent Teams, the Ralph Loop (iteration pattern), and cloud-hosted agent runners.

Community documentation sites emerged rapidly: **ccunpacked.dev** for visual code exploration, **ccleaks.com** for feature documentation, and **Claude Code Unleashed** (ccu.galdoron.com) cataloging all 27 API beta flags, 80 feature flags, 73 slash commands, 118 settings, 280 environment variables, and 11 hidden systems.

---

## What practitioners found most significant

The community reached several strong consensus positions. **Architecture was admired; execution quality was criticized.** The three-layer memory, tool isolation with per-tool permission gating, and prompt-driven orchestration were praised. But zero test coverage on 64K+ lines of production code, a 3,167-line single function in `print.ts` with 12 levels of nesting, and the 250K wasted API calls shipped knowingly drew sharp criticism. As the ninetwothree.co analysis put it: "If '100% AI-written' is the new quality standard from the company pulling our industry forward, I'm not sure I want to go where the industry is going."

**Feature flags were seen as more damaging than the source code itself.** HN user saadn92 captured the consensus: "The feature flag names alone are more revealing than the code. KAIROS, the anti-distillation flags, model codenames — those are product strategy decisions that competitors can now plan around. You can refactor code in a week. You can't un-leak a roadmap."

**The "prompt, not framework" finding was the most practically significant for builders.** It validates building orchestration with lightweight custom code and natural language instructions rather than heavyweight frameworks. Layer5's analysis summarized: "Multi-agent orchestration fits in a prompt rather than a framework, which makes LangChain and LangGraph look like solutions in search of a problem."

Internal model codenames were also revealed: **Capybara** = Claude 4.6 (with internal benchmarks showing v8 has a 29-30% false-claim rate, regressed from 16.7% in v4), **Fennec** = Opus 4.6, **Numbat** = unreleased next model. References to Opus 4.7 and Sonnet 4.8 appeared in the codebase.

---

## Actionable patterns for the Keystone Intelligence Engine

Synthesizing across all findings, these are the patterns from the leak most directly applicable to the Keystone build:

**L0 Specification Engine**: Adopt the ULTRAPLAN pattern — offload complex planning to a more powerful model with extended think time. Claude Code's approach of using Opus 4.6 in cloud containers for up to 30 minutes of dedicated planning directly maps to your spec generation step.

**L1 Parallel Research Agents**: Use the fork spawn mode with inherited KV cache for near-free parallelism. Implement filesystem isolation via worktrees. Limit each agent to 3-5 tools as you planned — Claude Code's 41 tools are available system-wide but most tasks use only a handful. The `AgentTool` pattern (sub-agents as tool calls, no special framework) is the validated approach.

**CitationProcessor**: Implement the three-tier memory architecture. Your dedup index = MEMORY.md (always loaded, pointers only). Your corroboration database = Topic Files (on-demand). Raw research output = Transcripts (grep-searchable, never bulk-loaded). Apply "memory as hint" — always re-verify cached claims against sources.

**L1.5 Deliberation**: The fork mode with isolated message histories but shared file cache is exactly your "independent parallel analysis, NOT debate" requirement. The mailbox pattern ensures deliberation agents cannot influence each other — they submit to a coordinator inbox.

**L4 Evaluator**: Adopt the coordinator prompt pattern: "Do not rubber-stamp weak work. You must understand findings before directing follow-up work." The TRANSCRIPT_CLASSIFIER feature flag suggests Anthropic is building ML-based auto-approval — your 5-layer evaluation stack is more rigorous. Include ablation testing (ABLATION_BASELINE flag) for systematic evaluation of your scoring approach.

**MCP Gateway**: Claude Code proves MCP-native architecture works at scale — even Computer Use (codenamed "Chicago") runs as an MCP server, not special-cased. This validates your MCP gateway approach. But treat all external MCP configurations as untrusted input based on the CLAUDE.md context poisoning vulnerability.

**What to avoid**: The 50-subcommand security bypass demonstrates that performance optimization in security enforcement creates exploitable gaps. Use a single canonical parser for all tool execution validation. The three-parser differential vulnerability is a direct cautionary tale. And implement the circuit breaker pattern for any retry logic — Claude Code's 250K wasted API calls came from not having one until after the damage was documented.

The leak's ultimate lesson is architectural: **the agent harness should be thin, the model should be thick.** Claude Code's sophistication is in context management, tool isolation, and permission governance — not in complex orchestration logic. The orchestration is a prompt. Build accordingly.