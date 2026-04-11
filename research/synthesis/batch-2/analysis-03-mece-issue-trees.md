# Analysis: Report 03 — MECE Issue Tree Decomposition
*Analyzed: 2026-04-05 | Priority: Tier 1 (HIGHEST) | Report quality: high*

## Executive Summary

This report is the highest-fidelity match to Jack's architectural directive of any report analyzed to date. It directly addresses the casing phase insertion before task decomposition, validates the independent parallel analysis pattern for tree generation, and provides a concrete implementation path using existing components (PydanticAI, Opus-as-evaluator, DAG-based task mapping). The central finding — that no production system currently enforces MECE properties, making this a genuine greenfield challenge — confirms that Keystone is building something novel. Three specific findings have immediate implementation consequence: reasoning-first schema ordering in Pydantic models (confirmed critical and easy to get wrong), heterogeneous consulting lenses as the correct framing for parallel tree generation (not just identical agents), and the ADaPT shallow-then-adaptive decomposition pattern as a cost-superior alternative to deep upfront decomposition. One significant gap remains: branch prioritization reliability, where the report honestly acknowledges systematic LLM overconfidence with no clean resolution.

---

## Key Findings (ranked by implementation impact)

### 1. Heterogeneous Consulting Lenses for Parallel Tree Generation

- **What:** Assigning distinct analytical roles to parallel agents (financial lens, operational lens, market/competitive lens) yields 4-6% absolute accuracy gains and 30% fewer factual errors over homogeneous parallel generation. Simple majority voting captures most observed gains from multi-agent debate; the communication/debate phase adds marginal value. Independent parallel generation with subsequent selection is the right pattern.
- **Evidence basis:** Zhou & Chen, A-HMAD (2025); NeurIPS 2025 Spotlight, Choi et al.; ICLR 2025 analysis of multi-agent debate methods; Google DeepMind compute-optimal scaling study (2025).
- **Evidence quality:** Verified (peer-reviewed 2025, multiple independent confirmations)
- **Temporal check:** Current. All citations 2025 or later.
- **Conflicts with existing project research?** No. This directly validates and extends the existing independent parallel analysis pattern from L1.5 deliberation. The extension is the heterogeneous lens specification.
- **Verdict:** ADOPT
- **Justification:** Directly validates Jack's directive on multi-agent tree generation while providing a concrete operationalization (lens assignment) that the original directive left unspecified.
- **Keystone impact:** L0 Specification Engine (Component 5); L1.5 Deliberation (Component 9); feeds into JACK-ARCHITECTURAL-DIRECTIVES.md item 2. Modifies the parallel tree generation step: agents receive distinct system prompts specifying consulting lens, not just "generate an issue tree."
- **Contradicts:** None. Consistent with settled decision #2 (deliberation = independent parallel analysis, not debate).

---

### 2. Reasoning-First Pydantic Schema Ordering (Critical Implementation Detail)

- **What:** When constrained JSON decoding forces a model to populate answer fields before reasoning fields, reasoning quality degrades because the model commits to a conclusion before it can think. For the issue tree Pydantic model, `reasoning` and `rationale` fields must be declared before `branches` and `priority` fields in the schema. An alternative: generate the tree in natural language first, then use a lightweight model (Haiku) to convert to structured JSON, decoupling formatting from reasoning.
- **Evidence basis:** Tam et al. (EMNLP 2024); Park et al. (NeurIPS 2024); SLOT framework (EMNLP 2025).
- **Evidence quality:** Verified (peer-reviewed, multiple independent replications across two EMNLP papers and one NeurIPS paper)
- **Temporal check:** Current. 2024-2025 citations.
- **Conflicts with existing project research?** This is new and directly actionable. No existing project research addresses Pydantic schema field ordering for reasoning tasks.
- **Verdict:** ADOPT
- **Justification:** This is a cheap, high-leverage implementation detail that is easy to get wrong by default and directly affects the quality of the most critical pipeline stage.
- **Keystone impact:** Component 5 (Specification Engine L0); Component 1 (RESEARCH.md spec format); any Pydantic model used in reasoning-intensive generation steps. Constraint: all issue tree Pydantic models must be audited for field order before implementation. The natural language-then-Haiku-conversion pattern (SLOT) is also worth tracking as a future optimization if Sonnet constrained decoding proves unreliable.
- **Contradicts:** None. Adds a constraint to settled decision #8 (protocol-based contracts / structural typing).

