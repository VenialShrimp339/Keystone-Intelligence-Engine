# Adaptive evaluation architecture for multi-type consulting AI

**A hybrid two-tier system—universal gate dimensions plus dynamically generated task-specific weights—is the strongest design for the Keystone Intelligence Engine.** This finding emerges from converging evidence across Anthropic's March 2026 sprint contract pattern, Google Vertex AI's adaptive rubrics (now the recommended production approach), the AdaRubric paper showing +8.5 percentage-point correlation gains from dynamic rubric generation, and MBB consulting firms' own quality frameworks, which universally apply MECE and Pyramid Principle standards while flexing emphasis by engagement type. The two predefined override profiles (estimative vs. current intelligence) are a reasonable starting point, but the system should evolve toward generating evaluation profiles from the research specification itself—using the sprint contract negotiation pattern between planner and evaluator agents. SOS-Bench (ICLR 2025) adds urgency: LLM judges overweight style with **R = 0.999** correlation to overall scores, penalize sarcasm 96% but factual errors only 13%, and are particularly unreliable on quantitative reasoning (the exact domain where consulting rigor matters most).

---

## Anthropic's sprint contract is the design pattern to adopt

The March 24, 2026 Anthropic engineering blog post, "Harness design for long-running application development" by Prithvi Rajasekaran, describes a three-agent architecture (Planner, Generator, Evaluator) where the Generator and Evaluator **negotiate a "sprint contract"** before work begins. The contract defines what "done" looks like—Sprint 3 alone had **27 testable criteria** covering a level editor. The Generator proposes what it will build and how success will be verified; the Evaluator reviews and iterates until both agree. Communication happens through files. Each criterion has a hard threshold; failing any one triggers rework with detailed feedback.

This pattern maps directly to engagement-level evaluation profiles. For the Keystone Intelligence Engine, the flow would be: (1) the research specification enters the system, (2) the planner decomposes it into an issue tree, (3) before research begins, the evaluator agent generates a draft evaluation contract specifying which of the 10 dimensions matter most and what thresholds apply, (4) the generator reviews this contract to ensure criteria are achievable and testable, and (5) both iterate to agreement. The contract becomes the evaluation rubric for that specific engagement.

Anthropic's key insight applies here: **"Every component in a harness encodes an assumption about what the model cannot do on its own. Those assumptions decay as models improve."** When they upgraded from Sonnet 4.5 to Opus 4.6, they removed sprint decomposition entirely because the model could sustain coherent work without it. For the Keystone Engine, this means the evaluation system should be designed so its scaffolding can gracefully degrade as underlying models improve—the sprint contract mechanism may eventually be absorbed into the model's native capability.

The closest software engineering analog is **consumer-driven contract testing (Pact)**, where a consuming service defines its expectations, these are serialized as a contract artifact, and the provider verifies against the contract. The structural parallel is exact: Pact's consumer defines expectations (Generator proposes what it will build), the provider verifies against the contract (Evaluator scores against criteria), and verification fails if responses diverge (sprint fails if any criterion falls below threshold). The key difference is directionality—Pact contracts are consumer-driven, while Anthropic's sprint contracts are bidirectionally negotiated.

---

## The field is moving from predefined to dynamic rubrics—but the best systems use both

Seven production and research systems reveal a clear spectrum from fully predefined to fully dynamic evaluation, with the most effective systems occupying a **hybrid middle ground**.

**Fully predefined systems** include OpenAI Evals (templates selected per task), Braintrust (task-specific vs. task-agnostic metrics chosen by developers), and LangSmith (evaluator functions chosen per experiment using a Rubric-Reasoning-Result pattern). These work well when task types are known in advance and relatively stable. OpenAI explicitly recommends "eval-driven development," comparing it to Behavior-Driven Development (BDD)—write scoped tests at every stage, design task-specific evals.

