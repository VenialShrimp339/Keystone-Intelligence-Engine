# OpenAI Switchover: Research Prompts

**Context for all prompts:** We're migrating the Keystone Intelligence Engine, a multi-agent AI consulting research system, from Anthropic Claude (Opus 4.6 / Sonnet 4.6 / Haiku) to OpenAI models accessed via Codex OAuth subscription (ChatGPT Pro, $200/mo). The goal is zero per-token LLM API costs -- the entire pipeline runs against the subscription quota. The system uses PydanticAI as the agent framework, with a 6-layer pipeline: L0 Spec Engine, L1 Research Agents (3-5 parallel), CitationProcessor, L1.5 Deliberation, L2/L3 Content Structuring/Generation (Phase 2), and L4 Evaluator.

**Current model landscape (verified April 2026):**
- GPT-5.3 Instant: fast everyday model, default in ChatGPT
- GPT-5.4 (standard): general purpose, strong coding + reasoning + computer use. $2.50/$15 per 1M tokens (API).
- GPT-5.4 Thinking: deeper reasoning, complex multi-step problems. Trades speed for depth. Replaced o-series reasoning models.
- GPT-5.4 Pro: maximum compute allocation, highest quality. $30/$180 per 1M tokens (API). Pro/Business/Enterprise only.
- GPT-5.4 Mini: fast, lower-cost for lighter tasks and subagents.
- GPT-5.4 Nano: API only, lightest weight.
- GPT-5.3-Codex: most capable agentic coding model, optimized for long-horizon tasks.
- GPT-5.3-Codex-Spark: near-instant coding iteration, Pro only research preview.
- O-series models (o3, o4-mini, etc.) are retired from ChatGPT as of Feb 13, 2026. Not relevant.

**Codex OAuth confirmed facts:**
- Standard /v1/chat/completions endpoint, authenticated via OAuth instead of API key
- Cline, OpenClaw, and other third-party tools officially use this path
- PydanticAI's OpenAI provider accepts a custom AsyncOpenAI client
- Pro plan: 300-1,500 messages per 5-hour rolling window (range varies by task complexity)
- As of April 2, 2026: Codex pricing aligned with API token usage (credits per million tokens)
- Responses API is OpenAI's recommended path for agents (built-in agentic loop, state management, 40-80% better caching)

---

## PROMPT 1: Codex OAuth Model Access, Quotas, and Rate Limits
**Run as: Deep Research**

