# nano-claude-code: Memory and Context Management Analysis

**Source:** `reference/nano-claude-code/memory/`, `reference/nano-claude-code/compaction.py`, `reference/nano-claude-code/context.py`
**Scope:** Memory persistence, context assembly, compaction, and JIT loading -- highest priority analysis for Keystone's Observation Library and trajectory storage
**Date:** 2026-04-05
**Priority:** HIGHEST -- this module directly determines whether the META layer is buildable

---

## Summary Verdict

The memory system provides the persistence mechanism Keystone needs but not the structure. The file-based storage pattern (YAML frontmatter + markdown body) is the right foundation for Observation Library entries. The AI-powered relevance search is the correct JIT loading pattern. The two-layer compaction is necessary infrastructure for L1 research agents. The critical gap is compaction without selective re-injection: high-value research findings can be silently discarded during context summarization. That gap must be closed before the system is safe for long research sessions.

---

## Module Map

| File | Lines | Purpose |
|---|---|---|
| `memory/types.py` | 87 | Memory type taxonomy, WHAT_NOT_TO_SAVE, system prompt guidance |
| `memory/store.py` | 224 | Dual-scope file storage, MEMORY.md index, save/search |
| `memory/context.py` | 222 | System prompt injection, truncation, AI-powered relevance |
| `memory/scan.py` | 145 | Lightweight frontmatter-only scanning, staleness detection |
| `memory/tools.py` | 217 | MemorySave, MemoryDelete, MemorySearch, MemoryList tools |
| `compaction.py` | 197 | Two-layer context window management (snip + LLM summary) |
| `context.py` | 166 | System prompt assembly including memory injection |

---

## 1. Memory Type Taxonomy (`memory/types.py`, lines 1-87)

### Four Memory Types

```python
# memory/types.py
class MemoryType(Enum):
    USER = "user"           # preferences, personal working style
    FEEDBACK = "feedback"   # corrections and confirmations
    PROJECT = "project"     # engagement-specific context
    REFERENCE = "reference" # external facts, frameworks, data
```

The taxonomy is deliberately narrow. nano-claude-code resists saving operational state as memory. ✅ Verified from source.

### WHAT_NOT_TO_SAVE

```python
# memory/types.py: WHAT_NOT_TO_SAVE
# Excludes:
# - Code patterns or snippets
# - Git history or commit messages
# - Debugging solutions (ephemeral)
# - CLAUDE.md content (already in system prompt)
# - Ephemeral task state
```

The exclusions encode a principle: memory is for patterns that generalize, not artifacts that are session-specific. This aligns precisely with Keystone's "save patterns, not code" conviction. ✅ Verified from source.

### MEMORY_SYSTEM_PROMPT

Full guidance injected into the agent's system prompt explaining when and how to use memory. The guidance ships with the system -- it is not optional or configurable. 🟡 Inferred: this is intentional to prevent agents from ignoring the memory system.

**Keystone mapping (META layer):** The MEMORY_SYSTEM_PROMPT pattern is the right approach for injecting Observation Library guidance into each agent's context. Rather than hoping agents know when to consult the library, the guidance is structural -- it ships in every system prompt.

---

## 2. Dual-Scope Storage (`memory/store.py`, lines 1-224)

### Scope Model

```python
# memory/store.py
# User scope: ~/.nano_claude/memory/  (global, persists across engagements)
# Project scope: .nano_claude/memory/ (per-engagement, scoped to cwd)
```

Two independent scopes with no merging conflicts. Project memories override nothing -- both scopes are read and injected. ✅ Verified from source.

### MemoryEntry Dataclass

```python
# memory/store.py
@dataclass
class MemoryEntry:
    name: str
    description: str
    type: MemoryType
    content: str
    file_path: Path
    created: datetime
    scope: str  # "user" or "project"
```

### File Format

```
---
name: client-risk-appetite-framework
description: How Keystone frames risk tolerance for PE clients
type: reference
created: 2026-04-05T10:22:00
---

## Pattern

PE clients at Keystone consistently prioritize...
[markdown body]
```

