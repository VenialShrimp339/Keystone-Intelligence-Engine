# Wave 4 / 4B Prework

## Scope

Planning-only decomposition for the accepted architecture-first post-2B plan.

Inputs read per prompt:
- `graphify-out/GRAPH_REPORT.md`
- `audit/remediation/WORKSTREAM-STATUS.md`
- `CURRENT-STATE.md`
- `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`
- `audit/remediation/WAVE-2B-RECONCILIATION.md`
- `audit/remediation/round-3/CONTENT-SYNTHESIS-v2.md`
- `audit/remediation/round-3/PLANNING-ADDENDUM.md`
- `audit/remediation/WAVE-3-3B-PREWORK.md`
- `CAPSTONE-PLAN-v2.md`
- `JACK-ARCHITECTURAL-DIRECTIVES.md`

Binding assumptions carried forward from those inputs:
- The accepted architecture-first overlay is binding.
- Phase 1 remains decision-informing analysis, not stakeholder-specific recommendation framing.
- Wave 4 is research/design plus low-risk polish.
- Wave 4B is implementation of Wave 4 content designs against the post-2B / post-3 / post-3B runtime.

Graphify context matters here: `StructuredFinding`, `CitationManifest`, `ResearchTask`, `EngagementSpec`, and the MCP gateway are current cross-community bridge nodes. For Wave 4 / 4B that means the highest downstream integration risk is not isolated prompt text by itself, but prompt text that changes behavior at the research/evaluator/routing seams.

## Wave 4 vs Wave 4B Delivery Map

| Track | Wave 4 research / design output | Wave 4B implementation output | Hard dependency |
|---|---|---|---|
| D-2 actionability reset | Define what "decision-informing specificity" means in scoring terms; produce positive/negative examples and rejection rules for recommendation creep. | Rewrite `src/keystone/evaluator/prompts/actionability.md` and align any related scoring/tests to grade implications, tradeoffs, decision levers, and "so what" logic rather than Monday-morning role playbooks. | Research can start now. Implementation should target the post-3B content path so it scores the final outline/render flow, not the pre-L2 path. |
| Core research-prompt quality | Research-backed designs for C-1, C-2, C-3, C-4, C-9, C-12, and C-13: analyst prompts, shallow synthesis quality bar, deep-prompt materiality guidance, lens utilization, injection delimiters, judge selection, and intent-clarifier cleanup. | Update `src/keystone/deliberation/analyst.py`, `src/keystone/research/research_agent.py`, `src/keystone/specification/prompts/intent_clarification.md`, `src/keystone/specification/intent_clarifier.py`, and related tests/fixtures. | Research can start now. Some implementation should wait for Wave 3 template wiring and Wave 3B loop continuity so prompt text targets the final runtime. |
| Sprint-contract / rubric content | Research-backed content for C-5 and C-7: full 10-dimension emphasis guidance plus contradiction/discrepancy handling. | Update `src/keystone/evaluator/prompts/sprint_contract_generation.md`, `src/keystone/evaluator/sprint_contract.py`, `src/keystone/evaluator/layer3_rubric.py`, and tests so the live runtime consumes the researched criteria. | Must wait for Wave 2B because `E-9`, `E-6`, and `E-7` make the sprint-contract path load-bearing. |
| Template / routing content | Designs for C-6, C-8, C-10, and C-14: classification tiebreakers, tool-selection heuristics, dynamic lens selection, and template enrichment. | Update `src/keystone/specification/prompts/classification.md`, `src/keystone/specification/engagement_classifier.py`, `src/keystone/specification/template_registry.py`, and possibly `src/keystone/evaluator/rubric_config.py`. | Final implementation must wait for Wave 3 dual-axis taxonomy and profile expansion. |
| Evaluator-verification content | Design decisions for C-11 and C-15: claim-support verification and minimum snippet-quality policy. | Update `src/keystone/evaluator/layer1_deterministic.py`, `src/keystone/evaluator/layer2_citation_gate.py`, `src/keystone/evaluator/evaluator.py`, and tests if the chosen design stays within existing evaluator seams. | Research can start now. Final implementation should wait for Wave 3 verifier/provenance work and may spill beyond 4B if it requires a new evaluator capability rather than prompt/rule changes. |
| Wave 4 polish | Prepare exact fix specs for E-2, E-4, and E-5. These do not need open-ended research. | Apply the low-risk corrections in the Wave 4 lane: completeness classification, renderer cleanup, and sample-schema sync. | Minimal architectural dependency, but still safer after Wave 3 / 3B if renderer contracts are changing. |

