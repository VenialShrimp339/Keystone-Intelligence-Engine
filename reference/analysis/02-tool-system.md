# nano-claude-code: Tool System Analysis

**Source:** `reference/nano-claude-code/tool_registry.py`, `tools.py`, `memory/tools.py`, `multi_agent/tools.py`, `task/tools.py`, `mcp/tools.py`
**Scope:** Tool registration, execution, subsetting, and output management patterns
**Date:** 2026-04-05

---

## Summary Verdict

The tool system is the most directly reusable subsystem. The ToolDef dataclass, central registry, and output truncation strategy map cleanly to Keystone's per-agent tool subsetting requirement. The registration-on-import pattern needs tightening for production use. MCP namespace convention is directly adoptable for Exa/Brave integration.

---

## 1. Tool Registry (`tool_registry.py`, 99 lines)

### ToolDef Dataclass

```python
# tool_registry.py
@dataclass
class ToolDef:
    name: str           # identifier used in API schema
    schema: dict        # Anthropic-style JSON schema
    func: Callable      # implementation: (params, config) -> str
    read_only: bool     # auto-approve in default permission mode
    concurrent_safe: bool  # safe to run in parallel with other tools
```

Five fields. No inheritance hierarchy. No abstract base classes. The schema is a plain dict matching Anthropic's tool_use format, which means it passes directly to the API without transformation.

**Why `read_only` and `concurrent_safe` are separate flags:**
- `read_only=True` controls permission gating (auto-approve without user prompt)
- `concurrent_safe=True` controls execution scheduling (can run in parallel with other tools in the same turn)
- A tool can be read-only but not concurrent-safe (e.g., reads shared mutable state)
- A tool can be write but concurrent-safe (e.g., writes to isolated namespaced storage)

🟡 Inferred: concurrent_safe is not yet used for parallel execution in the current implementation, but the flag is correctly placed for future scheduling logic.

### Central Registry

```python
# tool_registry.py
_registry: dict[str, ToolDef] = {}

def register_tool(tool_def: ToolDef) -> None:
    _registry[tool_def.name] = tool_def  # overwrites on name collision

def get_tool_schemas() -> list[dict]:
    return [t.schema for t in _registry.values()]

def execute_tool(name: str, params: dict, config: Config) -> str:
    tool = _registry[name]
    result = tool.func(params, config)
    return _truncate_output(result, config.max_tool_output)
```

Global dict, mutable at runtime. `register_tool()` silently overwrites on name collision - last writer wins. This is intentional: project-level tools in `.nano-claude/agents/` can override built-in tools by registering the same name.

### Output Truncation

```python
# tool_registry.py: _truncate_output()
# If len(result) > max_tool_output (default 32000 chars):
#   return result[:first_half] + "\n[truncated]\n" + result[-last_quarter:]
# first_half = max_tool_output // 2
# last_quarter = max_tool_output // 4
```

The first half / last quarter split for truncation mirrors the compaction heuristic. Beginning of output has invocation context and headers; end has conclusions and summary lines. Middle is typically verbose intermediate content.

**Keystone concern:** 32K char default may be too small for full SEC filings or earnings call transcripts fed through WebFetch. We need `max_tool_output: 128000` for research agents, with per-tool overrides for structured data tools that always produce compact output.

**Verdict: ADOPT** ToolDef dataclass and central registry. ADOPT output truncation strategy. Increase limit for research-grade tool outputs.

---

## 2. Tool Implementations (`tools.py`, ~750 lines)

### Core Pattern

Every tool follows the same signature:

```python
# tools.py: example pattern
def tool_read(params: dict, config: Config) -> str:
    path = params["path"]
    # ... implementation ...
    return result_string  # always a string

register_tool(ToolDef(
    name="Read",
    schema={
        "name": "Read",
        "description": "...",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", ...}},
            "required": ["path"]
        }
    },
    func=tool_read,
    read_only=True,
    concurrent_safe=True
))
```

Registration happens at module import time. If `tools.py` is imported, all 15+ tools are registered. There is no lazy loading or explicit activation step.

### Full Tool Inventory

