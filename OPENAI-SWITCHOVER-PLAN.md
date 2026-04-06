# OpenAI Switchover Plan

*Date: 2026-04-06 | Author: Claude Code (Opus 4.6, Session 16)*
*Based on: 4 research reports, full codebase audit, JACK-ARCHITECTURAL-DIRECTIVES.md*

---

## Executive Summary

The migration is a **provider swap, not an architecture rewrite**. PydanticAI abstracts tool definitions, structured output, and agent orchestration across providers. Our generator-based agent loop, Protocol contracts, and event system remain unchanged. The Responses API slots in as the completion backend. The real work is: rename config/enums, set up OAuth token management, and tune prompts for GPT-5.4's behavioral differences.

One critical finding reshapes the economics: **Codex OAuth quotas are marginal for our workload**. The research recommends a hybrid auth strategy or API key path for the automated pipeline. This needs a decision from Jack.

---

## 1. Architecture Decisions (Resolved)

### Decision 1: Model Tier Mapping

**Decision: Expand from 3 tiers to 4. Keep the tier abstraction provider-agnostic.**

The current `ModelTier` enum (`OPUS`/`SONNET`/`HAIKU`) maps cleanly to GPT-5.4 variants, but the GPT-5.4 family offers a useful fourth tier (Mini) between standard and Nano that has no Claude equivalent.

| Tier | Purpose | Old Model | New Model | Rationale |
|------|---------|-----------|-----------|-----------|
| `FLAGSHIP` | L0 spec, L4 eval, L1.5 aggregator | `claude-opus-4-6` | `gpt-5.4` | GPT-5.4 is the flagship via Codex OAuth. GPT-5.4 Thinking is not a separate slug; `gpt-5.4` includes reasoning. Report 1 confirms this. |
| `STANDARD` | L1 research agents, L1.5 analysts, L2/L3 | `claude-sonnet-4-6` | `gpt-5.4` | Same model. GPT-5.4 via OAuth has no mid-tier equivalent to Sonnet. `gpt-5.4-mini` is too weak for multi-turn research (Report 2: incomplete execution, constraint drift). Use `gpt-5.4` with lower `reasoning_effort` for throughput tasks. |
| `FAST` | Citation processing, extraction, classification | `claude-haiku-4-5` | `gpt-5.4-mini` | 30% of GPT-5.4 quota cost. Report 2 confirms Mini handles simple schemas reliably. Handles extraction/classification at Haiku-equivalent quality. |
| `LIGHT` | Initial filtering, routing, trivial extraction | *(none)* | `gpt-5.4-mini` | Same model as FAST for now. If API key auth is used, `gpt-5.4-nano` becomes available here at 5x cheaper than Mini. Codex OAuth does not expose Nano. |

**Why not GPT-5.4 Pro for L0/L4?** Report 1: "not explicitly listed on the Codex models page" for OAuth. Its availability is undocumented and uncertain. Do not plan around it.

**Why not separate the "Thinking" mode?** Report 1: "GPT-5.4 Thinking is the ChatGPT UI presentation name... not a separate Codex model slug." In Codex, you use `gpt-5.4` and control depth via `reasoning_effort` (low/medium/high/xhigh). This is better modeled as a per-call setting, not a tier.

**`reasoning_effort` mapping per pipeline layer:**

| Layer | `reasoning_effort` | Why |
|-------|-------------------|-----|
| L0 Specification | `xhigh` | Deep analytical decomposition; MECE trees |
| L1 Research | `medium` | Throughput; tool calling doesn't benefit from xhigh |
| L1.5 Deliberation (analysts) | `medium` | Independent analysis |
| L1.5 Deliberation (aggregator) | `xhigh` | Synthesis judgment |
| L4 Evaluator | `high` | Critical evaluation; catch fabrications |
| Extraction/classification | `low` | Simple schema extraction |

