# Autonomous Overnight Analysis: nano-claude-code → Keystone Intelligence Engine

## Your Mission

You are analyzing the nano-claude-code repository (a Python reimplementation of Claude Code's leaked source) to extract every architectural pattern, implementation decision, and design insight relevant to building the Keystone Intelligence Engine, a multi-agent AI system for automated consulting research.

**You will work autonomously until the entire codebase is analyzed. Do not stop to ask questions. Do not pause for confirmation. Every piece of context you need is in this project folder.** If you encounter ambiguity, make your best judgment, document your reasoning, and keep going. If a file is unreadable or missing, note it and move on.

## Context Loading Strategy

Read project context JIT (just-in-time), not all at once. Loading everything upfront wastes context you need for code analysis.

**Read immediately (small, orienting):**
1. `CLAUDE.md` -- Project conventions, pipeline summary, key terms. 77 lines.
2. `audit/SESSION-CONTEXT.md` -- What exists, what's settled, what to build. 66 lines.

**Read per-phase (only the relevant sections):**
3. `CAPSTONE-PLAN-v2.md` -- Source of truth. 1294 lines. Do NOT read the whole thing. Read only the sections relevant to the phase you're working on:
   - Phase 1 (Core Architecture): Read Sections 2 and 3 (Architecture Overview, Specification Engine)
   - Phase 2 (Tool System): Read Section 4.1 (agent tool loading) and Section 6.2 (retrieval architecture)
   - Phase 3 (Multi-Agent): Read Section 4.1-4.3 (Research Agents, Agent Specialization, Deliberation)
   - Phase 4 (Task Management): Read Section 3.6 (Research Initiation) and Section 4.4 (Sprint Contracts)
   - Phase 5 (Memory/Context): Read Section 7 (Self-Improvement Loop)
   - Phase 6 (MCP): Read Section 6.2 (Unified Retrieval Architecture) and Section 12 (Implementation)
   - Phase 9 (Recommendations): Read `audit/PHASE-1-IMPLEMENTATION-SPEC.md` for the 11 build components with schemas

**Read if relevant finding emerges:**
4. `synthesis/PLAN-CHANGELOG.md` -- The 17 changes already applied. Consult when you find a pattern that might confirm or contradict a decision we've made.
5. `synthesis/UNIFIED-SYNTHESIS.md` -- Cross-report synthesis. Consult when you need tool/framework verdicts.

The Keystone pipeline for quick reference:
```
META  → Self-Improvement (Observation Library, prompt evolution, trajectory storage)
L0    → Specification Engine (question → RESEARCH.md spec → task decomposition → agent dispatch)
L1    → Parallel Research Agents (strict filesystem isolation, JIT context, anti-confirmatory, 3-5 tools per agent)
       → CitationProcessor (cross-agent dedup, corroboration scoring, URL verification)
L1.5  → Deliberation (independent parallel analysis with methodological diversity + structured aggregation, NOT debate)
L2    → Content Structuring (consulting frameworks, sprint contracts, claim-level handoffs)
L3    → Generation (deliverables in Keystone format)
L4    → Evaluator (5-layer stack: deterministic → citation gate → Prometheus 2 rubric (10 dimensions) → process trajectory → cross-model ensemble)
```

## The Codebase You're Analyzing

Location: `reference/nano-claude-code/`
Size: 56 Python files, 11,833 lines.

**Start by reading:** `reference/nano-claude-code/docs/architecture.md` (374 lines). This is the developer architecture guide and contains the module dependency graph, data model definitions, and design rationale. Read this before any source code.

Also read: `reference/nano-claude-code/docs/comparison_claude_code_vs_nano_v3.03_en.md` (152 lines). This maps features between the original Claude Code and this reimplementation, showing what's implemented vs. what's missing.

**Ignore these items in the repo root** (they are junk files from the cloning process, not part of the codebase):
- `hsperfdata_root/`, `node-compile-cache/`, `snap-private-tmp/`, `systemd-private-*/`
- `CLAUDE_CODE_COMPREHENSIVE_RESEARCH.md`, `CLAUDE_CODE_QUICK_REFERENCE.md`, `CLAUDE_CODE_TO_KEYSTONE_MAPPING.md`, `RESEARCH_SUMMARY.md` (these are not part of nano-claude-code; they were accidentally copied during setup)

**Key directories:**
- `multi_agent/` -- Multi-agent orchestration (subagent spawning, coordination, tools)
- `task/` -- Task management with dependency graphs
- `memory/` -- Persistent memory system (store, context, scanning, types)
- `mcp/` -- Model Context Protocol implementation (client, config, tools, types)
- `skill/` -- Skills system (loader, executor, builtins)
- `plugin/` -- Plugin system (loader, store, recommendations, types)
- `tests/` -- Test suite (reveals what the authors considered critical/fragile)
- `docs/` -- Architecture guide, comparison docs, design specs
- `voice/` -- Voice input (skip, not relevant to Keystone)

**Core files:** `nano_claude.py`, `agent.py`, `config.py`, `context.py`, `providers.py`, `tools.py`, `compaction.py`, `subagent.py`, `skills.py`, `tool_registry.py`, `memory.py`

## Methodology

Work through the codebase in this order. For each phase, read every relevant file completely, then write your analysis to `reference/analysis/`.

**Priority weighting:** Phases 3 (Multi-Agent) and 5 (Memory/Context) are the highest-value for Keystone. Spend proportionally more time on these. Phase 7 (Skills/Plugins) is lower priority. If you're running low on context, prioritize Phases 3, 5, and 8 (Emergent Patterns) over Phase 7.

### Phase 1: Core Architecture (write to `reference/analysis/01-core-architecture.md`)

Read: `docs/architecture.md` first, then `nano_claude.py`, `agent.py`, `config.py`, `context.py`, `providers.py`

Analyze:
- The main orchestration loop (how does the agent process a query end-to-end?)
- How is the system prompt constructed and composed? What goes into it and in what order?
- How are tool calls dispatched and results handled?
- What is the retry/error handling pattern?
- How does configuration cascade work?
- The REPL loop in nano_claude.py vs. the multi-turn agent loop in agent.py: what's the separation of concerns?
- **Keystone connection:** Map this to our L0 Specification Engine's orchestration needs. What patterns can we reuse for the DPVI loop? Read CAPSTONE-PLAN-v2.md Sections 2-3 for our orchestration design.

### Phase 2: Tool System (write to `reference/analysis/02-tool-system.md`)

Read: `tool_registry.py` first (the central registry), then `tools.py`, then all `*/tools.py` files (memory/tools.py, mcp/tools.py, multi_agent/tools.py, task/tools.py, skill/tools.py)

Analyze:
- The ToolDef dataclass and ToolRegistry: how are tools defined, registered, and dispatched?
- What is the tool schema format exposed to the model?
- How does tool permission/sandboxing work?
- How are tool results formatted and returned to the model? What's the truncation/summarization strategy for large tool outputs?
- Is there per-agent tool subsetting? How does it decide which tools an agent gets?
- How do different modules (memory, mcp, task, skill) register their tools?
- **Keystone connection:** Map to our per-agent tool specialization (3-5 tools per agent). Map to our workflow-level tools design (research_company() pattern). Read CAPSTONE-PLAN-v2.md Section 4.1 for our agent tool loading design. What can we reuse for building Exa/Brave/Firecrawl tool wrappers?

### Phase 3: Multi-Agent Orchestration [HIGHEST PRIORITY] (write to `reference/analysis/03-multi-agent.md`)

Read: `multi_agent/__init__.py`, `multi_agent/subagent.py`, `multi_agent/tools.py`, AND `subagent.py` (the root-level file, which may differ from multi_agent/subagent.py)

Analyze with maximum depth:
- How are subagents spawned? What context do they inherit vs. get fresh?
- How do agents communicate (inbox system, shared state, file-based, message passing)?
- How is task claiming/locking implemented? What prevents two agents from claiming the same task?
- What isolation guarantees exist between agents? Are they process-level, thread-level, or filesystem-level?
- How does the coordinator/lead pattern work? What does the lead agent see that teammates don't?
- Fork vs. teammate vs. worktree execution models: which are implemented here? How do they differ?
- What happens when a subagent fails or hangs? Timeout handling? Error propagation?
- How are results collected from completed subagents and aggregated?
- **Keystone connection:** This is the most critical section for our project. Map every pattern to:
  - L0 dispatch (how the Specification Engine fans out research agents)
  - L1 parallel research agents (isolation, task claiming, independent execution)
  - L1.5 deliberation spawning (spawning analyst agents that access all findings)
  - The coordinator pattern (does it map to our L0 as coordinator?)
  - Identify what we can ADOPT directly, what needs ADAPT, and what we must SKIP
  - Our AgentLeak findings: 68.8% leakage in standard frameworks, 46.7% from shared memory. Does nano-claude-code's isolation prevent this?
- Read CAPSTONE-PLAN-v2.md Sections 4.1-4.3 while analyzing this.

### Phase 4: Task Management (write to `reference/analysis/04-task-management.md`)

Read: `task/__init__.py`, `task/types.py` first (data model), then `task/store.py`, `task/tools.py`

Analyze:
- The task data model: how are tasks defined and structured? What fields exist?
- How does the dependency graph work? Can tasks specify prerequisites?
- How is task state tracked (pending/in-progress/complete/failed)?
- How are task results collected and aggregated?
- How does task prioritization work?
- Is there a concept of a task "owner" (assigned agent)?
- **Keystone connection:** Map to our research-tasks.json format (see the schema in CAPSTONE-PLAN-v2.md Section 3.6), task decomposition in L0, and the `passes` field that only the Evaluator can flip. Can we adapt this dependency graph for our pipeline stages? Does the task model support our task-type field (estimative vs. current)?

### Phase 5: Memory & Context Management [HIGHEST PRIORITY] (write to `reference/analysis/05-memory-context.md`)

Read: `memory/__init__.py`, `memory/types.py` first (data model), then `memory/store.py`, `memory/context.py`, `memory/scan.py`, `memory/tools.py`. Then read: `memory.py` (root-level), `compaction.py`, `context.py`

Analyze with maximum depth:
- How does the persistent memory system work (store, retrieval, types)?
- What is the memory scanning mechanism? How does it decide what's relevant?
- How does context compaction work? Does it implement the three-layer system (MicroCompact, AutoCompact, Full Compact)?
- What triggers compaction? What threshold? What is preserved vs. dropped?
- How is selective re-injection implemented after compaction? Is there a relevance scoring mechanism?
- How does persistent memory (memory/ module) differ from conversation context (context.py)?
- How does MEMORY.md or equivalent work for cross-session knowledge?
- What are the data structures for memory entries? How is memory indexed?
- **Keystone connection:** Map to:
  - Trajectory storage (full decision logs of every research engagement)
  - Observation Library persistence (how captured patterns survive across sessions)
  - JIT context loading (how agents load only relevant source material)
  - Research agent session management (agents processing 50K+ tokens need compaction)
  - The instinct-to-skill pipeline (temporary observations → permanent skills)
  - Read CAPSTONE-PLAN-v2.md Section 7 while analyzing this.

### Phase 6: MCP Implementation (write to `reference/analysis/06-mcp-implementation.md`)

Read: `mcp/__init__.py`, `mcp/types.py` first, then `mcp/config.py`, `mcp/client.py`, `mcp/tools.py`

Analyze:
- How is the MCP client implemented? What protocol does it use (stdio, SSE, other)?
- How are MCP servers discovered, configured, and connected?
- How are MCP tools registered alongside built-in tools? Does the tool registry treat them uniformly?
- What is the configuration model for MCP servers?
- How does Claude Code handle multiple MCP servers providing different tool sets?
- Connection lifecycle: startup, health checks, reconnection, shutdown?
- **Keystone connection:** Map to our MCP gateway architecture (Component #4 in Phase 1). This is one of the first things we build (no dependencies, starts immediately). We need to integrate 8 services: Exa, Brave, Firecrawl, Tavily, EdgarTools, CrossRef, Semantic Scholar, OpenAlex. Read CAPSTONE-PLAN-v2.md Section 6.2 for our retrieval architecture.

### Phase 7: Skills & Plugins [LOWER PRIORITY] (write to `reference/analysis/07-skills-plugins.md`)

Read: `skill/__init__.py`, `skill/loader.py`, `skill/executor.py`, `skill/builtin.py`, `skill/tools.py`, `skills.py` (root-level). Then: `plugin/__init__.py`, `plugin/loader.py`, `plugin/store.py`, `plugin/recommend.py`, `plugin/types.py`

Analyze:
- How are skills defined, loaded, and composed?
- What is the skill schema/format? YAML frontmatter?
- How does progressive skill loading work (lightweight names → full methodology → supporting docs)?
- How does the skill executor work? How are skills invoked during a session?
- How does the plugin system extend functionality? What's the plugin data model?
- Plugin recommendations: how does the system suggest relevant plugins?
- **Keystone connection:** Map to our three-layer skill loading architecture and our consulting framework skills (market-sizing, competitive-analysis, etc.). Can we use this plugin architecture for our search API integrations?

### Phase 8: Emergent Patterns & Unexpected Findings (write to `reference/analysis/08-emergent-patterns.md`)

This is the open-ended discovery pass. Re-read any files that seemed particularly interesting or complex. Also read files not yet covered:
- `demo.py`, `make_demo.py` -- What do these reveal about intended usage patterns?
- `tests/` directory completely -- What do test cases reveal about edge cases, fragile components, and design assumptions? Read every test file.
- `docs/superpowers/` -- Design specs and enhancement plans
- Any code comments that document design decisions, known limitations, or future plans
- Any `__init__.py` files that reveal module-level exports and design intent

Look specifically for:
- Patterns we didn't ask about that are relevant to Keystone
- Clever engineering solutions to problems we'll face (error recovery, state management, streaming, rate limiting)
- Anti-patterns or documented limitations that we should avoid
- Cross-cutting concerns: logging, observability, error propagation, graceful degradation
- Type safety and validation patterns relevant to our handoff contracts
- Configuration defaults that reveal design philosophy
- Anything that changes or challenges our current architectural assumptions

**This phase is high-value.** The findings we didn't think to ask about are often the most important.

### Phase 9: Implementation Recommendations (write to `reference/analysis/09-implementation-recommendations.md`)

Read `audit/PHASE-1-IMPLEMENTATION-SPEC.md` now (the 11 build components with schemas and acceptance criteria).

Synthesize across all previous phases:
- The most significant patterns to adopt directly (with file paths, line numbers, and code snippets for each)
- Patterns to adapt/modify for our use case (with specific modification rationale)
- Anti-patterns to avoid (things nano-claude-code does that conflict with our architectural convictions)
- **For each of our 11 Phase 1 build components (#1 through #11):** cite the relevant nano-claude-code implementation, assess what's reusable, and note what we'd need to build from scratch
- **Critical question:** Does analyzing this codebase change any of our architectural decisions from PLAN-CHANGELOG.md? If so, which ones and why? If not, which decisions does it validate and how?

### Phase 10: Master Index (write to `reference/analysis/00-master-index.md`)

Create a master index that:
- Lists every analysis file with a 2-3 sentence summary of key findings
- Provides a file-by-file inventory: every nano-claude-code Python file, its line count, and its primary relevance to Keystone (one line per file)
- Quick-reference table: Keystone Phase 1 component → relevant nano-claude-code files → key pattern → verdict (ADOPT/ADAPT/SKIP)
- The 5 highest-impact findings across all phases (the "if you read nothing else, read these" items)
- Files or areas that warrant deeper follow-up analysis
- Any open questions that emerged during analysis

## Output Standards

For every analysis file:
- Lead with the key finding, not the methodology
- Include actual code snippets (with file paths and line numbers) for every significant pattern
- Make explicit verdicts: ADOPT (use directly in Keystone) / ADAPT (modify for our use case, specify how) / SKIP (not applicable, say why) / INVESTIGATE (promising but needs deeper analysis)
- Connect every finding to a specific Keystone pipeline layer (L0/L1/L1.5/L2/L3/L4/META) or Phase 1 component (#1-#11)
- Use evidence quality markers: ✅ Verified (code confirms it clearly) · 🟡 Inferred (code suggests it but implementation is partial) · ⚠️ Uncertain (code is ambiguous or incomplete)
- Flag contradictions with our current architecture explicitly and prominently

## Execution Rules

1. **Do not stop.** Work through all 10 phases sequentially. Write each file completely before starting the next.
2. **Do not ask questions.** Make your best judgment and document your reasoning.
3. **Read files completely.** Don't skim. The insights are in the implementation details, not the function signatures.
4. **Write as you go.** Complete each analysis file before moving to the next phase. This ensures partial progress is saved if the session ends unexpectedly.
5. **Cross-reference constantly.** When you find a pattern in nano-claude-code, check it against the relevant section of CAPSTONE-PLAN-v2.md. Does it validate, contradict, or extend our design?
6. **Be specific.** "The multi-agent system uses message passing" is useless. "multi_agent/tools.py implements a JSON inbox at lines 45-78 using file-based message queues with advisory locking, which maps to our L1 agent isolation requirement" is useful.
7. **Flag surprises.** If you find something we didn't anticipate, give it extra attention. These emergent findings are the highest-value output of this analysis.
8. **Context limit resilience.** If you sense you are approaching context limits, immediately write your current analysis to the appropriate file. After compaction, re-read your previously written analysis files in `reference/analysis/` to re-establish context before continuing with the next phase. Do not lose work.
9. **Prioritize breadth over perfection.** Getting through all 10 phases with solid analysis is more valuable than exhaustive analysis of 3 phases. If a phase is taking too long, capture the key findings and move on.
10. **Skip the voice/ directory.** It implements offline voice input and has no relevance to Keystone.
