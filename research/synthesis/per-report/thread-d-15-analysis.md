# Report 15: D2 — Academic Papers on Automated Analysis

## Source
`research/reports/batch-1/Deep_Research_Report_From_Prompt_15.md`

---

## Top Findings

### Finding 1: Unstructured multi-agent networks amplify errors 17.2x; centralized verification reduces this to 4.4x — DPVI is empirically optimal
**Pipeline layer affected:** L1 (Research Agents), L4 (Evaluator)
**Evidence quality:** Verified (peer-reviewed, 180 controlled configurations, Google DeepMind)

The Google DeepMind scaling study (Kim, Gu, et al., December 2025; arXiv:2512.08296) tested 180 configurations across 5 architectures and 3 LLM families. Independent multi-agent systems amplified errors 17.2x through unchecked propagation. Centralized coordination reduced this to 4.4x and improved performance by 80.9% on parallelizable tasks. The DPVI architecture maps to the "centralized" topology (parallel generation + centralized verification), not the independent topology. This is the single most important validation finding for Keystone's core architecture.

**Critical constraint also identified:** All multi-agent variants degraded performance by 39-70% on sequential reasoning tasks. The parallelizable vs. sequential distinction determines when multi-agent helps and when it hurts. Research gathering (L1) is parallelizable; synthesis and judgment (L2, L4) are sequential. This creates a clear architectural boundary: parallelize research, serialize synthesis.

**What it means for the build:** This empirical result validates the DPVI architecture and quantifies the risk of the alternative (independent agents). It also provides a hard design rule: L1 should be parallel, L2 and above should be serial. The plan currently describes this correctly but without empirical justification. This justification is now available.

---

### Finding 2: Naive debate adds almost nothing beyond majority voting; methodological diversity outperforms persona diversity
**Pipeline layer affected:** L1.5 (Deliberation)
**Evidence quality:** Verified (NeurIPS 2025 Spotlight, ICLR 2025 papers with reproducible code)

"Debate or Vote" (NeurIPS 2025 Spotlight; arXiv:2508.17536) proved majority voting accounts for most performance gains attributed to debate. Self-MoA (ICLR 2025) found a single strong model with self-ensembling outperforms mixed-model ensembles by 6.6%. Debate cannot exceed the accuracy of its strongest participant. The fix comes from three specific architectures:

- DMAD "Breaking Mental Set" (ICLR 2025): assigning agents different *reasoning methods* (CoT, step-back prompting, compositional reasoning) rather than different *roles* produces consistent gains
- A-HMAD: 4-6% accuracy improvement through heterogeneous agent roles with a learned consensus module replacing majority voting; 30%+ reduction in factual errors
- Attention-MoA (January 2026): inter-agent semantic attention + residual synthesis, 91.15% LC Win Rate on AlpacaEval 2.0, small open-source models beating Claude-4.5-Sonnet and GPT-4.1

**What it means for the build:** The current CAPSTONE-PLAN-v2.md describes L1.5 Deliberation with "multi-perspective debate" — but does not specify what makes perspectives genuinely different. This report provides the answer: methodological diversity (different reasoning methods applied to the same evidence), not persona diversity (different roles with the same reasoning approach). The plan needs to be updated: Deliberation agents should be assigned different analytical methodologies, not just different stakeholder perspectives.

---

### Finding 3: LLM judges have a ceiling of 60-68% agreement with domain experts; single-judge evaluation is insufficient for consulting-quality work
**Pipeline layer affected:** L4 (Evaluator)
**Evidence quality:** Verified (multiple peer-reviewed sources, ICLR 2025)

"When AIs Judge AIs" survey quantified the ceiling: SME-LLM judge agreement in expert domains is only 60-68%, far below the 80-90% Spearman correlation on generic tasks. SOS-Bench (ICLR 2025, 152,380 data points across 19 benchmarks) proved LLM judges systematically prefer style over factual accuracy. CALM (ICLR 2025) catalogued 12 distinct bias types including authority bias (inflated credibility from citations regardless of evidence quality) and fallacy-oversight bias.

Three ensemble approaches outperform single judges:
- PoLL (Cohere): panel of 3 smaller models from different families outperforms single GPT-4 judge, 7x cheaper, less intra-model bias
- SE-Jury (ASE 2025): 29.6-140.8% improvement over existing metrics with dynamic team selection at 50% cost reduction
- MAJ-EVAL: Spearman rho of 0.47 vs. 0.15-0.36 for single-judge baselines

