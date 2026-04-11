# Codex OAuth on ChatGPT Pro: models, quotas, and pipeline feasibility

**A ChatGPT Pro subscription provides access to GPT-5.4, GPT-5.4-mini, GPT-5.3-Codex, and GPT-5.3-Codex-Spark via Codex OAuth, but the 300–1,500 message/5-hour rolling window and weekly cap make a 60–120 call research pipeline marginal without supplemental credits or model-tier optimization.** The Codex OAuth path exclusively uses the Responses API (not Chat Completions), quota is shared across all concurrent agents, and Pro subscribers remain on legacy per-message pricing until OpenAI migrates them to the new token-based rate card. Below is a precise, sourced breakdown across all five areas you asked about.

---

## 1. Which models are actually accessible via Codex OAuth on Pro

The official Codex models page (developers.openai.com/codex/models) lists four recommended current models and several legacy ones. Here is the complete picture:

**Recommended models (all available via Codex OAuth on Pro):**

| Model slug | Notes | Quota impact |
|---|---|---|
| `gpt-5.4` | Flagship; recommended default for "most tasks in Codex" | Full rate |
| `gpt-5.4-mini` | Fast, efficient; uses **30% of GPT-5.4 quota** | ~0.3× |
| `gpt-5.3-codex` | Most capable dedicated coding model | Full rate |
| `gpt-5.3-codex-spark` | Research preview, **Pro-only**, separate usage limit, **NOT available via standard API** | Separate cap |

**Legacy models still accessible:** gpt-5.2-codex, gpt-5.2, gpt-5.1-codex-max, gpt-5.1, gpt-5.1-codex, gpt-5-codex, gpt-5-codex-mini, gpt-5. All of these work through Codex OAuth and appear on the official models page.

**Models NOT available or with caveats:**

- **GPT-5.4 Thinking** is the ChatGPT UI presentation name for GPT-5.4 in reasoning mode. It is not a separate Codex model slug — in Codex, you simply use `gpt-5.4`. The help center article (help.openai.com/en/articles/11909943) confirms this is a UI-layer distinction.
- **GPT-5.4 Pro** (`gpt-5.4-pro`) is available in ChatGPT and the standard API for Pro/Enterprise plans, but it is **not explicitly listed on the Codex models page**. Third-party tool OpenClaw lists it under the `openai/*` (API key) path but not under the `openai-codex/*` (OAuth) path (docs.openclaw.ai/providers/openai). Its availability through Codex OAuth is undocumented and uncertain.
- **GPT-5.4 Nano** is explicitly **API-only**. The official announcement (openai.com/index/introducing-gpt-5-4-mini-and-nano/) states: "GPT-5.4 nano is only available in the API." It is excluded from both Codex and ChatGPT.
- **GPT-5.3 Instant** is a ChatGPT UI conversation model, not a Codex model. It does not appear on the Codex models page.

**What "any model and provider" actually means:** The Codex docs state you can "point Codex at any model and provider that supports either the Chat Completions or Responses APIs." This refers to Codex's **custom model provider** system configured via `config.toml` — you can define alternative providers (Anthropic, Ollama, Azure OpenAI, OpenRouter) with custom base URLs. It is not a statement that all OpenAI API models are accessible through OAuth. Codex Cloud does not allow changing the default model; this flexibility exists only in CLI/IDE mode (developers.openai.com/codex/config-advanced).

**ChatGPT UI vs. Codex OAuth gap:** GPT-5.3 Instant and GPT-5.4 Pro are available in the ChatGPT model picker but not explicitly in Codex. Conversely, GPT-5.3-Codex-Spark is available only through Codex (Pro users), not in the ChatGPT conversation UI.

---

## 2. Quota mechanics: the 5-hour window and credit system

**The 300–1,500 range is real and documented.** The official pricing page (developers.openai.com/codex/pricing) shows Pro gets **300–1,500 local messages per 5-hour rolling window**, **50–400 cloud tasks per 5-hour window**, and **100–250 code reviews per week**. Local messages and cloud tasks share the same 5-hour window, with additional weekly limits.

**What determines where in the range you fall:** OpenAI states the number depends on "the model used, size and complexity of your coding tasks and whether you run them locally or in the cloud." Specifically, the factors are:

- **Model choice** — GPT-5.1-Codex-Mini provides up to **4× more usage** than GPT-5.3-Codex; GPT-5.4-mini uses 30% of GPT-5.4's quota
- **Task size** — larger codebases, longer context, more reasoning = more consumption per message
- **Speed configuration** — "fast mode" consumes **2× credits** across all models
- **Context injection** — MCP server count and AGENTS.md file size inflate per-message context costs

