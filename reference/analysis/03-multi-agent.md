# nano-claude-code: Multi-Agent System Analysis

**Source:** `reference/nano-claude-code/multi_agent/subagent.py` (481 lines), `multi_agent/tools.py` (296 lines)
**Scope:** Spawn patterns, isolation model, communication primitives, and security gaps
**Priority:** HIGHEST - maps directly to Keystone's L0/L1/L1.5 implementation
**Date:** 2026-04-05

---

## Summary Verdict

The multi-agent subsystem is the most architecturally relevant component for Keystone. Its spawn pattern, fresh-state-per-agent design, and AgentDefinition-from-markdown approach are directly adoptable. Its isolation model is thread-level only, which is insufficient for Keystone's security requirements given the 68.8% AgentLeak leakage finding. The fix is process-level isolation via subprocess or containers, not a refactor of the agent logic.

---

## 1. AgentDefinition (`multi_agent/subagent.py`)

```python
# multi_agent/subagent.py
@dataclass
class AgentDefinition:
    name: str
    description: str
    system_prompt: str      # extra instructions, prepended to base system prompt
    model: str | None       # None = inherit from parent config
    tools: list[str]        # empty list = all tools allowed
    source: str             # "builtin" | path to .md file
```

### Built-In Agent Definitions

Five built-in agents ship with nano-claude-code:

| Name | Tools | System Prompt Focus |
|---|---|---|
| `general-purpose` | all | Balanced generalist |
| `coder` | Read, Write, Edit, Bash, Glob, Grep | Code implementation |
| `reviewer` | Read, Glob, Grep | Read-only code review |
| `researcher` | Read, Glob, Grep, WebFetch, WebSearch | Information gathering |
| `tester` | Read, Write, Edit, Bash | Test execution and writing |

The `reviewer` getting only `[Read, Glob, Grep]` is a clean example of minimal tool access. It cannot write, cannot execute, cannot fetch - it can only read and analyze. This is the correct isolation model for a review/evaluation agent.

**Keystone mapping (L4 Evaluator):** The reviewer pattern maps directly to our L4 Evaluator. Read-only tool access prevents the evaluator from modifying what it's evaluating. This is structural enforcement, not policy enforcement.

### Custom Agents from `.md` Files

Agent definitions load from YAML frontmatter in markdown files:

```markdown
<!-- ~/.nano-claude/agents/market-researcher.md -->
---
tools: [Read, WebFetch, mcp__exa__search, mcp__brave__web_search]
model: claude-sonnet-4-5
description: Specialized market research agent for competitive analysis
---

You are a market research specialist. When analyzing companies:
1. Always verify claims with multiple sources
2. Prioritize primary sources (SEC filings, earnings calls) over secondary
3. Flag any data older than 18 months
4. Extract specific numbers, not qualitative descriptions
```

Search order: `~/.nano-claude/agents/*.md` (user-level) → `.nano-claude/agents/*.md` (project-level overrides user).

**Keystone mapping (L1 Research Agents, L0 Specification):**

This is the correct pattern for defining Keystone's research specializations. Each agent type becomes a `.md` file:

```
~/.keystone/agents/
  market-researcher.md
  financial-analyst.md
  competitive-intelligence.md
  regulatory-analyst.md
  synthesizer.md
  evaluator.md

{engagement_dir}/.keystone/agents/
  # Engagement-specific overrides
  acme-corp-researcher.md  # specialized for this client's sector
```

The engagement-level override pattern means client-specific methodology instructions live alongside the engagement files, not in global config. ✅ Verified: directory-walk override is implemented in context.py's CLAUDE.md loading, and the same pattern applies here.

**Verdict: ADOPT** AgentDefinition from .md files with YAML frontmatter. This is specification-as-file, which is exactly what Keystone's Specification Engine should produce.

---

## 2. SubAgentTask (`multi_agent/subagent.py`)

```python
# multi_agent/subagent.py
@dataclass
class SubAgentTask:
    id: str                          # UUID
    prompt: str                      # initial task prompt
    status: str                      # pending | running | completed | failed | cancelled
    result: str | None               # output string when completed
    depth: int                       # spawn depth (root=0)
    name: str                        # agent definition name
    worktree_path: str | None        # git worktree path if isolated
    worktree_branch: str | None      # git branch for worktree
    _cancel_flag: bool               # cooperative cancellation signal
    _future: Future                  # ThreadPoolExecutor future
    _inbox: queue.Queue              # message queue for SendMessage
```

The status lifecycle: `pending → running → completed | failed | cancelled`

