# Report 6: B1 — What Senior Consulting Partners Actually Value

## Top Findings

### Finding 1: The Eight Rubric Dimensions Are Fully Validated Against External Standards
The existing eight-dimension rubric in CAPSTONE-PLAN-v2.md Section 5.3 maps directly and completely to three independently developed quality frameworks: consulting practitioner standards (McKinsey, BCG), intelligence community analytical tradecraft (ICD 203), and the empirical BCG/Harvard study of 758 consultants. This is not coincidental alignment — these frameworks converge because they all derive from the same underlying problem of communicating analysis to a decision-maker who will act on it. The rubric needs no structural overhaul, only weight refinement and explicit pass/fail criteria per dimension.

**Layer affected:** L4 (Evaluator)
**Build implication:** Treat the rubric as architecturally validated. Invest in encoding the concrete pass/fail criteria documented in this report rather than redesigning the rubric structure. The specific criteria (e.g., "hypothesis stated in first 10% of content," "answer-first structure required") are now known and encodable.
**Evidence quality:** Verified — ICD 203 is a US government directive; BCG/Harvard study is a pre-registered RCT with 758 participants, forthcoming in Organization Science; Pyramid Principle is documented at mckinsey.com; Deloitte incidents documented by AP, Fortune, The Guardian.

---

### Finding 2: "Automatic Fail" Triggers Belong in the Architecture, Not the Rubric
The Deloitte Australia incident (AU$440,000 report, July 2025 — fabricated academic references, non-existent court cases, misattributed quotes) and the second Deloitte Canada incident (CA$1.6M healthcare report, November 2025, fabricated citations) establish that source fabrication is not a rubric dimension to be scored — it is a binary gate that nullifies the entire deliverable. The report recommends "automatic fail for entire deliverable" on any fabricated, non-existent, or misattributed source. This is distinct from the Source Quality dimension (which scores source diversity and reliability) — it is a pre-rubric check.

**Layer affected:** L4 (Evaluator), L1 (Research Agents)
**Build implication:** Before running the eight-dimension rubric, run a citation verification gate. Any fabricated source causes immediate rejection without scoring. This is structural enforcement, not dimensional scoring. The Rejection Library's first entry should be: "Fabricated citation = automatic full rejection regardless of other dimensions."
**Evidence quality:** Verified — Both Deloitte incidents are documented by multiple major news outlets and government agency records.

---

### Finding 3: The Intelligence Community's ICD 203 Provides Ready-to-Encode Quality Criteria
Five structured analytic techniques from CIA tradecraft translate directly into multi-agent pipeline components without modification: Analysis of Competing Hypotheses (ACH) as a devil's advocate agent, Key Assumptions Check (KAC) as a pre-flight verification agent, Red Team Analysis as an adversarial review agent, Pre-Mortem Analysis as a "what if wrong" agent, and Structured Self-Critique as a meta-evaluator across all eight dimensions. The ICD 203 Words of Estimative Probability table (seven-term lexicon with defined numerical ranges) provides the required vocabulary for calibrated uncertainty expression.

**Layer affected:** L1.5 (Deliberation), L4 (Evaluator)
**Build implication:** ACH, KAC, and Pre-Mortem map naturally to Deliberation Phase agent roles. These are not optional enrichments — ICD 203 makes them mandatory for any analysis making causal claims. Build them as required Deliberation agents, not optional add-ons.
**Evidence quality:** Verified — ICD 203 is an official US government directive; CIA Tradecraft Primer is a published government document; KAC and Pre-Mortem are documented CIA methods.

---

### Finding 4: "Trendslop" Is Now an Empirically Documented, Measurable Failure Mode
The HBR study (March 2026, Romasanta/Thomas/Levina at Esade, University of Sydney, NYU Stern) tested seven LLMs across 15,000+ strategic decision trials and found all LLMs consistently default to trendy, buzzword-aligned strategies — differentiating over cost leadership, augmentation over automation, long-term over short-term — regardless of context. The report calls this "trendslop." Critically, better prompting could not fix this bias. It is a structural property of RLHF-trained models that must be detected at the evaluation layer.

