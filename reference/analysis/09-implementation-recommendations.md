# Phase 9: Implementation Recommendations

## Key Finding

nano-claude-code **validates all existing architectural decisions** in CAPSTONE-PLAN-v2.md. No decisions need to change. The codebase provides concrete implementation patterns for 5 of our 11 Phase 1 components and reference patterns for 3 more.

---

## Phase 1 Build Components Mapped to nano-claude-code

### #1: RESEARCH.md Specification Format

**nano-claude-code equivalent:** `context.py` template composition pattern

No direct equivalent for RESEARCH.md, but context.py shows how structured specifications are loaded and injected into agent sessions. The CLAUDE.md walk-up pattern (searching parent directories) could inform how RESEARCH.md is discovered by agents.

**Reusable:** Template composition pattern, directory walk-up for config discovery
**Build from scratch:** Schema format, sample specs, validation logic
**Verdict:** BUILD. LEARN from `context.py:121-151` (CLAUDE.md loading).

### #2: Citation Data Model

**nano-claude-code equivalent:** None

No citation tracking exists in the codebase.

**Verdict:** BUILD from scratch.

### #3: pgvector + Hybrid Search Retrieval

**nano-claude-code equivalent:** `memory/context.py:107-221` (AI-powered relevance search)

The `find_relevant_memories()` function implements a two-strategy search:
1. Keyword match (cheap, always runs)
2. AI-powered ranking (optional, uses small LLM call to select from candidates)

This is conceptually similar to hybrid search (lexical + semantic), but uses LLM-as-ranker instead of vector similarity.

**Reusable:** The hybrid search concept (cheap filter + expensive ranker)
**Build from scratch:** pgvector integration, embedding pipeline, BM25 indexing
**Verdict:** BUILD. LEARN from `memory/context.py:107-152` (hybrid search concept).

### #4: MCP Gateway

**nano-claude-code equivalent:** `mcp/*` (complete MCP client, ~850 lines)

**DIRECT MATCH.** Complete working implementation with:
- Stdio/SSE/HTTP transports (`mcp/client.py:20-275`)
- Tool discovery and registration (`mcp/client.py:349-384`, `mcp/tools.py:34-53`)
- Configuration management (`mcp/config.py`)
- Background initialization (`mcp/tools.py:123-131`)
- Auto-reconnect (`mcp/client.py:507-509`)

**Reusable:** Entire MCP client architecture as reference implementation
**Build additionally:** Rate limiting (Redis), caching (Redis), cost tracking, health monitoring
**Verdict:** ADOPT as reference. See `06-mcp-implementation.md` for details.

### #5: Specification Engine (L0)

**nano-claude-code equivalent:** `agent.py` loop + `multi_agent/subagent.py` dispatch

L0 would be a specialized agent that:
1. Receives user question
2. Generates RESEARCH.md using the agent loop pattern
3. Decomposes into research-tasks.json
4. Dispatches research agents via SubAgentManager.spawn() pattern

**Reusable:**
- Generator-based agent loop (`agent.py:55-146`)
- System prompt composition (`context.py:153-165`)
- Sub-agent dispatch with specialization (`multi_agent/subagent.py:288-411`)

**Build additionally:** RESEARCH.md generation logic, task decomposition, pre-flight validation
**Verdict:** ADAPT. Reference: `agent.py:55-146` for loop, `multi_agent/subagent.py:288-411` for dispatch.

### #6: Evaluator Stack (L4) Layers 1-3

**nano-claude-code equivalent:** None (no evaluation layer)

The permission gate pattern (`agent.py:150-165`) demonstrates deterministic boolean checks, conceptually similar to our Layer 1 (deterministic verification).

**Reusable:** Permission gate pattern for deterministic checks
**Build from scratch:** Citation gate, Prometheus 2 rubric, evaluation orchestration
**Verdict:** BUILD. LEARN from `agent.py:150-165` (deterministic gate pattern).

### #7: Research Agent Pipeline (L1)

