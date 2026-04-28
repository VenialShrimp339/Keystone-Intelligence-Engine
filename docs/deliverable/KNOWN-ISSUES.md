# Known Issues

Issues discovered during pipeline development and the first two real runs (April 22-28, 2026). Each issue includes root cause analysis and what was learned from it.

---

## Fixed Issues

### F-1: LLM call timeouts across multiple pipeline stages
- **Severity:** CRITICAL (blocked L0 task generation, L1.5 deliberation, L4 fact decomposition)
- **Root cause:** The original hardcoded timeout was 300 seconds for all `claude -p` subprocess calls. Deep research sessions with extended web browsing need 20-40 minutes. Even standard LLM calls processing large inputs (13 tasks, 155 claims) exceeded 5 minutes.
- **Fix:** Three-stage progression: 300s → 600s configurable default (commit `e13f40c`) → split into two timeout paths: `claude_cli_timeout_s` at 1200s for regular calls, `deep_research_timeout_s` at 2400s for web research (commit `38c5e87`). The config field is now wired through `LayerAwareLLMFactory` to the actual subprocess call.
- **What we learned:** The quality improvement of richer task descriptions (80-120 words vs. the original 50 words) generated research sessions that need 20-40 minutes, not 5-10. The timeout problem was caused by the quality improvement — a good trade that needed infrastructure to catch up.

### F-2: LLM returns invalid model tier values
- **Severity:** HIGH (crashed downstream processing)
- **Root cause:** The LLM occasionally returns model tier strings that don't match the expected enum values — e.g., "reasoning" or "advanced" instead of "standard" or "flagship."
- **Fix:** Graceful coercion with fallback to default tier. Committed in `00e9101`.
- **What we learned:** Any field where the LLM chooses from an enum needs a coercion layer. The pipeline now treats LLM-generated enum values as suggestions, not contracts.

### F-3: Deliberation crashes when all analysts fail
- **Severity:** HIGH (blocked L1.5)
- **Root cause:** The aggregator assumed at least one analyst would succeed. When all analysts timed out (e.g., due to usage limits hitting mid-deliberation), it raised an unhandled exception.
- **Fix:** Graceful degradation — if all analysts fail, emit a governance flag and skip deliberation. Committed in `00e9101`.
- **What we learned:** Every `asyncio.gather` of LLM calls needs a total-failure path. The assumption "at least one will succeed" is false in production.

### F-4: Task generation timeout on large task sets
- **Severity:** HIGH (blocked L0)
- **Root cause:** Generating structured JSON for all 13-15 tasks in a single LLM call exceeded the timeout window.
- **Fix:** Chunked task generation into batches of 5 tasks per LLM call. Committed in `006e428`.
- **What we learned:** Any LLM call that generates N structured items should chunk at ~5 items per call. The output quality per item also improves with smaller batches — less context competition.

### F-5: Fact decomposition timeout in evaluator
- **Severity:** HIGH (blocked L4 Layer 1 deterministic checks)
- **Root cause:** Same pattern as F-4 — extracting atomic facts from the entire research output in one call.
- **Fix:** Chunked fact decomposition into batches of 5-8 claims per call. Committed in `006e428`.
- **What we learned:** Same lesson as F-4. The chunking pattern is now standard across the pipeline for any LLM call processing variable-length input.

### F-6: Consulting-specific language in prompt headers
- **Severity:** MEDIUM (biased output for non-business questions)
- **Root cause:** 15 of 38 prompt `.md` files contained consulting-specific language ("client engagement," "deliverable," "Monday-morning recommendation") in their headers and framing. The first run against a software architecture question produced research framed as if advising a consulting client on a technical decision.
- **Fix:** Systematic prompt audit identified all 38 prompts: 15 domain-neutral (no changes), 12 partially biased (headers de-biased), 11 consulting-specific (headers de-biased, body text still needs domain-conditional templates). Committed in `96d6632`.
- **What we learned:** Prompt bias is invisible until you test with a question from a different domain. The audit approach — categorize every prompt, fix systematically — was more effective than ad-hoc patching.

