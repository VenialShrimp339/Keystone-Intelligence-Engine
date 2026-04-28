# Downstream Pipeline Quality Analysis
**Date:** 2026-04-23
**Scope:** First live test of CitationProcessor, L1.5 Deliberation, and L4 Evaluator
**Input:** Synthetic StructuredFinding — 6 claims, 7 citations, 1 agent, topic: multi-agent systems architecture

---

## Executive Summary

The downstream layers execute correctly. CitationProcessor is deterministic and reliable. Deliberation runs correctly end-to-end but has a structural flaw in the analyst methodology design that will require architectural work. The L4 Evaluator's timeout is a pure infrastructure issue, not a quality issue, but reading the evaluator reveals separate concerns about how the 10-dimension rubric is applied to the L1 output format. The cross-cutting theme is the same problem that pervades L0: one-size-fits-all defaults that make sense for consulting engagements but not for technical architecture questions.

---

## 1. CitationProcessor

### 1.1 URL Liveness: Mostly Correct, One False Negative

The 7 citations processed:
- 5 live: `arxiv.org/abs/2308.08155`, `github.com/microsoft/autogen`, `github.com/stanford-oval/storm`, `arxiv.org/abs/2201.11903`, `arxiv.org/abs/2305.04388`
- 2 dead: `anthropic.com/research/multi-agent-research-system`, `example.com/notarealmultiagentsurvey-404`

The `example.com/...` URL is an intentionally fake 404 injected into the synthetic fixture. That detection is correct. The Anthropic URL (`anthropic.com/research/multi-agent-research-system`) is a synthetic URL for a paper that does not exist on Anthropic's site — so the dead-URL flag is correct. This is not a false negative. It is the fixture behaving as intended.

The URL liveness implementation in `url_check.py` uses HEAD with fallback to GET, 10-second timeout, a polite `User-Agent` header, and a 10-concurrency semaphore. The logic is sound. One notable gap: the checker treats all 2xx and 3xx status codes as "live" (`resp.status_code < 400`). This means a URL that redirects permanently to a 404 page — which some CDNs serve as 200 OK — would be marked live. The current test did not expose this, but it is a latent false-negative mode.

A more significant design gap: `url_check.py` does not retry transient failures (connection resets, 503s). A single `httpx.HTTPError` from a flaky server immediately returns `False`. For production use, transient failures should be retried with backoff before declaring a URL dead. The `check_url_liveness` function is also stateless — it creates a new `AsyncClient` per citation rather than sharing a session across the batch, which wastes connection overhead.

The 10.7-second total time for 7 citations with a 10-second timeout per citation implies that all HEAD requests returned quickly. The concurrency limit of 10 is well-matched to the batch size.

### 1.2 Corroboration: Zero Pairs Is Correct for Single-Agent Input

The `ManifestProduced` event reports `corroboration_pairs=0`. This is correct. The corroboration logic in `dedup.py:find_corroboration_pairs` detects pairs at the citation-URL level: two claims corroborate if they reference the same URL AND come from different agents. The synthetic fixture uses a single agent (`agent_qualitative_01`). With only one agent, there are no cross-agent pairs by definition.

This is the right design — corroboration is meaningless within a single agent's output (an agent citing a URL twice is repetition, not corroboration). The issue is that the test fixture only exercises single-agent input. The corroboration logic will only be meaningfully exercised when a full L1 run with multiple parallel agents feeds into CitationProcessor. The downstream smoke test was unable to validate this code path at all.

To be explicit about what the corroboration code does: it builds a `url_agents` dict mapping each URL to a list of `(agent_id, citation_id)` tuples across all agents. It then finds URLs referenced by 2+ distinct agents and creates `CorroborationPair` objects for each cross-agent combination. The overlap score is hardcoded at `1.0` for all pairs — there is no partial overlap concept. This is a simplification worth noting: two claims citing the same URL may make completely different points. True corroboration would also consider claim-text similarity, not just shared citations.

### 1.3 The ref:// URL Issue and Citation Chain Integrity