The `_inbox` queue enables asynchronous message passing while an agent is running. Messages are drained after the current work unit completes, not mid-stream. This prevents message processing from interrupting tool execution.

**Keystone mapping:** SubAgentTask maps to our Handoff Contract concept. The task carries: what was asked (`prompt`), current state (`status`), output (`result`), and lineage (`depth`, `name`). We need to extend it with:

```python
# Keystone extension to SubAgentTask
@dataclass
class KeystoneAgentTask(SubAgentTask):
    research_spec: str | None        # RESEARCH.md content that scoped this agent
    citations: list[Citation]        # extracted source citations
    confidence_scores: dict          # per-claim confidence
    evaluator_score: float | None    # L4 score when evaluated
    trajectory: list[TrajectoryEntry]  # tool call sequence for META layer
```

---

## 3. SubAgentManager (`multi_agent/subagent.py`)

The coordinator that manages the agent pool.

### Initialization

```python
# multi_agent/subagent.py
class SubAgentManager:
    def __init__(self, max_concurrent: int = 3, max_depth: int = 5):
        self._executor = ThreadPoolExecutor(max_workers=max_concurrent)
        self._tasks: dict[str, SubAgentTask] = {}
        self._max_depth = max_depth
```

ThreadPoolExecutor with configurable concurrency. Task registry is a plain dict. No priority queue, no work stealing, no backpressure.

### spawn()

```python
# multi_agent/subagent.py: spawn() (conceptual)
def spawn(self, agent_def: AgentDefinition, prompt: str,
          parent_config: Config, parent_depth: int,
          isolated: bool = False) -> SubAgentTask:

    if parent_depth >= self._max_depth:
        raise AgentDepthError(f"Max depth {self._max_depth} exceeded")

    task = SubAgentTask(id=uuid4(), prompt=prompt, depth=parent_depth+1, ...)
    self._tasks[task.id] = task

    # Build effective config for child
    child_config = copy(parent_config)
    child_config._depth = parent_depth + 1
    child_config._system_prompt = agent_def.system_prompt  # prepended

    if isolated and git_available():
        task.worktree_path, task.worktree_branch = self._create_worktree()

    task._future = self._executor.submit(self._run, task, child_config)
    return task
```

**Key behavior:** spawn() returns immediately. The task runs in the background. The caller can either `wait()` for the result (blocking) or poll `CheckAgentResult` (non-blocking).

**Keystone mapping (L0 Dispatch):**

L0 calls `spawn()` for each research subtask defined in RESEARCH.md. The DPVI decompose step produces N subtasks; L0 calls spawn() N times, gets N SubAgentTask objects back, then waits for all:

```python
# L0 conceptual dispatch
tasks = []
for subtask in research_spec.subtasks:
    agent_def = load_agent_def(subtask.agent_type)
    task = manager.spawn(agent_def, subtask.prompt, config, depth=0)
    tasks.append(task)

# Wait for all L1 agents
results = [manager.wait(t.id, timeout=300) for t in tasks]

# Pass to L1.5 Deliberation
deliberation_input = aggregate_results(results)
```

### _run() (the actual execution)

```python
# multi_agent/subagent.py: _run() (runs in thread)
def _run(self, task: SubAgentTask, config: Config) -> None:
    task.status = "running"
    try:
        if task.worktree_path:
            os.chdir(task.worktree_path)

        state = AgentState()  # FRESH - empty message history
        state.messages.append({"role": "user", "content": task.prompt})

        cancel_check = lambda: task._cancel_flag

        # Drain the generator - consume all events silently
        for event in agent.run(state, config, cancel_check=cancel_check):
            if isinstance(event, TurnDone):
                task.result = extract_final_text(event)

        # Drain inbox after completion
        while not task._inbox.empty():
            msg = task._inbox.get_nowait()
            # process followup message...

        task.status = "completed"
    except Exception as e:
        task.status = "failed"
        task.result = str(e)
```

**Critical: Fresh AgentState.** Each sub-agent starts with an empty message history. The only context it gets is:
1. The base system prompt (from context.py)
2. The agent_def's system_prompt (prepended)
3. The task prompt (first user message)

No conversation history bleeds from parent to child. No shared mutable state in AgentState. ✅ Verified: this is structurally enforced, not policy-enforced.

**Verdict: ADOPT** fresh AgentState per agent. This is non-negotiable for Keystone's anti-confirmatory research requirement.

### wait() and Cooperative Cancellation

