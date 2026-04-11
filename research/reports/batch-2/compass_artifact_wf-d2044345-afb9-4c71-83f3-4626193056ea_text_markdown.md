# How production AI systems implement iterative, multi-round research

**The dominant architecture across production deep research systems is an orchestrator-worker loop where a lead agent spawns specialized subagents, synthesizes their findings, and decides whether to iterate—with stopping governed by a combination of heuristic sufficiency judgments, hard iteration caps, and diminishing-returns detection.** This pattern appears independently in Anthropic's multi-agent research system, OpenAI's deep research, Google's Gemini Deep Research, and Stanford's STORM, with each system solving the same core tension: how to go deep enough for quality while knowing when to stop. The findings below synthesize technical details from engineering blog posts, academic papers, and production system analyses to provide actionable architectural guidance for the Keystone Intelligence Engine.

---

## Anthropic's orchestrator-worker research loop sets the production standard

Anthropic's multi-agent research system, detailed in their June 2025 engineering blog post "How we built our multi-agent research system," uses a three-tier architecture: **LeadResearcher → Subagents → CitationAgent**. The LeadResearcher (running Claude Opus 4) analyzes the user query, develops a strategy using extended thinking, saves its plan to a **Memory scratchpad** (critical because context beyond 200K tokens gets truncated), and spawns specialized Subagents (running Claude Sonnet 4) with distinct research tasks.

Each Subagent operates in its own **isolated context window** with dedicated tools and exploration trajectory, following an **OODA loop** (Observe-Orient-Decide-Act). Subagents iteratively search, evaluate results using interleaved thinking, and return condensed findings to the LeadResearcher. The lead agent then synthesizes results and makes the critical decision: is more research needed? If yes, it spawns additional subagents or refines its strategy. If not, it exits the loop and hands everything to a CitationAgent for source attribution.

**The stopping decision is fundamentally a model judgment call**, not a rigid algorithm. Anthropic's open-source prompts (available in their Cookbook repository) reveal layered guardrails rather than a single stopping criterion. The subagent prompt explicitly instructs: "Avoid continuing to use tools when you see diminishing returns—when you are no longer finding new relevant information and results are not getting better, STOP using tools." Hard limits enforce boundaries: **maximum 20 tool calls per subagent** and roughly 100 sources, with the subagent terminated if exceeded. The lead agent prompt scales effort to query complexity—simple fact-finding gets 1 agent with 3–10 tool calls, while complex research gets 10+ subagents with divided responsibilities. Early failure modes included "spawning 50 subagents for simple queries" and "scouring the web endlessly for nonexistent sources," which were fixed through prompt engineering and explicit guardrails.

The system's performance is striking: the multi-agent approach outperformed a single-agent Opus 4 baseline by **90.2%** on internal research evaluations. Token usage alone explains **80% of performance variance** on BrowseComp, and multi-agent runs consume roughly **15× more tokens** than standard chat. A key acknowledged limitation is synchronous execution—the lead agent waits for each batch of subagents to complete before deciding next steps.

## Context resets beat compaction for long-running iterative tasks

Anthropic's March 2026 blog post "Harness design for long-running application development" introduced a critical insight for iterative systems: **context resets with structured handoffs outperform context compaction** for models prone to "context anxiety"—where models begin prematurely wrapping up work as they approach their perceived context limit. As the post states: "A reset provides a clean slate, at the cost of the handoff artifact having enough state for the next agent to pick up the work cleanly."

The post describes a **Planner-Generator-Evaluator** architecture (inspired by GANs) where each agent operates in fresh context, communicating through files and structured handoff artifacts. A "sprint contract" negotiated before each iteration prevents goalpost-moving. The evaluator uses **Playwright MCP** to test outputs like a real user, grading against hard thresholds—if any criterion falls below threshold, the sprint fails and triggers another iteration.

A crucial finding for the Keystone Engine: **the optimal context management strategy depends on model capability**. Context resets were essential for Sonnet 4.5 (severe context anxiety), optional for Opus 4.5 (anxiety largely removed), and unnecessary for Opus 4.6 (coherent for 2+ hours without decomposition). This means the harness should be designed to evolve: "Every component in a harness encodes an assumption about what the model can't do on its own, and those assumptions are worth stress testing."