**Fully dynamic systems** include Google Vertex AI's adaptive rubrics (the recommended default), Amazon Nova's rubric-based judge, and the academic AdaRubric framework. Vertex AI's approach is a two-step process: first analyze the prompt and generate specific verifiable tests, then assess the response against each rubric with a Pass/Fail verdict and rationale. Amazon Nova dynamically generates weighted criteria for each prompt, claiming **49% improvement** on complex evaluation scenarios. AdaRubric generates task-specific orthogonal evaluation dimensions with calibrated 5-point scoring, achieving deployment-grade inter-rater reliability (Krippendorff's α = **0.83**).

**The hybrid approach** is what Anthropic actually uses. They predefine evaluation profiles per task type—frontend design uses four criteria (Design Quality, Originality, Craft, Functionality) with manual weighting, while full-stack coding covers product depth, functionality, visual design, and code quality. Within each task type, the sprint contract adds dynamic specificity per unit of work. Calibration happens through few-shot examples with detailed score breakdowns.

For the Keystone Engine with its 10-dimension rubric, the recommended architecture is:

- **Keep the 2 predefined override profiles** (estimative intelligence, current intelligence) as starting templates
- **Add 5–8 more engagement-type templates** covering the most common consulting deliverable types (market sizing, due diligence, turnaround, strategy, operations improvement, organizational transformation)
- **Layer dynamic refinement on top**, where the evaluator generates engagement-specific weight adjustments and threshold criteria from the research specification, using the sprint contract negotiation pattern
- **Curate over time**: Google Vertex AI practitioners recommend using adaptive rubrics to discover what "good" looks like across real prompts, then having humans curate the generated rubric sets into stable contracts for reuse

---

## LLM judges are systematically unreliable where consulting quality matters most

SOS-Bench (ICLR 2025, Arthur AI/NYU/Columbia) demonstrates that when LLM judges are given explicit criteria—completeness, conciseness, style, safety, correctness—**style predicts the overall score with Pearson R = 0.999**, stable across GPT-3.5-turbo, GPT-4o-mini, GPT-4o, and Claude 3.5 Sonnet. Conciseness is nearly irrelevant (R = 0.097). More critically, violations are penalized asymmetrically: sarcastic tone costs **96% of the score**, concise responses cost 63%, but factual errors cost only **13%** and bland/repetitive output costs just 8%. LLM judges are "highly critical of unconventional stylistic changes but fairly lenient on major factual errors."

This bias varies dramatically by task type. The research reveals a clear reliability hierarchy:

**High reliability (~80% human agreement):** General instruction following and factual QA with reference answers. This is where LLM-as-judge was originally validated (MT-Bench, Chatbot Arena).

**Moderate reliability:** Summarization and code generation with test suites. Pairwise comparison outperforms pointwise scoring. Code evaluation benefits from programmatic verification as a complement.

**Low reliability (58–68% agreement):** Domain-expert tasks (dietetics: 68%, mental health: 64%—both below inter-expert baselines), creative writing (~58%), and mathematical reasoning (~55% for smaller models, unreliable even for large models). For Olympiad-level math, LLM graders **overestimated solution quality by up to 20x**.

**Very low reliability (~47% agreement, κ ≈ 0.3):** Open-ended reasoning and multilingual evaluation.

The CALM framework (ICLR 2025) identified 12 specific biases, with task-type-specific patterns: **fallacy oversight bias** dominates scientific and math reasoning (judges miss logical errors), **authority bias** dominates alignment tasks (fake citations hack the judge), and **refinement bias** dominates humanities tasks (knowing an answer was revised inflates scores regardless of quality).

For the Keystone Engine, this means the **Quantitative Rigor and Analytical Depth dimensions are precisely where LLM evaluation is least trustworthy**. The system should use multi-dimensional scoring (separate scores per criterion) rather than single aggregate scores, provide human-written reference standards for quantitative analyses, employ position-switching and multiple judge models to reduce bias, and treat certain dimensions (particularly Quantitative Rigor for numerical work) as requiring higher-confidence verification—potentially through programmatic checks rather than pure LLM judgment.

---

## Four dimensions are universal gates; six should flex by engagement type

