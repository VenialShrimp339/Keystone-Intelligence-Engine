# Building MECE issue trees into AI: a specification engine design guide

**No production AI system today constructs consulting-quality MECE issue trees before executing research — making this a genuine greenfield engineering challenge.** The academic foundations exist: tree-of-thought reasoning, DAG-based task execution, and multi-agent deliberation all provide proven building blocks. But nobody has assembled them into a system that replicates how a McKinsey engagement manager structures a problem before deploying analysts. This report synthesizes findings across 60+ papers, frameworks, and production systems (2023–2026) to provide concrete architectural guidance for building this capability into the Keystone Intelligence Engine's Specification Engine.

The significance is substantial. Consulting firms spend 20–30% of engagement time on problem structuring — the step that most determines research quality. Encoding this discipline into an AI orchestrator could eliminate the primary failure mode of agent systems: executing confidently on poorly defined problems. The research reveals both encouraging capabilities and critical limitations that should shape the architecture.

---

## The decomposition landscape: strong foundations, missing MECE layer

Academic research on structured LLM reasoning has advanced rapidly since 2023. **Tree of Thoughts** (Yao et al., NeurIPS 2023) demonstrated that explicit tree-structured decomposition boosts GPT-4's Game of 24 performance from 4% to 74%. **Graph of Thoughts** (Besta et al., AAAI 2024) extended this to arbitrary graph structures, achieving 62% quality improvement over ToT while cutting costs by 31%. **ADAPT** (NAACL 2024) introduced recursive decomposition that dynamically adjusts depth based on problem complexity — decomposing further only when needed. **GoalAct** (2025) added continuously updated global planning with hierarchical skill-based execution, achieving 12% improvement on LegalAgentBench.

Production agent frameworks have converged on a **Plan-then-Execute (P-t-E) pattern** as the dominant architecture. LangGraph implements this through three variants: basic plan-and-execute, ReWOO (variable passing between tasks), and LLMCompiler (DAG-based parallel execution). CrewAI uses role-based hierarchical delegation. Microsoft's Semantic Kernel experimented with multiple planner types before concluding that modern LLMs' native function-calling capabilities often make explicit planners unnecessary for simpler tasks — a finding worth noting, though consulting-grade decomposition is categorically more complex than tool selection.

The critical gap is that **none of these systems enforce or even check MECE properties**. ToT and GoT evaluate branches by solution quality, not structural completeness or mutual exclusivity. No academic paper defines computable metrics for MECE-ness. No consulting firm has published how they encode problem-structuring methodology into AI — McKinsey's Lilli, BCG's GENE, and Bain's Sage all focus on knowledge retrieval and synthesis, not problem structuring. The closest production systems are AI case interview tools (Soreno, CasewithAI, MECE Academy) that use LLM-as-judge to evaluate candidate frameworks against consulting rubrics, but these are evaluators, not generators. [Verified/Credible]

---

## Architectural blueprint: encoding consulting methodology

The consulting problem-structuring process maps to a specific AI pipeline. A consultant takes an ambiguous question, generates hypotheses about root causes or key dimensions, decomposes into MECE branches, assesses which branches have highest expected value for investigation, then assigns analysts to each branch. This translates to five engineering components.

**Component 1: Structured generation with Plan-and-Solve prompting.** The Plan-and-Solve paradigm (Wang et al., ACL 2023) — instructing the LLM to "first understand the problem and devise a plan, then carry out the plan" — consistently outperforms zero-shot chain-of-thought across all tested benchmarks and is directly analogous to the consulting "structure before solve" discipline. For the Specification Engine, this means the initial prompt should explicitly separate the structuring phase from any analysis. The Skeleton-of-Thought technique (Ning et al., ICLR 2024) provides an additional pattern: generate a **3–10 point skeleton first**, then expand each point. This achieved equal or better quality to unstructured generation in ~60% of cases while enabling parallel expansion — directly useful for generating issue tree branches before populating them.

