# Evaluation architecture for the Keystone Intelligence Engine

**The Evaluator's power comes not from any single framework but from a layered architecture: deterministic checks form an ungameable foundation, decomposed LLM judging provides nuanced quality assessment, and cross-model ensembles neutralize the biases that make any individual judge unreliable.** This report synthesizes research across 8 evaluation frameworks, 7 academic papers, verified bias statistics, and production implementation patterns to deliver USE/LEARN/SKIP verdicts for every component. The critical finding: SOS-Bench proves that holistic LLM judging is fundamentally broken for consulting quality — sarcasm causes **96% scoring loss** while factual errors cause only **13%** — making your eight-dimension decomposed rubric not just useful but architecturally essential.

---

## Section 1: Eight frameworks, four verdicts that matter

### DeepEval — USE

**Stars: 13.6K | License: Apache-2.0 | Version: 3.2.6 | Evidence: Verified**

DeepEval is the strongest candidate for the primary evaluation engine. G-Eval accepts arbitrary natural language criteria (`criteria="Determine whether the output demonstrates intellectual honesty by acknowledging uncertainty and limitations"`), supports custom `evaluation_steps`, rubric overrides via `GEvalTemplate` subclassing, and chain-of-thought token-probability normalization. The DAG metric builder creates deterministic evaluation decision trees with Task nodes and Binary Judgment nodes, enabling hybrid approaches where G-Eval runs as a node within a DAG.

**For the eight-dimension weighted rubric**: DAG produces a single score per graph, so you need either 8 separate DAG metrics with weighted aggregation or a custom `BaseMetric` subclass orchestrating multiple DAGs. DeepEval does not natively support weighted multi-metric aggregation — **you must build this layer yourself**. The pytest integration (`deepeval test run`, `assert_test()`) makes CI/CD evaluation gates straightforward.

Key limitations: heavy reliance on OpenAI as judge model (custom models carry a documented warning that "evaluations may not work as expected"), strong push toward their commercial Confident AI platform for dashboards and experiment tracking, and the framework's author has been noted writing comparison articles ranking DeepEval first.

**Verdict: USE** — Integrate G-Eval for subjective consulting dimensions and DAG for deterministic checks. Build weighted aggregation on top.

### Inspect AI (UK AISI) — LEARN

**Stars: 1.7K | License: MIT | Version: 0.3.199 | Evidence: Verified**

The Task → Solver → Scorer architecture is genuinely elegant. Solvers chain composably (e.g., `chain_of_thought → generate → self_critique`), scorers return flexible `Score` values (dictionaries, sequences, mappings), and the `grouped()` function applies metrics by metadata key — useful for per-engagement-type weighting. The Agent Bridge wraps LangChain and OpenAI Agents for evaluation within Inspect's framework. Documentation is excellent (inspect.aisi.org.uk), and adoption by METR and Apollo Research validates the design.

However, Inspect is designed for offline model evaluation, not production pipeline monitoring. No built-in tracing, alerting, or online evaluation. The **Solver-Scorer composition pattern** is the real intellectual contribution worth stealing.

**Verdict: LEARN** — Adopt the composition architecture for building custom evaluation pipelines, but don't depend on the framework for production.

### Braintrust — LEARN

**Funding: $80M Series B Feb 2026, $800M valuation | Evidence: Verified**

The eval-gate CI/CD pattern — GitHub Action runs evals on every PR, posts case-by-case regression analysis, blocks merges when scores drop below thresholds — is the right mental model. Customers include Notion, Replit, Stripe, Vercel.

Critical distinction: **Braintrust gates deployment, not individual outputs.** For real-time "Evaluator rejects output and triggers regeneration," you'd need custom orchestration using their scoring API. Self-hosting requires Enterprise contract (free/pro tiers are cloud-only), and the core platform is proprietary. Pricing: $1.50–$2.50 per 1K evaluation scores, $3–$4/GB tracing.

**Verdict: LEARN** — Replicate the eval-gate pattern (dev → staging → production thresholds, PR-level quality reporting, threshold-based blocking) on open-source tools.

### RAGAS — USE (selectively)

**Stars: 12.4K | License: Apache-2.0 | Version: 0.3.4 | Evidence: Verified (EACL 2024 paper)**

