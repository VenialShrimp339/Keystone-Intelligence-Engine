# Prompt Engineering Reference Corpus

Research distillation for auditing the ~35 prompts in the Keystone Intelligence Engine pipeline. Every finding carries source, confidence level, and the prompt(s) it applies to.

Compiled from: PIPELINE-ATLAS.md, UNIFIED-SYNTHESIS.md, s4-evaluator deep research report, s3-memory deep research report, s2-prompt-versioning deep research report, GAP-AUDIT.md, CAPSTONE-PLAN-v2.md, and selected batch-2 Compass reports (wf-f6bc2f4e adaptive evaluation, wf-45485b06 specification design).

---

## Summary Table: Finding → Prompt Mapping

| # | Finding (abbreviated) | Prompt(s) affected | Section |
|---|---|---|---|
| S1 | Decision-First CoT improves intent from 25% to 84% | `intent_clarification.md` | §1 |
| S2 | Heterogeneous decomposition lenses yield 4-6% accuracy gain | `decompose_*_lens.md`, `decompose_synthesis.md` | §1 |
| S3 | MECE validation needs binary atomic criteria | `mece_validation.md` | §1 |
| S4 | Anti-confirmatory framing blocks must be structural | `task_generation.md`, all L1 prompts | §1 |
| S5 | Priority scoring lacks VOI cost denominator | `priority_scoring.md` | §1 |
| S6 | Issue tree co-generates evaluation criteria | `task_generation.md`, `sprint_contract_generation.md` | §1 |
| R1 | L1 inline prompts cannot be versioned or audited | `_build_synthesis_prompt`, `_build_deep_research_prompt`, absence report | §2 |
| R2 | Citation-ref enforcement prevents uncited claims structurally | All L1 synthesis prompts | §2 |
| R3 | Deep-mode prompt lacks gateway mediation safety | `_build_deep_research_prompt` | §2 |
| R4 | Evidence injection is untargeted (GAP-03) | All L1 synthesis prompts (EV-NNN block) | §2 |
| R5 | Confirmatory prompt prefixes produce cherry-picking | `task_generation.md` validator, L1 synthesis | §2 |
| R6 | Context has diminishing marginal returns | All L1 prompts, deep prompt | §2 |
| D1 | Debate is a mathematical martingale | All analyst methodology prompts, judge prompt | §3 |
| D2 | Methodological diversity > persona diversity | `METHODOLOGY_PROMPTS` (ACH, QUANT, ADV, HIST, SCENARIO) | §3 |
| D3 | Judge must select, not synthesize/blend | Judge prompt (aggregator.py:237) | §3 |
| D4 | WWHTB fires only below 0.6 — threshold unvalidated | WWHTB prompt (wwhtb.py) | §3 |
| D5 | Curmudgeon challenge structurally enforced | Judge/aggregator prompt | §3 |
| E1 | LLM judges weight style ~7x over factual errors | All 10 rubric dimension prompts | §4 |
| E2 | Single-judge ceiling is 60-68% in expert domains | All dimension prompts, ensemble design | §4 |
| E3 | Geometric mean prevents dimension compensation | Gestalt overlay, all dimension prompts | §4 |
| E4 | Tier 1 floor gates catch catastrophic failures early | `intent_alignment.md`, `intellectual_honesty.md`, `completeness.md`, `narrative_coherence.md` | §4 |
| E5 | "Always-true" anti-slop test in dimension prompts | `intent_alignment.md`, `actionability.md` | §4 |
| E6 | Process trajectory evaluates method, not output | `process_trajectory.md` | §4 |
| E7 | Sprint contracts bridge spec to testable criteria | `sprint_contract_generation.md` | §4 |
| E8 | Factual error detection requires decomposition | `fact_decomposition.md`, `numerical_consistency.md` | §4 |
| E9 | Authority markers must be stripped from eval prompts | All 10 rubric dimension prompts | §4 |
| C1 | Three evaluator thresholds are unvalidated (GAP-09) | All dimension prompts (calibration context) | §5 |
| C2 | No prompt carries model-version annotation (GAP-10) | All 35 prompts | §5 |
| C3 | Compensating complexity decays across model versions | All prompts with procedural scaffolding | §5 |
| C4 | Prompt caching requires stable context partitioning | L1 per-round prompts, L4 dimension prompts | §5 |
| C5 | Inline prompts defeat the versioned-.md pattern | L1 + L1.5 inline prompts (GAP-11) | §5 |
| C6 | Confidence band thresholds appear across 4+ prompts | WWHTB, confidence builder, analyst output format, L4 trajectory | §5 |

---

## 1. Specification Prompts (L0)

Nine `.md` files in `src/keystone/specification/prompts/`: `classification.md`, `intent_clarification.md`, `decompose_financial_lens.md`, `decompose_operational_lens.md`, `decompose_market_lens.md`, `decompose_synthesis.md`, `mece_validation.md`, `priority_scoring.md`, `task_generation.md`. All use `{{name}}`-templating. Tier/effort assignments per PIPELINE-ATLAS §3.

### S1. Decision-First Chain-of-Thought for intent clarification

**Claim:** LLMs score only 25% on pragmatic inference without structured prompting; the Decision-First CoT pattern (decision context → surprising finding → unstated constraints → change-of-mind evidence → scope boundary) is the single highest-leverage prompt structure in L0.