```
I'm building a multi-agent research pipeline that will run entirely on
an OpenAI ChatGPT Pro subscription ($200/month) via Codex OAuth -- zero
API credits, subscription-only. I need precise, current (April 2026)
answers to the following:

1. EXACT MODELS AVAILABLE VIA CODEX OAUTH ON PRO:
   - The Codex developer docs say "for most tasks, start with gpt-5.4"
     and mention gpt-5.4-mini and gpt-5.3-codex. But what is the
     COMPLETE list of models accessible when authenticated via Codex
     OAuth on a Pro subscription?
   - Specifically: is GPT-5.4 Thinking available via Codex OAuth?
   - Is GPT-5.4 Pro available via Codex OAuth?
   - Is GPT-5.3 Instant available via Codex OAuth?
   - Is GPT-5.4 Nano available via Codex OAuth?
   - The Codex docs also say "you can also point Codex at any model and
     provider that supports either the Chat Completions or Responses
     APIs." Does this mean ANY model in the OpenAI API is accessible
     through OAuth, or only models explicitly listed for Codex?
   - Are there models available in the ChatGPT UI (model picker) that
     are NOT available via the Codex OAuth API path?

2. QUOTA MECHANICS FOR PRO:
   - The help docs say Pro gets 300-1,500 messages per 5-hour rolling
     window. What determines where in that range a given message falls?
     Is it input token count? Output token count? Model used?
   - As of April 2, 2026, Codex pricing shifted to "credits per million
     tokens." How does this interact with the Pro subscription?
     Does Pro give you a fixed number of credits per month/period?
     What's the credit budget?
   - If I send 5 concurrent requests (parallel research agents), do
     they each consume from the same 5-hour window?
   - What happens when the Pro quota is exhausted mid-5-hour window?
     Hard block? Throttled to slower model? Error response?
   - Is there any mechanism to purchase additional credits on top of
     the Pro subscription (burst capacity)?

3. MODEL-SPECIFIC QUOTA COSTS:
   - Does using GPT-5.4 Thinking consume more quota than GPT-5.4
     standard for the same input?
   - Does GPT-5.4 Pro consume more quota than GPT-5.4 standard?
   - If quota is measured in token-credits, what are the credit rates
     per model? (This determines whether I can afford to use Thinking/
     Pro for my judgment layers.)

4. PRACTICAL CAPACITY ESTIMATE:
   - A single research engagement in my pipeline involves approximately:
     * 1 L0 call (spec generation): ~2K input, ~4K output
     * 15-30 L1 calls (research agents): ~3K input, ~2K output each
     * 15-30 citation processing calls: ~1K input, ~500 output each
     * 5-10 L1.5 deliberation calls: ~5K input, ~3K output each
     * 15-30 L4 evaluation calls: ~4K input, ~2K output each
     * Total: roughly 60-120 LLM calls, ~250K-500K total tokens
   - Can a Pro subscription handle this workload in a single 5-hour
     window? Multiple engagements per day?
   - What's the realistic throughput ceiling?

5. RESPONSES API VIA OAUTH:
   - Can the Responses API (not just Chat Completions) be used through
     Codex OAuth authentication?
   - If yes, do the same quota mechanics apply?
   - Does the Responses API's built-in state management
     (store: true) reduce quota consumption for multi-turn agent
     conversations?

For every claim, cite the specific source (OpenAI docs URL, help center
article, developer blog post, or community report). If specific numbers
aren't publicly documented, say so explicitly and provide the best
available estimates from community experience.
```

---

## PROMPT 2: GPT-5.4 Behavioral Characteristics for Multi-Agent Research Pipelines
**Run as: Normal Claude chat with web search**

```
I'm migrating a multi-agent research pipeline from Anthropic Claude
to OpenAI GPT-5.4 family models. The pipeline has these specific LLM
interaction patterns, and I need to understand how GPT-5.4 handles
each one differently from Claude:

PATTERN 1: SPECIFICATION GENERATION (currently Claude Opus 4.6)
The model receives a natural-language research question plus client
context, and must produce a structured JSON output containing:
- An issue tree (MECE decomposition of the question)
- 15-50 research tasks, each with acceptance criteria, tool
  assignments, anti-confirmatory framing, and priority ordering
- A task dependency DAG (directed acyclic graph)
This requires deep analytical reasoning and very precise structured
output. The output is ~4,000 tokens of JSON.
QUESTION: How does GPT-5.4 Thinking compare to Claude Opus 4.6 for
this kind of structured analytical decomposition? Does GPT-5.4
Thinking reliably produce valid, complex JSON without schema
violations?

PATTERN 2: RESEARCH AGENT LOOP (currently Claude Sonnet 4.6)
The model receives a research task + system prompt defining its
analytical methodology (quantitative, qualitative, contrarian, etc.)
and iteratively calls MCP tools (web search, financial data APIs,
academic paper search), processes results, and synthesizes findings.
This involves 3-8 tool call rounds per task.
QUESTION: How does GPT-5.4 (standard) compare to Claude Sonnet 4.6
for multi-turn tool use loops? Does GPT-5.4 maintain coherent
research direction across many tool calls, or does it lose the
thread? How does it handle tool errors (API failures, empty results)?

PATTERN 3: EVALUATION AND JUDGMENT (currently Claude Opus 4.6)
The model receives a research output, a sprint contract (acceptance
criteria), the original task, and a citation manifest. It must:
- Score across 10 rubric dimensions (0-100 each)
- Provide specific, actionable feedback per dimension
- Apply a "three-pass" evaluation (broad scan, deep analysis,
  gestalt check)
- Catch citation fabrications and factual errors
QUESTION: How does GPT-5.4 Thinking (or GPT-5.4 Pro) compare to
Claude Opus 4.6 for this kind of critical evaluation? Is GPT-5.4
more or less likely to be a "harsh grader" vs a "lenient grader"?
Does it tend to produce more specific or more generic feedback?

PATTERN 4: CITATION AND SOURCE HANDLING
Our pipeline requires precise attribution: every claim must cite a
specific source with URL, and the evaluator checks for fabricated
citations (hallucinated URLs, made-up paper titles).
QUESTION: What is GPT-5.4's current hallucination rate for citations
compared to Claude? When given explicit context documents, does
GPT-5.4 reliably cite from provided sources rather than inventing
references?

PATTERN 5: SYSTEM PROMPT ADHERENCE
Our agents have detailed system prompts (500-2000 tokens) specifying
analytical methodology, output format, and behavioral constraints
(e.g., "you must evaluate evidence both for and against the
hypothesis").
QUESTION: How does GPT-5.4 compare to Claude in following complex,
multi-part system prompts? Are there known failure modes where
GPT-5.4 ignores specific instructions?

PATTERN 6: EXTRACTION AND CLASSIFICATION (currently Claude Haiku)
Simple, fast tasks: extract structured data from search results,
classify findings by category, parse citation metadata.
QUESTION: How does GPT-5.4 Mini compare to Claude Haiku for speed
and accuracy on extraction tasks? Is GPT-5.4 Nano a viable
alternative for these lightweight tasks?

I need practical comparisons based on real-world usage, not benchmark
scores. Developer blog posts, community comparisons, and hands-on
reports are most valuable. Where direct Claude-to-GPT comparisons
don't exist, characterize GPT-5.4's behavior independently so I can
assess the gap myself.
```

