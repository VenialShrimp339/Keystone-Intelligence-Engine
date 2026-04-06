# Orchestration frameworks for the Keystone Intelligence Engine

**Build custom orchestration, but steal patterns aggressively.** No existing framework natively supports Keystone's combination of strict agent isolation, reject/regenerate evaluation loops, handoff contracts, and file-system-as-state coordination. The honest recommendation after deep evaluation of eight frameworks, four protocols, and extensive failure-mode research: use PydanticAI for agent definition and type-safe handoff contracts, MCP for tool integration, and custom orchestration logic for the pipeline itself — informed heavily by patterns from LangGraph, Google ADK, and Anthropic's own multi-agent architecture. This approach avoids the **68.8% inter-agent data leakage rate** documented in standard frameworks while maintaining the structural enforcement that Keystone's "structure over intent" principle demands.

The framework landscape is consolidating rapidly. Models are getting better at self-orchestration, meaning the orchestration layer is thinning. Investing heavily in framework abstractions today risks depreciation. The durable value lies in **context engineering, evaluation infrastructure, and observability** — exactly the components Keystone's architecture prioritizes.

---

## Framework-by-framework verdict against pipeline requirements

### LangGraph v1.1.0 — LEARN (steal patterns, don't adopt wholesale)

LangGraph's graph-based state machine maps cleanly to Keystone's six-layer pipeline. Each layer becomes a node, conditional edges handle the Evaluator's accept/reject routing, and the **Send API** enables dynamic fan-out to 15–50 parallel research agents at runtime. Reject-and-regenerate loops are first-class — cyclic workflows are LangGraph's core differentiator, with configurable `recursion_limit` (default 25, adjustable per-run). Checkpointing via `PostgresSaver` persists state after every node execution, enabling crash recovery for long-running research tasks.

Agent isolation is achievable through **isolated subgraphs with separate `TypedDict` schemas** — each research agent gets a completely private state that other agents cannot access. The parent orchestrator passes only the topic in and receives only the synthesized result back. However, a known `MultipleSubgraphsError` arises when running nested subgraphs with checkpointing, requiring careful architecture using the Send API rather than imperative subgraph calls.

**Security is a serious concern.** Three CVEs disclosed in the final week of March 2026: **CVE-2026-34070** (path traversal, CVSS 7.5), **CVE-2025-68664** ("LangGrinch" serialization injection, CVSS 9.3 — in langchain-core itself), and **CVE-2025-67644** (SQL injection in langgraph-checkpoint-sqlite, CVSS 7.3). All patched, but the rapid exploitation of related AI framework vulnerabilities (Langflow CVE-2026-33017 exploited within 20 hours) signals that LangGraph's security maturity is still developing. No SOC 2 or ISO 27001 certifications exist.

LangSmith provides **near-zero-overhead observability** with automatic tracing of every LLM call, tool invocation, and intermediate reasoning step — benchmarked at virtually no measurable overhead versus ~15% for Langfuse. The NVIDIA production deployment (AI-Q deep research agent, scaled to 1,000 concurrent users) is the strongest verified evidence of LangGraph at scale.

**Why LEARN, not USE**: The Elastic-2.0 license on `langgraph-api` limits self-hosting flexibility. The security posture requires constant vigilance. And the deep coupling to LangChain ecosystem creates migration risk. But the architectural patterns — typed state with reducers, conditional edges for routing, Send API for dynamic fan-out, PostgresSaver for checkpointing — are the best-documented orchestration patterns available and should directly inform Keystone's custom build. [Evidence: Verified — NVIDIA technical blog, CVE databases, PyPI metadata, GitHub issues]

### CrewAI v1.12.2 — SKIP (too fragile for production pipelines)

CrewAI's Flows architecture offers `@start()`, `@listen()`, and `@router()` primitives for event-driven orchestration. On paper, the `@router()` decorator can handle non-linear workflows where the Evaluator kicks output back. In practice, **GitHub issue #1579 documents that routers stop after the first iteration when looping back** — the exact pattern Keystone's reject/regenerate loop requires.