**Implementation note:** The tier names become provider-agnostic (`FLAGSHIP`/`STANDARD`/`FAST`/`LIGHT`). The actual model IDs are in config, not code. If we ever add Claude back as a fallback, the same tiers map to Opus/Sonnet/Haiku without code changes.

### Decision 2: Responses API vs Custom Agent Loop

**Decision: Keep our custom generator-based orchestration. Use Responses API as the completion backend. Hybrid with selective built-in tools.**

This was the clearest finding across all four reports. Report 4 is definitive:

> "The Responses API's agentic loop only runs server-side for built-in tools; custom function tools always return to your client for execution."

> "PydanticAI always manages its own orchestration loop -- it does not delegate the tool call loop to the Responses API."

> "For the Keystone Intelligence Engine's specific requirements -- per-agent tool authorization, detailed event logging, error recovery with alternative strategies, and cross-agent coordination -- the Responses API's built-in loop is insufficient."

Our architecture is validated:
- **contracts.py**: All 9 Protocol interfaces remain unchanged. They define async generators yielding typed events -- completely provider-agnostic.
- **events.py**: 34 typed events remain unchanged. The event system is our observability layer, orthogonal to the LLM provider.
- **gateway/mcp_gateway.py**: Auth -> rate limit -> circuit break -> execute -> audit pipeline. This is our control layer. The Responses API's built-in loop would bypass all of this.
- **evaluator/retry.py**: `LLMCallable = Callable[[str], Awaitable[str]]` stays as-is. PydanticAI's `agent.run()` returns a string result. The abstraction holds.

What we gain from the Responses API (without giving up control):
- **Prompt caching**: 40-80% better cache utilization. Keep instructions and tool definitions stable at the front of requests. Automatic for prompts >= 1,024 tokens.
- **`previous_response_id`**: Server-side state management for multi-turn agent conversations. Reduces bandwidth. PydanticAI exposes this via `OpenAIResponsesModelSettings(openai_previous_response_id='auto')`.
- **Built-in tools**: Selective use (see Decision 4).

**Critical constraint from Report 1:** `store: true` is NOT supported on the Codex OAuth endpoint. The backend requires `store: false`. This means `previous_response_id` chaining does NOT work via OAuth. It only works with API key auth. If Jack goes OAuth-only, we lose server-side state management and must manage conversation history client-side (which PydanticAI already does).

### Decision 3: Dual-Provider or Hard Cutover

**Decision: Hard cutover to OpenAI for Phase 1. Design for provider-agnostic config so fallback can be added in Phase 2.**