Synthesizing evidence from AdaRubric, the OECD evaluation criteria, Bloom's Taxonomy, Stanford's HELM framework, MQM translation quality metrics, and consulting quality literature, the 10 dimensions divide into two tiers.

**Tier 1 dimensions function as universal gates**—they must always pass a minimum threshold regardless of engagement type. **Intent Alignment** is foundational: every framework studied treats relevance as the first filter, and consulting literature (David A. Fields) insists deliverables must be "right-side up" about the client's question. **Intellectual Honesty** is non-negotiable because a deliverable that misrepresents certainty or cherry-picks evidence fails regardless of task type; the MASK benchmark (2025) specifically measures when LLMs "knowingly produce false statements." **Completeness** appears in virtually every quality framework—the MECE principle fundamentally demands "collectively exhaustive" coverage. **Narrative Coherence** ensures output is understandable and logically structured, though the type of coherence needed varies by task.

**Tier 2 dimensions should flex their weights based on engagement type.** The following mapping synthesizes consulting practice with evaluation research:

| Engagement type | Upweight | Downweight |
|---|---|---|
| Market sizing / financial modeling | Quantitative Rigor, Source Quality, Calibrated Confidence | Evaluative Surprise |
| Due diligence | Source Quality, Quantitative Rigor, Intellectual Honesty, Calibrated Confidence | Narrative Coherence |
| Strategy development | Analytical Depth, Evaluative Surprise, Actionability | (all moderate) |
| Turnaround / restructuring | Actionability, Quantitative Rigor, Analytical Depth | Evaluative Surprise, Source Quality |
| Organizational transformation | Narrative Coherence, Analytical Depth, Evaluative Surprise | Quantitative Rigor |
| Regulatory / compliance | Source Quality, Completeness, Calibrated Confidence | Evaluative Surprise |
| Innovation / market entry | Evaluative Surprise, Analytical Depth, Actionability | Source Quality (lower bar acceptable) |

The **Evaluative Surprise** dimension deserves special attention. No direct academic literature exists under this exact term, but the concept maps to consulting's emphasis on value-add—"Did you add unique value or simply move the pieces around?" It also connects to the AdaRubric finding that generic helpfulness rubrics miss task-specific quality signals. For strategy and innovation engagements, this dimension is critical; for compliance and standardized reporting, it should be downweighted substantially.

For aggregation, the evidence strongly favors **geometric mean** over weighted sum. Both Stanford's HELM and the MQM framework use geometric mean specifically because it prevents high-scoring dimensions from masking failures—a zero in any dimension zeros out the aggregate. AdaRubric implements the same principle through its DimensionAwareFilter.

---

## Issue tree decomposition should directly drive evaluation weight generation

The connection between MECE issue tree decomposition and evaluation criteria generation is the most architecturally novel aspect of this system. The research supports a three-step mapping:

**Step 1: Classify each issue tree branch by cognitive level.** Bloom's Revised Taxonomy (Anderson & Krathwohl, 2001) provides the framework. Branches requiring Remember/Understand (factual lookup, landscape scan) emphasize Completeness and Source Quality. Branches requiring Analyze (market structure, competitive dynamics) emphasize Analytical Depth and Quantitative Rigor. Branches requiring Evaluate/Create (strategic recommendations, risk assessment) emphasize Calibrated Confidence, Evaluative Surprise, and Actionability.

**Step 2: Classify each branch by quantitative vs. qualitative nature.** If the issue tree identifies "logistics optimization" as the key branch, the system should upweight Quantitative Rigor because that branch demands numerical analysis. If it identifies "organizational culture alignment" as key, Narrative Coherence and Analytical Depth should increase. MIT's Data Quality Assessment framework (Pipino, Lee & Wang, 2002) provides the theoretical basis for this: "task-dependent" quality metrics include business rules and contextual constraints that "task-independent" metrics miss.

**Step 3: Generate weighted evaluation criteria from the classification.** The OECD DAC evaluation framework explicitly states: "The use of the criteria depends on the purpose of the evaluation. The criteria should not be applied mechanistically." This principle, applied to the Keystone Engine, means the evaluator agent should examine the issue tree structure, identify which branches carry the most analytical weight, and generate dimension weights accordingly—then negotiate these with the generator via the sprint contract pattern.

