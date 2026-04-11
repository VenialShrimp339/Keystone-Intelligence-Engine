# nano-claude-code: Core Architecture Analysis

**Source:** `reference/nano-claude-code/`
**Scope:** Architecture patterns applicable to Keystone's 6-layer DPVI pipeline
**Date:** 2026-04-05

---

## Summary Verdict

nano-claude-code is a clean, minimal reference implementation. Its value is not in copying its code but in validating specific patterns: generator-based event loops, layered context compaction, and per-agent config injection. The multi-provider abstraction is its least relevant component for Keystone. The generator loop and compaction strategy are its most valuable.

---

## Module Map

| File | Lines | Purpose |
|---|---|---|
| `nano_claude.py` | ~400 | REPL loop, slash commands, UI rendering (rich library) |
| `agent.py` | 175 | Generator-based agent loop, AgentState, permission gating |
| `config.py` | 76 | JSON config at `~/.nano_claude/config.json`, defaults |
| `context.py` | 166 | System prompt assembly: base + git info + CLAUDE.md + memory |
| `providers.py` | 605 | Multi-provider abstraction, streaming adapters, cost tracking |
| `compaction.py` | 197 | Two-layer context window management |

---

## 1. REPL and UI Layer (`nano_claude.py`)

**Pattern:** Hard separation between UI concerns (rendering, input, slash commands) and agent logic.

The REPL handles:
- Slash command dispatch (`/help`, `/compact`, `/model`, etc.)
- Token count display and status rendering via `rich`
- Streaming event rendering (consumes the generator from `agent.run()`)
- User input loop

Agent logic never touches terminal output directly. The REPL renders events; the agent emits them.

**Keystone relevance (L0/L3):** This separation maps to our orchestration layer. L0 (Specification Engine) should emit structured events consumed by whatever rendering or logging layer sits above it. Don't mix prompt construction with output formatting.

**Verdict: ADOPT** the separation principle. Keystone's pipeline stages should emit structured events (not print to stdout), consumed by a dedicated rendering/logging layer.

---

## 2. Agent Loop (`agent.py`, 175 lines)

The most transferable pattern in the codebase.

### Generator-Based Event Loop

```python
# agent.py (conceptual structure)
def run(self) -> Generator[AgentEvent, None, None]:
    while True:
        self.maybe_compact()
        stream = provider.stream(self.state.messages, tools=get_tool_schemas())
        for event in stream:
            yield event  # TextChunk, ThinkingChunk, ToolStart, ToolEnd
        if tool_calls:
            for call in tool_calls:
                yield PermissionRequest(call)  # if needed
                result = execute_tool(call)
                yield ToolEnd(call, result)
            self.state.messages.append(tool_results)
            continue  # loop back
        yield TurnDone(self.state)
        break
```

**Event types emitted:**
- `TextChunk` - streaming text token
- `ThinkingChunk` - extended thinking token
- `ToolStart` / `ToolEnd` - tool execution boundaries
- `PermissionRequest` - blocked pending user approval
- `TurnDone` - turn complete, includes final state

**Why generators matter:** The caller controls consumption rate. A REPL renders as tokens arrive. A background orchestrator drains the generator silently. Same loop, different consumers. ✅ Verified pattern - this is standard Python async-compatible design.

### AgentState Dataclass

```python
# agent.py
@dataclass
class AgentState:
    messages: list[dict]   # conversation history
    input_tokens: int
    output_tokens: int
    turn_count: int
```

Minimal. Holds only what's needed for continuation. No business logic lives here.

**Keystone gap:** AgentState has no trajectory storage. For META layer self-improvement, we need to capture: which tools were called in what order, latency per tool, whether outputs passed evaluation. This requires extending AgentState with a `trajectory: list[TrajectoryEntry]` field.

### Permission Gate

```python
# agent.py: _check_permission()
# read_only tools: auto-approve
# write tools in prompt mode: yield PermissionRequest, wait
# write tools in auto mode: auto-approve all
```

