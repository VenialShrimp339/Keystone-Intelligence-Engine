# Designing the specification layer that IS the system

The Specification Engine should implement a **10-step pipeline** — not the original 7 — with problem framing and hypothesis generation before decomposition, a validation gate after it, and a feedback loop connecting execution back to planning. Every major consulting methodology (McKinsey, BCG, Bain) and every production AI research system (Claude, Perplexity, OpenAI) converges on the same architectural insight: the planning phase must separate problem definition from problem structuring, and must generate evaluation criteria simultaneously with the research plan itself. This report synthesizes findings across 7 research domains — existing AI planning systems, intent engineering, pipeline architecture, engagement-type adaptation, iterative planning, knowledge management, and multi-agent deliberation — into actionable architectural decisions for the Keystone Intelligence Engine's highest-leverage component.

The research draws on **primary sources** from Anthropic's engineering blog, Stanford's STORM paper, the AOP framework (ICLR 2025), the Mixture-of-Agents paper, McKinsey's published methodology, the RSA framework from cognitive science, and production systems including Harvey AI, Google's AMIE, and Sakana AI's AI Scientist-v2 (Nature 2026). Each finding carries a confidence tag and each recommendation carries an ADOPT/ADAPT/SKIP/INVESTIGATE verdict.

---

## 1. How production AI research planners actually work

The most important architectural pattern across every production research system is the **orchestrator-worker model with iterative plan revision**. Claude's deep research uses a Lead Researcher (Opus) that analyzes the query, records a plan to persistent memory, spawns parallel subagents (Sonnet), synthesizes results, and dynamically creates additional subagents if gaps remain. Anthropic's engineering blog confirms that prompt engineering of the decomposition step was their "primary lever for improving behaviors" and that their multi-agent system outperformed single-agent by **90.2%** on internal evaluations. [Verified — Anthropic engineering blog, June 2025]

Perplexity Deep Research operates a retrieval-reasoning-refinement cycle: it decomposes queries into a **dynamic research tree**, executes 20–50 targeted sub-queries across 3–5 sequential passes, and maintains context between sub-queries to avoid redundant searches. It scored highest across all 10 domains on the DRACO benchmark with the lowest latency (459.6 seconds vs. 592–1808 seconds for competitors). [Verified — Perplexity research blog]

Stanford's STORM introduced **perspective-guided question generation** — rather than directly decomposing a topic, STORM discovers relevant perspectives by surveying similar articles, then simulates conversations between a writer and topic expert to generate questions iteratively. This produced a 25% improvement in outline organization and 10% in breadth versus standard RAG baselines. The core insight is that automating research requires automating the question-asking process, not just the answer-finding. [Verified — Stanford NLP paper, arXiv 2402.14207]

OpenAI's deep research uses a specialized o3 model trained with **end-to-end reinforcement learning** in simulated research environments. The model learned to plan multi-step search trajectories, backtrack when paths prove unfruitful, and pivot strategies based on new information — capabilities that emerged from RL training rather than explicit programming. It generates a proposed research plan for user review before committing to execution. [Verified — OpenAI system card]

The cross-cutting patterns that matter most for the Specification Engine:

- **Query fan-out** (1 query → 8–12 sub-queries) is universal across Perplexity, Google, and ChatGPT. [Credible]
- **Plan-for-review** (generate plan → present to user → execute) is used by Gemini and OpenAI, and should be adopted for the human review gate. [Verified]
- **Hybrid static/dynamic workflows** outperform pure dynamic ones. A HuggingFace survey identifies this as the fundamental design choice: predefined research phases with dynamic LLM planning within each phase. [Credible — HuggingFace survey, Sep 2025]
- **Context window management** is the critical bottleneck. Claude's system saves plans to persistent memory; subagents operate with independent context windows. Multi-agent systems use ~**15× more tokens** than chat interactions. [Verified]
- AutoGPT's failures are equally instructive: infinite looping, context loss on long tasks, hallucinated task completion, and cascading errors from early mistakes. These are the precise failure modes the Specification Engine must guard against. [Credible]