---

## PROMPT 3: PydanticAI + OpenAI Integration Technical Deep Dive
**Run as: Normal Claude chat with web search**

```
I'm using PydanticAI as the agent framework for a multi-agent system.
Currently targeting Anthropic Claude, switching to OpenAI. I need the
precise technical integration details as of April 2026.

1. PYDANTIC AI OPENAI PROVIDER:
   - PydanticAI docs show OpenAIProvider accepts a custom AsyncOpenAI
     client. Can I pass an AsyncOpenAI client that uses an OAuth bearer
     token instead of an API key?
   - Specifically: does AsyncOpenAI support setting a custom
     Authorization header, or do I need to set the api_key field
     to the OAuth token?
   - Does PydanticAI's OpenAI provider support the Responses API, or
     only Chat Completions? (This matters because the Responses API
     is OpenAI's recommended path for agents.)
   - Does PydanticAI support OpenAI's "reasoning_effort" parameter
     for GPT-5.4 Thinking? (low/medium/high/xhigh)
   - Does PydanticAI support OpenAI's structured output mode
     (response_format with JSON schema)?
   - How does PydanticAI handle OpenAI's parallel tool calls
     (multiple tool_calls in a single response)?

2. CODEX-AUTH LIBRARY:
   - Current state of the codex-auth PyPI package
   - How does it integrate with AsyncOpenAI? Does it provide a
     drop-in replacement, or does it return tokens that you manually
     inject?
   - Token refresh behavior: what happens when a token expires
     during a long-running agent session (30+ minutes)?
   - Does it support concurrent requests from the same OAuth session?
   - Any known issues, limitations, or version conflicts?

3. OPENAI FUNCTION CALLING (current state):
   - Exact request format for tool definitions in Chat Completions API
   - Exact request format for tool definitions in Responses API
   - How does "strict mode" (guaranteed schema adherence) work?
   - What JSON schema features does strict mode support? (anyOf,
     allOf, $ref, enum, const, optional fields, nested objects?)
   - Can I force the model to always call a tool (tool_choice:
     "required") vs allowing free-form responses?
   - Maximum number of tools per request?
   - How do parallel tool calls work in practice? (Model returns
     multiple tool_calls in one response -- does PydanticAI handle
     this automatically?)

4. RESPONSES API SPECIFICS:
   - What built-in tools does the Responses API provide?
     (web_search, code_interpreter, file_search, etc.)
   - Can I mix built-in Responses API tools with custom function
     tools in the same request?
   - How does the stateful mode (store: true) work for multi-turn
     agent conversations?
   - What's the actual caching benefit? (The 40-80% improvement
     claim -- is this verified in practice for agent workflows?)

5. MIGRATION CHECKLIST:
   - What are the specific differences between Anthropic's tool_use
     content blocks and OpenAI's tool_calls format that will affect
     my PydanticAI agent definitions?
   - PydanticAI is supposed to abstract this away -- does it fully?
     Or are there provider-specific behaviors that leak through?
   - Are there any PydanticAI features that work with Anthropic
     but NOT with OpenAI (or vice versa)?

Provide code examples using the latest PydanticAI and openai Python
SDK versions. I need working patterns, not conceptual explanations.
```