YAML frontmatter for structured metadata; markdown body for rich content. This format is human-readable, git-diffable, and LLM-parseable. ✅ Verified pattern.

### MEMORY.md Index

```python
# memory/store.py: save_memory()
# After writing entry file, rebuilds MEMORY.md:
# - [name](file.md) - description
# One line per entry, max 200 lines, max 25,000 bytes
# Older entries dropped when index exceeds limits
```

The index is the quick-reference manifest injected into system prompts. Individual entry files are loaded on demand. The index gives agents a map of what exists without loading full content. ✅ Verified from source.

Limits: `MAX_INDEX_LINES = 200`, `MAX_INDEX_BYTES = 25,000`. At 200 entries this starts dropping older observations. For Keystone's Observation Library growing over months of engagements, this limit will be hit. We need configurable limits or a tiered index.

### _slugify()

```python
# memory/store.py: _slugify(name)
# Lowercases, replaces spaces and special chars with hyphens
# Truncates to 60 characters
# Returns filesystem-safe filename
```

Max 60 chars means long observation names get truncated. Not a critical issue but observation names should be kept concise. ✅ Verified from source.

---

## 3. Context Injection and AI-Powered Relevance (`memory/context.py`, lines 1-222)

### get_memory_context()

```python
# memory/context.py: get_memory_context()
# Loads user MEMORY.md + project MEMORY.md
# Concatenates with section headers
# Truncates with truncate_index_content() before returning
# Result is injected at end of system prompt
```

The full index (up to truncation limits) is injected on every turn. Individual entries are not loaded unless explicitly requested. Agents read the index and decide what to fetch. ✅ Verified from source.

### truncate_index_content()

```python
# memory/context.py: truncate_index_content()
# Enforces MAX_INDEX_LINES and MAX_INDEX_BYTES
# Matches Claude Code behavior exactly
# Truncation is hard cutoff at line/byte limit
```

Hard cutoff. Older entries fall off the end. No relevance-based pruning at the index level. ⚠️ For a large Observation Library, this means older (potentially still relevant) observations become invisible unless explicitly searched.

### find_relevant_memories() -- Two Strategies

**Strategy 1: Keyword match (default)**

```python
# memory/context.py: find_relevant_memories(query, use_ai=False)
# Loads all memory files
# Case-insensitive substring match on name + description + content
# Sorted by recency (most recent first)
# Returns top N matches
```

Fast, zero API cost, zero latency. Sufficient for simple retrieval. Fails on semantic queries where the terminology doesn't match stored names. ✅ Verified from source.

**Strategy 2: AI-powered ranking (use_ai=True)**

```python
# memory/context.py: find_relevant_memories(query, use_ai=True)
# Sends candidate manifest to LLM
# Asks for JSON response: {"indices": [2, 0, 4, ...]}
# Returns candidates in ranked order
# Falls back to keyword match on any error
```

The LLM receives a manifest (names + descriptions of candidates) and returns a ranked index list. This is a two-stage approach: keyword match generates candidates, LLM reranks by semantic relevance. The fallback on error is critical for production reliability. ✅ Verified from source.

**Keystone mapping (JIT Context Loading, L1):** This two-stage pattern is the correct implementation of JIT context loading for Keystone's research agents. Before each major research subtask, the agent queries the Observation Library with `use_ai=True`, gets semantically relevant observations, and loads those entries into working context. Cost is one small LLM call per retrieval -- acceptable given research agent session costs.

---

## 4. Memory Scanner (`memory/scan.py`, lines 1-145)

### Lightweight Frontmatter Scan

```python
# memory/scan.py: MemoryHeader
@dataclass
class MemoryHeader:
    filename: str
    file_path: Path
    mtime_s: float
    description: str
    type: str
    scope: str
```

Reads only the first 30 lines of each file to extract frontmatter. Does not load the markdown body. This makes index building fast even with 200 entries. ✅ Verified from source.

### Staleness Detection

