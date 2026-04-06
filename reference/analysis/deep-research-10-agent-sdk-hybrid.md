# Anthropic's multi-agent toolkit and the case for hybrid orchestration

**For a production research pipeline like the Keystone Intelligence Engine, the optimal strategy is option (d): combine approaches.** Use PydanticAI + Temporal + MCP as the durable orchestration backbone, extract architectural patterns from Anthropic's documented multi-agent guidance, and selectively integrate the Agent SDK where its built-in capabilities (web search, file handling, subagent spawning) reduce custom code. This hybrid approach preserves the strict isolation, type-safe contracts, and crash recovery your 6-layer architecture demands while leveraging Anthropic's battle-tested agent runtime where it adds value. The analysis below draws from 14 official Anthropic engineering posts, the Agent SDK repositories, PydanticAI v1.74, Temporal's AI workflow patterns, and the MCP specification.

---

## The Agent SDK is Claude Code repackaged as a library

The **Claude Agent SDK** (renamed from "Claude Code SDK" in late 2025) is not a lightweight API wrapper — it bundles the entire Claude Code CLI binary (~45MB) and communicates with it via subprocess/IPC. This means developers get the same ~40 built-in tools (Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch, Agent), the same context compaction engine, and the same permission system that powers Claude Code's millions of users.

The SDK exposes two primary Python interfaces: `query()` for one-shot agent interactions returning an async iterator, and `ClaudeSDKClient` for bidirectional conversations with custom tools and lifecycle hooks. Subagents are defined programmatically via `AgentDefinition` objects specifying a description, system prompt, allowed tools, and model override (sonnet/opus/haiku). Each subagent runs in a **fresh, isolated context window** — only the final message returns to the parent. The SDK supports parallel subagent execution and MCP server integration via both in-process SDK servers and external subprocess servers.

Critical constraints matter for the Keystone architecture. **Subagents cannot spawn sub-subagents** — only one level of nesting is allowed. The SDK is **Claude-only** (no model portability). Versioning remains at **0.x** (TypeScript v0.2.92, Python comparable), meaning breaking API changes are possible. Community reports cite **~12-second latency overhead** per query from subprocess communication. The license is governed by Anthropic's Commercial Terms of Service, not MIT. For a 6-layer pipeline requiring deep nesting (Specification Engine spawning Research Agents that invoke CitationProcessors), the single-level restriction is a hard architectural constraint.

---

## Anthropic's 14 engineering posts distill into five core principles

Anthropic has published an unusually rich body of architectural guidance across **14 agent-related engineering blog posts** from December 2024 through March 2026. The most consequential for a research pipeline are four posts that form a coherent design philosophy.

**"Building effective agents" (December 2024)** establishes the foundation: five composable workflow patterns (prompt chaining, routing, parallelization, orchestrator-workers, evaluator-optimizer) and three principles — maintain simplicity, prioritize transparency, and carefully craft the agent-computer interface. The post explicitly warns against frameworks that add unnecessary abstraction: "Incorrect assumptions about framework internals are a common source of error." It recommends routing different complexity levels to different models (Haiku for simple queries, Sonnet for standard work, Opus for complex reasoning).

**"How we built our multi-agent research system" (June 2025)** is the single most relevant post for Keystone. Anthropic's own production Research feature uses an orchestrator-worker pattern where **Claude Opus 4 leads and Claude Sonnet 4 subagents execute in parallel**, achieving a **90.2% improvement** over single-agent Opus 4 on their internal research eval. This finding is verified as official Anthropic data, not from any source leak. The post reveals that token usage explains **80% of performance variance**, and multi-agent systems consume **~15x more tokens** than chat interactions. Eight prompt engineering principles for multi-agent systems include: teach the orchestrator explicit delegation instructions with objectives, output formats, and task boundaries; embed scaling rules (1 agent for simple queries, 2-4 for comparisons, 10+ for complex research); and use parallel tool calling at both agent and tool levels, which cut research time by up to 90%.