Three modes: `default` (ask for writes), `auto` (approve all), `read_only` (deny writes).

**Keystone mapping (L1 isolation):** Maps directly to per-agent tool access control. Research agents should run in `read_only` mode for filesystem writes. Only the L2/L3 generation layer needs write access. The permission gate is the right abstraction point.

### Config Injection for Sub-Agents

```python
# agent.py: sub-agent receives modified config
config._depth = parent_depth + 1
config._system_prompt = agent_def.system_prompt  # prepended to base
```

Sub-agents inherit parent config, then get overrides injected. Depth is tracked. System prompt is additive (prepend, not replace).

**Verdict: ADOPT** the generator loop pattern, AgentState, and config injection approach. Extend AgentState for trajectory storage.

---

## 3. Configuration (`config.py`, 76 lines)

JSON config at `~/.nano_claude/config.json`. Key defaults:

```json
{
  "model": "claude-opus-4-5",
  "max_tokens": 40000,
  "permission_mode": "default",
  "max_tool_output": 32000,
  "max_agent_depth": 3,
  "max_concurrent_agents": 3
}
```

**Cascading opportunity:** The pattern supports per-engagement config files. A Keystone engagement could have `~/keystone/engagements/acme-corp/config.json` that overrides model, depth limits, and tool sets for that specific engagement.

**Keystone mapping (L0):** The `max_agent_depth` and `max_concurrent_agents` fields translate directly to our DPVI parallelism controls. `max_concurrent_agents: 3` is conservative for research workloads; we'll need 5-10 parallel L1 agents.

**Verdict: ADOPT** file-based config with cascading. Add engagement-scoped config files at `~/.keystone/engagements/{slug}/config.json`.

---

## 4. System Prompt Builder (`context.py`, 166 lines)

Assembly order:
1. Base template (~95 lines): tool descriptions, agent guidelines, multi-agent guidelines, environment info
2. Git info: branch, recent commits, repo status
3. CLAUDE.md: walks up to 10 parent directories, loads first match
4. Memory context: from persistent memory store

**The CLAUDE.md walk is the key insight.** Rather than hardcoding system prompts, the system loads context from the nearest `.md` file up the directory tree. Project-level instructions automatically override user-level instructions. This is specification-as-file.

**Keystone mapping (L0/Specification Engine):** This is exactly how RESEARCH.md should work. An engagement-level `RESEARCH.md` in the working directory automatically loads as agent context. Sub-agents spawned in that directory inherit the engagement specification. No config plumbing needed - the filesystem is the configuration.

**Gap:** `context.py` assembles one global system prompt. Keystone needs per-agent specialization. The researcher agent needs a different system prompt than the evaluator. The fix is per-AgentDefinition prompt composition (covered in `03-multi-agent.md`).

**Verdict: ADAPT.** Keep the directory-walk pattern for loading RESEARCH.md. Replace the single global template with per-agent prompt factories that share a common base.

---

## 5. Provider Abstraction (`providers.py`, 605 lines)

**What it does:**
- Neutral message format (provider-independent dict structure)
- `stream_anthropic()` adapter for Anthropic API
- `stream_openai_compat()` adapter for OpenAI-compatible endpoints
- Provider registry keyed by model name prefix
- Context limit tracking and cost calculation per provider

**Why Keystone doesn't need this:** We use Anthropic only, via PydanticAI. PydanticAI already handles provider abstraction at a higher level with typed outputs and structured validation. Adding nano-claude-code's provider layer would be redundant and conflict with PydanticAI's streaming model.

🟡 Inferred: PydanticAI's streaming interface is sufficient for our needs given single-provider constraint.

**Verdict: SKIP.** Zero code reuse from providers.py. Study it to understand streaming event shapes, then implement directly against Anthropic SDK + PydanticAI.

---

## 6. Context Compaction (`compaction.py`, 197 lines)

