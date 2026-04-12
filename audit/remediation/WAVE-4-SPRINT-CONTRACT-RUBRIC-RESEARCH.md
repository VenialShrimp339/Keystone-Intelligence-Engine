# Wave 4 Sprint Contract / Rubric Research

*Date: 2026-04-12 | Scope: C-5, C-7 | Purpose: freeze the sprint-contract and contradiction-handling content that can later land without widening the live seams*

---

## Purpose

This memo covers the Wave 4 research tranche for:

- `C-5`: sprint-contract generation prompt support for all 10 rubric dimensions
- `C-7`: aggregator consistency-check contract for contradiction handling

The goal is not to rewrite production code yet.
The goal is to freeze the design contracts, runtime consumers, negative examples, regression ideas, and explicit out-of-scope boundaries so Wave 4B does not improvise its way into evaluator or deliberation capability creep.

## Accepted Boundary

- Baseline runtime: cleared Wave 3B commit `5cc9585`
- `SprintContractGenerator.generate()` is live on the main pipeline path through `src/keystone/pipeline/orchestrator.py`
- `Layer3RubricScorer` already consumes:
  - `acceptance_criteria`
  - `mandatory_elements`
  - `anti_patterns`
  - `dimension_emphasis`
- The aggregation seam remains narrow:
  - `src/keystone/deliberation/aggregator.py` runs one post-selection consistency check
  - `AggregatedClaim` persists only a boolean `consistency_passed`
- This memo does **not** authorize:
  - global rubric-weight changes
  - new profile-generation logic
  - new contradiction-storage schemas
  - contradiction-graph infrastructure
  - chunked multi-pass pairwise consistency search

Any proposal that requires new persisted inconsistency classes, new evaluator storage, or new aggregation passes must be labeled `new capability` and kept out of Wave 4B.

## Runtime Consumer Summary

| Item | Observed problem | Runtime consumer | Recommended classification | Dependency note |
|---|---|---|---|---|
| `C-5` | Sprint-contract prompt exposes only 6 of the 10 rubric dimensions, so section-level weight guidance cannot express the full live rubric | `src/keystone/evaluator/prompts/sprint_contract_generation.md`, `src/keystone/evaluator/sprint_contract.py`, `src/keystone/evaluator/layer3_rubric.py` | `existing-seam code` | Safe now because the orchestrator already calls `SprintContractGenerator.generate()` at `5cc9585` |
| `C-7` | Consistency check defines only "directly contradict," inspects only the first 10 high-confidence claims, and collapses all disagreement into one binary bucket | `src/keystone/deliberation/aggregator.py` | `existing-seam code` for better contradiction criteria and removal of the 10-claim cap; `new capability` for persisted discrepancy / framing classes | Safe now only if the result still fits the existing boolean `consistency_passed` seam |

## C-5: Sprint Contract Generation Prompt

### Observed problem

- Source artifact: `audit/remediation/round-3/CONTENT-SYNTHESIS-v2.md` `C-5`
- Live prompt surface: `src/keystone/evaluator/prompts/sprint_contract_generation.md`
- Live model surface: `src/keystone/models/evaluation.py`

Current state:

- the prompt permits only 6 dimension names in `dimension_emphasis`
- the omitted live dimensions are:
  - `intent_alignment`
  - `intellectual_honesty`
  - `narrative_coherence`
  - `completeness`
- the runtime rubric and sprint-contract parser already recognize all 10 enum values

So the content surface is narrower than the live runtime consumer.

### Accepted boundary

- Engagement-level evaluation profiles remain the baseline weight system.
- Sprint contracts are section-local overrides, not a second place to re-encode the whole engagement profile.
- Tier-1 gate behavior must remain intact:
  - `intent_alignment`
  - `intellectual_honesty`
  - `completeness`
  - `narrative_coherence`
- This memo does **not** reopen:
  - global rubric calibration
  - weight-floor design
  - profile-template expansion beyond the already accepted research

### Recommended contract

The sprint-contract prompt should expose all 10 `RubricDimension` names as valid `dimension_emphasis` keys and apply them with these rules:

1. Engagement profile first, sprint contract second.
   The evaluation profile already encodes engagement-type defaults. The sprint contract should only express section-local deviations from that baseline.
2. Tier-1 dimensions are expressible but not casual de-emphasis targets.
   In the 4B-ready slice, the four universal gates may be omitted or upweighted, but should not be pushed below baseline with `0.7`.
3. `mandatory_elements` and `anti_patterns` must be concrete and observable.
   They should describe deliverables or failure modes that the Layer 3 prompts can actually reason about, not rubric slogans.
4. `dimension_emphasis` should be sparse.
   Only include keys when the section genuinely turns on that dimension more or less than the selected engagement profile.

### Complete 10-Dimension Emphasis Matrix

