# Change Specification B: Sections 5 and 6
*Track 1 Subagent B | Changes #23-38 | 2026-04-05*
*Source authority: JACK-ARCHITECTURAL-DIRECTIVES.md + MASTER-SYNTHESIS.md Section 9*

---

## Summary of Assignment

This file specifies 16 changes to CAPSTONE-PLAN-v2.md covering:
- Section 5 (Evaluator): Changes #23-29 — rubric aggregation, tier split, profile expansion, sprint contracts, verification strategies, graceful degradation
- Section 6 (Retrieval): Changes #30-38 — Component #3 split, embedding model, contextual retrieval, reranking, chunking, removal of Semantic Router and Bifrost, search API rationalization, compiled wiki

The orchestrator agent merges this spec with Track A (Sections 1-4) and Track C (Sections 7-12) and executes all edits.

Phase classification follows Directive 13 exactly. Where a change is Phase 2+, the spec still defines what the text should ultimately say so the orchestrator can add appropriate deferral language or placeholder subsections.

---

## Change #23: Geometric Mean as Rubric Aggregation Method

**MASTER-SYNTHESIS Reference:** Section 9, Change #23
**Phase Classification:** Phase 1
**Phase Rationale:** Directive 13 explicitly lists "Geometric mean rubric aggregation" as a Phase 1 ship item. It affects the scoring formula in Layer 3, which is foundational — retrofitting it after profiles are calibrated would force recalibration of every threshold.
**Location in CAPSTONE-PLAN-v2.md:** Section 5, subsection 5.3, around line 562; and subsection 5.10 Pass 1, around line 665.

### What exists now:

Section 5.3 ends with (line 579):

> Weights are deliberately calibrated *away* from where LLMs naturally perform well (coherent prose, comprehensive coverage) and *toward* where they naturally underperform (analytical novelty, quantitative rigor, actionable insight) — following Anthropic's finding that evaluator dimensions should target the generator's weakest areas to maximize corrective impact. The weight reduction on Analytical Depth (15% to 12%) and Completeness (10% to 8%) funds the two new dimensions while preserving the substance-over-style weighting.

Section 5.10 Pass 1 (line 665):

> **Pass 1: Dimensional Scoring.** The ten-dimension rubric, executed through Layer 3 of the evaluation stack (Prometheus 2). One prompt per dimension. Produces ten individual scores with specific feedback per dimension.

The document contains no explicit statement of the aggregation method. The implied method, given the listed weights that sum to 100%, is weighted arithmetic mean.

### What it should say:

**In Section 5.3**, replace the closing paragraph with:

> Weights are deliberately calibrated *away* from where LLMs naturally perform well (coherent prose, comprehensive coverage) and *toward* where they naturally underperform (analytical novelty, quantitative rigor, actionable insight) — following Anthropic's finding that evaluator dimensions should target the generator's weakest areas to maximize corrective impact. The weight reduction on Analytical Depth (15% to 12%) and Completeness (10% to 8%) funds the two new dimensions while preserving the substance-over-style weighting.
>
> **`[BATCH 2 UPDATE]` Aggregation method: geometric mean, not weighted sum.** The ten dimension scores are aggregated using the weighted geometric mean:
>
> ```
> composite_score = ∏(score_i ^ weight_i)   [i = 1..10, weights sum to 1.0]
> ```
>
> Weighted arithmetic mean (the implicit default) allows dimension compensation: a Narrative Coherence score of 9 can mask an Intellectual Honesty score of 3 if the weights are favorable. The geometric mean prevents this — a near-zero score on any dimension drives the composite toward zero regardless of other dimension performance. Three independent evaluation frameworks (Stanford HELM, MQM, AdaRubric) have independently adopted geometric mean specifically for this reason. This property becomes structurally important under the Tier 1/Tier 2 split (§5.3 below): Tier 1 gates impose hard floors precisely because the geometric mean alone does not fully prevent compensation across tiers.

**In Section 5.10, Pass 1**, replace with:

> **Pass 1: Dimensional Scoring.** The ten-dimension rubric, executed through Layer 3 of the evaluation stack (Prometheus 2). One prompt per dimension. Produces ten individual scores with specific feedback per dimension. The ten scores are aggregated via weighted geometric mean (see §5.3) — not weighted sum. Tier 1 gate scores are checked first; any Tier 1 score below the floor threshold triggers rejection before the geometric mean is computed for Tier 2 dimensions.

### Preservations:

All existing content in §5.3 above the closing paragraph is preserved exactly. All citations in §5.9 and §5.10 are preserved. The ten-dimension table is preserved (it is restructured separately under Change #24).

### Cross-section references:

The Layer 3 description in §5.9 (line 653) references "the ten-dimension rubric" without specifying aggregation. That sentence should be updated: replace "with the ten-dimension rubric" with "with the ten-dimension rubric, aggregating via weighted geometric mean (§5.3)." This is a minor in-section update, not a cross-section dependency.

### Directive compliance:

Directive 13 (Phase 1 list, geometric mean). Directive 14 (quality standard — geometric mean matches MBB-caliber evaluation rigor). No directives conflict.

---

## Change #24: Tier 1 (Universal Gates) / Tier 2 (Adaptive) Rubric Split

**MASTER-SYNTHESIS Reference:** Section 9, Change #24
**Phase Classification:** Phase 1
**Phase Rationale:** Directive 13 explicitly lists "Tier 1/Tier 2 rubric split" as Phase 1. The split is foundational to how profiles (Change #25) work — adaptive Tier 2 weights only make sense once Tier 1 gates are structurally defined. Building profiles without the tier structure would require re-architecting the rubric later.
**Location in CAPSTONE-PLAN-v2.md:** Section 5, subsection 5.3, the rubric table, around lines 566-578.

### What exists now:

The current rubric table has 10 dimensions listed without tier classification. The table header is:

```
| Dimension | Weight | Eval Type | What It Measures | Sub-Criteria |
```

The 10 dimensions as currently listed (lines 568-577):
1. Analytical Depth — 12% — Judgment-dependent
2. Source Quality — 10% — Machine-checkable + Expert
3. Quantitative Rigor — 15% — Machine-checkable + Expert
4. Narrative Coherence — 10% — Judgment-dependent
5. Completeness — 8% — Machine-checkable
6. Actionability — 15% — Expert-checkable
7. Intent Alignment — 15% — Expert-checkable
8. Intellectual Honesty — 10% — Judgment-dependent
9. Evaluative Surprise — 5% — Judgment-dependent
10. Calibrated Confidence — 5% — Machine-checkable + Expert

Weights total 105% (there appears to be a rounding artifact in the document; the intent is that they sum to 100% and are treated as fractional weights in the geometric mean formula).

There is no Tier column, no floor threshold column, and no distinction between universal gates and adaptive dimensions.

### What it should say:

**Replace the section 5.3 rubric table entirely** with the following restructured version. Note: the heading text before the table is preserved; only the table and the closing paragraph are replaced (the closing paragraph change is covered in Change #23).

> **`[BATCH 2 UPDATE]` Two-tier rubric structure.** The rubric is organized into two tiers. Tier 1 dimensions are universal gates: they apply with identical floor thresholds to every engagement type, every pipeline profile, and every output format. A score below the floor threshold on any Tier 1 dimension triggers immediate rejection — the output does not proceed to Tier 2 scoring or the geometric mean computation. Tier 2 dimensions are adaptive: their weights flex by engagement type (see §5.x, evaluation profiles). The Tier 2 geometric mean is computed only after all Tier 1 gates pass.
>
> **Tier 1: Universal Gates** (floor thresholds — failure = rejection regardless of Tier 2 performance)
>
> | Dimension | Tier 1 Floor | Adaptive Weight Range | Eval Type | What It Measures | Sub-Criteria |
> |-----------|-------------|----------------------|-----------|-----------------|-------------|
> | **Intent Alignment** | ≥ 5/10 | 12-20% | Expert-checkable | Is this answering the question the client actually needs answered? | Does output serve the decision context in RESEARCH.md? *Counterfactual deletion test*: if this section were removed, would the client's decision change? If not, it's padding. The Klarna pattern: "technically correct, strategically wrong" (Jones, "Klarna," Feb 24, 2026) |
> | **Intellectual Honesty** | ≥ 5/10 | 8-14% | Judgment-dependent | Are limitations named? Are contested claims framed as contested? | Is the opposing case steelmanned? Are uncertainty ranges honest or artificially narrow? Does the analysis acknowledge what it cannot determine? |
> | **Completeness** | ≥ 4/10 | 6-12% | Machine-checkable | Are obvious follow-up questions addressed? | *Absence detection*: mandatory completeness checklist with expected topics, perspectives, and data categories. *Deletion test*: would removing any section leave a gap a domain expert would notice? |
> | **Narrative Coherence** | ≥ 5/10 | 5-12% | Judgment-dependent | Does the analysis tell a clear story? Is the "so what?" evident? | *Cross-finding synthesis*: does the analysis tell the story the findings tell *together*, not just sequentially? |
>
> Rationale for these four as universal gates: Intent Alignment and Intellectual Honesty define the minimum standard of intellectual trustworthiness. Completeness prevents the evaluator from rewarding technically sharp but strategically incomplete analysis. Narrative Coherence is designated a universal gate because its weight in the Tier 2 profile system would otherwise fall so low (5% in some profiles) that it could be masked — and an incoherent output is not a usable deliverable regardless of its analytical rigor. As Settled Decision #11 confirmed: Narrative Coherence earns universal gate status precisely because its adaptive weight is low.
>
> **Tier 2: Adaptive Dimensions** (weights flex by engagement type profile — see §5.x)
>
> | Dimension | Phase 1 Default Weight | Adaptive Weight Range | Eval Type | What It Measures | Sub-Criteria |
> |-----------|----------------------|----------------------|-----------|-----------------|-------------|
> | Analytical Depth | **12%** | 10-18% | Judgment-dependent | Are conclusions non-obvious? Is the analysis layered? | *Judgment ratio*: % of output that is analytical judgment vs. information aggregation (Jones, "Artifacts > Credentials," Mar 26, 2026) |
> | Source Quality | 10% | 8-15% | Machine-checkable + Expert | Are sources authoritative and diverse? | *Signal depth* — triangulated/hard-to-access sources over press releases. Pre-rubric binary gate: citation existence verified via CrossRef/Semantic Scholar/OpenAlex (fabricated citation = immediate rejection) |
> | Quantitative Rigor | 15% | 10-22% | Machine-checkable + Expert | Are claims supported by data? Uncertainties quantified? | *Adversarial robustness*: do findings hold if key assumptions shift ±20%? *Precision calibration*: are numbers reported at appropriate precision for the underlying data quality? |
> | Actionability | 15% | 10-20% | Expert-checkable | Could a consultant advise a client based on this? | *Monday-morning actionability*: segmented by role, immediately executable. *Trendslop detection*: flag generic strategic recommendations that could apply to any company in any industry (HBR March 2026, 15K+ trials) |
> | Evaluative Surprise | **5%** | 3-8% | Judgment-dependent | Does the output contain at least one finding the requester didn't already suspect? | **NEW.** The conscious-competence ceiling: rubrics alone create proficiency, not expertise (Dreyfus model). This dimension detects competent mediocrity — outputs that satisfy every checklist item while containing zero genuine insight. A perfectly scored but unsurprising output caps at 95%. |
> | Calibrated Confidence | **5%** | 4-8% | Machine-checkable + Expert | Are probability assessments calibrated to evidence quality? | **NEW.** Operationalizes ICD 203 calibrated probability language: "almost certainly" (>95%), "highly likely" (80-95%), "likely" (60-80%), "roughly even" (40-60%), "unlikely" (20-40%), etc. Confidence ranges must match the evidence base. Overconfident claims on weak evidence and underconfident claims on strong evidence both penalized. |
>
> Phase 1 default weights represent the general-purpose consulting profile (used when no engagement-specific profile is active). Adaptive weight ranges are constrained by engagement type profiles (Phase 2; see §5.x). The geometric mean is computed over Tier 2 dimensions only, using weights normalized to sum to 1.0 within the active profile.

### Preservations:

The sub-criteria for each dimension are preserved exactly from the existing table. All inline citations are preserved. The table structure is extended, not replaced — the analytical content of each dimension row is identical to the current plan.

### Cross-section references:

Section 5.5 (Multi-Tiered Evaluation Intensity) uses the terms "Light-touch," "Standard," and "Deep" — these are pipeline depth tiers, not rubric tiers. They should be renamed "Light-touch evaluation profile," "Standard evaluation profile," and "Deep evaluation profile" to avoid collision with the new Tier 1/Tier 2 terminology. This is a minor wording update in §5.5.

Section 5.9 Layer 3 (line 653): "ten-dimension rubric" reference is preserved; no change needed. The orchestrator should ensure the Layer 3 description notes that Tier 1 gate dimensions are checked before Tier 2 scoring begins.

### Directive compliance:

Directive 13 (Phase 1 list — "Tier 1/Tier 2 rubric split"). Directive 14 (quality standard — two-tier structure matches MBB evaluation rigor where basic intellectual honesty standards are non-negotiable gates before analytical scoring begins). Directive 5 (build philosophy — correct interface now; profile expansion in Phase 2 without rework).

---

## Change #25: Expand from 2 Evaluation Profiles to 8-10

**MASTER-SYNTHESIS Reference:** Section 9, Change #25
**Phase Classification:** Phase 2+ (start with 3-4 profiles in Phase 1)
**Phase Rationale:** Directive 13 explicitly defers "8-10 engagement-type evaluation profiles (start with 3-4, expand)." The profile expansion requires calibration data from real engagements, which does not exist in Phase 1. The Phase 1 deliverable is the profile infrastructure (the Tier 2 weight-flexibility mechanism from Change #24) with 3-4 seed profiles covering the highest-priority engagement types. Expansion to 8-10 happens as calibration data accumulates.
**Location in CAPSTONE-PLAN-v2.md:** Section 5, subsection 5.3, following the rubric table. A new subsection should be added: §5.x "Evaluation Profiles."

### What exists now:

The current document (around line 564) references two profiles in passing:

> Each dimension is classified by evaluation type to determine which layers of the five-layer evaluation stack (Section 5.9) handle it

And in §5.5 the tiers reference "Estimative" and "Current Intelligence" as the two existing profiles (inherited from L0 spec language). There is no dedicated profile subsection in Section 5.

### What it should say:

**Add a new subsection §5.x immediately after §5.3** (before §5.4 Calibration):

---

> ### 5.x Evaluation Profiles `[BATCH 2 UPDATE]`
>
> Tier 2 dimension weights flex by engagement type through evaluation profiles. A profile is a named weight vector for the six Tier 2 dimensions, constrained by the ranges specified in §5.3. The Specification Engine assigns the active profile at engagement initialization based on the 5-type analytical taxonomy (SIZING, DIAGNOSTIC, EVALUATIVE, EXPLORATORY, STRATEGIC) and the engagement domain.
>
> **Phase 1: Three seed profiles.** Three profiles cover the primary Keystone engagement types in Phase 1. They serve as operational defaults while calibration data accumulates. Weight allocations are provisional and will be recalibrated against actual Keystone deliverables (§5.4).
>
> | Dimension | General Consulting (default) | M&A / Due Diligence | Market Sizing / Estimative |
> |-----------|-----------------------------|--------------------|--------------------------|
> | Analytical Depth | 12% | 15% | 10% |
> | Source Quality | 10% | 14% | 12% |
> | Quantitative Rigor | 15% | 22% | 20% |
> | Actionability | 15% | 14% | 10% |
> | Evaluative Surprise | 5% | 5% | 8% |
> | Calibrated Confidence | 5% | 6% | 8% |
> | *(Tier 1 weight remainder)* | 38% | 24% | 32% |
>
> *Note: Tier 1 dimensions (Intent Alignment, Intellectual Honesty, Completeness, Narrative Coherence) collectively receive the remaining weight within each profile, distributed per the adaptive ranges in §5.3. Exact Tier 1 weights per profile are set during calibration.*
>
> **Phase 2: Expand to 8-10 profiles.** As engagement data accumulates, profiles are added to cover:
> - Operations / Process Optimization
> - Restructuring / Turnaround
> - Growth Strategy / Market Entry
> - Competitive Intelligence (current)
> - Regulatory / Compliance Analysis
> - Technology Assessment
>
> Each new profile is calibrated against a minimum of 5 Jack-scored deliverables before activation. Profiles that diverge from the general consulting profile by fewer than 8 percentage points across all Tier 2 dimensions are merged, not added separately.
>
> **Profile activation logic.** The Specification Engine outputs an `engagement_type` field (5-type analytical taxonomy) and an `engagement_domain` field (consulting domain). Profile selection uses a lookup table at Phase 1. At Phase 2, profiles are matched via embedding similarity against the engagement description, with the closest-matching profile above 0.85 cosine similarity selected. Below threshold, the General Consulting default is used and the engagement is flagged for post-engagement profile calibration review.
>
> **Issue tree classification drives weight generation (Phase 2).** In Phase 2, when a dedicated evaluation profile does not exist for an engagement, the Specification Engine's issue tree branch classification (Bloom's Taxonomy cognitive level + quantitative/qualitative branch nature) generates a custom Tier 2 weight vector. Branches classified as higher-order cognitive (analysis, evaluation, creation) and quantitative nature increase the Quantitative Rigor and Analytical Depth weights. Branches classified as lower-order cognitive (recall, comprehension) and qualitative nature increase Completeness and Source Quality weights. The resulting weight vector is validated against the Tier 2 ranges in §5.3 before use.

---

### Preservations:

The existing two-profile language (Estimative / Current Intelligence) in the document is superseded by the new profile system. The "estimative" profile concept maps to the "Market Sizing / Estimative" profile above. The "current intelligence" concept maps to the forthcoming "Competitive Intelligence (current)" Phase 2 profile.

### Cross-section references:

The Specification Engine (Section 3) needs to output `engagement_type` and `engagement_domain` fields. This is a Section 3 change outside this subagent's scope — flagged for Track A subagent. The issue tree classification → weight generation mechanism (Change #26) is specified below and is co-located with this change.

### Directive compliance:

Directive 1 (rigidity problem — fixed profiles become flexible weight vectors). Directive 5 (build philosophy — Phase 1 infrastructure at correct interface depth, Phase 2 expansion without rework). Directive 13 (Phase 2 deferral — 8-10 profiles; Phase 1 ships 3-4).

---

## Change #26: Issue Tree Branch Classification → Weight Generation Mechanism

**MASTER-SYNTHESIS Reference:** Section 9, Change #26
**Phase Classification:** Phase 2+
**Phase Rationale:** Directive 13 defers this because the Observation Library and the cross-engagement knowledge base (which this mechanism ultimately feeds) do not exist in Phase 1. The mechanism also requires calibration against real issue trees from actual engagements to set the Bloom's level classification thresholds. The Phase 1 deliverable is the profile lookup table (Change #25); the dynamic weight generation via issue tree classification is the Phase 2 sophistication layer.
**Location in CAPSTONE-PLAN-v2.md:** Section 5, within new §5.x (Evaluation Profiles, added by Change #25), as a Phase 2 subsection.

### What exists now:

No mechanism exists for dynamic weight generation from issue tree structure. The existing document has no connection between L0 (Specification Engine / issue tree) and L4 (Evaluator) rubric weights.

### What it should say:

**The "Issue tree classification drives weight generation (Phase 2)" paragraph in new §5.x** (already written in the Change #25 spec above) covers this mechanism. No additional text location is required.

For completeness, the mechanism is:

1. The Specification Engine classifies each issue tree branch on two axes: (a) Bloom's Taxonomy cognitive level — lower order (recall, comprehension, application) vs. higher order (analysis, evaluation, creation); (b) nature — quantitative (numerical estimation, financial modeling, market sizing) vs. qualitative (strategic interpretation, competitive narrative, stakeholder analysis).
2. A weight generation function maps branch distribution to Tier 2 dimension weights. Inputs: fraction of branches classified as higher-order cognitive, fraction classified as quantitative. Outputs: Tier 2 weight adjustments within the ranges defined in §5.3.
3. The generated weight vector is validated against ranges before use. If it falls outside the ranges, it is clamped to the nearest valid weight.
4. The custom weight vector is logged alongside the engagement record for post-engagement calibration and potential promotion to a named profile.

### Preservations:

N/A — this is entirely new content.

### Cross-section references:

Requires the Specification Engine (Section 3) to output Bloom's level and quantitative/qualitative classification per issue tree branch. This is a data flow requirement flagged for Track A.

### Directive compliance:

Directive 2 (issue tree as living document — the tree's structure now drives downstream evaluation configuration). Directive 13 (Phase 2 deferral — build the hook now, activate in Phase 2).

---

## Change #27: Sprint Contract Directionality (Evaluator Proposes, Generator Reviews)

**MASTER-SYNTHESIS Reference:** Section 9, Change #27
**Phase Classification:** Phase 2+
**Phase Rationale:** Directive 13 explicitly defers "Sprint contract negotiation between Evaluator and Generator." The sprint contract concept is already described in the document; this change clarifies directionality. That clarification is correctly deferred because in Phase 1 there is no bidirectional communication channel between the Evaluator and the Generator at contract-creation time — the Generator executes against the RESEARCH.md spec, and the Evaluator grades afterward. The negotiation loop requires the HITL infrastructure and the database state machine as prerequisites.
**Location in CAPSTONE-PLAN-v2.md:** Section 5, around the sprint contract discussion. The existing plan mentions sprint contracts most explicitly in the subsection heading preceding line 520 (the sprint contract framing in the section 4/5 transition). Search for "Sprint Contracts" in the document.

### What exists now:

The document describes sprint contracts in the section preceding §5 (around lines 501-524) as:

> The Evaluator then grades the generated section against these exact criteria.

And the existing language implies the sprint contract is set by the Evaluator unilaterally before generation, with no Generator review step.

### What it should say:

**Add a new subsection §5.x "Sprint Contract Protocol" after the existing sprint contract description:**

> ### 5.x Sprint Contract Protocol `[BATCH 2 UPDATE]`
>
> A sprint contract is the per-section quality specification negotiated before generation begins. It makes evaluation criteria concrete, prevents gaming ("pass the rubric" optimization), and creates shared accountability between the Generator and the Evaluator.
>
> **Directionality (Phase 2).** The Evaluator proposes sprint contract criteria. The Generator reviews and confirms achievability before committing. Both commit before research execution begins.
>
> The flow:
>
> 1. **Evaluator proposes.** Based on the classified issue tree branch (engagement type, Bloom's level, quantitative/qualitative nature), the Evaluator generates a draft sprint contract specifying: required evidence types, minimum source quality thresholds, specific quantitative claims that must be substantiated, and the analysis format (specific chart type, table structure, conclusion framing per §3.x). The proposal is written in concrete, verifiable terms — not abstract quality aspirations.
>
> 2. **Generator reviews.** The Generator (or Specification Engine on its behalf) reviews the proposed criteria against available data sources and agent capabilities. If criteria are infeasible given the available data environment, the Generator flags specific criteria with an infeasibility rationale.
>
> 3. **Negotiation round (one pass).** The Evaluator adjusts infeasible criteria or explicitly accepts infeasibility as a documented constraint. Both sides commit to the final contract.
>
> 4. **Evaluation executes against contract.** The Evaluator grades the final output against the committed criteria, not against generic rubric defaults. Sprint contract compliance is a separate dimension from the ten-dimension rubric — it is a binary gate that runs before rubric scoring.
>
> **Graceful degradation (Phase 1 behavior).** In Phase 1, sprint contract negotiation is not implemented. The Evaluator proposes criteria unilaterally, the Generator executes, and the Evaluator grades against its own proposal. This is functionally equivalent to the existing "Evaluator grades against sprint contracts" language. The Phase 1 implementation already uses the correct interface: the sprint contract is a typed data structure in the handoff contract. The Phase 2 upgrade adds the Generator review step without changing the data structure.
>
> Sprint contracts are designed as optional scaffolding that degrades gracefully as model capability improves. As Opus-class models demonstrate consistent sprint contract compliance without negotiation, the negotiation overhead can be disabled without architectural change.

### Preservations:

All existing sprint contract language in the document is preserved. This is an additive subsection, not a replacement. The existing framing ("The Evaluator then grades the generated section against these exact criteria") remains accurate for Phase 1.

### Cross-section references:

The HITL database state machine (new component, referenced in MASTER-SYNTHESIS Section 1) is a prerequisite for Phase 2 sprint contract negotiation. Section 12 (Infrastructure) changes are outside this subagent's scope — flagged for Track C.

### Directive compliance:

Directive 7 (HITL gates — the human review gate after Specification Engine output is where sprint contracts become visible). Directive 13 (Phase 2 deferral — sprint contract negotiation deferred; graceful degradation principle ensures Phase 1 is valid behavior, not a temporary hack).

---

## Change #28: Dimension-Specific Verification Strategies (Quantitative Rigor, Analytical Depth)

**MASTER-SYNTHESIS Reference:** Section 9, Change #28
**Phase Classification:** Phase 2+
**Phase Rationale:** Directive 13 explicitly defers "Dimension-specific verification strategies (programmatic QR, position-switching AD)." These strategies require: (a) for Quantitative Rigor — a programmatic calculation verification infrastructure beyond FActScore; (b) for Analytical Depth — the position-switching evaluation protocol requiring multiple Evaluator passes. Neither is a Phase 1 prerequisite for shipping a functional evaluator. They address reliability at the margin (47-68% human agreement on these dimensions) and can be added to the evaluation stack without changing existing components.
**Location in CAPSTONE-PLAN-v2.md:** Section 5, subsection 5.9 (Five-Layer Evaluation Stack), around lines 645-659.

### What exists now:

Layer 3 description (line 653):

> **Layer 3: Multi-Rubric Scoring.** Prometheus 2 (EMNLP 2024, 72-85% human agreement, 7B and 8x7B variants) with the ten-dimension rubric. Critical constraint: **never score multiple dimensions in a single prompt.** Each dimension gets a separate evaluation prompt with dimension-specific criteria and calibration examples. This prevents the cross-contamination that SOS-Bench identified — where style scores infect substance scores within a single holistic evaluation. Prometheus 2 runs locally on Mac Mini infrastructure.

There is no mention of dimension-specific verification strategies for Quantitative Rigor or Analytical Depth.

### What it should say:

**Append the following to the Layer 3 paragraph in §5.9:**

> `[BATCH 2 UPDATE]` **Dimension-specific verification for Quantitative Rigor and Analytical Depth (Phase 2).** These are the two dimensions where LLM judges are demonstrably least reliable: 47-68% human agreement on average (Report 07, Batch 2). Phase 2 augments Prometheus 2 scoring on these dimensions with verification strategies that complement the LLM judge:
>
> - **Quantitative Rigor — programmatic complement.** For outputs with numerical claims, Layer 1 (Deterministic Verification) is extended with a calculation audit: extract all arithmetic chains, verify against source data, flag discrepancies exceeding ±5% as potential errors. Statistical claims are checked for appropriate precision given the underlying sample size or data quality. This does not replace the LLM judge for Quantitative Rigor; it provides a second signal that catches the specific failure mode (numerical error masked by confident prose) that LLM judges miss.
>
> - **Analytical Depth — position-switching protocol.** Analytical Depth is evaluated by presenting the same output to Prometheus 2 twice: once with the original argument structure, once with the key conclusion buried and supporting evidence leading. An output with genuine analytical depth produces consistent scores across both presentations (the insight is recognizable regardless of position). An output scoring high on narrative style but low on analytical substance scores inconsistently — the conclusion prominence drives the first score, but the lack of underlying reasoning collapses the second. Position-switching also mitigates the 43.4% positional inconsistency (ChatGPT, CALM 2025) in single-pass evaluation.
>
> Phase 1 behavior: Quantitative Rigor and Analytical Depth are scored by Prometheus 2 without programmatic complement or position-switching. The evaluation is valid; these strategies reduce noise at the margin and do not change the scoring framework.

### Preservations:

All other Layer descriptions (Layers 1, 2, 4, 5) are preserved exactly. The Prometheus 2 setup and calibration requirements are preserved.

### Cross-section references:

Layer 1 (Deterministic Verification) at line 649 references FActScore. The programmatic Quantitative Rigor complement extends Layer 1's scope in Phase 2. The orchestrator should add a note to Layer 1's description: "Phase 2 extension: numerical calculation audit for Quantitative Rigor (see Layer 3 dimension-specific strategies)."

### Directive compliance:

Directive 13 (Phase 2 deferral — dimension-specific verification strategies deferred). Directive 5 (build philosophy — Layer 3 interface unchanged; Phase 2 adds modules without rework). Directive 14 (quality standard — addressing the 47-68% agreement failure mode is essential for Goldman-grade evaluation).

---

## Change #29: Graceful Degradation Principle for Evaluation Scaffolding

**MASTER-SYNTHESIS Reference:** Section 9, Change #29
**Phase Classification:** Phase 1 (the principle must be stated now; it governs all Phase 1 design decisions about the evaluator)
**Phase Rationale:** This is a design principle, not a feature — it is what justifies deferring Changes #27 and #28 without calling Phase 1 an incomplete evaluator. It must be stated in Phase 1 so that every evaluator component is designed from the start to be augmentable rather than requiring rework.
**Location in CAPSTONE-PLAN-v2.md:** Section 5, as a new closing subsection after §5.11 (Cross-Model Evaluation Requirement), around line 682.

### What exists now:

No graceful degradation principle is stated anywhere in Section 5. The document implies completeness — each feature described is assumed to be fully implemented. There is no explicit statement that evaluation scaffolding (sprint contracts, dimension-specific strategies, position-switching) is designed to degrade gracefully as model capability evolves.

### What it should say:

**Add a new subsection §5.12 after §5.11:**

> ### 5.12 Graceful Degradation Principle `[BATCH 2 UPDATE]`
>
> The evaluation scaffolding is designed to be progressively simplified as model capability improves — not because the scaffolding is wrong, but because it is correctly positioned as capability augmentation rather than capability substitution.
>
> **The principle:** Every evaluation mechanism in this section that is not a structural gate (Layers 1-2 are structural gates; they are binary and cannot be degraded) is implemented as an optional module with a defined bypass behavior. When a module is inactive, the system reverts to the next-simpler behavior that is still valid — not to an error state.
>
> Examples of graceful degradation in practice:
>
> - **Sprint contract negotiation** (Phase 2 feature): when inactive, the Evaluator proposes criteria and grades against its own proposal — a valid, consistent evaluation. The data structure is identical; the Generator review step is simply absent.
> - **Position-switching for Analytical Depth** (Phase 2 feature): when inactive, Prometheus 2 scores Analytical Depth in a single pass — the same as standard evaluation. The score is noisier but still meaningful.
> - **Programmatic Quantitative Rigor complement** (Phase 2 feature): when inactive, Prometheus 2 scores Quantitative Rigor without external verification — the same as all other dimensions. The score may miss calculation errors that prose obscures.
> - **8-10 engagement profiles** (Phase 2 expansion): when fewer profiles are active, the system falls back to the General Consulting default — a valid, calibrated weight vector.
>
> **The architectural implication:** Every Phase 2 evaluation enhancement is added by implementing a new module and flipping a configuration flag — not by rewriting the scoring pipeline. The data flow (ten scores → Tier 1 gate check → geometric mean → composite score) is identical in Phase 1 and Phase 2. The modules that improve individual scores are plugged in without changing the aggregation architecture.
>
> This principle is specifically validated by Report 07 (Batch 2): the sprint contract structure is described as "optional scaffold that degrades gracefully as models improve." As Opus 5.0 and subsequent models demonstrate consistent criterion compliance without negotiation, the negotiation overhead can be disabled without any code changes to the scoring pipeline.

### Preservations:

All existing content in §5.11 is preserved. This is a new additive subsection.

### Cross-section references:

The graceful degradation principle applies to the entire Section 5 evaluator design. It is particularly relevant to the Phase 2 features called out in Changes #25, #27, and #28. No other sections require changes.

### Directive compliance:

Directive 5 (build philosophy — "build the architecture correctly but stage feature depth"). Directive 13 (Phase 1 depth staging — the graceful degradation principle is the formal statement of why Phase 1 deferrals are acceptable without technical debt). Directive 6 (FITFO standard — the evaluator degrades gracefully on novel engagement types, not to an error state).

---

---

# Section 6 Changes (Retrieval: §6.2 Unified Retrieval Architecture)

**Scope clarification:** Changes #30-38 target §6.2 "Unified Retrieval Architecture" (lines 701-731) exclusively. Sections §6.1, §6.3, §6.4, and §6.5 are preserved without modification. The structural argument in §6.1 (Scaffold vs. System Distinction, Prendergast hallucination tax analysis) is preserved verbatim — it motivates the retrieval architecture but is not affected by the technical changes within it.

**Nature of §6.2 changes:** The changes collectively require a near-complete rewrite of §6.2. Rather than specifying 9 separate replacement targets in a single densely interleaved table, the approach is: (a) specify each change individually with exact "What exists now" and "What it should say" per change, and (b) provide a complete replacement draft of §6.2 as the final change entry (#38), which supersedes the individual component-level drafts. The orchestrator should use the complete §6.2 replacement from Change #38 as the authoritative version and treat Changes #30-37 as the rationale and constraint specifications for each edit decision.

---

## Change #30: Split Component #3 into #3a (Source Discovery) + #3b (Knowledge Accumulation)

**MASTER-SYNTHESIS Reference:** Section 9, Change #30
**Phase Classification:** Phase 1 (the split itself — both subsystems are scaffolded in Phase 1; #3b at reduced depth)
**Phase Rationale:** Directive 13 explicitly lists "Component #3 split (#3a discovery + #3b accumulation)" as Phase 1. The split is architectural, not a feature — it determines data flow and interface contracts. #3a (source discovery) ships at full depth in Phase 1. #3b (knowledge accumulation) ships at reduced depth in Phase 1 (filesystem wiki structure with manual promotion), with cross-engagement promotion rules deferred to Phase 2 per Directive 13.
**Location in CAPSTONE-PLAN-v2.md:** Section 6, subsection 6.2, lines 701-731. The entire subsection.

### What exists now:

§6.2 (lines 701-731) describes a single integrated retrieval system with no distinction between source discovery and knowledge accumulation. The components are:
- pgvector + pgvectorscale (vector store)
- Hybrid search (dense + BM25 + RRF)
- Semantic Router (query routing)
- Search API stack: Exa, Brave, Firecrawl, Tavily
- Docling (document processing)
- Bifrost dual-layer caching
- Source quality scoring (Admiralty Code)
- Three source categories: public, internal, historical

### What it should say:

**The split creates two architecturally distinct subsystems within §6.2.** The full replacement is specified in Change #38. For the split structure itself, the new §6.2 organizes as:

> **Component #3a: Source Discovery.** The retrieval infrastructure for finding and retrieving sources not yet in the engagement knowledge base. Handles: external web search, SEC filings, internal document store, embedding-based semantic similarity search against unprocessed content. This is the RAG subsystem.
>
> **Component #3b: Knowledge Accumulation.** The infrastructure for navigating and querying knowledge already processed and compiled during this or prior engagements. Handles: the compiled markdown wiki (Karpathy three-layer pattern), the Observation Library, and cross-engagement knowledge. This is the filesystem navigation subsystem.

The distinction is fundamental: RAG for discovery (finding sources not yet ingested), filesystem navigation for accumulated knowledge (Karpathy pattern). King's College London (February 2026) confirms structure-driven retrieval outperforms similarity-driven for agent memory.

### Preservations:

The three source categories at the end of §6.2 (public, internal, historical — lines 726-731) are preserved in #3a, reframed as the three retrieval targets for the source discovery subsystem.

### Cross-section references:

The build sequence in MASTER-SYNTHESIS Section 10 shows #3a and #3b as parallel build items. Component #3b timing note: "can be deferred until after #5 ships, since it primarily serves cross-engagement knowledge (not needed for first engagement)." This note should appear in the #3b subsection.

### Directive compliance:

Directive 8 (Karpathy KB pattern — the split is the exact architectural implication described: "Component #3 (retrieval) may be simpler than planned if compiled wikis handle accumulated knowledge and embeddings are only needed for initial source discovery"). Directive 9 (Component #3 over-engineering concern resolved). Directive 13 (Phase 1 ship list).

---

## Change #31: Add Voyage-Finance-2 as Primary Embedding Model

**MASTER-SYNTHESIS Reference:** Section 9, Change #31
**Phase Classification:** Phase 1
**Phase Rationale:** The embedding model selection is a foundational #3a build decision. Voyage-finance-2 has a 49% improvement over OpenAI on ConvFinQA (FinMTEB, EMNLP 2025) and is independently validated by TigerData. This is a specific technical decision, not a sophistication layer — it cannot be added later by "extending an interface." The embedding model is baked into the vector index; changing it requires re-indexing all documents.
**Location in CAPSTONE-PLAN-v2.md:** Section 6, subsection 6.2, the Vector Store paragraph (line 705).

### What exists now:

Line 705:

> **Vector Store: pgvector + pgvectorscale.** PostgreSQL with pgvector extension as the primary vector store. Timescale benchmarks demonstrate 28x lower query latency than Pinecone at 75% less cost, with the advantage of SQL join capability for combining vector similarity with structured metadata queries. pgvectorscale adds streaming disk ANN for datasets exceeding RAM.

No embedding model is specified. The text implies the default embedding model of whatever service is used.

### What it should say:

> **Vector Store: pgvector + pgvectorscale, with Voyage-finance-2 embeddings.** `[BATCH 2 UPDATE]` PostgreSQL with pgvector extension as the primary vector store. Timescale benchmarks demonstrate 28x lower query latency than Pinecone at 75% less cost, with the advantage of SQL join capability for combining vector similarity with structured metadata queries. pgvectorscale adds streaming disk ANN for datasets exceeding RAM.
>
> **Embedding model: Voyage-finance-2** ($0.12/MTok). FinMTEB benchmark (EMNLP 2025) demonstrates 49% improvement over OpenAI text-embedding-3-large on ConvFinQA financial question answering; independently validated by TigerData on real-world financial corpora. Domain-specialized embedding models outperform general models on financial documents by material margins — the Keystone corpus (SEC filings, financial analyses, industry reports) falls squarely in the domain Voyage-finance-2 was optimized for. At $0.12/MTok, cost is negligible for engagement-scale corpora (a 1,000-document engagement corpus at 1,000 tokens per document = 1M tokens = $0.12 total embedding cost).

### Preservations:

The pgvector + pgvectorscale selection is preserved. The Timescale benchmark citation is preserved. All other §6.2 content is unchanged by this specific edit.

### Cross-section references:

None. The embedding model selection is internal to Component #3a.

### Directive compliance:

Directive 9 (Component #3 over-engineering resolved — specific model selected). Directive 14 (Goldman-grade quality — domain-specialized embeddings are demonstrably superior for financial corpora). Directive 13 (Phase 1 ship — foundational build decision).

---

## Change #32: Add Contextual Retrieval at Ingest Time

**MASTER-SYNTHESIS Reference:** Section 9, Change #32
**Phase Classification:** Phase 1
**Phase Rationale:** Contextual retrieval at ingest time is a 67% failure-reduction technique (combined with reranking) that requires zero additional cost on Claude Max. It is applied at document ingestion, not at query time — it affects the embedding quality of every chunk from the start. Adding it after the index is built would require re-ingestion of all documents. It cannot be deferred without accepting degraded retrieval quality from Day 1.
**Location in CAPSTONE-PLAN-v2.md:** Section 6, subsection 6.2, Document Processing paragraph (line 720) and/or after the Vector Store paragraph (line 705).

### What exists now:

Line 720:

> **Document Processing: Docling for structure-aware parsing.** Enterprise RAG Challenge validated: structure-aware PDF parsing achieves 87.7% accuracy vs. poor results from fixed-size chunking. Table structure, section headers, and figure captions preserved as metadata. This is critical for financial documents where table structure carries meaning.

There is no mention of contextual retrieval (prepending a Haiku-generated context window to each chunk before embedding).

### What it should say:

**Replace the Document Processing paragraph with:**

> **Document Processing: Docling for structure-aware parsing + contextual retrieval at ingest.** `[BATCH 2 UPDATE]` Enterprise RAG Challenge validated: structure-aware PDF parsing achieves 87.7% accuracy vs. poor results from fixed-size chunking. Table structure, section headers, and figure captions preserved as metadata. This is critical for financial documents where table structure carries meaning.
>
> At ingest time, before embedding, each chunk receives a Haiku-generated contextual preamble: a 2-4 sentence description of (a) the document's overall topic and provenance, (b) where this chunk appears within the document's structure, and (c) the key entities referenced in this chunk. The preamble is prepended to the chunk before generating the Voyage-finance-2 embedding. Combined with reranking (see Cohere Rerank below), contextual retrieval at ingest achieves 67% reduction in retrieval failures (Anthropic, 2025). On Claude Max, Haiku preamble generation has zero marginal API cost — this is a pure quality improvement.
>
> **Chunking rules** `[BATCH 2 UPDATE]`: 512 tokens per chunk, 50-100 token overlap between adjacent chunks. Tables are preserved as HTML strings within the chunk rather than being extracted as plain text — table structure carries meaning in financial documents and is lost in plain-text extraction. XBRL-tagged financial data bypasses chunk splitting entirely: XBRL tags are processed as structured data objects (key-value pairs) rather than embedded in text chunks, preserving the numerical precision and taxonomy linkage that text chunking would destroy.

### Preservations:

The Docling selection is preserved. The Enterprise RAG Challenge validation is preserved. The "table structure carries meaning" rationale is extended, not replaced.

### Cross-section references:

The chunking rules (Change #34) are co-located in this paragraph. No separate cross-section changes required.

### Directive compliance:

Directive 5 (build philosophy — contextual retrieval is a foundational ingest-time decision, not a Phase 2 sophistication). Directive 14 (Goldman-grade quality — 67% failure reduction is a material improvement, not a marginal one).

---

## Change #33: Add Cohere Rerank v3.5 to Retrieval Pipeline

**MASTER-SYNTHESIS Reference:** Section 9, Change #33
**Phase Classification:** Phase 1
**Phase Rationale:** Reranking is the second half of the contextual retrieval quality improvement (the first being Haiku preamble generation at ingest). Both changes work together to achieve the 67% failure reduction. Cohere Rerank v3.5 is a specific, production-deployed service with clear pipeline position (top 150 candidates → rerank → top 20). It cannot be deferred because the pipeline's precision depends on it from the first engagement.
**Location in CAPSTONE-PLAN-v2.md:** Section 6, subsection 6.2, after the Hybrid Search paragraph (line 707).

### What exists now:

Line 707:

> **Hybrid Search (non-negotiable for financial documents).** Dense vector similarity + BM25 keyword search + Reciprocal Rank Fusion. BEIR aggregate benchmarks show hybrid search improves NDCG by 26-31% over dense-only retrieval. Financial documents with precise numerical values and regulatory terminology require exact keyword matching that pure semantic search misses.

There is no reranking step after hybrid search.

### What it should say:

**After the Hybrid Search paragraph, insert:**

> **Reranking: Cohere Rerank v3.5.** `[BATCH 2 UPDATE]` Hybrid search returns a candidate set (top 150 results by RRF score). Before these results are passed to the research agent, Cohere Rerank v3.5 re-scores the full top-150 candidate set and returns the top 20. Reranking addresses the fundamental limitation of first-stage retrieval: BM25 + dense vector similarity scores are noisy proxies for relevance; they are optimized for recall, not precision. Cohere Rerank uses a cross-encoder architecture that scores each candidate against the full query, producing substantially more precise relevance ranking than the bi-encoder approach used for first-stage retrieval.
>
> Pipeline position: Query → Hybrid Search (dense + BM25 + RRF) → top 150 candidates → Cohere Rerank v3.5 → top 20 results delivered to agent. The 150→20 compression ratio is calibrated for financial research tasks: 20 results is sufficient context for a research agent operating within a 100K token subagent window, while 150 first-stage candidates provides enough coverage to capture rare but highly relevant sources that lower similarity scores might otherwise discard.

### Preservations:

The Hybrid Search paragraph is preserved intact. The BEIR benchmark citation is preserved. The reranking paragraph is additive.

### Cross-section references:

None. Reranking is internal to the #3a pipeline.

### Directive compliance:

Directive 9 (Component #3 resolution — specific reranking solution selected). Directive 14 (Goldman-grade quality). Directive 13 (Phase 1 ship).

---

## Change #34: Add Chunking Rules (512 tokens, 50-100 overlap, tables as HTML, XBRL bypass)

**MASTER-SYNTHESIS Reference:** Section 9, Change #34
**Phase Classification:** Phase 1
**Phase Rationale:** Chunking rules are part of the ingest pipeline specification. They must be defined before any documents are ingested — retroactively changing chunk size or overlap requires complete re-ingestion and re-embedding. The XBRL bypass rule is particularly important for financial documents: XBRL tags lose all analytical value when chunked as text.
**Location in CAPSTONE-PLAN-v2.md:** Section 6, subsection 6.2, Document Processing paragraph (line 720). Co-located with Change #32.

### What exists now:

No chunking rules are specified anywhere in §6.2. The document mentions Docling for parsing but does not specify how parsed content is chunked for embedding.

### What it should say:

The chunking rules are incorporated into the revised Document Processing paragraph under Change #32. Specifically:

> **Chunking rules** `[BATCH 2 UPDATE]`: 512 tokens per chunk, 50-100 token overlap between adjacent chunks. Tables are preserved as HTML strings within the chunk rather than being extracted as plain text — table structure carries meaning in financial documents and is lost in plain-text extraction. XBRL-tagged financial data bypasses chunk splitting entirely: XBRL tags are processed as structured data objects (key-value pairs) rather than embedded in text chunks, preserving the numerical precision and taxonomy linkage that text chunking would destroy.

This text is already included in the Change #32 paragraph draft above. No additional text location is required.

### Preservations:

N/A — new content co-located with Change #32.

### Cross-section references:

None.

### Directive compliance:

Directive 14 (Goldman-grade quality — precise chunking is foundational to retrieval quality for financial documents). Directive 13 (Phase 1 ship — foundational ingest-time decision).

---

## Change #35: Remove Semantic Router

**MASTER-SYNTHESIS Reference:** Section 9, Change #35
**Phase Classification:** Phase 1 (removal)
**Phase Rationale:** Semantic Router is being removed (not deferred). The MASTER-SYNTHESIS (Section 1, Component #3 description) explicitly states: "Semantic Router and Bifrost caching are removed." Report 04 (Batch 2) identified Semantic Router as over-engineered for the actual routing requirement — query classification for the three-path (quantitative, qualitative, hybrid) routing decision does not require a specialized routing library and adds a dependency without proportionate value.
**Location in CAPSTONE-PLAN-v2.md:** Section 6, subsection 6.2, lines 709-713 (Query Routing section).

### What exists now:

Lines 709-713:

> **Query Routing: Semantic Router (<5ms classification).** Incoming queries are classified and routed to the appropriate retrieval path before search execution:
> - **Quantitative queries** → Text2SQL path against structured databases (financial metrics, market data, regulatory filings)
> - **Qualitative queries** → Vector search path against unstructured corpus (analyses, reports, commentary)
> - **Hybrid queries** → Both paths, results merged via RRF

### What it should say:

**Replace the entire Query Routing paragraph with:**

> **Query Classification (inline, no external router).** `[BATCH 2 UPDATE]` Incoming queries are classified as quantitative (numerical estimation, financial metrics, regulatory data), qualitative (strategic analysis, narrative research, commentary), or hybrid (requires both). This three-way classification is implemented as a short prompt to Haiku (1-2 sentences, < 200ms), not as a specialized routing library. Semantic Router is not used: the classification task is simple enough that a direct Haiku call is faster, cheaper, and more maintainable than a dedicated routing service.
>
> Routing by classification:
> - **Quantitative queries** → Text2SQL path against structured databases (financial metrics, market data, regulatory filings via XBRL-structured data objects)
> - **Qualitative queries** → #3a vector search path (Voyage-finance-2 + Cohere Rerank, hybrid BM25 + dense)
> - **Hybrid queries** → both paths, results merged via RRF before reranking

### Preservations:

The three routing paths (quantitative, qualitative, hybrid) are preserved. The Text2SQL path rationale is preserved. Only the routing mechanism changes from Semantic Router library to inline Haiku classification.

### Cross-section references:

None. This is internal to #3a.

### Directive compliance:

Directive 5 (build philosophy — simpler implementation that achieves the same architectural function). Directive 9 (Component #3 over-engineering concern — Semantic Router was one of the over-engineered components identified).

---

## Change #36: Remove Bifrost Caching

**MASTER-SYNTHESIS Reference:** Section 9, Change #36
**Phase Classification:** Phase 1 (removal)
**Phase Rationale:** Bifrost is removed (not deferred). Report 04 (Batch 2) identified Bifrost as an over-engineered caching layer for the current scale — a Claude Max single-user deployment with 3-5 concurrent agents does not need a dual-layer Redis + disk caching architecture. Simple in-memory caching (Python dict or lru_cache) within a single engagement session is sufficient for Phase 1. The Bifrost dependency adds complexity without proportionate value at current scale.
**Location in CAPSTONE-PLAN-v2.md:** Section 6, subsection 6.2, lines 722-724 (Caching section).

### What exists now:

Lines 722-724:

> **Caching: Bifrost dual-layer architecture.** Hot layer (Redis/in-memory) for repeat queries within an engagement. Cold layer (disk-backed) with per-source TTLs: SEC filings (30 days), news (24 hours), market data (1 hour). Eliminates redundant API calls across agents working the same engagement.

### What it should say:

**Replace the Caching paragraph with:**

> **Caching: in-process session cache.** `[BATCH 2 UPDATE]` Repeat queries within a single engagement session are cached in-process (Python `lru_cache` or equivalent). Per-source TTL rules are enforced at cache population time: SEC filings (30 days), news (24 hours), market data (1 hour). This eliminates redundant API calls across agents working the same engagement without the operational overhead of a Redis cluster.
>
> Bifrost dual-layer caching is not used. At Phase 1 scale (single-user Claude Max, 3-5 concurrent agents per engagement), in-process caching achieves the same within-engagement deduplication. If cross-engagement caching or multi-user concurrency becomes a requirement, the cache interface is designed for drop-in replacement with Redis without changes to the retrieval pipeline.

### Preservations:

The TTL rules (30 days / 24 hours / 1 hour by source type) are preserved. The within-engagement deduplication goal is preserved.

### Cross-section references:

None.

### Directive compliance:

Directive 5 (build philosophy — correct interface, reduced implementation depth). Directive 9 (Component #3 over-engineering concern resolved).

---

## Change #37: Add Brave Search + Exa as External Discovery APIs (Remove Tavily Dependency, Skip Google CSE)

**MASTER-SYNTHESIS Reference:** Section 9, Change #37
**Phase Classification:** Phase 1
**Phase Rationale:** The Search API stack directly affects what sources the research agents can find. Tavily's acquisition by Nebius (February 2026) creates pricing uncertainty that MASTER-SYNTHESIS Risk Register flags as MEDIUM. Exa + Firecrawl already cover the same function. Google CSE sunsetting in January 2027 makes it an architectural liability. This is a foundational dependency decision that cannot be deferred — building against Tavily as a dependency creates supplier risk from Day 1.
**Location in CAPSTONE-PLAN-v2.md:** Section 6, subsection 6.2, lines 714-719 (Search API Stack section).

### What exists now:

Lines 714-719:

> **Search API Stack (per-agent tool assignment):**
> - **Exa**: Primary semantic/category search — SEC filings, company research, academic papers by type. Neural index with category-based search (no substitute for this capability)
> - **Brave Search**: Primary news and general web coverage. Only independent Western web index after Bing API shutdown (August 2025)
> - **Firecrawl**: Full-page extraction and autonomous browsing for content behind JavaScript rendering or requiring multi-page navigation
> - **Tavily**: RAG-optimized structured JSON output — reduces LLM post-processing for extraction tasks

### What it should say:

**Replace the Search API Stack paragraph with:**

> **Search API Stack (per-agent tool assignment):** `[BATCH 2 UPDATE]`
> - **Exa**: Primary semantic/category search — SEC filings, company research, academic papers by type. Neural index with category-based search (no substitute for this capability). Also covers structured JSON output for RAG-optimized extraction (replacing Tavily's prior role in this pipeline).
> - **Brave Search**: Primary news and general web coverage. Only independent Western web index after Bing API shutdown (August 2025). Not dependent on Google infrastructure, which is sunsetting Custom Search Engine in January 2027.
> - **Firecrawl**: Full-page extraction and autonomous browsing for content behind JavaScript rendering or requiring multi-page navigation.
>
> **Removed: Tavily.** Tavily was acquired by Nebius (February 2026); pricing and API stability are uncertain. Its primary function (RAG-optimized structured JSON output) is covered by Exa's native structured output mode. Tavily is not architecturally required and is removed to eliminate the supplier dependency risk.
>
> **Not used: Google Custom Search Engine.** Google CSE sunsetting January 2027 makes it unsuitable as a long-term dependency. Brave Search covers the same general web index function with a stable independent infrastructure.

### Preservations:

Exa, Brave, and Firecrawl are all preserved from the existing list. Only Tavily is removed. The rationale for Exa (neural index, category-based search) and Brave (independent Western web index, post-Bing-shutdown) are preserved verbatim.

### Cross-section references:

None.

### Directive compliance:

Directive 14 (Goldman-grade quality — eliminating supplier dependency risk). Directive 5 (build philosophy — stable dependency foundation). Risk Register: Tavily acquisition flagged as MEDIUM risk; this change mitigates it.

---

## Change #38: Add Compiled Wiki per Engagement (Karpathy Three-Layer Pattern) + Full §6.2 Replacement

**MASTER-SYNTHESIS Reference:** Section 9, Change #38
**Phase Classification:** #3b Phase 1 at reduced depth; cross-engagement promotion rules Phase 2+
**Phase Rationale:** Directive 13 lists "Component #3 split (#3a discovery + #3b accumulation)" as Phase 1. Component #3b ships in Phase 1 as a per-engagement compiled wiki (filesystem, three-layer structure). Cross-engagement knowledge base and wiki promotion rules are deferred to Phase 2 per Directive 13 ("Cross-engagement knowledge base / wiki promotion rules").
**Location in CAPSTONE-PLAN-v2.md:** Section 6, subsection 6.2, lines 701-731. Full replacement.

### What exists now:

The full existing §6.2 text (lines 701-731). See Change #30 for the complete current text.

### What it should say:

**Replace §6.2 entirely with the following:**

---

> ### 6.2 Unified Retrieval Architecture `[SYNTHESIS UPDATE]` `[BATCH 2 UPDATE]`
>
> The retrieval layer splits into two structurally distinct subsystems. **Component #3a (Source Discovery)** finds and retrieves sources not yet in the engagement knowledge base — this is the RAG subsystem. **Component #3b (Knowledge Accumulation)** navigates and queries knowledge already compiled during this or prior engagements — this is the filesystem wiki subsystem. The distinction is foundational: RAG for discovery (finding sources not yet ingested), filesystem navigation for accumulated knowledge. King's College London (February 2026) confirms structure-driven retrieval outperforms similarity-driven for agent memory.
>
> Each research agent receives only its relevant tools (3-5 per agent), not the unified interface. Tool specialization improves agent performance (Anthropic production finding, Report 09).
>
> #### Component #3a: Source Discovery
>
> **Vector Store: pgvector + pgvectorscale, with Voyage-finance-2 embeddings.** PostgreSQL with pgvector extension as the primary vector store. Timescale benchmarks demonstrate 28x lower query latency than Pinecone at 75% less cost, with the advantage of SQL join capability for combining vector similarity with structured metadata queries. pgvectorscale adds streaming disk ANN for datasets exceeding RAM.
>
> **Embedding model: Voyage-finance-2** ($0.12/MTok). FinMTEB benchmark (EMNLP 2025) demonstrates 49% improvement over OpenAI text-embedding-3-large on ConvFinQA financial question answering; independently validated by TigerData on real-world financial corpora. Domain-specialized embedding models outperform general models on financial documents by material margins — the Keystone corpus (SEC filings, financial analyses, industry reports) falls squarely in the domain Voyage-finance-2 was optimized for.
>
> **Hybrid Search (non-negotiable for financial documents).** Dense vector similarity + BM25 keyword search + Reciprocal Rank Fusion. BEIR aggregate benchmarks show hybrid search improves NDCG by 26-31% over dense-only retrieval. Financial documents with precise numerical values and regulatory terminology require exact keyword matching that pure semantic search misses.
>
> **Reranking: Cohere Rerank v3.5.** Hybrid search returns a candidate set (top 150 results by RRF score). Before these results are passed to the research agent, Cohere Rerank v3.5 re-scores the full top-150 candidate set and returns the top 20. Reranking uses a cross-encoder architecture that scores each candidate against the full query, producing substantially more precise relevance ranking than the bi-encoder approach used for first-stage retrieval. Pipeline position: Query → Hybrid Search (dense + BM25 + RRF) → top 150 candidates → Cohere Rerank v3.5 → top 20 results delivered to agent.
>
> **Query Classification (inline, no external router).** Incoming queries are classified as quantitative (numerical estimation, financial metrics, regulatory data), qualitative (strategic analysis, narrative research, commentary), or hybrid (requires both). This three-way classification is implemented as a short prompt to Haiku (1-2 sentences, < 200ms). Semantic Router is not used: the classification task is simple enough that a direct Haiku call is faster, cheaper, and more maintainable than a dedicated routing service.
>
> Routing by classification:
> - **Quantitative queries** → Text2SQL path against structured databases (financial metrics, market data, regulatory filings via XBRL-structured data objects)
> - **Qualitative queries** → Vector search path (Voyage-finance-2 + Cohere Rerank, hybrid BM25 + dense)
> - **Hybrid queries** → both paths, results merged via RRF before reranking
>
> **Search API Stack (per-agent tool assignment):**
> - **Exa**: Primary semantic/category search — SEC filings, company research, academic papers by type. Neural index with category-based search (no substitute for this capability). Also covers structured JSON output for RAG-optimized extraction.
> - **Brave Search**: Primary news and general web coverage. Only independent Western web index after Bing API shutdown (August 2025). Not dependent on Google infrastructure, which is sunsetting Custom Search Engine in January 2027.
> - **Firecrawl**: Full-page extraction and autonomous browsing for content behind JavaScript rendering or requiring multi-page navigation.
>
> Tavily is not used (acquired by Nebius February 2026; pricing uncertain; function covered by Exa). Google CSE is not used (sunsetting January 2027).
>
> **Document Processing: Docling for structure-aware parsing + contextual retrieval at ingest.** Enterprise RAG Challenge validated: structure-aware PDF parsing achieves 87.7% accuracy vs. poor results from fixed-size chunking. Table structure, section headers, and figure captions preserved as metadata. This is critical for financial documents where table structure carries meaning.
>
> At ingest time, before embedding, each chunk receives a Haiku-generated contextual preamble: a 2-4 sentence description of (a) the document's overall topic and provenance, (b) where this chunk appears within the document's structure, and (c) the key entities referenced in this chunk. The preamble is prepended to the chunk before generating the Voyage-finance-2 embedding. Combined with Cohere Rerank, contextual retrieval at ingest achieves 67% reduction in retrieval failures (Anthropic, 2025). On Claude Max, Haiku preamble generation has zero marginal API cost.
>
> **Chunking rules:** 512 tokens per chunk, 50-100 token overlap between adjacent chunks. Tables are preserved as HTML strings within the chunk rather than being extracted as plain text. XBRL-tagged financial data bypasses chunk splitting entirely: XBRL tags are processed as structured data objects (key-value pairs) rather than embedded in text chunks, preserving numerical precision and taxonomy linkage.
>
> **Caching: in-process session cache.** Repeat queries within a single engagement session are cached in-process (Python `lru_cache` or equivalent). Per-source TTL rules: SEC filings (30 days), news (24 hours), market data (1 hour). Eliminates redundant API calls across agents working the same engagement. Bifrost dual-layer caching is not used — at Phase 1 scale (single-user Claude Max, 3-5 concurrent agents), in-process caching is sufficient. The cache interface supports drop-in Redis replacement for multi-user scale without pipeline changes.
>
> **Source Quality Scoring.** Each retrieved source receives a composite quality score based on the Admiralty Code (source reliability x information credibility): `quality = w1*authority + w2*recency + w3*corroboration + w4*specificity`. Sources below threshold are flagged in the citation manifest for Evaluator review.
>
> One query fans out across three source categories:
> 1. **Public sources**: Web search APIs (Exa, Brave), SEC filings (EdgarTools MCP), industry reports, news, academic papers (Semantic Scholar + OpenAlex via paper-search-mcp)
> 2. **Internal sources**: Keystone's document store — past deliverables, methodology guides, partner preferences (pgvector)
> 3. **Historical sources**: Findings from prior research projects completed by this system (trajectory storage, pgvector)
>
> Results return merged, ranked by the source quality score, and annotated with source provenance. The research agent sees a coherent result set tailored to its task assignment.
>
> #### Component #3b: Knowledge Accumulation
>
> Component #3b manages knowledge already processed and compiled during the current engagement or prior engagements. It does not use embedding-based similarity search — instead, it uses the Karpathy three-layer pattern for structured filesystem navigation. This follows the principle established by Reports 04, 06, and 10 (Batch 2), and validated by the file-based memory finding (74% performance, outperforming Mem0 at 68.5%).
>
> **Three-layer structure per engagement:**
>
> ```
> {engagement_id}/
>   memory/
>     raw/           ← Full subagent artifacts (verbatim research outputs)
>     compiled/      ← Orchestrator-synthesized findings (round summaries, claim sets)
>     INDEX.md       ← Auto-maintained index of all compiled findings, updated after each round
> ```
>
> `raw/`: Every subagent writes its full artifact here after completing its task. Files are immutable after write. Naming convention: `{round}_{agent_id}_{task_id}.md`. These are the canonical source records for all findings.
>
> `compiled/`: The Opus orchestrator synthesizes `raw/` outputs into structured finding summaries after each research round. Files follow a consistent schema: summary header (key findings, open gaps, confidence levels), claim set (per-claim: text, confidence, source artifact paths, content-hash), and round metadata. Subagents in round N+1 receive selected excerpts from `compiled/` via JIT context loading — they read compiled findings, not raw artifacts, to stay within the 100K token subagent window.
>
> `INDEX.md`: Automatically maintained by the orchestrator after each round. Lists all compiled finding files with one-line summaries, organized by issue tree branch. The INDEX.md is the entry point for any agent or human trying to understand what the engagement has found. It is updated atomically after each round completes.
>
> **Citation provenance.** Each claim in `compiled/` carries a content-hash (`sha256(claim_text + source_url + access_timestamp)`) linking it to the specific `raw/` artifact from which it was derived. This enables the CitationProcessor to trace every compiled finding back to its original source, preventing provenance loss during multi-round synthesis.
>
> **Human-designed schemas.** The compiled finding schema is designed by humans, not auto-generated by LLM. ETH Zurich (2026) research confirms: human-written schemas improve retrieval accuracy by +4% while LLM-generated schemas degrade it by -2%. The orchestrator fills schema fields; it does not design them.
>
> **Cross-engagement knowledge base (Phase 2).** In Phase 2, compiled findings from completed engagements are promoted to a cross-engagement knowledge base — a shared wiki organized by industry, engagement type, and analytical pattern. Promotion rules (what findings qualify, what schema is used, how conflicts are resolved) are defined in Phase 2. Scoping constraints (engagement-scoped `raw/` and `compiled/` data never leaks cross-client; only anonymized patterns are promoted) are enforced by the promotion pipeline, not by agent instructions.
>
> *Build timing note:* Component #3b can be deferred until after Component #5 (Specification Engine) ships, since it primarily serves cross-round and cross-engagement continuity. Component #3a is the Phase 1 priority. However, the `raw/` write path must be wired into every subagent from the first engagement — retrofitting artifact writes is disruptive.

---

### Preservations:

The following existing §6.2 content is preserved verbatim in the replacement:
- The opening sentence about Internal Document Agent and orchestrator routing
- The pgvector + pgvectorscale selection and Timescale benchmark citation
- The Hybrid Search paragraph and BEIR benchmark citation
- The three source categories (public, internal, historical) at the end of #3a
- The source quality scoring paragraph (Admiralty Code formula and logic)
- The Docling selection and Enterprise RAG Challenge citation
- The per-source TTL rules (30 days / 24 hours / 1 hour)

The Prendergast hallucination tax analysis in §6.1 is entirely preserved — it is motivating context for the retrieval architecture and is not modified by any of these changes.

### Cross-section references:

The INDEX.md and compiled/ structure in Component #3b directly corresponds to the orchestrator Memory scratchpad (`research-state.md`) described in MASTER-SYNTHESIS Section 1. These are related but distinct: `research-state.md` is the orchestrator's working scratchpad (intent, current gaps, stopping status); `compiled/` is the persistent finding record. The relationship should be clarified in Section 4 (Research & Analysis) — flagged for Track A subagent.

The #3b Phase 2 cross-engagement knowledge base is a prerequisite for the Observation Library CBR query described in the Specification Engine (Section 3). This is noted in the Phase 2 description above. No Section 3 edits required here.

### Directive compliance:

Directive 8 (Karpathy KB pattern — #3b is the direct implementation: "compiled markdown wikis organized by industry/engagement-type/pattern, with LLM-maintained indexes"). Directive 9 (Component #3 over-engineering concern — resolved with split, specific model selections, removals). Directive 13 (Phase 1: split ships; cross-engagement promotion deferred to Phase 2). Directive 14 (Goldman-grade quality — 67% retrieval failure reduction, domain-specialized embeddings, structure-aware parsing).

---

## Appendix: Section 5 Subsection Numbering After Changes

The following new subsections are added to Section 5 and must be integrated into the section numbering:

| Existing | New Content | New Position |
|----------|-------------|--------------|
| §5.3 (rubric table) | Extended with tier split | §5.3 (expanded) |
| (new) | Evaluation Profiles | §5.x — insert after §5.3, before §5.4 |
| §5.4 Calibration | Unchanged | §5.4 (renumbered if needed) |
| ... | ... | ... |
| §5.11 Cross-Model | Unchanged | §5.11 |
| (new) | Graceful Degradation Principle | §5.12 |

The orchestrator should renumber subsections after insertion. The exact numbering (e.g., whether the new Evaluation Profiles section becomes §5.3a or §5.4 with existing §5.4 pushed to §5.5) is left to the orchestrator's discretion based on the full section state after all Track A, B, and C changes are merged.

## Appendix: §6.2 Component Map — What Was Removed vs. Added vs. Preserved

| Item | Status | Justification |
|------|--------|---------------|
| pgvector + pgvectorscale | PRESERVED | Validated in Batch 2 research |
| Hybrid search (BM25 + dense + RRF) | PRESERVED | BEIR NDCG +26-31% |
| Semantic Router | REMOVED | Over-engineered; replaced by Haiku inline classification |
| Bifrost caching | REMOVED | Over-engineered for Phase 1 scale |
| Tavily | REMOVED | Supplier risk (Nebius acquisition); function covered by Exa |
| Google CSE | NOT USED (clarified) | Sunsetting January 2027 |
| Exa | PRESERVED | Neural index, no substitute |
| Brave Search | PRESERVED | Only independent Western web index |
| Firecrawl | PRESERVED | JavaScript rendering, multi-page navigation |
| Docling | PRESERVED | Enterprise RAG Challenge validated |
| Admiralty Code source scoring | PRESERVED | Quality scoring formula unchanged |
| Voyage-finance-2 | ADDED | 49% improvement on ConvFinQA |
| Contextual retrieval at ingest | ADDED | 67% failure reduction (with reranking) |
| Cohere Rerank v3.5 | ADDED | Cross-encoder precision, top 150 → top 20 |
| Chunking rules (512t, 50-100 overlap) | ADDED | Foundational ingest spec |
| Tables as HTML, XBRL bypass | ADDED | Financial document structure preservation |
| In-process session cache | ADDED (simplified) | Replaces Bifrost |
| Component #3b wiki structure | ADDED | Karpathy three-layer pattern |
| Content-hash provenance | ADDED | Citation traceability in compiled/ |
| Cross-engagement wiki (Phase 2) | DEFERRED | Directive 13 |

---

*End of Change Specification B*
*Orchestrator: merge with Track A (Changes #1-22) and Track C (Changes #39-48) before editing CAPSTONE-PLAN-v2.md.*