**Component 2: Few-shot MECE exemplars.** Empirical evidence strongly supports using **2–3 high-quality examples** of MECE decompositions in prompts. Bug report decomposition studies found that few-shot examples improved LLM decomposition accuracy by 140–163% over zero-shot. However, quality matters far more than quantity: noisy examples degrade performance below zero-shot baselines (Cleanlab study), and "over-prompting" with excessive examples can paradoxically reduce quality. The recommendation is to curate a library of **gold-standard issue trees** across common consulting problem types (profitability, market entry, M&A, operations, growth strategy) and select the most structurally relevant example at inference time.

**Component 3: Structured JSON output with reasoning-first schema.** A critical finding from Tam et al. (EMNLP 2024) and Park et al. (NeurIPS 2024): **constrained JSON decoding degrades reasoning quality** when answer fields precede reasoning fields, because the model is forced to commit before thinking. The Pydantic schema for issue trees must place `reasoning` and `rationale` fields before `branches` and `priority` fields. The SLOT framework (EMNLP 2025) offers an alternative: generate the tree in natural language first, then use a lightweight model to convert to structured JSON, decoupling formatting from reasoning.

**Component 4: Self-evaluation loop for MECE verification.** Following the ToT/GoT pattern of LLM self-evaluation, the Specification Engine should include a verification step where the model (or a separate evaluator model) explicitly checks: (a) Do any sibling branches overlap in scope? (b) Are there significant aspects of the root question not covered? (c) Is each leaf node specific enough to generate a concrete research task? This maps to the **maker-checker pattern** documented in Microsoft's Azure AI architecture guidance. Using Claude Opus 4.6 as the evaluator for trees generated by Sonnet 4.6 would provide the model-capability asymmetry that makes maker-checker effective.

**Component 5: Hypothesis-driven framing.** The LINA framework (2024) demonstrates that hypothesis-deductive reasoning — generate hypothesis, test, refine — improves logical reasoning by 24% over baselines. For consulting-style trees, each branch should be framed as a testable hypothesis ("Revenue decline is driven by pricing pressure in the enterprise segment") rather than a topic label ("Enterprise pricing"), because hypothesis framing makes the research task and success criteria explicit. [Verified/Credible]

---

## Multi-agent generation: independent parallel analysis wins, but with caveats

The evidence on multi-agent vs. single-agent decomposition is nuanced and directly relevant to the Keystone system's existing independent parallel analysis pattern.

**The headline finding**: a NeurIPS 2025 Spotlight paper (Choi et al.) demonstrated that **simple majority voting accounts for most observed gains in multi-agent debate** — the communication/debate phase adds marginal value over independent parallel generation followed by selection. This aligns with the Keystone system's existing architecture. An ICLR 2025 analysis confirmed that current multi-agent debate methods "fail to consistently outperform simpler single-agent strategies" with homogeneous agents.

However, three nuances matter. First, **heterogeneous agents with distinct roles provide 4–6% absolute accuracy gains** over standard debate and reduce factual errors by 30% (Zhou & Chen, A-HMAD, 2025). For issue tree generation, this suggests assigning different "consulting lenses" — one agent structures through a financial lens, another through an operational lens, a third through a market/competitive lens — rather than having identical agents attempt the same task. Second, the **"lazy agent" problem** (Zhang et al., 2025) means that in multi-agent systems, one agent tends to dominate while others contribute minimally. The independent parallel analysis pattern avoids this by design, since agents never see each other's work. Third, **compute-optimal test-time scaling** (Snell et al., Google DeepMind 2024) found that the benefit of additional samples depends on problem difficulty: easy problems benefit more from iterative revision of a single solution, while **hard problems benefit from broader parallel sampling**. Since consulting problem structuring is inherently a "hard" creative task, parallel generation is the right default.

