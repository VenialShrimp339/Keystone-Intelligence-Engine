# Analysis: Report 07 — Adaptive Evaluation
*Analyzed: 2026-04-05 | Priority: Tier 3 (MEDIUM) | Report quality: HIGH*

---

## Executive Summary

The report resolves the predefined-vs-dynamic rubric question definitively: it is a false dichotomy, and the answer is a two-tier hybrid. Four dimensions (Intent Alignment, Intellectual Honesty, Completeness, Narrative Coherence) function as universal gates with minimum pass thresholds; six dimensions flex weights by engagement type. The current plan's two override profiles (estimative / current intelligence) are confirmed as valid starting templates but should expand to 8-10 engagement-type profiles covering the actual Keystone consulting portfolio. The sprint contract pattern between planner/evaluator and generator is validated by three independent sources (Anthropic's March 2026 blog, Vertex AI adaptive rubrics, AdaRubric ICLR 2025). The most urgent finding: LLM judges are empirically unreliable precisely where consulting quality matters most — Quantitative Rigor and Analytical Depth — and the current plan does not adequately address this. The geometric mean aggregation recommendation conflicts with the plan's implicit weighted sum and should be adopted. The issue tree -- evaluation weight coupling is novel and architecturally sound, directly serving Jack's Rigidity Problem directive.

Report quality is HIGH. Sources are current (ICLR 2025, Anthropic March 2026, Vertex AI production documentation). Most claims are VERIFIED or CREDIBLE. The SOS-Bench findings were already cited in CAPSTONE-PLAN-v2.md but the report extends them with more granular reliability hierarchy and specific bias types from the CALM framework that the plan does not yet incorporate.

---

## Key Findings (ranked by implementation impact)

### 1. Geometric Mean Aggregation Should Replace Weighted Sum

**Finding:** Three independent frameworks -- Stanford HELM, the MQM translation quality standard, and AdaRubric -- use geometric mean aggregation specifically because it prevents dimension compensation. A single failing dimension (e.g., Intellectual Honesty = 0) zeros out the aggregate, making failures visible rather than masked.

**Evidence quality:** VERIFIED (Stanford HELM is production; MQM is an industry standard for translation quality; AdaRubric is ICLR 2025 peer-reviewed).

**Assessment:** The current plan specifies a ten-dimension rubric with weights summing to 1.0 but does not specify the aggregation method. Weighted sum is the implicit default. This is a concrete architectural gap. A consultant deliverable with fabricated confidence levels but excellent narrative quality would score deceptively well under weighted sum. Under geometric mean, the same output fails unambiguously.

**Verdict:** ADOPT. Implement geometric mean as the default aggregation in Layer 3 (Prometheus 2 multi-rubric scoring). Exception: the dimensional scores should still be reported individually regardless of aggregation method, preserving diagnostic value.

**Connects to:** Component #6 (Evaluator stack), Layer 3 specifically. No other components affected.

**Implementation note:** Geometric mean requires all dimension scores to be on the same bounded scale (e.g., 0-10). If any dimension scores 0, the aggregate is 0. Practically, implement as: `exp(mean(log(score_i + epsilon)))` to avoid log(0), with epsilon = 0.01. Document the epsilon choice explicitly so calibration against Jack's scores can account for it.

---

### 2. Four Universal Gates, Six Adaptive Dimensions

**Finding:** The 10-dimension rubric splits into two tiers with different evaluation logic:

**Tier 1 -- Universal gates (always apply, minimum threshold mandatory regardless of engagement type):**
- Intent Alignment: foundational relevance filter; a "right-side up" deliverable is prerequisite to all other quality
- Intellectual Honesty: MASK benchmark (2025) measures this specifically; the plan's existing framing is correct
- Completeness: MECE principle demands "collectively exhaustive" -- this cannot be downweighted for any engagement
- Narrative Coherence: logical structure is a prerequisite for any usable deliverable

**Tier 2 -- Adaptive weights by engagement type:**