**What it means for the build:** The eight-dimension rubric in CAPSTONE-PLAN-v2.md will not achieve reliable evaluation with a single LLM judge. The evaluator design must use at minimum 2-3 judge models from different families, scoring independently. For consulting-quality research, the 60-68% single-judge ceiling means a substantial fraction of good research will be incorrectly rejected and bad research will pass if using a single judge. This is a hard architectural requirement, not an optimization.

---

### Finding 4: Self-improvement saturates after 2-3 iterations without new failure signals
**Pipeline layer affected:** META (Self-Improvement Loop)
**Evidence quality:** Verified (ICLR 2025 Oral, peer-reviewed)

"Mind the Gap" (Song et al., ICLR 2025 Oral; arXiv:2412.02674) provides a fundamental constraint on the Rejection Library: self-improvement saturates after 2-3 rounds without new information. The generation-verification gap (GV-Gap) determines when self-improvement works — it succeeds when verification is easier than generation. Cross-family verification is especially effective. HyperAgents (Meta, March 2026) validated this in practice: paper review scores improved from 0.0 to 0.710 through metacognitive self-modification, but required continued injection of new failure patterns to maintain improvement trajectory.

GEPA (ICLR 2026 Oral) provides the practical solution: prompt evolution outperforming MIPROv2 by 10%+ while using 35x fewer rollouts. RAFT/Reinforce-Rej reveals a critical nuance: GRPO's main advantage comes from discarding prompts with entirely incorrect responses, not from reward normalization. Negative samples should be used selectively.

**What it means for the build:** The Rejection Library's value depends on continuously encountering new failure types. After processing a stable set of research tasks, the same failure modes will recur and the loop will saturate. The META-layer design must include a mechanism to inject new failure signals — either through expansion to new research domains, deliberate adversarial probing, or periodic human review of borderline cases. Saturation at 2-3 rounds without new input is an empirical ceiling, not a design flaw that can be engineered away.

---

### Finding 5: Deep research quality depends on claim-level intermediate representations and DAG structure, not report length
**Pipeline layer affected:** L2 (Content Structuring), L1 (Research Agents)
**Evidence quality:** Verified (Microsoft Research, ICLR 2026; peer-reviewed)

"Characterizing Deep Research" (Java et al., Microsoft Research, ICLR 2026; arXiv:2508.04183) formally established that deep research is a DAG of information synthesis where quality depends on search intensity x reasoning intensity, not report length. F1 scores on LiveDRBench ranged from 0.02 to 0.72. Key finding: systems systematically underutilize backtracking and replanning. The pattern that improves quality: separating claim synthesis from report generation — producing intermediate claim representations before writing. STORM confirms: outline quality strongly predicts final output quality (25% increase in perceived organization).

**What it means for the build:** The L2 Content Structuring layer should not receive raw agent outputs and convert them to structure. It should receive synthesized claims (intermediate representations that have already been verified, triangulated, and structured) and convert claims to narrative. The handoff contract between L1 and L2 should be defined at the claim level, not the findings/notes level. This is a structural change to the pipeline handoffs.

---

## Tool/Framework Verdicts

### Prometheus 2 (Kim et al., EMNLP 2024; GitHub: prometheus-eval/prometheus-eval)
- Open-source evaluator backbone: 7B and 8x7B models, 0.6-0.7 Pearson correlation with GPT-4, 72-85% human agreement on pairwise ranking, custom evaluation rubric support
- **Verdict: INTEGRATE**
- The only open-source evaluator model supporting custom rubrics with documented human agreement rates; use as one judge in the multi-judge ensemble for L4, giving Keystone evaluator independence from closed-source models.

### PoLL (Cohere, 2024; arXiv:2404.18796)
- Panel of three smaller models from different families; outperforms single GPT-4 judge, 7x cheaper, less intra-model bias
- **Verdict: INTEGRATE**
- The architectural pattern (diverse panel) is the requirement; PoLL is the reference implementation. Use this pattern for L4's judge ensemble.

### SE-Jury (ASE 2025; arXiv:2505.20854)
- Dynamic team selection from 5 evaluation strategies, 29.6-140.8% improvement over existing metrics, ~50% cost reduction vs. full ensemble
- **Verdict: LEARN**
- The dynamic selection mechanism (match judge team to task type) is the right design for Keystone's multi-engagement system where different research types need different evaluation emphases.

### Agent-as-a-Judge (Zhuge et al., October 2024; arXiv:2410.10934)
- Agent-evaluators run code, query databases, independently verify results; matches human evaluation reliability
- **Verdict: INTEGRATE**
- For consulting research evaluation, running code to verify quantitative claims and querying sources to verify citations is non-negotiable. The agent-evaluator pattern is required for L4's deterministic checking tier.