```python
# multi_agent/subagent.py
def wait(self, task_id: str, timeout: float | None = None) -> str | None:
    task = self._tasks[task_id]
    task._future.result(timeout=timeout)  # blocks
    return task.result

def cancel(self, task_id: str) -> None:
    task = self._tasks[task_id]
    task._cancel_flag = True  # signal only; agent checks at each loop iteration
```

Cancellation is cooperative: the agent loop checks `cancel_check()` at the top of each iteration. Between iterations (during a long tool call), cancellation doesn't interrupt. This is a known limitation - a 60-second WebFetch can't be interrupted mid-call.

**Keystone implication:** Research agents doing large WebFetch calls on slow targets can hold threads for 60+ seconds. Set aggressive HTTP timeouts in WebFetch (10-15s), not at the agent level.

**Verdict: ADOPT** cooperative cancellation via cancel_check lambda. Add HTTP-level timeouts to all network tools separately.

---

## 4. Worktree Isolation (`multi_agent/subagent.py`)

```python
# multi_agent/subagent.py: _create_worktree()
def _create_worktree(self) -> tuple[str, str]:
    branch = f"agent-{uuid4().hex[:8]}"
    path = f"/tmp/nano-claude-worktree-{branch}"
    subprocess.run(["git", "worktree", "add", "-b", branch, path])
    return path, branch

def _remove_worktree(self, path: str, branch: str) -> None:
    subprocess.run(["git", "worktree", "remove", "--force", path])
    subprocess.run(["git", "branch", "-D", branch])
```

Git worktrees give each agent its own working directory with its own branch. Code changes made by one agent don't affect another agent's working files. The parent repo is shared, but each worktree has its own index.

**What this solves:** Multiple coding agents working on the same codebase simultaneously without clobbering each other's edits.

**What this does NOT solve for Keystone:**
- Agents still share the same process memory
- The global tool registry is shared (an agent could register a tool that affects other agents)
- Network calls are not isolated (no per-agent proxy)
- Agents can read each other's worktree directories (no filesystem permissions)
- Agents share environment variables (API keys, credentials visible to all)

**Verdict: SKIP** worktree isolation for Keystone. We need data isolation (prevent cross-contamination of research findings), not code isolation (prevent code edit conflicts). Worktrees solve the wrong problem.

---

## 5. Multi-Agent Tools (`multi_agent/tools.py`, 296 lines)

### Singleton Manager Pattern

```python
# multi_agent/tools.py
_agent_manager: SubAgentManager | None = None

def _get_manager(config: Config) -> SubAgentManager:
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = SubAgentManager(
            max_concurrent=config.max_concurrent_agents,
            max_depth=config.max_agent_depth
        )
    return _agent_manager
```

Lazy initialization, process-global singleton. One manager per process, shared across all tool calls.

**Keystone concern:** The singleton pattern means all agents share one thread pool. If L1 agents saturate the pool (e.g., 5 agents all blocking on WebFetch), L0 can't spawn more without waiting. For Keystone's parallel research workload, this needs a dedicated thread pool per pipeline layer, not a single global pool.

### Agent Tool (spawn interface)

```python
# multi_agent/tools.py: Agent tool
# params: {name, prompt, wait, model_override}
# wait=True: blocks until completion, returns result
# wait=False: returns task_id immediately, caller polls CheckAgentResult
```

The `wait` parameter is critical for controlling parallelism. L0 should use `wait=False` for all L1 spawns, then collect results via `CheckAgentResult` or by waiting on all futures simultaneously.

**Keystone mapping:** L0 orchestration loop:

```
1. Decompose RESEARCH.md into N subtasks
2. For each subtask: Agent(name=agent_type, prompt=subtask_prompt, wait=False)
   → returns task_id immediately
3. Wait for all task_ids: poll CheckAgentResult until all completed/failed
4. Aggregate results → L1.5 Deliberation
```

### SendMessage Tool

```python
# multi_agent/tools.py: SendMessage tool
# params: {task_id, message}
# Queues message to task._inbox
# Agent processes inbox messages after completing current work unit
```

Designed for the coordinator to inject additional context into a running agent. Use case: a running research agent discovers a relevant tangent; coordinator sends it a refined focus message.

**Keystone use case:** If L1 agent finds that a company has pending litigation (unexpected finding), L0 can SendMessage to a regulatory analyst agent with the litigation details. The agent processes the message after its current tool call completes.

**Gap:** SendMessage is fire-and-forget with no acknowledgment. The sender doesn't know if the message was processed. For Handoff Contracts, we need a request-reply pattern, not just one-way messaging.