**Verdict: ADOPT** the orchestrator-worker pattern with iterative plan revision. **ADAPT** STORM's perspective-guided question generation for the issue tree construction phase — discover relevant analytical perspectives before decomposing.

---

## 2. Intent engineering turns vague requests into decision-ready research

The Specification Engine's core challenge is inferring not just what to research but **what decision the research will inform**. This is "Level 3: Intent Engineering," and it has deep roots in both academic pragmatics and production AI systems.

### The decision-first prompting pattern

The most immediately implementable technique is **Decision-First Chain-of-Thought prompting** — a structured reasoning sequence that forces the LLM to identify the decision context before generating any research plan. The recommended five-step chain:

1. What decision or action will this research inform?
2. What is the client's current default position (their implicit hypothesis)?
3. What evidence would change their mind (falsification criteria)?
4. What evidence would confirm their direction (validation criteria)?
5. Therefore, what specific research questions must be answered?

This maps directly to **McKinsey's Problem Statement Worksheet**, which requires seven components: context/perspective of decision-maker, key question, scope/constraints, stakeholders, key sources of insight, risks/opportunities, and deliverables. The consulting methodology has been encoding intent engineering for decades — the AI system should formalize it. [Verified — McKinsey methodology, extensively documented]

### Pragmatic inference and the RSA framework

The **Rational Speech Act (RSA) framework** from cognitive science (Frank & Goodman, 2012; published in *Science*) provides the theoretical foundation. RSA models communication as recursive Bayesian reasoning: a pragmatic listener reasons "Why did the speaker choose THIS utterance rather than alternatives?" When a client says "research the competitive landscape in enterprise SaaS," RSA reasoning implies they're facing a competitive threat — they could have asked for market sizing or customer analysis but chose competitive positioning. The Specification Engine should implement **explicit Gricean inference rules**: if the client provided detailed context on competitors but not customers, they probably already understand customers. If they mention both "market entry" and "regulatory risk," these are connected in their mental model. [Verified — foundational cognitive science, actively extended through 2025]

However, LLMs remain weak at pragmatic inference. The CEI benchmark shows LLMs achieve only **25% accuracy on pragmatic emotion inference** versus 54% human majority agreement, and neither CoT nor few-shot prompting meaningfully improves performance. This means the Specification Engine cannot rely on implicit pragmatic reasoning — it must make inference explicit through structured prompting and disambiguation. [Verified — arXiv 2603.09993]

### Production systems that do intent engineering well

**Harvey AI** (legal research) processes between **30 and 1,500 model calls per query**, indicating multi-step intent decomposition. It achieves 94.8% accuracy on document Q&A through custom fine-tuning on legal processes. Google's **AMIE** (medical diagnosis, published in *Nature* 2025) uses a diagnostic interview pattern — taking a systematic clinical history through targeted questions to narrow a differential diagnosis. AMIE exceeded primary care physicians across most evaluation dimensions in randomized trials.

The medical diagnostic pattern maps directly to engagement scoping:

- Chief complaint → Engagement description
- History of present illness → Context questions about the decision timeline and triggers
- Differential diagnosis → Multiple possible research directions
- Targeted questions to narrow → "What would change your mind?" questions
- Assessment & plan → Structured research plan

**SAGE-Agent** (OpenReview, 2025) provides the most technically actionable approach: it uses **Expected Value of Perfect Information (EVPI)** to quantify the disambiguation value of each potential clarifying question, achieving 7–39% higher coverage while reducing clarification questions by 1.5–2.7×. The **TiCoder pattern** (Lahiri et al., 2022) generates multiple candidate outputs, identifies where they diverge, and presents those divergence points as clarifying questions — improving correctness from 40% to 84%. [Credible — active research]

**Verdict: ADOPT** Decision-First CoT prompting and the McKinsey Problem Statement schema as the first pipeline step. **ADOPT** the TiCoder divergence-detection pattern: generate 2–3 candidate research plans, identify where they disagree, and surface those as clarifying questions. **ADAPT** EVPI-based question selection for the human review gate. **INVESTIGATE** fine-grained Gricean inference rules as a future enhancement.