Working boundary:
- Wave 4 should produce research memos, prompt/rubric/template specs, example sets, and test hypotheses.
- Wave 4B should only implement items whose runtime seam is already stable.

## What Can Be Researched Now In Parallel

The following sidecars are safe to run now without waiting for code changes, because they are evidence-gathering and design-definition tasks rather than implementation:

| Parallel research lane | Bucket C items | Why it is safe now | Required output |
|---|---|---|---|
| 1. Actionability under D-2 | D-2, plus the Wave 4 portion of F4 | D-2 is already resolved: Phase 1 output is decision-informing analysis. The contradiction is conceptual, not blocked on runtime work. | A design memo defining scoring anchors, anti-patterns, pass/fail examples, and exact wording rules for "decision-informing specificity." |
| 2. Core L1/L1.5 prompt redesign | C-1, C-2, C-3, C-4, C-9, C-12, C-13 | These are content questions about quality bars, calibration, differentiation, and delimiter discipline. They do not require new architecture to be researched. | Draft prompt specs, field/schema notes, before/after examples, and explicit test hypotheses for each prompt. |
| 3. Sprint-contract and aggregation content | C-5, C-7 | The runtime consumer is blocked on 2B, but the content research is not. | Complete dimension-emphasis matrix, contradiction taxonomy, and concrete criteria text for generation and scoring. |
| 4. Template and routing content design | C-6, C-8, C-10, C-14 | D-1 is resolved architecturally, so research can proceed against the accepted dual-axis target even though implementation waits for Wave 3. | Routing rules, tool-selection table, lens-registry concept, enriched template content outlines, and a tiebreaker rule that assumes the dual-axis future state. |
| 5. Evaluator verification design | C-11, C-15 | The open work is method/design selection, not code. This is exactly the kind of sidecar research Wave 4 should absorb. | A design memo covering support verification options, snippet sufficiency policy, failure modes, and recommended Phase 1/4B boundary. |

Research lanes that should explicitly stay sidecar-only for now:
- Anything that rewrites production prompts before the evidence package is written.
- Anything that assumes the pre-3B renderer/content path is final.
- Anything that treats provisional profile weights as calibrated truth before Wave 5.

## What Must Wait For Wave 2B

Wave 2B is the point where the enforcement and sprint-contract path becomes real instead of advisory. The following work should not move from research into implementation until 2B is complete and adversarially reviewed:

- Any 4B change that expects `SprintContractGenerator.generate()` output to be consumed at runtime. That includes C-5 design work once it becomes code, because `dimension_emphasis`, `mandatory_elements`, and `anti_patterns` are not load-bearing until `E-9`, `E-6`, and `E-7` land.
- Any profile-specific content logic that assumes the evaluator is receiving the routed profile from `ResearchSpec`. Until `E-10` lands, profile-aware wording or rubric branching is liable to be silently scored against the default profile.
- Any content design that depends on the final Wave 2B enforcement behavior to define pass/fail semantics. Research can propose rules now, but implementation should target the post-2B evaluator surface, not the current advisory one.
- Any attempt to evaluate Wave 4 prompt ideas using live outputs from the current runtime as if they reflect the accepted enforcement model. Those comparisons will be misleading until 2B is cleared.

Practical consequence:
- Wave 4 can fully research sprint-contract and rubric content now.
- Wave 4B should not start that implementation track until 2B has turned the execution path on for real.

