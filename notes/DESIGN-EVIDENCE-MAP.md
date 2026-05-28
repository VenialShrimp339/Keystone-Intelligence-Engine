# Design Evidence Map: Research Behind Every Pipeline Decision

Every architectural choice in the Keystone Intelligence Engine traces to a specific empirical finding, benchmark, or production incident. This document maps each design decision to its evidence.

## Key Quantitative Anchors

| Statistic | Source | Design Implication |
|---|---|---|
| 78% vs. 42% | Jones, same model, different harness | Specification quality determines output quality, not model quality |
| 68.8% leakage | AgentLeak benchmark (4,979 traces) | Agent isolation must be architectural; 46.7% from shared memory |
| 96% vs. 13% scoring loss | SOS-Bench (152,380 data points) | LLM judges penalize tone 7x more than factual error |
| 81% vs. 51.2% | Batch 2 Report 06 | Claim selection beats synthesis blending |
| 17.2x error amplification | Google DeepMind (180 configs) | Unstructured multi-agent debate amplifies errors |
| 0.7691 vs. 0.7377 | NeurIPS 2025 Spotlight | Simple voting outperforms debate (martingale proof) |
| 49% improvement | FinMTEB (EMNLP 2025) | Voyage-finance-2 over OpenAI embeddings on financial QA |
| 40% instruction drift | @jordymaui | Prompt-based quality enforcement eventually fails |
| 19 points worse | BCG data via Jones | AI used outside capability frontier degrades outcomes |
| 25% pragmatic inference | CEI benchmark (March 2026) | LLMs fail intent interpretation without structured prompting |
| 39% bandwagon bias | CALM, ICLR 2025 | Claude-3.5 self-assessment bias |
| +28.3% improvement | ADaPT (2025) | Shallow-then-adaptive over static planning |

## Meta-Architecture: DPVI

**Why DPVI?** Four organizations independently converged on Decompose-Parallelize-Verify-Iterate (Jones, "DPVI Pattern," Mar 11, 2026). The convergence validates the pattern as structurally necessary, not clever. BCG's "jagged frontier" finding (19 points worse outside capability frontier) was reframed: the frontier was jagged because DPVI structure was absent.

**Why structure over intent?** Anthropic stress-tested 16 frontier models: every model chose to blackmail executives and leak blueprints even when explicitly instructed not to. @jordymaui measured ~40% instruction drift. Any system depending on agents *choosing* to comply will fail.

**Why evaluation > generation?** Carlini ($20K C compiler, 16 agents): "The test harness is more important than the agent prompt." Anthropic Harness Design: same finding. Jones: 78% vs 42% on the same model. The 19% paradox (Jones, Feb 18, 2026): developers were 19% slower with AI but believed 20% faster — subjective quality assessment is unreliable.

## L0 Specification Engine

**Why MECE issue trees?** Jones "Articulation Problem" (Feb 10, 2026): "The bottleneck isn't AI capability — it's specification quality." Jones "4:1 Ratio" (Mar 24, 2026): "Four of five agent deployment problems are engineering. The fifth — specification — is where all the value lives."

**Why 3 heterogeneous lenses?** DMAD, ICLR 2025: methodological diversity outperforms persona diversity. Reports 03 and 10 (peer-reviewed 2025): heterogeneous lenses produce 4-6% accuracy gains and 30% fewer factual errors.

**Why Day-1 Hypothesis?** Prevents AutoGPT infinite-loop failure mode. Anchors to falsifiable claim. Research starts at 70/30 exploration/exploitation, shifts to 20/80 as knowledge accumulates.

**Why anti-confirmatory framing?** Jones "Agent Schemes" (Mar 9, 2026): agents cherry-pick with "the grinding indifference of water finding the fastest path downhill." Structural constraint, not guideline.

**Why 5-step intent clarification?** CEI benchmark (March 2026): LLMs score 25% on pragmatic inference without structured prompting. Klarna: $60M brand destruction from optimizing stated goal instead of actual need.

