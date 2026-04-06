# Deep Research Prompts: Claude Code Leak Analysis for Keystone Intelligence Engine

## Setup Instructions

### Step 1: Create Claude Project
Create a new project in Claude called "Keystone: Claude Code Leak Analysis"

### Step 2: Upload These 4 Files as Project Knowledge

| File | Why This File | Size |
|------|---------------|------|
| `audit/PHASE-1-IMPLEMENTATION-SPEC.md` | The 11 components being built, with schemas and acceptance criteria. Every agent needs this to map findings to specific build targets. | 26KB |
| `synthesis/PLAN-CHANGELOG.md` | The 17 research-backed changes already applied. Prevents agents from re-discovering settled decisions. | 22KB |
| `audit/SESSION-CONTEXT.md` | Quick orientation briefing. Settled decisions, build order, what NOT to build yet. | 4KB |
| `audit/GAP-TRIAGE.md` | 8 remaining gaps. If an agent's findings address a gap, it should flag it. | 9KB |

**Why not CAPSTONE-PLAN-v2.md?** At 135KB it would consume too much of the deep research agents' context budget. The four files above contain the actionable subset: what we're building (Phase 1 spec), what's already decided (changelog + session context), and what's still open (gaps). The prompts themselves embed the architectural detail each agent needs.

### Step 3: Paste Custom Instructions
Copy the contents of `reference/PROJECT-CUSTOM-INSTRUCTIONS.md` into the project's Custom Instructions field.

### Step 4: Run Each Prompt Below as a Separate Deep Research Conversation
Open 10 new conversations inside the project. Paste one prompt per conversation. Run all 10 in parallel.

### Step 5: Save Results
When each completes, copy the output into `reference/analysis/deep-research-NN.md` (01 through 10).

---

## Prompt 1: Agent Teams Architecture and Multi-Agent Coordination

On March 31, 2026, Anthropic accidentally leaked the full Claude Code source code (512K lines of TypeScript) via an npm packaging error in v2.1.88. The community has extensively analyzed the multi-agent "Agent Teams" feature, which was behind the feature flag CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS.

Research everything that has been discovered about Claude Code's Agent Teams architecture from the leaked source code analysis. Specifically:

1. **Execution models**: The three modes (fork, teammate, worktree). How does each work at the implementation level? What context does a forked subagent inherit vs. a teammate? How does worktree isolation use git worktrees for conflict-free file operations? What are the tradeoffs between modes?

2. **Coordination primitives**: How does the shared task list with dependency tracking work? What is the JSON inbox system for inter-agent messaging? How does file locking prevent race conditions? How does automatic unblocking work when dependent tasks complete?

3. **Team lead pattern**: How does the coordinator session orchestrate teammates? What decisions does it make about task assignment, load balancing, and when to spawn vs. reuse agents?

4. **Token economics**: How does fork-mode prompt caching work (byte-identical parent context inheritance)? What are the actual cost implications of spawning N agents? Community reports on token overhead vs. single session?

5. **Isolation guarantees**: What prevents data leakage between agents? How does this compare to the AgentLeak benchmark finding of 68.8% leakage in standard frameworks?

Search for: GitHub analysis repos (ComeOnOliver/claude-code-analysis), WaveSpeedAI architecture deep dive, Hacker News threads (47586778, 47609294), blog posts about agent teams, the claw-code (instructkr/claw-code) Rust/Python rewrite's multi-agent implementation, nano-claude-code (SafeRL-Lab/nano-claude-code) multi-agent module, community tutorials on setting up agent teams, and any Anthropic documentation or engineering blog posts about the feature.

**How to use the project files:** Reference PHASE-1-IMPLEMENTATION-SPEC.md Components #5 (Specification Engine dispatch), #7 (Research Agent pipeline), and #8 (CitationProcessor) to map agent teams patterns to our specific build targets. Reference SESSION-CONTEXT.md for settled decisions on isolation (filesystem-based, advisory locks, 3-5 tools per agent).

For every pattern you find, assess: ADOPT (use directly) / ADAPT (modify for research context, specify how) / SKIP (not applicable, say why). Map each finding to a specific component in our Phase 1 build order.

---

## Prompt 2: Context Engineering, Compaction, and Memory Architecture