**The April 2 pricing transition does NOT yet apply to Pro.** The rate card (help.openai.com/en/articles/20001106-codex-rate-card) explicitly states: "Existing Plus/Pro and Enterprise/Edu customers should continue to use the **legacy rate card** displayed below, until we migrate you to the new rates in the future." The token-based system (credits per million tokens) currently applies only to new/existing ChatGPT Business and new Enterprise plans. Pro users should monitor for migration announcements.

**Legacy rate card (currently applies to Pro):**

| Task type | Unit | GPT-5.3-Codex / GPT-5.4 | GPT-5.1-Codex-Mini |
|---|---|---|---|
| Local tasks | per message | ~5 credits | ~1 credit |
| Cloud tasks | per message | ~25 credits | N/A |
| Code review | per PR | ~25 credits | N/A |

**Token-based rate card (coming to Pro eventually):**

| Model | Credits/1M input | Credits/1M cached input | Credits/1M output |
|---|---|---|---|
| GPT-5.4 | 62.50 | 6.250 | 375 |
| GPT-5.3-Codex | 43.75 | 4.375 | 350 |
| GPT-5.1-Codex-Mini | 6.25 | 0.625 | 50 |

**Concurrent agents share the same pool.** All parallel requests consume from the single account-level quota. OpenAI designed Codex for parallel agent work (openai.com/index/introducing-the-codex-app/), but a **critical known bug** (GitHub issue #9748) reports that "launching concurrent subagents instantly drains entire Pro plan usage quota." A community report (community.openai.com/t/codex-using-up-massive-credits-850-credits-5-hour-limit-used-on-only-8-queries/1364774) documented a user who burned through the entire 5-hour budget plus $48 in purchased credits with only 8 queries across 4 agents. OpenAI Support acknowledged this as a tracking bug and has issued compensatory credits.

**When quota is exhausted: hard block, not throttle.** Codex becomes unavailable until the 5-hour window refreshes. You see a banner offering to "Add credits." No overage charges apply to subscription plans, and there is no automatic downgrade to a slower model for Codex (unlike regular ChatGPT where Plus users may fall back to GPT-5.4-mini). For regular ChatGPT messaging, Pro retains "unlimited" access subject to abuse guardrails.

**Purchasing additional credits is supported.** Plus and Pro users can buy credits as a pay-as-you-go add-on via Codex Settings → Usage → Credits (help.openai.com/en/articles/12642688). Credits are consumed only after plan limits are exhausted. Auto top-up is available. Credits are non-refundable, valid for **12 months**, and shared across Codex and Sora. There is currently a **2× rate limits promotion** for all paid plans (developers.openai.com/codex/pricing).

---

## 3. Model-specific quota costs and the reasoning tax

**GPT-5.4 costs more quota than lighter models, and reasoning effort directly scales consumption.** Under the legacy rate card, both GPT-5.4 and GPT-5.3-Codex consume ~5 credits per local message on average, while GPT-5.1-Codex-Mini consumes ~1 credit — a **5× difference**. GPT-5.4-mini is documented to use 30% of GPT-5.4's quota.

Under the forthcoming token-based card, output tokens are dramatically more expensive than input tokens. **GPT-5.4 output costs 375 credits/1M tokens vs. 62.50 for input** — a 6:1 ratio. For reasoning-heavy models that produce long chain-of-thought outputs, this means reasoning effort is the primary cost driver. GPT-5.3-Codex has similar economics (350 credits/1M output). Cached input tokens cost approximately **10× less** than uncached input (6.250 vs. 62.50 for GPT-5.4), making prompt caching critical for multi-turn pipelines.

**GPT-5.4 Pro** is documented as using "more compute to think harder" (developers.openai.com/api/docs/models/gpt-5.4-pro), and for prompts exceeding 272K input tokens, pricing is **2× input and 1.5× output**. However, since GPT-5.4 Pro is not confirmed available via Codex OAuth, this may only apply to direct API usage.

**Practical implication for your pipeline:** Using GPT-5.4 for judgment/deliberation layers and GPT-5.4-mini for routine calls (research agents, citation processing) could yield a **3–5× improvement** in effective quota capacity versus using GPT-5.4 for everything.

---

## 4. Can your pipeline fit in a Pro subscription window

**The honest answer: it's marginal with GPT-5.4 and likely feasible with model-tier optimization, but risky without supplemental credits.**

Your described workload — 60–120 LLM calls, 250K–500K total tokens — maps to roughly the following under legacy pricing:

- **All GPT-5.4:** ~60–120 messages × ~5 credits = **300–600 credits** consumed. The Pro plan provides 300–1,500 messages per 5-hour window, so at best this consumes 8–40% of the window. However, community reports indicate complex GPT-5.4 tasks can yield as few as **~33 messages per 5-hour window** (getaiperks.com), which would make 120 calls impossible in a single window.
- **Mixed strategy (GPT-5.4-mini for routine, GPT-5.4 for judgment):** If 80% of calls use GPT-5.4-mini at 30% quota cost, effective consumption drops to ~40% of the all-GPT-5.4 scenario. This likely fits within a single 5-hour window.
- **Weekly cap is the binding constraint.** Community reports from Pro users describe exhausting weekly limits in **2–3 days** of heavy usage (github.com/openai/codex/discussions/2251). Running multiple 250K–500K token engagements per day would likely hit the weekly cap within 1–2 days.

**The concurrent subagent bug is a serious risk.** If your 5 parallel research agents trigger the accounting bug documented in issue #9748, a single engagement could drain the entire 5-hour budget regardless of actual compute. OpenAI has acknowledged this bug but it may not be fully resolved.

**Realistic throughput ceiling with supplemental credits:** Pro's included limits plus purchased credits (at ~$100–$200/developer/month average cost per OpenAI's own estimate) could sustain **2–4 research engagements per day** if using model tiering. Without credits, **1–2 per day** with careful model selection.