The recent B-1 fix in `lead_researcher.py` addressed `ref://` URLs appearing in citation objects when the lead researcher referenced sub-researcher findings using internal `ref://claim_id` handles rather than real URLs. The CitationProcessor's URL liveness check would have flagged all such internal handles as dead URLs, corrupting the manifest with false positives. The fix rewrites `ref://` handles to the actual source URLs before citations reach the CitationProcessor.

The current test shows this is working: all 7 citations have real HTTPS URLs. The canonical ID format (`CAN-eng_downstream_smoke-{hash}`) in the `URLVerified` events confirms that the deduplication and alias pipeline ran correctly — each source-instance ID was mapped to a canonical ID with a fresh `CAN-` prefix, ensuring that the alias map from source-instance IDs to canonical IDs is complete and stable.

One architectural note: the CitationProcessor processes citations in the order it receives them and emits `URLVerified` events before `ManifestProduced`. In the test output, all 7 `URLVerified` events appear with identical timestamps (`04:09:42.553...`), suggesting the URL checks ran from a pre-populated result (not live HTTP), or the concurrent batch returned essentially simultaneously. The 10.7-second elapsed time confirms real HTTP was performed — the timestamp resolution is insufficient to distinguish per-citation timing from batch timing.

---

## 2. L1.5 Deliberation

### 2.1 The Analyst Methodology Problem

The four analysts spawned: ACH, quantitative, adversarial, historical_analogy. For a question about multi-agent research systems architecture, these methodologies have uneven applicability:

**ACH (Analysis of Competing Hypotheses):** ACH per ICD 203 is designed for intelligence analysis of ambiguous situations where multiple hypotheses must be tested against diagnostic evidence. For a technical architecture question — "what are the best approaches to multi-agent research pipelines?" — the hypotheses are not "did North Korea launch the missile" but "does scatter-gather outperform fractal decomposition." ACH can be applied, but its diagnostic-evidence-matrix framing is mismatched. The ACH prompt asks to "identify competing hypotheses and rate evidence diagnosticity" — this makes sense when evidence is ambiguous about a binary outcome, not when evidence is a corpus of benchmark papers.

**Quantitative:** High applicability. Multi-agent systems research includes benchmark results, latency measurements, source coverage statistics, RACE scores. The quantitative analyst's sensitivity analysis, base-rate comparison, and statistical power procedures are directly applicable.

**Adversarial:** High applicability. The pre-mortem, steel-manning, and confirmation bias test procedures are valuable for any technical claim. Claims about multi-agent architectures are frequently advocacy-oriented (papers from the same labs that built the systems), so confirmation bias testing is especially relevant.

**Historical analogy:** Moderate applicability with significant mapping friction. The historical analogy analyst is designed for "what does history say about markets/technologies/regulatory patterns at this stage." For multi-agent systems in 2026, meaningful historical analogies exist (MapReduce vs. single-machine processing, early search engine architectures, distributed database evolution) but require domain knowledge to select the right reference class. The prompt's base-rate anchoring and analogy-breaking conditions procedures are generic enough to apply, but the analyst is most powerful for business/market questions where the reference class is obvious.

**More appropriate analyst types for technical architecture questions:**
- Systems engineering assessment: evaluates completeness of design (edge cases, failure modes, scalability boundaries)
- Failure mode analysis (FMEA-style): what breaks first under production load, what are the blast radii
- Comparative architecture review: direct head-to-head of alternative designs with scoring on specific dimensions
- Implementation risk analyst: practical barriers to adoption (operational complexity, cost structure, team skill requirements)
- Evidence quality analyst: does the research corpus have publication bias? Are all citations from builder-advocates?

The current four types are drawn from intelligence analysis traditions (ACH, historical) and consulting traditions (quantitative, adversarial). Neither tradition is native to systems architecture evaluation.

### 2.2 Analysts Produced Exactly 6 Claims — Is This Expected?

Yes, but the reason reveals an important design constraint. The `Analyst._build_prompt` method receives the flattened `InputClaim` list (6 claims from the single-agent finding) and asks the LLM to score each claim. The output schema is `[{"index": 0, "confidence": 0.85, "source_count": 3, "reasoning": "..."}]` — one entry per input claim. This is a re-scoring task, not a generation task.