### DeepResearchGym (CMU; arXiv:2505.19253; deepresearchgym.ai)
- Reproducible evaluation sandbox, multi-dimensional metrics (coverage, faithfulness, quality), human agreement exceeding inter-annotator agreement
- **Verdict: INTEGRATE**
- Use as the evaluation benchmark framework to calibrate Keystone's L4 rubric against; provides the standardized measurement foundation.

### EvalPlanner (Saha et al.; arXiv:2501.18099)
- Decouples evaluation into planning (generating criteria and rubric steps) then execution; SOTA 93.9 on RewardBench
- **Verdict: LEARN**
- The plan-then-execute evaluation design is more adaptable to different research types than a fixed rubric; consider implementing EvalPlanner's two-stage approach for L4.

### "Trust or Escalate" (ICLR 2025)
- Cascading from weak to strong judges guarantees target human agreement levels while saving up to 78.5% evaluation cost
- **Verdict: INTEGRATE**
- The cost savings (78.5%) while maintaining quality guarantees maps directly to Keystone's need for scalable evaluation at a reasonable cost.

### MAST taxonomy (UC Berkeley, NeurIPS 2025 Spotlight; GitHub: multi-agent-systems-failure-taxonomy/MAST)
- 1,642 execution traces across 7 MAS frameworks, 14 failure modes, coordination breakdowns 36.9% of failures
- **Verdict: LEARN**
- Design all pipeline handoff contracts and verification checks against MAST's 14 failure modes; every identified failure type should have a structural prevention mechanism.

### Attention-MoA (Wen et al., January 2026; arXiv:2601.16596)
- Inter-agent semantic attention + residual synthesis; 91.15% LC Win Rate, small models beating frontier models
- **Verdict: LEARN**
- The semantic attention mechanism between deliberation agents is more sophisticated than the plan's current L1.5 design; study for Deliberation Layer architectural design.

### DMAD / "Breaking Mental Set" (Liu et al., ICLR 2025; GitHub: MraDonkey/DMAD)
- Methodological diversity beats persona diversity in agent debate; assigns different reasoning methods (CoT, step-back, compositional) rather than different roles
- **Verdict: INTEGRATE**
- This is a direct design requirement for L1.5 Deliberation: agents must use different analytical methods, not just represent different stakeholder perspectives.

### HyperAgents (Meta, arXiv:2603.19461; GitHub: facebookresearch/Hyperagents)
- Metacognitive self-modification; improvement mechanism itself evolves; paper review from 0.0 to 0.710; spontaneously developed persistent memory and performance tracking
- **Verdict: LEARN**
- The long-term direction for META-layer evolution; too experimental for Phase 1-2 but should inform the META-layer architecture's extensibility design.

### ADAS (Hu, Lu, Clune; ICLR 2025; arXiv:2408.08435; GitHub: ShengranHu/ADAS)
- Meta-agent iteratively programs new agents, tests them, adds to growing archive; discovered agents transfer across models and domains
- **Verdict: LEARN**
- The growing archive pattern is directly analogous to the Rejection Library; ADAS shows it can extend to discovering new agent architectures, not just constraint accumulation.

### GEPA prompt optimizer (ICLR 2026 Oral; integrated into DSPy v3.1.3)
- 67%->93% on MATH benchmark, outperforms MIPROv2 by 10%+, 35x fewer rollouts than GRPO; MLflow integration
- **Verdict: INTEGRATE**
- Use GEPA as the prompt evolution mechanism for META-layer agent optimization; it is already integrated into DSPy and MLflow, making implementation straightforward.

### Rubrics as Rewards (Scale AI, NeurIPS 2025 Workshop)
- Structured checklists with Essential/Important/Optional/Pitfall categories; 28% improvement on HealthBench
- **Verdict: INTEGRATE**
- Replace the plan's eight-dimension rubric design with rubric-as-structured-checklist: categorize each dimension criterion as Essential/Important/Optional/Pitfall. This design is empirically superior to opaque reward models.

### WebThinker (Li et al., NeurIPS 2025; arXiv:2504.21776; GitHub: RUC-NLPIR/WebThinker)
- Score 8.0 surpassing Gemini Deep Research's 7.9; interleaved think-search-draft rather than rigid pipelines
- **Verdict: LEARN**
- The interleaved think-search-draft pattern enables backtracking and replanning that rigid sequential pipelines prevent; consider for L1 research agent design.