On March 31, 2026, Anthropic accidentally leaked the full Claude Code source code (512K lines of TypeScript) via an npm packaging error. The leak revealed a sophisticated three-layer context compaction system and memory architecture.

Research everything discovered about Claude Code's context management from the leaked source analysis:

1. **Three-layer compaction system**: MicroCompact (local edits to cached content, zero API cost), AutoCompact (triggers at ~93.5% context utilization / 187K tokens on 200K model), Full Compact (complete conversation compression with selective file re-injection). How does each layer work at the implementation level? What triggers the transitions? What heuristics determine what to preserve vs. drop?

2. **Selective re-injection**: After compaction, how does the system decide which files/context to re-inject? Is there a relevance scoring mechanism? How does it prevent losing critical information during compression?

3. **Memory persistence**: How does MEMORY.md work? How does the system decide what to commit to persistent memory vs. keep in session? Is there a memory scanning mechanism?

4. **System prompt composition**: How is the system prompt assembled from CLAUDE.md + skills + agents + settings? What is the loading order? How large does the system prompt get and how does this affect available context?

5. **KAIROS and autoDream**: The unreleased daemon feature with "memory consolidation." How does autoDream merge observations, remove contradictions, and convert insights to facts? What is the implementation pattern?

Search for: WaveSpeedAI blog posts, Alex Kim's blog analysis, ComeOnOliver/claude-code-analysis repo, Hacker News discussions, The New Stack investigation, any analysis of compaction.ts or context management files, KAIROS/autoDream analysis, claw-code's Python reimplementation of compaction.

**How to use the project files:** Reference PHASE-1-IMPLEMENTATION-SPEC.md for how research agents are structured (they process tens of thousands of tokens during investigation but return 1-2 page condensed syntheses). Reference GAP-TRIAGE.md Gap #1 (calibration methodology) and Gap #6 (calibration drift detection) -- the memory/learning patterns may inform how we detect evaluator drift.

My research agents will conduct deep investigations potentially exceeding context windows. Understanding exactly how Anthropic manages context is critical for designing our agent session management. The KAIROS autoDream pattern is directly relevant to our META-layer Observation Library (which consolidates learnings into permanent skills). Map every finding to these specific use cases.

---

## Prompt 3: Tool System Design and Workflow-Level Tool Patterns

On March 31, 2026, Anthropic accidentally leaked the full Claude Code source code (512K lines of TypeScript). The leak revealed 50+ tools with a sophisticated registration, dispatch, and permission system.

Research everything discovered about Claude Code's tool system from the leaked source:

1. **Tool definition schema**: How are tools defined? What fields does each tool definition include (name, description, input schema, permissions, execution logic)? How are tool schemas exposed to the model?

2. **Tool dispatch and execution**: How does the system route a model's tool call to the correct handler? What is the execution sandboxing model? How are tool results formatted and returned to the model?

3. **Permission model**: How does the tool permission system work (allow, deny, ask)? How do permissions cascade from managed → project → user → local settings? How is sandboxing enforced structurally?

4. **Tool subsetting**: Is there evidence of per-agent tool specialization (giving different agents different tool subsets)? How is this implemented? Does it match Anthropic's finding that "a model loaded with 50 different tools performs worse than specialized agents with 5 focused tools"?

5. **Workflow-level tools**: Are there higher-level tools that compose multiple lower-level operations? How do tools support concise vs. detailed response modes?

6. **Tool registry**: How does the dynamic tool registry work? How are MCP tools integrated alongside built-in tools?

Search for: Analysis of tools.ts from the leaked source, tool_registry implementations in nano-claude-code and claw-code, Anthropic's documentation on tool definitions, any blog posts analyzing the tool system, Hacker News discussions about tool design patterns.

**How to use the project files:** Reference PHASE-1-IMPLEMENTATION-SPEC.md Component #4 (MCP gateway) for our tool integration architecture, and Component #7 (Research Agent pipeline) for per-agent tool assignment. The spec defines `assigned_tools` as a field on each research task (3-5 tools). Our search API stack is: Exa (semantic/category search), Brave (news/web), Firecrawl (full-page extraction), Tavily (RAG-optimized JSON). Cross-reference PLAN-CHANGELOG.md Change #10 (agent isolation strengthened) for the per-agent tool specialization requirement.

