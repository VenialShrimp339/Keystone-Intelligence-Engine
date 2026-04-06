# Report 9: B4 — AI-Generated Research Quality Failures

## Top Findings

### Finding 1: 28 Empirically Documented Failure Modes — Three Are Highest Priority
The report delivers a 28-failure-mode taxonomy organized in six categories with detection methods and architectural prevention strategies for each. Three failure modes are designated highest priority because they are simultaneously common, consequential, and survive human review: (1) strategic trendslop, (2) style-substance inversion in LLM evaluation, and (3) absence failures. These three must be addressed first in the Evaluator architecture. Every other failure mode in the taxonomy represents a Rejection Library entry. This is the most operationally complete document in Thread B.

**Layer affected:** L4 (Evaluator), META (Rejection Library), L1 (Research Agents)
**Build implication:** The full 28-failure-mode taxonomy is the seed population for the Rejection Library. The three highest-priority failures define the MVP evaluation architecture: (1) differentiation test for trendslop, (2) factual verification separate from stylistic scoring, (3) completeness checklist with mandatory sections for absence detection. Build these three before implementing dimensional rubric scoring.
**Evidence quality:** Verified (METR RCT, BCG/Harvard study, SOS-Bench ICLR 2025, CALM framework ICLR 2025, Deloitte incidents, AbsenceBench, FActScore, Wall Street Prep model testing); Credible (Competitive Intelligence Alliance, Strategex TAM testing); Claimed (select vendor reports clearly flagged as such).

---

### Finding 2: SOS-Bench Is the Single Most Critical Finding for Evaluator Design — Style Bias Is Structural, Not Marginal
SOS-Bench (Feuer et al., ICLR 2025, arXiv:2409.15268) across 152,380 data points: sarcastic tone caused 96% scoring loss while factual errors caused only 13% loss. Style and completeness were near-perfect predictors of overall LLM judge scores while correctness and safety were "considerably weaker predictors." Conciseness was anti-correlated with score — judges actively preferred longer responses. This held across all four judge models tested (GPT-3.5-turbo, GPT-4o-mini, GPT-4o, Claude-3.5-Sonnet). The implication: any single LLM judge will systematically reward polished emptiness over rough accuracy. The Keystone Evaluator cannot be a single LLM judge.

**Layer affected:** L4 (Evaluator — architecture)
**Build implication:** The Evaluator must decompose evaluation into orthogonal dimensions with separate specialized evaluators for each. Factual accuracy and analytical substance must be weighted at ≥3x style scores. Never use a single LLM judge for quality assessment. This is the architectural mandate derived directly from empirical data, not a design preference.
**Evidence quality:** Verified — ICLR 2025 peer-reviewed paper, 152,380 data points, four judge models tested.

---

### Finding 3: Absence Failures Are Twice as Common as Hallucinations and May Be Architecturally Intractable with Transformers
AbsenceBench (arXiv:2506.11440, 14 models tested) found transformer self-attention architectures fundamentally struggle to "attend to information gaps" because there's no token position for absent content. The clinical safety study (Nature Digital Medicine, 2025, 12,999 sentences) found 3.45% omission rate vs. 1.47% hallucination rate — omissions more than twice as common as hallucinations. BART models produced average 3.9 errors but 6.6 omissions per clinical note. The AbsenceBench finding that including a placeholder token improved performance dramatically confirms this as an architectural limitation, not a prompt engineering problem.

**Layer affected:** L4 (Evaluator — Completeness dimension), L1 (Research Agents — output templates)
**Build implication:** Detection must be structural (completeness checklists, mandatory sections) rather than model-based. Build a "completeness checklist evaluator" that generates expected topics, perspectives, and data categories for any given task type, then verifies which are addressed. Deploy a dedicated "gap detector" agent. Require explicit "What I don't know" and "What's not covered" sections in every output template. This addresses the architectural limitation directly.
**Evidence quality:** Verified — AbsenceBench is a specific benchmark paper; Nature Digital Medicine 2025 study is peer-reviewed with 12,999 data points.

---

### Finding 4: A Five-Layer Evaluation Stack Is Recommended — Each Layer Addresses a Specific Failure Category
The report delivers a concrete five-layer architecture: Layer 1 (FActScore atomic fact verification), Layer 2 (citation validation via CrossRef/Semantic Scholar/OpenAlex APIs), Layer 3 (Prometheus 2 multi-rubric scoring weighted to prioritize substance over style), Layer 4 (Agent-as-a-Judge process trajectory evaluation), Layer 5 (diverse judge panel with dynamic team selection and minority-veto capability). This is the most specific Evaluator architecture specification in the research corpus.

