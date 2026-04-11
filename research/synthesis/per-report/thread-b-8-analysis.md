# Report 8: B3 — Taste, Judgment, and Quality of Thought

## Top Findings

### Finding 1: Taste Is Partially Decomposable — 65% Dimensional, 35% Holistic
The report delivers a direct answer to the core Evaluator design question: taste can be encoded into evaluation rubrics, but not completely. Analytic rubrics achieve 66% inter-rater agreement versus 46% for holistic approaches (Jönsson & Balan, 2018), but experts using analytic rubrics process quality holistically first and use dimensional criteria post-hoc. This means the optimal architecture is a two-pass system: dimensional scoring first (conscious-competence layer), holistic gestalt adjustment second (approaching unconscious-competence layer), with a Rejection Library functioning as a negative-space scan (disconfirmation layer). The split is approximately 65% dimensional and 35% holistic/negative-space.

**Layer affected:** L4 (Evaluator), META (Rejection Library)
**Build implication:** The plan's current Evaluator design (Section 5) is a dimensional scoring system. It needs two additional passes: a holistic overlay (±5-10% gestalt adjustment for emergent quality signals that dimensional scoring misses) and a Rejection Library scan (anti-pattern check). This is "better than what we planned" — the two-pass architecture makes the Evaluator more accurate than either approach alone.
**Evidence quality:** Verified — Jönsson & Balan (2018) inter-rater agreement statistics are a published, well-cited meta-analysis; Dreyfus model is well-established (1980/1986/2021); Sadler (1989/2013) evaluative judgment findings are foundational in assessment research.

---

### Finding 2: The Rubric Needs Two New Dimensions — Evaluative Surprise and Calibrated Confidence
The report recommends adding two dimensions to the existing rubric, specifically addressing the gap the current eight dimensions cannot detect. "Evaluative Surprise" (5%): does the brief contain at least one insight, framing, or connection that a competent analyst following standard procedures would not have produced? "Calibrated Confidence" (5%): does the brief appropriately distinguish what is known with high confidence from what is uncertain? The combined weight requires reducing existing dimensions, specifically Analytical Depth (15% to 12%) and Completeness (10% to 8%).

**Layer affected:** L4 (Evaluator — rubric structure)
**Build implication:** The ten-dimension rubric (with reweighting) is a direct upgrade proposal to CAPSTONE-PLAN-v2.md Section 5.3. The Evaluative Surprise dimension directly addresses Voronoff's "conviction argument" — the system must flag convergent, unsurprising analysis rather than reward it. Calibrated Confidence operationalizes the Intellectual Honesty dimension's uncertainty component as a separate scored axis.
**Evidence quality:** Credible — Stripe Press "Tacit" docuseries (December 2025) is a credible practitioner source; Voronoff's "You're Wrong About Taste" essay is well-reasoned but not empirically verified; the Dreyfus model and Ericsson deliberate practice research provide academic grounding for the two-dimension proposal.

---

### Finding 3: LLMs Are Stuck at Conscious Competence — The Evaluator Must Be Designed to Detect Ceiling-Level Failure
The Stripe Press finding — "The ceiling for LLMs, for now, seems to be conscious competence. They can capture procedure, but not judgment" — maps precisely to what the Evaluator must guard against: competent mediocrity. The perfumery test (all three LLMs produced correct but unsurprising note pyramids) operationalizes this. Competent mediocrity is the Evaluator's hardest problem: outputs that pass all dimensional checks but lack genuine quality.

**Layer affected:** L4 (Evaluator — Evaluative Surprise dimension), META (Rejection Library Category 3: judgment failures)
**Build implication:** The Rejection Library needs a Category 3 specifically for judgment failures: "Voronoff's hive mind problem" (arriving at consensus conclusions using consensus tools), "Duncan's AI-experience paradox" (looking right without genuine understanding), and Willison's "cognitive debt" (technically functioning output where reasoning is not understood). These are the hardest to detect and require the holistic overlay pass, not the dimensional scoring pass.
**Evidence quality:** Credible — Stripe Press is a credible practitioner source; Cedric Chin's Commoncog work is reputable practitioner research; the conscious/unconscious competence framing is well-established in education and expertise research.