Map findings to our specific tool integration needs. I need workflow-level tools like research_company() that compose multiple API calls into a single agent-friendly interface.

---

## Prompt 4: The Harness Architecture -- System Prompt, Query Engine, and Orchestration Loop

On March 31, 2026, Anthropic accidentally leaked the full Claude Code source code (512K lines of TypeScript). A key finding from the Keystone project's research: "Same model: 17% vs 92% depending on harness." The leaked source reveals exactly how Anthropic builds the harness that achieves this.

Research everything discovered about Claude Code's harness architecture:

1. **System prompt construction**: How is the system prompt assembled? What goes into it (CLAUDE.md content, tool definitions, skills, memory, project context)? How large does it get? What is the ordering/priority of different context sources?

2. **Query Engine loop**: What is the main orchestration loop that processes user queries? How does it decide when to use tools vs. respond directly? How does it handle multi-step reasoning? What is the retry/error handling pattern?

3. **The 785KB main.tsx**: What is the architecture of the primary entry point? How does it bootstrap, set up context, and initiate the agent loop?

4. **Layered architecture**: Entry points → Bootstrap → Setup → UI layer → QueryEngine → Tool system → Services. How do these layers interact? What are the interfaces between them?

5. **Extended thinking / effort levels**: How do the four effort levels (low, medium, high, max) affect the system prompt, thinking budget, and model behavior? What changes between effort levels?

6. **Settings hierarchy**: How does managed → project → user → local settings cascade work in practice? What can each level override?

Search for: WaveSpeedAI architecture deep dive, analysis of main.tsx, ComeOnOliver/claude-code-analysis architectural breakdown, any analysis of the query engine or orchestration loop, Anthropic's documentation on effort levels and extended thinking, blog posts about how Claude Code constructs its system prompt.

**How to use the project files:** Reference PHASE-1-IMPLEMENTATION-SPEC.md Component #5 (Specification Engine) for our orchestration needs. Our pipeline is: L0 specification → L1 parallel research → CitationProcessor → L1.5 deliberation → L2 structuring → L4 evaluation → iterate. The harness must manage this multi-stage flow with handoff contracts at each boundary. Reference PLAN-CHANGELOG.md Change #11 (orchestration architecture specified: PydanticAI + Temporal + MCP gateway) for our chosen stack.

Understanding how Anthropic built their orchestration loop is the single highest-value architectural insight available. Map every finding to our pipeline orchestration needs. Specifically assess whether the Query Engine pattern maps to our DPVI loop.

---

## Prompt 5: Evaluation, Quality Gates, and Hooks System

On March 31, 2026, Anthropic accidentally leaked the full Claude Code source code (512K lines of TypeScript). The leak revealed a hooks system with 18+ events and various quality enforcement mechanisms.

Research everything discovered about Claude Code's evaluation and quality patterns:

1. **Hooks system**: What are the 18+ hook events? How do pre/post command hooks work? Can hooks block or modify tool execution? How are hooks configured?

2. **Quality enforcement**: Does Claude Code have any built-in evaluation or quality checking mechanisms? How does it validate tool outputs? How does it handle tool failures?

3. **Structural enforcement patterns**: What quality requirements are enforced structurally (architecture prevents bad outcomes) vs. through prompt instructions (model chooses to comply)? This maps to our core conviction: "Structure over intent. Quality enforced by architecture, not prompt compliance. Instructions drift ~40%."

4. **Error handling and retry logic**: How does Claude Code handle failures at each layer? What is the retry strategy? How does it degrade gracefully?

5. **The anti-distillation mechanisms**: Fake tools injection, frustration detection, native client attestation. What do these reveal about Anthropic's approach to structural enforcement of system-level properties?

6. **Undercover mode**: How does this work? What does it reveal about commit/output metadata management?

Search for: Alex Kim's blog analysis (fake tools, frustration regexes, undercover mode), analysis of hooks system, ComeOnOliver/claude-code-analysis, WaveSpeedAI analysis, Hacker News thread 47586778, any analysis of quality gates or validation in the leaked source.