**Source:** CEI benchmark (March 2026) via CAPSTONE-PLAN-v2 §3.9; independently validated by batch-2 wf-45485b06 §2 citing the RSA framework (Frank & Goodman 2012, *Science*) and the TiCoder divergence-detection pattern (Lahiri et al. 2022, 40% → 84% correctness improvement).

**Confidence:** Verified. CEI is a published benchmark; TiCoder is peer-reviewed.

**Applies to:** `intent_clarification.md` (L0 Step 2, FLAGSHIP/xhigh). The current prompt already implements the 5-step CoT structure per PIPELINE-ATLAS §3. The audit should verify: (a) each step maps to a named output field on `IntentClarificationResult`, (b) the Day-1 Hypothesis output is a "declarative, falsifiable statement," (c) the "surprising finding" step is present and not a dead prompt section.

### S2. Heterogeneous decomposition lenses produce measurable gains

**Claim:** Three independent agents with distinct consulting lenses (financial, operational, market) producing parallel issue trees, followed by an Opus meta-agent synthesis, yields 4-6% accuracy gains and 30% fewer factual errors compared to single-agent homogeneous decomposition.

**Source:** Batch-2 reports 03 (wf-05889b6b) and 10 (wf-45485b06), both citing peer-reviewed 2025 evidence on heterogeneous planning. Independently, CAPSTONE-PLAN-v2 §3.4 Step 3.

**Confidence:** Corroborated. Two independent batch-2 reports converge; percentages from peer-reviewed sources.

**Applies to:** `decompose_financial_lens.md`, `decompose_operational_lens.md`, `decompose_market_lens.md` (all STANDARD/medium), and `decompose_synthesis.md` (FLAGSHIP/xhigh). Audit concern: the three lens prompts should encode genuinely different analytical frames, not just different section headers. The synthesis prompt should implement claim-level selection (pick best branches), not blending.

### S3. MECE validation needs five binary atomic criteria

**Claim:** Decomposition validation should check five dimensions with atomic binary criteria: mutual exclusivity (cosine similarity below 0.80), collective exhaustiveness, tailoring to the specific engagement, actionability (agents can research each branch), and depth appropriateness (2-3 levels). The AOP framework (ICLR 2025) found >15% of queries exhibit decomposition issues even with detailed instructions.

**Source:** AOP framework (ICLR 2025, arXiv:2410.02189) via batch-2 wf-45485b06 §3; CAPSTONE-PLAN-v2 §3.4 Step 4.

**Confidence:** Verified. ICLR 2025 peer-reviewed.

**Applies to:** `mece_validation.md` (FLAGSHIP/xhigh). Current implementation runs a retry loop (max 3 attempts); failing MECE ships without halt (GAP-06). Audit concern: does the prompt actually encode five discrete binary criteria, or does it ask for a holistic MECE judgment? The former is more auditable.

### S4. Anti-confirmatory framing is validated structurally

**Claim:** Agents given confirmatory prompts ("find evidence for X") cherry-pick with "the grinding indifference of water finding the fastest path downhill." Anti-confirmatory framing must be validated at the model level, not trusted as a prompt instruction.

**Source:** CAPSTONE-PLAN-v2 §4.1 citing Jones "Agent Schemes" (Mar 9, 2026); validated structurally at `tasks.py:165` which blocks prefixes "find evidence for," "prove that," "confirm that," "show that." GAP-AUDIT validated design choice #13.

**Confidence:** Verified. Structural enforcement confirmed in codebase.

**Applies to:** `task_generation.md` (must instruct the LLM to produce evaluative framing), all L1 synthesis prompts (must not reintroduce confirmatory framing in the per-round synthesis instructions), `_build_deep_research_prompt` (has an explicit ANTI-CONFIRMATORY FRAMING section per ATLAS §4).

### S5. Priority scoring lacks the cost denominator

**Claim:** The full VOI-inspired priority formula is `(decision_relevance × current_uncertainty) / estimated_cost`. Phase 1 uses only `decision_relevance × uncertainty_reduction` without the cost denominator, which means high-cost low-value tasks are not deprioritized.

**Source:** CAPSTONE-PLAN-v2 §3.4 Step 5; ISPOR VOI framework via batch-2 wf-45485b06 §5; PIPELINE-ATLAS §3 ("Priority scoring lacks `/estimated_cost` denominator").

**Confidence:** Verified. Documented as known stub.

**Applies to:** `priority_scoring.md` (FLAGSHIP/xhigh). The prompt audit should flag whether the prompt's scoring rubric mentions estimated cost as a factor, and if not, add a TODO for Phase 2.

### S6. Issue tree should co-generate evaluation criteria

**Claim:** The most effective production systems generate evaluation criteria simultaneously with the research plan, not after. Anthropic's sprint contract pattern and VeriMAP (arXiv:2510.17109) both show evaluation criteria co-generation improves alignment.