---

### Finding 4: The Rejection Library Is More Important Than the Rubric Itself
Three independent traditions converge on this finding: Heuer's ACH methodology (the best hypothesis has the least evidence against it, not the most evidence for it), Tetlock's superforecasting (generating reasons for AND against before scoring makes subjects "extremely well calibrated"), and biological taste research (the gustatory system evolved primarily as a rejection mechanism). Quality is better defined by what it excludes than by what it includes. The Rejection Library encodes this negative-space logic at scale.

**Layer affected:** META (Rejection Library), L4 (Evaluator)
**Build implication:** Invert the development priority: build the Rejection Library before refining the rubric. The first entries should not come from theoretical failure mode analysis but from actual deliverable rejections. The report's three-category taxonomy (structural failures, analytical failures, judgment failures) provides the structural template. Category 1 (machine-checkable structural failures) is buildable now; Category 2 (analytical failures) requires the Evaluator to be calibrated; Category 3 (judgment failures) requires human-in-the-loop calibration runs.
**Evidence quality:** Verified — Heuer's ACH methodology is documented CIA tradecraft; Tetlock's superforecasting research is peer-reviewed; the biological taste research is well-established in sensory science.

---

### Finding 5: Without Systematic Expert Calibration, the Evaluator Will Drift Toward Rewarding Mediocrity
The Ericsson 3F loop (Focus → Feedback → Fix It) identifies that evaluation quality only improves through comparison against expert judgments with rapid iteration — not through volume of evaluations performed. The CodeRabbit data (1.7x more issues in AI code vs. human code; 50-67% of AI PRs that pass automated tests rejected by human maintainers for poor quality) demonstrates the scale of the gap between machine evaluation and human quality standards. Without calibration against Keystone deliverables (as specified in Section 5.4 of the plan), the Evaluator will converge toward the very mediocrity it's designed to catch.

**Layer affected:** META (self-improvement loop), L4 (Evaluator — calibration)
**Build implication:** Section 5.4's calibration approach (10+ past Keystone deliverables, each scored by Jack, tuned until Evaluator scores match within ±1 point) is correctly designed but must be positioned as a continuous activity, not a one-time setup. The self-improvement loop must include regular re-calibration runs where Evaluator scores are compared against human expert scores. The Dreyfus model warning — "if one seeks the safety of rules, one will not get beyond competence" — means over-reliance on rubric criteria creates a ceiling. The holistic overlay must be calibrated separately from dimensional scoring.
**Evidence quality:** Verified — Ericsson deliberate practice framework is extensively documented; CodeRabbit study (December 2025) is a specific empirical dataset with 470 PR analysis; METR RCT (19% slower with AI) is a pre-registered controlled trial.

---

## Tool/Framework Verdicts

### AAC&U VALUE Rubrics (Association of American Colleges and Universities)
**Name/maturity:** Used by 5,600+ organizations across 159 countries. 16 rubrics with four progressive performance levels (Benchmark → Capstone). Well-established in higher education assessment.
**Verdict: INTEGRATE**
The design pattern — collaborative expert development, progressive sophistication levels, adaptable language — is the methodology for building the Keystone rubric. The Critical Thinking rubric dimensions (explanation of issues, evidence selection, context/assumptions, position-taking, conclusions) provide a validated model for analytical quality assessment.

### Lasater Clinical Judgment Rubric (Noticing → Interpreting → Responding → Reflecting)
**Name/maturity:** Published in nursing education research. Cronbach's alpha .80–.97. Models expert judgment as a process, not just an output.
**Verdict: INTEGRATE**
The four-stage process evaluation (noticing, interpreting, responding, reflecting) maps to the Intellectual Honesty and Intent Alignment dimensions. An evaluator should assess whether the research brief demonstrates good noticing (identifying the right signals) rather than just whether the conclusion is correct. The Cronbach's alpha reliability is high enough to trust as a design template.

### Google Code Review Framework
**Name/maturity:** Publicly documented at google.github.io/eng-practices. Active engineering practice.
**Verdict: INTEGRATE**
Two specific patterns are directly applicable: (1) the "Nit" prefix system for distinguishing required vs. optional feedback maps to the Rejection Library's severity levels; (2) "technical facts and data overrule opinions and personal preferences" maps to the Evaluator's anti-style-bias design principle.