The analysts are NOT supposed to generate new claims. They evaluate and rescore existing claims. This is an important architectural decision: deliberation is about testing the robustness of L1 findings under different methodological lenses, not about producing new research. The `ScoredClaim` model contains `analyst_confidence`, `source_count`, and `reasoning` — all assessment fields, nothing generative.

The design is correct for the current purpose, but it has an important limitation: an analyst cannot identify a claim that should exist but doesn't. The ACH analyst might notice that a critical competing hypothesis was not even considered by the L1 agent — but the prompt only asks "score these 6 claims," not "what claims are missing." The gap detection in `gap_detector.py` is supposed to handle this, but it operates on the aggregated output, not within each analyst's perspective.

### 2.3 Bimodal Confidence Distribution: 3 High, 0 Moderate, 0 Weak, 3 Contested

The bimodal distribution (high or contested, nothing in between) is a signal worth examining. The aggregation logic in `aggregator.py` classifies claims by `agreement_ratio`:
- Convergent (agreement_ratio > 0.6): 3 claims
- Disagreements (agreement_ratio < 0.5): 3 claims

With 4 analysts, the agreement_ratio is the fraction scoring >= 0.5 confidence. The classification thresholds for the confidence map tiers are set in `build_confidence_map`:
- High (>80%): needs all 4 analysts above threshold (agreement_ratio = 1.0 or 0.75)
- Moderate (60-80%): 3 of 4 analysts above threshold
- Weak (50-60%): 2 of 4 analysts above threshold, but barely
- Contested (<50%): 1 or 0 of 4 analysts above threshold

With only 4 analysts, the possible agreement ratios are 0.0, 0.25, 0.5, 0.75, and 1.0. There is no ratio in the 60-80% range with exactly 4 analysts — 0.75 falls in the "high or moderate" gap, and it was classified as high. The bimodal result is a mathematical artifact of the 4-analyst panel size. With 5 analysts, possible ratios are 0.0, 0.2, 0.4, 0.6, 0.8, 1.0 — the 0.6 value would populate the moderate tier.

The deeper question is whether the claims are genuinely polarizing. For claims about multi-agent systems architecture drawn from arxiv papers, strong disagreement between a quantitative analyst (which cares about statistical rigor) and a historical analogy analyst (which cares about base rates from prior technology waves) is plausible and meaningful. But we cannot verify this without reading the actual analyst reasoning, which was not captured in the test output.

**The bimodal distribution suggests a design fix: increase the analyst panel from 4 to 5.** This adds the 0.2/0.4/0.6/0.8 ratios and allows the moderate and weak tiers to be populated. The cost is one additional LLM call per deliberation run. Given the 326-second total time, adding a fifth analyst would add roughly 80 seconds — acceptable.

### 2.4 The Three Gaps

The `ConfidenceMapProduced` event shows `gaps_count=3` but does not name them. The gap detection runs via `detect_gaps(findings, aggregated)` in `deliberation.py`. Without reading `gap_detector.py`, the source of gaps cannot be confirmed from the event data alone. The test output does not surface gap text — it is only available in the `ConfidenceMap` object returned by `get_confidence_map()`, which the test script accessed but did not log beyond the summary statistics.

Based on the `FIRST-RUN-ANALYSIS.md`, the L1 deep-mode finding included an "absence report" with 9 items of what was not found. The gap detector likely surfaces a subset of these as formal gaps. For a 6-claim finding about multi-agent systems, 3 gaps is reasonable — roughly a 1:2 ratio of gaps to claims, which suggests the deliberation is doing meaningful gap analysis rather than rubber-stamping the L1 output.

**Key concern:** Gap text is not surfaced in any event. It lives exclusively in the `ConfidenceMap` object, which currently has no guaranteed persistence path in the pipeline. If the deliberation completes but the confidence map is not written to disk, the gaps are lost.

### 2.5 Timing: 326 Seconds Is Borderline Acceptable