**Source:** Batch-2 wf-45485b06 §3 (VeriMAP framework); batch-2 wf-f6bc2f4e (sprint contract pattern from Anthropic's Rajasekaran blog post).

**Confidence:** Corroborated. Two independent sources converge.

**Applies to:** `task_generation.md` (already produces `acceptance_criteria` and `anti_confirmatory_framing` per task), `sprint_contract_generation.md` (consumes those criteria). The audit should verify the task-generation prompt instructs the LLM to write testable acceptance criteria that the evaluator can grade against, not vague quality aspirations.

---

## 2. Research Prompts (L1)

**No `.md` files exist.** All L1 prompts are inline Python f-strings in `research_agent.py`: `_build_synthesis_prompt` (L891), `_build_deep_research_prompt` (L774), absence report prompt (L1014). L1.5 analyst prompts are similarly inline in `deliberation/analyst.py`. This is GAP-11.

### R1. Inline prompts defeat versioning, auditing, and annotation

**Claim:** L1's load-bearing synthesis prompts are the only major prompts in the pipeline not externalized to `.md` files, making them impossible to version independently, annotate with model-version metadata (GAP-10), or audit in a diff review.

**Source:** GAP-AUDIT GAP-11 (confirmed); PIPELINE-ATLAS §4 ("Prompts: no .md files"); batch-2 wf-45485b06 §1 citing Anthropic: "prompt engineering of the decomposition step was their primary lever for improving behaviors."

**Confidence:** Verified. Codebase confirmed.

**Applies to:** `_build_synthesis_prompt`, `_build_deep_research_prompt`, absence report prompt, all five `METHODOLOGY_PROMPTS` in `analyst.py`, judge prompt in `aggregator.py`, WWHTB prompt in `wwhtb.py`. Recommended action: externalize to `src/keystone/research/prompts/synthesis.md`, `deep_research.md`, `absence_report.md` with `{{template}}` variables.

### R2. Citation-ref enforcement is a structural success

**Claim:** The synthesis prompt requires every claim to include `citation_refs: ["SRC-NNN", "EV-NNN"]`. Claims without citation_refs are dropped (research_agent.py:973). This is the correct architectural pattern: make uncited claims structurally impossible, don't rely on prompt instructions alone.

**Source:** PIPELINE-ATLAS §4; UNIFIED-SYNTHESIS §1.5 (five-layer citation enforcement); CAPSTONE-PLAN-v2 §4.1 point 4 ("the @jordymaui principle — don't tell the agent to cite sources, make it impossible not to").

**Confidence:** Verified. Multiple sources converge.

**Applies to:** All L1 synthesis prompts. Audit concern: verify the deep-mode prompt enforces the same structural requirement. Per ATLAS §4, deep mode uses `claim.sources = [{url, title, content_snippet}]` directly, not the SRC-NNN indirection — confirm this is equivalent in enforcement strength.

### R3. Deep-mode prompt operates outside the safety envelope

**Claim:** The deep-research prompt (`_build_deep_research_prompt`) produces output via `claude -p --allowedTools WebSearch,WebFetch`, bypassing ToolAuthorizer, rate limiter, circuit breaker, and per-call audit logging. Prompt injection on fetched content is unmitigated.

**Source:** GAP-AUDIT GAP-08 (confirmed); PIPELINE-ATLAS §4 ("Tools NOT gated by MCPGateway"); s4-evaluator deep research report (structural safety > intent-based safety, with specific prompt-injection risk framing).

**Confidence:** Verified. Codebase confirmed.

**Applies to:** `_build_deep_research_prompt`. Audit recommendation: add prompt-injection sanitization to `_evidence_block` before injection; add WARN governance flag when deep mode activates; cap deep-mode tasks per engagement.

### R4. Evidence injection is a firehose, not a filter

**Claim:** `_prepare_evidence_context` injects up to 20 passages per task with no task-relevance filter. All tasks in an engagement see the same corpus dump, capped only by count. This matches the "memory rots" pattern: unstructured context accumulation degrades performance below clean-start baseline.

**Source:** GAP-AUDIT GAP-03 (confirmed); Nate Jones corpus B1 cross-pattern #3 citing 2026-04-04 Cowork/Lindy analysis; CAPSTONE-PLAN-v2 §4.1 point 2 (JIT context loading, diminishing marginal returns).

**Confidence:** Verified. Codebase confirmed.

**Applies to:** All L1 synthesis prompts (the `EV-NNN` evidence block). The prompt itself isn't the problem — the evidence selection feeding into it is. However, the prompt should instruct the agent to evaluate evidence relevance rather than treating all provided evidence as equally pertinent.

### R5. Confirmatory framing undermines the entire research path

**Claim:** Research agents with confirmatory prompts produce cherry-picked findings. The `tasks.py:165` validator blocks confirmatory prefixes structurally, but the L1 synthesis prompt must not reintroduce confirmatory framing (e.g., "find supporting evidence for...") in its per-round instructions.

**Source:** CAPSTONE-PLAN-v2 §4.1; Jones "Agent Schemes" (Mar 9, 2026); UNIFIED-SYNTHESIS §1.2. GAP-AUDIT validated design choice #13.

**Confidence:** Verified.

**Applies to:** `_build_synthesis_prompt` (check per-round instruction language), `_build_deep_research_prompt` (has explicit ANTI-CONFIRMATORY FRAMING section — verify it's not vestigial).

### R6. Context engineering: less is more

**Claim:** Loading an entire 10-K filing into context is worse than loading the three relevant sections, because irrelevant content dilutes attention across thousands of tokens the model doesn't need. Token usage explains 80% of performance variance.

**Source:** CAPSTONE-PLAN-v2 §4.1 point 2 citing Anthropic "Context Engineering" (Rajasekaran, Dixon, Ryan & Hadfield); §4.2 citing Anthropic multi-agent system findings.

**Confidence:** Verified. Anthropic engineering primary source.

**Applies to:** All L1 prompts (the evidence block and source table together can consume significant context), `_build_deep_research_prompt` (single-turn, no per-round context management). Deep mode is highest risk because it accumulates internally.

---

## 3. Deliberation Prompts (L1.5)

All inline in Python: five `METHODOLOGY_PROMPTS` entries in `analyst.py:61-87`, judge prompt in `aggregator.py:237`, consistency check prompt, WWHTB prompt in `wwhtb.py`. No `.md` files. GAP-11 applies.

### D1. Iterative debate is a mathematical martingale

**Claim:** Multi-agent debate forms a martingale — additional debate rounds consistently degrade accuracy rather than improve it. Majority voting alone (0.7691) outperformed the best debate variant (0.7377). More rounds = worse performance. The mathematical proof holds regardless of model quality.

**Source:** UNIFIED-SYNTHESIS §1.3 citing NeurIPS 2025 Spotlight ("Debate or Vote," formal proof + empirical); CAPSTONE-PLAN-v2 §4.3; confirmed by Wu et al. (majority pressure suppresses independent correction below 5%) and Google DeepMind (17.2x error amplification in unstructured multi-agent networks).

**Confidence:** Verified. NeurIPS 2025 Spotlight with formal proof.

**Applies to:** The deliberation architecture itself — no inter-analyst communication in Phase 1 is the correct implementation. The audit should verify: (a) no prompt instructs analysts to consider other analysts' work, (b) the aggregator receives all analyses simultaneously rather than sequentially, (c) no iterative debate rounds exist in the code path.

### D2. Methodological diversity outperforms persona diversity

**Claim:** Agents using different analytical methods (ACH, quantitative modeling, adversarial critique, historical analogy) on the same evidence produce genuinely independent assessments. Agents with different "personalities" using the same method produce correlated noise. DMAD (ICLR 2025) is the key reference.

**Source:** UNIFIED-SYNTHESIS §1.3 citing DMAD (ICLR 2025); CAPSTONE-PLAN-v2 §4.3; batch-2 wf-45485b06 §7 (multi-agent deliberation findings).

**Confidence:** Verified. ICLR 2025 peer-reviewed.

**Applies to:** The five `METHODOLOGY_PROMPTS` in `analyst.py`. Each prompt should encode a genuine analytical methodology with distinct reasoning steps, not just a different tone or persona. Current prompts per ATLAS §6:
- **ACH**: "identify competing hypotheses and rate evidence diagnosticity" — this is a real methodology
- **ADVERSARIAL**: "find weaknesses, identify strongest counter-argument, test for confirmation bias" — methodology-based
- **HISTORICAL_ANALOGY**: "identify relevant historical precedents, assess base rates and reference class forecasting" — methodology-based
- **QUANTITATIVE**: verify this encodes distinct quantitative reasoning (sensitivity analysis, base-rate comparison), not generic "be quantitative"
- **SCENARIO_PLANNING**: optional; verify distinct methodology

Audit concern: the prompts are brief (2-3 sentences). Are they specific enough to drive genuinely different analytical frames?

### D3. Judge must select, not synthesize or blend

**Claim:** Claim-level selection achieves an 81% win rate; synthesis-based blending scores 51.2% (near chance). Synthesis "introduces incoherence, conflicting perspectives, and diluted arguments."

**Source:** CAPSTONE-PLAN-v2 §4.3 Phase 2, citing batch-2 report 06; current judge prompt in `aggregator.py:237` already implements this — "Select the analyst whose assessment is best supported by the evidence. Do NOT blend or average. Pick one."

**Confidence:** Verified. Current implementation matches the finding.

**Applies to:** Judge prompt (`aggregator.py:237`). The existing prompt is correctly designed. Audit concern: verify the fallback on parse failure (`max(scores, key=scores.get)`) doesn't effectively blend by defaulting to the highest raw score rather than the most evidence-supported assessment.

### D4. WWHTB threshold is unvalidated

**Claim:** The WWHTB ("What Would Have To Be True") prompt fires only when `mean_confidence < 0.6`. This threshold is a `PipelineConfig` field (`wwhtb_confidence_threshold`) but has never been calibrated against human-scored outputs. The prompt itself asks: "For the following uncertain claim, identify the key assumptions that would have to be true for it to hold. List 2-5 specific, testable assumptions."

**Source:** PIPELINE-ATLAS §6; GAP-AUDIT GAP-09 (three unvalidated thresholds); CAPSTONE-PLAN-v2 §4.4 ("WWHTB step").

**Confidence:** Verified.

**Applies to:** WWHTB prompt (`wwhtb.py`). Audit concern: the threshold value is more important than the prompt wording. If calibration shows that claims at 0.5-0.7 benefit from WWHTB analysis but claims at 0.4-0.5 don't (because they're too uncertain to productively decompose), the threshold should shift.

### D5. Curmudgeon challenge is architecturally correct

**Claim:** For every high-confidence finding, the aggregator must articulate a specific, non-trivial reason it could be wrong and assess whether any analyst addressed that risk. This is the CIR3 Curmudgeon Agent pattern (UNIFIED-SYNTHESIS L1.5 tool table) — structurally enforced devil's advocacy with diversity score.

**Source:** UNIFIED-SYNTHESIS §2 (CIR3 BUILD verdict); CAPSTONE-PLAN-v2 §4.3 Phase 2.

**Confidence:** Corroborated.

**Applies to:** Judge/aggregator prompt. Verify the consistency check (`aggregator.py` — for top-10 claims with `mean_confidence >= 0.6`) effectively implements this, and that the curmudgeon challenge is not just a field on the output model but an active prompt instruction.

---

## 4. Evaluation Prompts (L4)

Fifteen `.md` files in `src/keystone/evaluator/prompts/`. Ten rubric dimensions, plus `fact_decomposition.md`, `numerical_consistency.md`, `gestalt_overlay.md`, `process_trajectory.md`, `sprint_contract_generation.md`.

### E1. LLM judges weight style ~7x more than factual errors

**Claim:** SOS-Bench (ICLR 2025, 152K data points) showed style correlates with overall judge score at Pearson r = 0.999, while injecting factual errors drops scores by only 13% vs. 96% for sarcastic tone. This held across all four judge models tested (GPT-3.5, GPT-4o-mini, GPT-4o, Claude 3.5 Sonnet).

**Source:** s4-evaluator deep research report (primary analysis); UNIFIED-SYNTHESIS §1.1, §1.4; batch-2 wf-f6bc2f4e §3 ("LLM judges are systematically unreliable where consulting quality matters most").

**Confidence:** Verified. ICLR 2025 published benchmark.

**Applies to:** All 10 rubric dimension prompts. Design consequence: weights are deliberately calibrated away from where LLMs naturally perform well (coherent prose, comprehensive coverage) and toward where they underperform (analytical novelty, quantitative rigor, actionable insight). Audit should verify each dimension prompt anchors scoring to substance-specific criteria rather than general quality language that judges will conflate with style.

### E2. Single-judge ceiling is 60-68% in expert domains

**Claim:** A single LLM judge reaches only 60-68% agreement with human experts in domain-specific evaluation. For Olympiad-level math, LLM graders overestimated solution quality by up to 20x. The PoLL pattern (2-3 models from different families) outperforms a single expensive judge while being 7-8x cheaper.

**Source:** UNIFIED-SYNTHESIS §1.4 citing D2 (60-68% single-judge ceiling); s4-evaluator report citing JudgeBench (Tan et al., ICLR 2025, GPT-4o "just slightly better than random guessing" on objectively-correct technical judgments); batch-2 wf-f6bc2f4e (reliability hierarchy by task type).

**Confidence:** Verified. Multiple peer-reviewed sources.

**Applies to:** All dimension prompts via the L5 ensemble design. The current L5 panel: STANDARD = 2×Opus (sampling stochasticity), DEEP = 2×Opus + 1×Sonnet. The `standard_crossmodel` slot is an interim placeholder for an external provider (GAP-14). The prompt audit should note: until cross-provider diversity is achieved, the ensemble mitigates stochastic noise but not systematic Claude-family biases.

### E3. Geometric mean aggregation prevents dimension compensation

**Claim:** Weighted arithmetic mean allows dimension compensation (high Narrative Coherence masking low Intellectual Honesty). Weighted geometric mean prevents this — a near-zero score on any dimension drives the composite toward zero. Three independent frameworks (Stanford HELM, MQM, AdaRubric) independently adopted geometric mean for this reason.

**Source:** CAPSTONE-PLAN-v2 §5.3; batch-2 wf-f6bc2f4e (explicit geometric mean recommendation with framework citations); PIPELINE-ATLAS §8 (current implementation confirmed: `exp(Σ w_i·log(x_i))` with floor at 0.01).

**Confidence:** Verified. Implemented in codebase.

**Applies to:** The scoring pipeline in `layer3_rubric.py`, and indirectly to the `gestalt_overlay.md` prompt (which produces a ±10 adjustment). Audit concern: the gestalt overlay applies an additive adjustment to a geometric-mean composite. Verify the clamping (`max(0, min(100, geo_mean + gestalt_adj))`) doesn't create an escape hatch that undoes the geometric mean's anti-compensation property.

### E4. Tier 1 floor gates are the most critical prompt design decision

**Claim:** Four dimensions function as universal gates with floor thresholds: Intent Alignment (floor 40), Intellectual Honesty (floor 40), Completeness (floor 30), Narrative Coherence (floor 40). Any Tier 1 score below its floor → immediate rejection; Tier 2 never runs.

**Source:** PIPELINE-ATLAS §8; CAPSTONE-PLAN-v2 §5.3; batch-2 wf-f6bc2f4e §4. Design rationale per CAPSTONE: "Intent Alignment and Intellectual Honesty define the minimum standard of intellectual trustworthiness."

**Confidence:** Verified. Implemented in codebase.

**Applies to:** `intent_alignment.md`, `intellectual_honesty.md`, `completeness.md`, `narrative_coherence.md`. These four prompts are the highest-stakes in the entire evaluation stack — a single miscalibrated Tier 1 prompt either blocks good output or passes bad output. Audit priority: verify floor thresholds in the prompts match the scoring bands (0-20, 21-40, 41-60, 61-80, 81-100) and that a score of 39 on Intent Alignment is unambiguously below the floor.

### E5. The "always-true" anti-slop test

**Claim:** The `intent_alignment.md` prompt includes an anti-slop sub-check: "If equally valid for the client's three closest competitors, it fails." The `actionability.md` prompt should include trendslop detection: generic strategic recommendations that could apply to any company in any industry (HBR March 2026, 15K+ trials).

**Source:** PIPELINE-ATLAS §8 (intent_alignment anatomy); CAPSTONE-PLAN-v2 §5.8 (anti-slop standard); UNIFIED-SYNTHESIS §6 (Actionability: "Monday-morning specificity; trendslop detection").

**Confidence:** Verified (intent_alignment). Corroborated (actionability trendslop — CAPSTONE design, verify in prompt).

**Applies to:** `intent_alignment.md` (existing anti-slop test), `actionability.md` (verify trendslop detection is present). Broader audit: which other dimension prompts would benefit from an "always-true" test? Source Quality ("would this source list be identical for any similar question?") is a candidate.

### E6. Process trajectory evaluates the method, not the output

**Claim:** Layer 4 (process trajectory) evaluates the research process — source diversity, tool utilization, round progression, branch coverage — not the output text. Agent-as-a-Judge achieves ~90% human agreement vs. ~70% for static LLM-as-Judge. 50-67% of AI PRs that pass automated tests are rejected by human maintainers, suggesting process quality predicts output quality failures invisible in the final deliverable.

**Source:** CAPSTONE-PLAN-v2 §5.9 Layer 4 citing arXiv:2410.10934; PIPELINE-ATLAS §8 (L4 sub-layer); UNIFIED-SYNTHESIS §1.1 (Agent-as-a-Judge BUILD verdict).

**Confidence:** Verified.

**Applies to:** `process_trajectory.md`. Audit concern: does the prompt include the deterministic metrics (source_count, unique_domains, source_type_diversity, tool_utilization, round_count, branches_covered/missed, citation_quality) as context, or does it ask the LLM to infer them? Per ATLAS §8, deterministic metrics are computed first and injected — the LLM provides the qualitative assessment and `missed_inquiries` judgment.

### E7. Sprint contracts bridge specification to testable criteria

**Claim:** Sprint contract pattern (Anthropic's Rajasekaran, Mar 2026): Generator and Evaluator negotiate what "done" looks like before work begins. Sprint 3 alone had 27 testable criteria. Per-dimension weight multipliers 0.7-1.5 allow engagement-type customization.

**Source:** Batch-2 wf-f6bc2f4e (primary analysis of sprint contract pattern); PIPELINE-ATLAS §7 (SprintContractGenerator); CAPSTONE-PLAN-v2 §4.4, §5.13.

**Confidence:** Verified. Current implementation confirmed.

**Applies to:** `sprint_contract_generation.md`. The prompt receives: `task_id`, `task_category`, `task_description`, `end_product`, `task_acceptance_criteria`, `anti_confirmatory_framing`, `engagement_type`, `decision_context`, `quality_bar`. It outputs: `acceptance_criteria`, `dimension_emphasis` (per-rubric-dimension weight multiplier), `mandatory_elements`, `anti_patterns`. Audit concern: Phase 1 is unidirectional (evaluator proposes unilaterally). Phase 2 adds bidirectional negotiation. The prompt should be structured to make negotiation possible without rewrite.

### E8. Factual error detection requires atomic decomposition

**Claim:** FActScore atomic fact decomposition achieves <2% error vs. human verification. Numerical consistency checks catch precision and internal-contradiction errors that rubric scoring misses. Together these form the "ungameable foundation" of the evaluation stack.

**Source:** UNIFIED-SYNTHESIS §1.1 Layer 1 (FActScore BUILD verdict); PIPELINE-ATLAS §8 (L1 sub-layer).

**Confidence:** Verified.

**Applies to:** `fact_decomposition.md` (receives `{{output_text}}` + `{{citation_texts}}`), `numerical_consistency.md`. Audit concern: the `infrastructure_failure` flag (ATLAS §8) means if these prompts fail to parse, the failure is silently flagged rather than halting — consumers must check the flag. Verify the prompts produce cleanly parseable JSON.

### E9. Authority markers must be stripped from evaluation prompts

**Claim:** CALM (ICLR 2025) found fake citations reversed ChatGPT's judgment 33.8% of the time (authority bias). Presentation order randomization is needed to prevent position bias (43.4% inconsistency). Authority markers — author names, institution affiliations, cited expert names — should be stripped from text before evaluation.

**Source:** CAPSTONE-PLAN-v2 §5.11 citing CALM (ICLR 2025); UNIFIED-SYNTHESIS §1.4; batch-2 wf-f6bc2f4e §3.

**Confidence:** Verified. ICLR 2025.

**Applies to:** All 10 rubric dimension prompts. Audit question: does the pipeline strip authority markers from `{{output_text}}` before injection into dimension prompts? If not, a section citing "Goldman Sachs research" or "McKinsey analysis" may receive inflated scores purely from authority bias. This is a pipeline concern, not a prompt-wording concern — but the prompts should not instruct judges to weight source prestige.

---

## 5. Cross-Cutting Findings

### C1. Three evaluator thresholds are unvalidated

**Claim:** `evaluator_pass_threshold = 60.0`, `evaluator_layer3_weight = 0.8`, `l5_low_agreement_threshold = 0.30` — all three were designed to be calibrated against human-scored samples and never have been. Every pass/fail decision rests on assumed parameters.

**Source:** GAP-AUDIT GAP-09 (confirmed); CAPSTONE-PLAN-v2 §5.4 (0.80+ Spearman target, 100-200 expert-scored samples).

**Confidence:** Verified. No calibration study exists.

**Applies to:** All dimension prompts (indirectly — calibration determines whether prompt improvements produce real quality signal or just noise). The 60.0 pass threshold, the 0.8 L3/L4 blend weight, and the 0.30 agreement floor should be treated as hypotheses, not constants.

### C2. No prompt carries model-version annotation

**Claim:** No prompt file in `src/keystone/specification/prompts/` or `src/keystone/evaluator/prompts/` contains model-version frontmatter or annotation. Inline prompts in L1/L1.5 have no equivalent mechanism.

**Source:** GAP-AUDIT GAP-10 (confirmed — spot-checked `classification.md` and `intent_alignment.md`); s2-prompt-versioning deep research report (neither OpenClaw nor Claude Code has a "tuned-for-model" annotation standard; both rely on git + release-note migration guides).

**Confidence:** Verified.

**Applies to:** All ~35 prompts. The audit should add frontmatter like `<!-- tuned-for: claude-opus-4-6, date: 2026-03-XX -->` to every `.md` prompt. For inline prompts, add an equivalent Python comment. Then add a canary test (`tests/canary/test_prompt_freshness.py`) that fails if any prompt's annotation is >2 model versions behind `AppConfig.flagship_model`.

### C3. Compensating complexity decays across model versions

**Claim:** "Every piece of 'how' you encode into your system is a bet against the model getting smarter." Procedural scaffolding (MECE retry loop at 3 attempts, explicit per-round citation-formatting instructions, anti-hallucination prefixes) becomes drag when the model improves. Three-month model generation cycles make any scaffolding stale within a quarter.

**Source:** GAP-AUDIT GAP-10 citing Nate Jones B4 (2026-02-11 "January obsolete," 2026-04-01 "every workaround you built for the last model is now breaking the next one"); s2-prompt-versioning report (Anthropic removed sprint decomposition when upgrading from Sonnet 4.5 to Opus 4.6); batch-2 wf-f6bc2f4e ("every component in a harness encodes an assumption about what the model cannot do on its own; those assumptions decay as models improve").

**Confidence:** Verified. Multiple independent sources.

**Applies to:** All prompts with procedural scaffolding. The audit should flag every procedural instruction and mark it as either: (a) structural invariant (citation enforcement, anti-confirmatory framing — these survive model upgrades), or (b) compensating complexity (step-by-step reasoning scaffolds, explicit output-format enforcement — these may become unnecessary). Per Boris Cherny: "Don't design your workflows around the limitations of today's model."

### C4. Prompt caching requires stable context partitioning

**Claim:** Anthropic prompt caching provides 90% cost discount on repeated content. Keystone uses it nowhere (GAP-16). L4 rubric scoring makes 10 parallel calls with nearly-identical context (dimension name varies); L5 multiplies by 2-3 judges. The L1 shallow-mode synthesis resubmits the same system prompt 3-5 times per task across rounds.

**Source:** GAP-AUDIT GAP-16 (confirmed); s2-prompt-versioning report (OpenClaw splits at `OPENCLAW_CACHE_BOUNDARY` — stable prefix vs. volatile suffix; Claude Code uses `__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__` for the same purpose); Nate Jones B5 (2026-04-02, explicit 90% discount claim).

**Confidence:** Verified. Blocked on HTTP SDK transport (GAP-14).

**Applies to:** All L4 dimension prompts (highest-value cache target — 10 prompts × 2-3 judges = 20-30 calls with mostly-identical context), L1 per-round synthesis prompts. The audit should identify which prompt content is stable across calls (rubric definition, scoring bands, sub-criteria) vs. volatile (the `{{output_text}}`, `{{sprint_contract_criteria}}`). The stable portion is the cache-prefix candidate.

### C5. The inline/file inconsistency creates a two-tier audit surface

**Claim:** L0 and L4 prompts live in `.md` files (auditable, diffable, annotatable). L1 and L1.5 prompts are inline Python f-strings (buried in logic, mixed with variable interpolation, harder to review). This creates a two-tier audit surface where the most load-bearing research prompts are the least accessible.

**Source:** GAP-AUDIT GAP-11 (confirmed); PIPELINE-ATLAS §4 ("no .md files"), §6 ("inline only").

**Confidence:** Verified.

**Applies to:** All L1 and L1.5 inline prompts. The synthesis prompt (90 lines of inline f-string at `research_agent.py:774-864`) is the single longest prompt in the pipeline and the hardest to review.

### C6. Confidence band thresholds appear across multiple prompts

**Claim:** The confidence tiering system (>80% high, 60-80% moderate, 50-60% weak, <50% contested, insufficient evidence) appears in: the WWHTB trigger (0.6), the confidence builder tiers, the analyst output format instruction, the L4 trajectory prompt's confidence assessment, and the section text renderer's hedging language. A change to these bands requires coordinated updates across at least 4 components.

**Source:** PIPELINE-ATLAS §6 (ConfidenceMap tiering), §7 (section text — hedging varies by tier); CAPSTONE-PLAN-v2 §4.3 (five-tier confidence taxonomy).

**Confidence:** Verified. Current implementation confirmed.

**Applies to:** WWHTB prompt, analyst output-format instruction, `process_trajectory.md` (if it references confidence bands), and the section-text renderer's lede framing. The audit should inventory every location where these thresholds appear and verify they're sourced from `PipelineConfig` rather than hardcoded in prompt text.

---

## Appendix: Complete Prompt Inventory

| # | Prompt | Location | Format | Tier/Effort | Layer |
|---|---|---|---|---|---|
| 1 | Engagement classification | `specification/prompts/classification.md` | .md | STANDARD/medium | L0 |
| 2 | Intent clarification | `specification/prompts/intent_clarification.md` | .md | FLAGSHIP/xhigh | L0 |
| 3 | Financial lens decomposition | `specification/prompts/decompose_financial_lens.md` | .md | STANDARD/medium | L0 |
| 4 | Operational lens decomposition | `specification/prompts/decompose_operational_lens.md` | .md | STANDARD/medium | L0 |
| 5 | Market lens decomposition | `specification/prompts/decompose_market_lens.md` | .md | STANDARD/medium | L0 |
| 6 | Decomposition synthesis | `specification/prompts/decompose_synthesis.md` | .md | FLAGSHIP/xhigh | L0 |
| 7 | MECE validation | `specification/prompts/mece_validation.md` | .md | FLAGSHIP/xhigh | L0 |
| 8 | Priority scoring | `specification/prompts/priority_scoring.md` | .md | FLAGSHIP/xhigh | L0 |
| 9 | Task generation | `specification/prompts/task_generation.md` | .md | STANDARD/medium | L0 |
| 10 | Shallow synthesis | `research/research_agent.py:891` | inline Python | STANDARD/medium | L1 |
| 11 | Deep research | `research/research_agent.py:774` | inline Python | STANDARD/medium | L1 |
| 12 | Absence report | `research/research_agent.py:1014` | inline Python | STANDARD/medium | L1 |
| 13 | ACH analyst | `deliberation/analyst.py:62` | inline Python | STANDARD | L1.5 |
| 14 | Quantitative analyst | `deliberation/analyst.py` | inline Python | STANDARD | L1.5 |
| 15 | Adversarial analyst | `deliberation/analyst.py` | inline Python | STANDARD | L1.5 |
| 16 | Historical analogy analyst | `deliberation/analyst.py` | inline Python | STANDARD | L1.5 |
| 17 | Scenario planning analyst | `deliberation/analyst.py` | inline Python | STANDARD | L1.5 |
| 18 | Aggregator judge | `deliberation/aggregator.py:237` | inline Python | FLAGSHIP | L1.5 |
| 19 | Consistency check | `deliberation/aggregator.py` | inline Python | FLAGSHIP | L1.5 |
| 20 | WWHTB | `deliberation/wwhtb.py` | inline Python | STANDARD | L1.5 |
| 21 | Sprint contract generation | `evaluator/prompts/sprint_contract_generation.md` | .md | FLAGSHIP/high | L2 |
| 22 | Fact decomposition | `evaluator/prompts/fact_decomposition.md` | .md | STANDARD/medium | L4-L1 |
| 23 | Numerical consistency | `evaluator/prompts/numerical_consistency.md` | .md | STANDARD/medium | L4-L1 |
| 24 | Intent alignment | `evaluator/prompts/intent_alignment.md` | .md | FLAGSHIP/high | L4-L3 |
| 25 | Intellectual honesty | `evaluator/prompts/intellectual_honesty.md` | .md | FLAGSHIP/high | L4-L3 |
| 26 | Completeness | `evaluator/prompts/completeness.md` | .md | FLAGSHIP/high | L4-L3 |
| 27 | Narrative coherence | `evaluator/prompts/narrative_coherence.md` | .md | FLAGSHIP/high | L4-L3 |
| 28 | Analytical depth | `evaluator/prompts/analytical_depth.md` | .md | FLAGSHIP/high | L4-L3 |
| 29 | Source quality | `evaluator/prompts/source_quality.md` | .md | FLAGSHIP/high | L4-L3 |
| 30 | Quantitative rigor | `evaluator/prompts/quantitative_rigor.md` | .md | FLAGSHIP/high | L4-L3 |
| 31 | Actionability | `evaluator/prompts/actionability.md` | .md | FLAGSHIP/high | L4-L3 |
| 32 | Evaluative surprise | `evaluator/prompts/evaluative_surprise.md` | .md | FLAGSHIP/high | L4-L3 |
| 33 | Calibrated confidence | `evaluator/prompts/calibrated_confidence.md` | .md | FLAGSHIP/high | L4-L3 |
| 34 | Gestalt overlay | `evaluator/prompts/gestalt_overlay.md` | .md | FLAGSHIP/high | L4-L3 |
| 35 | Process trajectory | `evaluator/prompts/process_trajectory.md` | .md | FLAGSHIP/high | L4-L4 |

L5 ensemble reuses the same rubric prompts (#24-33) with different judges; no additional prompt files.

---

*This document is a reference for the prompt audit session. It does not modify any prompts or propose implementations.*
