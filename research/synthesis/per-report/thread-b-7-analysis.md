# Report 7: B2 — Decision-Useful vs. Comprehensive Research

## Top Findings

### Finding 1: A Complete Five-Level Decision-Usefulness Rubric Is Ready to Encode
The report delivers a fully specified five-level rubric (Level 1: actively misleading through Level 5: changes the decision framing) with concrete pass/fail indicators, anti-gaming safeguards, and consulting examples at each level. This is directly encodable as the "decision-usefulness" scoring dimension within the Evaluator's Intent Alignment dimension. The rubric's theoretical grounding (Klein's Data/Frame sensemaking, Tetlock's superforecasting, Kahneman's Noise framework) is independently validated. This is not a proposal — it is a deliverable.

**Layer affected:** L4 (Evaluator — Intent Alignment dimension primarily, with secondary effects on all eight dimensions)
**Build implication:** The five levels provide the scoring scaffold for Intent Alignment. Level 3 is the minimum acceptable score for any client-facing deliverable; Level 4 is the target; Level 5 is a flag for exceptional output. The six gaming-resistance safeguards (counterfactual deletion test, specificity-to-context ratio, integration test, strongest-counterargument acknowledgment, prediction falsifiability, noise audit) are anti-gaming mechanisms for the Evaluator design.
**Evidence quality:** Verified (Kahneman/Klein collaboration documented, Noise framework 2021, superforecasting research peer-reviewed); Credible (2026 executive usage statistics from Deloitte, HBR, MIT Sloan surveys).

---

### Finding 2: The Counterfactual Deletion Test Is the Single Most Powerful Decision-Usefulness Signal
The report's most operationally useful contribution is the counterfactual deletion test: "If this analysis were removed from the decision-maker's information set, would the optimal decision change?" This single test distinguishes Level 3 from Level 4 and cannot be gamed by including more information — only by including decision-altering information. It operationalizes the entire debate between "comprehensive" and "decision-useful" into a single binary check.

**Layer affected:** L4 (Evaluator)
**Build implication:** Build the counterfactual deletion test as an Evaluator sub-routine: after scoring a section, ask whether the section introduces at least one finding that is both non-obvious to an informed decision-maker AND material to the decision's direction, timing, scope, or risk profile. An agent cannot game this by asserting novelty — the Evaluator must independently assess whether the underlying finding is genuinely novel relative to the baseline knowledge assumed for the decision context.
**Evidence quality:** Credible — derived from Klein's Data/Frame sensemaking theory (well-documented academic work) and Tetlock's superforecasting (peer-reviewed, forecasting competitions); the specific test formulation is analytically derived, not empirically measured.

---

### Finding 3: Information Overload Past Decision-Readiness Actively Degrades Quality — Not Just Wastes Time
The report cites Federal Reserve research showing a one standard deviation increase in information overload increases the market risk premium by 35 basis points, and a meta-analysis of 31 experiments confirming both diversity and repetition of information have adverse impact on decision quality. More striking: Heuer's finding that "once an experienced analyst has the minimum information necessary to make an informed judgment, obtaining additional information generally does not improve accuracy but does increase confidence to the point of overconfidence." This means comprehensiveness is not neutral — it actively makes decisions worse by inflating confidence without improving accuracy.

**Layer affected:** L4 (Evaluator — Completeness and Actionability dimensions), L3 (Deliverable Generation)
**Build implication:** The Evaluator must penalize unnecessary length and breadth, not reward it. Add a deletion test to the Completeness dimension: "Would removing 50% of the content change the recommendation? If not, the output is overloaded." This is a direct inversion of typical word-count or coverage metrics. The generation layer (L3) should also be constrained by decision-readiness signals from the Evaluator.
**Evidence quality:** Credible (Federal Reserve research, Heuer's work is well-documented CIA tradecraft; the meta-analysis is cited but not named).

---

### Finding 4: "Trendslop" Is a Documented LLM Structural Bias, Not a Prompt Engineering Problem
The HBR study (March 2026, Romasanta/Thomas/Levina) across 15,000+ LLM trials found that all seven tested LLMs default to trendy, buzzword-aligned strategies regardless of context — differentiation over cost leadership, augmentation over automation, long-term over short-term. The report emphasizes: "better prompting could not fix this bias." The CFA Institute's May 2025 analysis corroborates: LLM system prompts bias outputs "toward safe, consensus views and user affirmation." This means anti-trendslop detection must be an Evaluator function, not a prompt engineering intervention.

**Layer affected:** L4 (Evaluator — Actionability dimension), L1 (Research Agents)
**Build implication:** The Evaluator's Actionability dimension needs a "differentiation test": could this recommendation apply equally to three or more competitors without modification? A specificity-to-context ratio check should be computed: Level 4+ requires more than 70% of core analytical claims to reference specific entities, numbers, dates, or conditions unique to the decision context. This is a gaming-resistant quantitative check.
**Evidence quality:** Verified — named academic researchers at major universities, 15,000+ trials, March 2026 HBR publication.

---

### Finding 5: The ICD 203 Distinction Between Estimative and Current Intelligence Requires Evaluator Mode-Switching
The IC distinguishes between estimative intelligence (forward-looking, probabilistic, requires explicit uncertainty quantification) and current intelligence (situation updates, requires timeliness and source quality). This maps directly to different consulting research types: market sizing and strategic recommendation (estimative) vs. competitive monitoring and situation assessment (current). The Evaluator should detect which mode the research agent was addressing and apply different quality standards accordingly.

**Layer affected:** L4 (Evaluator), L0 (Specification Engine — task typing)
**Build implication:** Add a research-type field to the research-tasks.json format: "type": "estimative" or "type": "current". The Evaluator applies appropriate weight profiles per type. Estimative tasks get heavier weight on Quantitative Rigor and Intellectual Honesty; current intelligence tasks get heavier weight on Source Quality and timeliness. This is a direct encoding of ICD 203 Tradecraft Standards.
**Evidence quality:** Verified — ICD 203 is an official US government directive with multiple revisions through 2023.

---

## Tool/Framework Verdicts

### Kahneman's Noise Framework (2021)
**Name/maturity:** Published 2021 (Kahneman, Sibony, Sunstein). Applied to AI benchmarks in 2024 Scientific Reports study finding ~10% human and ~4% ChatGPT performance variation on identical tasks.
**Verdict: INTEGRATE**
Noise audit via parallel evaluation is directly implementable: the Evaluator should score outputs using multiple independent passes and adopt the lower score as a conservative default when passes diverge; this implements Kahneman's decision hygiene in the Evaluator architecture.

### Klein's Data/Frame Sensemaking Theory
**Name/maturity:** Developed through Gary Klein's NDM research; the six sensemaking activities (elaborating, questioning, comparing, preserving, reframing, seeking) are documented in "Sources of Power" and "Seeing What Others Don't."
**Verdict: INTEGRATE**
The five-level rubric is built directly on Klein's framework; Level 3 = elaborating within existing frame, Level 4 = questioning and comparing, Level 5 = reframing. Integrate as the theoretical backbone of the decision-usefulness scoring sub-system.

### Tetlock's Superforecasting Methodology
**Name/maturity:** Philip Tetlock; documented in "Superforecasting" (2015); operationalized through IARPA's Good Judgment Project; Tetlock joined ForecastEx Board (CFTC-registered prediction market) January 22, 2026.
**Verdict: INTEGRATE**
Reference class calibration (providing base rates for the decision type), outside-view vs. inside-view detection, and the multi-agent implementation pattern (independent research → distinct theses → structured debate → convergence) are directly encodable Evaluator checks. The base rate check for Level 4 research (does the analysis provide a reference class for the type of decision being made?) is a specific, implementable criterion.

### SOFAI Architecture (Fabiano et al., Communications of the ACM, 2025)
**Name/maturity:** Published 2025 in a major ACM journal. Implements System 1/System 2 agent metacognition for task routing.
**Verdict: LEARN**
The insight that analytical mode must match problem type is valuable; the architecture itself is a research contribution, not a deployable product. Borrow the concept (mode-matching between task type and evaluation rigor) without building the SOFAI architecture directly.

### Rosenzweig's Halo Effect / "The Halo Effect" (2007)
**Name/maturity:** Phil Rosenzweig, "The Halo Effect and the Eight Other Business Delusions" (2007); the 2025 PNAS study finding LLMs favor other LLMs' outputs provides updated empirical grounding.
**Verdict: INTEGRATE**
The style-over-substance detection imperative — high confidence/tone with low specific/verifiable claims — is directly buildable as an Evaluator heuristic; the 2025 PNAS LLM-prefers-LLM-output finding means the Evaluator itself is susceptible to this bias and must use cross-model or deterministic evaluation for style-substance divergence detection.

### Heath Brothers Decision Frameworks (Made to Stick / Decisive)
**Name/maturity:** Chip and Dan Heath; "Made to Stick" (2007), "Decisive" (2013). The SUCCESs model and WRAP framework are practitioner-grade rather than peer-reviewed.
**Verdict: LEARN**
The tripwire concept from Decisive (predetermined conditions that trigger decision reconsideration) maps to the Level 4 criterion "recommendations specify under what conditions to reconsider"; borrow the concept for encoding conditional recommendation criteria, but the frameworks themselves are not directly integrable as evaluation components.

### ICD 203 Tradecraft Standard 2 (Uncertainty Expression)
**Name/maturity:** Official US government directive, seven-term probability lexicon with defined numerical ranges.
**Verdict: INTEGRATE**
The seven-term lexicon is directly encodable as a pass/fail criterion for the Intellectual Honesty dimension; any deliverable using vague hedging ("this could go either way") instead of calibrated probability language fails Standard 2. Build a calibrated language checker that scans for vague uncertainty language and flags it.

---

## Contradictions with CAPSTONE-PLAN-v2.md

### Contradiction 1: The plan's Completeness dimension does not penalize information overload
**Plan says:** Completeness (10%) scores for "absence detection: what perspectives or data are systematically missing?" — focused on what should be present but isn't.
**Evidence shows:** The bigger failure mode is the presence of decision-irrelevant content that inflates confidence while consuming attention. Comprehensive analysis past the decision-readiness point is actively harmful, not neutral. The 50% deletion test — "would removing half the content change the recommendation?" — is a concrete check the plan does not include.
**Resolution:** Follow the evidence. Completeness should score both absence detection (what's missing that matters) AND presence detection (what's present that doesn't matter). Add a deletion test sub-criterion to the Completeness dimension.

### Contradiction 2: The plan implies the rubric is the same for all deliverable types
**Plan says:** Section 5.3 presents a single eight-dimension rubric; Section 5.5 has tiered evaluation intensity (light-touch, standard, deep) but doesn't distinguish between estimative and current intelligence types.
**Evidence shows:** Different research types have different quality criteria. Market sizing (estimative) requires uncertainty quantification as a primary criterion; competitive monitoring (current intelligence) requires timeliness and source quality as primary criteria. Applying the same weight profile to both misallocates evaluation resources.
**Resolution:** Follow the evidence. The plan's tiered intensity (5.5) addresses depth of evaluation, not type appropriateness. Add a type field to research-tasks.json and maintain type-specific weight profiles for the rubric.

### Contradiction 3: The plan's Deliberation phase outputs a Confidence Map — the rubric should assess whether this map is accurate
**Plan says:** Section 4.3 describes the Deliberation Phase producing a Confidence Map showing high-confidence, moderate-confidence, and contested claims.
**Evidence shows:** The Noise framework finding — ~4% ChatGPT performance variation on identical tasks — means the confidence ratings in the map may themselves be noisy. The Evaluator should run the noise audit (parallel independent evaluation passes) specifically on Confidence Map claims, not just on the deliverable content.
**Resolution:** The plan doesn't contradict this, but the implication is absent. Add a noise audit step to the Evaluator specifically for Confidence Map claims: generate the same confidence rating twice with different framing and check for divergence. If the same claim scores differently across framings, the confidence level is noise, not signal.

---

## Cross-Report Flags

**Reinforces B1 (Report 6):** Both B1 and B2 independently identify trendslop as a named, measurable failure mode requiring an Evaluator detection mechanism. B1 grounds it in the Actionability dimension; B2 grounds it in the Intent Alignment dimension (generic recommendations that apply to any company score below Level 3 on the five-level rubric). These are consistent and mutually reinforcing.

**Reinforces B4 (Report 9):** B2's anti-pattern 5 ("technically correct but strategically misleading") maps directly to what B4 calls the fluency trap. Both reports identify the failure where all individual facts are true but the selection and arrangement of true facts creates an inaccurate overall picture. B4 will likely name the detection mechanism for this (fluency-factuality divergence score); B2 names the conceptual failure pattern (selection bias creating false picture). These should be synthesized into a single Evaluator detection mechanism.

**Potential contradiction with B3 (Report 8):** B2 argues comprehensiveness is harmful past the decision-readiness point; B3's prompt asks about taste and the quality of thought, which may include valuing thoroughness as a signal of analytical seriousness. Watch for tension between B3's potential finding that comprehensive analysis signals rigor (a taste standard) and B2's finding that it actively degrades decision quality.

**Flag for Thread A (orchestration):** The five-level rubric implies the Specification Engine (L0) must specify which level of decision-usefulness is the target for each engagement. A market entry feasibility study targets Level 4; ongoing competitive monitoring may accept Level 3. The L0 task specification format (research-tasks.json) does not currently include a target decision-usefulness level field. This is a gap the Specification Engine design must address.

**Flag for Thread C (deliberation):** B2's finding that "premature consensus degrades forecast quality" (from Tetlock) and the multi-agent implementation pattern (independent research → distinct theses → structured debate → convergence) directly validate the Deliberation Phase design. Specifically, the principle of independent assessment before aggregation matches the plan's isolation of Research Agents (4.1). B2 validates this choice with Tetlock's empirical superforecasting research.

**Flag for META layer:** B2's noise audit recommendation — scoring outputs using multiple independent evaluation passes and adopting the lower score — directly informs how the self-improvement loop should assess Evaluator calibration quality. The META layer needs to track Evaluator noise (divergence between independent passes) as a metric of Evaluator reliability. High divergence means the Evaluator criteria are underspecified, and the Rejection Library should encode what caused the divergence.