Anthropic's September 2025 post on context engineering identifies three complementary techniques for long-horizon tasks: **compaction** (summarizing near context limits, preserving architectural decisions while discarding redundant tool outputs), **structured note-taking** (agents writing persistent notes outside the context window), and **sub-agent architectures** (subagents use tens of thousands of tokens but return only 1,000–2,000 token condensed summaries). The post frames context as "a finite resource with diminishing marginal returns" and notes that LLMs have an "attention budget" analogous to human working memory.

## Commercial deep research systems converge on 20–60 searches with 3–30 minute runtimes

Across production systems, a surprisingly consistent pattern emerges in scale and approach, though implementations differ significantly.

**OpenAI Deep Research** uses an early version of o3, trained through **end-to-end reinforcement learning** specifically on browsing and reasoning tasks. It follows a ReAct (Plan-Act-Observe) loop where the model autonomously decides when to search again based on information gaps, contradictions, or dead ends. Coverage-based stopping criteria include requiring 2+ independent sources per sub-question, novelty exhaustion detection, and contradiction resolution. Budget-driven hard stops include a **20–30 minute wall-clock maximum**, approximately **30–60 web searches**, and **120–150 page fetches** per task. A notable design choice: a multi-model pipeline where gpt-4.1 handles initial clarification and prompt rewriting before o3 handles the actual research.

**Perplexity Deep Research** takes a speed-optimized approach, completing most tasks in **under 3 minutes** while performing **20–50 targeted queries** and drawing from **200+ sources**. It runs on a custom DeepSeek R1 variant with a proprietary "test time compute expansion" framework. Its 5-stage RAG pipeline parses query intent, retrieves via a Vespa.ai search engine (indexing 200B+ URLs), extracts snippets, synthesizes answers with inline citations, and refines conversationally. A model-agnostic orchestration layer routes queries to the appropriate model based on complexity using small classifier models.

**Google Gemini Deep Research** uses a distinctive three-phase approach: Planning (decomposing the query into a multi-point research plan the user can edit), Research (iterative search/browse/reason loop), and Synthesis (multiple self-critique passes). Its key innovation is a **novel asynchronous task manager** with shared state between planner and task models, enabling graceful error recovery without restarting. It leverages Gemini's **1 million token context window** plus RAG, browses up to hundreds of websites, and according to iPullRank research, executes approximately **20 iterations maximum** before terminating. Most tasks complete in 5–10 minutes.

| System | Searches/task | Sources read | Max iterations | Typical runtime |
|--------|--------------|-------------|----------------|-----------------|
| OpenAI Deep Research | 30–60 | 120–150 pages | ~150–200 reasoning loops | 5–30 min |
| Perplexity Deep Research | 20–50 | 200+ sources | Not disclosed | Under 3 min |
| Google Gemini Deep Research | Dozens to hundreds | Hundreds of websites | ~20 max | 5–10 min |
| Anthropic (multi-agent) | 20 per subagent × 3–5 subagents | ~100 per subagent | Subagent-level capping | Variable |

No published empirical research directly measures quality as a function of iteration count. However, open-source implementations like dzhng/deep-research default to **depth 1–5 recursive iterations with 3–10 queries per iteration**, suggesting 3–5 iterations is a practical sweet spot. OpenAI's novelty-exhaustion stopping criterion implies diminishing returns after the initial rounds.

## STORM proves perspective-driven research threads create natural breadth-depth balance

Stanford's STORM system (NAACL 2024) offers the most transparent architecture for multi-perspective iterative research. STORM decomposes article generation into a **pre-writing stage** (research + outline) and a **writing stage** (article generation). The pre-writing stage has three phases that are directly relevant to the Keystone Engine.

First, **Perspective Discovery**: given a topic, STORM retrieves tables of contents from related Wikipedia articles and prompts an LLM to identify **N diverse perspectives** (default N=5)—for instance, for "2022 Winter Olympics Opening Ceremony," perspectives might include an event planner, cultural historian, and sports journalist. A baseline "basic fact writer" perspective is always included.

Second, **Simulated Conversations**: for each perspective, STORM runs a multi-turn dialogue between a "Wikipedia Writer" (personified with that perspective) and a "Topic Expert" (grounded on internet sources). Each conversation runs up to **M rounds** (default M=5). In each round, the writer asks a question based on conversation history, the system splits it into search queries, retrieves and filters sources, and the expert synthesizes an answer. The writer prompt includes a natural termination signal: "When you have no more questions to ask, say 'Thank you so much for your help!'"

Third, **Outline Refinement**: a draft outline generated from LLM parametric knowledge is refined using all collected conversation transcripts, producing the final research structure.

