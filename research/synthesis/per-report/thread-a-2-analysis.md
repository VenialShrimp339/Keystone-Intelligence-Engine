# Report 2: A2 — Evaluation & Verification Frameworks

---

## Top Findings

**Finding 1: SOS-Bench proves holistic LLM judging is fundamentally broken — decomposed evaluation is non-negotiable**
SOS-Bench (152,380 data points, 19 benchmarks, ICLR 2025) found that sarcastic tone causes 96% scoring loss while factual errors cause only 13% scoring loss. LLM-judge preferences show essentially zero correlation with concrete measures of safety, world knowledge, or instruction following. This is not a marginal effect — it is a category failure that invalidates any evaluation approach that scores output holistically (all dimensions at once). The eight-dimension rubric in CAPSTONE-PLAN-v2.md is not just a nice-to-have; it is the architecturally correct design given this evidence.
- Pipeline layer: L4 (Evaluator)
- Build implication: Score each of the eight dimensions with a separate prompt — never all at once. Any single-prompt scoring approach will conflate style with substance and produce unreliable quality gates.
- Evidence quality: Verified — ICLR 2025 peer-reviewed paper, 152K data points.

**Finding 2: Deterministic anchor checks must form the ungameable foundation of the evaluation stack**
Non-LLM verification layers (citation URL liveness via HTTP HEAD, source-claim entailment via NLI model, numerical consistency checks, format/completeness validation) cannot be gamed by optimizing prose quality. These form hard floors that no LLM-based evaluation can override. The Google Vertex AI Check Grounding API returns support scores with claim-by-claim verification at <500ms latency. This deterministic layer is architecturally essential because it closes the class of failure where well-written but factually wrong output passes LLM evaluation.
- Pipeline layer: L4 (Evaluator)
- Build implication: Build Gate 0 (deterministic checks) as the first pass before any LLM judge runs. This is the cheapest and most reliable quality gate — run it on every output, not just high-stakes ones.
- Evidence quality: Verified — HTTP/NLI mechanics are well-established; the Vertex API's specific performance is Credible.

**Finding 3: Cross-model evaluation is essential — same-family evaluation has a perplexity-based bias mechanism**
The "Play Favorites" paper (2025) provides the strongest evidence: GPT-4o and Claude 3.5 Sonnet systematically assign higher scores to their own outputs via a perplexity mechanism (models favor text with lower perplexity, and their own outputs have the lowest). Cross-family evaluation breaks this mechanism. This is not just a theoretical concern — it has an identified causal pathway. Google's FACTS Grounding benchmark explicitly uses mixed judges to mitigate family bias.
- Pipeline layer: L4 (Evaluator)
- Build implication: Never use Claude to evaluate Claude-generated output without a cross-model ensemble member. The Evaluator must include at least one judge from a different model family (e.g., GPT-4o evaluating Claude output, or vice versa).
- Evidence quality: Verified — peer-reviewed paper with causal mechanism identified; Google production implementation as independent validation.

**Finding 4: Calibrated ensembles with regression against a human gold set are more effective than larger uncalibrated ensembles**
LLM-Rubric (ACL 2024) demonstrates 2x improvement over uncalibrated baselines using regression calibration against 50-100 human-annotated examples. A 2-judge calibrated ensemble outperforms a 5-judge uncalibrated ensemble at lower cost. This reframes the ensemble question from "how many judges?" to "how well-calibrated are they?" The implication for Keystone: calibration against actual Keystone deliverables scored by experienced consultants is the highest-leverage investment in evaluation infrastructure.
- Pipeline layer: L4 (Evaluator), META
- Build implication: CAPSTONE-PLAN-v2.md Section 5.4 describes calibrating against 10+ past Keystone deliverables — this is the right approach and the research validates it. Prioritize the gold set creation as infrastructure before running the pipeline on real engagements.
- Evidence quality: Verified — ACL 2024 peer-reviewed paper.