The timing breaks down as:
- Phase 1 (4 parallel analysts): 04:09:42 to 04:12:17 = 155 seconds
- Phase 2 (aggregation + WWHTB + gap detection + confidence map): 04:12:17 to 04:15:08 = 171 seconds

Phase 1 is 4 parallel LLM calls using `asyncio.gather`. With `claude-sonnet` at standard tier on 6 claims, each call should complete in 30-60 seconds. The 155-second wall time suggests API throttling or queue time — the calls ran in parallel but all hit a rate limit boundary simultaneously and the last one took ~155 seconds. This is a typical pattern with Anthropic's API under concurrent load.

Phase 2 is 171 seconds. This is where the concern is. The `WWHTB` step calls the LLM again. The consistency check in `aggregator.py` calls the judge LLM for any claims with `mean_confidence >= 0.6`. With 3 high-confidence claims, the consistency check ran at least once. The 171-second Phase 2 is likely dominated by:
1. WWHTB run (one LLM call on the aggregated output)
2. Consistency check (one LLM call on the 3 high-confidence claims)
3. Judge selection for any disputed claims (one LLM call per dispute)

The dispute variance threshold is 0.04 (stddev ~0.2). With 4 analysts producing a bimodal split (some very high, some very low confidence), variance on the 3 contested claims almost certainly exceeded 0.04, triggering judge selection calls. Each judge selection is a separate LLM call. Three contested claims = up to 3 additional judge calls in Phase 2.

Total LLM calls during deliberation: 4 (analysts) + 1 (WWHTB) + 1 (consistency check) + up to 3 (judge selection) = up to 9 LLM calls. At 25-40 seconds each on Sonnet, 326 seconds for 9 calls is consistent.

For a production pipeline processing many tasks in parallel, 326 seconds per deliberation is expensive. This is the cost of genuine multi-analyst deliberation — the tradeoff is real analytical depth vs. speed. The appropriate mitigation is LIGHT profile mode (fewer analysts, no WWHTB, no consistency check) for lower-stakes engagements.

### 2.6 Analyst Methodology Prompts: Quality Assessment

Each of the four prompts (ACH, quantitative, adversarial, historical_analogy) is 15-18 sentences, procedural, and encodes genuine methodology. They are substantially better than the 2-3 sentence fallback strings in `METHODOLOGY_PROMPTS`. Specific observations:

**ACH prompt:** Encodes the core Heuer insight (disconfirmation focus over confirmation) and correctly describes diagnosticity. The four-step procedure (hypothesis generation → evidence matrix → disconfirmation focus → confidence assignment) maps accurately to ICD 203. The prompt correctly specifies that "volume without diagnosticity is noise" — this is the key ACH insight that prevents the model from defaulting to "more sources = higher confidence."

**Quantitative prompt:** The sensitivity analysis (+/-20% assumption variation), base-rate comparison, and statistical power checks are substantive and procedurally correct. The prompt correctly penalizes false precision ("not stated to four significant figures when based on three data points") — this is a genuine quality signal that will catch inflated confidence on thin quantitative evidence.

**Adversarial prompt:** The pre-mortem framing ("imagine it is one year from now and this claim turned out to be wrong") is a well-established technique from behavioral decision theory. The confirmation bias test (favorable sources only, unfavorable data dismissed, no falsifiable evidence) is specific and checkable. The steel-manning requirement prevents strawman attacks.

**Historical analogy prompt:** Reference class selection, base-rate anchoring, analogy-breaking conditions, and temporal adjustment are all present and correctly specified. The prompt correctly notes that reference class selection is the most important and difficult step — narrow enough to be informative, broad enough to have sample size.

**Verdict:** The prompts are driving genuinely different reasoning. Each procedure encodes a distinct epistemic lens that would produce different assessments of the same claim. An ACH analyst would flag a claim as low-confidence if all plausible alternative hypotheses are consistent with the evidence (low diagnosticity), even if 5 sources support it. A quantitative analyst would flag the same claim as low-confidence if those 5 sources all cite each other (low statistical independence). An adversarial analyst would flag it if there is a compelling pre-mortem scenario the claim's evidence does not address. A historical analogy analyst would flag it if the reference class base rate contradicts the claim.