**How to use the project files:** Reference PHASE-1-IMPLEMENTATION-SPEC.md Component #6 (Evaluator stack Layers 1-3) for our evaluation architecture. We're building: Layer 1 (deterministic verification via FActScore), Layer 2 (citation binary gate via CrossRef/Semantic Scholar), Layer 3 (Prometheus 2 rubric scoring, 10 dimensions, one prompt per dimension). Reference PLAN-CHANGELOG.md Changes #4-8 for the full evaluator specification. The hooks pattern is particularly interesting for implementing quality gates at handoff contract boundaries.

Map findings to our 5-layer evaluation stack. Assess whether Claude Code's hooks system can be adapted for sprint contract enforcement at pipeline boundaries.

---

## Prompt 6: MCP (Model Context Protocol) Implementation and Gateway Patterns

On March 31, 2026, Anthropic accidentally leaked the full Claude Code source code (512K lines of TypeScript). MCP is Anthropic's protocol for tool integration, and the leaked source reveals the production implementation.

Research everything discovered about Claude Code's MCP implementation:

1. **MCP client architecture**: How does Claude Code connect to MCP servers? What is the client implementation pattern? How does it handle server discovery, connection lifecycle, and reconnection?

2. **MCP tool registration**: How are MCP-provided tools registered alongside built-in tools? How does the tool search/deferred loading work for MCP tools? How are MCP tool schemas translated to the model's tool format?

3. **MCP server configuration**: How are MCP servers configured (mcp.json, project settings, etc.)? What configuration options exist (transport, args, env)?

4. **Gateway pattern**: Is there evidence of a gateway architecture that routes between multiple MCP servers? How does Claude Code handle multiple MCP servers providing different tool sets?

5. **Security model**: How are MCP server permissions managed? What prevents a malicious MCP server from accessing unauthorized resources?

6. **Community MCP implementations**: What MCP servers have been built by the community for research-relevant use cases? Specifically search for MCP servers for: Exa, Brave Search, Firecrawl, Tavily, EdgarTools/SEC filings, CrossRef, Semantic Scholar, OpenAlex, academic paper search, financial data.

Search for: Anthropic's MCP documentation, analysis of MCP implementation in the leaked source, nano-claude-code's mcp/ directory analysis, claw-code's MCP implementation, community-built MCP servers for research tools, any blog posts about building MCP servers or gateways, the MCP registry/marketplace.

**How to use the project files:** Reference PHASE-1-IMPLEMENTATION-SPEC.md Component #4 (MCP gateway) directly. Our spec calls for: "MCP gateway that routes tool calls to appropriate providers, handles rate limiting, circuit breaking, and per-agent tool subsetting." We need to integrate 8 external services (Exa, Brave, Firecrawl, Tavily, EdgarTools, CrossRef, Semantic Scholar, OpenAlex). Reference PLAN-CHANGELOG.md Change #11 (custom orchestration with MCP for tools) and Change #12 (retrieval architecture with hybrid search).

This is one of the first Phase 1 components we build (no dependencies, can start immediately). Map every finding to our specific gateway needs. If community MCP servers already exist for any of our 8 target services, that's a direct build-vs-integrate decision.

---

## Prompt 7: Self-Improvement, Learning Loops, and Knowledge Accumulation

On March 31, 2026, Anthropic accidentally leaked the full Claude Code source code (512K lines of TypeScript). The leak revealed KAIROS (an always-on daemon with "autoDream" memory consolidation) and patterns for persistent learning.

Research everything discovered about Claude Code's self-improvement and knowledge accumulation patterns:

1. **KAIROS and autoDream**: The unreleased daemon feature with 150+ feature flag references. How does autoDream work? It reportedly "merges disparate observations, removes logical contradictions, converts vague insights to absolute facts." What is the implementation pattern? How does it decide what to consolidate? What data structures does it use?

2. **MEMORY.md and persistent memory**: How does Claude Code accumulate knowledge across sessions? What format does memory use? How is relevance determined for memory retrieval? How does scanning work?

3. **The instinct-to-skill pipeline**: ECC (everything-claude-code, 112K stars) reportedly captures every tool call at 100% reliability and promotes validated patterns to skills. Is this pattern visible in the leaked source? How does it work?

4. **Trajectory storage**: Is there evidence of decision logging (what was tried, what worked, what failed) beyond simple conversation history?

