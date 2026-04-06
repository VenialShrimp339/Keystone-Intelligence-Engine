# Change Specification A — Sections 3 & 4 (Changes #1–22)
*Track 1 Session | Produced 2026-04-05 | Subagent A*
*Source authority: JACK-ARCHITECTURAL-DIRECTIVES.md (14 directives) + MASTER-SYNTHESIS.md Section 9 + CAPSTONE-PLAN-v2.md*

---

## Preamble: Integration Strategy

The 22 changes below are surgical additions to an existing document with a mature prose voice. They are not a wholesale rewrite. Key integration decisions:

**Section 3 restructuring:** The current §3 has subsections 3.1–3.7. The 10-step pipeline described in Change #1 consolidates and extends the current §3.4 (Specification Verification Phase, 4 steps) and §3.5 (Iterative Specification Refinement, scout/strike) into a unified 10-step flow. The existing prose in 3.1–3.3 and 3.6–3.7 is largely preserved. The replacement content targets §3.4 and §3.5, which are replaced, and §3.6, which receives significant additions. New subsections §3.8 and §3.9 are added.

**Section 4 restructuring:** The current §4 has subsections 4.1–4.4. Changes #11–22 add new subsections §4.5 and §4.6 and make targeted surgical modifications to §4.1, §4.2, and §4.3. The confidence map JSON and deliberation prose in §4.3 receive the most changes.

**Tag discipline:**
- `[SYNTHESIS UPDATE]` — existing tag for v1→v2 changes; do not remove any existing instances
- `[BATCH 2 UPDATE]` — new tag for all content added in this update cycle

---

## Change #1: Replace 7-Step Flow with 10-Step Flow