## What Must Wait For Wave 3 / 3B

Wave 3 and Wave 3B stabilize the routing, structuring, and loop-control seams that Wave 4B content changes need to target.

### Must wait for Wave 3

- Final implementation of classification tiebreakers, dynamic lens selection, and template/routing enrichment should wait for the Wave 3 dual-axis taxonomy (`DomainCategory`, `secondary_types`, profile expansion, domain-aware template routing).
- Any content logic that assumes template system prompts are reliably wired into the research path should wait for the Wave 3 deep-research formalization/template-wiring work.
- Evaluator-verification implementation that needs the concrete post-synthesis verifier or provenance-sidecar shape should wait until Wave 3 defines those seams.

### Must wait for Wave 3B

- Actionability implementation should target the post-L2 content path. If Wave 4B rewrites scoring language against the pre-L2 direct-render flow, it risks grading the wrong intermediate representation once `StructuredOutline` lands.
- Any prompt or template change that references section structure, issue-tree branch placement, framework selection, or per-section evidence packaging should wait for thin Pipeline-L2 to exist.
- Any prompt or rubric design that assumes round-to-round continuity, gap carry-forward, or novelty-based stopping should wait for the Wave 3B live iterative loop. Research can define those behaviors now; implementation should wait for the actual loop contract.

The single most important 3 / 3B dependency for 4B is seam stability:
- Wave 4 research can be broad.
- Wave 4B implementation should be narrow and should only target seams that Wave 3 / 3B have already frozen.

## Safe Future Implementation Slices

The safest 4B implementation plan is to keep slices disjoint and avoid mixing content edits with moving architecture seams.

### Slice A: Actionability / D-2 evaluator content

Expected write set:
- `src/keystone/evaluator/prompts/actionability.md`
- `src/keystone/evaluator/layer3_rubric.py`
- `tests/unit/evaluator/test_layer3.py`
- `tests/unit/evaluator/test_evaluator.py`
- evaluator fixtures under `tests/fixtures/evaluator/`

Why this is safe:
- It is a focused evaluator-content slice.
- It has a clear acceptance criterion: reward decision-informing specificity, reject recommendation-packaging creep.
- It should be owned by one worker because prompt text, scoring semantics, and tests must move together.

### Slice B: Core research-prompt quality

Expected write set:
- `src/keystone/deliberation/analyst.py`
- `src/keystone/research/research_agent.py`
- `src/keystone/specification/prompts/intent_clarification.md`
- `src/keystone/specification/intent_clarifier.py`
- `tests/unit/deliberation/test_analyst.py`
- `tests/unit/research/test_research_agent.py`

Why this is safe:
- It stays mostly inside the L1 / L1.5 content path.
- It can be split from evaluator work.
- It should not be merged with Wave 3B loop-control changes in the same worker slice.

### Slice C: Sprint-contract / rubric-content wiring

Expected write set:
- `src/keystone/evaluator/prompts/sprint_contract_generation.md`
- `src/keystone/evaluator/sprint_contract.py`
- `src/keystone/evaluator/layer3_rubric.py`
- `tests/unit/evaluator/test_sprint_contract.py`
- `tests/unit/evaluator/test_layer3.py`

Why this is safe:
- It is a self-contained evaluator/rubric slice once Wave 2B has made the path live.
- It should not start before 2B because otherwise the edits risk becoming dead code or misleading tests.

### Slice D: Template / routing content

Expected write set:
- `src/keystone/specification/prompts/classification.md`
- `src/keystone/specification/engagement_classifier.py`
- `src/keystone/specification/template_registry.py`
- `src/keystone/evaluator/rubric_config.py`
- `tests/unit/specification/test_engagement_classifier.py`
- `tests/unit/specification/test_template_registry.py`
- `tests/unit/evaluator/test_rubric_config.py`

Why this is safe:
- It aligns with the Wave 3 dual-axis routing path.
- It is mostly isolated from evaluator prompt text and research-agent prompt text.
- It should be treated as post-Wave-3 4B work, not pre-Wave-3 experimentation in code.