**Finding 5: ICD 203's uncertainty calibration standard fills a gap in the current 8-dimension rubric**
Intelligence Community Directive 203 establishes 9 Analytic Tradecraft Standards. The current rubric's Intellectual Honesty dimension lacks a concrete uncertainty expression standard. ICD 203 provides a calibrated probability language table ("almost no chance" = 1-5% through "nearly certain" = 95-99%) that gives a specific, evaluable criterion for whether uncertainty is properly expressed versus artificially narrowed. This is directly encodable as a sub-criterion.
- Pipeline layer: L4 (Evaluator), L0 (Specification Engine)
- Build implication: Add ICD 203's probability language as an explicit sub-criterion within the Intellectual Honesty dimension. This is a concrete quality improvement, not just an aspiration.
- Evidence quality: Verified — ICD 203 is official IC doctrine, Heuer & Pherson's 66 techniques are the standard reference.

---

## Tool/Framework Verdicts

**DeepEval (v3.2.6, 13.6K stars, Apache-2.0)**
- G-Eval accepts arbitrary natural language criteria; DAG metric builder enables hybrid deterministic/LLM evaluation; pytest integration for CI/CD gates
- Verdict: INTEGRATE
- Justification: Best custom criteria engine for the eight-dimension rubric — use G-Eval for subjective consulting dimensions (Analytical Depth, Intent Alignment) and DAG for deterministic checks; build weighted aggregation as a custom layer on top since DeepEval does not natively support it.

**Inspect AI (UK AISI, v0.3.199, 1.7K stars, MIT)**
- Task-Solver-Scorer composition architecture; adopted by METR and Apollo Research; designed for offline model evaluation
- Verdict: LEARN
- Justification: The Solver-Scorer composition pattern is the right architectural blueprint for building custom evaluation pipelines, but the framework itself is designed for offline batch evaluation, not production pipeline gating — steal the pattern, don't adopt the library.

**Braintrust ($80M Series B, $800M valuation)**
- Eval-gate CI/CD pattern; GitHub Action blocks merges on score drops; cloud-only self-hosting
- Verdict: LEARN
- Justification: The eval-gate pattern (PR blocks when quality drops below threshold) is exactly right for Keystone's development workflow, but replicate it on open-source tools (Promptfoo + Arize Phoenix) rather than paying Braintrust's cloud pricing.

**RAGAS (v0.3.4, 12.4K stars, Apache-2.0, EACL 2024)**
- RAG-centric; Faithfulness, AspectCritique, and Factual Correctness metrics are general-purpose
- Verdict: INTEGRATE (selective)
- Justification: Faithfulness and AspectCritique are directly applicable to the Source Quality and Analytical Depth dimensions in the L4 Evaluator; use as components within DeepEval or a custom pipeline, not as the primary framework.