---

### 3. Shallow-Then-Adaptive Decomposition (ADaPT Pattern)

- **What:** Start with a 2-3 level shallow issue tree, then trigger deeper decomposition only when a research agent reports a branch is too complex to investigate directly. ADaPT achieved +28.3% over standard plan-and-execute on ALFWorld while being more cost-effective. This is categorically different from the intuitive approach of building a complete deep tree upfront.
- **Evidence basis:** ADaPT framework (NAACL 2024); ADAPT framework (NAACL 2024); practitioner synthesis in the report's conclusion.
- **Evidence quality:** Credible (peer-reviewed 2024, solid benchmark results)
- **Temporal check:** Current. 2024, stable finding.
- **Conflicts with existing project research?** Minor tension. Jack's directive describes a deliberate upfront casing phase that implies a reasonably complete tree before research begins. This finding argues for intentional shallowness to allow organic deepening. These are compatible if the initial tree is framed as a working hypothesis, not a final structure, which aligns with Jack's "living document" directive.
- **Verdict:** ADOPT
- **Justification:** The +28.3% performance gain with lower cost is the strongest quantitative argument in the report; shallow initial trees also reduce the time cost of the human review gate after tree generation.
- **Keystone impact:** Component 5 (Specification Engine L0); modifies the casing phase design: L0 produces a 2-3 level tree for human review, not an exhaustively detailed one. Deeper decomposition happens during or after L1 research, feeding back into the living tree. Directly supports Jack's directive #2 (living document) and directive #7 (human gate after issue tree — a shallow tree is easier to review meaningfully).
- **Contradicts:** Partial tension with "complete casing before research begins" interpretation of directive #2. Resolution: the casing phase produces a validated structure, not complete depth.

---

### 4. Discrete MECE Verification Stage with Opus-as-Evaluator