5. **Prompt evolution**: Any evidence of prompt self-modification or A/B testing of different prompt variants?

6. **Saturation mechanisms**: Any patterns for escaping improvement plateaus after initial gains diminish?

Search for: WaveSpeedAI analysis of KAIROS and Buddy hidden features, The Information newsletter on KAIROS, Deep Learning AI coverage, analysis of memory systems in leaked source, ECC (everything-claude-code) repository analysis, any blog posts about Claude Code's learning mechanisms.

**How to use the project files:** Reference PLAN-CHANGELOG.md Change #9 (Observation Library expanded from Rejection Library) for our self-improvement architecture. Our design captures all tool call outcomes (successes and failures), uses a three-category taxonomy (structural/analytical/judgment failures), and includes five saturation-breaking mechanisms. Reference GAP-TRIAGE.md Gap #6 (evaluator calibration drift detection) -- KAIROS-style background consolidation could inform drift detection.

KAIROS's autoDream is essentially doing what our Observation Library's instinct-to-skill pipeline needs to do: merge observations, remove contradictions, consolidate into permanent knowledge. Extract maximum implementation detail. This is the single most relevant leaked feature for our self-improvement architecture.

---

## Prompt 8: Cost Optimization -- Prompt Caching, Model Mixing, and Token Economics

On March 31, 2026, Anthropic accidentally leaked the full Claude Code source code (512K lines of TypeScript). The leak revealed how Anthropic optimizes costs in their own agent system.

Research everything discovered about Claude Code's cost optimization patterns:

1. **Prompt caching**: How does Claude Code use prompt caching? How does fork-mode inheritance enable cheap subagent spawning (byte-identical parent context)? What are the cache invalidation rules? What is the cache TTL?

2. **Model mixing strategy**: How does Claude Code select between Opus, Sonnet, and Haiku for different tasks? What heuristics drive model selection? Is there automatic model routing based on task complexity?

3. **Token usage patterns**: Community reports on actual token consumption for various task types. What percentage goes to tool calls vs. reasoning vs. output? How does this compare to the finding that "verification consumes 72% of tokens"?

4. **Batch API usage**: Any evidence of batching multiple requests to reduce costs? How does this interact with real-time vs. background processing?

5. **Context optimization**: How does the compaction system reduce token costs? What are the measured savings from MicroCompact vs. AutoCompact vs. Full Compact?

6. **Community cost analysis**: What have community members reported about actual costs of running Claude Code agent teams vs. single sessions? Token overhead of multi-agent vs. sequential?

Search for: Community blog posts about Claude Code token usage, analysis of model selection in leaked source, claw-code's provider implementation, cost comparison analyses, Anthropic's documentation on prompt caching and batch API, any quantitative data on agent teams token overhead.

**How to use the project files:** Reference PLAN-CHANGELOG.md Change #16 (validated cost model: $12-$100/engagement) and Change #10 (model mixing: Opus for L0/L4, Sonnet for L1, Haiku for extraction). Reference GAP-TRIAGE.md Gap #8 (rate limit management at 15-50 parallel agents). Reference SESSION-CONTEXT.md for the decision to run on Claude Max with minimal external APIs.

I need specific numbers and ratios, not general guidance. The fork-mode caching pattern could dramatically reduce the cost of spawning 15-50 parallel research agents. Assess: does the leaked architecture change our cost model assumptions?

---

## Prompt 9: The Full Community Analysis Landscape -- What Has Been Discovered and Built

On March 31, 2026, Anthropic accidentally leaked the full Claude Code source code (512K lines of TypeScript). Within days, the community produced multiple rewrites, analysis repos, and derivative projects.

Research the full landscape of community response to the Claude Code leak:

1. **Analysis repositories**: ComeOnOliver/claude-code-analysis, any other systematic reverse-engineering efforts. What are the most important architectural findings not covered in the other 9 prompts?

2. **Rewrites and their innovations**: claw-code (Rust/Python, 100K+ stars), nano-claude-code (Python, research-focused), claurst (Rust), claw-code-agent (Python-only). What did each rewrite change or improve vs. the original? What architectural decisions did the rewrite authors make differently?