**Recommended architecture**: Generate **3–5 independent issue trees** using Claude Opus 4.6 with varied system prompts (different consulting lenses or framework preferences). Use a synthesis step — not simple majority voting, since trees are structures not discrete answers — where an evaluator model selects the best tree or merges the strongest branches from multiple trees. The MAKER framework's approach of extreme decomposition combined with multi-agent voting achieved over 1 million LLM steps with zero errors, suggesting that the overhead of parallel generation is justified for high-stakes structuring decisions. The diminishing returns finding from Google DeepMind (2025) — **performance plateaus around ~4 agents** — provides a practical upper bound. [Verified]

---

## Branch prioritization: moderate AI capability, multi-signal approach required

Can an AI system reliably decide which branches of an issue tree to investigate first? The evidence says **yes, with guardrails**.

Anthropic's foundational paper "Language Models (Mostly) Know What They Know" (Kadavath et al., 2022) established that larger models are well-calibrated on predicting whether they can answer questions correctly. The P(IK) — "probability I know" — metric shows that models can assess their own knowledge boundaries, and this capability scales with model size. More recently, Harvard's Kempner Institute demonstrated that **epistemic uncertainty is natively encoded in LLM representations** and can be extracted via linear probes that transfer across domains, achieving AUC ~0.70 for distinguishing "I don't know this but could learn it" from "this is inherently uncertain."

The critical limitation is **systematic overconfidence**. Griot et al. (Nature Communications, 2025) found that LLMs provide confident answers even when correct options are absent — "deceptive expertise" — particularly in specialized domains. Steyvers & Peters (2025) confirmed that explicit confidence reporting from LLMs is poorly calibrated, lagging behind what can be inferred from implicit signals like token probabilities. Fine-tuning specifically for calibration produces statistically significant improvements (Steyvers et al., 2025), but remains imperfect.

For branch prioritization, the practical approach should combine multiple signals rather than relying on any single confidence measure:

- **Sampling-based consistency**: Generate the issue tree multiple times and measure which branches appear consistently (high consistency = high confidence in relevance). This leverages self-consistency (Wang et al., 2022) without requiring explicit confidence judgments.
- **Feasibility estimation via self-knowledge**: For each leaf node, prompt the model to assess whether reliable data sources exist and whether the question is answerable with available tools. Frame this as a concrete assessment ("What specific data sources would answer this?") rather than an abstract confidence question.
- **Impact estimation via structured rubric**: Provide explicit prioritization criteria matching consulting methodology — impact on the client's decision, time sensitivity, interdependency with other branches — and have the model score each branch against each criterion separately rather than providing a holistic priority ranking.
- **Epistemic uncertainty probing**: For frontier models that expose logprobs, use token-level uncertainty as a complementary signal. High uncertainty in the model's own prioritization suggests the branch ordering is less reliable.

The vulnerability triage literature (2025) demonstrates that LLMs guided by organizational context achieve **F1 scores of 0.68–0.79** on prioritization tasks when given proper framing — adequate for a first-pass prioritization that can be refined as research progresses. [Verified/Credible]

---

## From tree to tasks: DAG-based mapping with completeness checking

The issue tree's leaf nodes must map to executable research tasks. **LLMCompiler** (Kim et al., 2023) provides the reference architecture: a Function Calling Planner generates a DAG of tasks with inter-dependencies, a Task Fetching Unit dispatches tasks in parallel as dependencies resolve, and an Executor handles each task asynchronously. This achieved **3.6x speedup** and **4.65x cost reduction** versus ReAct-style sequential execution, and is implemented as an official LangGraph tutorial.

Three mapping patterns apply. **One-to-one mapping** (each leaf = one research task) is the default for well-decomposed trees. **One-to-many mapping** occurs when a leaf requires multiple data sources or methodologies — e.g., "assess market size" might require a top-down estimate from industry reports and a bottom-up estimate from customer data. **Many-to-one mapping** occurs when a single data source answers multiple branches — e.g., a company's 10-K filing might inform both revenue analysis and cost structure branches. The DAG representation naturally handles all three patterns through dependency edges.