**"Effective context engineering" (September 2025)** introduces "context rot" — as token count increases, recall accuracy decreases with diminishing marginal returns. The solution is **just-in-time context retrieval** (agents maintain lightweight identifiers and dynamically load data via tools) combined with **sub-agent architectures** where each subagent may use tens of thousands of tokens internally but returns only 1,000-2,000 token summaries. This directly validates the Keystone pattern of isolated research agents reporting structured outputs upstream.

**"Harness design for long-running application development" (March 2026)** documents a Planner → Generator → Evaluator three-agent architecture inspired by GANs. The key finding: **self-evaluation is fundamentally unreliable** — "Making a generator self-critical is a fundamentally harder problem than building a separate, dedicated critic." This validates having a dedicated Evaluator layer rather than asking each agent to assess its own work.

---

## The "50 tools" finding and model mixing: provenance matters

Two widely cited claims require careful attribution. The claim that **"a model loaded with 50 tools performs worse than specialized agents with 5 focused tools"** is a community synthesis of multiple official Anthropic sources, not a verbatim quote. The underlying principle is well-documented: "Advanced tool use" (November 2025) shows that 50+ tools from multiple MCP servers consumed **55K-134K tokens** before any work began, and Anthropic's Tool Search Tool (loading only relevant tools on-demand) improved Opus 4 performance from **49% to 74%**. "Writing effective tools for agents" warns that "too many tools or overlapping tools can also distract agents from efficient strategies." The principle is sound and officially supported; the specific "50 vs. 5" framing is community shorthand.

**Model mixing** — using different models for different roles — is an official Anthropic recommendation documented in both the routing pattern ("Building effective agents") and the production Research architecture (Opus lead + Sonnet subagents). However, the term "model mixing" itself is community-coined; Anthropic describes the practice without using that label. None of these claims originate from the Claude Code source leak of March 2026; all trace to legitimate engineering blog posts.

---

## PydanticAI + Temporal + MCP forms a production-grade stack

**PydanticAI** reached v1.0 in September 2025 and stands at **v1.74.0** with 15 million downloads. It provides type-safe agent contracts where agents are generic over dependency types and output types (`Agent[SupportDependencies, SupportOutput]`), with Pydantic models enforcing structured outputs at runtime. Tools are registered via `@agent.tool` decorators with automatic schema generation and dependency injection via `RunContext`. The framework is model-agnostic across **25+ providers** (switching from Claude to GPT requires changing one string), includes built-in OpenTelemetry instrumentation, and ships with `pydantic-evals` for systematic agent evaluation.

For multi-agent patterns, PydanticAI supports agent delegation (one agent calls another as a tool), agent handoff (complete control transfer via output functions), and graph-based control flow via the `pydantic-graph` subpackage. The integration with Claude is first-class via `AnthropicModel`, supporting extended thinking, streaming, and all Claude features.

**Temporal** provides the durable execution layer that neither the Agent SDK nor PydanticAI alone can offer. The `TemporalAgent` wrapper — a **first-party PydanticAI integration** — automatically offloads all non-deterministic work (model calls, tool executions, MCP server communication) to Temporal Activities while keeping orchestration logic in deterministic Workflows. On crash recovery, completed Activities replay from history without re-executing LLM calls, saving both time and tokens. Human-in-the-loop gates use Temporal's Signal mechanism, allowing workflows to pause for days or weeks awaiting approval before resuming from the exact point of interruption. This directly enables the Deliberation layer's quality gates.

**MCP** has matured rapidly since its November 2024 introduction. The protocol was donated to the Linux Foundation's Agentic AI Foundation in December 2025, with co-founders Anthropic, Block, and OpenAI. The ecosystem has grown to **~2,000 MCP servers**, including production-ready options for the Keystone pipeline's needs:

- **Search**: Brave Search MCP (6 tools, 30B+ page index, free tier ~1,000 queries/month), Exa Search MCP (neural/semantic search with SEC filing and company research categories), and MCP Omnisearch combining Tavily, Brave, Kagi, Exa, GitHub, and Firecrawl
- **Financial data**: Exa's financial report category for SEC filings and 10-K/10-Q reports, plus dedicated financial market data MCP servers for stock, ETF, options, forex, and fundamentals
- **Content extraction**: Firecrawl and Jina AI MCP servers for structured web content extraction