- **What:** After tree generation, run a separate verification step that explicitly checks: (a) sibling branch overlap, (b) gaps in coverage of the root question, (c) leaf node specificity sufficient for concrete task assignment. Use a more capable model (Opus 4.6) as the evaluator for trees generated by Sonnet — this model-capability asymmetry makes maker-checker effective. Combine programmatic semantic similarity checks (cosine similarity between branch descriptions) with LLM-as-judge for coverage and tailoring.
- **Evidence basis:** Microsoft Azure AI maker-checker pattern (architecture guidance, 2025); G-Eval framework (Liu et al., EMNLP 2023); GPT-4-as-judge vs. human-human agreement study (Zheng et al., 2023, 85% vs. 81%); DeepEval's PlanQualityMetric.
- **Evidence quality:** Credible (maker-checker from production guidance; G-Eval peer-reviewed but 2023)
- **Temporal check:** G-Eval is 2023, but the LLM-as-judge pattern has only strengthened since. Credible.
- **Conflicts with existing project research?** No. Aligns with settled decision #3 (five-layer evaluator stack) and settled decision #4 (Opus for L0/L4).
- **Verdict:** ADOPT
- **Justification:** Formalizes the only reliable quality gate for MECE compliance into a discrete pipeline step with a concrete implementation path that uses already-decided model assignments.
- **Keystone impact:** Component 5 (Specification Engine L0); Component 6 (Evaluator L4 — the MECE verification step is structurally similar to L4's evaluator and may share implementation patterns). Creates a new discrete step: tree generation (Sonnet, heterogeneous lenses) -> MECE verification (Opus) -> human review gate -> task mapping.
- **Contradicts:** None.

---

### 5. Five-Dimension MECE Evaluation Rubric (Concrete Metric Framework)

- **What:** Consulting firms evaluate issue trees on five dimensions: mutual exclusivity, collective exhaustiveness, tailoring, actionability, depth appropriateness. The report provides specific, implementable LLM-as-judge prompts for each dimension. Tailoring check ("is this specific to the stated problem or could it apply to any similar question?") is the dimension most likely to catch the generic-framework failure mode. Depth heuristics: 2-4 levels, 8-20 leaf nodes for most consulting problems.
- **Evidence basis:** Consulting interview training rubrics (standard across McKinsey/BCG/Bain); G-Eval implementation pattern (EMNLP 2023); DeepEval PlanQualityMetric.
- **Evidence quality:** Credible (consulting rubrics are standard industry methodology; G-Eval peer-reviewed)
- **Temporal check:** Consulting methodology is timeless; G-Eval implementation from 2023 is still current pattern.
- **Conflicts with existing project research?** No existing project research defines MECE evaluation metrics. This fills a gap.
- **Verdict:** ADOPT
- **Justification:** The five-dimension rubric is directly implementable as structured LLM-as-judge prompts and provides the first concrete, actionable quality metric for the casing phase.
- **Keystone impact:** Component 5 (Specification Engine L0); Component 6 (Evaluator L4 — tree quality becomes a distinct evaluation sub-domain); contributes to the 10-dimension rubric via the Completeness (8%) and Intent Alignment (15%) dimensions, which partially overlap with collective exhaustiveness and tailoring.
- **Contradicts:** None.

---

### 6. Hypothesis-Driven Branch Framing

- **What:** Each branch should be framed as a testable hypothesis ("Revenue decline is driven by pricing pressure in the enterprise segment") rather than a topic label ("Enterprise pricing"). Hypothesis framing makes the research task and success criteria explicit, improving the quality of downstream task generation. LINA framework (2024) demonstrated 24% improvement in logical reasoning from hypothesis-deductive framing.
- **Evidence basis:** LINA framework (2024); consulting methodology (hypothesis-driven problem solving is McKinsey's foundational method).
- **Evidence quality:** Credible (LINA peer-reviewed 2024; consulting methodology is standard)
- **Temporal check:** Current. LINA is 2024; the consulting methodology is timeless.
- **Conflicts with existing project research?** No. Adds a specific prompt engineering constraint to the issue tree generation step.
- **Verdict:** ADOPT
- **Justification:** Aligns the AI-generated tree with McKinsey methodology (Jack's FITFO standard) while providing a mechanistic improvement in task clarity that reduces ambiguity in research task assignment.
- **Keystone impact:** Component 5 (Specification Engine L0); Component 1 (RESEARCH.md spec format — hypothesis framing should propagate into research task definitions); directly operationalizes Jack's directive #6 (FITFO standard / issue tree as primary analytical tool).
- **Contradicts:** None.

---

### 7. Performance Plateau at ~4 Agents for Parallel Tree Generation

- **What:** Google DeepMind (2025) compute-optimal scaling found that performance plateaus around 4 agents for parallel sampling on hard creative tasks. This provides a principled upper bound for the parallel tree generation step.
- **Evidence basis:** Snell et al., Google DeepMind (2025); MAKER framework results.
- **Evidence quality:** Verified (Google DeepMind research, 2025)
- **Temporal check:** Current. 2025.
- **Conflicts with existing project research?** No. The existing plan specified 3-5 agents for L1; this finding validates the upper bound. For the tree generation step specifically, the sweet spot is 3-4.
- **Verdict:** ADOPT
- **Justification:** Eliminates ambiguity from the "3-5 agents" range for the casing phase: default to 3 lenses (financial, operational, market/competitive), add a 4th (regulatory/risk) for complex engagements, do not go to 5.
- **Keystone impact:** Component 5 (Specification Engine L0); L1 Research Agent configuration. Tightens the deployment model spec.
- **Contradicts:** None.

---

### 8. LLMCompiler DAG Pattern for Tree-to-Task Mapping

- **What:** Issue tree leaf nodes map to a DAG of research tasks with dependency edges (one-to-one, one-to-many, many-to-one patterns). LLMCompiler achieved 3.6x speedup and 4.65x cost reduction versus sequential ReAct execution. The tree-to-task mapping should be validated as a discrete step before execution, not generated on-the-fly.
- **Evidence basis:** Kim et al., LLMCompiler (2023); pydantic-deep framework (Vstorm, 2026) for task tracking and cycle detection.
- **Evidence quality:** Verified for LLMCompiler (peer-reviewed 2023, implemented in LangGraph); Credible for pydantic-deep (2026, active project)
- **Temporal check:** LLMCompiler 2023 is foundational and current; pydantic-deep 2026 is current.
- **Conflicts with existing project research?** No. This is the first explicit specification of the tree-to-task mapping architecture. The existing plan has research-tasks.json dispatch but does not define the structural relationship between tree and tasks.
- **Verdict:** ADAPT
- **Justification:** The LLMCompiler DAG pattern is the right architecture but must be adapted for PydanticAI's graph support rather than adopted as a LangChain/LangGraph dependency; pydantic-deep adds cost tracking that aligns with the $12-$100 engagement cost target.
- **Keystone impact:** Component 5 (Specification Engine L0); Component 7 (Research Agent pipeline L1). The RESEARCH.md spec format (Component 1) and research-tasks.json need to encode dependency structure, not just flat task lists.
- **Contradicts:** None. Extends the existing dispatch architecture.

---

### 9. Two-Agent Living Tree Update Pattern (AINav)

- **What:** Separate "should we replan?" from "how do we replan?" using two distinct agents: an Advisor agent that detects when tree modification is warranted (failure, new discovery, periodic revaluation), and an Arborist agent that determines the structural change. Hard ceiling of ~3 replanning cycles per workflow. Completed tasks are immutable; only pending tasks can be modified.
- **Evidence basis:** AINav (2025); Sda-Planner (2025); KGLAMP (2025 — 64% vs 12% task completion under partial observability); practitioner convergence on 3-cycle limit.
- **Evidence quality:** Credible (AINav and Sda-Planner are 2025 peer-reviewed; KGLAMP is 2025; 3-cycle limit is practitioner consensus, not formally verified)
- **Temporal check:** Current. All 2025.
- **Conflicts with existing project research?** No. Directly implements Jack's directive that the issue tree is a living document. The two-agent separation is a concrete implementation pattern not previously specified.
- **Verdict:** ADAPT
- **Justification:** The separation of detection from modification is architecturally clean and prevents unnecessary replanning, but the "Advisor" and "Arborist" framing should be collapsed into a single orchestrator step in Phase 1 for simplicity, with the two-agent pattern reserved for Phase 2.
- **Keystone impact:** Component 5 (Specification Engine L0); Component 9 (Deliberation L1.5 — post-research tree updates happen here). The 3-cycle hard ceiling and immutable-completed-tasks rule should be encoded as system invariants, not prompt instructions.
- **Contradicts:** None.

---

### 10. Multi-Signal Branch Prioritization (With Acknowledged Reliability Ceiling)

- **What:** LLMs are systematically overconfident about knowledge boundaries. No single confidence measure is reliable. The recommended multi-signal approach combines: (1) sampling-based consistency across multiple tree generations (high consistency = high confidence in branch relevance), (2) feasibility estimation via concrete resource assessment ("what data sources would answer this?"), (3) structured rubric scoring against consulting-standard priority criteria (impact, time sensitivity, interdependency), (4) logprob uncertainty as a complementary signal. LLMs guided by organizational context achieve F1 scores of 0.68-0.79 on prioritization tasks.
- **Evidence basis:** Kadavath et al., Anthropic P(IK) paper (2022); Harvard Kempner Institute epistemic uncertainty study (2025); Griot et al., Nature Communications (2025); Steyvers & Peters (2025); vulnerability triage F1 scores (2025).
- **Evidence quality:** Verified for P(IK) and overconfidence findings (Anthropic and Nature Communications); Credible for multi-signal approach (2025, multiple sources)
- **Temporal check:** P(IK) paper is 2022 (Stale as a standalone claim, but the overconfidence finding has only been reinforced by subsequent work). The multi-signal approach is 2025 and current.
- **Conflicts with existing project research?** No. The 5-tier confidence map in L1.5 Deliberation is compatible with this approach.
- **Verdict:** ADAPT
- **Justification:** The multi-signal approach is the right pattern but F1 of 0.68-0.79 means roughly 1 in 4-5 branch priority assignments will be wrong; design the system to reprioritize after each research cycle rather than relying on initial prioritization being correct.
- **Keystone impact:** Component 9 (Deliberation L1.5 — confidence map generation); Component 7 (Research Agent pipeline — prioritization determines which branches are investigated first). Human review gate after confidence map (Jack's directive #7) is partly motivated by this reliability ceiling.
- **Contradicts:** None. Adds nuance to the 5-tier confidence map design.

---

### 11. Few-Shot MECE Exemplar Library

- **What:** 2-3 high-quality MECE decomposition examples in prompts improved LLM decomposition accuracy by 140-163% over zero-shot. Quality matters more than quantity: noisy examples degrade performance below zero-shot baselines. Recommendation: curate a library of gold-standard issue trees across common consulting problem types (profitability, market entry, M&A, operations, growth strategy), select the most structurally relevant example at inference time.
- **Evidence basis:** Bug report decomposition study (cited in report, no direct author/venue attribution); Cleanlab noisy-example degradation study.
- **Evidence quality:** Credible (the magnitude of the finding is consistent with broader few-shot literature, but the specific 140-163% figure lacks direct citation to a named paper)
- **Temporal check:** Consistent with known few-shot prompting research; the specific figure is unverifiable from the report's citations.
- **Conflicts with existing project research?** No. Aligns with Karpathy's compiled markdown wikis directive (item 8 in Jack's directives) — the exemplar library is the issue tree instantiation of that principle.
- **Verdict:** ADOPT
- **Justification:** The performance gain magnitude is plausible and the exemplar library directly operationalizes the accumulated knowledge principle (Observation Library, Karpathy wikis) in the most impactful pipeline stage.
- **Keystone impact:** Component 5 (Specification Engine L0); META layer (exemplar library is a form of Observation Library for structural patterns). The exemplar library must be curated before L0 is production-ready; this is a non-trivial content investment, not just an engineering task.
- **Contradicts:** None.

---

### 12. Plan-and-Solve + Skeleton-of-Thought Prompting Pattern

- **What:** Plan-and-Solve prompting (Wang et al., ACL 2023) — "first understand the problem and devise a plan, then carry out the plan" — consistently outperforms zero-shot chain-of-thought across all tested benchmarks. Skeleton-of-Thought (Ning et al., ICLR 2024) generates a 3-10 point skeleton first, then expands each point, achieving equal or better quality in ~60% of cases while enabling parallel expansion of branches.
- **Evidence basis:** Wang et al., ACL 2023; Ning et al., ICLR 2024.
- **Evidence quality:** Verified (both peer-reviewed; Plan-and-Solve has been widely replicated)
- **Temporal check:** Plan-and-Solve is 2023 (now well-established). Skeleton-of-Thought is ICLR 2024. Both credible and current.
- **Conflicts with existing project research?** No. These are specific prompting patterns for the issue tree generation step that are not currently specified in the plan.
- **Verdict:** ADOPT
- **Justification:** Both patterns are low-cost, high-reliability prompt engineering techniques that directly implement the "structure before solve" consulting discipline the system is trying to encode.
- **Keystone impact:** Component 5 (Specification Engine L0 — system prompt design); this should be part of the L0 prompt template library. Skeleton-of-Thought's parallel expansion is especially useful because it naturally maps to the parallel heterogeneous-lens architecture.
- **Contradicts:** None.

---

## Architectural Decisions This Enables

**Decision: Casing Phase as Discrete Pipeline Stage with Five Sub-Steps**

The casing phase is now fully specifiable. Sequence:
1. Receive engagement + workstream from RESEARCH.md
2. Generate 3 independent issue trees in parallel, each with a distinct consulting lens system prompt (financial, operational, market/competitive), using Plan-and-Solve + Skeleton-of-Thought prompting, with 2-3 curated MECE exemplars, reasoning fields declared before branch fields in Pydantic schema
3. MECE verification by Opus 4.6 on each tree against five-dimension rubric (mutual exclusivity, collective exhaustiveness, tailoring, actionability, depth appropriateness); also check programmatic semantic similarity between sibling branches
4. Select highest-scoring tree or synthesize strongest branches from multiple trees; Opus selects
5. Human review gate (non-negotiable per Jack's directive #7)
6. Tree-to-task DAG mapping with completeness validation (every leaf has at least one task; no duplicate tasks)
7. Dispatch to L1 research agents

**Decision: Shallow Initial Tree as Phase 1 Default**

Initial tree depth is 2-3 levels with 8-20 leaf nodes. Deeper decomposition is triggered adaptively by research agent reports, not built upfront. This is both more cost-effective and produces a more reviewable artifact for the human gate.

**Decision: Living Tree Update Rules as System Invariants**

Three replanning cycles maximum, hard ceiling. Completed tasks immutable. Replanning triggered by: research agent failure report, discovery of a branch that invalidates the current tree structure, or post-deliberation analysis. Update logic is an orchestrator responsibility, not a prompt instruction.

**Decision: Branch Prioritization via Multi-Signal Scoring, Reprioritized Per Cycle**

Initial prioritization uses sampling consistency + feasibility + structured rubric. The system is designed to reprioritize after each research cycle. Branch priority at cycle N is a working hypothesis, not a commitment.

---

## Changes to Existing Plan

**CAPSTONE-PLAN-v2.md / Specification Engine (L0):**
- Add the casing phase as a named, discrete stage before task generation. Currently the plan describes intent clarification -> RESEARCH.md -> 4-step verification -> research-tasks.json. The casing phase inserts between RESEARCH.md and research-tasks.json.
- Change research-tasks.json format to encode DAG dependency structure between tasks, not a flat list.
- Add the MECE verification step (Opus 4.6 evaluator) between tree generation and human review.
- Add reasoning-field-first constraint to all L0 Pydantic schemas.

**Component 1 (RESEARCH.md spec format):**
- The spec format must include fields that the casing phase consumes: engagement type (profitability, market entry, M&A, operations, growth, or custom), workstream scope, and hypothesis framing instructions for branch generation.

**Component 5 (Specification Engine L0) — now the most structurally complex Phase 1 component:**
- Requires: exemplar library (content investment, not just engineering), lens-specific system prompts (3 base templates + extension mechanism for engagement-specific lenses), Pydantic models with correct field ordering, MECE rubric prompts, Opus-as-verifier integration, human review gate implementation, DAG mapper with completeness checker.
- Estimated complexity should be upgraded from L (large) to XL; it is now comparable in complexity to L4 (Evaluator).

**10-Dimension Rubric (L4 Evaluator):**
- Tree quality evaluation (five MECE dimensions) should be considered for explicit representation in the rubric. Currently Completeness (8%) and Intent Alignment (15%) partially capture this. No rubric weight change is recommended here — tree quality is an L0 output metric, not an L4 deliverable metric — but the MECE rubric should be specified in the L4 evaluation spec as a cross-check on whether the research task decomposition was sound.

---

## Open Questions Remaining

1. **Lens selection for non-standard engagement types.** The three base lenses (financial, operational, market/competitive) cover standard consulting problem types. Novel engagement types (regulatory, technology transformation, organizational design) may require dynamically generated lenses. How does L0 determine which lenses to use when the engagement type is not one of the canonical five (profitability, market entry, M&A, operations, growth strategy)? This is the intersection of Report 03 and Report 10 (Spec Engine).

2. **Synthesis vs. selection for competing trees.** The report recommends "select the best tree or merge the strongest branches from multiple trees" but provides no concrete algorithm for branch-level synthesis. Simple selection is safe; synthesis risks producing a chimera tree with hidden inconsistencies. What is the merge policy when two trees agree on top-level branches but disagree on second-level decomposition?

3. **Exemplar library bootstrap problem.** The 140-163% few-shot improvement requires a curated exemplar library before L0 is production-ready. This library does not exist and is a content investment, not an engineering task. Who produces it, by what quality bar, and before which milestone?

4. **Human review gate tooling.** Jack's directive specifies a human review gate after the issue tree. The report does not address the tooling or interface for this gate. What does the human see? Can they edit branches directly? Does edits trigger re-verification? This is an implementation detail with significant UX consequence.

5. **MECE verification threshold for regeneration.** The report recommends running MECE evaluation and regenerating trees that fall below a threshold. What is the threshold, and what happens when all 3-4 parallel trees fail? Is there a fallback to human-guided decomposition?

6. **pydantic-deep dependency assessment.** The report cites pydantic-deep (Vstorm, 2026) for task tracking, cycle detection, and cost tracking. This is a 2026 project from an unknown vendor. Requires independent vetting before adoption; it may be underdeveloped or abandoned.

7. **Integration point with Report 02 (dynamic agents).** The tree structure determines how many research agents are instantiated and with what specialization. The dynamic agent spawning architecture from Report 02 must be compatible with the DAG-based task dispatch from this report. The interface contract between tree-to-task mapping and agent instantiation is unspecified.