**Arize Phoenix (v8.x, 8.5K stars, ELv2)**
- Single Docker container, SQLite default, OpenTelemetry-native, integrates with DeepEval/RAGAS/LangGraph
- Verdict: INTEGRATE
- Justification: Primary observability and evaluation storage layer — lightest Mac Mini footprint of any option evaluated (single container vs. Langfuse's 4-service requirement), with native LangGraph integration essential for pipeline monitoring.

**Langfuse (v3, 19K stars, MIT)**
- LLM-as-judge evaluators, annotation queues, Cohen's Kappa analytics; requires PostgreSQL + ClickHouse + Redis + MinIO
- Verdict: LEARN (upgrade path)
- Justification: Infrastructure overhead (4 services including ClickHouse) is excessive for a Mac Mini setup during initial build; use as the upgrade path if Phoenix's analytics become insufficient at production scale.

**Promptfoo (10.4K stars, MIT, used by OpenAI and Anthropic)**
- Evaluates the evaluator; red teaming for adversarial inputs; zero infrastructure (CLI)
- Verdict: INTEGRATE
- Justification: Essential for testing whether the Evaluator's rubric produces expected scores on known-quality outputs — the canary set of 50 outputs with injected errors should be run through Promptfoo after every prompt change.

**DeepTeam (1.3K stars, Apache-2.0)**
- Safety testing (bias, PII, toxicity, prompt injection); explicitly not for quality evaluation
- Verdict: SKIP
- Justification: Their own documentation redirects quality evaluation use cases to DeepEval; Promptfoo covers adversarial testing with better support for quality rubrics.

**Prometheus 2 (EMNLP 2024, purpose-built judge model)**
- 7B variant, ~14GB VRAM, llamafile quantized version achieves 0.9 Pearson correlation with original
- Verdict: INTEGRATE
- Justification: Best open-source local judge model for the cross-family ensemble — runs on Mac Mini M4 Pro 64GB alongside other models, providing a non-API judge that eliminates cost and latency for the first evaluation pass.

**CALM Framework (Ye et al., ICLR 2025)**
- 12 distinct bias types; attack-and-detect methodology; open-source with datasets
- Verdict: INTEGRATE (as periodic diagnostic)
- Justification: Run as a monthly diagnostic audit of the judge pipeline to quantify which biases are active in the specific Keystone judge configuration — not a runtime component, but an essential calibration tool.

**SE-Jury pattern (ASE 2025)**
- Strategy diversity; five evaluation strategies on single model; 29.6-140.8% improvement in human correlation
- Verdict: LEARN
- Justification: Strategy diversity (direct scoring, criteria-based, self-reflection, functional equivalence) is more cost-effective than model diversity for ensemble design — apply this pattern when building consulting-specific evaluation strategies per dimension.

**Agent-as-a-Judge (arXiv:2508.02994)**
- Evaluates dynamic agent behavior and process, not just static outputs
- Verdict: LEARN
- Justification: Future-phase pattern for evaluating whether the research pipeline followed correct execution paths (not just whether the output is good) — relevant when the META layer needs to evaluate methodology quality, not just output quality.

---

## Contradictions with CAPSTONE-PLAN-v2.md

**Plan says:** The eight-dimension rubric dimensions (listed in Section 5.3) should each be evaluated; verbosity bias and position bias are acknowledged risks.
**Evidence shows:** The SOS-Bench finding is more extreme than the plan acknowledges. The plan treats style-over-substance as a bias to mitigate; SOS-Bench shows it is a category-level failure mode that invalidates holistic evaluation entirely. Additionally, the specific bias statistics cited in the research prompt (40% inconsistency from position bias, 15% inflation from verbosity bias) were not independently verified — position bias varies by model and verbosity effects are smaller (~3.7%) when quality is controlled.
**Follow:** The plan's direction is correct (decomposed rubric, multi-pass evaluation) but the implementation must be stricter. Never score multiple dimensions in a single prompt. The exact bias statistics in the plan should be treated as directional rather than precise.

**Plan says:** The Evaluator uses an LLM-as-judge approach as its primary mechanism.
**Evidence shows:** AISI Cohen's Kappa of 0.52 vs. human-human 0.8 means automated graders achieve only "moderate" agreement even on relatively objective questions. For consulting-specific dimensions (Intellectual Honesty, Analytical Depth), expect lower agreement. The automated evaluator cannot be the sole quality arbiter.
**Follow:** The plan's tiered evaluation (Light/Standard/Deep) and human-in-the-loop calibration are the right response. Implement weekly spot-checks and track Cohen's Kappa between human and automated scores as the primary quality signal, recalibrating when kappa drops below 0.6.

**Plan says:** The rubric has eight dimensions.
**Evidence shows:** ICD 203's uncertainty calibration standard (probability language table) is missing from the current rubric's Intellectual Honesty dimension. This is a concrete, encodable gap — not a philosophical difference.
**Follow:** Add ICD 203 probability language as a sub-criterion within Intellectual Honesty. This strengthens, not replaces, the existing dimension.

---

## Cross-Report Flags

**Directly reinforces A1:** The finding that "evaluation quality scales with investment" (from Imbad0202 in A1) is structurally supported by SOS-Bench's 152K-datapoint finding in A2. Both reports converge on the same conclusion from different angles — this is high-confidence validation.

**May contradict A3 (Self-Improvement) on Goodhart risk:** A3 is expected to identify Goodhart's Law as the primary risk to self-improvement systems. A2's finding that automated graders achieve only kappa=0.52 (where kappa=0.8 for humans) means the self-improvement system's driving metric is unreliable. This is a serious compounding risk: optimizing against a 0.52-kappa metric may improve the metric without improving actual quality. Flag for A3 synthesis.

**Informs A4 (Orchestration) on cost modeling:** A2's tiered evaluation cost model (Gate 0: $0, Gate 1: $0 local, Gate 2: $0 local, Gate 3: $0.25-0.50 API) provides the basis for cost-per-engagement calculations in A4/A5. Evaluation will be the dominant cost at scale (A4 finding: verification consumes 72% of tokens in comparable systems).

**Informs all threads:** The recommendation that descending rubric order (5→1) improves scoring accuracy for GPT-4o, Qwen3-32B, and Mistral is a simple, zero-cost implementation improvement that applies to any LLM-as-judge rubric design.