PydanticAI's native MCP client support means any MCP server becomes an agent toolset with a single line: `MCPServerStreamableHTTP('http://localhost:8000/mcp')`. When wrapped in `TemporalAgent`, MCP tool calls automatically get durable execution guarantees.

---

## MCP gateways solve the production plumbing problem

For a production system with **strict isolation requirements**, an MCP gateway layer between agents and MCP servers is essential. Gateway patterns aggregate tools from multiple servers into a unified endpoint while providing five critical capabilities.

**Rate limiting** uses token bucket algorithms with per-user and per-tool limits backed by Redis counters, preventing any single research agent from monopolizing an external API. **Circuit breaking** monitors failure rates per backend server, tripping open when failures exceed a configurable threshold (e.g., 5 consecutive errors) — returning fast-fail responses in 50ms instead of hanging for 30 seconds, with half-open states for recovery testing. **Authentication and authorization** centralizes API keys and OAuth tokens with role-based access control per tool, keeping credentials outside the agent boundary as Anthropic recommends. **Audit logging** captures every tool call with user identity, cost, execution time, and tool parameters for compliance and debugging. **Transport adaptation** converts between MCP's stdio, SSE, and Streamable HTTP transports transparently.

Production gateway options include Composio (500+ managed integrations), Gravitee (API gateway with MCP support), and custom implementations. The 2026 MCP roadmap prioritizes stateless sessions for horizontal scaling, which will resolve the current tension between stateful MCP sessions and load balancers.

---

## How the three options compare for Keystone's 6-layer architecture

The decision matrix below evaluates each approach against the specific requirements of a Specification Engine → Parallel Research Agents → CitationProcessor → Deliberation → Content Structuring → Evaluator pipeline.

| Requirement | Agent SDK alone | Custom (PydanticAI + Temporal + MCP) | Hybrid approach |
|---|---|---|---|
| **Multi-level nesting** (6 layers) | ❌ One level only | ✅ Unlimited via workflow composition | ✅ Custom orchestration wraps SDK calls |
| **Strict agent isolation** | ✅ Fresh context per subagent | ✅ Full process-level + type-safe boundaries | ✅ Both mechanisms available |
| **Crash recovery** | ❌ No durable execution | ✅ Temporal replays from history | ✅ Temporal wraps everything |
| **Human-in-the-loop gates** | Partial (AskUserQuestion) | ✅ Temporal Signals, pause/resume | ✅ Temporal Signals |
| **Claim-level data contracts** | ❌ JSON Schema only | ✅ Pydantic models with validation | ✅ Pydantic models |
| **5-layer evaluation** | ❌ No built-in eval framework | ✅ pydantic-evals + custom evaluators | ✅ Full eval stack |
| **Model portability** | ❌ Claude only | ✅ 25+ providers, fallback chains | ✅ Use best model per layer |
| **Cost tracking** | ✅ Per-session tracking | ✅ OpenTelemetry spans | ✅ Both mechanisms |
| **Observability** | Limited | ✅ Native OpenTelemetry | ✅ Full trace pipeline |
| **Production maturity** | 0.x, pre-1.0 | ✅ V1 PydanticAI + mature Temporal | ✅ Best of both |

**Option (a), Agent SDK alone, fails** on three hard requirements: the single-level subagent nesting cannot express a 6-layer pipeline, there is no durable execution for crash recovery, and type-safe claim-level contracts require more than JSON Schema validation.

**Option (b), extracting Claude Code patterns**, is valuable for design guidance but impractical as a foundation. Claude Code's architecture (revealed in the March 2026 source leak) shows sophisticated context management, fork optimization for prompt cache sharing, and filesystem-based agent communication — but these are tightly coupled to the Claude Code runtime and not exposed as reusable primitives.

**Option (c), custom orchestration with PydanticAI + Temporal + MCP**, meets all requirements. PydanticAI provides type-safe agent contracts and model portability. Temporal provides crash recovery, human-in-the-loop gates, and durable state management. MCP provides standardized tool integration with the gateway patterns needed for rate limiting and circuit breaking.