---

## 3. The pipeline needs four missing steps

The proposed pipeline (`engagement description → issue tree decomposition → priority assignment → agent configuration → task generation → human review → execution`) is directionally correct but **missing critical steps** that every consulting methodology and production AI system requires.

### The recommended 10-step pipeline

```
 1. PROBLEM FRAMING & CLASSIFICATION (NEW)
    Engagement type classification → problem statement generation → ambiguity surfacing

 2. HYPOTHESIS GENERATION (NEW)
    Generate 2–3 initial hypotheses; each shapes a different decomposition strategy

 3. ISSUE TREE DECOMPOSITION (existing, enhanced)
    Multiple agents construct trees driven by hypotheses; co-generate evaluation
    criteria for each branch simultaneously

 4. DECOMPOSITION VALIDATION (NEW)
    Solvability: Can agents research each leaf? Completeness: All aspects covered?
    Non-redundancy: No duplicate branches?

 5. PRIORITY ASSIGNMENT (existing)
    Impact × feasibility matrix with uncertainty weighting

 6. DYNAMIC AGENT CONFIGURATION (existing)

 7. TASK GENERATION (existing, enhanced with success criteria per task)

 8. HUMAN REVIEW GATE (existing)

 9. RESEARCH EXECUTION (existing)

10. FEEDBACK LOOP (NEW)
    Research findings → refine issue tree → reprioritize → adjust tasks
```

**Step 1 — Problem Framing** is the highest-impact addition. McKinsey's Hugo Sarrazin (senior partner): "It is surprising how often people jump past this step and make a bunch of assumptions." Every major framework treats problem definition as distinct from structuring. The engine should classify the engagement into one of five types (see Section 4) and produce a structured problem statement object before any decomposition occurs. [Verified — McKinsey, BCG, Bain all separate these steps]

**Step 2 — Hypothesis Generation** follows BCG's core methodology: form an initial hypothesis ("answer-first thinking"), then build the issue tree to test it. This is fundamentally different from decomposing first and prioritizing after — the hypothesis shapes which branches matter. For the auto shop expansion example, competing hypotheses might be: "Expansion should target underserved markets with high vehicle density" vs. "Expansion should follow a hub-and-spoke model from existing locations" vs. "The client should franchise rather than expand owned locations." Each produces a different tree. [Verified — BCG methodology]

**Step 4 — Decomposition Validation** implements the AOP framework's three principles (ICLR 2025): solvability (each sub-task resolvable by an available agent), completeness (covers all necessary aspects), and non-redundancy (no duplicate sub-tasks). The paper finds that **more than 15% of queries still exhibit decomposition issues even with detailed instructions** — a separate validation step is necessary, not just better prompting. [Verified — arXiv 2410.02189]

**Step 10 — Feedback Loop** is the most universally validated missing piece. McKinsey requires continuous synthesis throughout engagements. BCG explicitly iterates: "If hypothesis disproven, reformulate and repeat from step 1." Anthropic's system dynamically spawns additional subagents based on synthesized results. The VeriMAP framework (arXiv 2510.17109) generates planner-specified verification functions that trigger replanning when subtasks fail. [Verified — all sources converge]

**Verdict: ADOPT** all four additions. The evaluation criteria co-generation (VeriMAP pattern) and feedback loop are particularly high-leverage and low-cost to implement.

---

## 4. Five engagement types require five different pipelines

The Specification Engine should **classify incoming queries into engagement types and route to different pipeline configurations** — a pattern validated by Adaptive-RAG (KAIST), FAIR-RAG's four-tier routing, and Perplexity's hybrid model selection. The most effective AI systems use upfront complexity classification. [Verified]

### The engagement type taxonomy