Cherry-pick three metrics for integration into the broader eval system. **Faithfulness** measures whether outputs are grounded in source materials — directly relevant for consulting briefs citing research. **AspectCritique** is entirely general-purpose and evaluates any custom dimension you define. **Factual Correctness** checks accuracy against references. The v0.3+ rewrite added `DiscreteMetric` and `NumericMetric` that accept arbitrary evaluation prompts.

The framework remains RAG-centric in design (data model assumes `contexts`, `question`, `answer` columns), and non-RAG use cases feel bolted on. No experiment tracking, CI/CD integration, or production monitoring.

**Verdict: USE selectively** — Integrate Faithfulness and AspectCritique as components within DeepEval or a custom pipeline. Don't use RAGAS as the primary framework.

### Langfuse vs. Arize Phoenix — the observability decision

**Langfuse** (19K stars, MIT, v3) provides rich evaluation capabilities beyond pure tracing: LLM-as-judge evaluators, annotation queues, score analytics with Cohen's Kappa and correlation analysis, and datasets/experiments for benchmarking. Self-hosting v3 requires PostgreSQL + ClickHouse + Redis + MinIO — **heavy for Mac Mini**. A 32GB M4 Pro handles it but a 16GB unit would be tight.

**Arize Phoenix** (8.5K stars, ELv2 license, v8.x) offers similar capabilities with dramatically lighter infrastructure: **single Docker container, SQLite default, no ClickHouse/Redis/S3 required**. It runs from `pip install arize-phoenix` with zero infra. OpenTelemetry-native. Integrates with DeepEval, RAGAS, and LangGraph. The trade-off: Elastic License 2.0 (not MIT) restricts providing it as a managed service.

**Verdict: USE Phoenix as primary** (lightweight, Mac Mini-optimal), with Langfuse as the upgrade path if Phoenix's analytics become insufficient. For a Mac Mini cluster, Phoenix's single-container deployment is a clear winner.

### Promptfoo — USE

**Stars: 10.4K | License: MIT | Evidence: Verified (used by OpenAI and Anthropic)**

Promptfoo fills a unique niche: **evaluating the evaluator**. You can use the `echo` provider to pass pre-generated content through without re-calling LLMs, define rubric-based assertions to test whether your eval rubric produces expected scores on known-quality outputs, and compare different grading models side-by-side. The red teaming engine (20+ vulnerability types) can target your Evaluator component directly — point it at your evaluation endpoint and test whether adversarial inputs cause incorrect scores.

Zero infrastructure: CLI tool running on Node.js, no Docker or database. Runs on any Mac Mini.

**Verdict: USE** — Essential for rubric validation, evaluator robustness testing, and CI/CD quality gates.

### DeepTeam — SKIP

**Stars: 1.3K | License: Apache-2.0 | Evidence: Credible**

Built by the same team as DeepEval, focused exclusively on safety testing (bias, PII leakage, toxicity, prompt injection). Their own docs state: "If you're looking to test on criteria such as RAG correctness, answer relevancy… you should check out DeepEval instead." Promptfoo already covers adversarial testing with better support for quality evaluation rubrics.

**Verdict: SKIP** for consulting quality evaluation. Revisit only if formal OWASP/NIST safety compliance becomes a requirement.

---

## Section 2: LLM-as-judge failure modes are the real architecture

### The twelve biases that will corrupt your Evaluator

The CALM framework (Ye et al., ICLR 2025) identifies **12 distinct bias types** through an attack-and-detect methodology — deliberate perturbations measured via Robustness Rate and Consistency Rate across 6 judge models. For consulting-quality evaluation, these rank by threat level:

**Critical threats** to your eight-dimension rubric:

- **Verbosity bias** — longer briefs score higher regardless of analytical quality, directly undermining Actionability and Analytical Depth scoring
- **Authority bias** — impressive-sounding but potentially fabricated citations inflate Source Quality scores
- **Fallacy-oversight bias** — judges miss flawed reasoning chains, undermining Quantitative Rigor and Analytical Depth
- **Style-over-substance** (from SOS-Bench, not CALM) — the dominant failure mode; sarcastic tone causes 96% scoring loss while factual errors cause only 13%