**MASTER-SYNTHESIS Reference:** Section 9, Change #1
**Phase Classification:** [Phase 1] — the 10-step pipeline is the correct architecture at full depth
**Phase Rationale:** Directive 13 explicitly ships issue tree decomposition (Step 3), MECE verification (Step 4), and engagement classifier (Step 1) in Phase 1. Steps 2, 6, 7, 9, and 10 are structurally required for correct data flow (Directive 5: "right interfaces, right data flow"). No step in the 10-step flow can be deferred without changing the handoff contracts between steps. Steps containing Phase 2 features (VOI scoring in Step 5, CBR query in Step 1) are handled within those individual change specs (#7 and #8) with the appropriate deferral markings.
**Location in CAPSTONE-PLAN-v2.md:** Section 3, subsections §3.4 and §3.5, lines 197–217

### What exists now:
```
### 3.4 Specification Verification Phase

Before Research Agents execute, the Specification Engine runs a four-step verification phase — a new architectural component not present in v1:

1. **Intent Clarification:** "Is this the right question? Does this decomposition capture the client's actual decision?" The Specification Engine can request clarification from the human operator if the research question is underspecified.

2. **Pre-Flight Scope Validation:** A lightweight "scout" pass where Research Agents confirm the question is correctly framed for their vertical. A market-sizing agent might flag that the requested geography doesn't match available data sources.

3. **Fit Assessment:** Identify upfront whether the question is inside or outside the system's competence frontier. BCG's data showed that AI used outside its capability frontier makes outcomes 19 points WORSE — not neutral, actively harmful (Jones, "201 Skills / 95% Stall," Jan 25, 2026). The system must know where its own frontier is and refuse to proceed outside it.

4. **Specification Quality Threshold:** The decomposition must meet a minimum quality bar before any agent spawns. Criteria include: decision context specified, acceptance criteria testable, source requirements achievable, non-goals explicit. This prevents the most expensive failure mode: burning compute on a poorly-specified question.

### 3.5 Iterative Specification Refinement

The specification shouldn't be a single pass. Drawing from the "scout/strike" model (Jones, "10x Output," Mar 8, 2026):

**Generate spec → preliminary scout research → refine spec → full strike research**

Phase 1 is *scout*: broad exploration with tolerance for dead ends. Research Agents investigate the landscape and report back on what questions are well-formed and which need reformulation. Phase 2+ is *strike*: focused execution based on scout findings. The Specification Engine adapts the RESEARCH.md between phases based on what the scouts discovered.

This mirrors how the best consulting engagements actually work: the first week's research often reveals that the original question was slightly wrong, and the team pivots before the second week's deep-dive.
```

### What it should say:
```
### 3.4 The 10-Step Specification Pipeline

`[BATCH 2 UPDATE]` The Specification Engine is now fully specified as a 10-step pipeline. Three independent evidence paths — consulting methodology (Report 03), AI planning research (Report 05), and production system analysis (Report 10) — converge on the same structural additions. This replaces the prior four-step verification phase and scout/strike framing with a unified flow from problem receipt to research execution.

**Step 1 — Problem Framing and Classification:** The Specification Engine classifies incoming queries using a 5-type engagement taxonomy (SIZING, DIAGNOSTIC, EVALUATIVE, EXPLORATORY, STRATEGIC) based on five signals: specificity of deliverable, presence of testable hypothesis, known analytical framework, scope boundedness, and decision type. This classification drives pipeline profile selection (Light / Standard / Deep) per Directive 11 and routes the engagement to the appropriate evaluation weight profile. The Observation Library is queried at this step via CBR Retrieve to seed the hypothesis space with patterns from prior engagements. [See Change #2 for the full taxonomy; see Change #8 for the CBR query, which is Phase 2.]

**Step 2 — Intent Clarification:** "Is this the right question? Does this decomposition capture the client's actual decision?" Intent clarification uses a Decision-First Chain-of-Thought — a 5-step structured prompt that asks: (1) What decision does this research inform? (2) What would a surprising finding look like? (3) What constraints aren't stated? (4) What evidence would change the client's mind? (5) What is explicitly out of scope? LLMs score only 25% on pragmatic inference without structured prompting (CEI benchmark, March 2026), making this structured clarification protocol essential rather than optional. The Specification Engine requests operator input when the research question is underspecified. [See Change #3 for TiCoder divergence detection layered onto this step, which is Phase 2.]

**Step 3 — Issue Tree Decomposition:** Three to four Sonnet agents with distinct consulting lenses (financial, operational, market/competitive; optionally regulatory/risk for complex engagements) independently construct shallow issue trees at 2–3 levels of depth. Each agent uses hypothesis-driven branch framing, Plan-and-Solve + Skeleton-of-Thought prompting, and 2–3 curated MECE exemplars derived from casing materials. Pydantic models enforce reasoning-first field ordering. The shallow start — targeting 8–20 leaf nodes — is deliberate: ADaPT-style adaptive deepening occurs during research when agents report complexity, not upfront. This reduces human review burden and avoids the deep-upfront-planning failure mode (+28.3% improvement from shallow-then-adaptive, ADaPT, 2025). [See Change #4 for the full multi-lens specification.]

**Step 4 — Decomposition Validation:** A discrete MECE verification step using Opus as evaluator. Five dimensions are checked with atomic binary criteria: mutual exclusivity, collective exhaustiveness, tailoring to the specific engagement context, actionability (can research agents execute against each branch?), and depth appropriateness. Programmatic semantic similarity checks (cosine similarity on branch embeddings) complement the LLM judge for mutual exclusivity detection. Trees failing verification trigger regeneration, not escalation. [See Change #5 for the full MECE verification specification.]

**Step 5 — Priority Assignment:** Issue tree branches are scored and ranked by priority. The full architecture uses a VOI-inspired formula — `(decision_relevance × current_uncertainty) / estimated_cost` — with multi-signal prioritization (sampling consistency, feasibility estimation, structured rubric). Priority is a working hypothesis, not a commitment: reprioritized each research cycle as findings accumulate. [Phase 1 implementation note: see Change #7 for phasing details.]

**Step 6 — Dynamic Agent Configuration:** The engagement type from Step 1 drives a template registry query (see Change #14, #15). Above 0.85 similarity to an existing seed template: instantiate with task-specific interpolation. Below threshold: generate a custom AgentDefinition constrained by structural validation and the tighten-only invariant (see Change #16). Token budget is set per agent at this step; token usage explains 80% of performance variance in Anthropic's multi-agent system (Anthropic, multi-agent production analysis, 2026). [See Changes #16 and #17 for tighten-only and token budget specification.]

**Step 7 — Task Generation:** Decomposition produces a `research-tasks.json` file with DAG dependency structure (not flat list), anti-confirmatory framing per task, per-branch "end product" specification (specific chart type, table structure, conclusion format), and the priority score as a computed field. [See Changes #9 and #10 for DAG structure and end-product specification.]

**Step 8 — Human Review Gate:** Non-negotiable (Directive 7). The human reviews: the issue tree, divergence points from the decomposition phase, the sprint contract proposed by the Evaluator, and the agent configurations. Phase 1 implementation: database state machine (PostgreSQL, 3 tables, REST API, web UI) with approve / modify / reject flows. Maps to Temporal Signals in Phase 2 with no agent code changes required.

**Step 9 — Research Execution (Scout Phase):** The Day-1 Hypothesis (see Change #6) anchors the scout phase. Research begins with a ~70/30 exploration-to-exploitation ratio that shifts to ~20/80 as knowledge accumulates across rounds. The scout phase feeds directly into the iterative research loop (see Change #11). The Specification Engine adapts the RESEARCH.md between rounds based on what scouts discover — a direct continuation of the prior scout/strike insight, now mechanically specified rather than aspirationally described.

**Step 10 — Feedback Loop:** Completed research findings feed back into issue tree refinement and task reprioritization. Completed tasks are immutable. Only pending tasks can be modified. Three replanning cycles maximum. This closes the loop from the iterative research specification (Change #11) back to the Specification Engine's state, enabling the system to be genuinely self-correcting without the AutoGPT infinite-loop failure mode (Day-1 Hypothesis as termination anchor).

The 10-step flow replaces the prior four-step verification phase (§3.4) and scout/strike framing (§3.5) with a unified pipeline. The fit assessment and scope validation concepts from the prior §3.4 are absorbed into Steps 2 and 6, respectively. The specification quality threshold from Step 4 of the old flow is absorbed into Step 4 (MECE verification) and Step 7 (task generation quality bar). Nothing substantive is lost; the architecture is more complete.
```

### Preservations:
- The existing prose in §3.1, §3.2, §3.3, §3.6, and §3.7 must not be changed by this update.
- The existing `[SYNTHESIS UPDATE]` tags throughout §3.6 must be preserved.
- The BCG 19-points-worse citation must be preserved; it should be referenced from Step 2 (fit assessment is now part of intent clarification) rather than removed.

### Cross-section references:
- The RESEARCH.md format in §3.2 will need additions for the Day-1 Hypothesis field, engagement type, and max_rounds override (addressed by Change #6 and in section changes owned by other tracks, but noted here for orchestrator awareness).
- The handoff contracts table in §2 will need a row update for the Specification Engine boundary (orchestrator to handle).

### Directive compliance:
- Directive 2 (MECE Issue Tree): Steps 3 and 4 implement the casing phase as specified.
- Directive 3 (Iterative Multi-Round Research): Steps 9 and 10 resolve the architectural gap.
- Directive 5 (Build Philosophy): Correct interfaces at full architectural depth; feature sophistication staged per Changes #7 and #8.
- Directive 7 (Human-in-the-Loop): Step 8 is non-negotiable gate per directive.
- Directive 11 (Configurable Pipeline Depth): Step 1 classification drives profile selection.
- Directive 13 (Phase 1 Depth Staging): Steps containing Phase 2 features are marked in subordinate change specs.

---

## Change #2: Add Engagement Type Classifier (5-Type Taxonomy)

**MASTER-SYNTHESIS Reference:** Section 9, Change #2
**Phase Classification:** [Phase 1]
**Phase Rationale:** Directive 13 explicitly lists "Engagement classifier (routes to pipeline profile)" as a Phase 1 ship item. Without the classifier, the configurable pipeline depth (Directive 11) cannot function — the system has no mechanism to select Light vs. Standard vs. Deep profile.
**Location in CAPSTONE-PLAN-v2.md:** Section 3, as a new subsection §3.8 added after §3.7 (line ~305, after the Task-vs-Job table)

### What exists now:
Section 3 ends at §3.7 (The Task-vs-Job Boundary). No engagement classifier exists.

### What it should say:
```
### 3.8 Engagement Classification and Pipeline Profile Selection

`[BATCH 2 UPDATE]` Before any issue tree construction or research decomposition begins, the Specification Engine classifies the engagement using a 5-type taxonomy. Reports 05 and 10 converge on this classification through independent evidence paths (consulting methodology research and production system analysis, respectively). The classification drives pipeline profile selection, evaluation weight profiles, and template registry queries.

**The 5-Type Analytical Taxonomy:**

| Type | Definition | Signals | Example |
|------|------------|---------|---------|
| **SIZING** | Estimate the magnitude of a market, phenomenon, or resource | Deliverable is a number with uncertainty range; bottom-up and top-down required | "How large is the L4+ AV sensor market in North America by 2030?" |
| **DIAGNOSTIC** | Identify root causes of a known problem | Testable hypothesis present; causal chain analysis required | "Why is Company X's gross margin declining despite revenue growth?" |
| **EVALUATIVE** | Assess options against defined criteria | Decision alternatives enumerable; comparative framework applicable | "Should Keystone advise Target A or Target B for the M&A mandate?" |
| **EXPLORATORY** | Map an unfamiliar landscape without a predetermined hypothesis | Scope deliberately open; discovery-oriented research mode | "What are the structural dynamics of the contract logistics market in Southeast Asia?" |
| **STRATEGIC** | Synthesize multiple analytical modes into a recommendation | Multiple sub-tasks spanning SIZING + DIAGNOSTIC + EVALUATIVE | "Evaluate the competitive position of Company X and recommend a response strategy" |

**Classification signals (five, evaluated in order):**
1. Specificity of deliverable — is the output format enumerable upfront?
2. Presence of testable hypothesis — does the client have a prior belief to validate or challenge?
3. Known analytical framework — does an established methodology (DCF, market sizing, Porter's Five Forces) map directly?
4. Scope boundedness — can the research domain be defined in advance?
5. Decision type — operational (specific, near-term) vs. strategic (directional, multi-horizon)?

An engagement may map to multiple types; the Specification Engine uses the primary type for pipeline routing and retains secondary types for evaluation profile blending.

**Pipeline Profile Selection:**

| Profile | Issue Tree | Agents | Rounds | Eval Stack |
|---------|------------|--------|--------|------------|
| **Light** | None | 1–2 agents | 1 round | Layers 1–2 only |
| **Standard** | Simplified (single agent, 1–2 levels) | 3 agents | 2–3 rounds | Layers 1–3 |
| **Deep** | Full MECE decomposition (3–4 agents, 2–3 levels) | Up to 5 agents | Up to 5 rounds | Full stack |

The engagement classifier recommends a profile; the operator can override up or down via the control panel (Directive 11). SIZING and DIAGNOSTIC engagements with bounded scope typically route to Standard. STRATEGIC and complex EVALUATIVE engagements route to Deep. EXPLORATORY engagements with a defined timeframe route to Standard; with open-ended scope, to Deep.

Note: Report 05 identified a parallel 10-category domain taxonomy (Corporate Strategy, Operations, M&A, Restructuring, etc.) that describes the *subject matter* of the engagement rather than its analytical mode. The 5-type taxonomy is used for pipeline routing; the domain taxonomy feeds the Observation Library retrieval (similar past engagements) and framework selection. Both are implemented in `engagement_classifier.py`; they are orthogonal, not competing.
```

### Preservations:
- §3.7 (Task-vs-Job Boundary) and its table must not be changed.
- Section numbering of subsequent sections may need to shift if §3.8 pushes §3.7 to renumber; however, §3.7 is the last subsection of §3, so no renumbering is required.

### Cross-section references:
- §2 (Architecture Overview) handoff contracts table: the Specification Engine row should note the engagement type as part of the RESEARCH.md output.
- §5 (Evaluator) references evaluation profiles that depend on the engagement type; the classifier is the upstream source.

### Directive compliance:
- Directive 1 (Rigidity Problem): The 5-type taxonomy is the first step in dynamic configuration — it drives which templates are queried, which eval profiles are applied.
- Directive 4 (Engagement Scope): The EXPLORATORY and STRATEGIC types directly support the "FITFO" requirement for novel engagements.
- Directive 11 (Configurable Pipeline Depth): This change is the mechanical implementation of that directive — the classifier selects the profile.
- Directive 13: Classifier explicitly listed as Phase 1.

---

## Change #3: Add Decision-First CoT + TiCoder Divergence Detection for Intent Clarification

**MASTER-SYNTHESIS Reference:** Section 9, Change #3
**Phase Classification:** Phase 1 (Decision-First CoT) / Phase 2 (TiCoder divergence detection)
**Phase Rationale:** Directive 13 explicitly defers "TiCoder divergence detection in intent clarification" to Phase 2. The Decision-First CoT 5-step structured prompt is a prerequisite for correct intent extraction regardless and ships in Phase 1. TiCoder (generate 2-3 candidate plans, surface divergences as clarifying questions) is additive sophistication that can be added to the existing intent clarifier without data flow changes — passes the deferral test.
**Location in CAPSTONE-PLAN-v2.md:** Section 3, §3.4 Step 2 (as specified in Change #1), and as a new subsection §3.9

### What exists now:
Step 2 of the new 10-step pipeline (established in Change #1) describes the Decision-First CoT at a high level. The TiCoder pattern has no existing representation.

### What it should say:
Add the following as §3.9, immediately after the new §3.8:

```
### 3.9 Intent Clarification: Decision-First Chain-of-Thought

`[BATCH 2 UPDATE]` Intent clarification is one of the highest-leverage steps in the pipeline. LLMs score only 25% on pragmatic inference — correctly interpreting what a client *means* rather than what they *say* — without structured prompting (CEI benchmark, March 2026). The gap between stated intent and actual intent is the leading cause of research that answers the wrong question thoroughly.

**Phase 1: Decision-First Chain-of-Thought (5-Step Structured Prompt)**

The intent clarifier runs a structured internal reasoning chain before any output is produced:

1. **Decision identification:** "What specific decision will this research inform, and who makes it?"
2. **Evidence threshold:** "What evidence would change the decision-maker's current position? What would they need to see to conclude the opposite of what they likely believe?"
3. **Unstated constraints:** "What constraints are implicit in the engagement context — budget, timeline, organizational dynamics, regulatory environment — that would affect research scope?"
4. **Surprise detection:** "What would a genuinely surprising finding look like? If the system only finds what the client expects, is that a research success or a research failure?"
5. **Scope boundary:** "What is explicitly NOT part of this research? Where does the system's competence frontier lie for this specific question?"

This 5-step chain operationalizes Level 3 intent engineering from §3.3 — not just what to research, but what decision the research must enable. The output is a structured `intent_clarification.json` that informs all subsequent pipeline steps, including the Day-1 Hypothesis (Change #6) and MECE verification criteria (Change #5).

If the research question cannot be mapped to a specific decision with identifiable evidence thresholds, the Specification Engine requests operator input before proceeding. Ambiguity is resolved at Step 2, not discovered at Step 9.

**Phase 2: TiCoder Divergence Detection**

`[Phase 2: Can be added to intent_clarifier.py without data flow changes]`

TiCoder divergence detection — generating 2–3 candidate research plans and surfacing where they disagree as clarifying questions — improves intent alignment from 40% to 84% (TiCoder, 2025). In Phase 2, the intent clarifier generates competing interpretations of the client's question, identifies the branches where those interpretations diverge, and surfaces only the divergence points to the operator. This transforms a potentially exhausting clarification interview into a targeted decision: "The system sees two ways to interpret this question — which do you mean?" Operators see these divergence points at the Human Review Gate (Step 8) alongside the issue tree, enabling informed approval rather than blind sign-off.
```

### Preservations:
- The existing §3.3 (Three-Discipline Maturity Model, including the Level 1/2/3 framework and Klarna citations) must not be changed.
- The Klarna $60M citation must remain.

### Cross-section references:
- The Human Review Gate (Step 8 in the new §3.4) shows TiCoder divergence points; this creates a Phase 2 dependency between §3.9 and the HITL display in §3.4.

### Directive compliance:
- Directive 6 (FITFO Standard): Decision-First CoT is what prevents the system from confidently answering the wrong question on novel engagements.
- Directive 13: TiCoder is explicitly deferred to Phase 2. Decision-First CoT ships Phase 1.

---

## Change #4: Add Issue Tree Construction with Heterogeneous Consulting Lenses

**MASTER-SYNTHESIS Reference:** Section 9, Change #4
**Phase Classification:** [Phase 1]
**Phase Rationale:** Directive 13 explicitly lists "Issue tree decomposition (multi-agent with heterogeneous lenses, shallow start)" as Phase 1. This is structurally foundational — the template registry and dynamic agent configuration (also Phase 1) depend on the issue tree output format being stable.
**Location in CAPSTONE-PLAN-v2.md:** Section 3, §3.4 Step 3 (established in Change #1), elaborated in §3.9 or as an inline expansion within the 10-step flow description

### What exists now:
Step 3 of the 10-step pipeline (established in Change #1) describes multi-lens construction at a summary level. No detailed specification exists.

### What it should say:
Expand Step 3 of the 10-step pipeline in §3.4 with the following detailed specification (replacing the bracketed summary in Change #1's Step 3):

```
**Step 3 — Issue Tree Construction with Heterogeneous Consulting Lenses:**

`[BATCH 2 UPDATE]` Three to four Sonnet agents with distinct consulting lens assignments independently construct shallow issue trees. Heterogeneous lenses — different analytical frames applied to the same problem — produce 4–6% accuracy gains and 30% fewer factual errors compared to homogeneous generation, even with the same model (Reports 03 and 10, peer-reviewed 2025). This is the same logic as methodological diversity in Deliberation (§4.3): not different personalities, but genuinely different analytical frameworks that surface different branches.

**Lens assignments:**

| Agent | Lens | Primary Branch Types | Anti-Pattern to Avoid |
|-------|------|---------------------|----------------------|
| Agent 1 | **Financial** | Revenue drivers, margin structure, capital allocation, valuation inputs, working capital dynamics | Overweighting public market data; missing private company dynamics |
| Agent 2 | **Operational** | Process efficiency, supply chain, capacity, organizational capability, cost structure drivers | Treating operational issues as symptoms of strategic failures |
| Agent 3 | **Market/Competitive** | Market structure, competitive positioning, customer segmentation, demand dynamics | Confusing market share with structural advantage |
| Agent 4 (optional) | **Regulatory/Risk** | Regulatory environment, legal exposure, ESG factors, tail-risk scenarios | Used for complex STRATEGIC and EVALUATIVE engagements; omitted for SIZING and DIAGNOSTIC |

**Construction methodology:**
- Plan-and-Solve prompting: agent states its plan before constructing branches, reducing reasoning errors
- Skeleton-of-Thought structure: the tree skeleton (2-3 levels) is generated before leaf-level detail, enabling parallel population
- 2–3 curated MECE exemplars from casing materials (Jack's casing books, analyzed by Opus 1M context — not memorized templates but demonstrated principles)
- Hypothesis-driven branch framing: each branch is framed as a question that research can answer, not as a topic to cover
- Pydantic models enforce reasoning-first field ordering: `reasoning` field must be populated before `branches` field, preventing shortcut generation

**Shallow start (8–20 leaf nodes):** Depth stops at 2–3 levels. Deeper decomposition is triggered reactively when research agents report complexity (ADaPT-style, +28.3% vs. deep upfront planning). The Human Review Gate (Step 8) shows a manageable tree — not an overwhelming 50-node taxonomy — enabling genuine operator review rather than rubber-stamping.

**Aggregation:** After all lens agents produce independent trees, an Opus meta-agent runs Self-MoA aggregation (same model, same family) to synthesize the best decomposition. This uses the four-phase deliberation pattern: construct (done), analyze (identify divergences and overlaps), evaluate (score branches by MECE criteria), synthesize (produce the unified tree that preserves the best of each lens). Self-MoA achieves +6.6% accuracy on issue tree tasks (Report 10) because quality sensitivity penalizes cross-provider model mixing during creative decomposition. The MECE verification step (Change #5) then validates the synthesized tree.

The issue tree is stored as a living document (`issue-tree.json` in the engagement directory). Completed branches are immutable; pending branches can be refined. Three replanning cycles maximum (Step 10 feedback loop).
```

### Preservations:
- §3.1 framing of the Specification Engine as translator of vague client needs must be preserved.
- All citations in the existing §3.4 and §3.5 must be preserved.

### Cross-section references:
- §4.2 (Agent Specialization) currently describes 5 fixed research agent types. Change #14 converts these to seed templates, which this change depends on at the dispatch level (Step 6).
- §5 (Evaluator) references issue tree branch classification for weight generation — the tree structure produced here is the input to that mechanism.

### Directive compliance:
- Directive 2 (MECE Issue Tree): This change is the direct implementation. Multi-agent, independent construction, MECE validation, living document, human review gate.
- Directive 12 (Casing Principles Over Example Libraries): Lenses are taught via principles from casing materials, not memorized example trees. The Opus 1M analysis of casing books produces a skill file that teaches methodology.
- Directive 13: Explicitly Phase 1.

---

## Change #5: Add MECE Verification as Discrete Step

**MASTER-SYNTHESIS Reference:** Section 9, Change #5
**Phase Classification:** [Phase 1]
**Phase Rationale:** Directive 13 explicitly lists "MECE verification step" as Phase 1. Without MECE verification, the quality of the issue tree — the foundation of everything downstream — is uncontrolled. This cannot be deferred without undermining the entire Specification Engine.
**Location in CAPSTONE-PLAN-v2.md:** Section 3, §3.4 Step 4 (established in Change #1), expanded inline

### What exists now:
Step 4 of the 10-step pipeline (from Change #1) describes MECE verification at summary level. No detailed specification exists.

### What it should say:
Replace the bracketed summary in Change #1's Step 4 with:

```
**Step 4 — MECE Verification:**

`[BATCH 2 UPDATE]` A discrete verification step using Opus as evaluator checks the synthesized issue tree against five dimensions with atomic binary criteria. "Binary criteria" means each check produces PASS or FAIL, with no partial credit — this prevents the evaluator from averaging away a structural flaw in one dimension with excellence in another.

**Five verification dimensions:**

| Dimension | Binary Criterion | Programmatic Complement |
|-----------|-----------------|------------------------|
| **Mutual Exclusivity** | No two branches at the same level can contain overlapping territory (overlap fraction < 5% on semantic similarity check) | Cosine similarity on branch embeddings; pairs above 0.80 similarity flagged automatically before LLM judge runs |
| **Collective Exhaustiveness** | All branches at any given level, combined, cover the full scope of the parent node without residual | Opus checks for obvious gaps; human operator sees coverage map at Step 8 |
| **Tailoring** | Branches are specific to this engagement, not generic consulting categories pasted in | Each branch must contain engagement-specific qualifiers — company names, timeframes, decision-relevant metrics |
| **Actionability** | A research agent can execute against each leaf node with the tools available | Branches that require unavailable data sources or out-of-scope analysis are flagged for scope discussion |
| **Depth Appropriateness** | 2–3 levels is the target; branches that are already at the appropriate leaf level are not artificially subdivided | Over-decomposition (> 3 levels deep at initial construction) is a failure mode, not a feature |

**Failure handling:** Trees failing any dimension on PASS/FAIL criteria are returned to the decomposition step (Step 3) for targeted regeneration. Failing trees do not proceed to Step 5. The specific failing dimensions and branches are provided as structured feedback to the regenerating agents. Maximum 2 regeneration cycles before escalation to operator.

**Programmatic complement:** Semantic similarity checks run before the Opus judge. This catches mutual exclusivity failures deterministically, at zero LLM cost, before the expensive Opus evaluation runs. The LLM judge handles the four dimensions that require contextual judgment.

The MECE verification is the quality gate between "we have a decomposition" and "we have a decomposition worth researching." It is not a formality.
```

### Preservations:
- All existing §3.4 content except the old 4-step verification phase text (which is being replaced by the 10-step flow).

### Cross-section references:
- §5 (Evaluator) evaluation stack architecture applies analogous binary criteria principles — consistent design philosophy.

### Directive compliance:
- Directive 2 (MECE Issue Tree): The verification step is explicitly listed in Directive 2's flow ("Deliberation selects or synthesizes the best decomposition").
- Directive 13: Explicitly Phase 1.
- Directive 14 (Quality Standard): Goldman-grade quality begins at the issue tree level, not at the deliverable level.

---

## Change #6: Add Day-1 Hypothesis as Required Output

**MASTER-SYNTHESIS Reference:** Section 9, Change #6
**Phase Classification:** [Phase 1]
**Phase Rationale:** Not explicitly listed in Directive 13, but passes the deferral test in the negative — it cannot be deferred without changing the data flow. The Day-1 Hypothesis anchors the iterative research loop's stopping condition (Change #11) and the scout phase direction (Step 9). If deferred, the research loop has no hypothesis to test and degrades toward open-ended exploration, recreating the AutoGPT failure mode. It must be part of the data structures from Day 1.
**Location in CAPSTONE-PLAN-v2.md:** Section 3, §3.4 Step 2 (between classification and decomposition in the 10-step flow) and as an addition to the RESEARCH.md format in §3.2

### What exists now:
No Day-1 Hypothesis concept exists in either §3.2 (RESEARCH.md format) or the pipeline specification. The scout/strike framing in the old §3.5 implies iterative research but provides no hypothesis anchor.

### What it should say:
**Addition 1:** Add a new Step 2b in the 10-step pipeline (between Step 2 Intent Clarification and Step 3 Issue Tree Construction), or incorporate into Step 2 as a required output:

```
**Step 2 (continued) — Day-1 Hypothesis Formation:**

`[BATCH 2 UPDATE]` Before issue tree construction begins, the Specification Engine forms a Day-1 Hypothesis: a specific, testable claim that the research will confirm, refute, or qualify. The hypothesis is formed from the intent clarification output — the client's implied prior belief about the answer, made explicit.

The Day-1 Hypothesis is not a prediction. It is an analytical anchor that:
1. Prevents open-ended exploration from becoming unbounded (the AutoGPT infinite-loop failure mode)
2. Gives research agents a falsifiable claim to investigate rather than a topic to cover
3. Enables the iterative research loop's stopping condition — "Has the hypothesis been confirmed, refuted, or qualified with sufficient confidence?" — to function as a termination criterion
4. Forces the Specification Engine to commit to an analytical frame before research begins, making any frame-changing discoveries explicit

**Format:**
```json
{
  "day_1_hypothesis": "Company X's declining gross margin is primarily driven by rising COGS from supply chain disruption, not pricing power erosion",
  "alternative_hypothesis": "Margin decline reflects a structural shift in competitive positioning rather than a transient supply chain issue",
  "confidence_prior": 0.55,
  "evidence_that_would_confirm": ["COGS breakdown by category YoY", "Competitor margin trends over same period", "Pricing power metrics vs. peers"],
  "evidence_that_would_refute": ["Stable COGS with declining ASP", "Margin recovery when supply chain normalized elsewhere in sector"],
  "hypothesis_author": "specification_engine_v1"
}
```

Multiple competing hypotheses are generated and ranked. The highest-confidence hypothesis anchors the scout phase. If research findings decisively support the alternative, the Specification Engine can promote the alternative hypothesis and re-anchor. This promotion is logged as a scope-change event (Change #12).
```

**Addition 2:** Add to the RESEARCH.md format in §3.2, under a new `## Day-1 Hypothesis` heading:

```
## Day-1 Hypothesis
Primary hypothesis: [Testable claim the research will confirm, refute, or qualify]
Alternative hypothesis: [The strongest competing interpretation]
Prior confidence: [0.0–1.0, representing the Specification Engine's assessment of the primary hypothesis before research begins]
Evidence thresholds: What specific findings would confirm vs. refute?
```

### Preservations:
- The full RESEARCH.md format block in §3.2 must be preserved with this addition; do not remove any existing fields.
- The scout/strike metaphor is preserved but now understood as hypothesis-anchored exploration, not merely time-phased.

### Cross-section references:
- Change #11 (Iterative Research Loop): The three-criterion stopping condition depends on hypothesis status as one of its criteria.
- §4.3 (Deliberation Phase): The confidence map's highest-confidence finding should validate or refute the Day-1 Hypothesis.

### Directive compliance:
- Directive 3 (Iterative Multi-Round Research): The Day-1 Hypothesis is the answer to "What's the stopping condition?" — one of the four questions Directive 3 identifies as missing.
- Directive 6 (FITFO Standard): A senior McKinsey consultant always forms a hypothesis before starting research. The Day-1 Hypothesis mechanizes this practice.

---

## Change #7: Add VOI-Inspired Priority Scoring Formula

**MASTER-SYNTHESIS Reference:** Section 9, Change #7
**Phase Classification:** Phase 1 (heuristic scoring) / Phase 2 (full VOI formula)
**Phase Rationale:** Directive 13 explicitly defers "VOI-inspired priority scoring" and states "use simpler heuristic scoring in Phase 1." Priority assignment passes the deferral test — heuristic scoring (`decision_relevance × uncertainty`) can be replaced by the full VOI formula by changing the `priority_calculator.py` module without altering the data flow or handoff contracts, because the `priority_score` field in `research-tasks.json` (Change #9) exists in both phases.
**Location in CAPSTONE-PLAN-v2.md:** Section 3, §3.4 Step 5 (established in Change #1), expanded inline, and in §3.6 (Research Initiation) for the `research-tasks.json` priority field

### What exists now:
The `research-tasks.json` in §3.6 already contains a `"priority": 1` field (integer), but no priority scoring methodology is specified. Tasks are prioritized implicitly rather than by a defined formula.

### What it should say:
Expand Step 5 in the 10-step pipeline and add the following specification:

```
**Step 5 — Priority Assignment:**

`[BATCH 2 UPDATE]` Issue tree branches are ranked by priority using a scoring formula. Priority scores are computed at task generation time (Step 7) and stored as `priority_score` in `research-tasks.json`. Priority is a working hypothesis: reprioritized each research cycle as findings accumulate.

**Phase 1 implementation — heuristic scoring:**

```
priority_score = decision_relevance × current_uncertainty
```

Where:
- `decision_relevance` (0.0–1.0): How directly does answering this branch affect the client's stated decision? Scored by the Specification Engine based on the intent clarification output.
- `current_uncertainty` (0.0–1.0): How uncertain is the system about this branch, given available prior knowledge? Higher uncertainty = higher priority for research.

Branches with high decision relevance and high uncertainty are researched first. Branches with low decision relevance are researched only if capacity permits or if upstream findings raise their relevance.

**Phase 2 implementation — VOI-inspired formula:**

`[Phase 2: Requires calibrated cost estimation; add to priority_calculator.py without data flow changes]`

```
priority_score = (decision_relevance × current_uncertainty) / estimated_research_cost
```

Where `estimated_research_cost` represents the expected token and time cost of investigating the branch, enabling the system to make explicit cost-quality tradeoffs: a medium-importance, low-uncertainty, cheap-to-research branch may score higher than a high-importance, high-uncertainty, expensive-to-research branch in budget-constrained engagements. Multi-signal prioritization (sampling consistency across lens agents, feasibility estimation based on tool availability, structured scoring rubric) replaces the two-factor heuristic. Calibration requires empirical data from completed engagements.

**In research-tasks.json:** The existing `"priority": 1` integer field is replaced by:
```json
"priority_score": 0.72,
"priority_rank": 1,
"priority_rationale": "High decision relevance (central to M&A go/no-go decision) × high uncertainty (no current reliable market size estimate)"
```
```

### Preservations:
- The `research-tasks.json` example in §3.6 should have the `"priority": 1` field updated to the new schema. All other fields in the JSON example are preserved.
- The five design decisions numbered list in §3.6 is preserved; a sixth design decision is added (see Change #9 for DAG changes, which also modifies this list).

### Cross-section references:
- Change #9 (DAG structure) also modifies `research-tasks.json` format; coordinate these two changes to produce a unified updated JSON example.

### Directive compliance:
- Directive 5 (Build Philosophy): Phase 1 heuristic scoring provides correct interface; Phase 2 VOI formula is depth extension without rework.
- Directive 13: VOI-inspired scoring explicitly deferred; Phase 1 uses heuristic.

---

## Change #8: Add Observation Library CBR Query at Spec Engine Entry

**MASTER-SYNTHESIS Reference:** Section 9, Change #8
**Phase Classification:** [Phase 2]
**Phase Rationale:** Directive 13 explicitly defers "CBR Observation Library query at Spec Engine entry" because "Observation Library doesn't exist in Phase 1." This is a hard sequencing dependency — the CBR query cannot execute if the Library has no data. The architectural hook (Step 1 of the 10-step pipeline includes the CBR Retrieve call site) ships in Phase 1 so no rework is required in Phase 2.
**Location in CAPSTONE-PLAN-v2.md:** Section 3, §3.4 Step 1 (established in Change #1), expanded inline

### What exists now:
No Observation Library query at Spec Engine entry exists. The Observation Library is mentioned in §2 (Architecture Overview) and the META layer but has no mechanical integration with the Specification Engine.

### What it should say:
Expand Step 1 of the 10-step pipeline to include the CBR specification:

```
**Step 1 (continued) — Observation Library CBR Query:**

`[BATCH 2 UPDATE]` At Specification Engine entry, before hypothesis formation, the system queries the Observation Library using case-based reasoning (CBR Retrieve) to seed the hypothesis space with patterns from prior engagements.

**CBR Retrieve mechanism:**
- Input: engagement type (5-type taxonomy), domain taxonomy, and key phrases from the initial research question
- Retrieval: similarity search across Observation Library entries by engagement type + domain + primary analytical frame
- Output: 3–5 most similar prior engagements with their Day-1 Hypotheses, research strategies that succeeded, research strategies that failed, and high-value analytical frames discovered post-hoc

The CBR output feeds into Step 2 (Intent Clarification) as prior knowledge about what questions to ask, and into Step 3 (Issue Tree Construction) as exemplar trees that the lens agents can learn from without copying.

`[Phase 2: Observation Library infrastructure required. The call site in Step 1 is present in Phase 1 but returns an empty result set until the Library is populated. The Specification Engine handles the empty-result case gracefully — no CBR output means no hypothesis seeding, which is the correct Phase 1 behavior.]`
```

### Preservations:
- All existing Observation Library references in §2 and the META layer description must not be changed.

### Cross-section references:
- The Observation Library itself is described elsewhere in the plan; this change only specifies the query interface from the Spec Engine.

### Directive compliance:
- Directive 6 (FITFO Standard): CBR query is what makes the Observation Library "feed forward" — past engagements inform future ones.
- Directive 13: Explicitly Phase 2. Call site present in Phase 1; data population is Phase 2.

---

## Change #9: Change research-tasks.json to DAG Structure

**MASTER-SYNTHESIS Reference:** Section 9, Change #9
**Phase Classification:** [Phase 1]
**Phase Rationale:** Not explicitly listed in Directive 13, but fails the deferral test — if research tasks have dependencies that are not encoded, parallel agents may execute tasks in the wrong order, producing incorrect results. A flat list is architecturally wrong if DAG structure is required for correct execution. This must be in the data structures from Day 1; adding it later requires changing the task scheduler and all downstream consumers of `research-tasks.json`.
**Location in CAPSTONE-PLAN-v2.md:** Section 3, §3.6 (Research Initiation: From Specification to Task List), lines ~221–284

### What exists now:
The `research-tasks.json` example in §3.6 shows a flat list of tasks (`"tasks": [...]`) with no dependency encoding. Each task has `"id"`, `"category"`, `"type"`, etc., but no `"depends_on"` field or DAG metadata.

### What it should say:
Add a `"depends_on"` field and DAG metadata to the `research-tasks.json` example, and add a seventh design decision to the numbered list:

**In the JSON structure, replace the existing `"tasks"` array opening with:**

```json
{
  "project": "Acme Corp Competitive Position Analysis",
  "research_md": "RESEARCH.md",
  "specification_version": 2,
  "dag_structure": true,
  "decomposition_rationale": "Broad competitive position question decomposed into market sizing, competitive landscape, technology assessment, and strategic positioning threads. Market sizing (task_001) is a prerequisite for competitive share calculations (task_002). All research tasks complete before deliberation (task_100).",
  "tasks": [
    {
      "id": "task_001",
      "depends_on": [],
      "can_parallelize_with": ["task_003", "task_004"],
      ...
    },
    {
      "id": "task_002",
      "depends_on": ["task_001"],
      "can_parallelize_with": [],
      ...
    }
  ]
}
```

**Add as the eighth design decision in §3.6 (renumbered from existing 6 + additions from Change #7):**

```
8. **`[BATCH 2 UPDATE]` Tasks encode DAG dependency structure.** The `depends_on` field lists task IDs that must complete before this task can begin. `can_parallelize_with` lists tasks that can execute concurrently. This enables the research scheduler to execute truly independent tasks in parallel while respecting ordering constraints — a research agent analyzing supply chain dynamics cannot reference market share data that hasn't been collected yet. Microsoft Research's "Characterizing Deep Research" (ICLR 2026) found that DAG structure is a predictor of output quality because it enforces analytical coherence between dependent research threads. The `dag_structure: true` flag signals to the task scheduler that dependency resolution is required before dispatch.
```

### Preservations:
- All five existing design decision items in §3.6 must be preserved exactly.
- The existing JSON example fields (`"category"`, `"type"`, `"target_decision_usefulness"`, `"description"`, `"required_sources"`, `"acceptance_criteria"`, `"deliverable_destination"`, `"passes"`, `"anti_confirmatory_framing"`) must all be preserved.

### Cross-section references:
- Change #7 (priority scoring) also modifies the JSON schema; both changes should produce a unified updated example.

### Directive compliance:
- Directive 3 (Iterative Multi-Round Research): DAG structure is part of the answer to "How do findings from round N inform the research plan for round N+1?" — dependent tasks in round N+1 can depend on outputs from round N.

---

## Change #10: Add Per-Branch "End Product" Specification

**MASTER-SYNTHESIS Reference:** Section 9, Change #10
**Phase Classification:** [Phase 1]
**Phase Rationale:** Not explicitly listed in Directive 13. Passes the deferral test in the negative: without per-branch end product specification, research agents have no concrete output target, which creates the same specification vacuum the overall RESEARCH.md is designed to prevent. This is a data field in `research-tasks.json` — adding it later would require retroactive updates to all task schemas and agent output contracts. Must be in the data structures from Day 1.
**Location in CAPSTONE-PLAN-v2.md:** Section 3, §3.6, within the `research-tasks.json` schema and design decisions

### What exists now:
The `research-tasks.json` already has `"deliverable_destination"` (e.g., "Section 2: Market Landscape, Slide 4-6") but no specification of the specific artifact format the research must produce.

### What it should say:
Add an `"end_product"` field to the `research-tasks.json` schema and add a design decision:

**In the JSON task objects, add:**

```json
{
  "id": "task_001",
  ...
  "end_product": {
    "artifact_type": "quantitative_estimate",
    "format": "three-scenario table (bear/base/bull) with explicit assumptions per scenario and sensitivity to top-3 inputs",
    "required_fields": ["TAM_estimate_USD", "CAGR", "uncertainty_range", "key_assumptions", "comparable_analyst_estimates"],
    "chart_type": "waterfall or scenario comparison bar chart",
    "conclusion_format": "The L4+ AV sensor market in North America is estimated at $[X]B by 2030 (base case), with upside of $[X]B under [assumption] and downside of $[X]B under [assumption]"
  },
  ...
}
```

**Add as the ninth design decision in §3.6:**

```
9. **`[BATCH 2 UPDATE]` Per-branch "end product" specification.** Each task specifies the exact artifact the research agent must produce: chart type, table structure, required quantitative fields, and conclusion format. This is not output format cosmetics — it is specification of what research must produce to be analytically useful. A market sizing task that produces a single point estimate without scenarios or sensitivity analysis has failed, regardless of whether the number is correct. The `end_product` field makes this failure detectable at the handoff boundary rather than after the deliverable is assembled. This extends the lossless pipeline principle: not just "link findings to deliverable destinations" but "specify what form those findings must take when they arrive."
```

### Preservations:
- The existing `"deliverable_destination"` field must be retained alongside the new `"end_product"` field; they serve different purposes (destination vs. format).
- The five `[SYNTHESIS UPDATE]` design decisions (6 and 7) must be preserved.

### Cross-section references:
- §4.4 (Content Structuring via Sprint Contracts): The sprint contract at L2 should reference the `end_product` specification from the task, creating consistency between what research was asked to produce and what L2 expects to receive.

### Directive compliance:
- Directive 14 (Quality Standard): Goldman-grade output begins at task specification, not at review. If the task doesn't specify what "good" looks like, no evaluator can reliably detect "not good."

---

## Change #11: Add Iterative Research Loop Specification

**MASTER-SYNTHESIS Reference:** Section 9, Change #11
**Phase Classification:** [Phase 1]
**Phase Rationale:** Directive 13 explicitly lists "Iterative research loop (3-round default, 5 max, three-criterion stopping)" as Phase 1. Directive 3 identifies this as "the single biggest architectural gap in the current plan." Without mechanical specification, the system is single-pass by default.
**Location in CAPSTONE-PLAN-v2.md:** Section 4, as a new §4.5 added after §4.4

### What exists now:
The scout/strike model (old §3.5) implied iterative research but provided no mechanical specification: no round count, no stopping criteria, no decision logic, no between-round continuity mechanism. Section 4 has no iterative loop specification.

### What it should say:
Add new subsection §4.5 immediately after §4.4:

```
### 4.5 The Iterative Research Loop

`[BATCH 2 UPDATE]` The research engine does not execute in a single pass. Findings from one round spawn new research threads, refine existing ones, and update the priority ranking of pending work. This section provides the mechanical specification that was identified as the single biggest architectural gap in the prior plan (Directive 3).

**Round structure:**

| Round | Role | Typical allocation |
|-------|------|--------------------|
| Round 1 | Scout: broad exploration, hypothesis validation, landscape mapping | 70% exploration / 30% exploitation |
| Round 2 | Strike: focused deep-dive on branches confirmed to be high-value | 30% exploration / 70% exploitation |
| Round 3 (if triggered) | Gap closure: targeted research on specific identified gaps | 10% exploration / 90% exploitation |
| Rounds 4–5 (if triggered) | Edge case coverage: only triggered by quality gate failure on specific dimensions | Requires logged justification |

**Stopping criteria (three-criterion combination; any one can terminate):**

1. **Hard iteration cap.** Default: 3 rounds. Maximum: 5 rounds. Round 5 requires logged justification — what specific quality gate failure necessitates this round? Prevents runaway research loops on engagements where diminishing returns are misread as gaps.

2. **Quality gate.** The L4 Evaluator is applied mid-pipeline after each round, scoring research completeness against the RESEARCH.md. If the quality gate score meets or exceeds the engagement type's threshold (provisional Phase 1 threshold: Tier 1 dimensions ≥ 6/10), research stops regardless of round count.

3. **Semantic novelty exhaustion.** If the latest round produces no new claims not already present in the compiled findings from prior rounds (measured by semantic similarity of new claim text against existing claims), the system stops. "More research" on an exhausted information space produces corroboration, not discovery. The system logs the novelty rate per round so operators can observe when diminishing returns set in.

**Decision logic per round:**

| Signal | Decision |
|--------|----------|
| Quality gate score < threshold AND round < cap | Spawn new research round (broader coverage on failing dimensions) |
| Score < threshold on specific dimension AND novelty exhaustion on that dimension | Go deeper: targeted subagents on the specific gap |
| Quality gate score ≥ threshold | Stop (log final state) |
| Round cap reached | Stop (log reasoning, flag for operator review if quality gate not met) |
| Scope-change detected | Hierarchical replan (see §4.6) |

**Between-round continuity:** The orchestrator (Opus) maintains a persistent Memory scratchpad (`research-state.md`) that carries state across rounds. See Change #13 for the scratchpad specification.

**Round N+1 seeding from Round N:** At round start, research agents receive selected excerpts from the compiled findings of prior rounds via JIT context loading — not the full artifact store, but the key findings relevant to their assigned branch. This prevents redundant research and ensures Round N+1 builds on Round N rather than repeating it.

**ADaPT-style deepening:** When a research agent reports that a branch is more complex than the issue tree anticipated (more sub-questions, more data sources, more analytical depth required), the orchestrator can adaptively deepen that branch — spawning additional subagents for the branch's sub-questions within the same round. This is reactive decomposition within L1 research rounds (see Change #22 for full specification).

**Convergent evidence:** Three-criterion stopping with 3–5 round cap was independently identified by Anthropic, OpenAI, Google, and DBAutoDoc as the standard for production iterative research systems (Reports 01 and 10). This is not a custom design decision — it is the emergent consensus from production deployments.
```

### Preservations:
- §4.1, §4.2, §4.3, and §4.4 are not changed by this addition.

### Cross-section references:
- Change #13 (Memory scratchpad): The scratchpad is the between-round continuity mechanism referenced here.
- Change #12 (Scope-change detection): The "scope-change detected → hierarchical replan" row in the decision logic table points to §4.6.
- §3.4 Step 9 and Step 10 (from Change #1): The feedback loop in Step 10 is this iterative loop, now mechanically specified.

### Directive compliance:
- Directive 3 (Iterative Multi-Round Research): All four missing mechanical specifications from Directive 3 are resolved: decision authority (Opus orchestrator via quality gate), round maximum (5), stopping condition (three-criterion), scope expansion handling (Change #12), and round-to-round carryover (scratchpad in Change #13).
- Directive 13: Explicitly Phase 1.

---

## Change #12: Add Scope-Change Detection Protocol

**MASTER-SYNTHESIS Reference:** Section 9, Change #12
**Phase Classification:** [Phase 1]
**Phase Rationale:** Not explicitly listed in Directive 13. Fails the deferral test: Directive 7 mandates a human review gate when scope changes. Without a scope-change detector, the gate cannot be triggered appropriately — the system would either ignore scope changes (violating Directive 7) or stop for every minor finding variation (unusable). The detector is a prerequisite for the HITL gate to function correctly on scope changes.
**Location in CAPSTONE-PLAN-v2.md:** Section 4, as a new §4.6 added after §4.5

### What exists now:
No scope-change detection mechanism exists. The prior text mentions `"insufficient_evidence"` triggers in the confidence map but provides no protocol for scope changes that alter the research direction.

### What it should say:
Add new subsection §4.6 immediately after §4.5:

```
### 4.6 Scope-Change Detection Protocol

`[BATCH 2 UPDATE]` Research frequently surfaces findings that fall outside the original RESEARCH.md specification. A company being researched for its competitive position may be in unannounced acquisition talks. A market sizing exercise may discover the market is fundamentally structured differently than the client's question assumed. These are scope changes — discoveries that alter what research should do, not just what it has found.

A lightweight Haiku-tier scope-change detector runs after each research agent's output is received. It classifies findings as:

**In-Plan:** The finding is surprising or significant but falls within the declared scope of the RESEARCH.md. Response: minor adjustment to the orchestrator's Memory scratchpad (Change #13). Research continues.

**Out-of-Plan:** The finding requires altering the research scope, hypothesis, or analytical framework to properly address. Response: hierarchical replan triggered. Human review gate opened (per Directive 7).

**Classification signals (Haiku evaluates in < 2 seconds):**

| Signal | In-Plan | Out-of-Plan |
|--------|---------|-------------|
| Does the finding alter the RESEARCH.md's primary research question? | No | Yes |
| Does it require research tools or data sources not provisioned for this engagement? | No | Yes |
| Does it expand the engagement's deliverable scope beyond what the client commissioned? | No | Yes |
| Does it require the Day-1 Hypothesis to be replaced rather than refined? | No | Yes |

**Out-of-Plan handling:**

1. The scope-change finding is logged to the orchestrator's Memory scratchpad with a `scope_change_detected: true` flag.
2. Research on the affected branch pauses.
3. The human review gate opens with: (a) the original RESEARCH.md, (b) the scope-change finding, (c) the orchestrator's analysis of what would change if the finding were incorporated, and (d) a recommended course of action (continue with original scope / expand scope / reframe hypothesis).
4. If the operator approves scope expansion: the RESEARCH.md is versioned (RESEARCH-v2.md, etc.), new tasks are generated, and the iterative loop continues.
5. If the operator rejects scope expansion: the finding is flagged as "noted but out-of-scope" in the deliverable, and research continues on the original scope.

**Example:** A research agent investigating Company X's competitive position finds a credible report that Company X is in acquisition talks with Company Y. This finding is Out-of-Plan: it changes what the competitive position analysis means (the client may be the acquirer's competitor, the target, or a bystander) and requires the engagement scope to be clarified before proceeding. The agent does not proceed to analyze the implications — it surfaces the finding, and the human decides.

The scope-change detector prevents two failure modes: (1) agents silently expanding scope beyond what was commissioned, producing a deliverable the client didn't ask for; and (2) agents silently ignoring scope-changing findings, producing a deliverable that's analytically stale by the time it's delivered.
```

### Preservations:
- The `"insufficient_evidence"` trigger in the confidence map JSON (§4.3) is preserved; it is a within-scope signal (more research needed on a specific claim), not a scope-change signal.

### Cross-section references:
- Directive 7 (Human-in-the-Loop): Out-of-Plan classification is an additional trigger for the HITL gate, per the directive.
- Change #11 (Iterative Research Loop): The "scope-change detected → hierarchical replan" row in the decision logic table is this protocol.
- Change #13 (Memory scratchpad): The scratchpad receives scope-change log entries.

### Directive compliance:
- Directive 3: "How does the system handle mid-research scope expansion?" is directly resolved here.
- Directive 7: Scope-change detection makes the HITL gate context-aware rather than only triggering at pre-scheduled points.

---

## Change #13: Add Orchestrator Memory Scratchpad as First-Class Data Structure

**MASTER-SYNTHESIS Reference:** Section 9, Change #13
**Phase Classification:** [Phase 1]
**Phase Rationale:** Not explicitly listed in Directive 13. Fails the deferral test: the between-round continuity mechanism referenced in Change #11 (iterative loop) and Change #12 (scope-change detection) requires a concrete data structure. Without it, the orchestrator cannot carry state across rounds, making the iterative loop stateless. Adding it later would require the iterative loop's orchestration code to be rewritten.
**Location in CAPSTONE-PLAN-v2.md:** Section 4, as a new §4.7 added after §4.6 (or incorporated into §4.5)

### What exists now:
No orchestrator memory or scratchpad mechanism is specified in Section 4. The plan describes agent isolation (§4.1) but provides no mechanism for the orchestrator to maintain state across research rounds.

### What it should say:
Add new subsection §4.7 immediately after §4.6:

```
### 4.7 Orchestrator Memory: The Research-State Scratchpad

`[BATCH 2 UPDATE]` The orchestrator (Opus) maintains a persistent Memory scratchpad — a structured markdown file (`research-state.md`) that carries engagement state across research rounds. This is a first-class data structure in the pipeline, not an implementation detail.

**The scratchpad is the orchestrator's working memory.** Within a research round, Opus 4.6 maintains state in context (context anxiety eliminated — Opus 4.6 does not degrade under context pressure within a round). Between rounds, the orchestrator persists its working memory to `research-state.md` and reads it at the next round's start. This enables multi-round research sessions that survive across long engagements without requiring the orchestrator to restart from scratch.

**Scratchpad structure:**

```markdown
# Research State — {engagement_id}
*Round {N} of {max_rounds} | Last updated: {timestamp}*

## RESEARCH.md Summary
[Condensed version of the current RESEARCH.md — the intent, hypothesis, and scope]
[Version: RESEARCH-v{N}.md if scope-changed]

## Day-1 Hypothesis Status
Primary hypothesis: [text]
Status: UNDER_INVESTIGATION / CONFIRMED / REFUTED / QUALIFIED
Confidence: [0.0–1.0]
Basis: [key findings from prior rounds that update confidence]

## Key Findings to Date
[3-sentence maximum per finding; link to full artifact in raw/]
- [CLM-001] [finding summary] [confidence] [sources]
...

## Open Gaps
[What the current round needs to address]
- [GAP-001] [description] [priority] [assigned to: task_XXX]
...

## Scope-Change Log
- [SC-001] [timestamp] [finding that triggered scope-change] [operator decision: accepted/rejected]

## Stopping Condition Status
- Hard cap: Round {N} of {default/max}
- Quality gate: [last score / threshold] [PASS/FAIL]
- Novelty rate: [claims per round, last 2 rounds]
- Decision: CONTINUE / STOP
```

**Hard ceiling:** 140–160K tokens (70–80% of Opus 4.6's 200K context window). When the scratchpad approaches this ceiling, the orchestrator compiles older findings into the Karpathy-pattern `compiled/` directory and references them by index, freeing scratchpad space while preserving access.

**Isolation preserved:** The Memory scratchpad is the orchestrator's private working memory. Research agents do not have access to it. They receive only their assigned task specification and JIT-loaded excerpts from the `compiled/` findings directory. This maintains the isolation requirement of §4.1 — agents do not see each other's intermediate findings — while enabling the orchestrator to track the engagement's overall state.

**Why this matters:** The 37% information retention failure rate (Factory.ai, 2026) applies to systems that allow individual agent context to serve as state storage. When state is in the orchestrator's scratchpad and full artifacts are in the filesystem, retention is deterministic — the orchestrator reads the scratchpad, agents produce artifacts, nothing is lost to context window overflow.
```

### Preservations:
- §4.1's isolation requirement — agents do not share intermediate findings — must be explicitly preserved. The scratchpad is orchestrator-only, not shared with agents.

### Cross-section references:
- Change #11 (Iterative Loop): The scratchpad is the between-round continuity mechanism.
- Change #12 (Scope-Change): The scope-change log section of the scratchpad is written by the scope-change detector.
- §4.1 isolation requirements must be cross-referenced to clarify that the scratchpad does not violate isolation.

### Directive compliance:
- Directive 3: "How do findings from round N inform the research plan for round N+1?" is directly resolved by the scratchpad.
- Directive 7: The scope-change log section provides the decision trail for human review gate openings.

---

## Change #14: Convert 5 Fixed Agent Types to Seed Templates in Registry

**MASTER-SYNTHESIS Reference:** Section 9, Change #14
**Phase Classification:** [Phase 1]
**Phase Rationale:** Directive 13 explicitly lists "Template registry for agent configs (seed templates, not just enums)" as Phase 1. Directive 1 (Rigidity Problem) identifies the 5 fixed types as the core design failure to correct. Without this change, the system cannot handle novel engagement types (Directive 4), cannot FITFO (Directive 6), and cannot achieve the dynamic configuration that is the architectural foundation.
**Location in CAPSTONE-PLAN-v2.md:** Section 4, §4.2 (Agent Specialization with Designed Diversity), lines ~333–347

### What exists now:
```
Different research threads benefit from different agent "personalities" and toolsets. Drawing from Carlini's C Compiler project — where agents were specialized into roles like code coalescing, performance optimization, and design critique — the research pipeline uses specialized agent types with **designed diversity in analytical frames** (Jones, "Agent Schemes," Mar 9, 2026). The diversity isn't just in tools — it's in *perspective*:

- **Quantitative Research Agent**: ...
- **Qualitative Research Agent**: ...
- **Contrarian Agent**: ...
- **Historical Analogy Agent**: ...
- **Internal Document Agent**: ...
```

### What it should say:
Replace the opening of §4.2 with:

```
### 4.2 Agent Configuration: Template Registry and Dynamic Specialization

`[BATCH 2 UPDATE]` The five research agent types described below are **seed templates**, not enum constraints. This distinction is architecturally critical: seed templates are the starting population of a registry, from which the Specification Engine either instantiates directly (high similarity match) or generates custom `AgentDefinition` objects (below similarity threshold). When engagement types fall outside the seed templates' coverage — an auto-shop chain expansion, an M&A target screen in a niche industry — the registry generates configurations that fit, rather than forcing the question into an ill-fitting predefined role (Directive 1 and Directive 4).

`[BATCH 2 UPDATE]` Five production multi-agent frameworks (Reports 01, 02, 03, 05, 10) independently converge on `Agent = (system_prompt, tools[], output_schema, constraints)` as the declarative configuration standard. Anthropic's own system dynamically spawns subagents with per-task configs. The seed templates below follow this structure. The tools[] assignment is the primary behavioral governance mechanism — it is a hard constraint, not prompt guidance (see Change #16).

**The five seed templates (starting population of the research agent registry):**

Each template is stored in the agent registry as a structured `AgentDefinition` with fields: `template_id`, `name`, `lens`, `system_prompt_base`, `tools_allowed` (hard list), `output_schema`, `constraints`, and `token_budget` (see Change #17). Templates are queryable by engagement type, analytical mode, and tool requirements.

- **Quantitative Research Agent** [`template_id: quant-research-v1`]: Optimized for financial data extraction, ratio analysis, trend decomposition, and numerical verification. Soul prompt calibrated toward precision, skepticism about rounded numbers, and explicit uncertainty quantification. Tools: financial_data_mcp, sec_filings_mcp, numerical_verification. Output schema: claims with quantitative confidence intervals.

- **Qualitative Research Agent** [`template_id: qual-research-v1`]: Optimized for narrative sources — news articles, expert commentary, conference presentations, video transcripts. Soul prompt emphasizes synthesis, thematic pattern recognition, and identification of sentiment shifts over time. Tools: web_search_mcp, paper_search_mcp, news_archive. Output schema: claims with source diversity scores.

- **Contrarian Agent** [`template_id: contrarian-v1`]: Exists specifically to stress-test the emerging thesis. Looks for disconfirming evidence, identifies implicit assumptions, and surfaces risks the consensus view might be underweighting. This agent is the institutional check against confirmation bias — a failure mode that persists in single-agent research (@Chris_Worsey, Darwinian selection work). Tools: same as primary research agents; system prompt inverts confirmatory framing to mandatory disconfirmatory framing.

- **Historical Analogy Agent** [`template_id: historical-analogy-v1`]: Approaches the question through historical parallels — what happened when a similar industry went through a similar transition? Different analytical frame from pure data analysis. Tools: paper_search_mcp, historical_data_sources.

- **Internal Document Agent** [`template_id: internal-doc-v1`]: Specializes in navigating and synthesizing Keystone's proprietary materials (covered in Section 6). Tools: internal_rag_mcp, document_store_mcp.

**Beyond the seed templates:** When the Specification Engine's template registry query scores below 0.85 similarity on all seed templates, it generates a custom `AgentDefinition` using the engagement type and task description as inputs. Successful custom configurations from completed engagements are candidates for promotion to the registry (Phase 3 promotion loop — validated configurations become permanent seeds). This is how the system FITFO without predefined skill files for every possible scenario (Directive 6).

Each agent type has both a **skill set** (procedural knowledge — what tools to use, what data formats to expect) and a **soul prompt** (identity and judgment — how skeptical to be, what "good enough" looks like, when to push deeper versus move on). This soul-based approach emerged from @tolibear_'s insight that agents need identity alongside procedural knowledge — a "skilled agent without a soul produces correct but generic output."
```

### Preservations:
- The soul prompt concept (@tolibear_ citation) must be preserved.
- The Carlini citation and the diversity-in-frames principle must be preserved.
- The @jordymaui principle ("make it impossible not to cite sources") referenced later in §4.1 is preserved.

### Cross-section references:
- Change #15 (template registry query): The registry query mechanism is the dispatch operation that operates on the templates defined here.
- Change #16 (tighten-only invariant): The `constraints` field in each `AgentDefinition` is where the tighten-only invariant is encoded.
- Change #17 (token budget): The `token_budget` field in each `AgentDefinition` is set by the Specification Engine based on the task.

### Directive compliance:
- Directive 1 (Rigidity Problem): Templates → not enum constraints. Dynamic configuration on novel tasks.
- Directive 4 (Engagement Scope): Custom AgentDefinition generation handles the "auto shop chain" test case.
- Directive 6 (FITFO Standard): Registry-plus-generation enables handling of novel engagements.
- Directive 13: Template registry explicitly Phase 1.

---

## Change #15: Add Template Registry Query + Interpolation as Dispatch Mechanism

**MASTER-SYNTHESIS Reference:** Section 9, Change #15
**Phase Classification:** [Phase 1]
**Phase Rationale:** Not explicitly listed in Directive 13 as a separate item, but is the mechanism that makes the template registry (explicitly Phase 1) function. The registry without a query-and-interpolation dispatch is an inert data structure. These are inseparable: registry + query mechanism ship together.
**Location in CAPSTONE-PLAN-v2.md:** Section 4, §4.2 (after the seed template definitions from Change #14)

### What exists now:
No registry query mechanism exists. The current text implies the Specification Engine "assigns" agent types by category, but provides no mechanical specification.

### What it should say:
Add after the seed template definitions in §4.2 (continuing from Change #14):

```
**Template registry query and interpolation:**

`[BATCH 2 UPDATE]` The Specification Engine queries the template registry at Step 6 of the pipeline (Dynamic Agent Configuration). The query process:

1. **Input:** engagement type (5-type taxonomy), task category (from issue tree branch), required tools (from task specification), analytical mode (quantitative / qualitative / adversarial / historical).

2. **Similarity scoring:** Each registry template is scored against the input via cosine similarity on a combined embedding of (system_prompt_base + tools_allowed + lens description). The highest-scoring template above the 0.85 threshold is selected.

3. **Interpolation:** The selected template's `system_prompt_base` is interpolated with task-specific variables: engagement context, specific company or market names, branch-specific research questions, day-1 hypothesis, and token budget. The interpolated system prompt is the agent's actual configuration for this task. Pydantic validation runs on the interpolated `AgentDefinition` before dispatch.

4. **Below-threshold generation:** If no template scores above 0.85, the Specification Engine generates a custom `AgentDefinition` from scratch. Inputs: task description, required analytical approach, available tools. The custom definition undergoes the same Pydantic validation and tighten-only constraint (Change #16) as instantiated templates. Generated definitions are stored in the engagement directory for post-hoc analysis and potential registry promotion.

5. **Dispatch:** The validated `AgentDefinition` is handed to the research orchestration layer. The orchestrator spawns the agent with the specified configuration. The agent's tools[], output_schema, and token_budget are set by the definition — not by runtime prompt instructions.

**Calibration note:** The 0.85 similarity threshold is a provisional value. Empirical calibration against first engagements will establish whether the threshold is too high (forcing unnecessary custom generation) or too low (producing poor template matches). The threshold is a configuration parameter, not a hardcoded constant, enabling adjustment without code changes.
```

### Preservations:
- The full seed template content from Change #14 is preserved.
- §4.1's tool specialization note ("3-5 domain-specific tools matched to its assigned task") is consistent with and preserved alongside the registry mechanism.

### Cross-section references:
- Change #2 (engagement classifier): The engagement type from Step 1 is one of the query inputs.
- Change #16 (tighten-only invariant): Validation step in query process enforces the invariant.

### Directive compliance:
- Directive 1 (Rigidity Problem): The below-threshold generation path ensures the registry never forces a bad fit.
- Directive 5 (Build Philosophy): Query mechanism is correct interface; threshold calibration is depth that can be adjusted without rework.

---

## Change #16: Add Tighten-Only Constraint Invariant

**MASTER-SYNTHESIS Reference:** Section 9, Change #16
**Phase Classification:** [Phase 1]
**Phase Rationale:** Not explicitly listed in Directive 13. Fails the deferral test: the tighten-only invariant is a security property of the dynamic agent configuration system. Without it, dynamically generated agent configurations could be manipulated to grant agents broader tool access than intended — a privilege escalation vulnerability in the multi-agent hierarchy. This must be enforced from Day 1; adding it later requires auditing all prior dynamically generated configurations.
**Location in CAPSTONE-PLAN-v2.md:** Section 4, §4.2 (as an addition to the registry/dispatch mechanism from Change #15)

### What exists now:
No tighten-only constraint exists. Tool assignment is described qualitatively ("3-5 domain-specific tools matched to its assigned task") but without a formal invariant.

### What it should say:
Add after the template registry query specification in §4.2:

```
**The tighten-only invariant:**

`[BATCH 2 UPDATE]` Dynamic agent configuration introduces a structural risk: if the Specification Engine can generate arbitrary `AgentDefinition` objects, a poorly-specified or adversarially-crafted task could produce an agent configuration with broader tool access than intended. The tighten-only invariant prevents this.

**Invariant:** A dynamically generated `AgentDefinition` can only *restrict* the tool set of the most permissive applicable seed template — never *expand* it. Child agents in a multi-agent hierarchy can never be granted permissions not held by the parent. The MCP gateway enforces this at the infrastructure level, not through prompt instructions.

Formally:
```
tools_allowed(generated_agent) ⊆ tools_allowed(best_matching_template)
```

When no matching template exists (below 0.85 threshold), the generated agent's tool set is constrained to the union of all tools in the registry — itself a defined boundary. A generated agent cannot access a tool that no seed template is authorized to use.

**Why this matters:** Tool restriction is a hard behavioral constraint; prompt instructions are soft guidance that models may ignore (Reports 02 and 08; @jordymaui principle). The MCP gateway is the enforcement point — it inspects tool call requests against the agent's declared `tools_allowed` list and rejects unauthorized calls at the infrastructure level before they execute. No amount of prompt engineering can bypass this check.

**Implementation:** Pydantic validation on `AgentDefinition` enforces the tighten-only constraint at creation time, before dispatch. The MCP gateway enforces it again at runtime. Defense in depth.
```

### Preservations:
- The existing `[SYNTHESIS UPDATE]` per-agent tool specialization note in §4.1 ("3-5 domain-specific tools") is consistent with and preserved alongside this invariant.

### Cross-section references:
- §4.1's `[SYNTHESIS UPDATE]` note on per-agent tool specialization is now explained more precisely as an instance of the tighten-only invariant in practice.

### Directive compliance:
- Directive 1 (Rigidity Problem): Dynamic configuration is safe because the invariant prevents privilege escalation.
- Directive 5 (Build Philosophy): Correct interface (tighten-only as structural constraint) from Day 1.

---

## Change #17: Add Token Budget as Explicit Agent Configuration Field

**MASTER-SYNTHESIS Reference:** Section 9, Change #17
**Phase Classification:** [Phase 1]
**Phase Rationale:** Not explicitly listed in Directive 13. Fails the deferral test: token budget explains 80% of performance variance in Anthropic's multi-agent system (Report 03, Anthropic production analysis). If token budget is not set explicitly per agent in the `AgentDefinition`, it defaults to whatever the API's default is — an uncontrolled variable that dominates quality outcomes. This must be set by the Specification Engine from Day 1; adding it later requires modifying all existing agent dispatch code and calibrating budgets retroactively.
**Location in CAPSTONE-PLAN-v2.md:** Section 4, §4.2 (as an addition to the AgentDefinition specification)

### What exists now:
Token budgets are not mentioned in §4.2 or the agent configuration section.

### What it should say:
Add as part of the `AgentDefinition` description in §4.2:

```
**Token budget as agent configuration:**

`[BATCH 2 UPDATE]` Each `AgentDefinition` includes an explicit `token_budget` field set by the Specification Engine at dispatch time. This is not a soft guideline — it is a hard configuration parameter passed to the agent's API call.

```python
class AgentDefinition(BaseModel):
    template_id: str
    name: str
    system_prompt: str  # interpolated from template base
    tools_allowed: list[str]
    output_schema: type[BaseModel]
    constraints: list[str]  # includes tighten-only enforcement
    token_budget: int  # hard limit; passed as max_tokens to API call
    token_budget_rationale: str  # logged for calibration
```

**Token usage explains 80% of performance variance** in Anthropic's multi-agent production system — not the sophistication of the system prompt, not the number of tools, not the model version. Getting the token budget right is the primary quality and cost lever available to the Specification Engine (Anthropic, multi-agent production analysis, 2026).

**Budget allocation guidelines (Phase 1, provisional):**

| Task Type | Recommended Budget | Rationale |
|-----------|-------------------|-----------|
| Simple fact retrieval | 2,000–4,000 tokens | Single source, structured output |
| Standard research task | 8,000–16,000 tokens | Multiple sources, synthesis required |
| Complex analytical task (quantitative modeling) | 16,000–32,000 tokens | Multi-source reasoning chain |
| Deliberation analyst | 8,000–16,000 tokens | Single analytical methodology per agent |

These budgets are calibrated against the Anthropic multi-agent production system's findings and the $12–$100 per-engagement cost target. The Specification Engine selects budget based on task complexity (estimated from the `end_product` specification and branch depth) and adjusts downward for budget-constrained engagements (Light profile).

**Calibration:** First-engagement data will establish actual budget requirements. The `token_budget_rationale` field is logged for each dispatch, enabling post-hoc analysis of where budgets were over- or under-specified.
```

### Preservations:
- All existing §4.2 content (soul prompts, skill sets, diversity principles) is preserved.

### Cross-section references:
- CLAUDE.md cost target ($12–$100 per engagement): Token budget is the primary lever for staying within this target.
- Change #14 (seed templates): The `token_budget` field is part of each template's `AgentDefinition`.

### Directive compliance:
- Directive 11 (Configurable Pipeline Depth): Token budget is one dimension of pipeline depth configurability.
- Directive 14 (Quality Standard): Correct token budget is a prerequisite for Goldman-grade output — agents given insufficient budget produce truncated, lower-quality analysis regardless of their configuration.

---

## Change #18: Add 1,000–2,000 Token Condensed Output Requirement for Subagents

**MASTER-SYNTHESIS Reference:** Section 9, Change #18
**Phase Classification:** [Phase 1]
**Phase Rationale:** Not explicitly listed in Directive 13. Fails the deferral test: the condensed output is the handoff artifact at the L1→L1.5 boundary. If the output format is not specified in Phase 1, each agent will produce variable-length outputs in whatever format feels natural, and the pipeline boundary cannot enforce the quality gate. The Pydantic output schema (which enforces this) is part of the `AgentDefinition` from Change #14 and must be specified from Day 1.
**Location in CAPSTONE-PLAN-v2.md:** Section 4, §4.1, after the "Returns a condensed summary" point (item 5 in the numbered list), around line 331

### What exists now:
```
5. **Returns a condensed summary.** Each research agent may process tens of thousands of tokens during its investigation but returns only a 1–2 page condensed synthesis to the pipeline. The Specification Engine never sees raw data. It works with pre-synthesized intelligence — exactly how a consulting engagement manager operates (Anthropic, "Context Engineering").
```

### What it should say:
Replace item 5 with:

```
5. **Returns a condensed summary in Pydantic-schemaed format.** Each research agent may process tens of thousands of tokens during its investigation but returns a structured condensed summary of 1,000–2,000 tokens to the pipeline. The orchestrator never sees raw data. It works with pre-synthesized intelligence — exactly how a consulting engagement manager operates (Anthropic, "Context Engineering").

`[BATCH 2 UPDATE]` The condensed summary is not prose — it is a Pydantic-validated structured object:

```python
class ResearchFinding(BaseModel):
    task_id: str
    agent_id: str
    status: Literal["complete", "partial", "insufficient_evidence"]
    claims: list[ClaimEntry]  # 3–7 claims maximum
    open_gaps: list[str]  # what the agent looked for but could not find
    artifact_path: str  # path to full artifact in {engagement_id}/memory/raw/
    token_usage: int

class ClaimEntry(BaseModel):
    claim_id: str
    text: str  # 1–3 sentences
    confidence: float  # 0.0–1.0
    source_count: int
    source_ids: list[str]  # references to CitationProcessor manifest
    requires_followup: bool
```

The 1,000–2,000 token target is Anthropic's recommended condensed output size for subagents in multi-agent systems (Reports 01 and 09). Factory.ai's 37% information retention failure rate is the failure mode this structure prevents: when agents are allowed to return arbitrarily long prose, critical claims get lost in context compression. The Pydantic schema enforces exactly what information must be present, making the handoff contract machine-verifiable.

**The artifact bypass pattern:** The structured summary (1,000–2,000 tokens) is the handoff artifact that travels through the pipeline. The full research artifact — all sources, all intermediate reasoning, all raw findings — is written to `{engagement_id}/memory/raw/{task_id}/` and referenced by `artifact_path`. The CitationProcessor and human reviewer can access the full artifact if needed. This decouples pipeline throughput (structured summaries are fast to process) from research depth (full artifacts preserve everything).
```

### Preservations:
- The consulting engagement manager metaphor and Anthropic "Context Engineering" citation must be preserved.
- Items 1–4 in the numbered list (claiming a task, loading context JIT, investigating using workflow-level tools, writing in structurally-enforced format) must not be changed.

### Cross-section references:
- Change #19 (artifact bypass pattern): The condensed summary + full external file pattern is described here; Change #19 specifies it as an explicit architectural pattern rather than an implementation note.

### Directive compliance:
- Directive 5 (Build Philosophy): Structured handoff contracts at correct abstractions; Pydantic schema is the contract mechanism.

---

## Change #19: Add Artifact Bypass Pattern

**MASTER-SYNTHESIS Reference:** Section 9, Change #19
**Phase Classification:** [Phase 1]
**Phase Rationale:** Not explicitly listed in Directive 13. Fails the deferral test: the artifact bypass pattern is the mechanism that enables the iterative research loop to function across multiple rounds without context overflow. If agents write everything to context and nothing to disk, round N+1 cannot access round N's findings without loading the full context. The filesystem write pattern must be established in the data flow from Day 1.
**Location in CAPSTONE-PLAN-v2.md:** Section 4, §4.1, as an elaboration of the artifact bypass note introduced in Change #18

### What exists now:
No artifact bypass pattern is specified. The condensed summary note (existing item 5) implies something similar but does not make it an explicit architectural pattern.

### What it should say:
The artifact bypass description in Change #18 (item 5 replacement) already introduces the pattern. Elevate it as a named architectural pattern by adding the following after item 5's replacement:

```
`[BATCH 2 UPDATE]` **The artifact bypass pattern** is a required architectural constraint, not an optional implementation choice. It is the mechanism that resolves the three-way tension between context efficiency, information fidelity, and cross-round continuity:

- **Context efficiency:** The pipeline operates on structured summaries (1,000–2,000 tokens), not raw research artifacts. Pipeline stages never load full artifacts unless a human reviewer or CitationProcessor requires them.

- **Information fidelity:** Nothing is lost. Full artifacts are written to `{engagement_id}/memory/raw/{task_id}/` at the point of production. The Factory.ai 37% retention failure mode — where information is lost because it was only in agent context and that context was compacted or discarded — cannot occur when artifacts are written to disk before context is released.

- **Cross-round continuity:** Round N+1 research agents receive JIT-loaded excerpts from the compiled findings in `{engagement_id}/memory/compiled/`, not re-processed raw artifacts. The Karpathy three-layer pattern (raw/ → compiled/ → INDEX.md) is the underlying structure (Reports 04 and 06, validated by King's College London, February 2026: structure-driven retrieval outperforms similarity-driven for agent memory).

This pattern is convergent across Anthropic, OpenAI, and Google production systems (Reports 01, 06, 09): context resets for subagents with structured handoff artifacts consistently outperform context accumulation. It is mandatory, not optional.
```

### Preservations:
- §4.1's existing isolation requirement is not changed; the artifact bypass pattern extends it (agents write to their own directories, not shared memory).

### Cross-section references:
- Change #13 (Memory scratchpad): The orchestrator's compiled/ directory is populated via this pattern.
- Change #11 (Iterative Research Loop): "Round N+1 seeding from Round N" depends on this pattern.

### Directive compliance:
- Directive 8 (Karpathy's LLM Knowledge Bases): The three-layer filesystem pattern is directly implemented here.

---

## Change #20: Change Deliberation Aggregation from "Structured Aggregation" to Explicit "Claim-Level Selection"

**MASTER-SYNTHESIS Reference:** Section 9, Change #20
**Phase Classification:** [Phase 1]
**Phase Rationale:** Directive 13 explicitly lists "Claim-level selection for deliberation" as Phase 1. The existing text says "structured aggregation" which is ambiguous — it could mean synthesis/blending. The evidence from Reports 03 and 06 (81% win rate for selection vs. 51.2% for synthesis) makes this a high-stakes design decision. The word "aggregation" has been actively misleading.
**Location in CAPSTONE-PLAN-v2.md:** Section 4, §4.3, Phase 2 (Structured Aggregation with Curmudgeon Challenge) — the heading and prose description around lines 376–384

### What exists now:
```
#### Phase 2: Structured Aggregation with Curmudgeon Challenge

A separate aggregation agent (Opus-class) reads all independent analyses simultaneously and produces the confidence map. No iterative debate rounds. The aggregator:

1. Identifies convergent findings (claims supported by 2+ independent methodologies)
2. Identifies genuine disagreements (different methodologies reaching different conclusions from the same evidence)
3. Flags methodological blind spots (evidence types that no methodology addressed)
4. Runs a **curmudgeon challenge**: for every high-confidence finding, the aggregator must articulate a specific, non-trivial reason it could be wrong and assess whether any analyst addressed that risk
```

### What it should say:
Replace the Phase 2 section heading and opening paragraph with:

```
#### Phase 2: Claim-Level Selection with Curmudgeon Challenge

`[BATCH 2 UPDATE]` A separate aggregation agent (Opus-class) reads all independent analyses simultaneously and produces the confidence map through **claim-level selection** — not synthesis or blending. This distinction is not semantic: judge-based claim selection achieves an 81% win rate; synthesis-based blending scores 51.2% (near chance), because "blending introduces incoherence, conflicting perspectives, and diluted arguments" (Reports 03 and 06). The aggregator does not average competing claims. It evaluates competing claims and selects the best-supported one.

**What claim-level selection means operationally:** For each claim appearing in two or more analyst outputs, the aggregator:
1. Evaluates the evidence quality supporting each version of the claim (source count, source diversity, analytical rigor of the supporting argument)
2. Selects the best-supported version — not a blend of all versions
3. Records which analyst's version was selected and why
4. Notes where selected claims are in tension with non-selected claims (genuine disagreements, preserved as contested findings rather than blended away)

The aggregator then:

1. Identifies convergent findings (claims supported by 2+ independent methodologies, where selection converges to the same claim)
2. Identifies genuine disagreements (different methodologies reaching different conclusions from the same evidence — preserved as contested, not blended)
3. Flags methodological blind spots (evidence types that no methodology addressed)
4. Runs a **curmudgeon challenge**: for every high-confidence finding, the aggregator must articulate a specific, non-trivial reason it could be wrong and assess whether any analyst addressed that risk
5. `[BATCH 2 UPDATE]` Runs a post-selection consistency check: do the selected claims, taken together, form a coherent analytical picture? Incoherent selected claims (where individually correct selections contradict each other) are flagged for human review.
```

### Preservations:
- The confidence map JSON schema in §4.3 must be preserved exactly — it already encodes per-claim source counts and methodological agreement, which are the inputs to claim-level selection.
- The Phase 1 (Independent Parallel Analysis) prose, critical constraints, and analyst descriptions must not be changed.
- All citations in the Deliberation section must be preserved.

### Cross-section references:
- The confidence map JSON already has `"methodological_agreement": "4/4"` and `"sources": 7` — these are the claim-level selection inputs. The schema is compatible; only the prose describing how aggregation works is changing.
- §2 (Architecture Overview) handoff contracts table: the Deliberation row should note "claim-level selection" rather than "structured aggregation."

### Directive compliance:
- Directive 13: "Claim-level selection for deliberation" explicitly Phase 1.
- Directive 14 (Quality Standard): 81% vs. 51.2% is not an incremental improvement — it's the difference between a functional deliberation phase and one performing at chance. Goldman-grade output requires the correct aggregation mechanism.

---

## Change #21: Add "What Would You Have to Believe?" Step for Low-Confidence Findings

**MASTER-SYNTHESIS Reference:** Section 9, Change #21
**Phase Classification:** [Phase 1]
**Phase Rationale:** Not explicitly listed in Directive 13. Passes the deferral test — this could be added as a post-processing step in the aggregation agent's prompt without changing the data flow. However, the weak_confidence_50_60pct tier in the confidence map (which already exists) specifically calls for this kind of structured uncertainty treatment, and the confidence map schema would need a `wyhtb_analysis` field to carry the output. Adding this field later requires updating the confidence map schema and all downstream consumers (Structuring, Generation, Evaluation). Better to include the field from Phase 1 with the analysis initially optional.

**Classification decision:** Phase 1 for the field and call site; Phase 2 complexity escalation (multi-analyst WYHTB challenges) is deferred.
**Location in CAPSTONE-PLAN-v2.md:** Section 4, §4.3, Phase 2 (after the curmudgeon challenge, within the confidence map discussion)

### What exists now:
The confidence map already has a `"weak_confidence_50_60pct"` tier with `"key_issue"` and `"recommendation"` fields, but no structured treatment for *what assumptions would need to be true* for the weak-confidence finding to be correct or incorrect.

### What it should say:
Add after the curmudgeon challenge in Phase 2, and add a `wyhtb_analysis` field to the weak-confidence tier of the confidence map JSON:

```
5. `[BATCH 2 UPDATE]` **"What Would You Have to Believe?" (WYHTB) analysis for low-confidence findings.** For every finding in the `weak_confidence_50_60pct` tier, the aggregator generates a structured WYHTB analysis:

> "To believe [this claim], you would have to believe: [explicit list of assumptions]. The most contestable of these assumptions is [X]. The probability of [X] is estimated at [Y], based on [evidence or reasoning]. If [X] is false, the conclusion becomes [alternative]."

This converts vague uncertainty into structured epistemic accounting. A claim that's "weak confidence because we're not sure" is analytically useless. A claim with an explicit WYHTB analysis tells the structuring agent exactly how to present it — which assumptions to surface, which sensitivity analyses to run, which alternative conclusion to steelman.

In the confidence map JSON, weak-confidence findings add a `wyhtb_analysis` field:

```json
"weak_confidence_50_60pct": [
  {
    "claim": "Acme's software stack provides a durable competitive advantage",
    "methodological_agreement": "2/4",
    "key_issue": "Historical analogy analyst notes software moats erode faster than hardware moats in adjacent industries",
    "sources": 3,
    "recommendation": "Flag as contested in deliverable; present both cases with explicit assumptions",
    "wyhtb_analysis": {
      "required_assumptions": [
        "Acme's software IP is sufficiently differentiated to prevent replication by well-funded competitors",
        "Switching costs in the sensor platform market are high enough to create lock-in",
        "Acme can maintain its engineering talent advantage as the market scales"
      ],
      "most_contestable": "Engineering talent advantage — historically fails to sustain beyond 3-5 years in competitive markets",
      "probability_estimate": 0.45,
      "alternative_conclusion": "If software moats erode per historical pattern, Acme's advantage is hardware-dependent and subject to commoditization"
    }
  }
]
```
```

### Preservations:
- All existing confidence map JSON fields must be preserved; `wyhtb_analysis` is an additive field.
- The DiscoUQ analysis in the existing `discouq_features` object (in the high-confidence tier) must not be changed.
- The five-tier taxonomy description paragraph must be preserved.

### Cross-section references:
- §4.4 (Content Structuring): The structuring agent uses the WYHTB analysis to determine how to present weak-confidence findings in the narrative.

### Directive compliance:
- Directive 14 (Quality Standard): Goldman-grade analysis surfaces and quantifies uncertainty rather than hiding it. WYHTB is a standard tool in strategic analysis.
- Directive 6 (FITFO Standard): A senior McKinsey consultant presented with a 50% confidence finding immediately asks "what would have to be true for this to be right?" The WYHTB step mechanizes this instinct.

---

## Change #22: Add ADaPT-Style Reactive Decomposition Within L1 Research Rounds

**MASTER-SYNTHESIS Reference:** Section 9, Change #22
**Phase Classification:** [Phase 1]
**Phase Rationale:** Not explicitly listed in Directive 13. Fails the deferral test: ADaPT-style reactive decomposition is how the shallow initial issue tree (2–3 levels, 8–20 leaf nodes) becomes more detailed without requiring upfront deep planning. If this mechanism is not specified in Phase 1, the system will either: (a) produce shallow research on branches that turn out to be complex, or (b) require deep upfront planning (which the architecture explicitly avoids). The mechanism must be part of the data flow definition because it requires the agent output schema to carry a `complexity_report` field that triggers orchestrator action.
**Location in CAPSTONE-PLAN-v2.md:** Section 4, §4.1 or as a new §4.8, and within the iterative research loop (§4.5 from Change #11)

### What exists now:
The ADaPT pattern is referenced in the MASTER-SYNTHESIS but does not appear in CAPSTONE-PLAN-v2.md. Section 4.1 describes agent execution but provides no mechanism for agents to signal that their assigned branch is more complex than anticipated.

### What it should say:
Add the following as item 6 in the §4.1 numbered list (after the existing item 5 replacement from Change #18):

```
6. **Signals complexity reactively.** `[BATCH 2 UPDATE]` When a research agent discovers that its assigned branch is substantially more complex than the issue tree anticipated — more sub-questions, more data sources, more analytical depth required — it does not silently truncate its research. It includes a `complexity_report` in its structured output:

```python
class ComplexityReport(BaseModel):
    is_complex: bool
    complexity_reason: str  # why this branch is more complex than anticipated
    suggested_decomposition: list[str]  # proposed sub-branches
    estimated_additional_tasks: int
    blocking: bool  # does complexity block this finding from being usable?
```

The orchestrator receives the `complexity_report` and makes an adaptive decomposition decision:

| Complexity signal | Orchestrator response |
|------------------|----------------------|
| `is_complex=True, blocking=False` | Log complexity; allow finding to proceed; spawn additional subagents for the sub-branches in the current round |
| `is_complex=True, blocking=True` | Pause this task; trigger issue tree refinement (Step 10 feedback loop); add sub-branches to pending tasks for next round |
| `is_complex=False` | No action; continue normally |

This is ADaPT-style (Adaptive-Depth Planning and Task decomposition) reactive decomposition: the issue tree starts shallow (2–3 levels) and deepens adaptively when research agents report genuine complexity. The +28.3% improvement over deep upfront planning (ADaPT, 2025) comes from avoiding two failure modes simultaneously: (1) deep upfront decomposition on branches that turn out to be simple (wasted planning effort), and (2) shallow decomposition that produces superficial research on branches that turn out to be complex (poor output quality).

**Round-level vs. engagement-level:** If complexity is detected within a round and `blocking=False`, the orchestrator spawns additional subagents within the same round. If complexity requires full issue tree revision, it is deferred to the next round's planning step (Step 10 feedback loop → Step 3 redeccomposition). Three replanning cycles maximum (as specified in §4.5).
```

Also add, in §4.5's ADaPT-style deepening note (from Change #11), a cross-reference:

```
**ADaPT-style deepening:** When a research agent reports that a branch is more complex than the issue tree anticipated (more sub-questions, more data sources, more analytical depth required), the orchestrator can adaptively deepen that branch — spawning additional subagents for the branch's sub-questions within the same round. See §4.1 item 6 for the `complexity_report` schema and decision logic.
```

### Preservations:
- All existing items 1–5 in the §4.1 numbered list must be preserved (items 1–4 unchanged; item 5 updated by Change #18).
- The Carlini git-based coordination pattern citation (item 1) must be preserved.

### Cross-section references:
- Change #4 (Issue Tree Construction): The shallow start (8–20 leaf nodes) is explicitly designed to enable this reactive deepening.
- Change #11 (Iterative Research Loop): The "ADaPT-style deepening" note in §4.5 references this mechanism.
- Step 10 (Feedback Loop) in the 10-step pipeline: Branch complexity signals are one of the inputs to the feedback loop.

### Directive compliance:
- Directive 2 (MECE Issue Tree): "The issue tree should be a living document that updates as research reveals new branches." ADaPT-style decomposition is the mechanical implementation of this directive.
- Directive 3 (Iterative Multi-Round Research): Complexity-triggered decomposition is part of the answer to "Who decides when to spawn new research?"
- Directive 5 (Build Philosophy): Shallow tree with reactive deepening is the "right abstraction" that enables later sophistication without rework.

---

## Orchestrator Notes: Coordinating the 22 Changes

The following notes are for the orchestrator applying these specifications to CAPSTONE-PLAN-v2.md:

**Section 3 structural changes:**
1. §3.4 and §3.5 are replaced by the new 10-step pipeline (Change #1). The new §3.4 is the unified 10-step flow.
2. §3.6 receives modifications to the `research-tasks.json` schema (Changes #9 and #10) and the design decisions list (expanded to 9 items). The existing prose structure of §3.6 is preserved.
3. §3.7 (Task-vs-Job Boundary) is unchanged.
4. New §3.8 (Engagement Classifier) and §3.9 (Intent Clarification) are added after §3.7.

**Section 4 structural changes:**
1. §4.1 numbered list gains items from Changes #18 and #22 (items 5 and 6 respectively, replacing the existing item 5).
2. §4.2 is substantially rewritten (Change #14) with additions from Changes #15, #16, and #17. All existing citations are preserved.
3. §4.3 Phase 2 heading and aggregation prose is updated (Change #20) and WYHTB analysis is added (Change #21). Confidence map JSON gains the `wyhtb_analysis` field.
4. §4.4 is unchanged.
5. New §4.5 (Iterative Research Loop), §4.6 (Scope-Change Detection), and §4.7 (Memory Scratchpad) are added after §4.4.

**JSON schema coordination:**
- Changes #7, #9, and #10 all modify the `research-tasks.json` schema. These must be applied together to produce a single updated JSON example that incorporates the DAG structure, priority scoring, and end product specification simultaneously.
- Change #20 and #21 together modify the confidence map JSON. Apply as a unit.

**Phase tagging summary:**
- [Phase 1, no caveat]: Changes #1 (architecture), #2, #4, #5, #6, #9, #10, #11, #12, #13, #14, #15, #16, #17, #18, #19, #20, #21, #22
- [Phase 1 heuristic, Phase 2 full]: Change #7 (VOI scoring)
- [Phase 2, call site in Phase 1]: Change #8 (CBR Observation Library query)
- [Phase 1 base, Phase 2 escalation]: Change #21 (WYHTB — field ships Phase 1; multi-analyst challenges Phase 2)
- [Phase 1 Decision-First CoT, Phase 2 TiCoder]: Change #3