| Type | Example | Uncertainty | Primary artifact | Pipeline mode |
|------|---------|-------------|-----------------|---------------|
| **SIZING** | "Size the NA EV sensor market" | Low | Calculation tree | Deterministic: data gathering → calculation → validation |
| **DIAGNOSTIC** | "Why is EMEA revenue declining?" | Medium-Low | Issue tree + hypothesis list | Hypothesis-test loop |
| **EVALUATIVE** | "Should we acquire Company X?" | Medium | Due diligence framework + scorecard | Parallel workstreams with known framework |
| **EXPLORATORY** | "What should we know about X?" | High | Exploration map → emerging issue tree | Wide scan → progressive narrowing |
| **STRATEGIC** | "What's our optimal Japan entry strategy?" | Medium-High | Decision tree + scenario matrix | Scenario generation → evaluation |

Classification uses five signals: **specificity of deliverable** (is the output format obvious?), **presence of a testable hypothesis** (can we form a yes/no question?), **known analytical framework** (is there a standard methodology?), **scope boundedness** (is the domain delimited?), and **decision type** (estimation, evaluation, diagnosis, discovery, or recommendation). [Credible — synthesized from consulting and AI sources]

The critical architectural insight is that **EXPLORATORY queries need sequential-with-reflection pipelines** while **EVALUATIVE queries benefit from parallel workstreams**. A paper on sequential research plan refinement (Deep Researcher, arXiv) demonstrates that maintaining global context with progressive narrowing outperforms parallel-only approaches for complex discovery tasks. Meanwhile, Claude and GPT-Researcher show parallel subagents excel when workstreams are independent (as in due diligence dimensions). [Verified]

For the auto shop expansion example, the classifier should identify this as **STRATEGIC** (medium-high uncertainty, scenario-based), producing a decision tree with options (geographic expansion, franchising, acquisition of existing chains) evaluated across dimensions (market attractiveness, operational feasibility, financial returns, competitive dynamics). Each dimension spawns a parallel research workstream.

**Verdict: ADOPT** the 5-type taxonomy and type-specific pipeline routing. **ADOPT** the Rumsfeld Matrix (Known/Unknown) as a structuring tool for EXPLORATORY and STRATEGIC types. **INVESTIGATE** hybrid classification for queries that blend types (e.g., an acquisition query containing EVALUATIVE + EXPLORATORY + SIZING elements).

---

## 5. Scout/strike works — with a Day-1 hypothesis and VOI-based prioritization

The scout/strike pattern is validated across consulting methodology, academic decision theory, and production AI systems. The optimal implementation is a **structured hybrid**: form a Day-1 hypothesis (best-guess answer) immediately, but execute a broad scout phase to test it before committing to focused strike research.

### The exploration-exploitation lifecycle

A multidisciplinary PLOS ONE framework identifies four knowledge phases that organisms and organizations pass through: knowledge establishment (heavy exploration), knowledge accumulation (declining exploration), knowledge maintenance (low exploration), and knowledge exploitation (minimal exploration). **The optimal exploration-exploitation balance varies dynamically with time.** This maps directly to scout/strike: start ~70% scout / 30% strike, then shift to ~20/80 as knowledge grows. [Verified — PLOS ONE]

Anthropic's production system explicitly encodes "start wide, then narrow": agents are prompted to "start with short, broad queries, evaluate what's available, then progressively narrow focus." Early agent versions failed by using "overly long, specific queries that return few results." [Verified — Anthropic engineering blog]

### Value of Information for task prioritization

The **ISPOR VOI framework** provides a rigorous basis for prioritizing research tasks. Four measures apply directly:

- **EVPI** (Expected Value of Perfect Information): sets the upper bound on total research effort worthwhile — "a negligible EVPI indicates little value from additional research"
- **EVPPI** (Expected Value of Partial Perfect Information): identifies which specific parameters matter most
- **EVSI** (Expected Value of Sample Information): value of a realistic research action accounting for imperfect information
- **ENBS** (Expected Net Benefit of Sampling): EVSI minus research cost — the actual decision criterion

For practical implementation, each research task should carry a simplified priority score: **(decision_relevance × current_uncertainty) / estimated_cost**. Tasks where the team is already confident or where the information won't change the output get deprioritized. Tasks where uncertainty is high AND the answer matters get prioritized. [Verified — Value in Health Journal]

### Stopping criteria from information foraging theory

