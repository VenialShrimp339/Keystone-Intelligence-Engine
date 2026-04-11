# Master Index: nano-claude-code Analysis for Keystone Intelligence Engine

*Analysis date: 2026-04-05 | Codebase: reference/nano-claude-code/ (56 Python files, ~11.8K lines)*

---

## Analysis Files

| File | Key Findings |
|------|-------------|
| [01-core-architecture.md](01-core-architecture.md) | Generator-based agent loop (175 lines), two-layer compaction, config cascading. ADOPT loop pattern for DPVI orchestration. |
| [02-tool-system.md](02-tool-system.md) | ToolDef registry with output truncation (32K), per-agent subsetting via AgentDefinition.tools. ADOPT for 3-5 tools per agent. |
| [03-multi-agent.md](03-multi-agent.md) | **HIGHEST VALUE.** AgentDefinition specialization from .md files, ThreadPoolExecutor concurrency, worktree isolation. Thread-level isolation is INSUFFICIENT for Keystone security (68.8% AgentLeak leakage applies). |
| [04-task-management.md](04-task-management.md) | Bidirectional dependency graph with automatic reverse-edge maintenance. Thread-safe JSON store. ADOPT for research-tasks.json, extend with passes/priority/type fields. |
| [05-memory-context.md](05-memory-context.md) | **HIGHEST VALUE.** Dual-scope memory (user/project), AI-powered relevance search, two-layer compaction, staleness warnings. Maps directly to Observation Library, JIT context loading, and trajectory storage. |
| [06-mcp-implementation.md](06-mcp-implementation.md) | Complete MCP client (~850 lines) with stdio/SSE/HTTP transports. ADOPT as reference for Component #4 MCP Gateway. Missing: rate limiting, caching, cost tracking. |
| [07-skills-plugins.md](07-skills-plugins.md) | Markdown skill definitions with YAML frontmatter, inline/fork execution modes. ADOPT for consulting methodology skills (market-sizing, competitive-analysis). |
| [08-emergent-patterns.md](08-emergent-patterns.md) | 10 cross-cutting patterns. Key: generator-as-event-stream for ALL layers, two-layer truncation (cheap then expensive), bidirectional dependencies. Anti-patterns: no logging, no retry, thread-level isolation. |
| [09-implementation-recommendations.md](09-implementation-recommendations.md) | Maps all 11 Phase 1 components to nano-claude-code. 5 components have strong matches (#4, #5, #7, #9, #11). **No architectural decisions changed; all validated.** |

---

## File-by-File Inventory

| nano-claude-code File | Lines | Primary Keystone Relevance |
|---|---|---|
| nano_claude.py | ~400 | REPL loop, UI only. SKIP. |
| agent.py | 175 | Core agent loop. ADOPT generator pattern for DPVI. |
| config.py | 76 | Config management. ADOPT, use Pydantic models. |
| context.py | 166 | System prompt builder. ADAPT for per-agent specialization. |
| providers.py | 605 | Multi-provider abstraction. SKIP (Anthropic only). |
| compaction.py | 197 | Two-layer context management. ADOPT for research agents. |
| tool_registry.py | 99 | Central tool registry. ADOPT with per-agent filtering. |
| tools.py | ~750 | Tool implementations. LEARN patterns, build own. |
| subagent.py (root) | 12 | Backward-compat shim. N/A. |
| memory.py (root) | 11 | Backward-compat shim. N/A. |
| skills.py (root) | 14 | Backward-compat shim. N/A. |
| multi_agent/__init__.py | 24 | Package exports. N/A. |
| multi_agent/subagent.py | 481 | **HIGHEST VALUE.** Agent definitions, spawning, isolation. |
| multi_agent/tools.py | 296 | Agent tool registrations. ADOPT spawn/check pattern. |
| task/__init__.py | 13 | Package exports. N/A. |
| task/types.py | 93 | Task dataclass with dependency graph. ADOPT + extend. |
| task/store.py | 200 | Thread-safe store. ADAPT for PostgreSQL. |
| task/tools.py | 266 | Task tool implementations. LEARN API shape. |
| memory/__init__.py | 87 | Package exports. N/A. |
| memory/types.py | 87 | Memory type taxonomy. ADOPT type system. |
| memory/store.py | 224 | File-based memory store. ADAPT for Observation Library. |
| memory/context.py | 222 | Context building + AI relevance. ADOPT for JIT loading. |
| memory/scan.py | 145 | Scanning + staleness. ADOPT for observation freshness. |
| memory/tools.py | 217 | Memory tool registrations. LEARN tool API. |
| mcp/__init__.py | 43 | Package exports. N/A. |
| mcp/types.py | 125 | MCP type definitions. ADOPT for gateway. |
| mcp/client.py | 547 | **HIGH VALUE.** MCP client. ADOPT as reference. |
| mcp/config.py | 134 | MCP config loading. ADOPT pattern. |
| mcp/tools.py | 132 | MCP tool registration. ADOPT pattern. |
| skill/__init__.py | 14 | Package exports. N/A. |
| skill/loader.py | 185 | Skill loading from markdown. ADOPT for methodology. |
| skill/executor.py | 67 | Execution modes (inline/fork). ADOPT. |
| skill/builtin.py | 101 | Built-in skills. LEARN structure. |
| plugin/__init__.py | 22 | Package exports. N/A. |
| plugin/types.py | 133 | Plugin manifest. INVESTIGATE for modular APIs. |

---

## Quick-Reference: Keystone Component -> nano-claude-code

| Keystone Component | nano-claude-code Files | Key Pattern | Verdict |
|---|---|---|---|
| #1 RESEARCH.md | context.py | Template composition | BUILD (learn from context loading) |
| #2 Citation Model | (none) | N/A | BUILD |
| #3 Retrieval | memory/context.py | AI relevance search | BUILD (learn from hybrid search) |
| #4 MCP Gateway | mcp/* | Full MCP client | **ADOPT** as reference |
| #5 Spec Engine (L0) | agent.py, multi_agent/subagent.py | Agent loop + dispatch | ADAPT |
| #6 Evaluator (L4) | (none) | N/A | BUILD |
| #7 Research Agents (L1) | multi_agent/subagent.py | AgentDefinition + spawn | **ADOPT** + harden isolation |
| #8 CitationProcessor | (none) | N/A | BUILD |
| #9 Deliberation (L1.5) | skill/executor.py | Fork execution mode | ADAPT spawn pattern |
| #10 Calibration | (none) | N/A | BUILD |
| #11 E2E Test | tests/test_subagent.py | Mock agent run | **ADOPT** test pattern |

---

## Top 5 Highest-Impact Findings

### 1. Generator-based agent loop is the right orchestration primitive
`agent.py` -- 175 lines. A Python generator handles the entire agent lifecycle, yielding typed events (TextChunk, ToolStart, ToolEnd, TurnDone). This validates our decision to build custom orchestration rather than adopting a framework. **Adopt for every pipeline stage, not just the agent loop.** Every L0/L1/L1.5/L2/L3/L4 transition should yield typed events for observability and trajectory storage.

### 2. Thread-level isolation is insufficient for our security model
`multi_agent/subagent.py` -- ThreadPoolExecutor-based agents share process memory, global state, and filesystem access. Our AgentLeak findings (68.8% leakage in standard frameworks, 46.7% from shared memory) apply directly to this architecture. **We MUST use process-level isolation** with per-agent working directories, per-agent tool registries, and advisory file locks.

### 3. MCP gateway is fully tractable as a build
`mcp/*` -- ~850 lines of working Python implementing stdio/SSE/HTTP transports, auto-discovery, tool registration, and auto-reconnect. Our Component #4 can reference this directly. **Add rate limiting (Redis), caching (Redis + pgvector), and cost tracking** to make it production-ready.

### 4. Two-layer compaction handles long research sessions
`compaction.py` -- Cheap rule-based snipping first (truncate old tool results to first_half + last_quarter), expensive LLM summarization second (only if still over 70% of context limit). **Critical for research agents** processing 50K+ tokens of search results. Adopt as baseline, add selective re-injection of claim-level findings.

### 5. AgentDefinition from markdown enables rapid specialization
`multi_agent/subagent.py` -- Agent types defined as .md files with YAML frontmatter specifying tools, model, system_prompt. Filesystem priority: builtin -> user -> project. **Maps perfectly to our L1 agent specialization needs:** define market_researcher.md, financial_analyst.md, etc. with specialized prompts and tool restrictions (3-5 tools each).

---

## Areas for Deeper Follow-Up

1. **Process-level agent isolation** -- Evaluate subprocess vs. containers vs. Temporal activity isolation for L1 agents
2. **Selective re-injection after compaction** -- Compaction drops old tool results, but claim-level findings should be preserved
3. **Rate limiting architecture** -- Design Redis-based rate limiter for 15-50 parallel agents hitting 8 search APIs
4. **Structured event logging** -- Design typed event schema for all pipeline stages (trajectory storage)
5. **Observation Library data model** -- Extend MemoryEntry with structured fields for evidence quality, pattern classification, constraint/reinforcement tagging