```python
# memory/scan.py: memory_freshness_text()
# For memories > 1 day old:
# "Note: this memory is N days old. Claims about code behavior
#  or file:line citations may be outdated."
```

Staleness warnings are surfaced at retrieval time, not write time. The system does not automatically invalidate stale memories -- it warns the consuming agent. ✅ Verified from source.

**Keystone mapping (Observation Library):** The staleness warning pattern is essential for the Observation Library. An observation recorded during an engagement six months ago about a client's financial position may be superseded. The warning surfaces this without requiring automated invalidation logic. For Keystone, the threshold should be configurable per memory type: `reference` memories stale after 30 days, `feedback` memories never stale.

---

## 5. Compaction (`compaction.py`, lines 1-197)

Covered partially in `01-core-architecture.md`. Expanded here with specific research-agent implications.

### Layer 1: Rule-Based Snipping

```python
# compaction.py: snip_old_tool_results()
# For tool result messages outside the last 6 turns:
#   Preserve first 50% + last 25% of content
#   Insert "[...N chars snipped...]" marker
# No API call, no latency cost
```

The 50%/25% heuristic works for conversational tool output (file reads, grep results). For research agents, the concern is different: a tool result containing a critical statistic ("EBITDA margin declined from 34% to 28% per 10-K, p.47") is exactly the kind of middle content that gets snipped. ⚠️ The snipping heuristic is not claim-aware. It has no concept of "this sentence is a key finding."

### Layer 2: LLM-Driven Summarization

```python
# compaction.py: compact_messages()
# Split at 70/30 ratio (old portion / recent portion)
# LLM summarizes old 70%
# Recent 30% kept verbatim
# Old messages replaced with summary + acknowledgment pair
```

The LLM summarizer is asked to preserve key decisions and context. There is no explicit instruction to preserve specific claim types (statistics, source URLs, contradictions). The summarizer will make its own judgment about what matters. ⚠️ This is not safe for research contexts without modification.

### Trigger Logic

```python
# agent.py: maybe_compact()
# estimate_tokens = len(all_content) / 3.5
# if estimated_tokens > context_limit * 0.70:
#     try snip first
#     if still > 70%: run LLM summarization
```

The 3.5 chars-per-token heuristic is conservative (Claude averages closer to 4). This means compaction triggers slightly earlier than necessary. For research agents with long tool outputs, this is acceptable -- better to compact early than to hit the hard context limit. ✅ Verified heuristic from source.

### CRITICAL GAP: No Selective Re-injection

After LLM summarization, specific claim-level findings can be lost if the summarizer does not judge them important. There is no mechanism to:

1. Extract key findings before compaction
2. Pin those findings as a structured artifact
3. Re-inject the artifact after compaction as a persistent system message

This gap is acceptable for a coding assistant (code is in files, not in context). It is unacceptable for a research agent where the "artifact" is the finding itself, not a file on disk.

**Required extension:** Before Layer 2 compaction, run a findings extraction pass:

```python
# Pseudocode: research-agent compaction extension
def extract_key_findings(messages: list[dict]) -> list[Finding]:
    # Ask LLM to extract: statistics with sources, contradictions, key claims
    # Returns structured findings with confidence scores
    # These are persisted as memory entries, not just held in context

def compact_with_findings_preservation(state: AgentState):
    findings = extract_key_findings(state.messages)
    persist_to_memory(findings)               # write to Observation Library
    compact_messages(state)                   # standard compaction
    inject_findings_summary(state, findings)  # re-inject as pinned message
```

The findings extraction itself requires an LLM call. Total cost for research compaction: 2 LLM calls (findings extraction + summarization) vs. 1 for standard compaction. The cost is justified given that research findings are the entire product of the pipeline. ✅ Verified requirement from CAPSTONE-PLAN-v2.md claim-level handoff specs.

---

## 6. System Prompt Assembly (`context.py`, lines 1-166)