**Moderate threats**: Sentiment bias (confident tone scores higher than appropriately hedged analysis, threatening Intellectual Honesty), self-enhancement bias (same model family generates and evaluates), refinement-aware bias (multi-draft pipeline inflates scores when the judge knows output was "refined"), and bandwagon bias (consensus views favored over contrarian-but-correct analysis).

**Lower threats** for this use case: Position bias (relevant only in pairwise comparison, not pointwise rubric scoring), compassion-fade bias, diversity bias, and chain-of-thought bias.

The CALM framework is implementable as a **periodic diagnostic tool** — run perturbation tests against your rubric dimensions to quantify which biases are active in your specific judge configuration. It is open-source with datasets on GitHub.

### SOS-Bench proves decomposition is non-negotiable

SOS-Bench (Feuer et al., ICLR 2025) analyzed **152,380 data points across 19 benchmarks** and found LLM-judge preferences show essentially zero correlation with concrete measures of safety, world knowledge, or instruction following. The paper does not directly test decomposed evaluation, but its findings strongly imply decomposition helps: since holistic judgments conflate style with substance, scoring factual accuracy independently from narrative quality allows detection and mitigation of style-substance confusion.

The paper's primary recommendations: never rely solely on LLM-judge scores, complement with ground-truth benchmarks, and focus on SFT data quality over preference optimization. The paper is primarily diagnostic rather than prescriptive — it proves the problem at massive scale without offering a complete solution architecture.

**Verdict: USE** — The strongest evidence that your decomposed eight-dimension rubric is architecturally correct. SOS-Bench is the paper to cite when justifying the design.

### Three additional findings that change the implementation

**Scoring prompt biases** (Li et al., arXiv:2506.22316, Feb 2026) identify three novel biases beyond CALM's content-focused taxonomy. **Rubric order bias**: descending score descriptions (5→1) actually improved accuracy for GPT-4o, Qwen3-32B, and Mistral — use descending order. **Score ID bias**: Roman numerals sometimes outperform Arabic numerals. **Reference answer score bias**: the most impactful — including a reference answer scored at 5 systematically inflates all scoring, with correlation fluctuations up to **0.2** for smaller models. Practical implication: never include high-scoring reference answers in evaluation prompts.

**SE-Jury** (ASE 2025) achieved **29.6–140.8% improvement** in human correlation using strategy diversity rather than model diversity. Five evaluation strategies — direct scoring, assessment with self-reflection, criteria-based evaluation, functional equivalence, and test-based evaluation — run on a single model (GPT-4o-mini at $0.15/M tokens). A dynamic team selection mechanism chooses the optimal subset per task, reducing cost. The pattern is directly transferable: define 3–5 consulting-specific evaluation strategies per dimension.

**Prometheus 2** (EMNLP 2024) provides an open-source purpose-built judge model supporting custom rubrics. The 7B variant runs on a single consumer GPU (~14GB VRAM) and achieves the highest correlation with human evaluators among open models. A llamafile quantized version achieves Pearson correlation of 0.9 versus the original. Ideal as one member of a cross-family judge ensemble alongside API judges.

---

## Section 3: Verified bias statistics and the self-evaluation problem

Of seven specific bias statistics provided, research confirms **two exactly**, **two directionally**, and **three remain unverified**:

| Claim | Status | Source |
|-------|--------|--------|
| GPT-4 ~80% agreement with humans | **Confirmed** | Zheng et al. (NeurIPS 2023), MT-Bench + Chatbot Arena |
| AISI κ=0.52 vs human κ=0.8 | **Confirmed exactly** | AISI May 2024 blog, biology/chemistry grading |
| Self-enhancement bias 5–7% | Direction confirmed, magnitude unverified | "Play Favorites" (Spiliopoulou et al. 2025), CALM |
| Position bias causes 40% inconsistency | Unverified number; bias is real but varies by model | Shi et al. (2025) found wide variance across 15 judges |
| Verbosity bias inflates scores ~15% | Unverified; one study found only ~3.7% effect | Shi et al. found no significant trend after controlling for quality |
| Domain expert agreement 60–68% | Plausible but no traceable source | Standard inter-rater ranges vary widely by domain |
| Ensemble reduces biases 30–40% at 3–5x cost | Unverified; direction plausible | Cost is linearly multiplicative; reduction magnitude varies |