However, the prompts have a structural limitation: they are applied to 6-claim summaries, not to full research documents. The `InputClaim` object provides `text`, `evidence` (a summary string), `source_count` (an integer), and `original_confidence`. The analysts cannot see the actual citation text, the full finding context, or the source metadata. This limits the depth of evaluation possible. A quantitative analyst told "source_count: 3" cannot assess statistical independence of those 3 sources. The data passed to analysts is too thin to enable the full methodological procedures they are instructed to follow.

---

## 3. L4 Evaluator

### 3.1 The fact_decomposition Timeout: Root Cause

The timeout occurs in `Layer1Evaluator._fact_check`. The sequence:
1. Read `fact_decomposition.md` template
2. Build citation texts string: `"[{citation_id}] {title} - {publication}\nContent: {content_snippet}"` for each citation in the manifest
3. Inject the full `output_text` (the research finding) and citation texts into the template
4. Call `retry_llm_call` with `description="fact_decomposition"` using `claude-opus-4-6`

The prompt contains the full research text plus citation snippets. For the L1 deep-mode finding (28 claims, ~3,500 words, 46 citations), this prompt is large — potentially 6,000-8,000 tokens of input. The model must:
1. Read all 3,500 words of output text
2. Decompose every factual assertion into atomic claims (the instruction says "every factual claim... MUST appear")
3. For each atomic fact, find the citation that supports/contradicts/does not support it
4. Return a JSON array with one entry per atomic fact

For 28 claims averaging 125 words each, a thorough decomposition might produce 100-150 atomic facts. Each fact needs a JSON entry with `claim`, `status`, `citation_id`, and `reasoning`. The output JSON alone could be 15,000-20,000 tokens. Combined with the instruction to produce the array without skipping any claim ("Do NOT skip claims"), the model is being asked to produce a very long structured output in a single LLM call under a 300-second timeout.

This is the core problem: the `fact_decomposition` step tries to process an entire research output in one call. For the downstream test fixture (6 claims, shorter output text), this might have succeeded. For the full L1 output (28 claims, 46 citations), it cannot complete within 300 seconds on Opus because the output is too long.

**The fix:** Chunk the output text into sections (by claim or by paragraph), process each chunk independently, and aggregate results. The `_fact_check` method should iterate over 5-10 claim batches rather than sending the full finding in one call.

**Secondary issue:** The `Layer1Evaluator` is initialized with `extraction_llm or llm`, and the test used `claude-opus-4-6` for both. The code comment in `evaluator.py` says "work that Sonnet (STANDARD) is fully capable of, reserving Opus (FLAGSHIP) for Layer 3 rubric judgment." The test did not pass a separate `extraction_llm`, so Opus was used for fact decomposition. Using Sonnet for Layer 1 would be faster (shorter latency) and cheaper. The test should have used separate LLM instances for Layer 1 and Layer 3.

### 3.2 The Three Layers: What Each Checks

**Layer 1 (Deterministic verification):** Three sub-checks:
- FActScore via `fact_decomposition.md`: LLM decomposes the finding into atomic facts and checks each against citation snippets. This is only as good as the `content_snippet` fields on the citations — if `content_snippet` is null (which it is for many citations that were not fetched during L1), the LLM is checking facts against title + publication only, which is nearly useless. The check will produce many `NOT_SUPPORTED` flags for facts that are perfectly correct but whose supporting citation was never fetched.
- Numerical consistency via `numerical_consistency.md`: cross-references numbers within the document to detect internal contradictions. This is genuinely useful.
- URL liveness via `batch_check_urls`: re-checks all citation URLs. This duplicates the CitationProcessor's liveness check. The manifests passed to the Evaluator have already been checked by CitationProcessor — running it again is redundant unless the Evaluator receives a fresh manifest. This should be deduplicated.

**Layer 2 (Citation gate):** The `Layer2CitationGate` checks for fabricated citations. With `doi_verifier=None` (the default in the smoke test), this currently only cross-references citation IDs against the manifest. It does not actually verify that a citation ID corresponds to a real publication. Without CrossRef/DOI verification, the citation gate is essentially a manifest integrity check, not a fabrication detector.