**Alternative worth considering:** Switching your pipeline to API key authentication for programmatic workloads. At standard API rates, 500K tokens with GPT-5.4 might cost **$3–$15 per engagement** — potentially cheaper and dramatically more predictable than subscription limits. OpenAI explicitly recommends API key authentication for "programmatic Codex CLI workflows (for example CI/CD jobs)" (developers.openai.com/codex/auth).

---

## 5. Responses API via OAuth is the only path, but store:true won't help

**The Codex OAuth endpoint exclusively uses the Responses API** — it is not optional; it is the only protocol. All requests route to `chatgpt.com/backend-api/codex/responses` when authenticated via ChatGPT OAuth, versus `api.openai.com/v1/responses` with API key auth (developers.openai.com/codex/auth). The Codex config reference confirms `wire_api = "responses"` is the only supported protocol value. Third-party tools (openai-oauth, codex-auth, OpenClaw) all confirm this same endpoint.

**The same subscription quota mechanics apply** to all Responses API calls made via OAuth. These are not the standard API rate limits (RPM, TPM) — they are subscription credit-based limits within the 5-hour/weekly window structure. If you authenticate with an API key instead, you get standard API per-token pricing with conventional RPM/TPM limits.

**`store: true` is NOT supported on the Codex OAuth endpoint.** The backend requires stateless operation (`store: false`). The OpenCode Codex Auth plugin documentation explicitly warns: "The Codex API requires stateless operation (store: false), where references cannot be resolved" (numman-ali.github.io/opencode-openai-codex-auth/configuration.html). GitHub issue #4047 confirms that even when `store: true` is set, `previous_response_id` is not used for multi-turn state. ZenML's architecture analysis explains that Codex "deliberately doesn't use [previous_response_id] to maintain stateless requests and support Zero Data Retention (ZDR) configurations."

Instead, Codex maintains reasoning context via **encrypted reasoning content** (`reasoning.encrypted_content`) that is returned and passed back in subsequent requests, and uses a `/responses/compact` endpoint for context window management. **Critically, even on the standard API path where `store: true` works, "all previous input tokens for responses in the chain are billed as input tokens"** (developers.openai.com/api/docs/guides/conversation-state) — so it reduces bandwidth complexity but not token billing.

**Max concurrent subagents defaults to 6** (`max_concurrent_subagents` in config reference). When the request queue is full, the app-server returns JSON-RPC error code -32001: "Server overloaded; retry later." No published RPM/TPM-style rate limits exist for the Codex OAuth path.

---

## Conclusion: recommendations for your PydanticAI pipeline

The zero-API-credit approach via Codex OAuth is technically possible but operationally fragile. Three key takeaways reshape the pipeline design:

**First, model tiering is non-negotiable.** Route research agents, citation processing, and evaluations through `gpt-5.4-mini` (30% quota cost) and reserve `gpt-5.4` exclusively for spec generation and deliberation calls. This alone could triple your effective window capacity.

**Second, the concurrent subagent accounting bug is a pipeline-breaking risk.** Until OpenAI resolves issue #9748, consider serializing or rate-limiting parallel agent calls rather than firing all 5 simultaneously. Monitor quota via `/status` between bursts.

**Third, a hybrid auth strategy is likely optimal.** Use Codex OAuth for interactive/ad-hoc work where "unlimited" ChatGPT messaging is valuable, but switch your automated PydanticAI pipeline to API key authentication for predictable per-token billing. At current API rates, your ~500K token workload would cost single-digit dollars per engagement — far more predictable than navigating opaque subscription limits, weekly caps, and known quota-tracking bugs. OpenAI's own documentation recommends API key auth for programmatic workflows, and the standard API path supports `store: true` with `previous_response_id` for proper multi-turn state management that could genuinely reduce redundant context in your agent conversations.