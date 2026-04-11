# OpenAI Switchover: Context from Cowork Session

You already know this codebase. You audited every component, fixed the tool name mismatches, cleaned up datetime warnings, trimmed deps, and regenerated ARCHITECTURE.md. This document gives you the NEW context that emerged from the Cowork planning session after your audit work completed. It covers a major strategic shift that affects the entire project.

---

## What Changed: Anthropic Is Out, OpenAI Is In

On April 4, 2026, Anthropic killed third-party harness OAuth access. Claude Max subscriptions ($100-200/month) cannot be used programmatically. The Anthropic API charges per-token on a completely separate billing system.

Jack's hard constraint: **zero per-token LLM API costs.** The entire Keystone pipeline must run against a flat-rate subscription. No API credits, ever. Non-negotiable.

The path forward is OpenAI's Codex OAuth. OpenAI officially supports third-party applications authenticating via ChatGPT subscriptions and hitting the standard `/v1/chat/completions` endpoint. Cline, OpenClaw, and the Codex CLI all use this in production. The `codex-auth` Python library provides drop-in OAuth for the `openai` SDK. PydanticAI's `OpenAIProvider` accepts a custom `AsyncOpenAI` client. This is not a workaround; it's the officially documented integration path that OpenAI actively encourages.

---

## The Model Landscape (Verified April 6, 2026)

The o-series models (o3, o3-pro, o4-mini) are dead. Retired from ChatGPT on February 13, 2026. GPT-5.4 Thinking absorbed the reasoning role. Do not reference or plan for o-series.

**The current GPT-5.4 family (released March 5, 2026):**

| Model | Role | Speed | Quality | API Pricing | Notes |
|-------|------|-------|---------|-------------|-------|
| GPT-5.4 | General purpose | Medium | High | $2.50/$15 per 1M tok | Recommended default for Codex tasks |
| GPT-5.4 Thinking | Deep reasoning | Slow | Very High | TBD | Replaced o-series. Has `reasoning_effort` param (low/med/high/xhigh) |
| GPT-5.4 Pro | Maximum compute | Slowest | Highest | $30/$180 per 1M tok | Pro/Business/Enterprise only |
| GPT-5.4 Mini | Fast/light | Fast | Good | Cheaper | For lighter tasks and subagents |
| GPT-5.4 Nano | Lightest | Fastest | Basic | Cheapest | API only |
| GPT-5.3 Instant | Everyday | Fast | Good | N/A (ChatGPT) | Default in ChatGPT UI, auto-switches to Thinking for complex queries |
| GPT-5.3-Codex | Agentic coding | Medium | Very High | N/A | Optimized for long-horizon agentic tasks |

**ChatGPT Pro subscription ($200/month):**
- 300-1,500 messages per 5-hour rolling window (range varies by task complexity/token count)
- As of April 2, 2026: pricing aligned with API token usage (credits per million tokens)
- Unlimited Codex usage with higher rate limits
- Access to GPT-5.4 Pro and GPT-5.3-Codex-Spark (Pro-exclusive)

---

## The Responses API: A Discovery That May Reshape Our Architecture

OpenAI's Responses API is their recommended replacement for Chat Completions for agent-based systems. This was NOT in the original project plan and could change how we build the orchestration layer.

Key differences from Chat Completions:
- **Built-in agentic loop:** For custom function tools, the API returns tool calls for you to execute and send results back, but with built-in state management across rounds.
- **Stateful mode (`store: true`):** Maintains conversation state server-side, eliminating the need to resend full conversation history each turn. 40-80% better cache utilization.
- **Built-in tools:** `web_search`, `code_interpreter`, `file_search`, `computer_use` are first-class. The `web_search` tool is potentially a free alternative to our Exa/Brave MCP tools for basic searches.
- **Long-term path:** Assistants API is sunsetting in 2026. Responses API is what OpenAI is pushing.

This creates a fundamental question: use the Responses API's capabilities to simplify our orchestration, keep our custom generator-based agent loop as-is, or create a hybrid? The research reports should have data to resolve this.

---

## What the Cowork Session Already Updated

- `.env` now has live keys: `EXA_API_KEY` and `BRAVE_SEARCH_API_KEY` are populated. `CROSSREF_POLITE_MAILTO` and `OPENALEX_POLITE_MAILTO` set to Jack's email. These are MCP gateway tool keys, provider-agnostic, and stay regardless of LLM switch.
- `OPENAI-SWITCHOVER-RESEARCH-PROMPTS.md` exists in the project root. It contains the four research prompts AND an "Implementation Scoping" section at the bottom that maps research questions to specific codebase files organized into four tiers. **Read this file, especially the Implementation Scoping section.**

---

## Provider-Sensitive Codebase Touchpoints

You already know these files from your audit. Here's what needs to change in each, organized by urgency.

**Tier 1: Must Change (direct provider references)**
- `src/keystone/models/config.py` — `AnthropicConfig` class (line 16), model ID strings (`claude-opus-4-6` etc.), `ModelMixingConfig` tier names (lines 89-121), `AppConfig` env vars (lines 155-184)
- `src/keystone/models/tasks.py` — `ModelTier` StrEnum (lines 39-48) with values `OPUS`, `SONNET`, `HAIKU`. Imported across the codebase.
- `src/keystone/models/agents.py` — `AgentDefinition.model` field (line 72) defaults to `ModelTier.SONNET`, docstrings reference Claude tiers
- `.env` / `.env.example` — `ANTHROPIC_API_KEY`, `OPUS_MODEL`, `SONNET_MODEL`, `HAIKU_MODEL` env vars
- `src/keystone/evaluator/retry.py` — `LLMCallable = Callable[[str], Awaitable[str]]` (line 15). Already provider-agnostic but may need changes for Responses API.
- `src/keystone/evaluator/evaluator.py` — Usage comment references `anthropic_client` (line 54)