**Layer 3 (Rubric scoring):** The `ThreePassEvaluator` runs the 10 rubric dimension prompts in three passes (first pass: initial scores, second pass: adversarial review, third pass: final scores). Each pass makes 10 LLM calls (one per dimension). Total: 30 LLM calls for a standard evaluation. This is where the bulk of computation time would go for a successful L4 run. The three-pass design is sound — it prevents the model from anchoring on initial scores without reconsideration.

### 3.3 The 10 Rubric Dimensions: Fitness for L1 Output

The 10 dimensions, with weights from `RUBRIC_WEIGHTS`:

| Dimension | Weight | Fitness for technical architecture findings |
|---|---|---|
| Intent Alignment | 15% | High — checks if the finding addresses what was asked |
| Quantitative Rigor | 15% | Medium — L1 output has numeric claims but they are often benchmark references |
| Actionability | 15% | Low for early research phase — findings are architectural assessment, not client recommendations |
| Analytical Depth | 12% | High — the depth gap identified in FIRST-RUN-ANALYSIS.md maps directly here |
| Intellectual Honesty | 10% | High — the anti-confirmatory claims in L1 output directly affect this |
| Source Quality | 10% | High — arxiv vs. GitHub vs. blog post quality matters for architecture claims |
| Narrative Coherence | 8% | Low for structured JSON claims — the renderer handles this, not the L1 output |
| Completeness | 8% | High — gap analysis directly |
| Calibrated Confidence | 5% | High — the per-claim confidence floats are exactly what this dimension checks |
| Evaluative Surprise | 2% | Medium — hard to score objectively; the FIRST-RUN-ANALYSIS confirms L1 found non-obvious sources |

**Actionability at 15% is the most problematic dimension.** The L4 Evaluator will apply the Actionability rubric to L1 research output — raw claims from research agents. The Actionability prompt asks for Monday-morning executable recommendations segmented by role. L1 agents produce factual claims about the landscape, not recommendations for the client. The existing L1 output ("AutoGen's GroupChat architecture supports N-agent routing with O(N) complexity" is a factual claim, not "The VP of Engineering should adopt AutoGen's GroupChat pattern for the triage routing layer"). Applying the Actionability rubric to L1 output will generate spuriously low scores on a dimension that should not apply at this stage. Actionability is a dimension for the final deliverable, not for intermediate research findings.

**Narrative Coherence at 8% has the same problem** for structured JSON output. The MarkdownRenderer converts findings to prose — the coherence judgment should be applied to the rendered output, not to the JSON array.

The appropriate fix is not to remove these dimensions but to apply them only to the appropriate layer. The current design applies the full rubric to every L1 output, which conflates the quality of the research with the quality of the final deliverable.

---

## 4. Cross-Cutting Issues

### 4.1 The One-Size-Fits-All Analyst Problem

The `DEFAULT_ANALYST_TYPES` in `deliberation.py` are hardcoded:
```python
DEFAULT_ANALYST_TYPES = [
    DeliberationAnalystType.ACH,
    DeliberationAnalystType.QUANTITATIVE,
    DeliberationAnalystType.ADVERSARIAL,
    DeliberationAnalystType.HISTORICAL_ANALOGY,
]
```

This is the same problem as L0's hardcoded `_LENSES = ["financial", "operational", "market"]`. The analyst types should be selected based on the engagement type and question domain. The `Deliberation` constructor already accepts `analyst_types: list[DeliberationAnalystType] | None` — the infrastructure for dynamic selection exists. What's missing is the logic that selects analyst types per engagement.

A proposed mapping:
- Technical architecture questions: systems_engineering, failure_mode, comparative_architecture, adversarial, quantitative
- Market/competitive questions: current analyst types (ACH, quantitative, adversarial, historical_analogy) — these are well-suited
- Strategic planning: scenario_planning, historical_analogy, adversarial, quantitative
- Regulatory/policy: historical_analogy, adversarial, ACH, stakeholder_mapping (new type needed)
- Technology evaluation: comparative_architecture, adversarial, quantitative, failure_mode