Rationale:
- Jack's constraint is zero per-token API costs. Claude API charges per-token. Maintaining a Claude fallback means either accepting per-token costs when the fallback fires, or maintaining unused code.
- PydanticAI's `FallbackModel` makes adding Claude back trivial later (Report 3 shows the pattern: `FallbackModel(OpenAIResponsesModel('gpt-5.4'), AnthropicModel('claude-sonnet-4-6'))`).
- Report 2 shows GPT-5.4 is weaker on system prompt adherence (80% completion rate vs Claude's near-100%). This is a real quality risk for our complex methodology prompts. **Mitigation: prompt engineering for GPT-5.4** (see Section 4), not dual-provider fallback.
- Directive 5: correct architecture at reduced depth. Get one provider working well before adding complexity.

**The provider-agnostic config design** (renaming `AnthropicConfig` to `LLMProviderConfig`, tier names to `FLAGSHIP`/`STANDARD`/`FAST`/`LIGHT`) makes it trivial to add Claude back later without rework. This satisfies the "can it be added later without changing data flow?" test from Directive 13.

### Decision 4: Responses API Built-in Tools

**Decision: Add built-in `web_search` as a supplementary tool for research agents. Keep Exa and Brave as primary research tools via MCP gateway.**

Report 4 is clear:

> "Web search works well for general queries but falls short of research-grade needs... no raw content extraction, limited domain filtering compared to Exa's 1,200-domain support, no date range filtering, and inconsistent results on complex multi-hop queries."

> "Exa excels at semantic/neural search (81% on complex retrieval benchmarks)"

> "Built-in web search costs $10 per 1,000 calls plus search content tokens... Exa at $2.50/1k, Brave at $5/1k"

The built-in `web_search` is useful for:
- Quick supplementary lookups within research agent sessions (background context, terminology, current events)
- Situations where Exa/Brave are rate-limited or unavailable

It is NOT suitable as a replacement for Exa/Brave for:
- Primary research retrieval (lower quality on complex queries)
- Citation-grade sourcing (no raw content extraction)
- Domain-specific financial/regulatory research

**Implementation:** Add `web_search` as an optional built-in tool in PydanticAI agent configs via `openai_builtin_tools=[{'type': 'web_search'}]`. This runs server-side (no MCP gateway routing needed) but also means no gateway-level logging/rate-limiting. Log the search results when they appear in the agent's response.

**`code_interpreter` -- defer.** Report 4 suggests it for data analysis tasks. We don't have data analysis agents in Phase 1. Add when needed.

---

## 2. Quota Budget and Auth Strategy

### The Quota Problem

Report 1 is stark. Our pipeline per engagement:
- 60-120 LLM calls, ~250K-500K total tokens
- Pro subscription: 300-1,500 messages per 5-hour rolling window

At face value, one engagement fits. But:
- **Community reports** show complex GPT-5.4 tasks can yield as few as ~33 messages per 5-hour window
- **Concurrent subagent accounting bug** (GitHub issue #9748): "launching concurrent subagents instantly drains entire Pro plan usage quota." OpenAI acknowledged but may not be fully resolved.
- **Weekly cap** is the binding constraint: "Pro users describe exhausting weekly limits in 2-3 days of heavy usage"

### Recommended Auth Strategy

**Use API key authentication for the automated pipeline, not Codex OAuth.**

Report 1's own conclusion:

> "A hybrid auth strategy is likely optimal. Use Codex OAuth for interactive/ad-hoc work... but switch your automated PydanticAI pipeline to API key authentication for predictable per-token billing."

> "OpenAI explicitly recommends API key auth for programmatic Codex CLI workflows"

At standard API rates: ~500K tokens with GPT-5.4 costs **$3-$15 per engagement**. This is within the original $12-$100 cost target from CLAUDE.md.

**This contradicts Jack's "zero per-token" constraint.** But the research makes it clear that Codex OAuth's quota mechanics are operationally fragile for automated multi-agent workloads. Jack needs to make a call:

| Option | Cost | Reliability | Complexity |
|--------|------|-------------|------------|
| **A: API key only** | $3-15/engagement | High (predictable) | Low |
| **B: OAuth only** | $200/mo flat | Low (quota bugs, weekly caps) | Medium |
| **C: OAuth primary + API key burst** | $200/mo + $3-15 overflow | Medium | High |
| **D: OAuth for dev/testing, API key for production** | $200/mo + per-engagement | High | Medium |

**Recommendation: Option D.** Use the $200/mo Pro subscription for interactive development, testing, and ad-hoc runs. Use API key auth for production engagements where predictability matters. The code supports both paths (same `AsyncOpenAI` client, different auth config). Per-engagement cost of $3-$15 is well within the original cost target.

**If Jack insists on Option B (OAuth only):** We must implement model-tier optimization aggressively (GPT-5.4-mini for 80%+ of calls at 30% quota cost), serialize parallel agents (no concurrent subagents until bug #9748 is resolved), and accept 1-2 engagements/day throughput ceiling with risk of quota exhaustion.

---

## 3. Implementation Plan (Ordered Sessions)

### Session A: Provider Config Swap (Tier 1 -- Must Change)

**Goal:** Replace all Anthropic references. Tests pass with new enum values.

**Files to modify:**

1. **`src/keystone/models/tasks.py`** (lines 39-47)
   - Rename `ModelTier` values: `OPUS` -> `FLAGSHIP`, `SONNET` -> `STANDARD`, `HAIKU` -> `FAST`
   - Add `LIGHT = "light"` tier
   - Update docstring to be provider-agnostic

2. **`src/keystone/models/config.py`** (lines 16-32, 89-121, 155-184)
   - Rename `AnthropicConfig` -> `LLMProviderConfig`
   - Replace model ID defaults: `claude-opus-4-6` -> `gpt-5.4`, `claude-sonnet-4-6` -> `gpt-5.4`, `claude-haiku-4-5-20251001` -> `gpt-5.4-mini`
   - Add `reasoning_effort` field per tier
   - Add `api_type` field: `"api_key"` or `"oauth"`
   - Add `oauth_token_endpoint` and `oauth_client_id` fields (optional)
   - Rename `anthropic_rpm` -> `provider_rpm` in `RateLimitConfig`
   - Update `ModelMixingConfig` tier string defaults: `"opus"` -> `"flagship"`, `"sonnet"` -> `"standard"`, `"haiku"` -> `"fast"`
   - Update `AppConfig` env var names: `ANTHROPIC_API_KEY` -> `OPENAI_API_KEY`, `OPUS_MODEL` -> `FLAGSHIP_MODEL`, etc.
   - Update `anthropic_rpm_limit` -> `provider_rpm_limit`

3. **`src/keystone/models/agents.py`** (lines 72-75)
   - Change `default=ModelTier.SONNET` -> `default=ModelTier.STANDARD`
   - Update description to be provider-agnostic

4. **`.env.example`** (full rewrite)
   - Replace `ANTHROPIC_API_KEY` with `OPENAI_API_KEY`
   - Replace model ID vars: `FLAGSHIP_MODEL`, `STANDARD_MODEL`, `FAST_MODEL`
   - Add `OPENAI_AUTH_TYPE=api_key` (or `oauth`)
   - Keep search API keys unchanged (Exa, Brave, CrossRef, OpenAlex)

5. **`src/keystone/evaluator/evaluator.py`** (line 54)
   - Change usage comment from `anthropic_client` to `llm_client`

6. **`src/keystone/specification/template_registry.py`** (7 templates, lines 37-142)
   - Change all `model=ModelTier.SONNET` -> `model=ModelTier.STANDARD`

7. **`src/keystone/specification/task_generator.py`** (line 139)
   - Change fallback `"sonnet"` -> `"standard"`

8. **`src/keystone/specification/decomposer.py`** (docstring lines 3-6)
   - Update "Sonnet-tier" and "Opus-tier" references to "standard-tier" and "flagship-tier"

9. **`src/keystone/specification/validator.py`** (docstring lines 3, 44)
   - Update "Opus as judge" -> "flagship model as judge"

10. **`src/keystone/specification/prompts/task_generation.md`** (line 59)
    - Change `"assigned_model": "sonnet"` -> `"assigned_model": "standard"`

11. **`src/keystone/models/__init__.py`**
    - Verify `ModelTier` re-export still works (should be automatic)

12. **`pyproject.toml`**
    - Add `openai>=1.60.0` to dependencies (needed for Responses API support)
    - Add `pydantic-ai>=1.77.0` to dependencies (needed for `OpenAIResponsesModel`)
    - Remove the commented-out `anthropic` dependency line

**Test files to update:**

| File | Change |
|------|--------|
| `tests/unit/test_research_models.py` | `ModelTier.OPUS/SONNET/HAIKU` -> `FLAGSHIP/STANDARD/FAST` |
| `tests/unit/specification/test_template_registry.py` | `ModelTier.SONNET` -> `ModelTier.STANDARD` |
| `tests/unit/specification/test_task_generator.py` | `"sonnet"` -> `"standard"` |
| `tests/unit/specification/test_spec_engine.py` | `"sonnet"` -> `"standard"` |
| `tests/unit/evaluator/test_sprint_contract.py` | `ModelTier` references |
| `tests/fixtures/evaluator/sample_research_task.json` | `"assigned_model": "sonnet"` -> `"standard"` |

**Validation:** All 486 existing tests must pass after this session. This is a pure rename + config change with no behavioral changes.

### Session B: OAuth Token Management + PydanticAI Integration

**Goal:** Create the LLM client factory that produces configured PydanticAI agents.

**New files to create:**

1. **`src/keystone/llm_client.py`** -- LLM client factory
   - `create_openai_client(config: LLMProviderConfig) -> AsyncOpenAI`
     - If `api_type == "api_key"`: standard `AsyncOpenAI(api_key=config.api_key)`
     - If `api_type == "oauth"`: `AsyncOpenAI(api_key=TokenManager(refresh_fn))` using callable pattern from Report 3
   - `create_provider(client: AsyncOpenAI) -> OpenAIProvider`
   - `create_model(provider, model_id, reasoning_effort) -> OpenAIResponsesModel`
   - `get_model_for_tier(tier: ModelTier, config: LLMProviderConfig) -> OpenAIResponsesModel`
   - Token refresh with async locking and 5-minute buffer (Report 3 pattern)

2. **`src/keystone/llm_settings.py`** -- Per-layer model settings
   - `get_settings_for_layer(layer: str) -> OpenAIResponsesModelSettings`
   - Maps pipeline layers to `reasoning_effort`, `openai_builtin_tools`, etc.
   - Keeps `store: false` for OAuth path, `store: true` for API key path

**Key patterns from Report 3:**
```python
# OAuth token management
client = AsyncOpenAI(api_key=token_manager)  # callable api_key

# Responses API model
model = OpenAIResponsesModel('gpt-5.4', provider=OpenAIProvider(openai_client=client))

# PydanticAI agent with Responses API
agent = Agent(model, instructions='...')

# Per-run model settings
result = await agent.run(prompt, model_settings=OpenAIResponsesModelSettings(
    openai_reasoning_effort='high',
    openai_builtin_tools=[{'type': 'web_search'}],
))
```

**Dependencies:** Requires Session A (provider config) to be complete.

### Session C: Prompt Tuning for GPT-5.4 (Tier 2 -- Behavioral)

**Goal:** Adapt system prompts for GPT-5.4's documented behavioral differences.

**The core problem from Report 2:**

> "The most common failure mode -- the model delivering 80% of what you asked for and quietly dropping the rest."

> "Markdown instruction drift -- adherence degrades over long conversations, requiring re-injection every 3-5 messages."

**Mitigation strategies per Report 2:**
1. Use XML-tagged instruction blocks: `<structured_output_contract>`, `<research_mode>`, `<persistence>`
2. Add explicit "completeness contracts" listing required deliverables
3. Use scoped constraints ("after the final JSON, output nothing further") instead of broad ones
4. Re-inject critical instructions periodically in multi-turn sessions

**Files to modify:**

1. **`src/keystone/specification/prompts/task_generation.md`**
   - Add `<structured_output_contract>` wrapper around JSON schema requirements
   - Add explicit completeness checklist at the end
   - This is the highest-risk prompt (complex JSON output, 4K tokens)

2. **`src/keystone/specification/prompts/decompose_*.md`** (3 lens prompts + synthesis)
   - Add MECE completeness contract
   - Wrap analytical constraints in `<research_mode>` tags
   - Add explicit "you MUST evaluate evidence both for and against" reinforcement

3. **`src/keystone/specification/prompts/mece_validation.md`**
   - Add structured output block with all 5 binary dimensions listed

4. **`src/keystone/evaluator/prompts/*.md`** (14 files)
   - Add `<evaluation_contract>` wrapper specifying exact output format
   - Re-inject scoring rubric constraints within each prompt
   - Add explicit "score on a 0-100 scale, provide specific actionable feedback per dimension"
   - **Priority: gestalt_overlay.md, intent_alignment.md, intellectual_honesty.md** (Tier 1 dimensions where GPT-5.4's harshness bias matters most)

5. **`src/keystone/evaluator/rubric_config.py`**
   - **Defer calibration changes.** Report 2 says GPT-5.4 is a harsh grader (odds ratio 0.33 vs human). But we don't have calibration data yet. Build Component #7 first, run it, collect scores, THEN calibrate. Per Directive 5: correct architecture, reduced depth.

**Dependencies:** Independent of Sessions A/B. Can run in parallel.

### Session D: Documentation + Handoff Updates

**Goal:** Update all project documentation to reflect the switchover.

**Files to update:**

1. **`CLAUDE.md`** -- Update deployment context, model mixing section, key terms
2. **`CURRENT-STATE.md`** -- Rewrite to reflect switchover, new next steps
3. **`SESSION-LOG.md`** -- Append switchover session entry
4. **`docs/ARCHITECTURE.md`** -- Add llm_client.py, llm_settings.py, update config descriptions
5. **`JACK-ARCHITECTURAL-DIRECTIVES.md`** -- Add Directive 15: provider migration rationale
6. **`audit/PHASE-1-IMPLEMENTATION-SPEC.md`** -- Update Component #7 spec for OpenAI (model strings, Responses API patterns)

**Dependencies:** After Sessions A+B are complete.

---

## 4. Prompt Migration Notes

### GPT-5.4 Behavioral Differences That Affect Our Prompts

| Behavior | Claude | GPT-5.4 | Impact | Mitigation |
|----------|--------|---------|--------|------------|
| System prompt adherence | ~100% on complex prompts | ~80% ("quietly drops constraints") | HIGH: methodology specs in L0/L4 | XML-tagged instruction blocks, completeness contracts |
| Structured JSON output | Grammar-based constrained generation | Token-level constrained decoding (strict mode) | LOW: GPT-5.4 is actually better here | Use `response_format: {type: "json_schema"}` with PydanticAI `NativeOutput` |
| Evaluation calibration | Approximates human judgment | Systematically overcritical (OR 0.33) | MEDIUM: L4 scores will skew low | Defer calibration to post-Component #7. Consider floor adjustment. |
| Citation fabrication | Less likely to fabricate confidently | Higher fabrication rate without retrieval context | MEDIUM: L4 citation gate exists | Reinforce citation-from-context constraints in prompts. Layer 2 gate catches fabrications. |
| Multi-turn coherence | Strong long-context understanding | "Less reliable at tool routing early in session" | MEDIUM: L1 research agents | Provide richer initial context. Re-inject task description periodically. |
| Sycophancy | "Moral remorse" pattern | Improved to <6% but uneven | LOW: evaluation prompts designed to resist this | Anti-confirmatory framing already built in |

### Specific Prompt Patterns for GPT-5.4

**Before (Claude-optimized):**
```
You are an evaluator. Score this output on intent alignment (0-100).
Consider whether the output addresses the original question.
Provide specific feedback.
```

**After (GPT-5.4-optimized):**
```
<evaluation_contract>
You MUST produce exactly this output format:
- score: integer 0-100
- feedback: 2-4 specific, actionable sentences
- evidence: quote the exact passage that supports your score

Do NOT omit any field. Do NOT add commentary outside this format.
After the JSON output, output nothing further.
</evaluation_contract>

<scoring_rubric>
Intent Alignment measures whether the output directly addresses the
original research question. Score 0-100 where:
- 90-100: Directly answers the question with evidence
- 70-89: Addresses the question but misses secondary aspects
- 50-69: Partially addresses the question
- Below 50: Does not address the core question
</scoring_rubric>

Score this output on intent alignment.
```

---

## 5. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Codex OAuth quota exhaustion mid-engagement** | HIGH (if Option B) | Pipeline stalls | Option D (API key for production). Or: model-tier optimization + serialized agents. |
| **Concurrent subagent quota bug (#9748)** | MEDIUM | Full 5-hour budget drained | Serialize parallel agents on OAuth path. Rate-limit to max 2 concurrent. |
| **GPT-5.4 drops system prompt constraints** | HIGH | Lower quality L0 specs, L4 evaluations | XML-tagged instruction blocks, completeness contracts, periodic re-injection |
| **GPT-5.4 evaluation score inflation/deflation** | HIGH | Scores not calibrated to human judgment | Run Component #7 first, collect data, then calibrate rubric_config.py |
| **GPT-5.4 citation fabrication in research agents** | MEDIUM | Fabricated sources in output | Layer 2 citation gate catches fabrications. Reinforce citation-from-context in prompts. |
| **OAuth token expiry during long agent session** | LOW | 401 error, agent fails | TokenManager with preemptive refresh (5-min buffer). retry_llm_call catches transient failures. |
| **`store: false` requirement on OAuth breaks state management** | LOW | Must manage conversation history client-side | PydanticAI already manages history client-side. No code change needed. |
| **PydanticAI version incompatibility** | LOW | Build failure | Pin to `>=1.77.0` (current stable with Responses API support) |
| **"Individual use only" restriction** | LOW (Phase 1) | Legal concern for multi-user deployment | Phase 1 is Jack-as-sole-operator. Multi-tenant is Phase 2+ concern. |
| **Model availability changes** | LOW | OAuth model list changes | Config-driven model IDs. Update .env, not code. |

---

## 6. Quota Budget Estimate

### Per-Engagement Token Budget

| Pipeline Stage | Calls | Avg Tokens/Call | Total Tokens | Model | Credit Cost (Legacy) |
|---------------|-------|-----------------|-------------|-------|---------------------|
| L0 Specification | 1 | ~6K | ~6K | gpt-5.4 | ~5 credits |
| L1 Research (3 agents, 3 rounds each) | ~27 | ~5K | ~135K | gpt-5.4 | ~135 credits |
| CitationProcessor | ~20 | ~1.5K | ~30K | gpt-5.4-mini | ~6 credits |
| L1.5 Deliberation | ~8 | ~8K | ~64K | gpt-5.4 | ~40 credits |
| L4 Evaluation | ~20 | ~6K | ~120K | gpt-5.4 | ~100 credits |
| **Total** | **~76** | | **~355K** | | **~286 credits** |

### If using GPT-5.4-mini aggressively (Option B optimization)

Route L1 research + CitProc + some L4 dimensions through GPT-5.4-mini:
- 47 calls at gpt-5.4-mini (30% cost): ~14 credits
- 29 calls at gpt-5.4 (full cost): ~145 credits
- **Total: ~159 credits** (44% reduction)

### Throughput under Pro subscription

- **OAuth (legacy rate card):** 300-1,500 messages/5hr. Mixed usage: **1-2 engagements per 5-hour window**, likely limited to 3-5 per day by weekly cap. Risky.
- **API key (standard pricing):** ~355K tokens at GPT-5.4 rates ($2.50/$15 per 1M) = **~$6-$7 per engagement**. Run as many as needed. Well within original $12-$100 target.

---

## 7. New Capabilities: Integrate Now vs Defer

### Integrate Now (Sessions A-D)

| Capability | Where | Why Now |
|-----------|-------|---------|
| `reasoning_effort` parameter | `llm_settings.py` | Direct quality/cost lever. Maps to `OpenAIResponsesModelSettings`. Zero additional complexity. |
| Built-in `web_search` | Agent configs in Component #7 | Free supplementary search. PydanticAI supports via `openai_builtin_tools`. |
| Prompt caching (automatic) | Implicit with Responses API | No code needed. Keep instructions/tools stable at front of requests. 40-80% cache improvement. |
| Structured output strict mode | PydanticAI `NativeOutput` | Better JSON reliability than Claude. Use for all structured outputs. |

### Defer to Phase 2

| Capability | Why Defer |
|-----------|-----------|
| `previous_response_id` state management | Not supported on OAuth path. Only useful with API key auth. Add when auth strategy is finalized. |
| `code_interpreter` built-in tool | No data analysis agents in Phase 1. |
| User-configurable model tier toggle | Requires UI. Phase 2. |
| PydanticAI `FallbackModel` (dual-provider) | Directive 5: get one provider working first. |
| Evaluation score recalibration | Need data from Component #7 runs first. |
| `Conversations API` for long-lived state | Newer than Responses API, not yet in PydanticAI. |

---

## 8. Validation

### Against Jack's Architectural Directives

| Directive | Compliance | Notes |
|-----------|------------|-------|
| D1 (Templates not constraints) | MAINTAINED | Template registry templates unchanged. ModelTier rename is cosmetic. |
| D2 (MECE issue trees) | MAINTAINED | Decomposer logic unchanged. Only docstring and tier references updated. |
| D3 (Iterative research) | MAINTAINED | Generator-based loop unchanged. Responses API is backend, not orchestrator. |
| D5 (Correct architecture, reduced depth) | COMPLIANT | Provider swap first, tune later. Prompt changes are structural (XML tags), not depth changes. |
| D7 (Two HITL gates) | MAINTAINED | HITL module is fully provider-agnostic. |
| D9 (Retry + dead-letter) | MAINTAINED | `retry_llm_call` is `Callable[[str], Awaitable[str]]`. Provider-agnostic. |
| D11 (Configurable pipeline depth) | MAINTAINED | Light/Standard/Deep profiles unaffected. |
| D13 (Phase 1/Phase 2 staging) | COMPLIANT | Defer calibration, dual-provider, state management to Phase 2. |
| D14 (Goldman-grade quality) | AT RISK | GPT-5.4's 80% system prompt adherence is the primary quality risk. XML-tagged prompts mitigate. Must validate empirically. |

### Existing Test Suite Impact

**Tests that will break (Session A):** All tests referencing `ModelTier.OPUS`, `ModelTier.SONNET`, `ModelTier.HAIKU`, or string literals `"opus"`, `"sonnet"`, `"haiku"`. These are pure rename fixes.

**Tests that will NOT break:** All evaluator tests (mock LLM), all gateway tests (MockMCPClient), all HITL tests (database state machine), all knowledge tests (filesystem ops), all citation tests (hash/dedup/URL). These are provider-agnostic.

### Protocol Interface Stability

All 9 `contracts.py` Protocol interfaces remain unchanged:
- `SpecificationEngineContract.generate_spec()` -- takes strings, yields events
- `ResearchAgentContract.execute()` -- takes models, yields events
- `EvaluatorContract.evaluate()` -- takes models, yields events
- etc.

The `LLMCallable` type alias in `evaluator/retry.py` (`Callable[[str], Awaitable[str]]`) is the narrowest integration point. It stays. The actual LLM call implementation (what produces the `Awaitable[str]`) changes from an Anthropic client to a PydanticAI agent run, but the interface doesn't.

---

## 9. Open Questions for Jack

1. **Auth strategy:** Option A (API key, $3-15/engagement), Option B (OAuth, $200/mo flat but fragile), Option C (hybrid), or Option D (OAuth for dev, API for prod)? The research strongly recommends against Option B for production workloads.

2. **Cost tolerance:** Is $3-15/engagement acceptable if it means predictable execution? This is within the original $12-$100 target but violates the "zero per-token" constraint.

3. **Quality risk acceptance:** GPT-5.4's 80% system prompt adherence rate means some methodology constraints will be silently dropped. XML-tagged prompts mitigate but don't eliminate. Are you comfortable running Component #7 first and evaluating quality empirically before committing fully?

4. **`codex-auth` vs direct OAuth:** Report 3 says `codex-auth` is "community-built and not for production." If OAuth is chosen, we need to implement our own token management using the callable `api_key` pattern. Alternatively, the standard `openai` SDK with an API key is dramatically simpler.