### Config Stripping

```python
# multi_agent/tools.py: before passing config to child
child_config = copy(parent_config)
for key in list(vars(child_config).keys()):
    if key.startswith('_'):
        del child_config[key]  # strip private fields
```

Private fields (prefixed `_`) are stripped before passing config to sub-agents. This prevents internal orchestration state from leaking down the hierarchy.

**Keystone mapping:** API keys and credentials should be private fields (`_anthropic_api_key`, `_exa_api_key`). They inherit to children (needed for API calls) but can't be read by agent-level prompts. ⚠️ Uncertain: need to verify that stripping only affects logging/serialization, not actual config access.

---

## 6. Security Gap Analysis (CRITICAL)

### Current Isolation Model

```
Process
└── ThreadPoolExecutor
    ├── Thread 1: Agent A (market researcher)
    ├── Thread 2: Agent B (financial analyst)
    └── Thread 3: Agent C (competitive intelligence)
```

All three agents share:
- Same process memory (Python GIL protects writes, but reads are unguarded)
- Same global `_registry` dict (a tool registered by Agent A is visible to B and C)
- Same filesystem namespace (no directory restrictions)
- Same environment variables (API keys, tokens)
- Same network stack (no per-agent proxy or firewall)

### AgentLeak Assessment

The AgentLeak benchmark found 68.8% leakage in thread-isolated multi-agent systems. nano-claude-code's architecture falls squarely into this category. Specific leakage vectors:

1. **Global tool registry mutation:** An agent could call `register_tool()` with a malicious tool definition that overwrites a legitimate tool. All subsequent agents in the same process use the compromised tool.

2. **Shared filesystem reads:** Agent B can `Read` the working files of Agent A (no filesystem permissions enforcement). Research findings from Agent A are visible to Agent B before the deliberation phase, creating confirmation bias.

3. **Environment variable access:** `Bash(command="env")` returns all environment variables including API keys. All agents can execute this.

4. **Import-time side effects:** Python modules imported by one agent are cached in `sys.modules` and shared with all agents. A compromised dependency affects all agents.

### Keystone Isolation Requirements

For L1 research agents, the threat model is: agent B must not be able to read agent A's intermediate findings before the L1.5 Deliberation phase. This is not a security threat from malicious agents - it's a scientific validity requirement. Cross-contamination of research findings violates the anti-confirmatory research methodology.

Required isolation properties:
1. **Filesystem isolation:** Each agent writes to its own working directory; cannot read peer directories
2. **Tool registry isolation:** Each agent gets its own registry snapshot at spawn time; no shared mutable registry
3. **Memory isolation:** No shared Python objects between agent threads (findings, intermediate results)
4. **Sequenced disclosure:** All L1 agents complete before any agent can read peer results

### Remediation Architecture

**Option A: Process-Level Isolation (Recommended)**

```python
# Replace ThreadPoolExecutor with subprocess spawning
import subprocess, multiprocessing

def spawn_isolated(agent_def, prompt, working_dir) -> Future:
    return process_pool.submit(
        run_agent_subprocess,
        agent_def=agent_def,
        prompt=prompt,
        cwd=working_dir,  # per-agent working directory
        env=sanitized_env  # strip unnecessary credentials
    )
```

Each agent runs as a separate Python process. OS-level memory isolation. No shared global state. Filesystem isolation via separate working directories with `chmod 700`. IPC via files or queue (not shared memory).

Cost: ~100ms process spawn overhead per agent. Acceptable for research workloads where each agent runs 30-300 seconds.

**Option B: Thread-Level with Explicit Isolation Guards**

If subprocess overhead is unacceptable, enforce isolation within the thread model:
1. Copy `_registry` at spawn time → per-agent registry dict
2. Per-agent working directory with `os.chdir()` inside the thread
3. Lock on findings access: L1 agents write to isolated files; L1.5 reads all after all L1 complete
4. No `Bash` tool for L1 agents (prevents `env` leakage)

This is partial remediation. It reduces leakage but doesn't eliminate it. Process-level is the correct solution.

**Verdict: ADAPT** SubAgentManager to use process-level isolation for L1 research agents. Thread-level is acceptable for L2/L3/L4 where agents operate on already-aggregated data.

---

## 7. Coordinator Pattern (L0 as Orchestrator)

The parent agent in nano-claude-code is itself an agent running the same `agent.run()` loop. It uses the Agent tool to spawn children. This means the coordinator has full conversational context about all spawned tasks.

**Keystone mapping (L0 Specification Engine):**

