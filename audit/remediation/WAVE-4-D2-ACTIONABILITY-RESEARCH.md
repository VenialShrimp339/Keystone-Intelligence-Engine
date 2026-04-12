# Wave 4 D-2 Actionability Research

## Problem Statement

The repo currently contains a live contradiction about what "actionability" means in Phase 1. The accepted architecture-first plan says Phase 1 outputs are decision-informing analysis and must respect the Task-vs-Job boundary. The current `actionability.md` prompt instead rewards Monday-morning recommendations, role-segmented next steps, and operational playbooks. That means the evaluator is presently biased to penalize outputs that are compliant with the accepted Phase 1 boundary and to reward recommendation-packaging behavior that the governing decisions explicitly rejected.

Wave 4 therefore needs a research-backed scoring contract for actionability that measures how well the analysis helps a decision-maker understand what matters, what changes under different conditions, and what tradeoffs are exposed, without demanding stakeholder-specific execution guidance. Wave 4B should implement that contract only at the correct evaluator seam and only against the post-3B content path.

## Accepted Constraint: What D-2 Actually Means

D-2 is resolved. The binding interpretation is:

- Phase 1 output is decision-informing analysis.
- Phase 1 output is not stakeholder-specific recommendation framing.
- The architecture-first plan remains binding; this is not a narrowed research-prep MVP.
- Strong Phase 1 output should help a reader decide among options, understand implications, and identify what evidence matters most.
- Strong Phase 1 output should not pretend to own client politics, role-by-role persuasion, implementation management, or Monday-morning execution choreography.

Operationally, D-2 means the Actionability dimension should score whether the analysis materially sharpens a decision. It should not score whether the output reads like a board memo, operating plan, or consulting recommendation pack.

## What Good Decision-Informing Specificity Looks Like

Good decision-informing specificity makes the analysis usable for a real decision without crossing into recommendation theater. It should explicitly surface the following:

### Decision levers

Decision levers are the variables a decision-maker can actually choose, weight, or constrain differently. Examples: entry geography, timing, partnership model, build-versus-buy posture, pricing posture, diligence depth, or investment pace. Strong outputs make clear which findings matter to which lever instead of leaving the reader to infer relevance.

### Implications

Implications translate findings into decision meaning. They answer: "If this is true, what does it change?" Strong implication framing links evidence to consequences for attractiveness, risk, timing, defensibility, cost, or option value. It is stronger than summary and weaker than prescriptive execution.

### Tradeoffs

Tradeoffs explain what is gained and what is given up across plausible options. Strong outputs identify at least one meaningful cost, constraint, or downside attached to each attractive path. Quantification is preferred when supported by evidence; directional tradeoffs are acceptable when the evidence only supports directional confidence.

### Threshold / condition framing

Threshold framing states when a conclusion holds, when it breaks, or what condition would change the recommended interpretation of the evidence. This can be numeric or qualitative. Good examples include "if approval lead times stay above 12 months, option A loses its timing advantage" or "this conclusion holds only if OEM access can be secured." The point is conditional clarity, not fake precision.

### "So what" logic

"So what" logic is the explicit bridge from finding to decision relevance. It should operate at the finding or subsection level:

- finding
- implication
- decision consequence

Example pattern: "Embedded telematics shifts bargaining power to OEMs; therefore market entry attractiveness depends less on sensor capability and more on partner access; therefore any entry thesis that assumes direct data ownership is structurally weaker."

Strong actionability does not require telling the client what to do on Monday. It requires making it obvious what the evidence means for the decision.

## What Recommendation Creep Looks Like

Recommendation creep is any move from decision-informing analysis into unsupported execution or stakeholder choreography. The evaluator should explicitly reject:

- Role-segmented action plans such as "CEO should do X, Operations should do Y, Finance should do Z."
- Stakeholder-specific persuasion language such as "position this for the board," "sell this to regulators," or "frame this to calm middle management."
- Monday-morning operating playbooks that specify immediate action sequencing, owners, workstreams, or timelines as if the system owns implementation.
- Fake precision about execution steps not supported by evidence, such as exact budget, timeline, staffing, or rollout instructions derived from analytical findings alone.