---

## PROMPT 4: Responses API Architecture Implications for Custom Agent Orchestration
**Run as: Deep Research**

```
I'm building a custom multi-agent orchestration system (Keystone
Intelligence Engine) that currently implements its own agent loop:

- A generator-based orchestrator dispatches tasks to agents
- Each agent runs an async loop: receive task -> call tools ->
  process results -> call more tools -> synthesize findings
- The orchestrator handles parallelism (3-5 concurrent agents),
  error recovery, and cross-agent coordination
- Tool calls go through an MCP gateway that handles auth,
  rate limiting, and per-agent tool authorization

OpenAI's Responses API provides a BUILT-IN agentic loop that can
handle multi-step tool calling within a single API request. This
creates a fundamental architectural question: should I use the
Responses API's built-in orchestration, keep my custom orchestration,
or create a hybrid?

I need analysis on:

1. RESPONSES API AGENTIC LOOP:
   - How exactly does the built-in agentic loop work? When the model
     makes a tool call, does the API execute it and feed results back
     automatically? Or does it return the tool call for me to execute
     and then I send results back?
   - For CUSTOM function tools (not built-in ones like web_search),
     does the Responses API still provide automatic looping? Or is
     the loop only for built-in tools?
   - Can I intercept between tool call rounds in the Responses API
     loop? (I need to enforce per-agent tool authorization, rate
     limiting, and logging at each step.)

2. CUSTOM ORCHESTRATION COMPATIBILITY:
   - If I keep my own orchestration loop and just use the Responses
     API as a "smart completion endpoint" (one call at a time, I
     manage the loop), do I still get the caching benefits?
   - Can I use the stateful mode (store: true) with manual
     orchestration to avoid resending full conversation history?
   - What's the interaction between the Responses API's state
     management and PydanticAI's agent conversation management?

3. HYBRID APPROACH:
   - Could I use the Responses API's built-in web_search tool as a
     REPLACEMENT for my Exa/Brave MCP tool calls? (The Responses API
     web_search is free/included -- if it's good enough, it saves
     external API costs.)
   - Could I use code_interpreter for data analysis tasks within
     research agents instead of custom extraction code?
   - Can I use BOTH built-in Responses API tools AND my custom MCP
     tools in the same agent session?

4. PRACTICAL TRADEOFFS:
   - What control do I lose by letting the Responses API manage the
     agent loop vs doing it myself?
   - For a research pipeline where I need: per-agent tool
     authorization, detailed event logging at each step, error
     recovery with alternative strategies, and cross-agent
     coordination -- is the Responses API loop sufficient, or do
     I need my own?
   - What are the latency implications? (My current approach makes
     individual API calls per tool round. The Responses API batches
     multiple rounds into one request -- is this faster or slower
     in practice?)

5. WHAT ARE PRODUCTION TEAMS ACTUALLY DOING?
   - Are multi-agent systems like mine (research pipelines, complex
     workflows) using the Responses API loop in production, or are
     they using it as a completion endpoint with custom orchestration?
   - How are tools like OpenClaw, Cline, and Codex CLI using the
     Responses API? Do they use the built-in loop or manage their own?
   - Any case studies or technical blog posts about migrating custom
     agent orchestration to the Responses API?

This determines whether we're doing a simple provider swap (keep our
architecture, change the LLM backend) or a deeper architectural
refactor (leverage the Responses API's capabilities to simplify our
orchestration layer).
```