### Slice E: Evaluator verification-content rules

Expected write set:
- `src/keystone/evaluator/layer1_deterministic.py`
- `src/keystone/evaluator/layer2_citation_gate.py`
- `src/keystone/evaluator/evaluator.py`
- `tests/unit/evaluator/test_layer1.py`
- `tests/unit/evaluator/test_layer2.py`
- `tests/unit/evaluator/test_evaluator.py`

Why this is safe:
- It localizes C-11 / C-15 implementation if the chosen design remains within the existing evaluator stack.
- It should be explicitly re-scoped out of 4B if the research concludes that a new verification stage or new content-fetch capability is required.

### Slice F: Low-risk polish

Expected write set:
- `src/keystone/pipeline/markdown_renderer.py`
- relevant evaluator prompt/config surface for Completeness
- sample / fixture files under `tests/fixtures/`
- `tests/unit/pipeline/test_markdown_renderer.py`

Why this is safe:
- It is low-conflict cleanup work.
- It should land after the renderer contract is stable enough that Wave 3B is not about to rewrite the same surface.

## Research Program For Bucket C / content-layer work

The Wave 4 research program should produce evidence packages, not speculative rewrites. The right unit of work is a research memo that ends in a proposed content contract plus test hypotheses.

### Program 1: Actionability under the D-2 decision-informing-analysis stance

Items:
- D-2
- the Wave 4 portion of F4

Research question:
- What does strong "decision-informing specificity" look like when the system is forbidden from doing stakeholder-specific recommendation framing?

Must explicitly define:
- what counts as a clear decision lever
- what counts as a quantified tradeoff
- what counts as valid implication framing
- what "so what" means at finding level
- what recommendation creep looks like and how to penalize it

Required artifact:
- a scoring contract for `actionability.md`
- 5-10 positive/negative examples
- explicit "do not require" rules for timelines, role-segmented action plans, and client-political packaging

Implementation note:
- Research starts now.
- Code should wait until the final post-3B content path is available.

### Program 2: Research-generation prompt quality

Items:
- C-1
- C-2
- C-3
- C-4
- C-9
- C-12
- C-13

Focus:
- analyst-method differentiation
- shallow-mode quality standards
- deep-mode materiality over volume
- lens utilization instructions
- injection-safe delimiter usage
- judge-selection criteria
- intent-clarifier Step 4 resolution

Required artifact:
- one memo per prompt family
- revised contract text
- before/after examples
- any schema consequences called out explicitly
- one proposed regression test per change

Implementation note:
- This is the most productive Wave 4 design tranche after D-2 because it shapes the content entering every downstream stage.

### Program 3: Rubric / sprint-contract content pushed out of Wave 2B

Items:
- C-5
- C-7

Why this belongs in Wave 4 research:
- The runtime wiring belongs to Wave 2B, but the content design was intentionally not solved there.
- Wave 2B should make the mechanism real.
- Wave 4 should decide what high-quality content the mechanism should actually carry.

Required artifact:
- complete 10-dimension emphasis matrix
- contradiction / discrepancy / framing-disagreement taxonomy
- concrete generation instructions and scoring expectations

Implementation note:
- Do not backfill these as speculative prompt edits before 2B is done.
- Treat them as 4B-ready only when the live sprint-contract path has been verified.

### Program 4: Template, routing, and content-selection design

Items:
- C-6
- C-8
- C-10
- C-14

Focus:
- borderline classification tiebreaker under the accepted dual-axis model
- tool-selection heuristics by task type
- dynamic lens-selection rules
- template enrichment strategy and tighten-only escape hatch

Required artifact:
- routing rules aligned to the Wave 3 taxonomy target
- tool-selection table
- lens-registry concept
- template enrichment blueprint with examples

Implementation note:
- Research can run now because D-1 is settled architecturally.
- Final code should wait for the Wave 3 taxonomy/routing surface.