**nano-claude-code equivalent:** `multi_agent/subagent.py` (agent definitions + spawning)

**STRONG MATCH.** The AgentDefinition pattern with:
- Specialized system_prompt per agent type
- Model override (inherit or override parent)
- Tool restriction (empty list = all tools, explicit list = subset)
- Fresh AgentState per agent (no shared conversation history)

```python
# multi_agent/subagent.py:17-25
@dataclass
class AgentDefinition:
    name: str
    description: str = ""
    system_prompt: str = ""   # extra instructions prepended
    model: str = ""           # override; "" = inherit
    tools: list = field(default_factory=list)  # empty = all tools
    source: str = "user"      # "built-in" | "user" | "project"
```

**Reusable:** AgentDefinition, spawn pattern, fresh state per agent, depth limiting
**Adapt:** Thread-level isolation -> process-level isolation
**Verdict:** ADOPT AgentDefinition. ADAPT SubAgentManager for process-level isolation.

### #8: CitationProcessor

**nano-claude-code equivalent:** None

**Verdict:** BUILD from scratch.

### #9: Basic Deliberation (L1.5)

**nano-claude-code equivalent:** `skill/executor.py:45-67` (fork execution mode) + spawn pattern

The fork mode runs a skill as an isolated sub-agent with fresh state. Combined with SubAgentManager's ability to spawn multiple agents and collect results, this provides the deliberation pattern:
1. Spawn N analyst agents, each with all L1 findings as prompt
2. Each analyst runs independently (fresh AgentState)
3. Collect all results
4. Aggregate (structured aggregation, not debate)

**Reusable:** Fork execution mode, spawn + collect pattern
**Build additionally:** Methodological diversity assignment, structured aggregation logic, DiscoUQ confidence mapping
**Verdict:** ADAPT spawn + collect pattern.

### #10: Evaluator Calibration

**nano-claude-code equivalent:** None

**Verdict:** BUILD from scratch.

### #11: End-to-End Pipeline Test

**nano-claude-code equivalent:** `tests/test_subagent.py:12-29` (mock agent run pattern)

The test suite mocks `_agent_run` to avoid real API calls while testing the full agent lifecycle:

```python
# tests/test_subagent.py:12-29
def _make_mock_agent_run(sleep_per_iter=0.05, iters=3):
    def mock_agent_run(prompt, state, config, system_prompt, depth=0, cancel_check=None):
        for i in range(iters):
            if cancel_check and cancel_check():
                return
            time.sleep(sleep_per_iter)
        state.messages.append({"role": "assistant", "content": f"Result for: {prompt}"})
        yield None
    return mock_agent_run
```

**Reusable:** Mock LLM pattern, monkeypatch fixtures, thread-safety tests
**Verdict:** ADOPT test mocking pattern.

---

## Top 5 Patterns to Adopt Directly

### 1. ToolDef Dataclass + Central Registry (`tool_registry.py`)

```python
@dataclass
class ToolDef:
    name: str
    schema: dict       # JSON schema for API
    func: Callable     # (params, config) -> str
    read_only: bool    # auto-approve in "auto" mode
    concurrent_safe: bool  # safe for parallel execution
```

Per-agent tool subsetting: AgentDefinition.tools lists which tools the agent can use. If empty, all tools are available.

**Keystone application:** Define ToolDefs for research_company(), search_filings(), analyze_market(). Restrict each L1 agent to 3-5 tools.

### 2. Generator-Based Agent Loop (`agent.py`)

175-line generator handling the full agent lifecycle. Events enable streaming, logging, cancellation, and progress tracking.

**Keystone application:** Use for EVERY pipeline stage. L0 yields ResearchSpecGenerated. L1 yields CitationFound. L4 yields EvaluationResult.

### 3. AgentDefinition from Markdown (`multi_agent/subagent.py`)

Agent types defined as .md files with YAML frontmatter (tools, model, system_prompt). Filesystem hierarchy: builtin -> user -> project.