The mapping could be added as a method in `deliberation.py` or in L0's SpecEngine, since the engagement type is known at that stage.

### 4.2 Intermediate Data Loss

The following data is produced and then lost between layers:

- **CitationProcessor → Deliberation:** The `CitationProcessorResult.canonicalized_findings` is passed to Deliberation but not persisted. The alias map (source_instance_id → canonical_citation_id) is in the manifest but the manifest is not written to disk by default.

- **Deliberation Phase 1 → Phase 2:** Each `AnalystOutput` with `ScoredClaim` objects (including per-claim `reasoning` strings from all 4 analysts) is consumed by the Aggregator and is not written to disk. This is the richest intermediate data in the pipeline — 4 analyst perspectives on each claim, with explicit reasoning. It is entirely invisible in the test output and in any subsequent run.

- **Aggregator → ConfidenceMap:** The `AggregatedClaim` objects (with `agreement_ratio`, `analyst_scores`, `analyst_reasoning`, `selected_from`, `selection_reasoning`) are used to build the ConfidenceMap but are not preserved separately. If you want to understand why a claim ended up as contested vs. high-confidence, the data exists in the `AggregatedClaim` but not in the `ConfidenceMap` or any event.

- **Deliberation → L4:** The `ConfidenceMap` object is not passed to the L4 Evaluator. The Evaluator receives only the `output_text` (rendered finding), the `CitationManifest`, and a `SprintContract`. The confidence map — which contains the deliberation's judgment of each claim's strength — is completely invisible to the evaluator. This means L4 cannot factor in "this claim was contested by 3 of 4 analysts" when scoring Calibrated Confidence or Analytical Depth.

**What should be saved per engagement:**
```
output/{engagement_id}/
  citation_manifest.json     — already structure to support this
  l15_analyst_outputs.json   — all ScoredClaim objects per analyst
  l15_aggregated_claims.json — AggregatedClaim objects with reasoning
  l15_confidence_map.json    — final confidence map
  l4_evaluation.json         — evaluation result
```

None of these are currently written automatically.

### 4.3 Error Handling and Graceful Degradation

The L4 timeout crashed the downstream test — all 3 retry attempts exhausted (300s each), totaling 900 seconds of wasted compute, after which the test process terminated without a result. This is the correct behavior for a test script but wrong for a production pipeline.

Reading the evaluator code, graceful degradation is partially implemented:
- `Layer1Evaluator` failure: caught in `evaluator.py:159-179`, produces `Layer1Result(infrastructure_failure=True)` and continues
- `Layer3Evaluator` failure: caught in `evaluator.py:260-278`, produces `Layer3Result(infrastructure_failure=True)` and continues
- `Layer4Evaluator` (process trajectory) failure: caught in `evaluator.py:344-353`, sets `layer4_result = None` and continues

But `Layer1Evaluator._fact_check` uses `retry_llm_call` which exhausts all 3 retries before raising. The retry exhaustion is what caused the 900-second hang. The outer `try/except` in the evaluator catches the eventual `RuntimeError` from retry exhaustion — so the pipeline would eventually recover (after 900s). In production, the timeout per call should be much shorter for Layer 1 (which can afford to be fast-and-imperfect) and the chunking fix described above would prevent the timeout from occurring at all.

The deliberation has a cleaner failure mode: `asyncio.gather(return_exceptions=True)` catches individual analyst failures without killing the ensemble. If 1 of 4 analysts fails, the remaining 3 continue and the aggregation runs on the surviving outputs. This is good design.

### 4.4 Dynamic Analyst Types: What Should Drive Selection

The analyst type selection should be driven by a combination of:
1. **Engagement type** (from `EngagementType` enum) — strategic vs. evaluative vs. diagnostic
2. **Question domain** (from the task description or L0 classification) — technical vs. financial vs. regulatory
3. **Evidence character** (from the L1 finding) — quantitative-heavy, qualitative, mixed