For completeness verification — ensuring no orphan branches and no duplicate tasks — the field primarily relies on three mechanisms. **DAG-Plan** (Gao et al., 2024) includes explicit completeness checking: the system validates graph completeness and prompts the LLM to regenerate incomplete portions. **Sda-Planner** (2025) uses a State-Dependency Graph to model preconditions and effects, enabling formal coverage validation. The **maker-checker pattern** (Microsoft) provides the simplest implementation: after task generation, a second LLM pass reviews the mapping against the issue tree and flags any unmapped leaves or redundant tasks.

For the Keystone system using PydanticAI, the implementation path is straightforward. PydanticAI's structured output capabilities (Pydantic models) can enforce that every issue tree leaf has at least one associated task via schema validation. The **pydantic-deep** framework (Vstorm, 2026) adds task tracking with subtasks, dependencies, cycle detection, and PostgreSQL storage — providing the persistent state management needed for the task DAG. PydanticAI's graph support enables defining the execution workflow with type-safe state transitions, and its agent delegation pattern allows the orchestrator to dispatch research tasks to specialized worker agents. The key architectural decision is to **validate the tree-to-task mapping as a discrete step** before execution begins, rather than generating tasks on-the-fly during execution. [Verified/Credible]

---

## Living trees: incremental updates with hard boundaries

Research rarely proceeds as planned. New findings invalidate assumptions, reveal unexpected branches, or make some investigations unnecessary. The issue tree must be a living document — but with disciplined update rules to prevent scope creep and infinite replanning loops.

The consensus from the literature is clear: **incremental update, not full rebuild**. Sda-Planner's Adaptive Action SubTree Generation locally reconstructs only the affected portion of a plan when errors occur. AINav (2025) introduces an elegant **two-agent pattern**: an Advisor agent determines *when* to replan (triggered by failure, new discoveries, or periodic revaluation), while an Arborist agent determines *how* to modify the tree structure. This separation of "should we change the plan?" from "what should the new plan be?" prevents unnecessary replanning while ensuring genuine discoveries are incorporated.

KGLAMP (2025) demonstrates the most sophisticated approach: maintaining a **persistent, dynamically updated knowledge graph** that integrates new observations, updates inconsistencies, and triggers replanning only when changes propagate to affect pending tasks. This achieved 64% task completion under partial observability versus 12% for the best competitor — a 5x improvement from dynamic planning alone.

Practical guardrails are essential. Production experience from multiple agent systems converges on these rules:

- **Hard ceiling of ~3 replanning cycles** per workflow to prevent infinite loops (Ranjan Kumar, practitioner analysis)
- **Completed tasks are immutable** — only pending tasks may be modified during replanning
- **Explicit termination tools** rather than letting the LLM decide "done" via natural language (TraycerAI production experience)
- **Two-threshold termination**: a warning threshold ("wrap up research") followed by a hard threshold ("deliver with current findings")
- **Convergence detection**: if newly generated tasks duplicate existing ones, the system has exhausted productive directions (BabyAGI pattern)
- **Cost/token budgets** with automatic enforcement (pydantic-deep's CostTracking capability)

For the Keystone system, the ADaPT framework (2024) offers a particularly relevant pattern: decompose tasks adaptively, only creating subtasks when the executor fails to handle a leaf directly. This achieved **+28.3% over standard plan-and-execute** on ALFWorld while being more cost-effective. Applied to issue trees, this means the initial decomposition can be relatively shallow (2–3 levels), with deeper decomposition triggered only when a research agent reports that a branch is too complex to investigate directly. [Verified/Credible]

---

## Evaluating tree quality: a hybrid metric framework

No formal MECE evaluation metrics exist in the literature — this is a genuine research gap. However, combining consulting interview rubrics with LLM-as-judge frameworks yields a practical evaluation system.

Consulting firms evaluate issue tree quality across **five dimensions**: mutual exclusivity (no overlap between sibling branches), collective exhaustiveness (all significant aspects covered), tailoring (customized to the specific problem, not generic), actionability (each leaf maps to a concrete investigation), and depth appropriateness (right level of granularity). These are typically scored on a 1–5 scale, with structure receiving approximately **25% weight** in McKinsey's evaluation rubric.

The **G-Eval framework** (Liu et al., EMNLP 2023) provides the implementation pattern: use auto-generated chain-of-thought evaluation steps, apply them via LLM-as-judge, and extract probability-weighted scores. GPT-4 as judge achieves 85% agreement with human evaluators (excluding ties), exceeding human-human agreement of 81% (Zheng et al., 2023). For MECE evaluation specifically, the system should decompose assessment into independent sub-evaluations:

- **Mutual exclusivity check**: For each pair of sibling branches, ask: "Do these branches address overlapping concerns? Could a single finding be relevant to both?" Supplement with programmatic semantic similarity scoring — high cosine similarity between branch descriptions suggests overlap.
- **Collective exhaustiveness check**: "Given the root question, what significant aspects are NOT covered by any branch?" This requires domain reasoning and is best handled by LLM-as-judge with relevant context.
- **Actionability check**: "For each leaf, can you specify a concrete data source, analysis method, or expert to consult?" Binary assessment per leaf, programmatically aggregatable.
- **Depth appropriateness check**: Programmatic heuristics (tree depth 2–4 for most consulting problems, leaf count 8–20) combined with LLM assessment of whether leaves are at the right granularity.
- **Tailoring check**: "Is this framework specific to the stated problem, or could it apply to any similar question?" This catches the common failure of generic frameworks.

**DeepEval's PlanQualityMetric** provides the closest existing implementation — evaluating whether plans are "logical, complete, and efficient" via LLM-as-judge. For the Keystone system, extending this with MECE-specific sub-criteria is the most practical path. The evaluation should run after each tree generation, with a minimum quality threshold that triggers regeneration. Using the independent parallel analysis pattern, **evaluate all candidate trees on the same rubric and select the highest-scoring one** before proceeding to task mapping. [Verified/Credible]

---

## Conclusion: a clear but unbuilt path

The Keystone Intelligence Engine's Specification Engine sits at the intersection of well-researched capabilities that nobody has yet combined. The academic foundations — structured decomposition via Plan-and-Solve, parallel generation via best-of-N sampling, DAG-based task execution via LLMCompiler, incremental replanning via Sda-Planner/ADaPT, and evaluation via G-Eval — are each individually proven. The missing piece is the **MECE constraint layer**: explicit enforcement and verification of mutual exclusivity and collective exhaustiveness, drawing from consulting methodology rather than computer science.

Three architectural decisions emerge as highest-leverage. First, **generate 3–5 independent issue trees with heterogeneous consulting lenses**, then select or synthesize the best — this exploits the proven benefit of parallel sampling while avoiding the marginal returns of multi-agent debate. Second, **treat MECE verification as a discrete pipeline stage** using a separate evaluator model (Opus 4.6), not as an afterthought — the maker-checker pattern with model-capability asymmetry is the most reliable quality gate. Third, **start shallow and decompose adaptively** following ADaPT's pattern, rather than attempting deep upfront decomposition — this is both more cost-effective and more robust to the inevitable mid-research discoveries that require tree updates.

The biggest open risk is branch prioritization reliability. LLMs are systematically overconfident about their knowledge boundaries, and no amount of prompting eliminates this bias entirely. The multi-signal approach (sampling consistency + feasibility assessment + structured rubric scoring) provides adequate accuracy for a first-pass prioritization, but the system should be designed to **reprioritize after each research cycle** as actual findings update the model's understanding of which branches matter most. The two-threshold termination pattern and hard replanning limits prevent this iterative process from becoming unbounded.

This is buildable today with Claude API, PydanticAI, and pydantic-deep as the infrastructure layer. The novel engineering work is in the MECE constraint system, the multi-lens tree generation pipeline, and the hybrid evaluation framework — none of which require fundamental research breakthroughs, only careful implementation of patterns proven in adjacent domains.