**Tier 2: Should Optimize (behavioral adaptation)**
- `src/keystone/specification/prompts/task_generation.md` — System prompt needs testing/tuning for GPT-5.4 Thinking
- `src/keystone/evaluator/rubric_config.py` — Score calibration if GPT-5.4 grades differently
- `src/keystone/evaluator/three_pass.py` — Three-pass evaluation prompts
- `src/keystone/specification/template_registry.py` — 7 agent specialization templates

**Tier 3: Opportunity (new capabilities)**
- `reasoning_effort` parameter for GPT-5.4 Thinking: low for extraction, xhigh for L0/L4 judgment
- User-configurable model tier toggle: "use the heavy model for this engagement" (Jack's suggestion)
- Responses API built-in `web_search` as supplement/replacement for Exa/Brave
- Responses API state management to reduce token overhead in multi-turn agent sessions

**Tier 4: Architecture Decision (needs research input)**
- Custom agent loop vs Responses API agentic loop vs hybrid
- Dual-provider fallback (OpenAI primary + Claude API for quota overflow)
- Model tier count: 3 tiers (match current) vs 4-5 tiers (exploit GPT-5.4 variant depth)

---

## The "Individual Use Only" Restriction

Codex OAuth docs say it's "not for commercial services, API resale, or multi-user applications." For Jack-as-sole-operator running the harness on his own machine with his own subscription producing deliverables he gives to clients: that's individual use (consultant using a tool). Multi-tenant SaaS would not be. Not a Phase 1 blocker. Flag as future consideration.

---

## Your Task

### Step 0: Collect and Organize Research Reports

Check `~/Downloads/` for the four most recent markdown/document files. These are research reports Jack ran from the prompts in `OPENAI-SWITCHOVER-RESEARCH-PROMPTS.md`. They correspond to:
- **Report 1 (Deep Research):** Codex OAuth model access, quotas, rate limits, practical capacity
- **Report 2 (Claude chat):** GPT-5.4 behavioral differences for multi-agent research pipelines
- **Report 3 (Claude chat):** PydanticAI + OpenAI integration technical deep dive
- **Report 4 (Deep Research):** Responses API agentic loop vs custom orchestration architecture

Copy them into `research-reports/openai-switchover/` in the project directory. Name them clearly (e.g., `01-codex-oauth-models-quotas.md`, `02-gpt54-behavioral-differences.md`, `03-pydanticai-openai-integration.md`, `04-responses-api-architecture.md`). If you can't determine which is which from the content, use the file timestamps (most recent should be Report 4, oldest Report 1) and read the opening paragraphs to match them to the prompts.

### Step 1: Read Everything

Read all four reports completely. Also read `OPENAI-SWITCHOVER-RESEARCH-PROMPTS.md` (especially the Implementation Scoping section at the bottom).

### Step 2: Cross-Reference Against the Codebase

For each finding in the research reports, map it to specific files you already know. Identify:
1. **Confirmed changes** — research validates a change listed above
2. **New findings** — research surfaced something the Cowork session missed
3. **Contradictions** — research contradicts assumptions above (especially about quota capacity, model availability via OAuth, or Responses API + PydanticAI compatibility)
4. **Unresolved questions** — research didn't answer something critical

### Step 3: Resolve the Four Architecture Decisions

**Decision 1: Model Tier Mapping**
Current 3-tier (opus/sonnet/haiku) → which GPT-5.4 variants for each layer? Should we expand to 4-5 tiers?

**Decision 2: Responses API vs Custom Agent Loop**
Keep our generator-based loop? Use Responses API loop? Hybrid with state management?

**Decision 3: Dual-Provider or Hard Cutover**
OpenAI only? OpenAI primary + Claude fallback? Full provider-agnostic config?

**Decision 4: Responses API Built-in Tools**
Use built-in `web_search` to supplement/replace Exa and Brave?

### Step 4: Write the Implementation Plan

Output `OPENAI-SWITCHOVER-PLAN.md` in the project root containing:
1. Model tier mapping with exact model strings per pipeline layer, with rationale
2. Architecture decisions resolved with evidence from the research reports
3. Ordered implementation steps grouped into Claude Code sessions, with files affected and dependencies
4. Prompt migration notes for adapting system prompts from Claude to GPT-5.4
5. Risk register
6. Quota budget estimate (can Pro handle our workload?)
7. New capabilities to integrate now vs defer

### Step 5: Validate

Check your plan against:
- JACK-ARCHITECTURAL-DIRECTIVES.md (Directive 5: correct architecture at reduced depth, Directive 13: Phase 1/Phase 2 staging)
- The existing test suite (which tests will break?)
- `src/keystone/contracts.py` (Protocol interfaces should remain stable)
- `LLMCallable` in `src/keystone/evaluator/retry.py` (narrowest integration point)

---

## Quality Standards

- **Synthesize, don't summarize.** The value is connecting research findings to specific codebase decisions, not restating what the reports say.
- **Trace every recommendation to a file.** "The system prompt in `src/keystone/specification/prompts/task_generation.md` needs X change because GPT-5.4 handles Y differently per Report 2 finding Z" — not "we should adjust the prompts."
- **Don't conflate this with Component #7.** The switchover plan comes first. Component #7 build starts after.
- **Flag uncertainty.** If a report didn't answer something, say what's missing and how to resolve it.
- **Respect Directive 5.** Correct architecture at reduced feature depth. Get the provider swap working first, then tune.