**Option (d), the hybrid approach**, is optimal. It uses the custom stack as the orchestration backbone while selectively incorporating the Agent SDK where its built-in capabilities reduce development effort — specifically, using the SDK's research agent pattern for the Parallel Research Agents layer where its built-in WebSearch, WebFetch, and context compaction are immediately useful, while wrapping SDK calls within Temporal Activities for durability.

---

## Recommended architecture for the Keystone Intelligence Engine

The hybrid architecture maps each Keystone layer to the appropriate technology:

**Layer 1 — Specification Engine**: PydanticAI agent with Claude Opus, wrapped in `TemporalAgent`. Accepts user queries, classifies complexity, generates a research plan with structured Pydantic output (query decomposition, source priorities, scaling heuristics). Uses extended thinking for planning. This layer embeds Anthropic's scaling rules: 1 agent for simple queries, 3-5 subagents for comparisons, 10+ for complex research.

**Layer 2 — Parallel Research Agents**: This is where the Agent SDK adds the most value. Each research subagent can be an Agent SDK `query()` call with restricted tools (WebSearch, WebFetch, Read) and model override (Sonnet for standard research, Opus for synthesis-heavy tasks). These SDK calls are wrapped as Temporal Activities, gaining retry policies and crash recovery. MCP servers (Brave Search, Exa, financial data) are registered via the MCP gateway for rate-limited, circuit-broken external access.

**Layer 3 — CitationProcessor**: PydanticAI agent with strict Pydantic output models enforcing claim-level citation contracts. Each claim must reference specific source locations with confidence scores. This mirrors Anthropic's production CitationAgent pattern from their Research feature.

**Layer 4 — Deliberation**: Temporal Workflow with Signal-based human-in-the-loop gates. Multiple evaluator agents (PydanticAI) assess factual accuracy, source quality, and completeness. Uses Anthropic's finding that self-evaluation is unreliable — **dedicated critic agents outperform self-critical generators**.

**Layer 5 — Content Structuring**: PydanticAI agent with structured Pydantic output models defining the final report schema. Model can be Sonnet for cost efficiency since the creative work is constrained by structured contracts.

**Layer 6 — Evaluator**: PydanticAI agent using `pydantic-evals` with LLM-as-judge evaluators. Implements the five evaluation dimensions as separate evaluation criteria with hard thresholds, following the Planner → Generator → Evaluator GAN-inspired pattern from Anthropic's March 2026 harness design post.

The entire pipeline runs as a Temporal Workflow with each layer as a sequence of Activities. Cross-layer state flows through typed Pydantic models. OpenTelemetry spans from PydanticAI feed into the observability platform (Logfire or any OTel-compatible backend). The MCP gateway handles all external tool access with centralized rate limiting, circuit breaking, and audit logging.

---

## Conclusion: what the evidence actually shows

The research reveals a clear hierarchy of value across Anthropic's offerings. The **engineering blog posts** are the highest-value asset — 14 posts containing battle-tested architectural patterns from Anthropic's own production systems, including the specific finding that orchestrator-worker with model mixing achieved 90.2% improvement. The **Agent SDK** is genuinely useful as a component but inadequate as a complete orchestration solution for complex pipelines due to single-level nesting, no durable execution, and Claude lock-in. **Claude Code's architecture** provides design inspiration (context compaction strategies, fork optimization, filesystem-based coordination) but its internals are not reusable outside the SDK.

The custom stack of PydanticAI + Temporal + MCP has reached a level of maturity that makes it the strongest production foundation. PydanticAI's first-party `TemporalAgent` wrapper and native MCP client mean the three technologies integrate with minimal glue code. Temporal's durable execution solves the hardest production problem — recovering from failures in long-running, expensive multi-agent workflows without re-running completed LLM calls. MCP's ecosystem of ~2,000 servers provides immediate access to search, financial data, and content extraction tools through a standardized protocol.

The key insight from Anthropic's own experience: **"Validation is the bottleneck, not orchestration."** The Keystone team should invest most heavily in the Evaluator layer and claim-level data contracts, not in orchestration complexity. Start with 2-3 agents per research query and add parallelism only when evaluation metrics demonstrate clear improvement. Budget ~15x chat-level token costs for multi-agent research. Build comprehensive tracing from day one. And follow Anthropic's most repeated advice: start simple, add complexity only when measured outcomes justify it.