### F-7: No intermediate artifact output
- **Severity:** MEDIUM (debugging impossible)
- **Root cause:** All intermediate state was in-memory only. When the pipeline crashed mid-run, there was no way to inspect what each layer produced.
- **Fix:** Each pipeline stage now writes its output to `output/{engagement_id}/`. Committed in `006e428`.
- **What we learned:** Observability is not optional in multi-stage LLM pipelines. The intermediate artifacts are also valuable for iterating on individual layers without re-running the entire pipeline.

### F-8: No crash recovery
- **Severity:** MEDIUM (lost all progress on failure)
- **Root cause:** A crash mid-pipeline (e.g., from hitting usage limits) meant re-running everything from scratch — including expensive L1 deep research sessions.
- **Fix:** Checkpoint store backed by SQLite with 5 stage boundaries (POST_SPEC, POST_L1_CITPROC, POST_DELIBERATION, POST_STRUCTURING, POST_EVALUATION). `PipelineRunner.resume()` skips completed stages. Committed in `761bc6f`.
- **What we learned:** Any pipeline where a single stage costs $10-50 in API calls needs checkpoint/resume. The checkpoint design also enabled the `resume_from_l1.py` script that lets us iterate on downstream layers without repeating research.

### F-9: `ref://` placeholder URLs in citation chain
- **Severity:** HIGH (fake citations in output)
- **Root cause:** The LeadResearcher's citation forwarding path was replacing real URLs with internal `ref://` placeholders during sub-agent result merging.
- **Fix:** Citations now carry real URLs through the entire PartialFinding → StructuredFinding chain. Committed in `4a0dc33`.
- **What we learned:** Citation integrity must be a structural invariant, not a prompt instruction. The fix was in the data pipeline (Pydantic model fields), not in the prompts.

### F-10: `claude_cli_timeout_s` config field not wired to subprocess
- **Severity:** LOW (required environment variable workaround)
- **Root cause:** `PipelineConfig` had a `claude_cli_timeout_s` field, but the subprocess call read directly from `AppConfig`, bypassing the pipeline config.
- **Fix:** `_build_llm_callable` now accepts `cli_timeout_s`, `LayerAwareLLMFactory` threads it through. Default raised to 1200s. Committed in `38c5e87`.
- **What we learned:** Config fields that aren't wired to the actual execution path are worse than no config — they create false confidence that a parameter is being respected.

---

## Open Issues

### O-1: Deliberation times out on real data
- **Severity:** CRITICAL (blocks the pipeline from completing)
- **Root cause:** Four deliberation analyst agents each attempt to process 155 claims from 6 task findings. At 600s timeout, all four exhaust 3 retry attempts. The most recent fix raised the timeout to 1200s but this has not been tested against real data yet.
- **Impact:** The pipeline completes L0 → L1 → CitProc but cannot proceed past L1.5. This is the immediate blocker for a full end-to-end run.
- **Path forward:** The 1200s timeout should help, but the underlying issue is that analyst prompts receive all 155 claims. Chunking or claim selection may be needed.

### O-2: Decomposition lenses are hardcoded
- **Severity:** CRITICAL for generality (works for business questions, breaks for everything else)
- **Root cause:** `_LENSES = ["financial", "operational", "market"]` in `decomposer.py`. These three lenses are consulting-engagement defaults. For a question like "how to architect an agentic research system," the financial lens produces branches about revenue models and unit economics. The first run against a software architecture question missed 7-9 of 16 benchmark research streams entirely.
- **Impact:** The auto body repair test question worked because it's a business question. The system cannot handle technical, scientific, or non-business research questions at acceptable quality.
- **Path forward:** A dynamic `LensSelector` is designed — it analyzes the question domain and selects 2-4 appropriate lenses from a larger menu. Implementation is next after the deliberation timeout is resolved.

