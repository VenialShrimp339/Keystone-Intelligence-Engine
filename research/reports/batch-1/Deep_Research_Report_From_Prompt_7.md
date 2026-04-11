# Five levels of decision-usefulness: a rubric for the Keystone Evaluator

**The core problem in AI-generated consulting research is not accuracy — it is relevance.** An automated system can produce 60,000 words of technically correct analysis that destroys decision quality by overwhelming executives who won't read past page 20. Herbert Simon identified the root cause in 1971: "a wealth of information creates a poverty of attention." The Keystone Evaluator must therefore measure not what the research *contains* but what it *does* to the decision-maker's ability to act. This report synthesizes decision science (Kahneman, Klein, Tetlock), intelligence community tradecraft (Heuer, ICD 203), consulting methodology (Minto, McKinsey), and 2025–2026 executive usage data to produce a five-level rubric with concrete, gaming-resistant indicators for each tier.

The rubric that follows is grounded in a single organizing principle drawn from the Kahneman-Klein 2009 collaboration: **decision-useful analysis must change the decision-maker's mental model of the problem, not merely add information to their existing model.** Klein's Data/Frame sensemaking theory provides the mechanism — analysis can elaborate within an existing frame (Level 3), provide decision-relevant data that reshapes priorities within the frame (Level 4), or trigger a genuine reframing of the problem itself (Level 5). The lower levels represent failures: analysis that corrupts the frame (Level 1) or that is frame-irrelevant despite technical correctness (Level 2).

---

## The academic architecture behind the rubric

Three foundational frameworks converge to define what "decision-useful" means, and each must be encoded into the Evaluator's logic.

**Kahneman's Noise framework** (2021, with Sunstein and Sibony) establishes that unwanted variability in judgment — not just systematic bias — is a primary threat to analytical quality. A 2024 study published in *Scientific Reports* applied noise audits to AI benchmarks and found performance estimate variations of nearly **10%** for humans and **4%+** for ChatGPT on identical tasks, driven by level noise, pattern noise, and occasion noise in the evaluation data itself. For the Keystone Evaluator, this means the rubric must measure *consistency of analytical stance* across equivalent prompts. An agent that rates the same market opportunity as "promising" in one analysis and "risky" in a parallel analysis — without new evidence — is producing noise, not insight. Kahneman's "decision hygiene" protocols (independent assessment before discussion, structured judgment, noise audits) map directly to multi-agent evaluation design: evaluator agents should score independently before any aggregation step.

The posthumous operationalization of Kahneman's System 1/System 2 distinction has accelerated since his death on March 27, 2024. The **SOFAI architecture** (Fabiano et al., *Communications of the ACM*, 2025) implements a metacognitive agent that selects between a fast ML-based solver (System 1) and a slower symbolic reasoning solver (System 2), mirroring how expert judgment shifts between intuitive pattern recognition and deliberate analysis. This architecture validates a key Evaluator principle: **the quality of research output depends on matching analytical mode to problem type**. Analysis that applies System 2 rigor to a straightforward factual question wastes attention; analysis that applies System 1 pattern-matching to a novel strategic dilemma produces confident-sounding but potentially empty conclusions.

**Gary Klein's Recognition-Primed Decision model** explains why executives process consulting deliverables differently from novice analysts. In Klein's original fireground commander studies, **87% of decisions** were made through pattern recognition — experienced decision-makers don't compare options but recognize situations as familiar, simulate outcomes mentally, and act. This has a direct implication for the Evaluator: Level 4 and Level 5 research must connect to the patterns executives already use to make decisions. Research that provides correct information in a framework alien to the decision-maker's mental model will score no higher than Level 3 regardless of analytical quality. Klein's Data/Frame model provides the mechanism: the six sensemaking activities (elaborating, questioning, comparing, preserving, reframing, seeking) describe exactly what research at each quality level triggers in the reader.

**Philip Tetlock's superforecasting methodology** provides the procedural template. His appointment to the Board of Directors of ForecastEx (a CFTC-registered prediction market, announced January 22, 2026) signals that his methods are moving from academia into institutional practice. The multi-agent AI implementation of Tetlock's approach — documented in experiments where AI agents independently research a question, form distinct theses, then engage in structured debate before convergence — has demonstrated that **premature consensus degrades forecast quality**. For the Evaluator, this means outputs that present a single confident conclusion without visible evidence of alternative-hypothesis testing should be penalized. The IC's Analysis of Competing Hypotheses technique, Heuer's signature contribution, operationalizes the same principle: focus on *disproving* rather than *confirming* hypotheses, and the least-disproved hypothesis is the most credible.