---

## MBB quality frameworks reveal a universal-plus-flexible architecture

McKinsey, BCG, and Bain all operate with a **two-layer quality system** that mirrors the recommended evaluation architecture. The universal layer—MECE structuring, Pyramid Principle communication, hypothesis-driven approach, the "so what?" test, source rigor, and partner review—applies to every engagement regardless of type. McKinsey's **obligation to dissent** requires every team member, from junior analyst to senior partner, to challenge work they believe is wrong. Bain's **True North** philosophy demands "deep intellectual honesty, and the candor to tell it like it is." BCG evaluates consultants on **5 dimensions** (3 weighted more heavily) covering frameworking, driving value, and client management.

The engagement-specific layer then shifts emphasis dramatically. Due diligence engagements for PE clients operate under compressed **2–3 week timelines** where speed-to-insight and investment-grade confidence dominate; PE clients are sophisticated and the quality bar for analytical rigor is extreme. Strategy engagements over 6–12 weeks prioritize novel insight and "aha" moments. Turnaround engagements sacrifice comprehensive analysis for speed, with weekly milestone tracking. No engagement type has a "lower" quality bar—the dimensions that matter most simply shift.

One crucial finding: **no MBB firm publishes a formal quality rubric**. Quality enforcement works through cultural norms (obligation to dissent), standardized communication frameworks (MECE, Pyramid), tiered review processes (analyst → manager → partner), and performance evaluation systems. Unlike auditing (which has PCAOB, SQMS, and external quality reviews), management consulting has no external regulatory quality framework. Quality is entirely self-policed through culture and brand reputation. This means the Keystone Engine's explicit rubric-based approach actually exceeds consulting industry practice in evaluation formality—a potential competitive advantage if calibrated well.

Partners review decks by **reading only the action titles**—if the argument doesn't hold from titles alone, the deck fails. Every data point requires a cited source. Every finding must pass the "so what?" test. These principles translate directly to evaluation criteria: Intent Alignment maps to "right-side up" deliverables, Source Quality maps to citation requirements, Narrative Coherence maps to the Pyramid Principle, and Actionability maps to the "so what?" test.

---

## Conclusion: a practical evaluation architecture for the Keystone Engine

The evidence points to five architectural decisions. First, **keep the 10-dimension rubric but implement it as two tiers**: four universal gate dimensions (Intent Alignment, Intellectual Honesty, Completeness, Narrative Coherence) that must pass minimum thresholds on every engagement, and six adaptive dimensions whose weights are generated from the research specification. Second, **extend the two predefined override profiles to approximately 8–10 engagement-type templates**, covering the most common consulting deliverable types, but treat these as starting points rather than endpoints. Third, **implement the sprint contract pattern** between the planner/evaluator and generator agents, where the evaluator proposes engagement-specific evaluation criteria derived from the issue tree decomposition, and the generator reviews these before work begins. Fourth, **use geometric mean aggregation** rather than weighted sum to prevent compensation across dimensions—a failure in Intellectual Honesty should not be masked by high Narrative Coherence scores. Fifth, **build explicit safeguards against LLM judge style bias**, particularly for Quantitative Rigor evaluation, where LLM judges are empirically least reliable: consider programmatic verification of numerical claims, multi-judge panels with position-switching, and human-written reference standards for high-stakes engagements.

The most important insight from this research is that the predefined-vs-dynamic question is a false dichotomy. Anthropic's sprint contract demonstrates the correct answer: **predefined frameworks provide the vocabulary and constraints, while dynamic negotiation provides the task-specific calibration**. The system should know the 10 dimensions it can evaluate against (predefined), have template profiles for common engagement types (predefined), and generate specific weights, thresholds, and success criteria from each engagement's research specification and issue tree (dynamic). As models improve, the predefined scaffolding can gracefully degrade while the dynamic negotiation capabilities strengthen.