| Dimension | 4B-ready emphasis guidance | De-emphasis guidance | Notes |
|---|---|---|---|
| `intent_alignment` | Emphasize for go/no-go, recommendation, diligence, or explicitly decision-bound sections where drifting off the client question would invalidate the output | Do not de-emphasize below baseline in the 4B-ready slice | Universal gate; use when the section is especially prone to elegant-but-irrelevant output |
| `intellectual_honesty` | Emphasize when evidence is thin, management claims are self-serving, competing hypotheses are live, or caveat discipline matters materially | Do not de-emphasize below baseline | Universal gate; anti-patterns should name motivated reasoning or overclaiming failures |
| `completeness` | Emphasize for checklist, diligence, risk-register, compliance, or explicitly exhaustive sections | Do not de-emphasize below baseline | Universal gate; missing mandatory elements should bite here even when prose is strong |
| `narrative_coherence` | Emphasize for executive-summary, storyline, synthesis, or multi-step recommendation sections where argument structure matters | Do not de-emphasize below baseline in the 4B-ready slice | Universal gate despite low default weight |
| `analytical_depth` | Emphasize for root-cause diagnosis, thesis testing, option comparison, or causal reasoning sections | De-emphasize for simple factual inventories or status snapshots | Adaptive dimension |
| `source_quality` | Emphasize for disputed external claims, diligence, regulatory facts, or competitor assertions where provenance quality is load-bearing | De-emphasize only when the section is tightly bounded to a fixed trusted input pack and source differentiation is not the main failure mode | Adaptive dimension |
| `quantitative_rigor` | Emphasize for sizing, modeling, forecast, KPI, unit-economics, or sensitivity-driven sections | De-emphasize for qualitative culture, operating-model, or framing sections with little arithmetic burden | Adaptive dimension |
| `actionability` | Emphasize for turnaround plans, prioritization, next-step design, or recommendation sections | De-emphasize for background or evidence-building sections that are intentionally non-prescriptive | Adaptive dimension |
| `evaluative_surprise` | Emphasize for strategy, market-entry, investment-thesis, or non-obvious insight sections | De-emphasize for confirmatory diligence, compliance, or checklist-style work | Adaptive dimension |
| `calibrated_confidence` | Emphasize when forecast ranges, sparse evidence, scenario uncertainty, or contested claims must be expressed precisely | De-emphasize only for descriptive sections with little uncertainty-expression burden | Adaptive dimension that becomes more important when recommendation risk is high |

### Generation Instructions

The future Wave 4B prompt text should enforce these generation rules:

- valid keys are the exact 10 enum strings from `RubricDimension`
- `dimension_emphasis` is for section-local emphasis, not engagement-wide profile replay
- `mandatory_elements` must be observable output artifacts:
  - tables
  - ranges
  - comparisons
  - explicit caveats
  - named counterarguments
- `anti_patterns` must be concrete failure modes tied to the task or engagement type
- do not use dimension names themselves as pseudo-criteria
- do not use `0.7` on the four universal-gate dimensions in the 4B-ready slice

### Scoring expectations

- Layer 3 still scores all 10 dimensions.
- `dimension_emphasis` changes relative weight, not whether a dimension exists.
- Tier-1 floor behavior is not waived by leaving a dimension out of `dimension_emphasis`.
- Missing a mandatory element should still be able to hurt `completeness`, `intent_alignment`, or `source_quality` even if those dimensions are not upweighted.
- Anti-patterns should be worded so the judge can map them to real penalties, especially on:
  - `intent_alignment`
  - `intellectual_honesty`
  - `actionability`
  - `narrative_coherence`

### Negative example

Bad implementation:

- adding the four omitted dimension names but then blindly mirroring the engagement profile in every section
- using `0.7` on `completeness` or `intellectual_honesty` to excuse a narrow or weak section
- filling `mandatory_elements` with vague text like "high-quality analysis"
- filling `anti_patterns` with generic slogans like "avoid bad writing"

### Regression test ideas

- `tests/unit/evaluator/test_sprint_contract.py::test_dimension_emphasis_accepts_all_ten_rubric_dimensions`
- `tests/unit/evaluator/test_sprint_contract.py::test_prompt_exposes_all_ten_dimension_names`
- `tests/unit/evaluator/test_layer3.py::test_dimension_emphasis_remains_section_local_not_profile_replay`
- `tests/unit/evaluator/test_layer3.py::test_missing_mandatory_element_can_still_hurt_completeness_feedback`

## C-7: Aggregator Consistency Check Contract

### Observed problem

- Source artifact: `audit/remediation/round-3/CONTENT-SYNTHESIS-v2.md` `C-7`
- Live consumer: `src/keystone/deliberation/aggregator.py::_consistency_check`

Current state:

- only the first 10 high-confidence claims are checked
- the prompt uses the undefined phrase "directly contradict"
- the output contract exposes only one bucket: `contradictions`
- any flagged pair causes both claims to fail the boolean `consistency_passed` gate

This is too coarse for multi-methodology aggregation, where some disagreements are genuine contradictions and others are merely scope, magnitude, or framing differences.

### Accepted boundary

- The existing runtime seam stores only `consistency_passed: bool`.
- A 4B-ready slice may improve the prompt criteria and input scope, but must still fit the current boolean gate.
- The 4B-ready slice must **not** introduce:
  - new persisted inconsistency labels
  - new contradiction graphs
  - new aggregation phases
  - auto-rewrite or auto-reconciliation behavior

### Recommended contract

The consistency check should evaluate **all** high-confidence aggregated claims currently admitted by the seam and use the following taxonomy internally before deciding what belongs in the `contradictions` array.

### Contradiction taxonomy

| Class | Definition | 4B-ready behavior under the current seam | Example |
|---|---|---|---|
| `contradiction` | Two claims cannot both be true under the same metric, scope, timeframe, population, and decision context | Return the pair in `contradictions`; both claims fail `consistency_passed` | "US market demand grew 8% in 2025" vs. "US market demand fell 3% in 2025" |
| `discrepancy` | Claims differ on degree, segmentation, timeframe, denominator, or certainty, but could both be true after qualification | Do **not** return as a contradiction in the 4B-ready slice | "Gross margin is ~12%" vs. "Gross margin is 14% in the premium segment" |
| `framing_disagreement` | Claims emphasize different causal stories, implications, or interpretations of compatible facts | Do **not** return as a contradiction in the 4B-ready slice | "Churn reflects weak PMF" vs. "Churn reflects deliberate customer pruning" |

### 4B-ready prompt rules

The future prompt should instruct the judge to:

- compare claims only after checking whether they share the same:
  - timeframe
  - geography
  - metric / denominator
  - segment or population
  - decision context
- prefer "not a contradiction" when qualifiers differ or are missing
- treat magnitude disagreement alone as a discrepancy, not a contradiction
- treat alternative causal interpretation alone as framing disagreement, not a contradiction
- return only true contradictions in the existing JSON shape
- explain in `issue` why the two claims are mutually exclusive

### Input-scope rule

- Remove the hard `[:10]` claim cap from the high-confidence summaries passed to the judge.
- Keep the current high-confidence threshold unless a later controller checkpoint explicitly reopens it.
- If very large claim sets later require chunking or graph search, that is `new capability`, not part of the 4B-ready slice.

### Negative example

Bad implementation:

- flagging "market grows 5-7%" and "market grows 8-10%" as contradictions without checking whether one is a subsegment or different timeframe
- flagging two different explanations of the same evidence as contradictions
- still checking only the first 10 claims and missing a true contradiction later in the list
- inventing new discrepancy arrays or nonblocking warning schemas inside the current boolean seam

### Regression test ideas

- `tests/unit/deliberation/test_aggregator.py::test_consistency_check_does_not_flag_magnitude_discrepancy_as_contradiction`
- `tests/unit/deliberation/test_aggregator.py::test_consistency_check_does_not_flag_framing_difference_as_contradiction`
- `tests/unit/deliberation/test_aggregator.py::test_consistency_check_requires_shared_scope_for_contradiction`
- `tests/unit/deliberation/test_aggregator.py::test_consistency_check_reviews_all_high_confidence_claims_without_ten_claim_cap`

## 4B-Ready Scope Vs Deferred Scope

### 4B-ready scope

- `C-5`: expand the sprint-contract prompt to all 10 dimensions and add the section-local guidance above
- `C-7`: tighten contradiction criteria and remove the 10-claim cap while preserving the current boolean `consistency_passed` seam

### Deferred as `new capability`

- persisted discrepancy or framing-disagreement classes on `AggregatedClaim`
- contradiction graphs or pairwise clustering infrastructure
- automatic confidence downgrades derived from discrepancy classes
- multi-pass or chunked contradiction search for very large claim sets
- profile-generation logic that makes sprint contracts rebuild engagement-level weighting from scratch

## Recommended Wave 4B Write Surfaces

- `src/keystone/evaluator/prompts/sprint_contract_generation.md`
- `tests/unit/evaluator/test_sprint_contract.py`
- `tests/unit/evaluator/test_layer3.py`
- `src/keystone/deliberation/aggregator.py`
- `tests/unit/deliberation/test_aggregator.py`

## Final Classification

- `C-5` is `existing-seam code`.
- `C-7` is split:
  - `existing-seam code` for better contradiction instructions plus removal of the 10-claim cap
  - `new capability` for any design that persists discrepancy or framing-disagreement classes beyond the current boolean seam

Wave 4B should carry only the `existing-seam code` slice above.
Any broader contradiction-taxonomy runtime must be gated into a later capability wave.
