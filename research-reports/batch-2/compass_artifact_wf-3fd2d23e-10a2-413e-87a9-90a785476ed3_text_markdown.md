# Orchestrating multi-agent AI pipelines in 2026: the definitive stack

**PydanticAI v1.77 + custom async orchestration is the right foundation for the Keystone Intelligence Engine**, and deferring Temporal to Phase 2 is the correct call. The framework landscape has matured dramatically since mid-2025: PydanticAI reached production stability (v1.0 in September 2025), Anthropic shipped a Claude Agent SDK that powers their internal systems, and Temporal now has native PydanticAI integration. This report synthesizes findings across all seven research questions to give the team a clear architectural roadmap.

The bottom line: PydanticAI's type safety, model-agnosticism, and composable primitives make it the best agent framework for custom pipelines. The team should use a **hierarchical supervisor + DAG hybrid pattern** — a deterministic DAG backbone for the 6-layer pipeline with a supervisor pattern inside L1 for parallel research. Human-in-the-loop gates can start as a simple database state machine (2–3 days of implementation) and graduate to Temporal Signals when scale demands it.

---

## PydanticAI has become the production standard for typed agent systems

PydanticAI hit **v1.0 on September 4, 2025**, after 15 million pre-release downloads, and now sits at **v1.77.0** with 16,100 GitHub stars and 414+ contributors. The PyPI classifier reads "Production/Stable," and the team has committed to no breaking changes until v2 (planned April 2026 at earliest). This is no longer an experimental choice — it's the mature option.

The framework's core strength for the Keystone pipeline is **type-safe structured outputs**. Every agent declares an `output_type` as a Pydantic model, and the framework validates responses automatically — including during streaming. Three output modes exist: Tool Output (default, sends JSON schema as a tool parameter), Native Output (uses the model's structured output mode), and Prompted Output (injects schema into instructions). When validation fails, PydanticAI automatically prompts the model to retry, which means malformed outputs self-correct without custom error handling.

For multi-agent orchestration, PydanticAI provides four composition patterns: agent delegation (one agent calls another as a tool), programmatic hand-off (application code routes between agents), output functions (complete handoffs without returning to the caller), and graph-based workflows via the `pydantic_graph` package. The newer **beta Graph API** adds a `GraphBuilder` with parallel execution, joins, reducers, and conditional branching — directly relevant to the L1 parallel research phase.

Critical capabilities added since mid-2025 include **native MCP integration** (MCPServerStdio, MCPServerSSE, MCPServerStreamableHTTP), **A2A protocol support**, **AG-UI integration** for interactive applications, a **Capabilities system** for composable tool bundles, and **durable execution integrations** with Temporal, DBOS, and Prefect. The HITL story is now first-class: tools can be marked `approval_required`, pausing execution until a human approves or modifies the tool call.

The main limitation is that PydanticAI provides **primitives, not opinions**. There's no built-in "Crew" or "Team" abstraction — multi-agent coordination is assembled from building blocks. For the Keystone pipeline, this is actually a strength: the team gets maximum control over orchestration logic without fighting framework assumptions. The graph API is still in beta, which means occasional API churn, but the core agent primitives are API-stable.

---

## Anthropic's Agent SDK is powerful but wrong for this use case

Anthropic renamed the Claude Code SDK to **Claude Agent SDK** on September 29, 2025, reflecting that the same agent harness powers their deep research, video creation, and note-taking systems internally. The Python SDK is at v0.1.48 with 5,500 GitHub stars.

The SDK is architecturally different from PydanticAI. It's a **runtime harness** rather than a declarative framework — it wraps Claude Code's entire agent loop, including 14+ built-in tools (Bash, Read, Write, Edit, WebSearch, WebFetch) that actually execute on the system. The `query()` function returns an async iterator of typed messages. Custom tools are defined via in-process MCP servers. Subagents get isolated context windows and can run in parallel, with optional AI-generated progress summaries.

The SDK's MCP integration is the deepest in the ecosystem (Anthropic created MCP), and it includes features like automatic context compaction when approaching token limits, extended thinking support, and a sophisticated hooks system for safety guardrails. For agents that need "a computer" — terminal access, file operations, web browsing — it's unmatched.

However, **three factors disqualify it as the primary framework for Keystone**. First, it's **Claude-only** — locked to Anthropic models with no provider flexibility. Second, it's governed by **Anthropic's Commercial Terms of Service**, not an open-source license, creating long-term ownership risk. Third, the architecture spawns a Claude Code subprocess (Node.js) under the hood, adding deployment complexity compared to pure Python API calls.