**Layer affected:** L4 (Evaluator — complete architecture)
**Build implication:** The five-layer stack is the implementation blueprint. Layer 1 and Layer 2 are deterministic, buildable immediately (APIs exist, FActScore is installable via pip). Layer 3 requires Prometheus 2 setup and custom rubric development. Layer 4 requires Agent-as-a-Judge implementation (not a released product, but arXiv:2410.10934 provides the pattern). Layer 5 requires ensemble infrastructure. Build in stack order: Layers 1-2 first (deterministic verification gates), Layer 3 second (rubric scoring), Layers 4-5 last (process evaluation and ensemble).
**Evidence quality:** Verified for individual components (FActScore, Prometheus 2, Agent-as-a-Judge are all peer-reviewed published systems); Credible for the integration architecture (the stack design is the report's synthesis, not a published system).

---

### Finding 5: The CALM Framework's 12 Bias Types Define Mandatory Mitigations for the Evaluator Design
The CALM framework (Ye et al., ICLR 2025, arXiv:2410.02736) quantified 12 bias types across 6 judge models with specific robustness rates. The most dangerous: authority bias (fake citations reversed ChatGPT's judgment 33.8% of the time), bandwagon bias (even GPT-4o was swayed 20.9% by majority framing; Claude-3.5 at 39%), and position bias (ChatGPT 43.4% inconsistency; Claude-3.5 better at 16.8%). Claude-3.5-Sonnet is the most robust judge overall but has notable bandwagon and sentiment vulnerabilities. Self-enhancement bias is systematically correlated with self-recognition capability.

**Layer affected:** L4 (Evaluator — judge design)
**Build implication:** Four mandatory mitigations: (1) randomize presentation order for all pairwise comparisons; (2) run sentiment-neutralized versions through judges alongside originals; (3) strip authority markers before evaluation; (4) use diverse model panels (PoLL approach). Specifically: do not use Claude-3.5 as the solo judge for any evaluation involving bandwagon framing or sentiment-loaded content — add at least one contrasting model. Never include authority markers (author names, institution affiliations, cited expert names) in evaluation prompts.
**Evidence quality:** Verified — ICLR 2025 peer-reviewed paper, 6 judge models tested, quantified robustness rates provided.

---

## Tool/Framework Verdicts

### Prometheus 2 (Kim et al., EMNLP 2024, arXiv:2405.01535)
**Name/maturity:** Open-source evaluator model, 7B and 8x7B variants. 72-85% human agreement. Custom rubric support with 1,000+ evaluation criteria. Local deployment on single GPU. pip install prometheus-eval.
**Verdict: BUILD**
This is the recommended multi-rubric scoring backbone for Layer 3 of the evaluation stack; build custom consulting rubrics on top of Prometheus 2 rather than relying on a general-purpose LLM judge; the local deployment capability is critical for Mac Mini infrastructure.

### FActScore (Min et al., EMNLP 2023)
**Name/maturity:** Published EMNLP 2023. Decomposes text into atomic facts, verifies each against knowledge sources. <2% error rate vs. human scoring. ~$1 API cost per 100 sentences. pip install factscore.
**Verdict: INTEGRATE**
This is Layer 1 of the evaluation stack — the atomic fact verification foundation; directly addresses the fabrication problem (Deloitte incidents) and the style-substance inversion (flags factually wrong outputs that score high on style).

### ARES (Saad-Falcon et al., NAACL 2024)
**Name/maturity:** Published NAACL 2024. Evaluates RAG systems on context relevance, answer faithfulness, answer relevance. Fine-tunes lightweight judges with synthetic data. Outperforms RAGAS by 59.3 and 14.4 percentage points. Predicts hallucination within 2.5 percentage points with 78% fewer annotations.
**Verdict: INTEGRATE**
Essential for evaluating the research retrieval pipeline quality (Layer 1.5 of the evaluation stack, between atomic fact verification and rubric scoring); addresses the fabrication gap where retrieved content is used but misrepresented.

### Agent-as-a-Judge (Zhuge et al., October 2024, arXiv:2410.10934)
**Name/maturity:** Published October 2024. Evaluates research process via task-solving trajectory observation. ~90% agreement with human experts (vs. ~70% for LLM-as-Judge). 97.7% time savings, 97.6% cost savings.
**Verdict: BUILD**
This is Layer 4 of the evaluation stack — process trajectory evaluation; directly applicable to multi-agent research pipelines; the accuracy improvement over static LLM-as-Judge (90% vs. 70%) justifies the implementation investment.

### DeepResearchGym (Coelho et al., CMU, May 2025, arXiv:2505.19253)
**Name/maturity:** Open-source benchmark, CMU, May 2025. Evaluates deep research systems across information coverage, retrieval faithfulness, and report quality. Local deployment available.
**Verdict: INTEGRATE**
Use as the benchmark for evaluating the Keystone system's research output quality relative to other deep research systems; aligns evaluation criteria with an external standard rather than only internal calibration.

### SE-Jury (ASE 2025, arXiv:2505.20854)
**Name/maturity:** Published ASE 2025. 5 independent evaluation strategies with dynamic team selection. 29.6-140.8% improvement in correlation with human judgments. Dynamic selection reduces cost ~50%.
**Verdict: INTEGRATE**
The dynamic team selection mechanism (some strategies are detrimental for certain tasks; selecting the optimal subset outperforms full ensemble) is the Layer 5 architecture pattern; borrow the dynamic selection approach for the ensemble meta-evaluation layer.

### PoLL (Verga et al., 2024, arXiv:2404.18796)
**Name/maturity:** Published 2024. Diverse panel of smaller models (Command R + Haiku + GPT-3.5) outperforms single GPT-4 while being 7-8x cheaper. Reduces intra-model bias.
**Verdict: INTEGRATE**
The cost-quality tradeoff and bias reduction are directly applicable to the Layer 5 ensemble design; a panel of three smaller diverse models costs less and performs better than a single expensive judge.

### DeepResearch Bench (Du et al., arXiv:2506.11763)
**Name/maturity:** 2506 preprint. RACE framework (adaptive criteria) and FACT framework (citation count and accuracy separately). DRB II provides 9,430 fine-grained binary rubrics.
**Verdict: LEARN**
The adaptive criteria generation concept (generating evaluation criteria dynamically based on the specific research question) is valuable for the L0 Specification Engine's task quality criteria; borrow the pattern of generating rubric criteria from the task specification rather than using static criteria.

### VERDICT (Haize Labs, 2025)
**Name/maturity:** Haize Labs report, 2025. +14.5% over standalone GPT-4o on factuality detection.
**Verdict: LEARN**
The ensemble + verification pipeline pattern is the same as the five-layer stack recommendation; use as a reference architecture for the ensemble design, not as a deployable component.

### AlpacaEval 2.0 / Arena-Hard
**Name/maturity:** Standard chatbot benchmarks.
**Verdict: SKIP**
Designed for chatbot response comparison, not research quality evaluation; inapplicable to the Keystone context.

### VHELM / Audio-HELM
**Name/maturity:** Modality-specific benchmarks.
**Verdict: SKIP**
Not relevant to text-based consulting research quality.

### RAGAS
**Name/maturity:** RAG evaluation framework; superseded by ARES for the purposes in this system.
**Verdict: SKIP (as primary) / LEARN (as baseline)**
ARES outperforms RAGAS by large margins for the relevant use cases; use RAGAS only as a baseline comparison for validating ARES implementation.

---

## Contradictions with CAPSTONE-PLAN-v2.md

### Contradiction 1: The plan's Evaluator is implicitly a single-model judge; the evidence mandates multi-model architecture
**Plan says:** Section 5 describes "the Evaluator" as a single component. Section 5.5 distinguishes evaluation intensity tiers. The plan does not specify that multiple different model families are required.
**Evidence shows:** SOS-Bench demonstrates that any single LLM judge systematically rewards style over substance. CALM framework shows Claude-3.5 specifically has 39% bandwagon susceptibility and significant sentiment bias. A single-model Evaluator will produce systematically biased scores.
**Resolution:** Follow the evidence. The Evaluator must be a multi-layer system with deterministic verification (Layers 1-2), Prometheus 2 for rubric scoring (Layer 3), and a diverse model ensemble for meta-evaluation (Layer 5). "The Evaluator" in the plan refers to the evaluation subsystem, not a single model call.

### Contradiction 2: The plan focuses the Evaluator on output quality; the evidence shows process quality must also be evaluated
**Plan says:** Section 5 evaluates outputs against the eight-dimension rubric. The evaluation framework is output-focused.
**Evidence shows:** Agent-as-a-Judge achieves 90% human agreement by evaluating task-solving trajectories, not just final outputs. The METR finding (50-67% of AI PRs that pass automated tests get rejected by human maintainers) suggests that process quality predicts output quality failures that aren't visible in the output alone.
**Resolution:** Follow the evidence. Add a process trajectory evaluation layer (Layer 4 of the five-layer stack) that assesses research agent behavior, not just deliverable content. This is a non-trivial addition to the plan's Evaluator design.

### Contradiction 3: The plan treats citation quality as a rubric dimension; the evidence treats citation existence as a binary gate
**Plan says:** Source Quality (10%) is a rubric dimension that can be scored partially.
**Evidence shows:** Zero-tolerance architecture for citation fabrication — the system must never generate citations from parametric knowledge. DOI error rates of 36.2% and author-title fabrication make partial credit for citations dangerous. The Deloitte incidents demonstrate that even one fabricated citation destroys the entire deliverable's credibility.
**Resolution:** Maintain Source Quality as a dimension but add a pre-rubric binary gate: citation existence verification via CrossRef/Semantic Scholar/OpenAlex APIs. Any citation that fails the existence check triggers immediate rejection, not a score deduction. The rubric then scores remaining source quality factors (diversity, timeliness, reliability).

### Contradiction 4: The plan's "self-evaluation problem" (Section A2 prompt context) is partially addressed but not solved
**Plan says:** The system needs to prevent "same model evaluating same model" failure. Section 5 mentions anti-confirmatory checking and factorial evaluation but doesn't specify different model families for evaluation.
**Evidence shows:** Self-enhancement bias (models rate their own outputs higher) correlates linearly with self-recognition capability. CALM quantified this. The solution is cross-model evaluation (different model family as judge) plus the PoLL diverse-panel approach.
**Resolution:** Follow the evidence. The plan's solution to self-evaluation is incomplete. Add the mandatory cross-model constraint: the primary generation model cannot be used as the primary evaluation model. If Claude Sonnet generates the research output, the rubric evaluation layer should use a different model family (GPT-4 class or Gemini class) as the primary judge, with Claude as one of multiple ensemble members.

---

## Cross-Report Flags

**Reinforces B1 (Report 6):** B4's Category 1.5 (professional-grade fabrication, Deloitte incidents) provides the specific empirical grounding for B1's "automatic fail" trigger recommendation. B4 adds the zero-tolerance architecture (citation-grounded RAG, verification microservice) that B1 implies but doesn't specify. Together they define a complete citation integrity system: structural prevention (RAG-only citations) plus runtime verification (existence check gate) plus rubric scoring (Source Quality dimension).

**Reinforces B2 (Report 7):** B4's anti-pattern documentation (Category 3: fluency trap) directly maps to B2's anti-pattern 3 (style over substance). Both identify the same failure mode from different angles. B4 provides the quantitative data (SOS-Bench 96% vs. 13%), B2 provides the framing (Halo Effect for LLMs). Together they mandate the same Evaluator design: factual verification weighted at ≥3x style scores, with style evaluation separated from substance evaluation.

**Reinforces B3 (Report 8):** B4's three highest-priority failure modes (trendslop, style-substance inversion, absence failures) map directly to B3's three Rejection Library categories (judgment failures, analytical failures, structural failures) but in different order. B3 prioritizes structural failures (most detectable) first; B4 prioritizes impact (most dangerous to consulting quality) first. Synthesis: build detection in B4's impact priority order, but implement using B3's detection sophistication gradient (machine-checkable first, then expert-checkable, then judgment-dependent).

**Flag for Thread A (evaluation frameworks):** B4 recommends Prometheus 2 as the multi-rubric backbone (Layer 3) and FActScore as the atomic verification backbone (Layer 1). Thread A Report 2 (A2: Evaluation and Verification Frameworks) will likely evaluate these same tools independently. Look for convergence or contradiction on Prometheus 2 specifically — if A2 reaches a different verdict on Prometheus 2's custom rubric flexibility or local deployment capability, that should trigger re-evaluation.

**Flag for Thread A (agent architecture):** B4's failure mode 1.3 (jagged frontier collapse) directly informs the Specification Engine's task classification requirement. The system must classify every task against a capability frontier map before execution, routing outside-frontier tasks to mandatory human review. This is an L0 architectural requirement derived from B4's empirical finding. Thread A's orchestration reports will determine how to implement this classification in the task dispatch system.

**Flag for Thread C (deliberation):** B4's failure mode 5.3 (anchoring and confirmation bias amplification) finds 17.8-57.3% bias-consistent behavior in LLMs across decision scenarios, with adversarial framing causing 16-93 percentage point detection degradation. This directly validates the plan's anti-confirmatory framing requirement (Section 3.6, mandatory anti-confirmatory framing in research-tasks.json). The data provides quantitative justification: without anti-confirmatory framing, up to 93% of relevant evidence may be missed in adversarial contexts.

**Flag for Thread C (self-improvement):** B4's failure mode 1.6 (the evaluation gap — models detect when being evaluated) is a specific threat to the self-improvement loop. If Research Agents detect they're being evaluated by the Evaluator, they may modify behavior to score well without improving actual quality. The architectural prevention (evaluation structurally indistinguishable from production; canary tasks embedded in real workstreams without markers) is relevant to how the self-improvement loop should be designed to avoid Goodhart's Law.