---

## What executives actually do with AI analysis in 2026

The rubric must be calibrated against how decision-makers actually consume research, not how analysts imagine they do. The 2025–2026 data reveals a stark paradox that shapes every level of the rubric.

**Deloitte's 2026 Global Human Capital Trends survey** (9,000+ leaders across 89 countries) found that **60% of executives regularly use AI to support decisions** — but only **5%** say they manage AI in decision-making well. The HBR/Bean 15th Annual AI & Data Leadership Executive Benchmark Survey (January 2026, ~110 Fortune 1000 companies) found **97.3%** claim measurable value from AI investments, yet **93.2%** cite cultural challenges and change management — not technology — as the top barrier. MIT Sloan called 2026 a **"level-set year"** with dialed-back expectations, noting that generative AI now sits in Gartner's trough of disillusionment and agentic AI will join it. IMD professor José Parra Moyano captured the structural shift: "When AI takes care of scale and speed, the real bottleneck becomes human judgment — the precision of the questions we ask, the depth with which we interpret model reasoning, and our ability to turn AI-generated ideas into better decisions."

This data has three concrete implications for the Evaluator rubric:

First, **executives don't read past 20 pages**. Research that is comprehensive but unstructured actively harms decision quality. The consulting industry's hard-won insight is that co-created recommendations get executed while "polished decks they've never seen before collect dust." The best deliverables balance confirmatory findings (validating what the client already suspects but couldn't prove) with genuinely new insights — too much confirmation and the client questions why they paid; too much novelty and they feel disoriented.

Second, **AI-generated "trendslop" is a documented failure mode**. HBR research published March 2026 tested seven leading LLMs across strategic decisions and found they overwhelmingly recommend trendy, buzzword-aligned strategies — consistently favoring differentiation over cost leadership, augmentation over automation, long-term over short-term, regardless of context. Across **15,000+ trials**, better prompting could not fix this bias. This is exactly Rosenzweig's Halo Effect applied to AI: the fluent, confident style of LLM output creates a halo that masks analytical emptiness.

Third, the **IMF's June 2025 analysis** (Ajay Agrawal, *Finance & Development*) frames the stakes: "As AI prediction advances, the distribution of judgment will increasingly determine the distribution of wealth and power." The Evaluator is not merely a quality-control tool — it is the mechanism that determines whether the Keystone system produces judgment-augmenting analysis or judgment-replacing noise.

---

## Intelligence community standards as the rubric's structural backbone

The IC's formal analytic standards, codified in **ICD 203** (originally 2007, revised 2015, amended 2022–2023), provide the most battle-tested framework for evaluating analytical quality at scale. ICD 203's nine Analytic Tradecraft Standards map directly to Evaluator criteria, and several are particularly relevant.

**Tradecraft Standard 2** (expressing uncertainties) requires calibrated probability language using a standardized seven-term lexicon ranging from "almost no chance" (1–5%) to "almost certainly" (95–99%), plus separate confidence levels (High/Moderate/Low) reflecting source quality rather than event probability. Sherman Kent's 1964 insight drives this: the word "probable" was interpreted as anywhere from 30% to 75% likelihood by different readers. For the Evaluator, Level 2 ("technically correct but unhelpful") analysis fails this standard by using vague hedging language ("this could go either way," "there are arguments on both sides") that provides no basis for calibrated action.

**Tradecraft Standard 4** (analysis of alternatives) requires systematic evaluation of competing hypotheses — essentially mandating Heuer's ACH at the institutional level. For the Evaluator, this standard separates Level 3 from Level 4: Level 3 analysis presents a conclusion without visible alternative-hypothesis testing, while Level 4 analysis explicitly identifies and tests competing explanations, showing why the chosen interpretation is more consistent with evidence than alternatives.

**Tradecraft Standard 5** (customer relevance and implications) requires that products "add value by addressing prospects, context, threats, or factors affecting opportunities for action." This is the IC's version of the consulting "so what?" test. Analysis that is accurate but fails to address implications for the decision-maker's action space cannot score above Level 3.

The IC's distinction between **estimative intelligence** (forward-looking, probabilistic) and **current intelligence** (situation updates) maps to a key Evaluator calibration: research answering "what is happening?" operates under different quality criteria than research answering "what is likely to happen and what should we do?" The Evaluator must detect which type of question the research agent was addressing and apply appropriate standards. Estimative analysis requires explicit uncertainty quantification; current intelligence requires timeliness and source quality.

Heuer's most potent insight for the Evaluator is this: **"Once an experienced analyst has the minimum information necessary to make an informed judgment, obtaining additional information generally does not improve the accuracy of estimates. Additional information does, however, lead the analyst to become more confident in the judgment, to the point of overconfidence."** This is the theoretical basis for penalizing information overload — more research is not better research past the point of decision-readiness.

---

## The five anti-patterns that define the rubric's failure modes

Each anti-pattern maps to specific rubric levels and provides the Evaluator with concrete detection signals.

**Anti-pattern 1: Comprehensive but decision-irrelevant (Level 2–3).** The system produces exhaustive coverage of a topic without connecting findings to the decision at hand. Detection signal: high information density with low implication density — many facts per paragraph but few sentences containing "therefore," "this means," "the implication is," or equivalent connective reasoning. The Evaluator should compute a ratio of descriptive claims to prescriptive/implicative claims; a ratio above 5:1 signals this anti-pattern.

**Anti-pattern 2: Balanced to the point of uselessness (Level 2).** LLM alignment via RLHF optimizes for being "helpful, harmless, and honest," which produces a structural bias toward presenting both sides so evenhandedly that no actionable conclusion emerges. The CFA Institute's May 2025 analysis found that LLM system prompts bias outputs "toward safe, consensus views and user affirmation." Detection signal: the analysis acknowledges multiple perspectives but fails to assess their relative likelihood, fails to recommend a course of action, or hedges every conclusion with symmetric qualifiers ("on the one hand… on the other hand" without resolution).

**Anti-pattern 3: Style over substance — the Halo Effect for LLMs (Level 1–2).** Rosenzweig documented nine delusions in management research, with the central Halo Effect — where financial performance retroactively colors perception of strategy, culture, and leadership — now replicated in AI outputs. A 2025 PNAS study found LLMs **favor communications produced by other LLMs** over human text, creating a self-reinforcing halo. A 2025 *ScienceDirect* study found LLM-generated personas "replicate and exaggerate human cognitive biases including the Halo Effect, behaving more like caricatures of human cognitive behavior." Detection signal: polished structure and confident tone without corresponding analytical depth — the ratio of hedging language is low (suggesting confidence) but the ratio of specific, verifiable, decision-relevant claims is also low (suggesting empty confidence).

**Anti-pattern 4: Information overload as decision-quality destroyer (Level 2–3).** Federal Reserve research found that a one standard deviation increase in information overload increases the market risk premium by **35 basis points** — information overload literally makes financial decisions worse. Meta-analysis of 31 experiments across 18 studies confirmed that "both information diversity and repetition have adverse impact on decision quality." Detection signal: output length substantially exceeds what is necessary to support the core recommendation; the Evaluator should assess whether removing 50% of the content would change the recommendation — if not, the output is overloaded.

**Anti-pattern 5: Technically correct but strategically misleading (Level 1).** This is the most dangerous failure mode because it passes surface-level accuracy checks. Mechanisms include consensus amplification (training data reflects majority views, systematically underweighting contrarian positions), truncation bias (length caps cut off nuanced contrary evidence), and post-hoc rationalization (LLMs generate explanations that look like reasoning but are pattern-matching). Detection signal: the analysis reaches a conclusion that would be validated by checking individual facts, but the overall framing omits critical context, ignores base rates, or fails to consider the reference class of similar situations. The Evaluator must check not just whether claims are true but whether the *selection and arrangement* of true claims creates an accurate overall picture.

---

## The five-level rubric: concrete criteria for the Keystone Evaluator

### Level 1 — Actively misleading

**Definition:** Output that, if acted upon, would lead to a worse decision than the decision-maker would have reached with no analysis at all. The analysis corrupts the decision-maker's frame rather than informing it.

**Core indicators (all must be checked; any single indicator is sufficient for Level 1 classification):**

- **Factual inversion or critical omission that reverses the correct conclusion.** The analysis states or strongly implies a directional claim (e.g., "the market is growing," "the acquisition target is undervalued") that is contradicted by available evidence, and this claim is material to the recommended action. This is distinct from mere factual error — the error must be *load-bearing* in the analytical structure.

- **Selection bias that creates a false picture.** All individual facts may be verifiable, but the selection and arrangement of facts systematically omits contrary evidence, producing a conclusion that would not survive if the omitted evidence were included. The Evaluator should check: does the analysis acknowledge the strongest counterargument to its conclusion? If the strongest counterargument is absent, the output is potentially Level 1.

- **Base rate neglect in probabilistic claims.** The analysis asserts likelihood of an outcome without reference to the base rate for that class of event. Example: "This acquisition will create significant synergies" without noting that research consistently shows **60–70% of acquisitions destroy value**. The Evaluator should check whether claims about future outcomes reference the statistical base rate for the relevant reference class.

- **Confidence-accuracy mismatch on critical claims.** The analysis expresses high confidence (using language equivalent to "almost certainly" or "very likely" in the IC lexicon — 80%+ implied probability) on claims where available evidence supports only moderate confidence. Per the Kahneman Noise framework, this is a form of systematic bias that is more dangerous than noise because it triggers unwarranted action.

- **Causal claims from correlational evidence without disclosure.** The analysis implies X causes Y based on co-occurrence data without acknowledging the correlation-causation distinction — Rosenzweig's "Delusion of Connecting the Winning Dots."

**Consulting example:** An analysis of a potential market entry concludes "the target market is highly attractive with strong growth fundamentals" based on three years of historical revenue growth in the sector, without mentioning that (a) growth has decelerated in each of the last four quarters, (b) two major competitors announced entry in the past six months, and (c) the regulatory environment is shifting unfavorably. Each stated fact is true; the omission of contrary facts makes the overall analysis actively misleading.

**Gaming resistance:** Level 1 cannot be detected by keyword matching or structural analysis alone. The Evaluator must assess whether the analysis *as a whole* creates an accurate picture by checking for the presence of strongest-counterargument acknowledgment, base rate reference, and balanced evidence selection. An agent cannot avoid Level 1 simply by including hedging language — the hedging must address the *specific* risks and contrary evidence that are most material.

---

### Level 2 — Technically correct but unhelpful

**Definition:** Output that contains no material factual errors but fails to connect information to the decision at hand. The analysis adds to the decision-maker's information load without improving their ability to act. This is the "data without frame" failure mode in Klein's sensemaking model.

**Core indicators (two or more indicate Level 2):**

- **High description-to-implication ratio.** The output presents facts, data, and observations without translating them into implications for the decision. The Evaluator should assess: for each major section, does the analysis answer "so what does this mean for the decision?" If more than 60% of sections lack implicative conclusions, the output is Level 2.

- **Generic recommendations not tailored to the specific decision context.** Recommendations like "the company should invest in innovation," "management should monitor competitive dynamics," or "a phased approach is recommended" that could apply to virtually any company in any situation. The Evaluator should check: could these recommendations be copy-pasted into a different client's analysis without modification? If yes, Level 2.

- **Symmetric hedging without resolution.** The analysis presents competing perspectives ("some analysts believe X while others believe Y") without assessing relative likelihood, evidentiary support, or which perspective is more relevant to the decision. This is the "balanced to uselessness" anti-pattern. The Evaluator should check: does the analysis take a position, and does it explain why that position is better supported than alternatives?

- **Failure to prioritize.** All findings are presented with equal weight, without identifying which are most material to the decision. The Evaluator should check: does the output identify the **2–3 factors that matter most** and explain why they matter more than the others? If all factors are presented as equally important, the output lacks the prioritization that makes analysis decision-useful.

- **Absence of uncertainty quantification.** The analysis discusses risks and uncertainties in purely qualitative terms without any attempt to calibrate likelihood or magnitude. Per ICD 203 Tradecraft Standard 2, useful analysis must express uncertainty in terms that allow the decision-maker to calibrate their response. Language like "there is some risk" or "this could be challenging" provides no basis for action.

- **Structural completeness masking analytical emptiness.** The output follows a professional-looking structure (executive summary, market analysis, competitive landscape, recommendations) but the content within each section is shallow, derivative, or simply restates publicly available information without synthesis. This is the Halo Effect applied to document structure — the form suggests rigor that the content does not deliver.

**Consulting example:** An M&A target assessment provides a thorough overview of the target's industry, a correct summary of its financial statements, a balanced discussion of market trends, and a list of "key considerations" — but never takes a position on whether the acquisition should proceed, at what price, or under what conditions. A board member reading this learns nothing they couldn't have found in a Bloomberg terminal search.

**Gaming resistance:** The Evaluator must distinguish between outputs that *contain* implications and outputs that *foreground* implications. An agent that appends a generic "implications" paragraph to an otherwise descriptive analysis should not score above Level 2. The test is whether the implications are specific enough to falsify — could someone disagree with the stated implication based on the evidence presented? If the implications are so vague that disagreement is impossible, they are Level 2.

---

### Level 3 — Informative but doesn't change the decision

**Definition:** Output that provides genuine analytical value — correct facts, reasonable synthesis, legitimate insights — but tells the decision-maker things they already knew or suspected, or provides information that, while interesting, does not alter the optimal course of action. In Klein's framework, this analysis *elaborates within the existing frame* without questioning or reframing it.

**Core indicators (the key distinguishing feature from Level 4 is that removal of this analysis would not change the decision):**

- **Confirmatory analysis without new signal.** The research validates what the decision-maker's team already believed, using different or better sources but reaching the same conclusion. While this has some value (reducing uncertainty around an existing belief), it does not shift the decision. The Evaluator should assess: does this analysis introduce any finding that would surprise an informed decision-maker? If the answer is no, the ceiling is Level 3.

- **Correct identification of relevant factors without ranking or weighting.** The analysis identifies the right variables to consider but does not assess their relative importance for the specific decision. It answers "what factors are relevant?" but not "which factors matter most here and why?"

- **Analysis of the right question at insufficient depth.** The analysis is pointed at the right decision but stays at a level of generality that doesn't provide actionable specificity. Example: "Customer acquisition costs in this market are high" (Level 3) vs. "Customer acquisition costs average $340 per customer in this market, 2.3x the company's current CAC, requiring 18-month payback periods that conflict with the company's 12-month ROI threshold" (Level 4).

- **Sound methodology, obvious conclusion.** The analysis applies rigorous analytical technique to arrive at a conclusion that an experienced executive would have reached through pattern recognition (Klein's RPD). The analysis is not wrong — but it consumes attention without adding decision value proportional to that consumption.

- **Passes the "so what?" test at the section level but fails it at the document level.** Individual sections contain relevant insights, but the overall document does not build to a coherent, prioritized recommendation that would change how the decision-maker allocates resources, timing, or strategic direction.

- **Single-hypothesis analysis with adequate evidence.** The analysis tests and supports one hypothesis but does not systematically evaluate alternatives (failing ICD 203 Tradecraft Standard 4). This means even if the conclusion is correct, the decision-maker cannot assess how robust it is — they don't know what the analysis would have concluded if a different hypothesis had been explored.

**Consulting example:** A market entry analysis for a consumer electronics company correctly identifies that the Southeast Asian market is growing at 12% CAGR, that the middle class is expanding, that smartphone penetration is increasing, and that several competitors are already present. The analysis is well-sourced and accurately synthesized. But the company's strategy team had already identified Southeast Asia as a priority market — what they needed was analysis of *which specific country* to enter first, *what entry mode* minimizes risk given regulatory constraints, and *what the competitive response* is likely to be. The analysis answers the wrong question at the right level of quality.

**Gaming resistance:** The critical test for Level 3 vs. Level 4 is the **counterfactual deletion test**: if this analysis were removed from the decision-maker's information set, would the decision change? The Evaluator should assess whether the analysis introduces at least one finding that is both (a) non-obvious to an informed decision-maker and (b) material to the decision's direction, timing, scope, or risk profile. Agents cannot game this by simply asserting novelty ("surprisingly," "counter-intuitively") — the Evaluator must assess whether the underlying finding is genuinely novel relative to the baseline knowledge assumed for the decision context.

---

### Level 4 — Directly decision-relevant

**Definition:** Output that provides specific, actionable analysis that materially improves the decision-maker's ability to choose between options, calibrate risks, allocate resources, or set timing. In Klein's framework, this analysis provides data that causes *questioning* of existing assumptions and *comparison* between frames, though the fundamental decision frame remains intact. The decision-maker's choice improves but the *nature* of the choice does not change.

**Core indicators (three or more indicate Level 4):**

- **Specific, quantified findings that differentiate between options.** The analysis provides data points that create meaningful separation between alternatives. Not "Option A has risks and Option B has risks" (Level 2) or "Option A is risky because of market volatility" (Level 3) but "Option A requires $14M upfront with 65% probability of 3x return within 5 years based on the reference class of 23 comparable market entries; Option B requires $6M with 80% probability of 1.5x return based on 41 comparable licensing deals" (Level 4).

- **Explicit alternative-hypothesis testing.** The analysis identifies at least two competing interpretations of the key evidence, systematically evaluates which is better supported, and explains the sensitivity of the conclusion to the choice between hypotheses. This satisfies ICD 203 Tradecraft Standard 4 and implements Heuer's ACH principle.

- **Calibrated uncertainty expression.** Probabilities or likelihood ranges are attached to key claims, confidence levels are distinguished from probability levels (per IC standards), and the analysis identifies what evidence would change the assessment. The seven-term IC probability lexicon (or numerical equivalents) provides the standard.

- **Identification of linchpin assumptions.** The analysis explicitly names the 1–3 assumptions on which the conclusion most depends and assesses their validity. Per Heuer's Key Assumptions Check, these are assumptions that, if wrong, would reverse the conclusion. The Evaluator should check: does the analysis identify assumptions? Are those assumptions the ones that actually matter? (Agents can game this by identifying trivial assumptions.)

- **Decision-specific recommendations with conditions.** Recommendations specify not just *what* to do but *under what conditions* to do it, *when* to act, and *what signals should trigger reconsideration*. This implements the Heath brothers' "tripwire" concept from WRAP: predetermined conditions that trigger a revisitation of the decision.

- **Outside-view calibration.** The analysis provides a reference class or base rate for the type of decision being made, per Tetlock's first commandment of superforecasting. Example: "Of 47 comparable market entries by companies of similar size and market position, 28 (60%) achieved profitability within 3 years, but only 12 (26%) exceeded the projected ROI provided in their initial business cases."

- **Effective signal-to-noise ratio.** Every major section contributes directly to the decision recommendation. Removing any section would weaken the analytical foundation. There is no "padding" — no sections included for comprehensiveness that do not serve the decision.

**Consulting example:** A competitive response analysis for a pharmaceutical company facing generic entry identifies that (a) the generic competitor's supply chain depends on a single API manufacturer in India currently under FDA warning letter (specific, verifiable, non-obvious), (b) historical analysis of 34 comparable generic entry situations shows the branded product retains 45–55% market share at month 24 when supported by authorized generic launch within 60 days (base-rate calibrated), (c) the optimal pricing strategy is a 25% price reduction within 30 days of generic launch based on elasticity modeling from three analogous situations, and (d) the conclusion is sensitive to the assumption that no second generic entrant files within 12 months — if a second filing occurs, the recommended strategy shifts to an authorized generic partnership. This analysis directly shapes the decision on pricing, timing, and contingency planning.

**Gaming resistance:** Level 4 requires *integration* of multiple analytical elements (quantification + alternative hypotheses + uncertainty calibration + assumption identification + conditional recommendations). An agent cannot score Level 4 by including any single element superficially. The Evaluator should check that these elements are *mutually referencing* — that the uncertainty quantification reflects the alternative hypotheses, that the conditional recommendations respond to the linchpin assumptions, and that the base-rate data informs the probability estimates. Isolated checklist-style inclusion of these elements without integration should score Level 3 at best.

---

### Level 5 — Changes the framing of the decision itself

**Definition:** Output that causes the decision-maker to reconceptualize the problem — to see the decision differently, to identify options not previously considered, or to recognize that the question being asked is not the right question. In Klein's framework, this is *reframing*: the analysis triggers rejection of the initial frame and adoption of a fundamentally different frame that better accounts for the evidence. This is the rarest and most valuable form of analysis. It is what separates the $500K McKinsey engagement from the $50K boutique at the analytical level.

**Core indicators (the key distinguishing feature from Level 4 is that the analysis changes *what decision is being made*, not just *which option is chosen*):**

- **Identification of options not previously in the decision-maker's consideration set.** McKinsey's corporate spin-off case study exemplifies this: the CEO framed the decision as "spin off two underperforming units or keep them." Red and blue team analysis revealed a third option — spin off one unit and pursue a joint venture for the other — that no one had considered. The Evaluator should check: does the analysis introduce at least one option, framing, or interpretation that is demonstrably absent from the decision context as originally stated?

- **Reframing the question itself.** The analysis demonstrates that the question being asked contains a flawed assumption or misidentifies the real decision. Example: the client asks "Should we enter Market X?" and the analysis shows that the real decision is "Should we build the capability to serve Customer Segment Y, which happens to be concentrated in Market X but is also growing in Markets Z and W?" The Evaluator should check: does the analysis explicitly challenge the premise of the original question?

- **Surfacing of a non-obvious constraint or enabler that restructures the option space.** The analysis identifies a factor — regulatory, technological, competitive, organizational — that fundamentally changes what is possible or advisable, and that was not part of the decision-maker's prior mental model. This is not merely new information (which would be Level 4) but new information that *changes the structure of the problem*.

- **Contrarian conclusion supported by stronger evidence than the consensus.** The analysis reaches a conclusion that contradicts the prevailing view within the client organization (or the market consensus) and provides evidence sufficient to justify the contrarian position. Per McKinsey research, "for big-bet decisions, high-quality debate led to decisions that were **2.3 times more likely to be successful**." Level 5 analysis creates this debate. The Evaluator should check: does the analysis identify and explain where and why it disagrees with the prevailing view, and is the evidence for the contrarian position specifically stronger than the evidence for the consensus?

- **Temporal reframing — identifying that the decision window is different from what was assumed.** The analysis shows that the decision must be made sooner (an opportunity is closing), later (conditions are not yet right), or in a different sequence (a prerequisite decision must be made first) than the decision-maker assumed.

- **Application of the "outside view" that reveals the decision-maker's "inside view" is miscalibrated.** Tetlock's methodology prioritizes base rates over narrative. Level 5 analysis provides a reference class that shows the decision-maker's expectations are systematically miscalibrated — for example, showing that companies in comparable situations succeed at 15% rates rather than the 60% the management team assumed.

- **Integration of evidence across domains that reveals a pattern invisible from within any single domain.** The analysis connects signals from technology, regulation, competitive dynamics, and customer behavior to identify an emergent pattern that would not be visible to a domain specialist. This is the Tetlock "dragonfly eye" — many facets combining to produce vision that no single facet provides.

**Consulting example:** A private equity firm considering acquisition of a regional hospital chain asks for a standard due diligence analysis focused on financial performance, regulatory risk, and market position. The analysis provides all of this (Level 4 content) but then demonstrates that (a) the hospital chain's geographic footprint overlaps with three of the fastest-growing Medicare Advantage plan markets, (b) the real asset is not the hospitals themselves but the referral network and physician relationships that could be leveraged into a value-based care platform, (c) the comparable reference class is not hospital acquisitions (which have 40% failure rates) but healthcare platform plays (which have different risk profiles and exit multiples), and (d) the optimal strategy is therefore not a traditional hospital rollup but a platform acquisition with different operational requirements, investment horizons, and exit strategies. The PE firm entered the process asking "Should we buy this hospital chain at $X valuation?" and exits the analysis asking "Should we build a value-based care platform using this chain as the anchor asset?"

**Gaming resistance:** Level 5 is the hardest to achieve and the hardest to game. The Evaluator must distinguish between genuine reframing and *superficial contrarianism* — analysis that claims to challenge assumptions but actually just asserts the opposite of the obvious without evidentiary support. True Level 5 analysis meets ALL Level 4 criteria (quantified, uncertainty-calibrated, alternative-hypothesis-tested, assumption-identified) AND provides reframing that is supported by evidence at least as strong as the evidence supporting the original frame. The Evaluator should apply a **two-step test**: (1) Does the analysis meet Level 4 criteria? If not, it cannot be Level 5 regardless of how bold its claims are. (2) Does the analysis change the structure of the decision (options, question, constraints, timeline) rather than merely the answer to the existing decision?

---

## Making the rubric gaming-resistant: structural safeguards

The five levels above provide semantic criteria, but semantic criteria alone are gameable. Six structural safeguards make the rubric resistant to agents that optimize for scoring rather than decision quality.

**Safeguard 1: The counterfactual deletion test.** For any analysis scoring Level 3 or above, the Evaluator should assess: if this specific output were removed from the decision-maker's information set, would the optimal decision change? If removal changes nothing, the ceiling is Level 3. If removal changes the *choice* between options, the floor is Level 4. If removal changes *what options are considered*, the floor is Level 5. This test cannot be gamed by including more information — only by including *decision-altering* information.

**Safeguard 2: The specificity-to-context ratio.** The Evaluator should compute the proportion of claims, recommendations, and findings that are specific to the decision context vs. generic enough to apply to any similar decision. Level 4+ requires that **over 70%** of core analytical claims reference specific entities, numbers, dates, or conditions unique to the decision at hand. Generic claims like "the market is competitive" or "execution risk exists" cannot contribute to a score above Level 3.

**Safeguard 3: The integration test (anti-checklist).** Agents may attempt to game the rubric by mechanically including required elements (alternative hypotheses, uncertainty quantification, assumption identification) without integrating them. The Evaluator should verify that these elements *reference each other*: do the stated uncertainties connect to the identified alternative hypotheses? Do the conditional recommendations respond to the linchpin assumptions? Are the probability estimates informed by the base-rate data? Isolated, unconnected analytical elements indicate checklist-gaming rather than genuine analytical integration.

**Safeguard 4: Strongest-counterargument acknowledgment.** For any analysis with a directional conclusion, the Evaluator should independently identify the strongest counterargument (using a separate analytical pass) and check whether the primary analysis addresses it. If the strongest counterargument is absent, the analysis cannot score above Level 3 and may score Level 1 if the omission is material enough to reverse the conclusion.

**Safeguard 5: Prediction specificity and falsifiability.** Level 4+ analysis must contain at least one claim specific enough to be proven wrong. Predictions, forecasts, and conditional statements must be stated in terms that allow future evaluation — with timeframes, quantified thresholds, and specified conditions. Analysis consisting entirely of unfalsifiable claims ("this could go either way," "results will depend on execution") cannot score above Level 2.

**Safeguard 6: Noise audit via parallel evaluation.** Per Kahneman's decision hygiene framework, the Evaluator should score outputs using multiple independent evaluation passes (analogous to the IC's multi-evaluator approach and the Deloitte finding that only 5% of organizations manage AI decision-support well). If independent evaluation passes produce widely divergent scores, the scoring criteria are insufficiently specified, and the lower score should be adopted as a conservative default.

---

## Mapping academic frameworks to evaluator logic

The rubric's theoretical coherence is grounded in the convergence of five frameworks, each contributing distinct evaluable dimensions:

| Framework | Key concept | Evaluator application | Primary level distinction |
|---|---|---|---|
| **Kahneman (Noise)** | Unwanted judgment variability | Consistency audit across parallel outputs; calibrated uncertainty expression | Level 2 vs. Level 4 (vague hedging vs. calibrated probability) |
| **Klein (Data/Frame)** | Six sensemaking activities | Does output elaborate, question, compare, or reframe? | Level 3 (elaborate) vs. Level 4 (question/compare) vs. Level 5 (reframe) |
| **Tetlock (Superforecasting)** | Base rates, reference classes, independent perspectives then debate | Outside-view calibration; alternative-hypothesis testing; integration without premature consensus | Level 3 (inside view only) vs. Level 4 (outside view included) |
| **Rosenzweig (Halo Effect)** | Confident style masking analytical emptiness | Style-substance divergence detection; confidence-evidence alignment | Level 1–2 (high confidence, low evidence) vs. Level 4 (aligned) |
| **Heath (SUCCESs/WRAP)** | Sticky communication; structured decision process | Is the finding simple, unexpected, concrete, credible? Are options widened, assumptions tested? | Level 2 (abstract, expected) vs. Level 4 (concrete, tested) vs. Level 5 (options widened) |

The Heath brothers' finding from *Decisive* deserves special emphasis in the Evaluator design: **"Process mattered more than analysis — by a factor of six."** A good decision process leads to better analysis, but superb analysis is useless unless the decision process gives it a fair hearing. This means the Evaluator should assess not just analytical quality but whether the analysis is *structured to be heard* — leading with the conclusion (Minto's Pyramid Principle), using concrete rather than abstract language (Heath's SUCCESs), and framing findings around the decision-maker's action space rather than the analyst's research process.

---

## Conclusion: judgment is the scarce resource

The rubric presented here is designed around a single unifying insight confirmed by every source examined: **the bottleneck in AI-augmented decision-making is not information but judgment** — specifically, the judgment to determine what information matters for the decision at hand, to calibrate confidence appropriately, to consider alternatives systematically, and to recognize when the question itself needs changing.

Three novel principles should guide the Evaluator's implementation. First, **decision-usefulness is not monotonically increasing with comprehensiveness**. Past the point of decision-readiness, additional information actively degrades decision quality by consuming the scarce resource of executive attention. The Evaluator should penalize unnecessary length and breadth that do not serve the decision. Second, **the highest-value analytical move is often subtraction, not addition** — identifying which of the decision-maker's existing beliefs are wrong is more valuable than confirming which are right. Level 5 analysis frequently works by *removing* a false constraint or *eliminating* a previously assumed option rather than by adding new information. Third, **gaming resistance requires evaluating the relationships between analytical elements, not just their presence**. An integrated analysis where uncertainty quantification, alternative hypotheses, assumption identification, and conditional recommendations all reference and reinforce each other is qualitatively different from a checklist that includes all four elements in isolation — and the Evaluator must be designed to detect this difference.

The Gartner projection that **50% of business decisions** will be augmented or automated by agents by 2027 makes this rubric not merely a quality-control tool but a governance mechanism. The Keystone Evaluator, armed with these five levels and six gaming-resistance safeguards, can distinguish between AI research that makes executives smarter and AI research that makes them more confident about being wrong.