Other recommendation-creep signals:

- analysis that appears actionable only because it is dressed in imperative verbs
- generic advice repackaged in client language
- unsupported certainty about what a stakeholder will accept or resist
- "next steps" that outrun the evidence base

The penalty principle is simple: the system should not earn a high Actionability score by pretending to be an execution planner.

## Scoring Contract For Actionability

Primary scoring question:

Does this output make the focal decision materially easier by identifying the relevant levers, implications, tradeoffs, conditions, and "so what" logic, without drifting into unsupported recommendation packaging?

Suggested scoring dimensions inside the actionability prompt:

1. Lever clarity: Are the decision levers explicit and connected to the evidence?
2. Implication quality: Does the output explain what the findings change?
3. Tradeoff specificity: Does it name meaningful upside/downside or constraint tradeoffs?
4. Threshold/condition framing: Does it identify when the conclusion holds or changes?
5. "So what" synthesis: Does the reader understand why the findings matter to the decision?
6. Recommendation-creep penalty: Does the output drift into stakeholder-specific playbooks or fake execution precision?

Suggested score anchors:

- `0-20`: Purely descriptive or generic. Findings do not connect to a decision, or the output substitutes empty recommendation language for real analysis.
- `21-40`: Some implications appear, but lever mapping and tradeoffs are mostly absent. The reader gets background, not decision help.
- `41-60`: Moderately decision-relevant. At least some findings are connected to implications or tradeoffs, but the output still leaves important conditions or levers implicit.
- `61-80`: Strong decision-informing analysis. Most major findings connect to explicit levers, implications, and tradeoffs; conditions are stated where they matter; "so what" logic is clear.
- `81-100`: Exceptional decision-informing analysis. The output consistently clarifies how the decision changes under different conditions, makes tradeoffs legible, and remains tightly evidence-grounded without drifting into implementation theater.

Penalty and cap rules:

- Role-segmented action plans should not be required for a high score.
- Unsupported stakeholder playbooks should cap the score rather than increase it.
- Fake precision about implementation steps should cap the score even if the prose sounds decisive.
- A strongly analytical output with explicit implications, tradeoffs, and conditions should be able to score highly even if it contains no recommendations section at all.

## Positive Examples

### Example 1: Lever + tradeoff + condition

"The attractive entry paths are not equivalent. An OEM-partnership path reduces time-to-scale but gives up margin control and bargaining leverage. A phone-based launch preserves economics but is weaker in data defensibility. If OEM access cannot be secured within the first 12 months, the economics case for fast national rollout weakens materially."

Why this is strong:

- names the lever
- states the tradeoff
- includes a condition that changes the conclusion
- informs a decision without assigning an operating playbook

### Example 2: Finding-level "so what"

"California's approval regime favors incumbents with established filings. The implication is not just slower expansion; it is a different regional sequencing logic. A national-first strategy is less attractive if the thesis depends on rapid California scale."

Why this is strong:

- translates a fact into decision meaning
- narrows a strategic option without prescribing a stakeholder-specific action list

### Example 3: Decision-useful without recommendations

"The market is still growing, but the source of advantage has shifted from technology novelty to data-history and regulatory positioning. That changes the relevant diligence question from 'is the product differentiated?' to 'can the entrant overcome data and approval disadvantages quickly enough to matter?'"

Why this is strong:

- reframes the decision
- clarifies what matters most
- contains no recommendation package, yet is clearly actionable in the D-2 sense

## Negative Examples

### Example 1: Role-segmented playbook

"The CEO should approve an OEM strategy this week, the COO should launch a 90-day implementation sprint, and regional managers should begin carrier outreach immediately."

Why this is weak:

- role-segmented action plan
- execution choreography unsupported by the analysis itself
- recommendation creep, not decision-informing specificity

### Example 2: Generic strategic advice

"The company should invest in digital transformation, strengthen partnerships, and stay agile as the market evolves."

Why this is weak:

- applies to almost any company
- no decision lever, no tradeoff, no condition
- generic recommendation packaging masquerading as actionability

### Example 3: Fake precision

"Management should allocate $12M over the next two quarters to a phased rollout across Texas, Florida, and Illinois."

Why this is weak:

- budget, timing, and sequencing precision exceed the evidence shown
- sounds concrete but is analytically ungrounded

### Example 4: Descriptive but not decision-informing

"OEM telematics adoption is rising, regulation varies by state, and incumbents hold more behavioral data."

Why this is weak:

- facts are relevant
- but the output never explains what those facts mean for the decision

## Do Not Require

Strong Phase 1 outputs should not be penalized for omitting:

- role-segmented action plans
- stakeholder-specific persuasion language
- Monday-morning operating playbooks
- implementation timelines, staffing plans, or workstream sequencing
- change-management advice
- political packaging about what a partner or board can "sell"
- budget, ROI, or resource estimates not supported by the evidence
- an explicit recommendations section, if the analysis already makes the decision implications clear
- narrative packaging that belongs to later generation layers rather than Phase 1 analytical output

The correct test is not "did this tell someone exactly what to do tomorrow?" The correct test is "did this make the decision sharper, more conditional, and more evidence-legible?"

## Candidate Test / Fixture Set

Keep the 4B fixture set small and concrete. A good initial set is four paired evaluator fixtures:

1. `actionability_decision_informing_strong.txt`
   Before case: a strong analytical brief with explicit levers, tradeoffs, conditions, and "so what" logic but no recommendations section.
   Expected result: high Actionability score.

2. `actionability_descriptive_background.txt`
   Before case: factually solid market summary with limited decision linkage.
   Expected result: mid or low Actionability score because implication framing is weak.

3. `actionability_recommendation_creep_role_playbook.txt`
   Before case: role-segmented CEO/COO/operations next-step memo with thin analytical grounding.
   Expected result: capped score despite concrete-sounding language.

4. `actionability_fake_precision.txt`
   Before case: highly specific execution timeline, budget, and ownership instructions not warranted by the evidence.
   Expected result: penalty for fake precision and recommendation creep.

Suggested 4B regression tests:

- `test_actionability_prompt_grades_decision_informing_specificity`
- `test_actionability_prompt_does_not_require_role_segmented_actions`
- `test_actionability_prompt_penalizes_recommendation_creep`
- `test_actionability_prompt_penalizes_fake_precision`
- `test_actionability_prompt_rewards_threshold_and_tradeoff_framing`

Suggested comparison rule for the fixtures:

- the strong decision-informing analysis fixture should outrank the role-playbook fixture
- the descriptive-background fixture should outrank empty trendslop but remain below true decision-informing analysis
- the fake-precision fixture should not achieve a high score merely by sounding operationally concrete

## Implementation Readiness Notes

This research is implementation-ready only as an evaluator-content contract, not as a broad rewrite of production output behavior.

- The primary 4B target should be the Actionability evaluator prompt plus tightly coupled evaluator tests and fixtures.
- Any prompt/schema change should preserve the accepted boundary: grade decision usefulness, not execution packaging.
- Implementation should wait for the post-3B content path so Actionability is grading the stable final representation rather than the pre-L2 direct-render flow.
- This work should stay narrow. It does not by itself justify changes to recommendation fields in confidence models, markdown rendering, or other output seams unless a later memo explicitly scopes those as separate follow-on work.
- Be careful not to smuggle Wave 5 calibration policy into 4B. This memo defines what to score, not final profile weights or passing thresholds.
- The current prompt also contains stale authority theater ("HBR March 2026, 15K+ trials"). 4B should remove fabricated authority while rewriting the scoring contract.
- The nearest adjacent dimensions are `intent_alignment` and `narrative_coherence`. Actionability should remain distinct:
  - `intent_alignment` asks whether the output addresses the decision.
  - `narrative_coherence` asks whether the argument hangs together.
  - `actionability` should ask whether the analysis makes the decision materially easier by clarifying levers, implications, tradeoffs, and conditions.

- Single highest-value file likely to change in 4B: `src/keystone/evaluator/prompts/actionability.md`
- Single biggest risk if this research is implemented against the wrong runtime seam: rewriting for the pre-L2 direct-render path instead of the post-3B evaluator/content seam, which would optimize for the wrong intermediate representation and create a false sense that Actionability improved when the live final content path is still grading different behavior.