A rigorous Towards Data Science analysis with Langfuse traces found that "the manager does not effectively coordinate agents; instead, CrewAI executes tasks sequentially, leading to incorrect reasoning, unnecessary tool calls, and extremely high latency." The hierarchical process pattern fails without very specific custom prompting. Memory system bugs persisted through v1.12.x, with Long-Term Memory APIs documented as non-functional in earlier versions.

For 15–50 parallel research agents, CrewAI would require separate Crews per agent kicked off asynchronously within a Flow — architecturally complex and untested at this scale. Agent isolation requires placing each research agent in its own Crew, which is a workaround, not a designed capability. The framework's claimed scale ("12M+ executions/day," "450M agents/month") comes exclusively from company marketing and investor materials with no independent verification.

The emerging practitioner consensus: **"prototype in CrewAI, ship in LangGraph."** For Keystone's complexity requirements, CrewAI adds risk without commensurate benefit. [Evidence: Credible — GitHub issues, TDS analysis with traces, community reports]

### PydanticAI v1.72.0 — USE (for agent definition and handoff contracts)

PydanticAI delivers the strongest "structure over intent" enforcement of any framework evaluated. Its `Agent[DepsType, OutputType]` generic typing catches handoff contract mismatches at write-time, not runtime. AgentSpec enables declarative YAML/JSON agent definitions where input/output types are validated Pydantic models — mapping directly to Keystone's explicit I/O quality gates. If an LLM output doesn't match the schema, PydanticAI **automatically re-prompts**, providing a built-in reject/regenerate primitive at the individual agent level.

**Pydantic Evals** can serve as the backbone for the 8-dimension rubric evaluator: each dimension becomes a custom evaluator or LLM-as-Judge instance with specific criteria, span-based evaluation verifies agents followed correct execution paths, and multi-run evaluation compares across generation attempts. This isn't a drop-in replacement for the Evaluator — custom evaluator development is required — but the infrastructure is solid.

The **Temporal integration** (`TemporalAgent` wrapper) is the key production enabler. It offloads all I/O to Temporal activities, providing deterministic workflow replay, crash recovery, and "pause until approval" patterns. For Keystone's 6-layer pipeline with long-running research tasks, Temporal's proven durability is more valuable than any framework's built-in checkpointing. The DBOS alternative offers lighter-weight Postgres-backed durable execution without Temporal's server requirement.

**Critical limitation**: The beta graph API for multi-agent coordination **does not include built-in state persistence** due to "complexity of achieving consistent snapshotting with parallel execution." The `pydantic_graph` broadcast/map/join primitives support parallel execution with type-checked edges, but persistence must come from Temporal/DBOS externally. PydanticAI is a library, not a platform — you must build the orchestration layer yourself.

Agent isolation is the **default**, not an opt-in: separate Agent instances share nothing. First-class MCP support via three transport types (Stdio, Streamable HTTP, SSE) connects research agents to the tool ecosystem. MIT license with no commercial restrictions on core features. [Evidence: Verified — official API documentation, Temporal integration examples, PyPI metadata]

### Claude Agent SDK (Python v0.1.51, TypeScript v0.2.86) — USE (as execution substrate)

This is the natural execution layer since Keystone builds on Anthropic infrastructure. The SDK wraps Claude Code's full capabilities as a programmable library with built-in tools (Read, Edit, Bash, WebSearch, WebFetch), session management, and **deep MCP integration** including runtime toggle/reconnect of MCP servers.

**Session forking** creates independent conversation branches — technically enabling 15–50 parallel research agents by forking from a common specification context. Each fork gets its own session ID and diverges independently. However, forking branches conversation history, not the filesystem — file edits in one fork are visible to others. For true isolation, use separate working directories or containers. Anthropic's own system typically runs **3–5 subagents** in parallel, with "more than 10" for complex tasks. Scaling to 50 is possible but beyond their tested range.