**Layer affected:** L4 (Evaluator — Actionability dimension)
**Build implication:** Add a "trendslop detection" check to the Actionability dimension. The detection signal is: could these recommendations be copy-pasted into a different client's analysis without modification? If yes, automatic point deduction. Also adds a Rejection Library entry: "Generic recommendations applicable to multiple companies without modification = Actionability failure."
**Evidence quality:** Verified — named academic researchers, major university affiliations, 15,000+ trials.

---

### Finding 5: The 80/20 Quality Partition Creates a Concrete Build Mandate
The report explicitly partitions quality assessment into 80% pattern-matching (structural checks, source verification, precision calibration, completeness coverage) that can be automated, and 20% genuine judgment (strategic insight quality, client-specific relevance, creative value) requiring human review. This directly maps to the Verifiability-Tier Classification in Section 5.7 of CAPSTONE-PLAN-v2.md. The 80% is machine-checkable or expert-checkable; the 20% is judgment-dependent. This is not an estimate — it is the explicit finding of every practitioner and academic source in this report.

**Layer affected:** L4 (Evaluator), META (self-improvement)
**Build implication:** The Evaluator should explicitly route outputs: automated checks first (structural, source, precision) → LLM rubric scoring second → flag judgment-dependent items for human review. This partition determines what can be built now vs. what requires calibration against Keystone deliverables.
**Evidence quality:** Credible — consistent across five-plus independent practitioner and academic sources; the specific 80/20 partition is asserted, not measured, but aligned with practitioner consensus.

---

## Tool/Framework Verdicts

### Admiralty Code (NATO two-axis source evaluation system)
**Name/maturity:** NATO standard, decades-old, actively used by intelligence agencies and military organizations. Two axes: source reliability (A-F) and information credibility (1-6), scored independently.
**Verdict: BUILD**
Implement as the source evaluation component of the Source Quality dimension; the two-axis independence (source vs. information) prevents the common error of treating a reliable source's unverified claim as verified.

### ICD 203 (US Intelligence Community Directive 203)
**Name/maturity:** Official US government directive, revised 2022-2023. Nine analytical standards with specific, encodable criteria.
**Verdict: INTEGRATE**
Directly maps to six of eight rubric dimensions; the Words of Estimative Probability table, Tradecraft Standards 2 (uncertainty), 4 (alternatives), and 5 (relevance) are encodable as specific pass/fail criteria without modification.

### Analysis of Competing Hypotheses (ACH)
**Name/maturity:** Developed by Richards Heuer (CIA), documented in "Psychology of Intelligence Analysis" (1999), standard in intelligence community.
**Verdict: BUILD**
Map to a dedicated Deliberation Phase agent that generates and evaluates alternative hypotheses for any deliverable making causal claims; this is a Deliberation component that feeds findings back to the Evaluator for verification.

### Key Assumptions Check (KAC)
**Name/maturity:** CIA four-step method, documented in "Structured Analytic Techniques" (Heuer and Pherson, 3rd edition). Standard IC practice.
**Verdict: BUILD**
Implement as a pre-output verification agent that extracts all unstated assumptions and flags uncertain ones; this should run before the Evaluator scores the Intellectual Honesty dimension.

### Pre-Mortem Analysis (Gary Klein)
**Name/maturity:** Developed by cognitive psychologist Gary Klein, widely adopted in decision research and practice.
**Verdict: BUILD**
Implement as a "what if wrong" agent that runs after draft generation; findings feed directly into Intellectual Honesty and Quantitative Rigor scoring.

### Pyramid Principle (Barbara Minto / McKinsey)
**Name/maturity:** Developed 1963, documented at mckinsey.com, standard MBB communication framework.
**Verdict: INTEGRATE**
Encode the answer-first rule, action title test, and storyline test as structural pass/fail criteria for the Narrative Coherence dimension; these are machine-checkable (does recommendation appear in first 10% of content? do section headers form a coherent argument?).

### Victor Cheng Consulting Frameworks
**Name/maturity:** Published frameworks (Business Situation Framework, etc.); now considered outdated by active MBB practitioners on PrepLounge.
**Verdict: LEARN**
Steal the meta-skill of structured decomposition; explicitly do not implement his specific frameworks as analytical templates since current practitioners call them "completely outdated and useless for many cases."

