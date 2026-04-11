# Responses API architecture for custom multi-agent orchestration

**The Responses API's agentic loop only runs server-side for built-in tools; custom function tools always return to your client for execution, giving you full orchestration control.** This means the Keystone Intelligence Engine can adopt a hybrid architecture: use the Responses API as a smart completion endpoint within your existing generator-based PydanticAI orchestration, selectively enabling built-in tools where they add value, while retaining complete control over tool authorization, logging, error recovery, and cross-agent coordination. Production systems like Codex CLI have validated exactly this pattern — managing their own loop while leveraging built-in tools and prompt caching for performance.

---

## How the agentic loop actually works under the hood

The Responses API draws a hard architectural line between **built-in tools** and **custom function tools**, and understanding this distinction is essential for your decision.

**Built-in tools execute server-side in a single API call.** When you include `web_search`, `file_search`, `code_interpreter`, `shell`, or remote `mcp` tools, the model proposes a tool call, OpenAI's infrastructure executes it, feeds the result back to the model, and repeats — all within one HTTP request/stream. You send one request and receive the final answer. From OpenAI's engineering blog: *"Because tool execution happens server-side through hosted tools, you're not bouncing every call back through your own backend, ensuring better latency and round-trip costs."*

**Custom function tools require a client-side loop — no automatic execution.** When the model calls a custom function, the API returns `function_call` items in the response output. Your code must parse the call, execute the function locally, append a `function_call_output` item (matched by `call_id`), and make another API call. The loop terminates when the response contains only `message` items (text output) with no further `function_call` items. There is **no `max_tool_rounds` parameter** for custom tools — you must enforce round limits client-side.

**Both tool types coexist in a single request.** You can pass `tools=[{"type": "web_search"}, {"type": "function", "name": "query_database", ...}]` in one call. The API executes the web search server-side, then returns any custom function calls for your client to handle. This is the hybrid pattern that Codex CLI and other production systems use.

For interception between rounds, the picture is clear: **custom function tools give you total control** — you can authorize, log, rate-limit, validate, and modify between every round because the loop is yours. Built-in tools offer limited interception via `max_tool_calls` (a cap on total built-in tool invocations) and MCP's `require_approval: "always"` setting. Streaming surfaces observability events (`response.web_search_call.searching`, etc.) but these are read-only — you cannot inject logic into the server-side loop.

The key parameters controlling behavior include `max_tool_calls` (built-in tools only), `tool_choice` (`"auto"`, `"none"`, `"required"`, or a specific function), `parallel_tool_calls` (boolean, allows concurrent function calls), `truncation` (auto-truncate context), and `context_management` with compaction for long-running loops.

---

## PydanticAI's Responses API integration and what it means for your orchestration

PydanticAI supports the Responses API through `OpenAIResponsesModel`, activated with the `openai-responses:` prefix. **PydanticAI always manages its own orchestration loop** — it does not delegate the tool call loop to the Responses API. This aligns perfectly with your existing generator-based orchestration pattern.

The integration architecture works in layers. PydanticAI's `pydantic-graph` finite state machine handles the agent execution flow: send request → receive response → execute any function tools locally with Pydantic validation → append results → repeat. Built-in tools execute server-side within each individual API call, but PydanticAI still controls when to make each call and how to process results. This means your custom orchestration sits *on top of* PydanticAI, which sits on top of the Responses API — a clean separation of concerns.