**Information Foraging Theory** (Pirolli & Card, 1999) and the **Marginal Value Theorem** (Charnov, 1976) provide principled stopping rules: a research agent should stop investigating one topic when the marginal rate of return drops below the average rate of return across all research directions. Implement dual stopping criteria: (1) sufficiency — has the working answer met quality thresholds? and (2) diminishing returns — is marginal information gain per token declining below threshold? [Verified — foundational information science]

### Two-phase systems in production

Multiple production systems validate the scout/strike architecture:
- **AI Scientist-v2** (Sakana AI, published in *Nature* 2026) uses progressive agentic tree search: ideation scouts generate research ideas with self-assessed scores, then best-first tree search conducts parallel experiments with pruning of failed branches
- **Go-Explore** (Ecoffet et al., 2019) is explicitly two-phase: Phase 1 explores by returning to promising states and continuing random exploration; Phase 2 robustifies solutions via imitation learning
- **SWE-Search** integrates MCTS with self-improvement, achieving 23% improvement over linear agents through UCB-based node selection (scout) followed by deep exploitation of promising paths (strike) [Credible — OpenReview]

**Verdict: ADOPT** the scout/strike pattern with Day-1 hypothesis. **ADAPT** VOI-inspired priority scoring (simplified, not formal analysis). **ADOPT** dual stopping criteria (sufficiency + diminishing returns). **INVESTIGATE** MCTS/UCB-inspired node selection for choosing which research branches to explore next.

---

## 6. The Observation Library should combine CBR, pgvector, and Karpathy's wiki pattern

The Observation Library is a **Case-Based Reasoning (CBR) system** — this framing unlocks decades of validated architecture. The classic CBR cycle (Aamodt & Plaza, 1994) maps directly: **Retrieve** similar past engagements → **Reuse** past research plans as templates → **Revise** based on new context → **Retain** new outcomes back into the library.

### What consulting firms actually store

McKinsey employs **1,800 knowledge professionals** (10% of workforce) across 6 global knowledge centers and spends **10% of annual revenues on knowledge management**. Their system stores sanitized client project reports, industry/functional deep dives, expert directories, and best practices — all indexed by industry, function, and topic. McKinsey Lilli (their internal AI tool, 2023) scans this knowledge base, locates 5–7 relevant pieces, summarizes key points, and identifies internal experts, cutting research time "from weeks to hours, hours to minutes." [Verified — StrategyU firsthand account, HBS Case Study 396357]

### The hybrid architecture

**Andrej Karpathy's "LLM Knowledge Bases" pattern** (X post and GitHub gist, April 2026) uses three layers: raw sources (immutable documents), an LLM-maintained wiki (markdown summaries, entity pages, cross-references), and a schema file (CLAUDE.md/AGENTS.md) that tells the LLM how the wiki is structured. The wiki's key advantage is **knowledge compounding** — each query's explorations are filed back into the wiki, so synthesis builds over time. It scales well for ~100–1,000 documents but lacks native similarity search. [Verified — primary source]

For the Observation Library's expected scale (dozens to low hundreds of engagements), the recommended architecture is a **three-layer hybrid**:

- **Layer 1 — PostgreSQL + pgvector**: Stores observation records with vector embeddings for semantic similarity search, HNSW indexing, structured metadata columns (domain tags, quality scores, dates), and full-text search via tsvector. This is the retrieval engine.
- **Layer 2 — Compiled Knowledge Wiki** (Karpathy pattern adapted): LLM-maintained markdown files for domain summaries, strategy patterns, failure catalogs, and source quality guides. Auto-maintained `index.md` and periodic "lint" passes for contradictions. This is the synthesis layer.
- **Layer 3 — CBR Engine** (PydanticAI): Implements the full R4 cycle — retrieves similar cases via pgvector, has Claude adapt past plans to new context, revises based on execution results, and retains new observations.

### What to extract from each engagement

The **Trajectory-Informed Memory** paper (arXiv 2603.10600, March 2026) provides the extraction framework. After each engagement, extract three types of guidance: **strategy tips** from successful patterns, **recovery tips** from failure handling, and **optimization tips** from inefficient-but-successful executions. This achieved up to **14.3 percentage point improvement** in task completion on the AppWorld benchmark. [Credible — recent paper with benchmarks]