| Engagement type | Upweight | Downweight |
|---|---|---|
| Market sizing / financial modeling | Quantitative Rigor, Source Quality, Calibrated Confidence | Evaluative Surprise |
| Due diligence | Source Quality, Quantitative Rigor, Intellectual Honesty, Calibrated Confidence | Narrative Coherence |
| Strategy development | Analytical Depth, Evaluative Surprise, Actionability | (all moderate) |
| Turnaround / restructuring | Actionability, Quantitative Rigor, Analytical Depth | Evaluative Surprise, Source Quality |
| Organizational transformation | Narrative Coherence, Analytical Depth, Evaluative Surprise | Quantitative Rigor |
| Regulatory / compliance | Source Quality, Completeness, Calibrated Confidence | Evaluative Surprise |
| Innovation / market entry | Evaluative Surprise, Analytical Depth, Actionability | Source Quality |

**Evidence quality:** CREDIBLE. Synthesized from AdaRubric, OECD DAC evaluation criteria, Bloom's Revised Taxonomy, MQM, and consulting quality literature. No single source verifies the full table, but the component sources are reputable.

**Assessment:** This maps precisely to Jack's Rigidity Problem directive: fixed weight profiles work for known engagement types but fail novel ones. The tier split is a clean architectural principle. Narrative Coherence in Tier 1 (universal gate) is noted -- this is consistent with the plan's existing 5% weight (reduced from 10% in Session 9 fix), but as a universal gate it receives a floor threshold even if its adaptive weight is low.

**Verdict:** ADOPT. The tier 1/tier 2 split should be explicit in the plan. The engagement-type table should be the initial template set for the 8-10 profiles recommended in Finding 3.

**Connects to:** Component #6 (Evaluator stack), Component #5 (Specification Engine -- which determines engagement type), Jack's Directive #1 (Rigidity Problem).

---

### 3. Expand to 8-10 Engagement-Type Templates (Replace 2-Profile System)

**Finding:** The current plan has two predefined override profiles (estimative vs. current intelligence) borrowed from ICD 203. This framing works for intelligence-style research tasks but misses the consulting engagement diversity that Jack's Directive #4 (Engagement Scope) explicitly requires: operations, growth, M&A, restructuring, across diverse industries. The Anthropic hybrid pattern -- predefined profiles per task type, sprint contract adds dynamic specificity per unit of work -- validates expanding to more profiles.

**Evidence quality:** VERIFIED for Anthropic's approach (March 2026 engineering blog). The specific profile count (8-10) is the report's recommendation, not empirically derived -- treat as CREDIBLE guidance.

**Assessment:** This is a direct conflict between the current plan and the report, and the report is right. The two-profile system was appropriate given Batch 1 research which focused on market research engagements. Batch 2 Report #5 (engagement taxonomy) should have defined the full taxonomy -- these templates should be derived from that report's findings. The current two profiles become two members of the expanded set, not the entire system.

**Verdict:** ADOPT. Design the evaluation profile as a configuration object generated by the Specification Engine (from the issue tree and engagement classification), with the 8-10 templates as defaults when dynamic generation is uncertain. The two existing profiles (estimative, current intelligence) remain valid as sub-types within the broader taxonomy.

**Connects to:** Component #5 (Specification Engine), Component #6 (Evaluator stack), Report 05 (engagement taxonomy -- direct dependency per task brief), Report 10 (Specification Engine -- direct feed per task brief).

---

### 4. Sprint Contract Generation from Issue Tree Branches

**Finding:** The report proposes a mechanically specific three-step process for generating evaluation weights from the issue tree: (1) classify each branch by Bloom's Taxonomy cognitive level (Remember/Understand vs. Analyze vs. Evaluate/Create), (2) classify each branch by quantitative vs. qualitative nature, (3) generate weighted evaluation criteria from the classification. The OECD DAC principle is cited: "The criteria should not be applied mechanistically."

**Evidence quality:** CREDIBLE (Bloom's Revised Taxonomy is established; the three-step mapping to evaluation weights is the report's own synthesis -- no direct empirical validation, but logically sound).