The right approach is **hybrid**: use PydanticAI as the primary framework for typed, testable, model-agnostic agents, and consider the Agent SDK only for specific workflows that benefit from the full Claude Code runtime (complex file operations, code execution sandboxes). For standard research agents making API calls with structured outputs, PydanticAI calling Claude directly is simpler, cheaper (lower token overhead), and more flexible.

---

## Temporal is correct to defer but architect for it now

The Temporal Python SDK is at **v1.24.0**, fully GA, with ~25 million monthly PyPI downloads. It now has **native PydanticAI integration** via `TemporalAgent` — a wrapper that automatically offloads all non-deterministic work (model calls, tool executions) to Temporal Activities while keeping orchestration logic deterministic. The migration path from plain async to Temporal is smooth: wrap agents with `TemporalAgent`, move orchestration into `@workflow.defn` classes, deploy Temporal Cloud.

Production validation is strong. **OpenAI uses Temporal for Codex**, handling millions of requests for their AI coding agent. **Replit migrated Agent 3 to Temporal** for improved reliability. **Retool built their Agents product on Temporal**, shipping in months with a small team. Temporal raised a Series D at a **$5B valuation** in 2025, with AI demand as the primary driver.

What the team loses by deferring: crash recovery mid-pipeline (must re-run from the beginning or build custom checkpointing), unified execution visibility (debugging stuck pipelines requires log-grepping rather than Temporal's Web UI), automatic deduplication, and configurable per-activity retry policies. What the team keeps: basic parallelism via `asyncio.gather()`, simple sequential flow, and development velocity without infrastructure overhead.

**The inflection point is when you can't afford to re-run failed pipelines.** With 2–5 rounds of 3–5 agents each, a single pipeline run involves 6–25+ LLM API calls at $0.10–0.50 per run. During MVP validation, re-running is acceptable. With paying customers and SLA requirements, it's not.

The async alternative requires building ~500–1,000 lines of custom orchestration code: a state machine for pipeline status tracking, PostgreSQL checkpoint persistence via `asyncpg`, retry logic with `tenacity`, concurrency control with `asyncio.Semaphore`, and structured logging with correlation IDs. This is **2–4 weeks of implementation**, non-trivial but manageable.

Five architectural decisions to make now for painless migration later:

- Make each pipeline layer a pure function: `async def run_layer(input: LayerInput) -> LayerOutput`
- Use Pydantic models for all inter-layer data (clean serialization for both PostgreSQL and Temporal)
- Keep the pipeline controller separate from agent code
- Log with correlation IDs per pipeline run (maps to Temporal workflow IDs later)
- Build idempotent layers that produce the same output for the same input

When Phase 2 arrives, **Temporal Cloud at ~$100/month** (with $1,000 in free credits for new users) eliminates all server management. Don't self-host — the operational complexity of Temporal Server (Frontend, History, Matching, Worker services plus persistence and visibility databases) is significant, with real users reporting "several days" of cryptic debugging and PostgreSQL spikes at modest scale.

---

## The right orchestration pattern is a DAG backbone with a supervisor core

The Keystone pipeline maps naturally to a **deterministic DAG with a supervisor pattern inside L1**. This is the dominant production pattern — Anthropic, OpenAI, Microsoft, and virtually every major platform uses this hybrid approach.

At the macro level, the 6-layer pipeline forms a sequential DAG with conditional edges for evaluation loops. Each stage produces a typed Pydantic output consumed by the next stage. The pipeline controller owns all state transitions — the LLM reasons, but the system decides flow. At the micro level within L1, a supervisor agent (running on Opus 4.6) spawns 3–5 parallel research agents (running on Sonnet 4.6), collects condensed results, and decides whether more rounds are needed.

Anthropic's own multi-agent research system, documented in a June 2025 engineering blog post, validates this exact architecture. Their LeadResearcher (Opus 4) analyzes queries, plans strategy, and spawns subagents (Sonnet 4) that operate independently with their own context windows. Each subagent explores **tens of thousands of tokens** but returns only **1,000–2,000 tokens** of condensed findings. Their multi-agent system outperformed single-agent Opus 4 by **90.2%** on research evaluations, with token usage explaining 80% of performance variance.

Context management across rounds follows a clear hierarchy. **Isolation is the primary strategy**: each subagent gets a fresh context window with only the compressed structured output from prior rounds plus round-specific instructions. Between rounds, a context compaction layer compresses research findings into structured schemas — preserving key facts, sources, and confidence scores while discarding raw search results and intermediate reasoning. The principle from Manus (a production agent platform): "Share memory by communicating, don't communicate by sharing memory."

The critical design choice is **centralized orchestration for the pipeline, decentralized execution for research**. The DAG controller maintains global state and enforces quality gates. Research agents operate independently within their rounds. The evaluator (L4) conditionally routes back to earlier stages based on structured quality scores. This hybrid gives auditability and control at the pipeline level while allowing parallel exploration at the research level.

---

## Error recovery requires a four-layer defense architecture

Production multi-agent systems face seven failure categories: API rate limits and timeouts, context window overflow, semantic failures (hallucinations, off-topic responses), token budget exhaustion, network failures, cascading agent-to-agent failures, and silent failures where agents return 200 OK with fabricated data. Claude API specifically shows **62 incidents in 90 days** according to StatusGator, with a median duration of 1 hour 19 minutes.

The layered defense, in priority order:

**Layer 1 — Retry with exponential backoff** (biggest impact, least code). Use `tenacity` with 1-second base delay, 60-second cap, full jitter, and 5 maximum attempts. Honor Claude API's `Retry-After` and `X-RateLimit-*` headers. Only retry on 429 (rate limited), 500 (server error), 529 (overloaded), and connection timeouts. Never retry 400 (bad request), 401 (unauthorized), or 413 (too large). AWS research shows exponential backoff with jitter reduces retry storms by **60–80%**.

**Layer 2 — Model fallback chains**. Primary: Opus 4.6 for planning/evaluation. Fallback 1: Sonnet 4.6 for most tasks. Fallback 2: Haiku 4.5 for extraction and simple tasks. Fallback 3: cached/template response (deterministic). Put retry middleware before fallback middleware — retry the primary model 2–3 times before falling back. One production system reported that these layered patterns dropped **unrecoverable failures from 23% to under 2%**.

**Layer 3 — Error classification and routing**. Transient errors (rate limits, server errors) get retried with backoff. LLM-recoverable errors (tool failures, parsing errors) get sent back to the model for reformulation. Context overflow triggers compression and retry with shorter context. User-fixable errors (missing information) pause for human input. Unexpected errors bubble up with the Claude API `request_id` for debugging.

**Layer 4 — Checkpointing**. Persist intermediate results to PostgreSQL after each pipeline layer completes. If the pipeline crashes at L2, resume from the L1.5 checkpoint without re-running research. Store pending writes from successful parallel agents so they aren't re-run on resume. This is where the Temporal migration pays off most — Temporal provides this automatically via event history replay.

For the parallel research phase specifically, the system should support **partial result continuation**. If 3 of 5 research agents complete but 2 fail, combine the available results, note reduced coverage, and either retry the failed agents independently or proceed with a degradation notice. Every agent should return structured results including a success/failure status, so the orchestrator always knows what it has.

Circuit breakers should operate at the **agent-cluster level**, not individual connections. Monitor failure rates across the L1 research agent pool. If more than 50% of agents fail within 60 seconds, trip the circuit breaker and fail fast rather than burning API credits on a degraded provider. Classic circuit breakers can't catch hallucinations — add semantic quality checks that flag responses deviating from expected patterns.

---

## Human-in-the-loop gates start simple and graduate to Temporal

For the MVP, the simplest viable HITL pattern is a **database state machine with a REST API and web UI**. The pipeline writes an artifact to PostgreSQL, sets status to `AWAITING_REVIEW`, and returns. A web UI polls for pending reviews, presents the artifact with agent reasoning alongside, and posts the decision back. The pipeline orchestrator resumes with the (potentially modified) artifact.

The database schema needs three tables: `pipeline_runs` (status, current stage, timestamps), `review_gates` (artifact JSON, review status, reviewer notes, modified artifact JSON, timeout timestamp), and `agent_results` (per-agent outputs for debugging). All artifacts are Pydantic models — free serialization, deserialization, and validation of human modifications. **Estimated implementation: 2–3 days** for the core pattern.

Three review flows should be supported from day one: **approve** (accept artifact as-is, pipeline continues), **modify** (edit the artifact inline with schema validation, pipeline continues with modified version), and **reject** (send back for regeneration with feedback notes that become context for the next attempt). The UI should show the artifact prominently alongside a collapsible "Agent Reasoning" panel with sources consulted, key decisions, confidence levels, and token usage.

For handling long waits, implement **timeout and escalation**. Default timeouts of 1 hour for low-stakes reviews (L0 spec approval) and 24 hours for high-stakes reviews (L1 research output). Background tasks check for overdue gates every 5 minutes. When timeout hits, escalate to a backup reviewer or auto-approve with an audit log for non-critical gates.

When the team migrates to Temporal in Phase 2, HITL gates become **Temporal Signals**. The workflow calls `workflow.wait_condition()`, which can wait indefinitely — hours, days, weeks — with zero resource consumption. The workflow state is durably persisted and survives crashes, deploys, and restarts. A Query endpoint exposes current state for the UI. The REST API simply sends a Signal to the running workflow instead of writing to a database. Agent code doesn't change; only the orchestration layer migrates.

PydanticAI's native HITL support (tool approval with `approval_required` flags plus durable execution integrations) bridges the gap between MVP and production. Tools marked for approval pause execution and surface the call for human review. Combined with the Temporal integration, this provides a complete HITL story without leaving the PydanticAI ecosystem.

---

## The framework landscape validates PydanticAI as the right choice

Evaluating all six options against the Keystone requirements — strict agent isolation, structured Pydantic outputs, parallel execution, human review gates, custom orchestration, Claude API primary, MCP integration — **PydanticAI is the clear winner** with LangGraph as the only viable alternative worth considering.

| Criterion | PydanticAI | LangGraph | Others |
|---|---|---|---|
| Type safety / structured outputs | Best-in-class — native Pydantic models, streamed validation, 3 output modes | Functional but secondary concern | Anthropic SDK: JSON Schema only. CrewAI: role-playing adds 3× token overhead |
| Parallel execution | Native async, `asyncio.gather()` with multiple `Agent.run()` | Graph-native fan-out/fan-in, deferred nodes | All support basic parallelism |
| Human-in-the-loop | Tool approval + Temporal/DBOS durable execution | Best in ecosystem — `interrupt()` at any node, persistent checkpoints | OpenAI SDK has interruptions; CrewAI basic |
| Vendor lock-in | **Zero** — MIT license, 25+ providers | Zero — MIT, model-agnostic | Anthropic SDK: Claude-only, proprietary license |
| MCP integration | Native (MCPServerStdio, HTTP, SSE, Streamable HTTP) | Via adapters, not native | Anthropic SDK: deepest (they created MCP) |
| Production readiness | v1.0+, API-stable, OTel observability | v1.0 (October 2025), checkpointing, used by Klarna/Replit | OpenAI SDK still pre-1.0 |
| Learning curve | Easiest for Python devs — "FastAPI for AI agents" | Steepest — requires graph-based architectural thinking | CrewAI easiest for prototyping |

**LangGraph** deserves serious consideration only if orchestration complexity becomes extreme. Its persistent checkpointing with automatic crash recovery, time-travel debugging, and mature `interrupt()` mechanism for HITL are genuinely superior to PydanticAI's newer graph API. Used in production by Klarna, Replit, and Elastic. But it carries the LangChain ecosystem's abstraction weight, a steeper learning curve, and more boilerplate for simple cases.

**OpenAI Agents SDK** (v0.13.3, 18,900 stars) has the cleanest handoff model in the ecosystem and built-in guardrails that run in parallel with execution. But it's pre-1.0, lacks checkpointing, and its handoff-based orchestration is too rigid for custom pipelines.

**CrewAI** (45,900 stars, largest community) excels at rapid prototyping with its role-based metaphor but burns **3× more tokens** than alternatives due to role-playing prompts, has opaque debugging, and lacks fine-grained control — dealbreakers for a research pipeline where cost efficiency and precision matter.

**Simple async** (no framework) is viable but unnecessary. PydanticAI provides the same control with type safety, MCP integration, streaming, and observability built in. The framework adds value without constraining flexibility.

---

## Conclusion: the architectural roadmap

The team's instinct — PydanticAI + custom async orchestration for MVP, Temporal deferred to Phase 2 — is validated by the current framework landscape. Three insights emerged that should sharpen execution:

**The orchestration pattern should be explicit.** Use a deterministic DAG controller for the macro pipeline (L0→L1→L1.5→L2→L3→L4) with conditional edges for evaluation loops. Embed a supervisor pattern only inside L1 for parallel research. Don't let the LLM decide pipeline flow — let the system decide based on structured outputs from each stage. This matches how Anthropic's own research system works in production.

**Error recovery is a day-one concern, not a Phase 2 feature.** The four-layer defense (retry → fallback → classification → checkpointing) should ship with the MVP. Retry with exponential backoff takes a few hours to implement with `tenacity` and prevents the majority of failures. Model fallback chains (Opus → Sonnet → Haiku) provide resilience against provider degradation. These patterns dropped unrecoverable failures from 23% to under 2% in documented production systems.

**The Anthropic Agent SDK is complementary, not competitive.** PydanticAI handles the structured, typed, multi-model agent work that forms the pipeline backbone. The Agent SDK is worth evaluating only for specific nodes that need Claude Code's full runtime — computer use, code execution, or complex file operations. For standard research agents making API calls with structured outputs, PydanticAI calling Claude directly is simpler, cheaper, and more flexible. The hybrid approach preserves optionality without taking on unnecessary vendor lock-in.