```python
# context.py: build_system_prompt()
# Assembly order:
# 1. Base template (~95 lines)
# 2. Git info (branch, recent commits, status)
# 3. CLAUDE.md (walk up 10 parent dirs, load first match)
# 4. Memory context (user MEMORY.md + project MEMORY.md)
```

Memory is injected last -- lowest priority in the system prompt. This means if the system prompt approaches token limits, memory context is the first to be truncated by the model's own attention mechanisms. ⚠️ For Keystone, Observation Library context should be injected earlier (after RESEARCH.md, before boilerplate tool descriptions) so it receives appropriate attention weight.

---

## Keystone Layer Connections

### META Layer -- Observation Library Implementation

The memory system provides three of the four components needed for the Observation Library:

| Observation Library Need | nano-claude-code Equivalent | Gap |
|---|---|---|
| Entry persistence | `memory/store.py` file storage | Need structured fields: pattern_name, evidence_quality, constraint_or_reinforcement |
| Entry retrieval | `find_relevant_memories(use_ai=True)` | None -- this is the correct pattern |
| Index for quick-reference | MEMORY.md | Need configurable index limits per scope |
| Staleness detection | `memory/scan.py` freshness text | Need configurable thresholds per memory type |
| Instinct → skill promotion | Not present | Must build: promotion mechanism from temporary → permanent |
| Evidence quality tagging | Not present | Must add: ✅/🟡/⚠️/❌ markers in frontmatter |

The Observation Library entry schema extends MemoryEntry:

```yaml
---
name: pe-client-ebitda-framing
description: PE clients weight EBITDA margin trajectory over absolute level
type: feedback
evidence_quality: verified          # verified | credible | claimed | stale
constraint_or_reinforcement: constraint
pattern_source: engagement-acme-2026
created: 2026-04-05T10:22:00
promoted_from_instinct: true
promotion_date: 2026-04-12T14:00:00
---

## Pattern

When presenting financial analysis to PE clients, frame margin trends as...

## Evidence

Observed in 3 consecutive engagements (Acme, Beta, Gamma). Client feedback
consistently flagged absolute EBITDA as "not the number we care about."

## Constraint

Always lead with margin trajectory (current vs. prior period vs. sector median)
before presenting absolute EBITDA figures.

## How to Apply

In L3 generation, financial exhibit headers should use "Margin Trajectory"
not "EBITDA Summary."
```

### META Layer -- Trajectory Storage

nano-claude-code has no trajectory storage. The memory system can serve as a lightweight trajectory log if we treat each turn's key events as memory entries. A better approach is parallel structured logging:

```
.nano_claude/memory/          ← Pattern observations (MemoryEntry format)
.nano_claude/trajectories/    ← Execution logs (JSON, per-engagement)
  acme-2026-04-05/
    L1_agent_1.jsonl          ← Tool calls, latency, outputs per turn
    L4_evaluator.jsonl        ← Evaluation scores per dimension
    META_summary.json         ← Aggregated stats for self-improvement
```

The memory system handles the qualitative pattern layer. A separate trajectory store handles the quantitative execution layer. ✅ This matches the two-tier architecture described in CAPSTONE-PLAN-v2.md.

### L1 -- Research Agent Session Management

Compaction is not optional for L1 agents. A research agent processing:
- 5 SEC filings (10-K: ~80K tokens each)
- 10 earnings call transcripts (~15K tokens each)
- 20 web sources via Firecrawl (~5K tokens each)

...will generate 600K+ tokens of tool output in a single session. The two-layer compaction is the minimum viable approach. The selective re-injection extension is required, not optional.

**Deployment note:** L1 research agents should run with extended context (claude-opus-4-5 at 200K tokens). Even at 200K, compaction will trigger for deep research tasks. ⚠️ Budget for compaction costs as a fixed overhead per L1 agent session.

### L1 -- JIT Context Loading Pattern

The find_relevant_memories() pattern maps directly to the JIT context loading described in CAPSTONE-PLAN-v2.md:

```python
# JIT context loading at L1 research agent startup
async def load_jit_context(research_question: str, engagement: str) -> str:
    # 1. Load global Observation Library entries relevant to question
    global_obs = find_relevant_memories(research_question, scope="user", use_ai=True)
    # 2. Load engagement-specific context
    engagement_ctx = find_relevant_memories(research_question, scope="project", use_ai=True)
    # 3. Load RESEARCH.md spec for this engagement
    research_spec = load_research_md(engagement)
    # 4. Compose agent system prompt with all three layers
    return compose_system_prompt(research_spec, global_obs, engagement_ctx)
```

The dual-scope memory maps naturally to global observations (user scope) vs. per-engagement context (project scope). ✅ Direct structural match.

### L4 -- Evaluator Memory

The Evaluator should write feedback memories after each evaluation pass. This creates the feedback loop from L4 back to META:

```
L4 Evaluator marks task REJECTED with reason →
L4 writes feedback memory: "Output failed dimension 7 (citation integrity)
  because claim sourced to 'industry report' without URL" →
META Observation Library promotes this to constraint after 3 occurrences →
L1 agents load this constraint via JIT context on next engagement
```

This is the instinct-to-skill pipeline materialized as code. nano-claude-code has the storage (memory types, feedback type) but not the promotion trigger. We must build the trigger.

---

## Gap Analysis

| Gap | Severity | Fix |
|---|---|---|
| No selective re-injection after compaction | CRITICAL -- findings can be lost | Build findings extraction pass before Layer 2 |
| No instinct → skill promotion mechanism | HIGH -- Observation Library stays flat | Build promotion trigger: N occurrences → permanent constraint |
| No evidence quality tagging in frontmatter | HIGH -- all observations treated equally | Add evidence_quality field to MemoryEntry schema |
| Index limit (200 entries) | MEDIUM -- hits ceiling over months | Make MAX_INDEX_LINES configurable per scope |
| Memory injected last in system prompt | MEDIUM -- may be attention-deprioritized | Move Observation Library context to earlier injection position |
| No trajectory storage | HIGH -- META cannot self-improve without it | Build parallel JSONL trajectory store alongside memory store |
| Staleness threshold not configurable | LOW | Add per-type thresholds to config |
| No automatic promotion from temporary → permanent | HIGH | Build: metadata field `promoted: false`, promotion trigger |

---

## Verdict Summary

| Component | Source | Verdict | Keystone Layer |
|---|---|---|---|
| Dual-scope memory (user/project) | `memory/store.py` | ADOPT -- maps to global observations vs. per-engagement | META, L1 |
| MemoryEntry with YAML frontmatter | `memory/store.py` | ADAPT -- add evidence_quality, constraint_or_reinforcement, promotion fields | META |
| MEMORY.md index with truncation | `memory/store.py` | ADOPT -- quick-reference manifest for system prompt injection | META, L1 |
| AI-powered relevance search | `memory/context.py` | ADOPT -- correct JIT context loading pattern | L1, META |
| Keyword + AI hybrid search | `memory/context.py` | ADOPT -- keyword for speed, AI for semantic precision | L1 |
| Staleness warnings | `memory/scan.py` | ADOPT -- essential for Observation Library entries | META |
| Two-layer compaction | `compaction.py` | ADOPT as baseline -- add selective re-injection layer | L1 |
| Snip heuristic (50% + 25%) | `compaction.py` | ADOPT for tool output; flag as insufficient for claim-bearing content | L1 |
| 70% trigger threshold | `compaction.py` | ADOPT | L1 |
| MEMORY_SYSTEM_PROMPT injection | `memory/types.py` | ADOPT -- structural guidance beats optional usage | All agents |
| Memory type taxonomy | `memory/types.py` | ADAPT -- add observation-specific types | META |
| No trajectory storage | All modules | BUILD -- parallel JSONL store, not memory store extension | META |
| No instinct → skill promotion | All modules | BUILD from scratch | META |
| Selective re-injection post-compaction | Not present | BUILD -- findings extraction pass before Layer 2 | L1 |