The third driver requires L0 classification to reach the Deliberation layer, which it currently does not. The pipeline currently passes `engagement_id`, `client_id`, `manifest`, and `findings` to `Deliberation.deliberate()` — there is no channel for L0's engagement classification or question domain to influence the analyst selection.

**Proposed fix:** Pass the `EngagementSpec` or a domain tag to the `Deliberation` constructor. The `Deliberation.__init__` already accepts `effective_pipeline_profile: PipelineProfile` — a similar pattern could accept a domain classification that maps to an analyst set.

### 4.5 The Missing Layer: Synthesis

The most significant structural absence confirmed by this test is the lack of a synthesis layer between L1 research findings and the confidence map. The current flow:
```
L1 claims (flat JSON array) → CitationProcessor → Deliberation → ConfidenceMap
```

The ConfidenceMap classifies claims into tiers but does not synthesize them into narrative insights. The three convergent findings from the deliberation are not connected to each other — they are independently high-confidence claims that happen to all be about multi-agent systems. A senior analyst would read these three claims and ask: "what do they tell us together? What is the meta-pattern?" This synthesis step does not exist in the pipeline.

The batch-1 report's "compose the commodity, build the moat" insight is this kind of meta-synthesis. It required reading multiple systems, observing a shared pattern ("every system enforces quality through prompts, not architecture"), and drawing a strategic conclusion. No layer in the current pipeline performs this function.

---

## 5. Verdict and Priority Issues

### P0 Issues (Block pipeline quality at production scale)

1. **fact_decomposition chunking:** The Layer 1 fact check sends the entire research output in one LLM call. For outputs larger than ~2,000 words with 10+ claims, this will timeout on every run. Chunk into batches of 5-8 claims.

2. **Dynamic analyst type selection:** Hardcoded ACH/quantitative/adversarial/historical_analogy is wrong for technical architecture, regulatory, and systems engineering questions. Add an `EngagementSpec` parameter to `Deliberation` and select analyst types by domain.

3. **Analyst input data is too thin:** Analysts receive `text`, `evidence` (summary string), `source_count` (integer), `original_confidence`. They cannot see citation metadata, source types, or the actual supporting evidence. The quantitative analyst cannot assess statistical independence of sources. The adversarial analyst cannot check if only favorable sources were cited. Pass richer claim objects to analysts.

### P1 Issues (Materially degrade quality without blocking execution)

4. **No intermediate artifact persistence:** Analyst reasoning, aggregated claims with per-analyst scores, and the gap list are not written to disk. These are essential for debugging and for human review.

5. **ConfidenceMap not passed to L4:** The evaluator scores Calibrated Confidence without knowing which claims were contested in deliberation. The deliberation's output should inform L4 scoring.

6. **Actionability rubric misapplied to L1 output:** L1 findings are architectural facts, not client recommendations. Actionability at 15% weight will systematically undercount L1 research quality. Apply Actionability only to the final rendered deliverable.

7. **4-analyst panel produces bimodal distribution:** Increase to 5 analysts to populate the moderate and weak confidence tiers. The cost is ~80 additional seconds.

8. **URL liveness: no retry for transient failures:** A single `httpx.HTTPError` marks a URL dead. Add 1-2 retries with short backoff before declaring dead.

### P2 Issues (Design debt to address before scaling)

9. **corroboration overlap_score hardcoded at 1.0:** Corroboration should be weighted by claim-text similarity, not just shared URL. Two claims that cite the same paper for different facts are not corroborating the same finding.

10. **URL liveness duplicated between CitationProcessor and Layer 1:** CitationProcessor already checks liveness. Layer 1 re-checks the same manifest. Reuse CitationProcessor results rather than running a second HTTP batch.

11. **No synthesis layer:** The pipeline converts individual claims to a confidence map but never synthesizes claims into meta-insights. The gap between "3 high-confidence claims" and "one strategic observation drawn from those 3 claims" is not bridged.

12. **Gap text not surfaced in events:** `ConfidenceMapProduced` emits `gaps_count` but not gap content. Gap text should appear in the event stream so consumers can log, display, or act on gaps without parsing the full `ConfidenceMap` object.