The SDK's subagent system provides **context-level isolation** with custom system prompts, restricted tool access via `allowed_tools`, and separate context windows per subagent. The hooks system (PreToolUse, PostToolUse, SubagentStart/Stop, PermissionRequest) enables custom quality gates at every execution boundary. Structured outputs with validated JSON enable type-safe handoff contracts.

**Rate limits are the critical constraint** for 15–50 parallel agents. API rate limits are per-organization, not per-key. At minimum, **Tier 4** ($400 deposit, ~160K input tokens per minute for Sonnet) is required. For sustained parallel operation, custom/monthly invoicing with negotiated limits is strongly recommended. **Prompt caching** (cached tokens don't count toward input token limits) can effectively multiply throughput 5–10x and should be used aggressively.

**Production maturity is mixed**: the SDK releases multiple times per week (high velocity, but also instability signal), sessions are machine-local (distributed deployment requires manual session file management), there's no built-in OpenTelemetry, and synchronous subagent execution is the current default (async is "under development"). The filesystem-oriented tool set is natural for Keystone's file-system-as-state approach. [Evidence: Verified — official Anthropic documentation, PyPI/npm releases, GitHub repository metrics]

### Google ADK v0.6.0 — LEARN (best pipeline primitives, wrong ecosystem)

ADK has the **closest 1:1 mapping** to Keystone's pipeline of any framework evaluated. Its workflow agents provide exactly the primitives needed:

- `SequentialAgent` for pipeline stages
- `ParallelAgent` for concurrent research execution (native, not a workaround)
- `LoopAgent` with exit conditions for reject/regenerate cycles

The Keystone pipeline maps almost directly: `SequentialAgent[SpecEngine, ParallelAgent[Research1...Research50], Deliberation, LoopAgent[Generator, Evaluator], FinalAssembler]`. This is the "Generator-Critic" pattern explicitly documented in ADK. Claude is supported via a direct wrapper class (`com.google.adk.models.Claude`) and LiteLLM integration for 100+ models.

**Why LEARN, not USE**: ADK is pre-1.0 (v0.6.0), meaning API-breaking changes are expected. The LiteLLM dependency suffered a **supply chain compromise on March 24, 2026** (versions 1.82.7–1.82.8 had unauthorized code). ADK is optimized for the Google ecosystem — deployment to Vertex AI is the easiest path, creating an awkward split for a Claude-native system. ParallelAgent sub-agents share session state, requiring careful key management to avoid race conditions. But the SequentialAgent → ParallelAgent → LoopAgent composition pattern is the clearest architectural blueprint for Keystone's pipeline and should be replicated in custom code. [Evidence: Credible — official Google documentation, codelabs, LiteLLM security advisory verified]

### OpenAI Agents SDK v0.13.2 — LEARN (handoff pattern only)

The SDK's handoff architecture is elegantly designed: `input_filter` controls what context the receiving agent sees, `on_handoff` callbacks execute at transition boundaries, and the agents-as-tools pattern maintains hierarchical control. Guardrails run **in parallel** with agent execution and fail fast — a pattern worth replicating for quality gates. However, there is **no built-in ParallelAgent primitive** (parallel execution requires manual `asyncio.gather`), and while technically model-agnostic, Claude support is second-class — Anthropic's compatibility layer is "not considered a long-term or production-ready solution" and loses prompt caching, structured outputs, and extended thinking. [Evidence: Credible — official documentation, community forum posts]

### OpenAgents — SKIP | Mastra — LEARN

**OpenAgents** solves agent networking and discovery between independent services, not structured pipeline orchestration. Documentation warns it's "still under active revision." No visible production adoption. The wrong abstraction level for Keystone's controlled pipeline.

**Mastra** (22.3K stars, $13M seed, YC W25) has an excellent **processor/tripwire pattern** where processors intercept agent I/O at every step and tripwires trigger retries with LLM feedback — the cleanest reject/regenerate implementation found. Enterprise customers include SoftBank, Adobe, and Replit. But it's TypeScript-only, making it a language mismatch. Steal the tripwire pattern. [Evidence: Verified — funding, npm downloads; Credible — enterprise adoption]

---

## The protocol stack Keystone should adopt

Three protocols form a complementary stack addressing different layers:

**MCP (Model Context Protocol) — USE now.** The de facto standard for agent-to-tool communication, now under the Linux Foundation's Agentic AI Foundation with Anthropic, OpenAI, Google, AWS, and Microsoft as members. Spec version 2025-11-25, with **97M+ monthly SDK downloads** and **10,000+ active servers**. For Keystone's research agents, MCP provides standardized access to web search, document analysis, file systems, and databases without building custom connectors per tool. The 2026 roadmap focuses on transport scalability (stateless Streamable HTTP for horizontal scaling), enterprise readiness (audit trails, SSO), and agent communication primitives (Tasks for async long-running operations). **Security caveat**: 53% of MCP servers rely on insecure static secrets, and 66% of scanned servers had security findings — use an MCP gateway with proper auth overlay. MCP does NOT solve inter-agent coordination; it's the tool layer.

**A2A (Agent-to-Agent Protocol) v1.0 — LEARN, adopt later.** Google-originated, now under Linux Foundation, with 150+ supporting organizations. Agent Cards (JSON at `/.well-known/agent-card.json`) describe capabilities, endpoints, and authentication. Tasks provide structured lifecycle management (submitted → working → input-required → completed/failed). For Keystone's **internal** pipeline with known topology, custom handoff contracts with file-system-as-state are simpler and sufficient. A2A adds value when: agents need to communicate with external systems, the pipeline topology becomes dynamic, or cross-platform interoperability is needed. The IBM ACP (BeeAI) merger into A2A signals consolidation — this will likely become the standard for inter-agent communication.

**AG-UI (CopilotKit) — USE for output delivery.** Event-based protocol (~16 types over SSE/WebSockets) for agent-to-frontend streaming. Adopted by **AWS Bedrock AgentCore** (March 2026) and **Microsoft Agent Framework** as native middleware. Enables token-by-token streaming of final outputs, real-time pipeline progress dashboards, and human-in-the-loop evaluator approval gates. Lightweight and transport-agnostic.

**OpenClaw ACP — SKIP.** IDE-to-agent protocol for coding workflows, not relevant for pipeline coordination.

---

## Anthropic's own architecture validates Keystone's design

Anthropic's engineering blog post "How we built our multi-agent research system" (June 2025) describes their production architecture — and it maps remarkably well to Keystone. Their system uses an **orchestrator-worker pattern**: a Lead Researcher Agent analyzes queries, develops strategy, spawns subagents, and synthesizes results. Subagents run with **separate context windows** (strict isolation), custom system prompts, and restricted tool access. A CitationAgent handles post-processing.

The performance data is striking: multi-agent (Opus lead + Sonnet subagents) outperformed single-agent Opus by **90.2%** on internal research evaluation. **Token usage explains 80% of performance variance** — more tokens consumed correlates with better results. The system runs 3–5 subagents in parallel, with prompts explicitly instructing parallel tool calls. Their quality control uses **LLM-as-judge** with rubric scoring on factual accuracy, citation accuracy, completeness, source quality, and tool efficiency — directly analogous to Keystone's 8-dimension evaluator.

Key Anthropic recommendations that validate Keystone's architecture:

- **File-system-as-state**: Anthropic explicitly recommends subagent output to filesystem to minimize "game of telephone" information loss
- **Evaluator-Optimizer pattern**: Their documented pattern for iterative refinement with evaluation loops maps to Keystone's reject/regenerate
- **Model mixing**: Opus for lead agent ($5/$25 per MTok), Sonnet for subagents ($3/$15) — **40% cheaper** for the bulk of execution
- **Start small**: 20 representative queries sufficient for early development evaluation
- **Rainbow deployments**: Safe updates for production agent systems where small lead-agent changes cascade unpredictably to subagents

The 2026 Agentic Coding Trends Report confirms multi-agent systems as standard, identifies engineering as shifting from code-writing to agent orchestration, and emphasizes that only **0–20% of tasks are fully delegatable** — human oversight remains essential. [Evidence: Verified — Anthropic Engineering blog with specific metrics]

---

## What fails at scale and why it matters for Keystone

**The coordination tax is real and exponential.** Two agents create 1 interaction path; 5 agents create 10; Keystone's 15–50 agents create **105–1,225 potential interaction paths**. GitHub's engineering team documented this with Copilot production experience. The solution is Keystone's existing isolation approach — strict isolation means interaction paths equal N (one per agent to orchestrator), not N(N-1)/2.

**Inter-agent data leakage is endemic.** The AgentLeak benchmark (February 2026, 4,979 traces) found that **68.8% of inter-agent message traces leak sensitive data** in standard frameworks. Shared memory leaks in 46.7% of traces. No framework tested provides mechanisms to intercept inter-agent messages or monitor shared memory writes. Claude 3.5 Sonnet showed lower leakage (28.1% inter-agent) than GPT-4o (76.8%), but the rates are still unacceptable for strict isolation. Keystone's architecture of isolated agents communicating only through the orchestrator is not just a nice-to-have — it's a **necessary defense** against a documented, measured failure mode.

**Reflexive loops are expensive.** An empirical benchmark of four architectures on 10,000 SEC filings found reflexive (self-correcting) loops achieve the highest accuracy (F1 = **0.943**) but at **2.3x the cost** of sequential baselines. Critically, **hybrid configurations recover 89% of reflexive accuracy at only 1.15x baseline cost**. For Keystone: use reject/regenerate selectively on high-value pipeline stages, not everywhere. The ICLR 2025 workshop finding that **verification phases consume 72% of tokens** means the Evaluator will be Keystone's primary cost driver.

**Infinite loops present as slow budget drain, not outages.** The LoopGuard pattern recommends: max 12 total steps, max 3 repeats per tool signature, max 4 steps without new signal. For Keystone's Evaluator, **3 regeneration cycles maximum** before escalating to human review or accepting best-effort output. Loop control must live in the orchestration layer, not in the agents themselves.

**Retry storms are the cascade mechanism.** In agent systems, each retry sends full conversation context to the LLM — 10 retries consume 10x the tokens, unlike traditional web retries. With K agents each doing 3 retries, the bottom service faces **4^K requests**. The solution: centralized retry governance with per-process retry budgets, circuit breakers, and exponential backoff with jitter (reduces retry storms by 60–80%).

**File-system-as-state works until concurrent writes.** Oracle's benchmark confirms that without a central coordinator, parallel agents hit race conditions and inconsistent views. Keystone's design — where each agent writes to its own directory and only the orchestrator reads across directories — sidesteps the concurrent write problem. Add advisory file locks for the orchestrator's read operations and write-ahead logging for crash recovery. The trade-off versus database-backed state: no ACID transactions, no semantic search, coarse access control, but human-readable, inspectable, and simple to implement. [Evidence: Verified — AgentLeak benchmark, ICLR workshop paper, arxiv SEC filing study, Google SRE]

---

## Build vs. buy: the honest analysis

The build-custom case is unusually strong for Keystone, for five specific reasons:

1. **No framework enforces strict agent isolation by default.** Every framework assumes shared state as the coordination primitive. Isolation must be bolted on, and the AgentLeak data shows bolting it on fails 46–69% of the time.

2. **The Rejection Library has no framework equivalent.** No evaluated framework provides persistent constraint storage that feeds back into generation. This is a novel component requiring custom engineering regardless of framework choice.

3. **File-system-as-state is orthogonal to framework assumptions.** Every framework assumes in-memory state or database-backed persistence. Adopting a framework means either abandoning file-system-as-state or fighting the framework's assumptions.

4. **The framework layer is thinning.** AWS Strands team: "We realized we no longer needed such complex orchestration." Better models commoditize orchestration logic. Manus rebuilt their agent framework **4 times** before getting context management right. Heavy framework investment today may depreciate.

5. **Framework disruption is real.** Microsoft merged AutoGen and Semantic Kernel into a new Agent Framework in 2026, requiring migration for all existing users. A practitioner reports that wrong framework choice at startup scale cost "6 months of velocity" to rebuild.

The recommended architecture: **PydanticAI for agent definition + Temporal for durable execution + custom pipeline orchestration + MCP for tools + AG-UI for output delivery.** PydanticAI provides type-safe handoff contracts and individual agent reject/retry. Temporal provides crash recovery, long-running workflow support, and the pipeline's sequential/parallel/loop execution patterns. Custom code glues the six layers together with strict isolation enforcement. MCP connects research agents to the tool ecosystem. AG-UI streams results to users.

The estimated engineering investment for custom orchestration: **2–3 developer-months** for the pipeline skeleton (typed state, fan-out/fan-in, conditional routing, checkpointing), plus **1–2 months** for the Rejection Library, observability integration, and rate limit management. This is significantly less than the ongoing maintenance burden of fighting a framework's assumptions at every architectural boundary.

---

## The recommended architecture, concretely

| Layer | Implementation | Classification |
|---|---|---|
| Agent definition + handoff contracts | PydanticAI `Agent[DepsT, OutputT]` + AgentSpec | **USE** |
| Pipeline orchestration | Custom (informed by LangGraph patterns + ADK composition) | **BUILD** |
| Durable execution | Temporal (`TemporalAgent` wrapper) | **USE** |
| Tool integration | MCP (Streamable HTTP transport) | **USE** |
| Output delivery | AG-UI (SSE event streaming) | **USE** |
| Agent execution substrate | Claude Agent SDK (subagents with isolated contexts) | **USE** |
| Evaluator framework | Pydantic Evals (custom 8-dimension evaluators) | **USE** |
| Observability | OpenTelemetry → Datadog/Grafana (LangSmith optional overlay) | **USE** |
| Inter-agent protocol | Custom handoff contracts now; A2A when topology becomes dynamic | **LEARN** |
| Rejection Library | Custom (structured JSON files with frequency-based injection) | **BUILD** |
| Rate limit management | Custom (token bucket tracking, staggered startup, prompt caching) | **BUILD** |

**Model strategy**: Claude Opus 4.6 with adaptive thinking (high effort) for the Specification Engine and Evaluator. Claude Sonnet 4.6 with adaptive thinking (medium effort) for parallel research agents — **40% cheaper** for the bulk of token consumption. Use the Batch API (50% discount) for non-time-sensitive evaluation passes. Prompt caching is mandatory for throughput.

---

## Conclusion: what the research changes

Three findings should shift Keystone's architectural decisions. First, **strict isolation isn't just a design preference — it's a measured necessity**, with 69% leakage rates in standard frameworks validating the isolation-by-default approach. Second, **the Evaluator will dominate costs** (verification consumes 72% of tokens in comparable systems), making selective application of reject/regenerate loops and the hybrid cost-recovery finding (89% accuracy at 1.15x cost) directly actionable for budget management. Third, **Anthropic's own production architecture already validates Keystone's core patterns** — orchestrator-worker, file-system-as-state, model mixing, LLM-as-judge evaluation — with a 90.2% performance improvement over single-agent approaches.

The framework landscape will continue churning. What won't change: the need for typed contracts at every boundary, durable execution for long-running pipelines, and structural enforcement of isolation. Build for those invariants. Use frameworks where they provide clear value (PydanticAI for type safety, MCP for tools, Temporal for durability). Build custom where Keystone's requirements are genuinely novel (pipeline orchestration, Rejection Library, isolation enforcement). And steal patterns aggressively from every framework evaluated — LangGraph's Send API fan-out, ADK's SequentialAgent/ParallelAgent/LoopAgent composition, OpenAI's input_filter handoffs, and Mastra's tripwire retry pattern.