### O-3: MCP tool servers are mocked
- **Severity:** HIGH (shallow research mode is dead)
- **Root cause:** The MCP Gateway has tool definitions, auth, rate limiting, and circuit breaker logic, but the actual transport layer uses `MockMCPClient`. The configured MCP servers (Exa, Brave, EDGAR) don't actually launch.
- **Impact:** Only deep research mode (`claude -p` with its own tool access) produces real data. The standard shallow research path produces empty results. This means every research run requires the expensive deep mode.
- **Path forward:** FastMCP-based client replacing `MockMCPClient`, wiring stdio server launches for each configured tool server.

### O-4: No narrative synthesis layer
- **Severity:** HIGH (the primary quality gap vs. benchmark)
- **Root cause:** There is no component between L1 research and L1.5 deliberation that transforms flat claims into analytical hierarchy. The pipeline produces "155 JSON claims" where the benchmark produces "one 5,000-word analytical brief with a synthesizing thesis."
- **Impact:** The pipeline produces research material, not a deliverable. A human analyst would need to read all 155 claims and write the synthesis themselves.
- **Path forward:** A `NarrativeSynthesizer` between L1 and L1.5 that produces cross-cutting themes, claim hierarchy, and a Situation-Complication-Resolution argument from flat claims.

### O-5: Evaluator rubric prompts still have consulting language in body text
- **Severity:** MEDIUM
- **Root cause:** F-6 fixed the headers of all prompt files, but `actionability.md` and `intent_alignment.md` still use consulting-specific language ("client," "engagement") throughout their body text.
- **Impact:** Evaluation scoring may be slightly biased toward consulting-style output for non-consulting questions.
- **Path forward:** Domain-conditional template variables so prompt body text adapts to engagement type.

### O-6: Hardcoded deliberation analyst types
- **Severity:** MEDIUM
- **Root cause:** The four analyst methodologies (ACH, quantitative, adversarial, historical analogy) are fixed as `DEFAULT_ANALYST_TYPES`. The constructor accepts an `analyst_types` parameter, but nothing passes domain-appropriate types. For a software architecture question, more appropriate methodologies would be systems engineering assessment, failure mode analysis, and comparative architecture review.
- **Impact:** Same domain mismatch problem as O-2, but at the deliberation layer.
- **Path forward:** Thread engagement domain from L0 classification through to deliberation; select analyst types per domain.

### O-7: Interactive clarification loop not implemented
- **Severity:** MEDIUM
- **Root cause:** The pipeline takes a question string and immediately decomposes it. The intent clarifier can set `intent_clear=False`, but the pipeline has no mechanism to surface clarifying questions, wait for user input, and resume. In the first run, the clarifier returned `intent_clear=True` on a complex, multi-faceted question with at least five unresolved ambiguities.
- **Impact:** The system confidently decomposes ambiguous questions into potentially wrong research tasks. Garbage in, structured garbage out.
- **Path forward:** `ClarificationNeeded` event type + HITL-like gate in the orchestrator that pauses and waits for user input when `intent_clear=False`.

### O-8: Content structuring doesn't thread domain to framework selector
- **Severity:** LOW
- **Root cause:** The L2 framework selector picks analytical frameworks (e.g., Porter's Five Forces) based on engagement type but doesn't receive domain classification. A technology evaluation could get a market analysis framework.
- **Path forward:** Pass domain classification from L0 through to L2 framework selector.

### O-9: L5 ensemble cross-model slot is interim
- **Severity:** LOW (functional but suboptimal)
- **Root cause:** The DEEP profile's third judge uses Sonnet (the same model family as the L1 generator), creating a "Play Favorites" risk where the evaluator may be biased toward output produced by a related model. This is explicitly documented as an interim placeholder.
- **Path forward:** Replace the Sonnet slot with an external provider (GPT-5.4 or Gemini) when a second provider family is wired into the LLM client factory.