**State management offers two complementary approaches.** PydanticAI exposes the Responses API's `previous_response_id` via `OpenAIResponsesModelSettings`. Set it to `'auto'` and PydanticAI automatically extracts the most recent `provider_response_id` from message history, omitting messages that came before it and letting OpenAI's server-side state take over. This avoids resending full conversation history. Alternatively, you can manage state entirely client-side (PydanticAI's `message_history`) for full control and ZDR compatibility.

```python
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings

# Automatic server-side state chaining
model_settings = OpenAIResponsesModelSettings(openai_previous_response_id='auto')
result2 = await agent.run('Follow up question', message_history=result1.new_messages(), model_settings=model_settings)
```

**Built-in tools are first-class citizens in PydanticAI.** Web search, code interpreter, image generation, file search, and MCP servers all work via the `builtin_tools` parameter on `Agent`. These execute server-side while PydanticAI's custom function tools execute client-side — both in the same agent. PydanticAI also offers provider-adaptive `capabilities` (`WebSearch`, `ImageGeneration`) that auto-detect whether the model supports native tools and fall back to local implementations if not.

For custom `AsyncOpenAI` clients (including OAuth-based authentication), PydanticAI fully supports this via `OpenAIProvider(openai_client=your_custom_client)`. Your existing Codex OAuth flow plugs in directly.

The `agent.iter()` method provides the step-by-step control your generator-based orchestration needs — it returns an `AgentRun` object that can be async-iterated node-by-node, with full visibility into each tool call, result, and state transition.

---

## Built-in tools as replacements for external APIs

**Web search works well for general queries but falls short of research-grade needs.** OpenAI's built-in `web_search` is powered by Bing infrastructure. It supports domain filtering (up to 100 domains via `filters.allowed_domains`), configurable search context size (`"low"`, `"medium"`, `"high"`), and with reasoning models performs agentic multi-step search within the chain of thought. It provides inline citations and source URLs. However, for the Keystone Intelligence Engine's research pipeline, there are meaningful limitations: no raw content extraction, limited domain filtering compared to Exa's 1,200-domain support, no date range filtering, and inconsistent results on complex multi-hop queries. **Exa excels at semantic/neural search (81% on complex retrieval benchmarks) while Tavily scores 93.3% on grounding tasks** — both outperform built-in search for research-grade work.

The cost differential is significant at scale. Built-in web search costs **$10 per 1,000 calls** plus search content tokens billed at the model's input rate. External alternatives are cheaper: Exa at $2.50/1k, Brave at $5/1k, Tavily at $8/1k. For a research pipeline executing thousands of searches daily, external APIs could save 60–75% on search costs alone.

**Code interpreter is viable for data analysis within research agents.** It executes Python in sandboxed containers with configurable memory (1GB to 64GB), supports file uploads and chart generation, and integrates with reasoning models' chain of thought. Limitations: Python-only (the newer `shell` tool supports arbitrary languages), containers expire after inactivity, and no explicit per-request timeout configuration. For research data analysis — statistical processing, visualization, CSV manipulation — it's well-suited.

**The recommended hybrid for Keystone is clear:** use built-in `web_search` for quick supplementary lookups and `code_interpreter` for data analysis, but keep Exa or Tavily as your primary research search tools implemented as custom function tools. This gives you the best of both: server-side execution for simple searches and full control over your core research retrieval pipeline.

---

## The production consensus is custom orchestration with selective built-in tools

**Codex CLI — OpenAI's own flagship agent product — manages its own loop.** It uses the Responses API as a completion endpoint, sends full conversation history each request (stateless), deliberately avoids `previous_response_id` for ZDR compliance, and relies on prompt caching to keep performance linear despite quadratic JSON growth. It mixes built-in web search, custom CLI tools (sandboxed shell), and user MCP servers in the same `tools` array. OpenAI reports **40–80% better cache utilization** with the Responses API versus Chat Completions.

The broader ecosystem follows this same pattern. Production systems like Hexagon (four-agent simulation pipeline) and Collxn (16 custom tools + web search) use the Responses API for individual calls while managing orchestration externally. The OpenAI Agents SDK, built on top of the Responses API, provides higher-level primitives — handoffs, guardrails, tracing — but even it implements the tool call loop client-side through its `Runner` class.

**For the Keystone Intelligence Engine's specific requirements** — per-agent tool authorization, detailed event logging, error recovery with alternative strategies, and cross-agent coordination — the Responses API's built-in loop is insufficient. These requirements all demand client-side interception between tool rounds, which only custom orchestration provides. The built-in loop is a black box for these concerns.

Latency implications favor the hybrid approach. Built-in tools eliminate client-server round trips (**server-side execution is measurably faster**). Prompt caching reduces time-to-first-token by up to **80%** for large contexts — at 150k+ tokens, cached prompts are 67% faster. The Responses API's server-controlled prompt ordering (system → tools → instructions → input) ensures stable prefixes cache perfectly. Your custom orchestration benefits from this caching even when managing the loop manually, as long as you keep instructions and tool definitions stable and at the front of requests.

Migration momentum is strong: starting with recent models, **tool calling is not supported in Chat Completions with `reasoning: none`**, effectively requiring the Responses API for certain configurations. The Assistants API sunsets August 2026. An "Open Responses" specification backed by Nvidia, Vercel, Hugging Face, Ollama, and others aims to make the Responses API format a cross-provider standard, reducing vendor lock-in concerns.

---

## Concrete recommendation for Keystone Intelligence Engine

The optimal architecture is a **hybrid with custom orchestration as the primary control layer**:

- **Keep your generator-based PydanticAI orchestration** as the outer loop. Use `agent.iter()` for step-by-step control. This preserves per-agent authorization, logging, error recovery, and cross-agent coordination. Use `OpenAIResponsesModel` as the model backend.
- **Enable built-in `web_search`** for supplementary lookups within research agents, but maintain Exa/Tavily as custom function tools for primary research retrieval — they offer better quality, control, and cost at scale.
- **Use `code_interpreter`** for data analysis tasks within analytical agents. PydanticAI's `CodeExecutionTool` integrates it cleanly.
- **Use `previous_response_id` with `'auto'` mode** for long-running agent conversations to reduce bandwidth and leverage server-side state, but design for stateless fallback (ZDR compatibility).
- **Leverage prompt caching aggressively**: keep instructions and tool definitions stable and identical across requests. The Responses API's 40–80% cache improvement translates directly to cost and latency savings even with custom orchestration.
- **Do not use the OpenAI Agents SDK** as your orchestration layer — it would conflict with your existing PydanticAI orchestration and adds abstraction without adding capability you don't already have. PydanticAI's `pydantic-graph` already provides the finite state machine semantics.

This architecture gives you the Responses API's performance advantages (caching, server-side tool execution, reasoning token preservation) without sacrificing any of the control your research pipeline requires.