STORM's convergence approach is notable for its simplicity: it uses a **fixed budget** (N×M question-answer pairs) rather than dynamic convergence detection, supplemented by LLM-initiated early termination within each conversation. The ablation study validates this design—the full pipeline (5 perspectives × 5 rounds) discovers approximately **99.83 unique references** on average, compared to 54.36 without perspectives.

The follow-up **Co-STORM** (EMNLP 2024) adds three important mechanisms: a **Moderator Agent** that surfaces "unknown unknowns" by prioritizing information relevant to the topic but not yet addressed in conversation, a **DiscourseManager** that forces moderator intervention after L consecutive expert responses to prevent stagnation on a single subtopic, and a **dynamic mind map** (tree-structured knowledge graph) that organizes collected information hierarchically and triggers node expansion when concepts accumulate too many items.

## Failure-triggered decomposition outperforms upfront planning for emergent task graphs

The academic literature on adaptive task decomposition reveals a clear finding: **systems that decompose tasks reactively based on execution feedback outperform those that plan everything upfront**. The most important system is **ADaPT** (NAACL 2024 Findings), which implements recursive failure-triggered decomposition. ADaPT first attempts to execute a task directly; only if the executor fails (assessed via a self-generated success heuristic) does the planner decompose the task into sub-tasks with logical operators (AND/OR). Each sub-task is then recursively handled, with a configurable maximum depth. This achieves success rates **28.3% higher on ALFWorld** and **27% higher on WebShop** than baselines, with decomposition depth naturally aligning with task complexity.

**DynTaskMAS** (ICAPS 2025) extends this to asynchronous parallel execution with four innovations: a Dynamic Task Graph Generator that decomposes tasks while maintaining logical dependencies, an asynchronous parallel execution engine, semantic-aware context management, and an adaptive workflow manager that optimizes based on real-time metrics. Results show **21–33% reduction in execution time** and **35.4% improvement in resource utilization**.

For the Keystone Engine, the key architectural pattern is: **attempt execution first, decompose only on failure or insufficient quality, and bound recursion depth**. This creates a natural breadth-depth balance—the system goes deeper only where the executor struggles while leaving simpler sub-tasks at shallow depth. **AdaptOrch** (2026) formalizes a "Performance Convergence Scaling Law" showing that as LLM capabilities converge, orchestration topology (how agents coordinate) dominates system performance over individual model capability—making the Keystone Engine's 6-layer pipeline architecture itself the primary lever for quality.

## Six categories of stopping mechanisms exist, but most production systems use heuristic combinations

The literature reveals six distinct approaches to the stopping problem, roughly ordered from simplest to most sophisticated:

- **Hard iteration limits** remain the most common production approach. Self-Refine caps at 4 iterations, DBAutoDoc at 5, the AI Scientist at 10 search rounds. Simple but effective as a safety net.
- **Quality gate / threshold-based stopping** uses an evaluator LLM to score outputs against criteria. Self-Refine's `is_refinement_sufficient` function returns a scalar score; when it exceeds a threshold or stops improving, the loop terminates. This is the closest AI analog to consulting's "marginal insight doesn't justify marginal cost."
- **Environmental task completion signals** provide binary success/failure—code passing tests, search queries returning sufficient results.
- **Semantic stability detection** measures whether outputs have stopped changing meaningfully. Tacheny (2025) provides the most rigorous theoretical treatment, formalizing agentic loops as discrete dynamical systems in semantic embedding space with measurable geometric indicators: **local drift** (step-to-step similarity), **dispersion** (spread of recent outputs), and **cluster persistence**. Convergence is detected when drift approaches maximum similarity and dispersion decreases monotonically. A critical finding: **prompt design directly controls the dynamical regime**—iterative paraphrasing produces contractive dynamics (convergence), while negation produces exploratory dynamics (divergence).
- **Novelty/information gain scoring** checks whether new iterations produce genuinely new information. The AI Scientist uses Semantic Scholar API for automated novelty checks, discarding ideas with high semantic similarity to existing work.
- **Cost-aware stopping** explicitly factors in API costs, latency, and diminishing quality improvements against a budget constraint.

**DBAutoDoc** (2026) demonstrates the most practical multi-criterion approach, combining description stability windows, per-column confidence thresholds, and semantic change magnitude. It converges within **2 iterations at median**, with rapid quality gains in iterations 1–2 followed by sharp diminishing returns—a pattern likely generalizable to research synthesis tasks.