### Prometheus 2 (Kim et al., EMNLP 2024)
**Name/maturity:** Open-source evaluator model, 7B and 8x7B variants, 72-85% human agreement, supports custom rubrics. Available via pip install prometheus-eval.
**Verdict: INTEGRATE (noted in B3 context, confirmed by B4)**
Directly enables the dimensional scoring layer with custom consulting rubrics. See B4 analysis for full evaluation.

### Tetlock's Superforecaster Calibration Methods (Brier Scoring, Reason-Generation)
**Name/maturity:** Philip Tetlock; documented in "Superforecasting" (2015); empirically validated through forecasting competitions.
**Verdict: INTEGRATE**
Three specific mechanisms: Brier scoring for calibrated confidence evaluation; generating reasons for AND against each assessment as the strongest debiasing technique; and the commitment to self-improvement through calibration feedback. These map to the META layer self-improvement loop design.

### Ericsson's 3F Deliberate Practice Model
**Name/maturity:** Anders Ericsson; documented in multiple publications; the meta-analytic finding (deliberate practice explains ~12% of variance across domains) is controversial but the core mechanism is widely validated.
**Verdict: INTEGRATE**
The 3F loop (Focus → Feedback → Fix It with tight feedback cycles) is the correct model for the META layer's self-improvement mechanism. The Evaluator calibration against Keystone deliverables is the "feedback" component; the loop requires rapid iteration, not annual recalibration.

### Dreyfus Model of Skill Acquisition (1980/1986/2021)
**Name/maturity:** Hubert and Stuart Dreyfus; updated with a sixth stage in 2021. Standard in expertise and education research.
**Verdict: LEARN**
The model provides the conceptual frame for understanding why rubrics alone create a ceiling (stage 3: competent) without reaching proficiency (stage 4) or expertise (stage 5). Specifically relevant for designing the holistic overlay and avoiding over-specification of dimensional criteria. The warning — "if one seeks the safety of rules, one will not get beyond competence" — is the architectural constraint the two-pass design addresses.

### Cedric Chin's Cognitive Task Analysis (Commoncog)
**Name/maturity:** Practitioner research blog. Draws on Gary Klein and Laura Militello's NDM research. Validated by Stripe Press citation.
**Verdict: LEARN**
The taxonomy of tacit knowledge (somatic, relational, collective) suggests the Evaluator can capture relational tacit knowledge (expert judgment patterns across many examples) but not collective tacit knowledge (Keystone-specific culture and standards) without deliberate organizational encoding. The implication: calibration against Keystone deliverables is not optional for capturing collective tacit knowledge.