| Tool | read_only | concurrent_safe | Notes |
|---|---|---|---|
| Read | True | True | File read with offset/limit |
| Write | False | False | Full file overwrite |
| Edit | False | False | Exact string replacement |
| Bash | False | False | Shell execution with safe prefix whitelist |
| Glob | True | True | Pattern file search |
| Grep | True | True | Ripgrep wrapper |
| WebFetch | True | False | HTTP fetch + HTML→text |
| WebSearch | True | False | DuckDuckGo HTML scraping (no API key) |
| TaskCreate | False | False | Create task in task store |
| TaskUpdate | False | False | Update task status/result |
| TaskGet | True | True | Read task by ID |
| TaskList | True | True | List all tasks |
| NotebookEdit | False | False | Jupyter notebook cell edit |
| GetDiagnostics | True | True | LSP diagnostics |
| AskUserQuestion | False | False | Interactive user prompt |
| SleepTimer | True | False | Async wait |

### Safe Bash Whitelist (`_SAFE_PREFIXES`)

```python
# tools.py
_SAFE_PREFIXES = [
    "git ", "ls ", "cat ", "head ", "tail ",
    "echo ", "pwd", "date", "whoami",
    # ... ~20 more read-safe prefixes
]
```

Any bash command starting with a safe prefix auto-approves in default permission mode. Commands outside the whitelist require explicit user approval or auto mode.