L0 is a coordinator agent. Its loop:

```
1. Receive engagement brief
2. Load RESEARCH.md spec (or generate one via L0's specification tools)
3. Decompose into subtasks
4. Spawn L1 agents (one per subtask)
5. Monitor progress via CheckAgentResult
6. Collect completed results
7. Dispatch to L1.5 Deliberation agents with all L1 outputs
8. Collect deliberation outputs
9. Dispatch to L2 Content Structuring
10. Continue through L3 → L4 → iterate on low scores
```

Steps 3-10 are the outer DPVI loop. The inner DPVI loop runs inside each agent. The coordinator's conversation history contains the full lineage of the engagement run - this is the trajectory the META layer needs.

**Key insight:** The coordinator's message history IS the Observation Library entry for that engagement. Capture it at TurnDone and store structured.

---

## 8. L1.5 Deliberation via Fresh Agents

The multi-agent architecture supports L1.5 Deliberation cleanly:

```python
# L1.5 spawn pattern
for i, analyst_perspective in enumerate(deliberation_config.perspectives):
    # Each deliberation agent gets ALL L1 findings as context
    # But starts with fresh AgentState (no peer deliberation visible)
    prompt = f"""
    You are analyst {i+1} of {n_analysts}.
    
    L1 Research Findings:
    {aggregate_l1_results}
    
    Your analytical perspective: {analyst_perspective}
    
    Produce an independent structured analysis...
    """
    agent_def = load_agent_def("deliberation-analyst")
    task = manager.spawn(agent_def, prompt, config, depth=1)
```

Each deliberation agent receives the same L1 findings but approaches them from a different analytical lens. They cannot see each other's deliberation outputs (fresh state, no inbox messages during deliberation). After all deliberation agents complete, L0 aggregates the outputs via structured aggregation (not debate).

**This is NOT debate.** Debate requires agents to read and respond to peer positions - that would require SendMessage during the deliberation phase. Keystone's deliberation is independent parallel analysis followed by structured aggregation. Fresh state enforces independence.

**Verdict: ADOPT** the spawn pattern for L1.5 Deliberation. Use fresh AgentState + withheld peer outputs to enforce analytical independence.

---

## Verdict Summary

| Pattern | Source | Verdict | Keystone Layer |
|---|---|---|---|
| AgentDefinition from .md files | `subagent.py` | ADOPT | L0 dispatch, L1 specialization |
| Built-in agent types (reviewer pattern) | `subagent.py` | ADOPT | L4 Evaluator |
| SubAgentTask dataclass (extended) | `subagent.py` | ADOPT + extend | L0, L1, META |
| spawn() with config injection | `subagent.py` | ADOPT | L0 |
| Fresh AgentState per agent | `subagent.py` | ADOPT (non-negotiable) | L1, L1.5 |
| Cooperative cancellation | `subagent.py` | ADOPT | L1 |
| Depth limiting | `subagent.py` | ADOPT | L0 safety |
| Tool subsetting via AgentDefinition.tools | `subagent.py` | ADOPT | L1, L4 |
| ThreadPoolExecutor for isolation | `subagent.py` | ADAPT → process pool for L1 | L1 |
| Worktree isolation | `subagent.py` | SKIP | N/A |
| Singleton manager | `multi_agent/tools.py` | ADAPT → per-layer managers | L0, L1, L4 |
| wait=False async spawn | `multi_agent/tools.py` | ADOPT | L0 dispatch |
| SendMessage inbox | `multi_agent/tools.py` | ADAPT → add ACK | L0 → L1 |
| Config stripping for children | `multi_agent/tools.py` | ADOPT | All layers |
| Coordinator = agent with tools | architecture | ADOPT | L0 |
| L1.5 via fresh parallel agents | derived pattern | ADOPT | L1.5 |

---

## Critical Path for Implementation

In order of dependency:

1. **AgentDefinition + .md loading** → defines all agent specializations (no code dependency)
2. **get_tool_schemas() with filter** → enables per-agent tool subsetting (3-line change)
3. **Process-level spawn for L1** → resolves isolation gap before any L1 agents run research
4. **Per-agent working directories** → filesystem isolation alongside process isolation
5. **Extended SubAgentTask** → adds citation extraction + evaluator scoring fields
6. **L0 coordinator loop** → orchestrates the full DPVI pipeline
7. **L1.5 Deliberation spawn pattern** → derives directly from L0 coordinator once that works

Items 1-3 are blockers. Items 4-7 build on them. Do not run L1 research agents in thread-level isolation against real engagement data.