3. **Derivative projects**: Shipyard.build (multi-agent orchestration platform), ruflo (enterprise multi-agent swarm), any other projects built on top of the leaked architecture insights. What patterns did they adopt?

4. **44 gated features**: The New Stack reported 44 features behind feature flags. What are they? Which ones are relevant to multi-agent research systems?

5. **Security findings**: Anti-distillation mechanisms, the malware campaigns exploiting the leak, undercover mode implications. What do these reveal about production agent system security?

6. **Hacker News and Twitter/X discussions**: What did experienced practitioners identify as the most significant findings? What surprised the community? What was the consensus on the quality of Anthropic's engineering?

Search for: All GitHub repos related to the Claude Code leak, Hacker News threads (multiple), Twitter/X threads from AI practitioners, blog posts from WaveSpeedAI, Alex Kim, The New Stack, Medium, Dev.to, any community forums discussing the leak.

**How to use the project files:** Reference PHASE-1-IMPLEMENTATION-SPEC.md for the full list of components being built. For every significant community finding, assess whether it maps to any of our 11 Phase 1 components. Reference GAP-TRIAGE.md for the 8 open gaps -- community findings may address gaps we haven't resolved.

This is the sweep prompt -- find everything the other 9 prompts might miss. Prioritize findings relevant to building production multi-agent AI systems for research and analysis.

---

## Prompt 10: Anthropic's Agent SDK, Claude Code Official Architecture, and Production Patterns

Research Anthropic's officially released tools and frameworks for building multi-agent systems, SEPARATE from the leak. The leak revealed internals, but Anthropic has also published official documentation, engineering blog posts, and the Agent SDK.

Research:

1. **Claude Agent SDK**: What is it? How does it work? Python and TypeScript implementations. How does it compare to the leaked internals? What patterns does it expose officially that the leak also revealed?

2. **Anthropic's engineering blog posts on multi-agent systems**: The "Building effective agents" post, "Context engineering" post, "Harness design" post, "Effective harnesses for long-running agents" post. What specific architectural guidance do they provide?

3. **Official Claude Code architecture**: What has Anthropic officially documented about how Claude Code works? How does the official documentation compare to what the leak revealed?

4. **Production multi-agent patterns from Anthropic**: The pattern where Opus leads and Sonnet subagents execute. The 90.2% improvement finding. The "model loaded with 50 tools performs worse than specialized agents with 5" finding. How are these patterns meant to be implemented?

5. **PydanticAI, Temporal, and MCP as orchestration stack**: Our Phase 1 spec calls for PydanticAI for type-safe agent contracts, Temporal for durable execution, and MCP for tool integration. What is the current state of these tools? How do they integrate? Are there production examples of this stack?

6. **The relationship between Claude Code and the Agent SDK**: Can Claude Code itself be used as a building block for multi-agent systems (not just as a dev tool)? Could we build on top of Claude Code's subagent spawning rather than implementing our own orchestration?

Search for: Anthropic's official documentation (docs.anthropic.com, docs.claude.com), Claude Agent SDK GitHub repo, Anthropic engineering blog, PydanticAI documentation and GitHub, Temporal documentation, community projects using PydanticAI + Claude, any production multi-agent system case studies using Anthropic's tools.

**How to use the project files:** Reference PLAN-CHANGELOG.md Change #11 (custom orchestration: PydanticAI + Temporal + MCP) and the rationale. Reference SESSION-CONTEXT.md for the settled decision on custom orchestration vs. framework adoption. Reference PHASE-1-IMPLEMENTATION-SPEC.md for the full component list to assess whether the Agent SDK changes our build-vs-integrate calculus for any component.

This prompt bridges the gap between "what Anthropic does internally" (the leak) and "what Anthropic recommends for builders" (official tools). The critical question: should we build on the Agent SDK, use patterns from the leak, adapt Claude Code's subagent system directly, or combine approaches? Assess with specific tradeoffs for our use case.

---

## Post-Research Next Steps

After all 10 complete:
1. Save results to `reference/analysis/deep-research-01.md` through `deep-research-10.md`
2. A synthesis session will cross-reference these findings with the nano-claude-code repo analysis (running overnight in Claude Code)
3. Combined findings will inform final architecture decisions before Phase 1 build begins