**Keystone mapping (L1 isolation):** Research agents should have a more restrictive whitelist - no `git` commands (agents shouldn't modify repo state), no `echo` with redirects. The whitelist should be per-agent, not global.

### Diff Generation for Edit/Write

Edit and Write tools return a unified diff as their output string, not just "success". This gives the agent (and the human reviewer) immediate visibility into what changed. The diff is generated before returning:

```python
# tools.py: Edit tool (conceptual)
old_content = read_file(path)
new_content = apply_edit(old_content, old_string, new_string)
write_file(path, new_content)
return generate_unified_diff(old_content, new_content)
```

**Keystone mapping (L3 Generation):** Report generation tools should return diffs or structured change summaries, not silent success. The L4 Evaluator needs to see what changed to evaluate it.

### WebSearch Implementation

DuckDuckGo HTML scraping - no API key required, no cost, but fragile:

```python
# tools.py: WebSearch (conceptual)
url = f"https://html.duckduckgo.com/html/?q={query}"
response = requests.get(url, headers={"User-Agent": ...})
# Parse HTML, extract result titles/URLs/snippets
return formatted_results
```

⚠️ Uncertain: DuckDuckGo HTML structure changes without notice. This approach is appropriate for a reference implementation, not a production research system.

**Keystone verdict:** Replace with Exa (semantic search) and Brave Search API (web coverage) via MCP. The WebSearch tool implementation is a placeholder pattern only.

**Verdict for tools.py:**
- Core tool pattern (func + schema + ToolDef): ADOPT
- Bash safe prefix whitelist: ADAPT - make per-agent, tighten for research agents
- Diff output for write operations: ADOPT
- WebSearch (DuckDuckGo scraping): SKIP - replace with Exa/Brave MCP tools
- WebFetch (HTTP fetch + HTML parsing): ADAPT - add structured extraction for financial documents

---

## 3. Module-Level Registration Pattern

Four separate tool modules, each registering on import:

```
tools.py              → 15 core tools (Read, Write, Bash, etc.)
memory/tools.py       → memory read/write tools
multi_agent/tools.py  → Agent, SendMessage, CheckAgentResult, ListAgentTasks
task/tools.py         → TaskCreate, TaskUpdate, TaskGet, TaskList
mcp/tools.py          → MCP server proxy tools
```

Each module calls `register_tool()` at module level (outside any function). Import order determines registration order. Name collisions silently overwrite.

**The problem for Keystone:** Global shared registry means all tools are always available to all agents unless explicitly filtered. Research agents currently have access to Write and Bash unless we add filtering at the `get_tool_schemas()` call site.

nano-claude-code handles this via `AgentDefinition.tools` (a list of allowed tool names). The `get_tool_schemas()` function needs a filter parameter:

```python
# Current (from tool_registry.py):
def get_tool_schemas() -> list[dict]:
    return [t.schema for t in _registry.values()]

# Keystone needs:
def get_tool_schemas(allowed: list[str] | None = None) -> list[dict]:
    if allowed is None:
        return [t.schema for t in _registry.values()]
    return [t.schema for t in _registry.values() if t.name in allowed]
```

This change is 3 lines but architecturally critical. ✅ Verified: AgentDefinition.tools already passes the filter list; get_tool_schemas() just needs to accept it.

**Verdict: ADAPT** registration pattern. Add explicit initialization order (tools.py first, then specialized modules). Add `allowed` filter parameter to `get_tool_schemas()`. Log registration at startup for debuggability.

---

## 4. MCP Tool Integration (`mcp/tools.py`)

MCP tools register under a namespaced convention:

```
mcp__<server_name>__<tool_name>
```

Examples:
- `mcp__filesystem__read_file`
- `mcp__brave__web_search`
- `mcp__exa__search`

The MCP module acts as a proxy: it discovers available tools from connected MCP servers and registers a wrapper ToolDef for each. The wrapper forwards calls to the MCP server and returns the response as a string.

**Keystone mapping (L1 Research Tools):**

This namespace convention is directly adoptable for Exa and Brave Search integration:

| MCP Tool | Keystone Use | Agent Layer |
|---|---|---|
| `mcp__exa__search` | Semantic search for research topics | L1 Research Agents |
| `mcp__exa__find_similar` | Find similar companies/reports | L1 Research Agents |
| `mcp__brave__web_search` | Broad web coverage for news | L1 Research Agents |
| `mcp__filesystem__read_file` | Read engagement documents | L0 Specification |

The proxy pattern means new data sources are added by connecting an MCP server - no code changes needed in the core agent loop.

**CitationProcessor implication:** MCP tools return raw content. The CitationProcessor needs to extract source URLs from MCP tool results before they enter the compaction pipeline, or the source provenance is lost.

**Verdict: ADOPT** MCP namespace convention and proxy registration pattern. Connect Exa and Brave as MCP servers. Add CitationProcessor hook at the ToolEnd event boundary.

---

## 5. Keystone Tool Architecture (Synthesis)

Based on the nano-claude-code analysis, the Keystone tool registry should look like:

```
Core Research Tools (read_only=True, concurrent_safe=True):
  mcp__exa__search
  mcp__exa__find_similar
  mcp__brave__web_search
  WebFetch (adapted for financial documents)
  Grep (for local document search)
  Glob (for engagement file discovery)
  Read (for RESEARCH.md, source documents)

Content Generation Tools (read_only=False, concurrent_safe=False):
  Write (for draft sections)
  Edit (for revision passes)

Orchestration Tools (internal):
  Agent (spawn sub-agent)
  CheckAgentResult
  SendMessage
  TaskCreate / TaskUpdate / TaskGet

Evaluation Tools (L4 only):
  GetDiagnostics (adapted for claim verification)
  [custom] EvaluateClaim
  [custom] ScoreOutput
```

Per-agent tool subsets (enforced via `AgentDefinition.tools`):

| Agent Type | Allowed Tools |
|---|---|
| L1 Researcher | exa, brave, WebFetch, Grep, Read |
| L1.5 Deliberation | Read, TaskGet, TaskList |
| L2 Content Structurer | Read, Write, Edit |
| L3 Generator | Read, Write, Edit |
| L4 Evaluator | Read, GetDiagnostics, EvaluateClaim, ScoreOutput |
| L0 Orchestrator | All orchestration tools, Read, TaskCreate |

---

## Verdict Summary

| Pattern | Source | Verdict | Keystone Layer |
|---|---|---|---|
| ToolDef dataclass | `tool_registry.py` | ADOPT directly | All layers |
| Central registry (global dict) | `tool_registry.py` | ADOPT | All layers |
| Output truncation (first_half + last_quarter) | `tool_registry.py` | ADOPT, increase limit | L1 |
| read_only / concurrent_safe flags | `tool_registry.py` | ADOPT | L1 isolation |
| Per-tool func(params, config) signature | `tools.py` | ADOPT | All layers |
| Bash safe prefix whitelist | `tools.py` | ADAPT - per-agent | L1 |
| Diff output for write operations | `tools.py` | ADOPT | L3, L4 |
| WebSearch (DuckDuckGo scraping) | `tools.py` | SKIP | N/A |
| WebFetch (HTTP + HTML parsing) | `tools.py` | ADAPT for finance docs | L1 |
| Registration-on-import | Multiple modules | ADAPT - explicit order | All layers |
| `get_tool_schemas()` filter | `tool_registry.py` gap | BUILD (3-line addition) | L1 |
| MCP namespace convention | `mcp/tools.py` | ADOPT | L1 |
| MCP proxy registration | `mcp/tools.py` | ADOPT | L1 |