### BCG/Harvard Study (Dell'Acqua et al., HBS Working Paper 24-013)
**Name/maturity:** Pre-registered RCT, 758 BCG consultants, 18 tasks. Forthcoming in Organization Science.
**Verdict: INTEGRATE**
Use the "jagged frontier" finding to calibrate when quantitative AI output needs mandatory human verification (inside-frontier: market sizing, benchmarking, trend analysis; outside-frontier: cross-modal integrative analysis); this directly informs the Verifiability-Tier Classification.

---

## Contradictions with CAPSTONE-PLAN-v2.md

### Contradiction 1: Completeness dimension needs weight reduction
**Plan says:** Completeness is weighted at 10%, same as Source Quality and Narrative Coherence.
**Evidence shows:** "Completeness in consulting means covering the decision-relevant territory, not covering everything." Excess completeness produces boiling-the-ocean failures. The 80/20 principle is cited throughout as a core value — completeness of decision-relevant coverage, not exhaustive coverage.
**Resolution:** Follow the evidence. B3 (Report 8) will recommend reducing Completeness from 10% to 8% and redirecting that weight to new dimensions. The plan's definition of completeness is already correct ("absence detection: what perspectives or data are systematically missing?") but the weight is calibrated too high given the risk of rewarding comprehensiveness over relevance.

### Contradiction 2: False precision framing is backward in the rubric
**Plan says:** Quantitative Rigor (15%) asks "Are claims supported by data? Uncertainties quantified?"
**Evidence shows:** The bigger sin is false precision — "$4.237B when the methodology only supports roughly $4–5B." The rubric should explicitly penalize over-precision as a quality failure, not just reward uncertainty quantification.
**Resolution:** Follow the evidence. Add a "precision calibration" pass/fail criterion to Quantitative Rigor: numbers must be rounded to reflect actual methodology precision, and false precision is a scoring failure, not a neutral presentation choice.

### Contradiction 3: Plan doesn't specify pre-rubric gates
**Plan says:** Evaluator runs the eight-dimension rubric.
**Evidence shows:** Source fabrication should be a binary pre-rubric gate, not a scored dimension. Scoring a deliverable with fabricated citations on eight dimensions misallocates evaluation resources and implies the deliverable has partial merit.
**Resolution:** Follow the evidence. Add a verification layer before rubric scoring: citation existence check and source fabrication detection. Any automatic-fail trigger short-circuits rubric scoring entirely.

---

## Cross-Report Flags

**Flag for B2 (Report 7):** The five-level decision-usefulness rubric requested in Prompt 7 is closely related to the Intent Alignment and Actionability dimensions. The pass/fail criteria here (especially for trendslop detection and 80/20 prioritization) should be integrated with whatever level definitions B2 produces. Watch for tension between "covering decision-relevant territory" (completeness standard) and "information overload reduces decision quality" (the anti-comprehensive finding B2 will likely develop).

**Flag for B3 (Report 8):** Rubric weight modifications suggested here (especially reducing Completeness) need to be coordinated with B3's findings on taste decomposition. B3 will likely add new dimensions (based on the Prompt 8 research questions); the total must sum to 100%.

**Flag for B4 (Report 9):** The "automatic fail" trigger for fabricated citations and the detection architecture for trendslop both require detection infrastructure described in B4's taxonomy of AI failure modes. Specifically, the citation verification gate maps to B4's Category 1 failure mode (professional-grade fabrication at scale, Deloitte incident). These findings should reinforce each other.

**Flag for Thread A:** The BCG/Harvard "jagged frontier" finding that AI performs 19 percentage points worse on outside-frontier tasks has direct implications for how the Specification Engine (L0) should classify tasks. Before dispatching research agents, the system needs to identify whether each task is inside or outside the AI capability frontier. B1 names this classification requirement; Thread A reports likely describe the orchestration mechanisms for enforcing it.

**Flag for Thread C (likely):** The McKinsey Lilli statistics (75%+ employee usage, 500,000+ prompts/month, blind scoring on 5-point scale for accuracy, content richness, and distinctiveness) are the closest real-world analogue to what the Keystone system is building. Lilli's evaluation design (blind scoring, three-dimension rubric) may contradict or validate design choices in the plan. Thread C reports on Specification-Driven Development or Report Generation will likely encounter these numbers.