### STORM (Shao et al., NAACL 2024; GitHub: stanford-oval/storm)
- 84.8% citation recall, 85.2% citation precision; reference-pool constraint: gather sources first, write second; 25% increase in perceived organization
- **Verdict: INTEGRATE**
- The reference-pool constraint (gather sources before writing) is directly implementable as a structural enforcement mechanism at the L1→L2 handoff.

---

## Contradictions with CAPSTONE-PLAN-v2.md

### Contradiction 1: The plan describes multi-perspective debate in L1.5 using different analytical lenses; the academic literature shows this design is insufficient

**What the plan says:** "Multi-perspective debate" with "bull/bear/consensus minimum viable deliberation" and steelmanning. The design uses different perspectives (roles) to generate debate.

**What the evidence shows:** Persona diversity (different roles, same reasoning method) produces minimal gains over majority voting alone. Methodological diversity (same role, different reasoning method) is what produces consistent improvements. DMAD, A-HMAD, and Attention-MoA all validate this distinction. MAD cannot exceed the accuracy of its strongest participant regardless of persona diversity.

**Which to follow:** The evidence fundamentally changes the Deliberation design. L1.5 should assign agents different analytical methodologies (quantitative analysis, qualitative framing, adversarial critique, first-principles reasoning, historical analogy) rather than different stakeholder perspectives (bull, bear, neutral). This is a design change, not a contradiction that can be resolved by "both are useful."

---

### Contradiction 2: The plan's Rejection Library is described as improving over time without an explicit saturation mechanism; the literature shows saturation after 2-3 iterations is empirical

**What the plan says:** Section 7 describes the self-improvement loop as compounding with every engagement. Section 11.6 states "the 20th project the system completes will be meaningfully better than the 5th." The implication is monotonic improvement.

**What the evidence shows:** "Mind the Gap" (ICLR 2025 Oral) empirically establishes saturation after 2-3 iterations without new information. The generation-verification gap must be maintained for improvement to continue. Without new failure signals, the loop converges.

**Which to follow:** Both are true at different timescales. The plan's description is accurate for early stages when new failure types are frequently encountered. But the architecture must explicitly plan for saturation: after the initial rapid improvement curve, the META-layer needs mechanisms to inject new failure signals (new research domains, adversarial probing, deliberate hard cases). Add this to the Phase 2 design.

---

### Contradiction 3: The plan caps research agents at 15-50 tasks; the academic literature finds saturation at 3-4 agents per sub-task

**What the plan says:** Section 3.6 describes decomposing the research question into 15-50 discrete research tasks, each assigned to a single agent.

**What the evidence shows:** The Google DeepMind study found agent count saturates at 3-4 agents per task cluster. Beyond this, coordination yields diminishing or negative returns. Performance degrades by 39-70% on sequential reasoning tasks with any multi-agent variant.

**Which to follow:** These are compatible if properly interpreted. 15-50 tasks is the correct decomposition granularity for the total research question. But each individual task should involve at most 3-4 agents. The 15-50 describes research breadth (how many parallel workstreams); the 3-4 limit describes per-workstream depth. The plan should make this distinction explicit.

---

## Cross-Report Flags

**Strongly validates Report D1:** D2's academic evidence that specification flaws cause 36.9% of failures (MAST) and centralized verification reduces error amplification from 17.2x to 4.4x (DeepMind) aligns with D1's practitioner evidence that specification quality determines system quality. Both routes of evidence point to the same conclusion with independent support.

**Extends Report D3:** D2 provides the empirical justification for D3's recommendations. The five-layer citation architecture in D3 is validated by D2's finding that hallucination rates of 18-55% are documented across systems and multi-stage verification frameworks consistently outperform single-pass generation. The claim-level intermediate representation finding from D2 makes D3's citation architecture more precisely specified.

**Flags for synthesis agent:** The finding that self-improvement saturates after 2-3 iterations (D2, ICLR 2025 Oral) creates tension with D1's more optimistic characterization of the autoresearch ratchet loop. D1 presents the ratchet as a reliable improvement mechanism. D2 provides the empirical ceiling: it works for 2-3 rounds then needs new signals. The synthesis plan should incorporate both: the ratchet is real and valuable, but requires active injection of new challenge domains to escape saturation.

**Flag for evaluation design (cross-thread):** D2's finding that single LLM judges achieve only 60-68% expert agreement in specialized domains is the most critical constraint for L4 evaluation design. Any report from another thread recommending a single-model evaluator design should be overridden by this finding. The multi-judge ensemble (2+ model families) is not optional for consulting-quality evaluation.
