# Analysis: Report 02 — Dynamic Agent Configuration
*Analyzed: 2026-04-05 | Priority: Tier 2 (HIGH) | Report quality: high*

## Executive Summary

This report directly validates Jack's Directive #1 (the Rigidity Problem) with substantial empirical grounding and provides a concrete architecture — the template registry pattern — for replacing the current fixed enums. The evidence is current (Anthropic June 2025, Google DeepMind December 2025, Snap 2026), the production case studies are instructive and credible, and the recommended design maps cleanly onto the existing `AgentDefinition` model. Three insights are immediately actionable: tool assignment as hard constraint (not system prompt guidance), the tighten-only invariant for governance in dynamic hierarchies, and the template promotion loop as the mechanism for closing the fixed-vs-dynamic tradeoff. The single most important calibration finding — that token usage explains 80% of performance variance, not architecture — is a significant constraint on the Specification Engine's responsibility and should influence Phase 1 prioritization.

---

## Key Findings (ranked by implementation impact)

### 1. Agents as declarative configs: the industry-wide convergence

- **What:** Every major production framework (OpenAI Agents SDK, Google ADK, CrewAI, PydanticAI, Claude Code) has converged on a single abstraction: `Agent = (system_prompt, tools[], output_schema, constraints)`. This is a declarative configuration generated and composed at runtime, not a code-level class hierarchy or enum.
- **Evidence basis:** OpenAI Agents SDK, Google ADK, CrewAI, PydanticAI, Claude Code subagent system — all documented against 2025-2026 production systems. Snap Inc.'s Agent Format (.agf.yaml) open-sourced in 2026.
- **Evidence quality:** Credible (PydanticAI, Google ADK, OpenAI documentation); Verified (Anthropic's own system architecture published June 2025).
- **Temporal check:** Current. All references are 2025-2026. Snap's .agf.yaml is 2026.
- **Conflicts with existing project research?** No — reinforces existing `AgentDefinition` model in `src/keystone/`. The shape is already correct.
- **Verdict:** ADOPT
- **Justification:** The existing `AgentDefinition` model already has the right fields; the only gap is that the Specification Engine treats it as a downstream artifact of enum selection rather than as the primary unit of configuration.
- **Keystone impact:** Component #5 (Specification Engine L0), Component #7 (Research Agent pipeline L1). Settled Decision #8 (protocol-based contracts) is reinforced — configs are protocols, not class hierarchies.
- **Contradicts:** None. Directly validates Jack Directive #1.

---

### 2. Anthropic's own research system: dynamic subagent spawning with complexity-scaled rules

- **What:** Anthropic's multi-agent research system (published June 2025) spawns subagents as dynamically generated configurations, not predefined types. The LeadResearcher (Opus 4) uses extended thinking to generate each subagent's objective, output format, tools, and task boundaries on the fly. Complexity-scaled spawning: 1 agent for simple fact-finding, 2-4 for direct comparisons, 10+ for complex research (max 20). Default is 3.
- **Evidence basis:** Anthropic published architecture, June 2025.
- **Evidence quality:** Verified (Anthropic first-party documentation of production system).
- **Temporal check:** Current. June 2025.
- **Conflicts with existing project research?** No — extends and validates the current plan's approach to L0->L1 dispatch.
- **Verdict:** ADOPT
- **Justification:** This is the closest architectural analog to Keystone, published by Anthropic themselves, and maps directly onto our L0 (Opus orchestrator) -> L1 (parallel research agents) structure — the complexity-scaled spawning rules give a concrete calibration table for the Specification Engine.
- **Keystone impact:** Component #5 (Specification Engine L0), Component #7 (Research Agent pipeline L1). Informs the spawning logic in `research-tasks.json`.
- **Contradicts:** Challenges the current plan's framing of 5 fixed `ResearchAgentType` enum values as the dispatch unit — they should be seed templates, not the dispatch mechanism.

---

### 3. Token usage explains 80% of performance variance — not architecture

- **What:** In Anthropic's evaluations, token usage alone explained 80% of performance variance. Multi-agent configurations use ~15x more tokens than single chat interactions. This means the Specification Engine's decision about how many agents to spawn and with what token budgets is the primary quality and cost lever — more important than any specific agent configuration pattern.
- **Evidence basis:** Anthropic's multi-agent research system evaluation, June 2025.
- **Evidence quality:** Verified (first-party Anthropic empirical result from production system).
- **Temporal check:** Current.
- **Conflicts with existing project research?** Partially. The existing CAPSTONE-PLAN-v2.md focuses heavily on agent type architecture; this finding shifts weight toward token budget calibration as the dominant performance variable.
- **Verdict:** ADOPT
- **Justification:** The Specification Engine's most critical function is effort calibration (how many agents, what token budgets) — architectural sophistication of agent configs is secondary to getting the scaling rules right.
- **Keystone impact:** Component #5 (Specification Engine L0). Directly affects cost target ($12-$100 per engagement) — token scaling rules must be built into L0 from Day 1, not tuned later.
- **Contradicts:** Implicitly challenges excessive focus on agent type sophistication before token budget governance is solved. The architecture can be simpler than feared if token allocation is right.

---

### 4. Tool assignment as hard constraint vs. system prompt as soft guidance

- **What:** Tool restriction is a hard behavioral constraint; prompt instruction is soft guidance that models may ignore under pressure (GitHub Copilot architecture finding, validated by MAST study). An agent with read-only tools literally cannot edit files; an instruction not to edit files can be disobeyed. The `tools[]` assignment in an AgentDefinition is the primary enforcement mechanism for agent behavior boundaries.
- **Evidence basis:** GitHub Copilot architecture (production system, 2025); MAST framework analysis of 1,642 execution traces across 7 frameworks (ICLR 2025).
- **Evidence quality:** Credible (GitHub Copilot is a production system at scale); Verified (MAST is peer-reviewed empirical analysis).
- **Temporal check:** Current. ICLR 2025, GitHub Copilot production system.
- **Conflicts with existing project research?** Reinforces Settled Decision #5 (agent isolation via filesystem-based per-agent working directories, 3-5 tools per agent). The 3-5 tool limit is now grounded in more than operational simplicity — it is the primary behavioral governance mechanism.
- **Verdict:** ADOPT
- **Justification:** Every research agent's tool set must be treated as its behavioral contract, not as a convenience configuration — this has direct implications for how the Specification Engine assigns tools when generating custom agent configs.
- **Keystone impact:** Component #5 (Specification Engine L0), Component #7 (Research Agent pipeline L1), Component #4 (MCP gateway — gateway becomes the enforcement point for tool whitelisting). Settled Decision #5 is strengthened.
- **Contradicts:** None. Amplifies rather than contradicts existing decisions.

---

### 5. Tighten-only constraint invariant for dynamic agent hierarchies

- **What:** When an orchestrator delegates to subagents, constraints can only become more restrictive, never less. If the orchestrator has 20 tools, a subagent gets at most 20 (typically fewer). If the orchestrator has a 50,000-token budget, subagents inherit that ceiling. Borrowed from Snap's .agf.yaml (2026). Prevents privilege escalation in dynamically generated hierarchies.
- **Evidence basis:** Snap Inc. Agent Format (.agf.yaml), open-sourced 2026. Grounded in POMDP theory.
- **Evidence quality:** Credible (Snap is a production system at scale; .agf.yaml 2026 publication is recent).
- **Temporal check:** Current. 2026.
- **Conflicts with existing project research?** No — fills a governance gap in the current plan, which specifies agent isolation but does not specify a propagation rule for constraints in dynamic hierarchies.
- **Verdict:** ADOPT
- **Justification:** A single enforceable invariant that prevents the primary failure mode of dynamic generation (privilege escalation, budget overrun) — this should be built into the `AgentDefinition` schema validation from Phase 1.
- **Keystone impact:** Component #5 (Specification Engine L0), Component #7 (Research Agent pipeline L1). Should be encoded in the `AgentDefinition` Pydantic model as a validated constraint.
- **Contradicts:** None.

---

### 6. Template registry pattern: seed templates + dynamic generation + promotion loop

- **What:** Replace fixed enums with a registry of `AgentTemplate` objects (base system prompt, default tool set, output schema, evaluation rubric, constraint set). The Specification Engine first attempts semantic similarity matching against the registry (threshold ~0.85). Above threshold: instantiate the template with task-specific variable interpolation. Below threshold: generate a custom `AgentDefinition` from scratch, constrained by structural validation and the tighten-only invariant. When a dynamically generated config performs well, it is promoted to the registry as a new named template.
- **Evidence basis:** Synthesis across Anthropic (June 2025), Google ADK, CrewAI, Snap .agf.yaml (2026). Two-tier classification is the report's own framework derived from these sources.
- **Evidence quality:** Credible (drawn from multiple production systems; the specific synthesis and threshold recommendation are the report's own framework, not empirically validated).
- **Temporal check:** Current.
- **Conflicts with existing project research?** No — directly implements Jack Directive #1. The report's three-phase roadmap (Phase 1: parameterize existing types; Phase 2: registry + dynamic generation; Phase 3: promotion loop + skill loading) is a practical staging of the directive.
- **Verdict:** ADAPT
- **Justification:** The architecture is right; the 0.85 similarity threshold is a reasonable starting point but will require empirical calibration — adopt the pattern, treat the threshold as a tunable hyperparameter not a fixed design spec.
- **Keystone impact:** Component #5 (Specification Engine L0), Component #7 (Research Agent pipeline L1), Component #9 (Basic Deliberation L1.5 — applies equally to the 5 fixed deliberation analyst types). Jack Directive #1 fully validated and given a concrete implementation path.
- **Contradicts:** None.

---

### 7. Microsoft Azure SRE Agent: collapse from 50+ specialized agents to a handful of generalists

- **What:** Azure SRE started with 100+ tools and 50+ specialized sub-agents. They ended with 5 core tools and a handful of generalists. Problems requiring more than 4 handoffs almost always failed. Failure modes: discovery problems, system prompt fragility, infinite loops, tunnel vision. Their conclusion: they had built "a workflow with an LLM stapled on." Domain knowledge was moved from rigid system prompts into files agents could read on demand.
- **Evidence basis:** Microsoft Azure SRE team production case study (2025).
- **Evidence quality:** Credible (Microsoft production system; no specific paper citation, but described as a team's retrospective on a deployed production system).
- **Temporal check:** Current. 2025.
- **Conflicts with existing project research?** Partially. The current plan specifies 5 research agent types + 5 deliberation analyst types, which is within the safe zone the study implies, but the Contrarian and Historical Analogy types are at risk of "tunnel vision" if their system prompts are too rigid.
- **Verdict:** ADAPT
- **Justification:** The 4-handoff failure threshold is a hard operational constraint; the on-demand knowledge loading pattern (Jack Directive #8 — Karpathy's compiled markdown wikis) is directly validated by this case study.
- **Keystone impact:** Component #7 (Research Agent pipeline L1), Component #9 (Basic Deliberation L1.5). Validates Jack Directive #8. The 4-hop limit implies the L0 -> L1 -> CitationProcessor -> L1.5 -> L2 chain must be monitored — that is already 4 handoffs before L3 Generation.
- **Contradicts:** None on architecture; implicitly cautions against over-specialization in deliberation analyst types.

---

### 8. Google DeepMind scaling study: coordination gains plateau beyond 4 agents, -70% on sequential tasks

- **What:** Testing 180 configurations, Google DeepMind found: +81% improvement on parallelizable tasks, up to 70% degradation on sequential tasks, coordination gains plateau beyond 4 agents, error amplification reaches 17.2x in poorly structured networks. The saturation threshold is 4 agents for coordination gains.
- **Evidence basis:** Google DeepMind scaling study, December 2025.
- **Evidence quality:** Credible (DeepMind research lab; published December 2025, no specific conference venue cited in the report).
- **Temporal check:** Current. December 2025.
- **Conflicts with existing project research?** Reinforces the existing architecture's parallel research model (L1 is parallel, read-heavy) and the deliberation structure (L1.5 is parallel analysis). Raises a yellow flag on agent counts above 4-5 for coordination-heavy stages.
- **Verdict:** ADOPT
- **Justification:** The 4-agent coordination plateau should inform the Specification Engine's default and maximum agent counts — the current "3-5 agents, tier up organically" target in CLAUDE.md is well-calibrated against this finding.
- **Keystone impact:** Component #5 (Specification Engine L0) — validates the 3-5 agent default. Deployment Context section of CLAUDE.md is confirmed. Error amplification finding (17.2x) supports the need for the CitationProcessor as a validation stage between L1 and L1.5.
- **Contradicts:** None. Validates existing plan's parallelism strategy.

---

### 9. MAST framework: 41%-86.7% failure rates, coordination breakdowns = 36.9% of failures

- **What:** Analysis of 1,642 execution traces across 7 open-source frameworks found failure rates from 41% to 86.7%. Coordination breakdowns were the largest failure category at 36.9%. "Disobeying role specification" was a primary failure mode. The finding: too-rigid roles create brittleness; too-loose roles create coordination chaos.
- **Evidence basis:** MAST framework, ICLR 2025 (peer-reviewed).
- **Evidence quality:** Verified (peer-reviewed, 1,642 traces is substantial empirical basis).
- **Temporal check:** Current. ICLR 2025.
- **Conflicts with existing project research?** Consistent with the existing UNIFIED-SYNTHESIS concern about agent isolation and the LEAK-SYNTHESIS findings. The 36.9% coordination failure rate validates the CitationProcessor as a mandatory intermediate stage.
- **Verdict:** ADOPT
- **Justification:** The failure rate range (41-86.7%) should be treated as the baseline risk for any multi-agent system — Keystone's evaluator and structural validation exist precisely to catch these failures before they propagate.
- **Keystone impact:** Component #6 (Evaluator L4 Layers 1-3), Component #8 (CitationProcessor). Validates the five-layer evaluator stack as non-optional. The 29-30% false claim rate from CLAUDE.md's empirical anchors now has corroborating structural failure data.
- **Contradicts:** None.

---

### 10. DyLAN / X-MAS / MetaAgent: dynamic configuration accuracy gains on research tasks

- **What:** DyLAN (ICLR 2024): +25% accuracy on MMLU vs. fixed teams. X-MAS: +8.4% on MATH, +47% on AIME via role-wise LLM assignment. MetaAgent: 97% of best human-designed system performance, 50% more checkpoints on software development — via automatic multi-agent design from finite state machines.
- **Evidence basis:** DyLAN (ICLR 2024); X-MAS (paper, date not specified in report); MetaAgent (paper, date not specified in report).
- **Evidence quality:** Credible (ICLR peer-reviewed for DyLAN; X-MAS and MetaAgent dates not specified — treat as credible but not verified until dated).
- **Temporal check:** DyLAN is 2024 — still current for architectural guidance. X-MAS and MetaAgent: unknown dates, flag as potentially stale.
- **Conflicts with existing project research?** No. Consistent with the 90.2% improvement finding from Anthropic's own research system.
- **Verdict:** INVESTIGATE
- **Justification:** The accuracy gains are real and the direction is clear, but X-MAS and MetaAgent need date verification before treating as current — the core finding (dynamic > fixed for parallel research tasks) is already validated by stronger evidence (Anthropic's own system).
- **Keystone impact:** Marginal — the stronger Anthropic evidence already settles this question. These papers would be useful citations in documentation but don't change the architecture.
- **Contradicts:** None.

---

### 11. LLM-as-judge evaluation for dynamically generated agents with generated rubrics

- **What:** For agents without pre-calibrated benchmarks, the evaluation rubric itself can be generated from the agent's task description. Each dimension gets its own LLM-as-judge prompt (not a single aggregate grader). Google Cloud bootstrapping path: human evaluation -> binary Pass/Fail scores -> LLM-as-judge automation -> golden dataset accumulation.
- **Evidence basis:** Anthropic evaluation guidance (2025); Google Cloud bootstrapping pattern (2025).
- **Evidence quality:** Credible (Anthropic first-party guidance; Google Cloud documentation).
- **Temporal check:** Current. 2025.
- **Conflicts with existing project research?** Consistent with the existing 10-dimension rubric in the Evaluator. Extends it: the rubric can be dynamically generated for novel agent types, not only applied from a fixed template.
- **Verdict:** ADAPT
- **Justification:** Adopt the generated rubric approach for dynamically configured agents; the existing 10-dimension rubric applies to the overall deliverable (L4), while this mechanism applies at the agent-output level within L1 — these are distinct evaluation layers and should not be conflated.
- **Keystone impact:** Component #6 (Evaluator L4 Layers 1-3). Also feeds into Component #9 (Basic Deliberation L1.5) — the critic step in deliberation can use generated rubrics for novel analyst types.
- **Contradicts:** None.

---

### 12. Progressive skill loading vs. monolithic system prompts

- **What:** Domain expertise (M&A knowledge, market sizing methodologies, industry frameworks) should live as loadable skill files referenced by agent definitions, not hardcoded into system prompts. This is the pattern Microsoft Azure SRE adopted after failure with rigid system prompts. Google ADK implements it as a three-tier pattern.
- **Evidence basis:** Microsoft Azure SRE case study (2025); Google ADK (2025).
- **Evidence quality:** Credible (both production systems).
- **Temporal check:** Current. 2025.
- **Conflicts with existing project research?** Directly validates Jack Directive #8 (Karpathy's compiled markdown wikis, embeddings only for initial source discovery).
- **Verdict:** ADOPT
- **Justification:** Jack Directive #8 is confirmed by two independent production case studies; the skill loading architecture should be built into the Phase 1 `AgentDefinition` schema as a `skills: list[SkillRef]` field, even if skill library population is deferred to later phases.
- **Keystone impact:** Component #5 (Specification Engine L0), Component #7 (Research Agent pipeline L1). Jack Directive #8 is validated.
- **Contradicts:** None.

---

## Architectural Decisions This Enables

**1. Replace `ResearchAgentType` and `DeliberationAnalystType` enums with a template registry.**
The existing 10 agent types (5 research + 5 deliberation) become seed templates in the registry. The Specification Engine queries the registry first; below the similarity threshold, it generates a custom `AgentDefinition`. No code change to the `AgentDefinition` model itself — the shape is already correct. The change is in how the Spec Engine produces them.

**2. Tighten-only invariant as a schema-level constraint.**
The `AgentDefinition` Pydantic model should include a `parent_constraints: Optional[AgentConstraints]` field. Schema validation enforces that child `constraints` are a subset of parent `constraints`. This is a compile-time guarantee, not a runtime hope.

**3. Tool assignment as the primary behavioral governance mechanism.**
The MCP gateway (Component #4) becomes the enforcement point for tool whitelisting. The Specification Engine's tool assignment logic is the critical path for agent behavioral control — not the system prompt content. Tool set selection for dynamically generated agents must be explicit and validated, not inferred.

**4. Complexity-scaled spawning table in the Specification Engine.**
Concrete calibration table from Anthropic's system (applicable to Keystone):
- Simple fact-finding: 1 agent, 3-10 tool calls
- Direct comparisons: 2-4 subagents, 10-15 calls each
- Complex research: up to 10 subagents (Keystone ceiling: 5 for Phase 1, expandable)
- Default: 3 subagents

**5. Four-handoff ceiling as an architectural constraint.**
The L0 -> L1 -> CitationProcessor -> L1.5 -> L2 chain is already at 4 handoffs. This means the pipeline must be treated as at the coordination complexity ceiling. Adding additional stages or nesting within stages requires explicit justification against the Microsoft failure data.

**6. Template promotion loop as a Phase 3 target.**
When dynamic agent configs score above a quality threshold (evaluator + human feedback), they are promoted to named templates in the registry. This is the flywheel that makes the system self-improving without requiring explicit human curation of every new agent type.

---

## Changes to Existing Plan

### CAPSTONE-PLAN-v2.md changes

**Section: Research Agents (L1) — 5 fixed types**
Current: `ResearchAgentType(Enum)` with values Quantitative, Qualitative, Contrarian, Historical Analogy, Internal Document.
Required change: Convert to seed templates in a template registry. The enum values become template IDs, not dispatch values. The Specification Engine queries the registry, not the enum.

**Section: Specification Engine (L0) — 4-step verification, research-tasks.json dispatch**
Current: Dispatch produces a `research-tasks.json` that references agent types by enum value.
Required change: Dispatch produces `AgentDefinition` objects (already the right model shape) with the spawning decision logged: template match (with similarity score) or dynamic generation (with validation report). Add complexity-scaled spawning table as a calibration constraint.

**Section: Deliberation (L1.5) — 5 fixed deliberation analyst types**
Same change as L1: the 5 analyst types (ACH, Quantitative, Adversarial, Historical, Scenario) become seed templates, not fixed dispatch values. The aggregation step can request custom analyst types for novel engagement structures.

**Section: Token budget governance (not currently explicit in plan)**
Required addition: Token budget allocation must be explicit in the Specification Engine's output, not left implicit. The 80% performance variance finding means token budget per agent is as important as agent configuration. Add a `token_budget: int` field to `AgentDefinition` with the tighten-only invariant applied.

### Component-level changes (Phase 1 Implementation)

**Component #5 (Specification Engine L0) — marked as Large:**
Phase 1 scope must include the template registry (even if it only contains the 10 seed templates initially) and the two-path dispatcher logic. Generating fully custom `AgentDefinition` objects from scratch can be Phase 2, but the registry query + template interpolation path must be Phase 1. The `AgentDefinition` schema should include `parent_constraints`, `skills: list[SkillRef]`, and `token_budget` fields.

**Component #7 (Research Agent pipeline L1) — marked as Large:**
Tool assignment logic must be treated as the primary behavioral governance mechanism, not system prompt design. The agent loop should validate tool assignments against the tighten-only invariant before spawning.

**Component #4 (MCP gateway — marked as Medium):**
The gateway is the enforcement point for tool whitelisting. The two-path dispatcher in L0 must produce tool lists that the gateway can validate and enforce — this is a coordination requirement between Component #4 and Component #5 that is not currently explicit in the plan.

### Jack's Directives — Validation

**Directive #1 (The Rigidity Problem):** Fully validated. The report provides a concrete three-phase implementation path and empirical evidence that dynamic configuration outperforms fixed types on parallel research tasks. No modification needed to the directive.

**Directive #8 (Karpathy's LLM Knowledge Bases):** Validated by two independent production case studies (Microsoft Azure SRE, Google ADK). Skill loading architecture should be scaffolded in Phase 1 even if skill library population is deferred.

**Directive #3 (Iterative Multi-Round Research):** Not directly addressed by this report. The template registry pattern supports iterative research (subsequent rounds can spawn different agent configurations based on what was learned), but the iterative loop architecture itself is not covered here. This remains an open architectural gap for Report 10 (Spec Engine) to address.

**Directive #7 (Human-in-the-Loop Gates):** The report's recommendation for human evaluation in the bootstrapping phase (human eval -> binary scores -> LLM-as-judge) implicitly validates the human-in-the-loop approach but does not address the gate placement (after issue tree, after confidence map). No change needed to the directive.

**Directive #9 (Component #3 Over-Engineering Concern):** Not relevant to this report.

---

## Open Questions Remaining

1. **Similarity threshold calibration:** The 0.85 template matching threshold is a reasonable starting point but entirely uncalibrated for consulting research tasks. What is the actual false positive/negative rate at this threshold? This needs empirical measurement from the first real engagements — cannot be set a priori.

2. **Template registry storage:** Should the template registry be a structured database (pgvector for semantic search, Component #3) or a flat file store of Pydantic models? The report implies semantic similarity matching against template descriptions — this may require pgvector to be involved earlier than planned, or an alternative similarity mechanism must be specified.

3. **Generated rubric quality:** The report recommends generating evaluation rubrics from agent task descriptions for novel agent types. Who validates the generated rubric itself? A meta-evaluator? This is a second-order quality problem that is not resolved in the report and needs an architecture decision before Phase 2.

4. **Skill loading JIT vs. eager:** The skill loading pattern is recommended but the loading timing is unspecified. Should skills be loaded into context before the agent starts (eager) or requested by the agent during its task (JIT via tool call)? JIT is more token-efficient; eager is more predictable. The existing plan's JIT context pattern (noted in CLAUDE.md) implies JIT, but the interaction with the tighten-only invariant (does loading a skill grant the agent capabilities?) needs resolution.

5. **Template promotion criteria:** What evaluation score threshold triggers promotion from dynamic configuration to named template? How many successful executions are required? The report describes the promotion loop conceptually but provides no calibration data. This needs a policy decision before Phase 3.

6. **Four-handoff ceiling and the existing pipeline:** The pipeline is already at 4 handoffs (L0 -> L1 -> CitationProcessor -> L1.5 -> L2). The META layer and L3/L4 add more. Does the Microsoft finding apply to handoffs within a single engagement or to the overall pipeline depth? If it applies to pipeline depth, the architecture is at the edge of the safety zone and any additional nesting (e.g., nested deliberation rounds) requires explicit risk assessment.

7. **Cross-report dependency — Report 05 (engagement taxonomy):** The template registry's seed templates should be organized around engagement taxonomy categories. This analysis assumes the current 10 agent types are adequate seeds, but Report 05 may reveal engagement types that require fundamentally different agent configurations not covered by the existing types. The template registry design should be finalized only after Report 05 is analyzed.

8. **Cross-report dependency — Report 10 (Spec Engine):** The two-path dispatcher logic (template match vs. dynamic generation) is the core function of the Specification Engine. This report defines the architecture but not the Spec Engine's internal implementation. Report 10 must specify how the orchestrator LLM (Opus) is prompted to generate valid `AgentDefinition` objects, how structural validation is integrated into the generation loop, and how the spawning decision is logged for observability.