**Keystone application:** Define market_researcher.md, financial_analyst.md, regulatory_scanner.md with specialized prompts and tool sets.

### 4. Two-Layer Compaction (`compaction.py`)

Snip (cheap, rule-based) -> Compact (expensive, LLM-driven). Trigger at 70% of context limit.

**Keystone application:** Research agents processing 50K+ tokens of search results will hit context limits. This pattern handles it.

### 5. MCP Client Architecture (`mcp/`)

Complete client with transport abstraction, tool registration, background init, auto-reconnect.

**Keystone application:** Direct reference for Component #4 MCP Gateway. Add rate limiting and caching.

---

## Top 5 Patterns to Adapt

### 1. SubAgentManager -> Process-Level Isolation

Thread-level isolation is insufficient for our security requirements (68.8% AgentLeak leakage). Replace ThreadPoolExecutor with subprocess-based isolation, per-agent working directories, and per-agent tool registries.

### 2. Memory System -> Observation Library

Add structured fields for pattern_name, evidence_quality, constraint_or_reinforcement. Add vector search via pgvector. Keep the dual-scope (user/project -> global/engagement) and staleness warnings.

### 3. Task Dependency Graph -> Research Tasks

Add research-specific fields: passes (evaluator-only), priority, task-type (estimative/current), anti_confirmatory_framing, assigned_tools, assigned_model. Replace sequential IDs with UUIDs. Replace JSON file store with PostgreSQL.

### 4. Config System -> Typed Pydantic Models

Replace plain dict with Pydantic models. Replace _prefix convention with explicit runtime/persistent field separation.

### 5. System Prompt Composition -> Per-Agent Specialization

Replace single global prompt with per-agent prompt assembly: base methodology + agent specialization + engagement context + JIT research context.

---

## Anti-Patterns to Avoid

1. **Global mutable registries** -> Dependency injection
2. **Thread-level agent isolation** -> Process-level with filesystem sandboxing
3. **No structured logging** -> Structured event logging from day one
4. **No retry/backoff** -> Exponential backoff with jitter, model fallback
5. **No rate limiting** -> Redis-based per-API rate limiting
6. **Debug file writes** -> Proper logging (no `debug_payload.json`)
7. **Silent exception swallowing** -> Log and propagate or handle explicitly
8. **Registration-on-import** -> Explicit initialization for deterministic behavior

---

## Does This Change Our Architecture?

### Validated Decisions (No Changes Needed)

| Decision | Validation Evidence |
|---|---|
| Custom orchestration over framework adoption | 175-line agent loop proves custom is tractable |
| Agent isolation must be structural | Thread-level isolation demonstrably insufficient |
| Per-agent tool specialization (3-5 tools) | AgentDefinition.tools works well |
| File-based persistent memory | memory/ package demonstrates cross-session knowledge works |
| MCP for tool integration | Complete working implementation proves feasibility |
| Claim-level intermediate representations | Neutral message format shows provider-agnostic interchange works |
| Two-layer compaction for long contexts | Snip + summarize handles 200K context windows |

### New Insights (Additive, Not Changes)

1. **Generator-based event streams for ALL pipeline stages** -- not just the agent loop. Every L0/L1/L1.5/L2/L3/L4 transition should yield typed events for observability and trajectory storage.

2. **Background initialization for external services** -- pre-warm all 8 search API connections at pipeline startup, don't block the Specification Engine.

3. **Bidirectional dependency tracking** should be automatic -- when task A blocks task B, the reverse edge should be maintained automatically (as in task/store.py).

4. **Staleness warnings on persistent observations** -- research findings age. Memory freshness_text pattern should be adopted for Observation Library entries.

### Bottom Line

**No architectural decisions changed.** The codebase validates our plan. The value is in concrete implementation patterns we can reference rather than designing from scratch. The 5 highest-value patterns (ToolDef, generator loop, AgentDefinition, compaction, MCP client) collectively save significant implementation time on Components #4, #5, #7, #9, and #11.