---

## Implementation Scoping: What the Research Feeds Into

Once you bring back results from all four prompts, here's what I'll map against the actual codebase. Every file listed below is a confirmed touchpoint:

### Tier 1: Must Change (provider swap)
| File | What changes | Depends on |
|------|-------------|------------|
| `src/keystone/models/config.py` | `AnthropicConfig` -> `OpenAIConfig`, model ID strings, env var names | Prompt 1 (model names) |
| `src/keystone/models/tasks.py` | `ModelTier` enum values (opus/sonnet/haiku -> GPT-5.4 variants) | Prompt 1 (which models) |
| `src/keystone/models/agents.py` | `AgentDefinition.model` field, docstrings referencing Claude tiers | Prompt 1 |
| `.env` / `.env.example` | `ANTHROPIC_API_KEY` -> OAuth config, model ID env vars | Prompt 3 (codex-auth) |
| `src/keystone/evaluator/retry.py` | `LLMCallable` may need to change signature if Responses API differs | Prompt 3, 4 |
| `src/keystone/evaluator/evaluator.py` | LLM instantiation, any Anthropic-specific patterns | Prompt 3 |

### Tier 2: Should Optimize (behavioral adaptation)
| File | What changes | Depends on |
|------|-------------|------------|
| `src/keystone/specification/prompts/task_generation.md` | System prompt tuning for GPT-5.4 Thinking | Prompt 2 (behavioral) |
| `src/keystone/evaluator/rubric_config.py` | Score calibration if GPT-5.4 grades differently than Claude | Prompt 2 |
| `src/keystone/evaluator/three_pass.py` | Three-pass evaluation prompts tuned for GPT-5.4 | Prompt 2 |
| `src/keystone/specification/template_registry.py` | Agent specialization templates | Prompt 2 |
| `src/keystone/models/config.py` `ModelMixingConfig` | Tier assignments: which GPT-5.4 variant for each layer | Prompt 1 + 2 |

### Tier 3: Opportunity (new capabilities)
| Capability | What it enables | Depends on |
|-----------|----------------|------------|
| GPT-5.4 Thinking for L0/L4 | Deeper reasoning for spec generation and evaluation | Prompt 1 (quota cost) |
| GPT-5.4 Pro for critical evaluations | Maximum quality for L4 judgment calls | Prompt 1 (availability via OAuth) |
| Responses API built-in web search | Potentially replace Exa/Brave for basic searches | Prompt 4 |
| Responses API state management | Reduce token overhead in multi-turn agent sessions | Prompt 4 |
| User-configurable model tier | "Use Thinking for this engagement" toggle | Prompt 1 + architecture |
| `reasoning_effort` parameter | Dial reasoning depth per call (low for extraction, xhigh for judgment) | Prompt 1, 3 |

### Tier 4: Architecture Decision (may restructure)
| Decision | Options | Depends on |
|----------|---------|------------|
| Keep custom agent loop vs Responses API loop | Keep ours / Use theirs / Hybrid | Prompt 4 |
| Dual-provider fallback | OpenAI primary + Claude API fallback if quota exhausted | All prompts |
| Responses API for multi-turn | store:true state mgmt vs our own context management | Prompt 3, 4 |
| Model tier count | 3 tiers (match current) vs 4-5 tiers (exploit GPT-5.4 variant depth) | Prompt 1, 2 |

---

## Execution Order

1. **Prompt 1** (Deep Research, ~15 min) -- BLOCKER. Everything depends on knowing which models are actually available via OAuth and what quota costs.
2. **Prompt 2** (Claude chat, ~5 min) -- can run in parallel with Prompt 1.
3. **Prompt 3** (Claude chat, ~5 min) -- can run in parallel with Prompt 1 and 2.
4. **Prompt 4** (Deep Research, ~15 min) -- can run in parallel with all others, but its findings are most useful after Prompt 1 results are known.
5. **Bring all results back to Cowork session** -- I'll synthesize against the codebase and produce the complete switchover implementation plan.
