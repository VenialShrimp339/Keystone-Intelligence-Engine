# Skills & Plugin System — nano-claude-code Analysis

**Source files:** `skill/loader.py` (185 lines), `skill/executor.py` (67 lines), `skill/builtin.py` (101 lines), `plugin/types.py` (133 lines), `plugin/__init__.py`

---

## Skills System

### SkillDef Data Model (`skill/loader.py`)

The `SkillDef` dataclass captures everything needed to define, locate, and execute a skill:

```python
@dataclass
class SkillDef:
    name: str
    description: str
    triggers: list[str]        # e.g. ["/commit"]
    tools: list[str]           # allowed-tools restriction
    prompt: str                # body text
    file_path: str
    when_to_use: str
    argument_hint: str
    arguments: list[str]       # named arg names for substitution
    model: str | None          # optional model override
    user_invocable: bool
    context: str               # "inline" or "fork"
    source: str                # builtin | user | project
```

Skills are markdown files with YAML frontmatter. `_parse_skill_file()` splits the frontmatter from the body and hydrates a `SkillDef`. The body becomes the prompt. This means skill definitions are human-readable, version-controllable, and editable without touching Python.

### Three-Layer Loading and Deduplication

`load_skills()` searches in priority order:

1. `.nano_claude/skills/` — project-level (highest priority)
2. `~/.nano_claude/skills/` — user-level
3. Built-ins registered via `register_builtin_skill()` — lowest priority

Deduplication is by name: project overrides user, user overrides builtin. This gives teams a clean override mechanism without forking core code.

`find_skill()` matches against `triggers` by comparing the first word of user input.

### Argument Substitution

`substitute_arguments()` does simple string replacement:

- `$ARGUMENTS` → the full argument string
- `$ARG_NAME` → named argument by position

This is intentionally minimal. No templating engine, no conditionals. The entire argument surface is defined by the `arguments` list in frontmatter.

### Execution Modes (`skill/executor.py`)

`execute_skill()` renders the prompt with substituted arguments and wraps it as `[Skill: name]\n\n{rendered}`. Two paths then diverge:

**Inline (`context: inline`):** Passes the rendered prompt into `agent.run()` on the current conversation. Shares `AgentState`, tool registry, and conversation history. Low overhead, no isolation.

**Fork (`context: fork`):** Instantiates a fresh `AgentState`. Accepts an optional `model` override and restricts tools via the `_allowed_tools` config key. The sub-agent is isolated from the parent's conversation state. This is structurally the same mechanism as `subagent.py` but triggered at the skill boundary rather than by a tool call.

### Built-in Skills (`skill/builtin.py`)

Two built-ins ship with the system: `/commit` and `/review`. Both are multi-step structured prompts registered via `register_builtin_skill()`. They illustrate the intended pattern: a skill is not a shortcut but a complete methodology — a sequence of instructions with quality criteria baked in.

---

## Plugin System

### PluginManifest (`plugin/types.py`)

```python
@dataclass
class PluginManifest:
    name: str
    version: str
    description: str
    author: str
    tags: list[str]
    tools: list[str]        # python modules providing tools
    skills: list[str]       # .md files providing skills
    mcp_servers: dict       # MCP server config keyed by server name
    dependencies: list[str] # pip packages
    homepage: str
```

Loaded from `plugin.json` or YAML frontmatter in `PLUGIN.md`. The `mcp_servers` field is the structural anchor: a plugin can bundle an MCP server config alongside the skills and tools that use it. Install the plugin, get the server wired up automatically.

`PluginEntry` adds runtime metadata: `scope` (user/project), `source` (git URL), `install_dir`, `enabled`.

`parse_plugin_identifier()` handles the `name@source` format, enabling git-URL installs with a pinned name.

### Plugin Lifecycle

`plugin/__init__.py` exports the full lifecycle:

```
install_plugin, uninstall_plugin, enable_plugin, disable_plugin,
list_plugins, load_all_plugins, recommend_plugins
```

`recommend_plugins` is the only export not directly relevant to Keystone — it suggests plugins based on project context, which is a user-facing UX feature, not a pipeline automation concern.

---

## Keystone Connections

### Consulting Framework as Skill Files

The SkillDef structure maps directly onto Keystone's consulting methodology needs. Each framework becomes a markdown file:

```
market-sizing.md
  ---
  name: market-sizing
  model: claude-opus-4-5
  context: fork
  tools: [web_search, read_file]
  arguments: [company_name, industry, geography]
  ---
  [Bottom-up and top-down sizing methodology...]

competitive-landscape.md
  ---
  name: competitive-landscape
  model: claude-opus-4-5
  context: fork
  tools: [web_search, read_file]
  arguments: [company_name, competitors]
  ---
  [Porter's Five Forces + positioning analysis...]
```

The frontmatter handles tool restriction, model selection, and argument surface. The body encodes the methodology. Changes to the framework are diffs to a markdown file.

### L0 → Skill Selection

nano-claude-code selects skills via trigger matching on user input. Keystone does not have user input at skill invocation time — L0 (Specification Engine) produces a RESEARCH.md and then dispatches agents programmatically. The trigger mechanism is the wrong interface for this.

L0 should select skills by name lookup: `load_skills()` returns all available `SkillDef` objects; L0 picks the appropriate one based on the engagement type parsed from RESEARCH.md. The `find_skill()` trigger path is bypassed entirely.

### Fork Mode for Independent Analysis

`context: fork` with a fresh `AgentState` and `_allowed_tools` restriction is the correct execution model for L1 parallel research agents. Each agent gets:

- An isolated state (no cross-contamination of conversation history)
- A restricted tool set (only the search/read tools needed for that task)
- An optional model override (cheaper model for preliminary passes)

This matches the structural isolation requirement. The gap (thread-level only, not process-level) remains, but fork mode is the right layer for it.

### Inline Mode for L2 Content Structuring

Content structuring (L2) operates on already-collected research. It does not need isolation — it needs access to the accumulated L1 outputs. `context: inline` is correct here. The structuring skill runs in the same context as the aggregated research, with access to the full conversation state.

### $ARGUMENTS Substitution for Research Parameters

`substitute_arguments()` as-is handles positional named args. Keystone needs structured research parameters: `company_name`, `industry`, `geography`, `time_horizon`, `depth`. These map cleanly onto named `$ARG_NAME` placeholders. No change to the mechanism needed — the frontmatter `arguments` list defines the surface, and L0 populates the values from RESEARCH.md.

### Plugin as Search API Bundle

The `mcp_servers` field in `PluginManifest` is the key capability. A `keystone-search` plugin would bundle:

```json
{
  "name": "keystone-search",
  "tools": ["keystone_search_tools"],
  "skills": ["market-sizing.md", "competitive-landscape.md"],
  "mcp_servers": {
    "exa": { "command": "npx", "args": ["-y", "exa-mcp-server"] },
    "brave": { "command": "npx", "args": ["-y", "brave-search-mcp"] }
  },
  "dependencies": ["exa-py"]
}
```

Installing this plugin wires up both MCP servers and registers the consulting skills. The bundle is the unit of deployment. This is worth investigating further before committing — the MCP server lifecycle management (startup, health check, restart) is the unknown.

---

## Verdicts

| Component | Verdict | Justification |
|-----------|---------|---------------|
| SkillDef with markdown frontmatter | **ADOPT** | Clean separation of methodology (body) from execution config (frontmatter). Version-controllable consulting framework definitions. |
| Trigger-based skill invocation (`find_skill()`) | **SKIP** | L0 selects skills programmatically by name, not by parsing user input. Wrong interface for an automated pipeline. |
| `context: fork` execution | **ADOPT** | Correct model for L1 parallel agents. Provides state isolation, tool restriction, and model override per agent. |
| `context: inline` execution | **ADOPT** | Correct model for L2 content structuring. Access to accumulated research without spawning new state. |
| `$ARGUMENTS` substitution | **ADAPT** | Mechanism is sound. Extend argument definitions to match Keystone research parameters (company_name, industry, geography, time_horizon). |
| Three-layer loading (builtin → user → project) | **ADOPT** | Maps to Keystone's skill priority: core methodology (builtin) → firm defaults (user) → engagement-specific overrides (project). |
| Plugin manifest with tools/skills/mcp_servers | **INVESTIGATE** | Bundling search APIs with consulting skills is architecturally clean. MCP server lifecycle management needs validation before committing. |
| Plugin `recommend_plugins` | **SKIP** | User-facing UX feature with no role in an automated research pipeline. |