The **80% agreement** figure applies to open-ended chatbot preference on pairwise comparisons — not structured analytical brief grading. Expect significantly lower agreement for consulting-specific dimensions, especially Intellectual Honesty and Analytical Depth. The AISI κ=0.52 finding is particularly sobering: automated graders achieve only "moderate" agreement where humans achieve "substantial/almost perfect" — and this was for relatively objective biology/chemistry questions, not subjective analytical quality.

### Cross-model evaluation has strong empirical support

The "Play Favorites" paper (2025) provides the strongest evidence: GPT-4o and Claude 3.5 Sonnet **systematically assign higher scores to their own outputs** and exhibit "family bias" favoring outputs from the same model lineage. The mechanism is perplexity-based — models favor text with lower perplexity, and their own outputs have the lowest. Cross-family evaluation breaks this mechanism because different families have different internal distributions.

Google's FACTS Grounding benchmark uses "a combination of different judges to mitigate any potential bias of a judge giving higher scores to responses produced by a member of its own model family." Implementation pattern: use Claude to evaluate outputs generated by GPT-4 (or vice versa), never within the same model family.

### Calibrated ensembles outperform pure ensembles

Rather than simply adding judges (linear cost increase), the LLM-Rubric approach (Hashemi et al., ACL 2024) uses **regression-based calibration** against a small set of human-annotated examples to achieve **2× improvement** over uncalibrated baselines. This means a 2-judge calibrated ensemble can outperform a 5-judge uncalibrated ensemble at lower cost.