The most architecturally sophisticated module. Two independent layers that run in sequence.

### Layer 1: Rule-Based Snipping (`snip_old_tool_results`)

```python
# compaction.py: snip_old_tool_results()
# For tool result messages older than last 6 turns:
#   Replace content with: first_half + "[truncated]" + last_quarter
# Preserves recent context, drops middle of old tool outputs
```

Heuristic: keep first 50% + last 25% of old tool outputs. The first half has the tool invocation context; the last quarter has conclusions. The middle is usually verbose intermediate output.

**Token estimation:** `len(content) / 3.5` - rough but fast. No API call needed.

### Layer 2: LLM-Driven Summary (`compact_messages`)

```python
# compaction.py: compact_messages()
# Split conversation at 70/30 ratio
# Summarize the old 70% with an LLM call
# Replace old messages with the summary
# Keep recent 30% intact
```

The 70/30 split is empirically chosen. The LLM summarizer preserves: key decisions, tool results, user instructions, context needed to continue. The recent 30% stays verbatim because it's most relevant.

### Trigger

```python
# agent.py: maybe_compact()
# Trigger: current_tokens > 0.70 * context_limit
# Runs Layer 1 first, recalculates. If still > 70%, runs Layer 2.
```

70% threshold leaves headroom for the next turn's output tokens.

**Keystone mapping (L1 Research Agents):**

Research agents processing full SEC filings, earnings transcripts, and web content will routinely hit 50K+ tokens per turn. The two-layer approach is necessary, not optional.

- Layer 1 (snipping) handles tool output bloat - exactly the pattern for Grep/WebFetch results
- Layer 2 (LLM summary) handles long research conversations where early context is superseded

**Keystone extension needed:** Standard compaction discards context indiscriminately. For research agents, some early findings are high-value (a specific statistic, a source URL) and must survive compaction. We need selective re-injection: before compaction, extract key findings into a structured `findings_buffer`, then re-inject after compaction as a pinned system message.

**Verdict: ADAPT.** Adopt the two-layer trigger architecture. Add a findings extraction pass before Layer 2 that pins high-value research outputs to survive the LLM summary.

---

## Cross-Cutting: DPVI Loop Mapping

The nano-claude-code agent loop is a single-agent DPVI. Keystone extends this to multi-agent:

| DPVI Phase | nano-claude-code | Keystone Extension |
|---|---|---|
| Decompose | Implicit in system prompt | L0 explicit decomposition into RESEARCH.md subtasks |
| Parallelize | Single thread | SubAgentManager thread pool → process pool |
| Verify | No evaluator | L4 Evaluator with 10-dimension rubric |
| Iterate | Re-runs on tool failure | L0 re-dispatches failed subtasks with failure context |

The while-True loop in `agent.py` is the inner DPVI. Keystone's orchestration is the outer DPVI. The generator pattern composes cleanly at both levels.

---

## Architecture Verdict Summary

| Pattern | Source | Verdict | Keystone Layer |
|---|---|---|---|
| Generator-based agent loop | `agent.py` | ADOPT | L0, L1 |
| AgentState (extended) | `agent.py` | ADOPT + extend for trajectory | META |
| Permission gate | `agent.py` | ADOPT | L1 isolation |
| Config injection for sub-agents | `agent.py` | ADOPT | L0 dispatch |
| File-based config with cascading | `config.py` | ADOPT | L0 |
| Directory-walk for RESEARCH.md | `context.py` | ADOPT | L0 Specification |
| Per-agent prompt specialization | `context.py` gap | ADAPT | L1, L4 |
| Provider abstraction | `providers.py` | SKIP | N/A |
| Two-layer compaction | `compaction.py` | ADAPT + findings buffer | L1 |
| Snip-old-tool-results heuristic | `compaction.py` | ADOPT | L1 |
| 70% trigger threshold | `compaction.py` | ADOPT | L1 |