### Simon Willison's "Slop" Framework
**Name/maturity:** Practitioner-coined term; Willison is a major practitioner voice on LLMs; the "slop" concept is widely adopted in the community.
**Verdict: LEARN**
The concept of "cognitive debt" (technically functioning output where the system doesn't understand its own reasoning) provides a useful Rejection Library Category 3 entry. Willison's shift from "writing code" to "managing context, specifications, and agent oversight" validates the Specification Engine's priority in the architecture.

---

## Contradictions with CAPSTONE-PLAN-v2.md

### Contradiction 1: The plan has eight dimensions; the evidence supports ten
**Plan says:** Section 5.3 defines an eight-dimension judgment rubric.
**Evidence shows:** The rubric needs two new dimensions (Evaluative Surprise at 5%, Calibrated Confidence at 5%) with corresponding weight reductions to existing dimensions (Analytical Depth: 15% → 12%, Completeness: 10% → 8%). The report's reweighted ten-dimension rubric allocates judgment-dependent evaluation at 35% of total weight vs. the plan's approximately 25%, reflecting where real quality differentiation occurs.
**Resolution:** Follow the evidence. The ten-dimension rubric is better than the eight-dimension version. The new dimensions address the most significant blind spots: the conscious-competence ceiling (Evaluative Surprise) and calibrated uncertainty expression (Calibrated Confidence). These dimensions address precisely what the plan identifies as LLMs' weakest areas in Section 5.3.

### Contradiction 2: The plan positions the Rejection Library as a self-improvement artifact; the evidence suggests it is the primary evaluation mechanism
**Plan says:** Section 7.1 describes the Rejection Library as the primary self-improvement engine — accumulated constraints that prevent recurrence.
**Evidence shows:** The Rejection Library's most important function may be real-time evaluation (negative-space scanning during Evaluator runs), not retrospective learning. Heuer's disconfirmation principle, biological taste research, and Tetlock's reason-generation method all suggest that defining quality through rejection is more reliable than defining it through positive criteria.
**Resolution:** Not a contradiction — complement. The Rejection Library serves both functions: real-time negative-space scan (Pass 3 of the evaluation architecture) and retrospective constraint accumulation (META layer). Build the Evaluator to run the Rejection Library as a mandatory third pass after dimensional scoring and holistic overlay.

### Contradiction 3: The plan doesn't distinguish conscious-competence evaluation from unconscious-competence evaluation
**Plan says:** Section 5.3 lists eight dimensions without distinguishing which require procedural evaluation (machine/expert-checkable) versus judgment (judgment-dependent). The verification tier classification (Section 5.7) distinguishes machine-checkable from expert-checkable from judgment-dependent, but does not connect this to evaluation architecture.
**Evidence shows:** The Dreyfus model distinction is architecturally significant. Dimensions 1-6 of the rubric are largely conscious-competence evaluations. Dimensions 7-8 (Intent Alignment, Intellectual Honesty) approach unconscious competence. The two new dimensions (Evaluative Surprise, Calibrated Confidence) are judgment-dependent. Each tier needs different evaluation architecture.
**Resolution:** Follow the evidence. Add the evaluation type column from the report's reweighted rubric table (machine-checkable, expert-checkable, judgment-dependent) to the rubric definition. This determines which evaluation layer each dimension is scored in.

---

## Cross-Report Flags

**Reinforces B4 (Report 9):** B3's Rejection Library Category 3 (judgment failures — hive mind, cognitive debt, flat quality) requires detection mechanisms that B4's taxonomy will likely formalize. Specifically, B3's "Evaluative Surprise" dimension addresses the same problem as B4's "trendslop" failure mode (4.4) from a different angle. B3 frames it as missing exceptional quality; B4 frames it as detecting generic advice dressed as insight. These are the same phenomenon approached from different directions and should converge on a single detection mechanism.

**Reinforces B1 (Report 6):** B3's finding that the Rejection Library is more important than the rubric aligns with B1's "automatic fail" triggers. B1 establishes pre-rubric gates (fabricated citations); B3 establishes post-rubric scanning (negative-space rejection check). The evaluation architecture is: pre-rubric gate → dimensional scoring → holistic overlay → rejection library scan. B1 and B3 together define the full evaluation flow.

**Potential tension with B2 (Report 7):** B2 argues comprehensiveness is harmful; B3 argues the Completeness dimension should be reduced but retained. B3's recommended weight reduction (10% → 8%) is modest; B2's deletion test may imply further reduction. Resolution: the dimensions are measuring different things. Completeness measures coverage of decision-relevant territory; B2's deletion test measures information overload. These are compatible. Add both the absence detection (B3) and the information overload check (B2) as sub-criteria of the Completeness dimension.

**Flag for Thread A (self-improvement loop):** B3's finding that the self-improvement loop is the mechanism preventing evaluator drift toward mediocrity directly validates the META layer's priority in the implementation roadmap. Specifically, the 3F loop design mandate (Focus → Feedback → Fix It with rapid iteration) suggests the self-improvement loop needs calibration cycles measured in engagements (every 5-10 projects), not months. Thread A reports on self-improvement architecture will determine the technical feasibility.

**Flag for Thread A (evaluation infrastructure):** B3 notes that "multi-judge ensembles using diverse model families achieve >80% consensus in most cases" and that the LLM-as-judge literature validates pairwise comparison over absolute scoring. This is consistent with Thread A's likely findings on DeepEval, Prometheus 2, and ensemble judging patterns. The two-pass architecture (dimensional + holistic) may require different model families for each pass to avoid self-enhancement bias.