The optimal pattern: ensemble of **2–3 models from different families**, combined with regression calibration against a "gold set" of **50–100 human-graded briefs**. Minority-veto logic (where any judge's low score flags the output) increases True Negative Rate substantially — better for high-stakes consulting deliverables where false positives are expensive.

---

## Section 4: ICD 203 provides a battle-tested rubric template

Intelligence Community Directive 203 establishes **9 Analytic Tradecraft Standards** that map remarkably well to AI evaluation:

Standards 1–3 cover **epistemic hygiene** — source attribution, uncertainty quantification with prescribed probability language ("almost no chance" 1–5% → "nearly certain" 95–99%), and explicit separation of intelligence from analyst assumptions. Standard 4 requires **analysis of competing hypotheses** — directly evaluable by checking whether outputs consider alternatives. Standard 5 demands **customer relevance and actionability**. Standard 6 requires **clear logical argumentation** with the main message upfront. Standard 8 addresses **accuracy**.

Your existing eight-dimension rubric aligns well with ICD 203 but could be strengthened in two areas: **uncertainty calibration** (ICD 203's probability language table provides a concrete standard for evaluating whether uncertainty is properly expressed) and **assumption/judgment separation** (ICD 203 Standard 3 explicitly requires distinguishing underlying information from analyst judgments).

Heuer & Pherson's 66 structured analytic techniques yield three directly automatable evaluation checks: **Analysis of Competing Hypotheses** (does the output evaluate competing explanations?), **Key Assumptions Check** (are assumptions explicitly stated?), and **Argument Mapping** (is the logical structure sound?). These can be operationalized as sub-criteria within the Analytical Depth and Intellectual Honesty dimensions.

**Can MECE be evaluated by an LLM judge?** Partially. "Mutually exclusive" (checking for overlapping categories) is relatively objective and evaluable. "Collectively exhaustive" (identifying gaps) requires domain knowledge and is much more subjective. Decompose into binary sub-questions rather than a single MECE score. Calibrate against ~30 human-annotated examples.

---

## Section 5: The four-layer anti-gaming architecture

### Layer 1 — Deterministic anchor checks (ungameable foundation)

Non-LLM verification layers that cannot be gamed by optimizing prose quality:

- **Citation URL liveness**: HTTP HEAD requests on all cited URLs — fast, deterministic, binary pass/fail
- **Source-claim entailment**: NLI model checks whether the cited source actually supports the claim (Google Vertex AI Check Grounding API returns support scores 0–1 with claim-by-claim verification, latency <500ms)
- **Numerical consistency**: Extract all numbers, verify internal consistency (percentages sum correctly, cited statistics match source data)
- **Format/completeness validation**: Deterministic regex/schema checks for structural requirements
- **Metadata verification**: Publication dates, author credentials, journal existence

These form hard floors that no LLM-based evaluation can override. A brief that cites dead URLs or internally inconsistent numbers fails regardless of how well-written it is.

### Layer 2 — Adversarial probes and factorial testing

Maintain a **"canary set" of ~50 outputs with injected errors** of varying types and severity: wrong probabilities, unsupported conclusions, missing alternative analyses, fabricated citations, logical fallacies. Re-test the Evaluator against this set after every model or prompt change.

The REFINE framework (IBM, arXiv 2508.02827) demonstrates that creating 3-tiered quality hierarchies and testing whether evaluators correctly preserve ordering improved alignment from below 0.7 to above 0.9. Computational cost: linear in variants × dimensions. For 3 variants × 5 dimensions: 15 LLM calls per calibration test.

### Layer 3 — Multi-persona evaluation

Deploy separate LLM judge prompts as adversarial personas, each scoring a different dimension:

- **Devil's Advocate** — challenges assumptions (maps to ICD 203 Standard 3/4)
- **Stakeholder proxy** — tests relevance and actionability (Standard 5)
- **Methodologist** — critiques logical structure and quantitative rigor (Standard 6)
- **Domain Expert** — tests factual accuracy and completeness (Standard 8)

The MAJ-EVAL framework (2025) demonstrates that multi-agent personas with in-group debate followed by synthesized multi-dimensional rating catch failure modes that single evaluators miss — particularly omissions, inappropriate certainty, and missing stakeholder perspectives.

### Layer 4 — Human-in-the-loop calibration

**Minimum viable cadence**: after every model/prompt change (immediate recalibration), weekly 5–10% spot-checks (~2–4 hours expert time), monthly full calibration against the gold set. Track Cohen's κ between human and automated scores — recalibrate when κ drops below 0.6. The Hugging Face cookbook recommends ~30 annotated examples as sufficient for initial calibration.

---

## Section 6: Production stack for Mac Mini infrastructure

### Recommended hardware and software

**Hardware**: 2–3× Mac Mini M4 Pro 64GB (~$2,200 each, ~$6,600 total). The M4 Pro delivers Geekbench 6 multi-core scores exceeding the M2 Ultra Mac Studio at **20–40W** power draw. LLM performance: **8B models at 20–30 tok/sec**, 32B models at 11–14 tok/sec (Q4 quantization), 70B models at 8–12 tok/sec. Multiple models can reside in the 64GB unified memory simultaneously.

**Minimum viable evaluation stack**:

| Component | Tool | Deployment | Mac Mini Fit |
|-----------|------|-----------|-------------|
| Evaluation metrics | DeepEval | `pip install` | Excellent |
| Observability + storage | Arize Phoenix | Single Docker container, SQLite | Excellent |
| Evaluator testing | Promptfoo | CLI (Node.js) | Excellent |
| Local judge model | Prometheus 2 7B or Qwen 2.5 32B via Ollama | Native | Good |
| Orchestration | LangGraph | `pip install` | Excellent |
| Cross-model judge | Claude/GPT-4o API | API calls | N/A |

Phoenix integrates directly with LangGraph via auto-instrumentor, DeepEval via `CallbackHandler`, and supports LLM-as-judge evaluators, datasets, and experiments — all in a single container with SQLite.

### Tiered evaluation for cost and latency optimization

| Tier | Judge | Dimensions | Latency | Cost | When |
|------|-------|-----------|---------|------|------|
| Gate 0 | Deterministic checks | URL, numbers, format | <2s | $0 | Every output |
| Gate 1 | Local 8B model | 3 critical dimensions | ~10–15s | $0 | Every output |
| Gate 2 | Local 32B model | All 8 dimensions | ~50–75s | $0 | Passed Gate 1 |
| Gate 3 | Cloud API ensemble | All 8 dimensions, cross-model | ~5–10s | $0.25–0.50 | Borderline or high-stakes |

Evaluation parallelizes across dimensions and across Mac Mini nodes. A 3-node cluster can run 3 evaluation dimensions simultaneously, bringing Gate 2 latency from ~75s sequential to ~25s parallel.

### LangGraph integration pattern

LangGraph quality gates follow the PROMOTE/HOLD/ROLLBACK pattern documented in arXiv 2603.15676: the Evaluator node receives structured output, runs tiered evaluation, and returns a routing decision. PROMOTE flows to output delivery; HOLD triggers re-generation with rejection feedback appended to context; ROLLBACK escalates to human review. A published implementation achieved 36/38 runs promoted, 2 rolled back (catching evidence coverage drops to 50%).

Store evaluation results in Phoenix (PostgreSQL-backed for production scale) with this schema: `evaluation_id`, `timestamp`, `input_hash`, `output_hash`, `model_version`, `evaluator_model`, per-dimension scores as JSON, `overall_weighted_score`, `human_override`, `evaluation_latency_ms`. Track rolling averages per dimension over 7/30/90-day windows and alert on >10% score degradation.

---

## Conclusion: What this means for the Keystone Evaluator

The research converges on five non-negotiable architectural decisions. **First**, decomposed evaluation is not optional — SOS-Bench's 152K-datapoint proof that holistic judging conflates style with substance makes your eight-dimension rubric the correct design, not a nice-to-have. Score each dimension with a separate prompt, never all at once. **Second**, deterministic checks must form the foundation layer — citation verification, numerical consistency, and format validation create ungameable floors that LLM judges cannot override. **Third**, cross-model judging is essential — the perplexity mechanism underlying self-enhancement bias means you must never use the same model family for generation and evaluation. **Fourth**, calibration against a human gold set matters more than ensemble size — regression calibration with 50–100 human-graded examples achieves 2× improvement over uncalibrated baselines, outperforming larger uncalibrated ensembles at lower cost. **Fifth**, descending rubric order, no reference answer anchoring, and explicit anti-verbosity instructions in each dimension's prompt are cheap mitigations with outsized impact on scoring accuracy.

The biggest gap in the current rubric design: ICD 203's **uncertainty calibration standard** (prescribed probability language from "almost no chance" to "nearly certain") is missing from the eight dimensions. Adding an explicit uncertainty expression sub-criterion within Intellectual Honesty would close this gap and provide a concrete, evaluable standard that distinguishes appropriately caveated analysis from false confidence — the hallmark of consulting quality that LLM outputs most commonly fail to achieve.

### Master verdict table

| Component | Verdict | Rationale |
|-----------|---------|-----------|
| DeepEval | **USE** | Best custom criteria engine; build weighted aggregation on top |
| Inspect AI | **LEARN** | Steal Solver-Scorer composition; too safety-focused for production |
| Braintrust | **LEARN** | Replicate eval-gate CI/CD pattern on open-source tools |
| RAGAS | **USE (selective)** | Faithfulness + AspectCritique as component metrics only |
| Arize Phoenix | **USE** | Primary observability + eval; lightest Mac Mini footprint |
| Langfuse | **USE (backup)** | Upgrade path if Phoenix becomes insufficient |
| Promptfoo | **USE** | Essential for evaluator robustness testing and CI/CD |
| DeepTeam | **SKIP** | Safety-only; Promptfoo covers adversarial testing better |
| CALM (12 biases) | **USE** | Periodic diagnostic audit of judge pipeline |
| SOS-Bench | **USE** | Foundational evidence for decomposed rubric architecture |
| Scoring Bias paper | **USE** | Rubric prompt engineering (descending order, no anchoring) |
| Prometheus 2 | **USE** | Local 7B judge model as ensemble member |
| SE-Jury pattern | **LEARN** | Strategy diversity > model diversity for ensembles |
| Agent-as-a-Judge | **LEARN** | Future phase: process-aware evaluation of pipeline steps |
| LLM-as-Judge Survey | **LEARN** | Reference document for architecture decisions |
| ICD 203 standards | **USE** | Battle-tested rubric template; adopt probability language |
| Cross-model eval | **USE** | Strong empirical support via perplexity mechanism |
| Calibrated ensembles | **USE** | 2× improvement over uncalibrated at lower cost |
| Deterministic anchors | **USE** | Ungameable foundation layer |
| Constitutional principles | **LEARN** | Encode anti-bias instructions in prompts; not a substitute for cross-model |
| Multi-persona eval | **USE** | Different personas catch different failure modes |
| Canary set testing | **USE** | 50 outputs with injected errors; test after every change |
| Human calibration | **USE** | Weekly spot-checks minimum; κ tracking for drift detection |