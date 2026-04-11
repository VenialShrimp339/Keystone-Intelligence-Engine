# Phase 8: Emergent Patterns & Unexpected Findings

## Key Finding

Beyond the module-specific analysis, 10 cross-cutting architectural patterns emerge from nano-claude-code that are relevant to Keystone. The most impactful: the generator-as-event-stream pattern should be adopted for ALL pipeline stages, not just the agent loop.

---

## Cross-Cutting Patterns

### 1. Generator-as-Event-Stream ✅ Verified

**Where:** `agent.py:55-146`

The agent loop is a Python generator yielding typed events (TextChunk, ToolStart, ToolEnd, TurnDone, PermissionRequest). This enables:
- Streaming UI updates without polling
- Event logging for trajectory storage
- Cooperative cancellation (check between yields)
- Progress tracking across long operations

```python
# agent.py:62-66
def run(user_message, state, config, system_prompt,
        depth=0, cancel_check=None) -> Generator:
    # Yields: TextChunk | ThinkingChunk | ToolStart | ToolEnd |
    #         PermissionRequest | TurnDone
```

**Keystone connection (ALL layers):** Every pipeline stage (L0-L1-L1.5-L2-L3-L4) should yield typed events. This enables:
- Trajectory storage: log every event for META layer analysis
- Pipeline observability: monitor progress across all stages
- Graceful cancellation: abort long-running research engagements
- Debugging: replay events to diagnose quality issues

**Verdict:** ADOPT -- extend with pipeline-specific event types (ResearchTaskDispatched, CitationFound, ClaimExtracted, EvaluationScored)

### 2. Lazy Import for Circular Dependencies ✅ Verified

**Where:** `multi_agent/subagent.py:258-265`

```python
def _agent_run(prompt, state, config, system_prompt, depth=0, cancel_check=None):
    """Lazy-import wrapper to avoid circular dependency."""
    import agent as _agent_mod
    return _agent_mod.run(prompt, state, config, system_prompt, depth=depth, cancel_check=cancel_check)
```

Breaks: agent -> subagent -> agent circular import.

**Keystone connection (L0, L4):** We'll face this pattern when L4 Evaluator triggers L1 re-runs, or when L0 needs to spawn agents that reference L0's own task tracking.

**Verdict:** LEARN -- use dependency injection instead where possible, lazy import as fallback

### 3. Neutral Message Format ✅ Verified

**Where:** `providers.py:224-314`

All internal code works with a provider-independent message format. Conversion to Anthropic/OpenAI format happens only at the API boundary.

```python
# Internal format:
{"role": "user", "content": "text"}
{"role": "assistant", "content": "text", "tool_calls": [{id, name, input}]}
{"role": "tool", "tool_call_id": "...", "name": "...", "content": "..."}
```

**Keystone connection (L1-L1.5, L1.5-L2 handoffs):** Internal representations should be provider-agnostic. Our claim-level intermediate representation is the equivalent -- a neutral format that any pipeline stage can consume.

**Verdict:** ADOPT -- use typed dataclasses for all inter-layer data formats

### 4. Config as Runtime State Container ✅ Verified

**Where:** `agent.py:77`, `multi_agent/tools.py:51`

The config dict carries runtime metadata via `_`-prefixed keys that are stripped before saving or passing to sub-agents:

```python
# agent.py:77
config = {**config, "_depth": depth, "_system_prompt": system_prompt}

# multi_agent/tools.py:51
eff_config = {k: v for k, v in config.items() if not k.startswith("_")}
```

**Verdict:** ADAPT -- use Pydantic models with `exclude` fields instead of string prefix convention

### 5. Registration-on-Import Side Effect 🟡 Inferred

**Where:** `multi_agent/tools.py:160-295`, `memory/tools.py:84-216`, `task/tools.py:265`, `mcp/tools.py:130-131`

Every tool module registers its tools when imported. This is implicit and order-dependent.

**Verdict:** ADAPT -- use explicit tool registry initialization with per-agent filtering

### 6. Two-Layer Truncation (Cheap Then Expensive) ✅ Verified

**Where:** `compaction.py:53-83` (snip), `compaction.py:110-165` (compact), `tool_registry.py:57-93` (output)

Pattern: always try the cheap operation first, only escalate to the expensive one if needed.
- Compaction: rule-based snip (free) -> LLM summarization (costs tokens)
- Output: first_half + last_quarter truncation (preserves context from both ends)