**Why tasks as JSON?** Anthropic "Effective Harnesses": models are significantly less likely to corrupt JSON vs Markdown.

**Why DAG dependencies?** Microsoft Research, ICLR 2026: research quality depends on DAG structure, not report length.

## L1 Research Agents

**Why strict isolation?** AgentLeak benchmark (4,979 traces): 68.8% inter-agent data leakage, 46.7% from shared memory. No framework intercepts at infrastructure level. Filesystem isolation is non-negotiable.

**Why 3-5 tools per agent?** Anthropic production: "A model loaded with 50 tools performs worse than specialized agents with 5 focused tools."

**Why citations as required fields?** @jordymaui principle: don't tell agents to cite — make it structurally impossible not to. Required Pydantic field, not prompt instruction.

**Why artifact bypass?** Factory.ai: 37% information retention failure when full artifacts flow through pipeline stages. Send structured summary through pipeline, write full artifact to disk.

**Why JIT context loading?** Anthropic "Context Engineering": context has diminishing marginal returns. Loading an entire 10-K is worse than loading three relevant sections.

## Citation Processor

**Why discrete pipeline stage?** Anthropic production CitationAgent: 90.2% improvement over single-agent baseline. Deloitte incidents: AU$440K and CA$1.6M damages from fabricated citations surviving senior review.

**Why URL liveness?** Deloitte failure mode: citations that exist in form but don't resolve to real content.

## L1.5 Deliberation

**Why NOT debate?** NeurIPS 2025 Spotlight: formal proof that multi-agent debate is a martingale — additional rounds cannot improve expected accuracy. Voting (0.7691) outperformed best debate variant (0.7377). Wu et al.: majority pressure suppresses correction below 5%. DeepMind: unstructured networks amplify errors 17.2x.

**Why methodological diversity?** DMAD, ICLR 2025: different analytical methods produce genuinely independent assessments. Different personas using the same method produce correlated noise.

**Why claim selection, not synthesis?** 81% vs 51.2% win rate. Synthesis "introduces incoherence, conflicting perspectives, and diluted arguments."

**Why 5-tier confidence?** DiscoUQ (AUROC 0.802): the 50-60% range is exactly where simple voting fails and computational confidence features help most.

## L4 Evaluation

**Why 5-layer stack?** SOS-Bench (152K data points): single LLM judges penalize sarcasm 96% but factual errors only 13%. Style overwhelms substance by 7x. Held across all four judge models tested.

**Why geometric mean?** Stanford HELM, MQM, AdaRubric independently converged. Under arithmetic mean, high coherence can mask failing honesty. Under geometric mean, any near-zero dimension drives composite to near-zero.

**Why separate prompts per dimension?** SOS-Bench: style scores infect substance scores within a single prompt (cross-contamination).

**Why cross-model ensemble?** CALM, ICLR 2025: self-enhancement bias correlates linearly with self-recognition. Claude-3.5: 39% bandwagon susceptibility. ChatGPT: 43.4% positional inconsistency, 33.8% judgment reversal from fake citations.

**Why dissenter veto?** Same martingale logic as deliberation: majority consensus in evaluation can be achieved without being correct.

**Why these weights?** SOS-Bench: LLM judges overweight style/completeness, underweight accuracy/substance. Weights deliberately shifted toward LLM weak spots (Quantitative Rigor 15%, Actionability 15%) and away from natural strengths (Narrative Coherence 8%).

**Why binary citation gate?** Deloitte: AU$440K damages. 36.2% DOI error rate documented. Partial credit for citations is dangerous.

**Why process trajectory?** Agent-as-a-Judge (arXiv:2410.10934): ~90% human agreement vs ~70% for static LLM-as-Judge. METR: 50-67% of AI PRs passing automated tests get rejected by humans.

**Why 0.80+ Spearman target?** Anthropic "Demystifying Evals" (Jan 2026): below 0.80, automated scores are noise.