Each observation should store: engagement description, generated research plan, actual queries executed, sources used with quality scores, findings summary, outcome quality score, success factors, failure modes, strategy/recovery/optimization tips, domain tags, human feedback, and vector embedding of the description + findings.

**Verdict: ADOPT** the CBR R4 cycle as the foundational paradigm. **ADOPT** pgvector + structured metadata as the retrieval layer. **ADAPT** Karpathy's wiki pattern as a compiled synthesis layer stored in PostgreSQL (not filesystem). **ADOPT** trajectory-informed learning extraction. **SKIP** knowledge graphs (Neo4j) — premature complexity at this scale. **SKIP** fine-tuning on observations — insufficient data points, RAG approach superior.

---

## 7. Building and evaluating issue trees with three agents and a meta-judge

### What makes an issue tree good

Six quality dimensions emerge from consulting literature, each measurable:

1. **Mutual Exclusivity**: No overlap between branches at same level. Test: "Can you change one issue independently from the others?"
2. **Collective Exhaustiveness**: All branches cover every possibility. Test: "Are there any other conditions that must be true?"
3. **Insightfulness**: Problem-specific decomposition, not generic frameworks. A tree can be "technically MECE but bring absolutely no insight" (Bruno Nogueira, ex-McKinsey)
4. **Depth & Balance**: 3–4 layers, 2–5 sub-branches per node, with balanced distribution
5. **Actionability**: Each leaf is either testable with specific data or suggests a concrete action
6. **Logical Coherence**: "If Branch 1 AND Branch 2 AND Branch 3 are true, then the hypothesis is true" — if/then structure holds from root to leaves

[Verified — CraftingCases, CaseInterview.com, FirmsConsulting, MCConsultingPrep]

### The Self-MoA synthesis pattern