### Program 5: Evaluator verification design

Items:
- C-11
- C-15

Focus:
- claim-support verification, not just citation existence
- minimum snippet quality for meaningful factual verification
- how to behave when source evidence is too thin

Required artifact:
- design memo comparing feasible Phase 1 options
- recommendation on whether the work fits inside 4B or needs a post-4B architectural slot
- adversarial examples covering real-citation / unsupported-claim failure modes

Implementation note:
- This is the one Bucket C program that may legitimately escape 4B if the answer is "new capability, not content rewrite."

### Rule For Avoiding Speculative Prompt Rewrites

No Wave 4 research memo should be treated as 4B-ready unless it includes all of the following:
- the exact observed problem and the source document or fixture that proves it
- the accepted architectural boundary it must respect
- the runtime consumer of the proposed change
- at least one negative example showing what the new text must reject
- at least one regression test idea
- a note on whether the change depends on 2B, 3, or 3B landing first

If any of those are missing, the output is a brainstorming note, not an implementation-ready design.

## Test / Review Plan For Wave 4B

Wave 4B should be reviewed as a content-system release, not just a prompt-edit release.

### Entry criteria before 4B starts

- Wave 2B is complete and adversarially cleared.
- The specific Wave 3 / 3B seam targeted by the slice is complete enough that the contract is stable.
- The corresponding Wave 4 research memo exists and includes evidence, examples, and test hypotheses.
- Goldens / fixtures exist for the behaviors being changed.

### Minimum test expectations by slice

| Slice | Minimum tests |
|---|---|
| Actionability / D-2 | `test_actionability_prompt_grades_decision_informing_specificity`; a regression that rejects recommendation framing; fixture diff showing stronger tradeoff/implication grading without requiring role-segmented actions. |
| Core research prompts | Tests that shallow mode enforces a quality bar; deep mode does not reward raw claim count; analyst prompts remain method-distinct; injection delimiters treat embedded content as data. |
| Sprint-contract / rubric content | Tests that all 10 dimensions are expressible; `dimension_emphasis`, `mandatory_elements`, and `anti_patterns` actually flow into scoring; contradiction handling no longer collapses partial disagreement into binary contradiction. |
| Template / routing content | Tests that dual-axis routing chooses the right template/profile path; tool-selection guidance is injected where expected; enriched templates do not regress the tighten-only behavior for standard engagements. |
| Evaluator verification design | Tests for title-only / snippet-thin citations; unsupported claims with real citations; behavior when support is ambiguous; explicit distinction between `UNVERIFIABLE` and `NOT_SUPPORTED` style outcomes if the design adopts that split. |

### Review sequence

1. Research-to-code conformity review: confirm the implementation matches the Wave 4 memo, not a fresh ad hoc rewrite.
2. Unit and fixture review: confirm the tests encode the intended boundary conditions.
3. Adversarial review: specifically look for recommendation creep, dead prompt branches, dead rubric branches, and content changes that are invisible because the runtime seam is still unwired.
4. Comparative output review: run a small fixed set of representative engagements and compare before/after behavior qualitatively.
5. Wave gate: do not treat 4B as complete until the changed content path has both passing tests and a human-read output diff that looks better for the right reasons.

### Residual risk to watch

- False confidence from prompt diffs that do not change live runtime behavior.
- Rewriting content against the pre-L2 renderer path and having to redo it after Wave 3B.
- Smuggling calibration-policy decisions into 4B that the accepted plan explicitly deferred to Wave 5.

## Next Sidecar / Remaining Blocker

- **Single best next sidecar:** a focused Wave 4 research session for D-2 actionability redesign that defines the decision-informing-analysis scoring contract, examples, and anti-patterns for `src/keystone/evaluator/prompts/actionability.md`.
- **Single best blocker that would still prevent starting 4B implementation:** Wave 3B seam instability, especially the absence of the final Pipeline-L2 / iterative-loop content path that 4B prompt and evaluator changes need to target.