An important counterpoint from Sinha et al. (2025): marginal gains in single-step accuracy **compound into exponential improvements** in the length of tasks a model can successfully complete, due to a "self-conditioning effect" where errors in context breed more errors. This warns against premature stopping based on perceived step-level diminishing returns.

## Mid-research pivots require hierarchical replanning, not full restarts

For handling discoveries that change the entire research agenda (like finding a company is being acquired mid-competitive analysis), the literature converges on **Plan-and-Act architectures with dynamic replanning**. After each executor step, the Planner receives the current state plus all previous plans and actions and generates a new plan incorporating discoveries. This carries forward relevant context in the evolving plan itself without requiring an explicit memory module.

**AdaPlanner** introduces two complementary refiners: an **In-Plan Refiner** that adjusts the current plan based on environmental feedback (minor scope adjustments) and an **Out-of-Plan Refiner** that handles completely unexpected situations requiring plan restructuring (major pivots). For the Keystone Engine, this maps to detecting whether a discovery requires tweaking the current research thread (in-plan) or fundamentally reframing the research question (out-of-plan).

**LangGraph's LLMCompiler pattern** provides a production-ready implementation: a DAG-based planner with a "Joiner" step that dynamically decides whether to replan or finish based on the entire execution history. The **Reflexion** architecture adds a learning dimension—after evaluating results, the agent generates verbal "lessons learned" stored in episodic memory that inform the next iteration's strategy.

Practical guidance for the Keystone Engine: implement a **scope-change detector** as a lightweight LLM judge that evaluates each subagent's findings against the original research plan. When a finding is classified as scope-changing, the orchestrator should cancel or deprioritize irrelevant in-flight subagents, update the shared memory/scratchpad with new context, and spawn new subagents for the revised research direction. This hierarchical replanning approach avoids full restarts while ensuring the system adapts to genuinely important discoveries. **CostBench** (2025) provides a benchmark for testing exactly this capability, with four types of runtime disruptions including preference changes and tool availability changes.

## Four context strategies and when to use each

LangChain's Harrison Chase codifies context engineering into four strategies: **Write** (save context outside the window via scratchpads and memories), **Select** (pull relevant context back in via RAG or memory retrieval), **Compress** (summarization and observation masking), and **Isolate** (subagents with separate context windows). JetBrains Research (2025) demonstrated empirically that a **hybrid of observation masking plus LLM summarization** provides the best cost-performance tradeoff, reducing costs 7–11% while improving success rates by ~2.6 percentage points on SWE-bench.

For multi-round research specifically, the **Letta/MemGPT paradigm** offers a compelling model: structured memory blocks (core memory always in-context, archival memory searchable out-of-context, recall memory for conversation history) with **self-editing memory**—agents actively manage their own context using tools. When context fills, conversation history is compacted into recursive summaries stored as memory blocks, while old messages remain searchable.

The "lost-in-the-middle" effect remains a practical constraint: even frontier models show sharp performance drops past **32K tokens** on the NoLiMa benchmark (11/12 models dropped below 50% performance). Larger context windows help but don't eliminate the need for active context management.

## Conclusion

The research reveals a mature but still-evolving field where production systems have converged on orchestrator-worker patterns with isolated subagent contexts, but diverge significantly on stopping criteria and context management. For the Keystone Intelligence Engine's 6-layer pipeline, five architectural decisions emerge as most consequential.

First, **implement ADaPT-style failure-triggered deepening** rather than fixed-depth research plans. Each layer should attempt synthesis first and decompose further only when quality gates aren't met—this naturally allocates research depth where it's most needed.

Second, **combine three stopping mechanisms**: a hard iteration cap (likely 3–5 rounds based on production evidence), a quality-gate evaluator that scores research completeness against the original brief requirements, and semantic stability detection measuring whether new rounds produce genuinely novel information.

Third, **use context isolation with structured handoffs** between pipeline layers. Each round's subagents should operate in fresh context, returning condensed 1,000–2,000 token summaries. The orchestrator should maintain a persistent Memory scratchpad with the research plan, key findings, and identified gaps—surviving context resets intact.

Fourth, **build a scope-change detector** into the orchestrator that evaluates subagent findings for research-plan-invalidating discoveries, triggering hierarchical replanning (not full restart) when genuine pivots are needed.

Fifth, **treat the harness as model-capability-dependent**. As Anthropic demonstrated, context resets essential for one model generation become unnecessary for the next. Design the pipeline to make these architectural components pluggable and regularly stress-test whether each component is still earning its complexity cost.