The **Mixture-of-Agents paper** (Wang et al., 2024) achieved SOTA on AlpacaEval 2.0 (65.1% vs GPT-4 Omni's 57.5%) using layered architecture where an aggregator synthesizes outputs from multiple proposers. Critically, a follow-up study found that **Self-MoA** — aggregating outputs from the same model — outperforms Mixed-MoA by **6.6%** because "MoA performance is rather sensitive to quality, and mixing different LLMs often lowers the average quality." Since the Keystone system uses Sonnet for all construction agents, this validates the architecture: three Sonnet instances with different analytical personas will outperform mixing different model families. [Verified — arXiv 2406.04692 and arXiv 2502.00674]

### The recommended four-phase deliberation pipeline

**Phase 1 — Parallel Construction** (3× Claude Sonnet with different personas):
- Agent A: "First Principles Analyst" — decomposes from fundamentals
- Agent B: "Industry Framework Expert" — applies domain-specific frameworks
- Agent C: "Creative Problem Decomposer" — generates non-obvious angles

All output Pydantic-validated JSON trees with identical schema.

**Phase 2 — Structural Analysis** (programmatic, no LLM):
Compute tree metrics (depth, breadth, balance, node count) and pairwise Structural Similarity Index between trees. Flag structural outliers. This is computationally free and provides useful signal.

**Phase 3 — MECE Evaluation** (Claude Opus as judge):
For each tree independently, evaluate using atomic criteria decomposition (DAG scorer pattern). Mutual exclusivity via pairwise branch overlap detection. Collective exhaustiveness via element extraction from the problem statement mapped to branches (the AOP completeness method). Plus insightfulness, actionability, and logical coherence. **Use binary verdicts (pass/fail) per criterion** — more reliable than numeric scoring for LLM judges. [Credible — DeepEval/ConfidentAI pattern]

**Phase 4 — Synthesis** (Claude Opus as meta-agent):
MoA-style generative aggregation, **not selection**. The meta-agent identifies unique branches across all three trees (union of insights), consensus branches (intersection), resolves conflicts using evaluation scores as weights, and constructs a synthesized tree taking the best branches from each. Apply AOP validation (solvability, completeness, non-redundancy) on the synthesized result. Output includes provenance — which agent contributed what.

The **Delphi method** principles validate this design: anonymity (agents don't see each other's outputs), structured process, and controlled feedback focused on reasoning. The HAH-Delphi paper adds that consensus should be classified not just by score convergence but by "convergence or divergence of underlying logic" — the meta-agent should flag where agents agree structurally but disagree on content, and vice versa. [Credible — multiple recent papers]

**Verdict: ADOPT** Self-MoA pattern with persona-diverse Sonnet agents. **ADOPT** the four-phase pipeline (construct → analyze → evaluate → synthesize). **ADOPT** atomic criteria decomposition for MECE evaluation. **ADAPT** Delphi-style logic-convergence analysis for the synthesis step. **INVESTIGATE** iterative Delphi rounds (start with single round, add iteration if quality is insufficient).

---

## Putting it all together: the auto shop expansion example

For the example engagement — "Keystone is hired by an auto shop chain to determine optimal expansion locations" — the complete Specification Engine flow would execute as follows:

**Step 1 (Problem Framing)**: Classify as STRATEGIC (medium-high uncertainty, multiple viable approaches). Generate problem statement: Decision = where to expand next; Decision-maker = chain's CEO/board; Current hypothesis = "we should expand to nearby markets"; Falsification evidence = data showing nearby markets are saturated or unprofitable; Scope = North American expansion, owned locations.

**Step 2 (Hypothesis Generation)**: Three competing hypotheses: (a) "Expand to adjacent geographies with demographic similarity to successful locations," (b) "Target underserved markets with high vehicle density and few competitors," (c) "Acquire struggling competitors rather than building new locations."

**Step 3 (Issue Tree Decomposition)**: Three Sonnet agents each construct a tree, one per hypothesis. Agent A might decompose into market attractiveness, operational feasibility, and financial returns. Agent B into competitive gaps, customer demand drivers, and regulatory barriers. Agent C into organic growth vs. M&A trade-offs, site selection criteria, and workforce availability.

**Step 4 (Validation)**: Check solvability (can research agents actually find data on workforce availability in target markets?), completeness (does any tree miss the competitive landscape?), non-redundancy (do "demographic similarity" and "customer demand drivers" overlap?).

**Steps 5–8**: Prioritize branches by VOI, configure agents with domain-specific tools (MCP servers for Census data, market research APIs, competitor databases), generate tasks with success criteria ("identify top 10 MSAs by vehicle-per-shop ratio with ≥15% population growth"), present to human for review.

**Step 9 (Scout → Strike)**: Broad scan of 20+ candidate markets, then deep-dive on the 5 highest-signal locations. If scout reveals that the acquisition market is active (several chains recently sold), re-prioritize to explore M&A alongside organic growth.

**Step 10 (Feedback)**: After execution, store the observation: this STRATEGIC engagement worked well with the 3-hypothesis approach; the competitive-gap analysis was most decision-relevant; Census data was the highest-quality source; the initial hypothesis about adjacent markets was falsified.

---

## Conclusion: three things that matter most

First, **problem framing before decomposition is non-negotiable**. The single highest-leverage improvement to the proposed pipeline is separating "What is the problem?" from "How do we break it down?" — and generating competing hypotheses between the two. Every consulting firm learned this lesson; the AI system should encode it.

Second, **the system needs five modes, not one**. A SIZING query and an EXPLORATORY query require fundamentally different pipelines — deterministic calculation trees vs. progressive-narrowing exploration maps. The Specification Engine should classify engagement type in its first step and route to type-specific configurations. This pattern is validated by Adaptive-RAG, FAIR-RAG, and Perplexity's hybrid architecture.

Third, **the Observation Library is the system's long-term moat**. While the pipeline architecture can be replicated, a well-curated CBR library of past engagements — with strategy tips, failure modes, and domain-specific source quality ratings — creates compounding advantage over time. The hybrid pgvector + compiled wiki architecture, implementing the full Retrieve-Reuse-Revise-Retain cycle, turns every engagement into training data without requiring model fine-tuning. McKinsey spends 10% of revenue on knowledge management for good reason.