**Assessment:** This is the most architecturally novel finding in the report. The issue tree already exists as a Specification Engine output (Jack's Directive #2). The report proposes using it as the primary input to evaluation profile generation, not just as a research decomposition tool. This closes a design gap: the current plan says evaluation profiles should be engagement-specific but does not specify the mechanism for generating them. The Bloom's classification provides a principled non-arbitrary basis.

**Specific mapping:**
- Issue tree branches at Remember/Understand level -> upweight Completeness, Source Quality
- Branches at Analyze level -> upweight Analytical Depth, Quantitative Rigor
- Branches at Evaluate/Create level -> upweight Calibrated Confidence, Evaluative Surprise, Actionability

**Verdict:** ADOPT. This is the mechanical specification the plan was missing. Implement as a sub-step within the Specification Engine (after issue tree generation, before dispatching to research agents): the Evaluator agent reads the classified issue tree and proposes dimension weights, then negotiates with the generator via sprint contract before research begins.

**Connects to:** Component #5 (Specification Engine), Component #6 (Evaluator stack), Jack's Directives #1, #2, #3.

---

### 5. LLM Judge Reliability Hierarchy Requires Dimension-Specific Verification Strategies

**Finding:** The CALM framework (ICLR 2025) identified 12 biases with task-specific patterns. The SOS-Bench reliability hierarchy (previously known in general terms) is now granular:

- High reliability (~80% human agreement): factual QA with reference answers, general instruction following
- Moderate reliability: summarization, code with test suites; pairwise > pointwise
- Low reliability (58-68%): domain-expert tasks, creative writing, mathematical reasoning
- Very low reliability (~47%, kappa ~0.3): open-ended reasoning, multilingual

**Three dominant bias patterns by task type:**
- Fallacy oversight bias: scientific and math reasoning -- judges miss logical errors
- Authority bias: alignment tasks -- fake citations inflate scores
- Refinement bias: humanities tasks -- knowing an answer was revised inflates scores

**For consulting specifically:** Quantitative Rigor is in the "low reliability" zone (mathematical reasoning). Analytical Depth involves open-ended reasoning at "very low reliability." These are precisely the two highest-value dimensions for consulting quality.

**Evidence quality:** VERIFIED (ICLR 2025 peer-reviewed, multi-institution: Arthur AI, NYU, Columbia; 152K+ data points; four judge models tested).

**Assessment:** The current plan acknowledges SOS-Bench style bias in a general way but does not differentiate verification strategy by dimension. This is a concrete gap. The plan specifies Prometheus 2 as the Layer 3 judge for all 10 dimensions equally. Given the reliability data, Quantitative Rigor and Analytical Depth should be treated differently: programmatic verification for the former, multi-judge panels with position-switching for the latter.

**Verdict:** ADOPT with specifics:
1. Quantitative Rigor: add programmatic verification as a complement to Prometheus 2 (Layer 1 / Layer 2 can handle numerical consistency checking already -- extend Layer 1 deterministic checks to cover quantitative reasoning steps, not just output numbers)
2. Analytical Depth: implement position-switching (evaluate the claim, then evaluate the opposite framing) -- this is already referenced in the plan but should be mandatory for this dimension
3. Authority bias (Intellectual Honesty / Source Quality): relevant because fabricated citations with authoritative-sounding provenance can inflate these dimensions -- the Layer 2 citation gate is the correct mitigation, but it must check ALL cited authority claims, not just DOI-resolvable references

**Connects to:** Component #6 (Evaluator stack), Layers 1-3 specifically.

---

### 6. Anthropic Sprint Contract Pattern: Bidirectional Negotiation, Not Generator-Proposed-Only

**Finding:** The report clarifies a structural detail: Anthropic's sprint contracts are bidirectionally negotiated, not generator-driven. The Evaluator proposes the evaluation contract (based on the issue tree); the Generator reviews and negotiates; both iterate to agreement. The consumer-driven contract testing (Pact) analogy is directionally wrong for this pattern -- Pact is consumer-driven, sprint contracts are bidirectional.

The Anthropic model also carries a decay warning: "Every component in a harness encodes an assumption about what the model cannot do on its own. Those assumptions decay as models improve." Upgrading from Sonnet 4.5 to Opus 4.6 removed sprint decomposition entirely in their system.

**Evidence quality:** VERIFIED (Anthropic engineering blog, March 24, 2026, named author Prithvi Rajasekaran).

**Assessment:** The current plan describes sprint contracts as negotiated but does not specify who proposes. The report clarifies: the Evaluator proposes, the Generator reviews. This is the correct directionality for quality assurance -- the entity responsible for standards sets them, the entity responsible for production confirms they are achievable. The decay warning is important for system design: the sprint contract infrastructure should be an optional scaffold, not a hard dependency, so it can degrade gracefully as base model capabilities improve.

**Verdict:** ADOPT. Specify in the plan: Evaluator agent proposes sprint contract criteria (derived from issue tree classification), Generator agent reviews and accepts or requests modification, both commit to the final contract before research begins. Design the sprint contract as a file-based artifact (consistent with Settled Decision #8: file-based agent isolation) that persists as an engagement record.

**Connects to:** Component #5 (Specification Engine), Component #6 (Evaluator stack), Settled Decision #5 (filesystem-based isolation), Jack's Directive #7 (HITL gates -- the sprint contract review is a natural sub-gate before the full issue tree HITL review).

---

### 7. MBB Quality Architecture Confirms Explicit Rubrics as Competitive Advantage

**Finding:** No MBB firm publishes a formal quality rubric. Quality enforcement is through cultural norms (McKinsey's obligation to dissent, Bain's True North), communication frameworks (MECE, Pyramid Principle), and tiered review (analyst -> manager -> partner). Partners review decks by reading only action titles -- if the argument doesn't hold from titles alone, the deck fails. Keystone Engine's explicit rubric approach exceeds industry practice in evaluation formality.

**Evidence quality:** CREDIBLE (well-documented consulting practice; specific details like "partner reads only action titles" are widely reported; BCG's 5-dimension evaluation system is referenced without a specific citable source).

**Assessment:** This finding has strategic value for the capstone's research narrative. The system is not imitating consulting quality -- it is formalizing it. The MBB principles also map directly to existing rubric dimensions: Pyramid Principle -> Narrative Coherence, "so what?" test -> Actionability, source citation requirements -> Source Quality, right-side-up deliverable -> Intent Alignment. These mappings should be documented in the rubric specification to provide calibration anchors.

**Verdict:** ADOPT for framing. Incorporate the MBB-to-rubric-dimension mapping table into the Evaluator calibration documentation. This gives Jack concrete grounding for scoring calibration deliverables and explains the rubric's design rationale in the capstone paper.

**Connects to:** Component #10 (Evaluator calibration), CAPSTONE-PLAN-v2.md Section 5.

---

### 8. Graceful Degradation Principle for Evaluation Scaffolding

**Finding:** Anthropic's key architectural insight: "When they upgraded from Sonnet 4.5 to Opus 4.6, they removed sprint decomposition entirely because the model could sustain coherent work without it." Evaluation scaffolding should be designed to degrade gracefully as models improve, not be permanently embedded as hard dependencies.

**Evidence quality:** VERIFIED (same Anthropic source as Finding 6).

**Assessment:** The current plan does not address scaffolding lifetime or degradation. This is not a Phase 1 concern -- the system needs the scaffolding now. But it is an architectural concern: if sprint contract negotiation is hardwired into the pipeline as a mandatory step, removing it later requires rework. If it is a configurable optional step, the system improves with models automatically.

**Verdict:** ADOPT as design principle, DEFER implementation. Design sprint contracts as a `skip_if_capable` configurable feature in the engagement config. Do not implement the skip logic in Phase 1 -- just ensure the architectural abstraction supports it.

**Connects to:** Component #5, Component #6, Jack's Directive #5 (Build Philosophy: right architecture, staged depth).

---

## Architectural Decisions This Enables

**Decision A: Geometric Mean Aggregation (Resolves Unspecified Gap)**
The aggregation method for the 10-dimension rubric was unspecified. Adopt geometric mean. Implement in Layer 3. Document epsilon choice for calibration consistency.

**Decision B: Explicit Tier 1 / Tier 2 Rubric Split (Extends Settled Decision #11)**
Settled Decision #11 (Narrative Coherence 5%) should be extended: Intent Alignment, Intellectual Honesty, Completeness, and Narrative Coherence are Tier 1 universal gates with floor thresholds. The remaining six dimensions are Tier 2 with engagement-adaptive weights. This is not a change to the weights -- it is an explicit structural designation that affects how failures are handled (Tier 1 floor failure = output rejected regardless of Tier 2 scores).

**Decision C: Issue Tree Branch Classification Drives Weight Generation**
The Specification Engine produces a classified issue tree (Bloom's cognitive level + quantitative/qualitative nature per branch). The Evaluator agent uses this classification to propose dimension weights for the sprint contract. This is the mechanical specification for how evaluation profiles are generated dynamically -- closing the gap between "profiles should be engagement-specific" and "here is how they are generated."

**Decision D: Expand to 8-10 Engagement-Type Profiles**
Replace the two-profile (estimative/current intelligence) system with an expanded template library covering the Keystone consulting portfolio. The two existing profiles become members of this library, not the entire system. The engagement-type table in Finding 2 is the initial template set pending confirmation from Report 05 findings.

**Decision E: Dimension-Specific Verification Strategies**
Layer 3 (Prometheus 2) is not sufficient alone for Quantitative Rigor (mathematical reasoning, low LLM reliability) or Analytical Depth (open-ended reasoning, very low reliability). Quantitative Rigor gets programmatic verification complement. Analytical Depth gets mandatory position-switching. Both are Layer 3 enhancements, not new layers.

---

## Changes to Existing Plan

**CAPSTONE-PLAN-v2.md Section 5 changes needed:**

1. **Aggregation method (explicit gap):** Add geometric mean specification to Layer 3 description. This is additive, no conflict with existing text.

2. **Tier 1/Tier 2 split (extension):** The current plan says the Evaluator "exercises judgment" and has a 10-dimension rubric but does not designate universal gates vs. adaptive dimensions. Add the explicit tier designation. This extends but does not contradict existing architecture.

3. **Engagement-type profiles (extension):** The plan currently mentions two override profiles. Expand to 8-10. The two existing profiles are preserved as-is; additional profiles added. This is additive.

4. **Sprint contract directionality (clarification):** Specify that the Evaluator proposes and the Generator reviews, not the reverse. Current text says "negotiated" without directional specification.

5. **Issue tree -> evaluation weight coupling (new mechanism):** The three-step Bloom's classification mechanism (Finding 4) is not in the plan. Add as a sub-step of Specification Engine output: "Evaluator reads classified issue tree -> proposes dimension weights -> sprint contract negotiation."

6. **Dimension-specific verification strategies (extension):** Current plan treats all 10 dimensions equivalently in Layer 3. Add differentiated strategy for Quantitative Rigor (programmatic complement) and Analytical Depth (position-switching mandatory).

**No conflicts with settled decisions.** All changes are additive extensions or clarifications.

---

## Open Questions Remaining

**Q1: What engagement-type profiles does Report 05 define?**
The engagement taxonomy report (Report 05) should be the source for the engagement-type profile list. This analysis uses the report's proposed table as a placeholder. The final profile set should be reconciled with Report 05 before finalizing the evaluation profile library.

**Q2: How does geometric mean interact with sprint contract pass/fail gates?**
Sprint contracts currently specify hard binary thresholds: fail any criterion = reject. If a section has 27 testable criteria and one fails, it rejects. The geometric mean applies to the 10-dimension rubric. These are parallel mechanisms -- sprint contracts are binary at the criterion level, geometric mean applies to dimension-level scores. Need to clarify: does a Tier 1 dimension floor breach trigger an outright rejection (like a sprint contract criterion fail), or does it generate a low-but-nonzero geometric mean score? The cleaner design is: Tier 1 floor breach = rejection (no further scoring); Tier 2 geometric mean computed on passing outputs.

**Q3: How is Bloom's classification automated reliably?**
The issue tree -> Bloom's level classification requires the Specification Engine to label each branch. Bloom's classification of ambiguous consulting branches (e.g., "assess competitive dynamics in the auto body repair market") is not trivially automated. This is judgment-dependent. What is the fallback when classification is uncertain? One option: default all branches to Analyze level (Analytical Depth + Quantitative Rigor emphasis) when uncertain, which is a conservative and reasonable default for consulting work.

**Q4: How does Report 10 (Specification Engine) change the sprint contract proposal mechanism?**
Report 10 is identified as the downstream consumer of this report's findings. The sprint contract proposal mechanism requires the Specification Engine to produce a classified issue tree before the Evaluator can propose weights. The design of the Specification Engine (Report 10) determines whether this sequencing is feasible and at what point in the pipeline it occurs. This analysis assumes the issue tree is available before research agents are dispatched -- confirm this assumption holds in Report 10's design.

**Q5: What is the right threshold for Tier 1 universal gates?**
The report identifies four Tier 1 dimensions but does not specify minimum passing thresholds. This is a calibration question that requires Jack's scored deliverables (planned for Week 6+, per CURRENT-STATE.md). Proposed placeholder: Tier 1 minimum = 6/10 on any dimension triggers a warning; < 4/10 triggers rejection. These numbers should be treated as provisional until calibration data is available.