**Verdict:** ADOPT -- universal optimization principle for the pipeline

### 7. Bidirectional Dependency Graph ✅ Verified

**Where:** `task/store.py:146-166`

When adding dependency edges, both directions are maintained automatically. Tests verify 20 concurrent creates with unique IDs (`tests/test_task.py:196-213`).

**Verdict:** ADOPT for research-tasks.json dependency management

### 8. Staleness Detection on Persistent State ✅ Verified

**Where:** `memory/scan.py:109-123`

Warns when memories are >1 day old: "claims about code behavior may be outdated."

**Keystone connection (META, Observation Library):** Research findings age at different rates:
- Market data: stale within days
- Methodology insights: stable for months
- Regulatory findings: depends on legislative calendar

**Verdict:** ADOPT -- add domain-specific staleness models per observation type

### 9. Background Initialization ✅ Verified

**Where:** `mcp/tools.py:123-131`

MCP servers connect in background thread so startup isn't blocked.

**Verdict:** ADOPT for pre-warming all 8 search API connections at pipeline startup

### 10. Output Truncation: First Half + Last Quarter ✅ Verified

**Where:** `tool_registry.py:82-92`

Better than simple head truncation because the end of output often has summaries and conclusions.

**Verdict:** ADOPT for all tool outputs and intermediate results

---

## Unexpected Findings

### A. No Structured Logging

The entire 11.8K-line codebase has zero logging infrastructure. No log levels, no structured events, no telemetry. Output goes to stdout via print().

**Keystone impact:** We need structured logging from day one for trajectory storage and debugging.

### B. No Error Recovery ✅ Verified

agent.py loop has no retry logic. If providers.stream() fails, the loop ends. No exponential backoff, no fallback, no graceful degradation.

**Keystone impact:** Research agents running for minutes need retry/backoff on API failures.

### C. Thread-Level Only Isolation ✅ Verified

Agents share process memory, global tool_registry, filesystem. AgentLeak findings (68.8% leakage) apply directly.

**Keystone impact:** MUST implement process-level isolation for L1 agents.

### D. No Rate Limiting ✅ Verified

The only concurrency control is max_concurrent_agents on ThreadPoolExecutor.

**Keystone impact:** 15-50 parallel agents need Redis-based per-provider rate limiting.

### E. Debug Payload Leak ✅ Verified

`providers.py:431` writes every OpenAI-compat API call to debug_payload.json in cwd. Development artifact showing maturity level.

**Keystone impact:** AVOID. Use proper structured logging.

### F. AskUserQuestion Threading Pattern 🟡 Inferred

`tools.py:14-17` implements async user interaction with pending_questions list and threading lock. Not directly useful for automated pipeline but demonstrates architecture flexibility.

---

## Anti-Patterns to Avoid

| Anti-Pattern | Where | Keystone Alternative |
|---|---|---|
| Global mutable registries | _registry, _agent_manager, _manager | Dependency injection |
| Registration-on-import | All tools.py modules | Explicit initialization |
| Thread-level isolation | SubAgentManager | Process-level (subprocess) |
| No structured error types | Bare `except Exception` | Typed exceptions |
| Magic _prefixed config keys | _depth, _system_prompt | Typed Pydantic models |
| Debug file writes | providers.py:431 | Structured logging |
| Silent exception swallowing | Multiple `except Exception: pass` | Log before swallowing |

---

## Test Suite Insights

The test suite (78 tests, 10 files) reveals design priorities:

| Test File | Tests | What It Protects |
|---|---|---|
| test_tool_registry.py | 8 | Registration, lookup, truncation |
| test_compaction.py | 12 | Token estimation, snipping, context limits |
| test_subagent.py | 8 | Spawn/wait, cancel, depth limit |
| test_memory.py | 20 | Save/load, dual-scope, search, staleness |
| test_task.py | 25 | CRUD, dependency edges, thread safety |
| test_skills.py | ~5 | Skill loading, parsing |

**Key test patterns for Keystone adoption:**
- monkeypatch for redirecting storage to tmp_path
- Mocking _agent_run to avoid real API calls
- Thread-safety stress tests (20 concurrent creates)
- Persistence roundtrips (clear memory, reload from disk, verify)
