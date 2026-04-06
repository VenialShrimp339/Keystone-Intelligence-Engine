# Concrete quality criteria for an AI consulting evaluator rubric

**Senior consulting partners judge deliverables on a single axis: does this advance a client decision or waste their time?** Every quality standard that follows derives from this principle. Drawing on practitioner testimony from MBB and Big Four forums, intelligence community analytical tradecraft (ICD 203), the BCG/Harvard field experiment with 758 consultants, the Deloitte Australia fabrication scandal, and the emerging 2026 discourse on AI quality gaps, this report translates what partners actually expect into concrete, encodable pass/fail criteria across all eight evaluation dimensions.

The evidence converges on a uncomfortable truth: the most common AI failure modes — fabricated citations, "trendslop" recommendations, false precision, missing the "so what" — are the exact same failures that get junior analyst work sent back for rework. The Keystone evaluator rubric must encode the judgment that partners apply instinctively, making it explicit enough for an automated system to replicate.

---

## What partners actually reject and why it maps to your rubric

The practitioner evidence reveals **six recurring failure modes** that account for the vast majority of deliverable rejections. Each maps directly to one or more evaluation dimensions:

**Failure 1: Missing the "so what."** A former McKinsey consultant on Wall Street Oasis stated bluntly: "Any manager/partner, upon seeing a data slide would immediately ask: 'What is the so-what? If there is none, let's get rid of the slide or put it into backup.'" The Working With McKinsey blog (by a verified ex-McKinsey practitioner) specifies every page needs three elements: a headline capturing attention, content/exhibits supporting it, and a key takeaway. A useful "so what" is **quantified, comparative, implication-bearing, and specific to the client** — e.g., "Top 20% of customers generate 65% of gross margin, concentrated in the enterprise segment." A generic "so what" like "the market is competitive" is functionally invisible to a partner. This failure maps to **Analytical Depth** and **Actionability**.

**Failure 2: False precision.** Strategy consultant Casey Ma (Yale MBA) captures the standard: "A client agrees to enter a market if opportunity exceeds $100M. Consultant determines it's $200–300M in four weeks. Spending two more weeks to narrow to $227.1M versus $281.5M is a big mistake — going from 'mostly right' to 'precisely wrong.'" Partners expect **directionally correct** answers within **±20% margin of error**, not scientific exactitude. This maps to **Quantitative Rigor** — and critically, rigor means knowing when to stop refining.

**Failure 3: Boiling the ocean.** The Working With McKinsey blog identifies this as "the most common example: trying to analyze too much data." A practitioner on LinkedIn (Gorka K. Briones, former management consultant) observed: "Very often you can find hard-working junior consultants that, after two weeks working on a benchmark, do not really know what was the question they were trying to answer." The 80/20 rule applies aggressively: focus on the 20% of analyses that prove 80% of the answer. This maps to **Intent Alignment** and **Completeness** — completeness means covering what matters, not covering everything.

**Failure 4: Generic frameworks applied without adaptation.** Current MBB coaches on PrepLounge are explicit: "Victor Cheng's Business Situation Framework — company-client-competition-product — is completely outdated and useless for many cases." The meta-skill of structured decomposition is valuable; the specific frameworks are not. Partners immediately spot when an analyst has applied a textbook framework rather than building a custom issue tree from the problem's specific structure. This maps to **Analytical Depth**.

**Failure 5: Conclusions disconnected from evidence.** What partners call the "logic chain" — every recommendation must trace back through supporting arguments to specific data. The McKinsey standard, per Ethan Rasiel's *The McKinsey Way*, is **"proving and double-proving every recommendation."** A WSO commenter captured the consequence of the opposite: "Client loses trust when data has not been verified." This maps to **Narrative Coherence** and **Intellectual Honesty**.

**Failure 6: Fabricated or unverified sources.** The Deloitte Australia incident (July 2025) is now the canonical case: a **AU$440,000 government report** contained roughly 20 errors including 12 references to a fabricated academic book, two citations of a non-existent Swedish professor's report, a fabricated quote attributed to a Federal Court judge with their name misspelled, and incorrect references to court decisions. Azure OpenAI GPT-4o was used but not disclosed. Deloitte was forced to partially refund and rewrite. A second Deloitte incident in Canada (November 2025) involved a C$1.6M healthcare report with at least four fake AI-generated citations. This maps to **Source Quality** — the single most catastrophic failure mode.

---

## Pass/fail criteria for each dimension, encoded for an AI evaluator

### Analytical Depth (15%) — "Does this advance understanding beyond the obvious?"

The intelligence community's ICD 203 Standard 4 ("Alternatives") and Standard 6 ("Logic") provide the sharpest encodable criteria. Analysis of Competing Hypotheses (ACH), developed by Richards Heuer, requires identifying alternative explanations and evaluating evidence that **disconfirms** rather than confirms hypotheses. This is the operational definition of analytical depth: the deliverable considers what else could be true and explains why the chosen interpretation is strongest.

| Criterion | Pass | Fail |
|-----------|------|------|
| Hypothesis articulation | States a specific, falsifiable hypothesis within the first 10% of content | No hypothesis stated; begins with background or methodology |
| Alternative consideration | Identifies ≥2 competing explanations and explains why they were rejected with specific evidence | Single explanation offered without acknowledging alternatives |
| Decomposition quality | Custom issue tree built from the problem's specific structure; branches are MECE; analysis prioritizes high-impact branches | Recognizable textbook framework applied without adaptation; all branches explored equally |
| "So what" presence | Every major finding has an explicit implication statement that is quantified and client-specific | Findings presented as data without interpretation; implications are generic |
| Causal reasoning | Distinguishes correlation from causation; identifies mechanism, not just pattern | Implies causation from correlation; states trends without explaining drivers |
| Depth vs. breadth balance | Goes deep on 2–3 highest-impact areas; acknowledges remaining areas with 80/20 prioritization | Surface-level treatment of many areas; or exhaustive treatment of low-impact areas |

**USE**: ICD 203 Standard 4 (Alternatives) — encode ACH as a required check for any deliverable making causal claims. **USE**: The McKinsey "ghost deck" pattern — the evaluator should check whether the argument structure is coherent before evaluating content quality. **LEARN**: Victor Cheng's decomposition logic — steal the meta-skill of structured decomposition but not the specific frameworks. **Confidence**: Credible (ICD 203 is official government directive; practitioner testimony is consistent across sources).

### Source Quality (10%) — "Would this survive a hostile fact-check?"

The intelligence community's **Admiralty Code** (NATO system) provides a directly implementable two-axis evaluation: source reliability (A–F) and information credibility (1–6), evaluated independently. The Deloitte incidents prove this dimension is existential — a single fabricated citation can destroy an entire deliverable's credibility.

| Criterion | Pass | Fail |
|-----------|------|------|
| Citation verifiability | Every factual claim cites a specific, retrievable source (named publication, date, author) | Claims made without attribution; sources are vague ("studies show," "experts say") |
| Source existence | All cited sources actually exist and say what is attributed to them | Any fabricated, non-existent, or misattributed source (automatic fail for entire deliverable) |
| Source timeliness | Data points cite sources from within 18 months unless historical context requires older data | Key market/financial data from >2 years ago presented as current without temporal caveat |
| Source diversity | ≥3 independent source types used (e.g., primary data, industry report, academic study, practitioner account) | Single source type for all claims; or circular citation (multiple sources citing the same original) |
| Source reliability grading | Acknowledges source limitations where relevant (e.g., "per company self-reported data" vs. "per audited financials") | All sources treated as equally authoritative; no distinction between marketing claims and verified data |
| Quote accuracy | All direct quotes are verbatim; attributed to correct individuals with correct titles | Paraphrases presented as quotes; quotes attributed to wrong people; names misspelled |

**USE**: Admiralty Code — implement as a two-axis scoring system (source reliability × information credibility) for every major claim. **USE**: Deloitte incident as the canonical negative case — define "automatic fail" triggers for fabricated sources. **USE**: ICD 203 Standard 1 (Sourcing) — "properly describes quality and credibility of underlying sources." **Confidence**: Verified (Admiralty Code is NATO standard; ICD 203 is official US government directive; Deloitte incidents documented by AP, Fortune, The Guardian).

### Quantitative Rigor (15%) — "Are the numbers defensible at the right level of precision?"

The consulting standard is **"directionally correct"** — within ±20% margin of error, with appropriate rounding and offsetting errors. False precision is a bigger sin than imprecision. The BCG/Harvard study provides the benchmark: AI-assisted consultants produced **40%+ higher quality** on "inside the frontier" analytical tasks but performed **19 percentage points worse** on complex integrative tasks. This "jagged technological frontier" maps directly to when quantitative AI output can be trusted versus when it needs human verification.

| Criterion | Pass | Fail |
|-----------|------|------|
| Precision calibration | Numbers rounded to reflect actual methodology precision; ranges used when methodology supports ranges | False precision (e.g., "$4.237B" when inputs only support "roughly $4–5B") |
| Methodology transparency | States how numbers were derived; key assumptions explicit | Numbers presented without derivation; assumptions unstated |
| Sensitivity acknowledgment | Identifies which inputs the conclusion is most sensitive to; tests at least one key variable | Conclusion presented as certain when it depends heavily on a single assumption |
| Unit consistency | All numbers use consistent units, time periods, and currencies with explicit labeling | Mixed currencies without conversion; annual vs. quarterly figures compared without adjustment |
| Order-of-magnitude check | Result is sanity-checked against known benchmarks or back-of-envelope verification | Result is implausible on inspection (e.g., market size exceeds country GDP) |
| "Stop when sufficient" test | Analysis stops when it reaches decision-relevant precision; doesn't over-refine | Two extra weeks spent narrowing $200–300M to $227.1M when threshold is $100M |

**USE**: The ±20% "directionally correct" standard from practitioner sources. **USE**: BCG/Harvard study's "jagged frontier" concept to calibrate where AI quantitative work needs human verification (inside-frontier tasks: market sizing, benchmarking, trend analysis; outside-frontier tasks: integrative analysis requiring multiple data types). **LEARN**: ICD 203 Words of Estimative Probability table — adapt the ~probability ranges for conveying quantitative uncertainty in consulting context. **Confidence**: Verified (BCG/Harvard study is pre-registered RCT with 758 participants, forthcoming in *Organization Science*; practitioner precision standards are consistent across 5+ independent sources).

### Narrative Coherence (10%) — "Can I read only the headlines and understand the entire argument?"

The Pyramid Principle as practiced at McKinsey is the gold standard, and it is not optional. Barbara Minto, the first female post-MBA hire at McKinsey (1963), developed it because "the problem was the thinking, not the language." In practice, per former McKinsey consultant Ameet Ranadive: "When an executive asked 'What should we do?' — you were to start your response with 'You should do X,' very crisply and directly." The SCR (Situation-Complication-Resolution) framework provides the narrative arc; the Pyramid structures the argument within Resolution.

| Criterion | Pass | Fail |
|-----------|------|------|
| Answer-first structure | Recommendation/key finding stated in first 1–2 sentences; body provides supporting evidence | Conclusion buried at end; builds up to answer; begins with methodology or context |
| Action titles | Every section header is a complete declarative sentence stating the key insight | Section headers are topic labels ("Market Analysis," "Competitive Landscape") |
| Storyline test | Reading only the section headers conveys the complete logical argument | Headers are disconnected; reading them sequentially produces no coherent narrative |
| MECE supporting arguments | 2–4 supporting arguments that don't overlap and collectively cover the key reasoning | Arguments overlap; >4 arguments (unfocused); <2 arguments (insufficient) |
| SCR presence | Clear situation (what's known), complication (what changed/threatens), and resolution (what to do) | No narrative arc; facts presented without context or urgency |
| Logical chain integrity | Each claim follows from the prior; no logical leaps; evidence connects to conclusions | Assertions without evidence; evidence presented but not connected to conclusion; non sequiturs |

**USE**: Pyramid Principle's answer-first rule — encode as a structural check (is the recommendation in the first 10% of content?). **USE**: Action title test — evaluate whether section headers form a coherent argument when read alone. **USE**: SCR framework detection — check for Situation/Complication/Resolution arc. **LEARN**: The McKinsey "ghost deck" process — the evaluator should assess structure before content, mimicking how partners review. **Confidence**: Verified (Minto's framework is documented at mckinsey.com; practitioner testimony is consistent across 10+ independent sources; actual McKinsey decks like the USPS engagement are publicly available as examples).

### Completeness (10%) — "Does this cover what matters without drowning in what doesn't?"

This is the most counterintuitive dimension: completeness in consulting means **covering the decision-relevant territory, not covering everything**. The 80/20 principle is sacred. McKinsey's Rasiel is explicit: "resist the temptation to tweak your presentation at the last minute." The ICD 203 standard requires analysis be "based on all available sources of intelligence information" — but even the IC acknowledges analysts must "identify and address critical information gaps," not fill every gap.

| Criterion | Pass | Fail |
|-----------|------|------|
| Decision-relevant coverage | All factors material to the stated decision/question are addressed | Key factor obviously missing (e.g., regulatory risk absent from market entry analysis) |
| 80/20 prioritization | High-impact areas receive deep treatment; low-impact areas acknowledged briefly or relegated to appendix | All areas treated equally regardless of impact; or major area omitted entirely |
| Gap acknowledgment | Explicitly states what was not analyzed and why (e.g., "We excluded SMB segment as it represents <5% of addressable market") | Gaps exist without acknowledgment; reader must discover omissions |
| Scope discipline | Stays within the boundaries of the question asked; doesn't drift into tangentially related territory | Boils the ocean — two weeks of benchmark analysis without answering the original question |
| Supporting evidence sufficiency | Each major claim supported by ≥2 independent data points | Claims supported by single anecdote or unsupported assertion |
| Appendix strategy | Detailed backup data available but separated from the main argument | Dense data tables embedded in the main narrative; or no backup data available when challenged |

**USE**: ICD 203 Standard 5 (Relevance) — "demonstrates customer relevance and addresses implications." **USE**: The 80/20 standard as a concrete test: does the deliverable spend proportionally more space on higher-impact factors? **LEARN**: The McKinsey "one insight per slide" rule — adapt to "one insight per section" for written deliverables. **Confidence**: Credible (practitioner testimony consistent across 5+ sources; ICD 203 is official government directive).

### Actionability (15%) — "Could a decision-maker act on this Monday morning?"

The highest-weighted dimension alongside Analytical Depth and Intent Alignment, and for good reason. The HBR "trendslop" study (March 2026, by researchers from Esade, University of Sydney, and NYU Stern) demonstrated that LLMs consistently recommend strategies aligned with modern buzzwords rather than context-specific strategic logic. Partners reject deliverables that end with "consider digital transformation" — they want "invest $12M in warehouse automation by Q3, targeting 18% cost reduction in fulfillment, monitored via weekly throughput metrics." David A. Fields (consulting practitioner) captures the standard: great deliverables are "New-Balanced — they simultaneously tell clients, 'It's a good thing you hired us' and 'You're smart too.'"

| Criterion | Pass | Fail |
|-----------|------|------|
| Specificity of recommendations | Recommendations name specific actions, owners, timelines, and expected outcomes | "Consider exploring," "may want to evaluate," or other hedge-laden suggestions |
| Implementation awareness | Acknowledges real constraints (budget, org structure, regulatory, timeline) | Recommendations ignore obvious implementation barriers |
| Prioritization | Actions ranked by impact and urgency; first step is unambiguous | Flat list of actions with no prioritization or sequencing |
| Measurability | Each recommendation includes a metric or indicator to track progress | No way to measure whether recommendation was implemented or successful |
| Context specificity | Recommendations are specific to this client's situation, industry, and competitive position | Generic recommendations that could apply to any company ("leverage data analytics," "focus on customer experience") — this is trendslop |
| Risk acknowledgment | Key risks and mitigation strategies stated for top recommendations | Recommendations presented without downside analysis |

**USE**: "Trendslop" detection as a measurable quality criterion — the evaluator should penalize outputs that default to trendy/generic recommendations. **USE**: ICD 203 Standard 5 (Relevance) — specifically the requirement to "address implications." **USE**: The 5R recommendation framework (Recommendation, Reasons, Risks, Retention/next steps) as a structural check. **LEARN**: The Pyramid Principle's Resolution section — the resolution must be the majority (60–80%) of the deliverable content. **Confidence**: Verified (HBR trendslop study is from named academic researchers at major universities; practitioner standards consistent across sources).

### Intent Alignment (15%) — "Does this answer the actual question that was asked?"

This dimension maps to what partners describe as the difference between "doing the work" and "answering the question." Gorka K. Briones (practitioner) captured it precisely: "Very often you can find hard-working junior consultants that, after two weeks working on a benchmark, do not really know what was the question they were trying to answer." In intelligence tradecraft, ICD 203's timeliness standard includes the requirement that analysis be "disseminated in time to be actionable" — late but perfect analysis fails this dimension. The ICD 203 Standard 5 (Relevance) requires products to "demonstrate customer relevance."

| Criterion | Pass | Fail |
|-----------|------|------|
| Question restatement | Deliverable explicitly restates or references the original question/brief within the first section | No clear connection between the content and the question asked |
| Scope match | Depth and breadth match what was requested (quick scan vs. deep dive vs. comprehensive landscape) | Quick question answered with 50-page report; strategic question answered with data dump |
| Decision context awareness | Frames findings in terms of the decision the client faces, not abstract knowledge | Academic treatment of a topic disconnected from the decision context |
| Audience calibration | Technical depth matches the intended audience (C-suite summary vs. technical appendix vs. implementation guide) | PhD-level methodology section for a board presentation; or oversimplified analysis for a technical team |
| Hypothesis alignment | If a hypothesis was provided, the analysis tests it directly (confirming, refuting, or refining) | Analysis tangential to the hypothesis; new questions raised without answering the original |
| Format compliance | Follows any explicit formatting requirements; respects stated page/time/scope constraints | Ignores explicit constraints; delivers wrong format or dramatically exceeds scope |

**USE**: ICD 203 Standard 3 (Distinguishing) — "properly distinguishes between underlying intelligence information and analysts' assumptions and judgments." This is directly encodable: does the deliverable clearly separate facts from interpretation? **USE**: The McKinsey "ghost deck alignment" practice — the evaluator should check whether the deliverable structure was aligned to the question before content was produced. **LEARN**: The "elevator test" — can the core answer be delivered in 30 seconds? If not, intent alignment is failing. **Confidence**: Credible (practitioner sources consistent; ICD 203 is official directive).

### Intellectual Honesty (10%) — "Does this acknowledge what it doesn't know?"

ICD 203 Standard 2 ("Uncertainty") and Standard 3 ("Distinguishing") provide the most rigorous encodable criteria for intellectual honesty. The IC mandates specific **Words of Estimative Probability** with defined numerical ranges: "likely" means ~55–80%; "very likely" means ~80–95%. Confidence levels (high, moderate, low) must be stated separately from likelihood. The intelligence community requires that analysts never conflate what they know with what they infer. The BCG/Harvard study's "jagged technological frontier" finding — that AI-assisted consultants performed 19 percentage points worse on complex integrative tasks — demonstrates that acknowledging the boundaries of AI-generated analysis is not optional.

| Criterion | Pass | Fail |
|-----------|------|------|
| Uncertainty expression | Confidence levels or probability qualifiers used for key judgments; ranges provided rather than false point estimates | All claims presented with equal certainty; no hedging on uncertain judgments |
| Fact/inference separation | Clear distinction between verified data, analyst interpretation, and speculation | Inferences presented as facts; assumptions unstated; analyst opinion blended with data |
| Limitation disclosure | Methodology limitations, data gaps, and analytical constraints stated explicitly | No limitations section; implies comprehensive certainty |
| Contrary evidence | Mentions evidence that contradicts the main thesis; explains why it was weighted lower | Only evidence supporting the preferred conclusion presented; confirmation bias |
| Assumption transparency | Key assumptions listed explicitly; conditions under which they might not hold are identified | Assumptions hidden within analysis; not available for challenge |
| Epistemic humility markers | Uses calibrated language: "the evidence suggests" vs. "this proves"; "based on available data" vs. absolute claims | Overclaims certainty; uses absolute language for probabilistic judgments |

**USE**: ICD 203 Words of Estimative Probability table — adapt directly as the required lexicon for expressing uncertainty in deliverables. Define consulting equivalents: "high confidence" = assessment based on multiple high-quality sources with consistent findings; "moderate confidence" = credibly sourced but insufficient corroboration; "low confidence" = fragmented or poorly corroborated. **USE**: Key Assumptions Check (KAC) technique — encode as a required section: list key assumptions, state why each must be true, identify what would change the conclusion. **USE**: Pre-Mortem Analysis — encode as a quality check: "Imagine this analysis proved wrong. What would have been the most likely cause of failure?" **Confidence**: Verified (ICD 203 is official government directive; KAC and Pre-Mortem are documented CIA tradecraft techniques; BCG/Harvard study is peer-reviewed RCT).

---

## Intelligence tradecraft techniques directly implementable as multi-agent components

Five structured analytic techniques from the CIA Tradecraft Primer and Heuer & Pherson translate directly into multi-agent system components:

**Analysis of Competing Hypotheses (ACH)** maps to a dedicated "devil's advocate" agent that takes the primary agent's conclusion, generates 2–3 alternative explanations, and evaluates which evidence would differentiate between hypotheses. Pass criterion: the system considered alternatives. Fail: single-hypothesis tunnel vision. Maps to **Analytical Depth** and **Intellectual Honesty**.

**Key Assumptions Check (KAC)** maps to a "pre-flight" agent that runs before the final output, extracting every unstated assumption and flagging any that are uncertain, unverified, or contested. The CIA's four-step method (review analytic line → articulate all premises → challenge each → refine) is directly automatable. Maps to **Intellectual Honesty**.

**Red Team Analysis** maps to an adversarial review agent that adopts the perspective of a skeptical partner or a competitor's strategy team and attacks the deliverable's weakest points. The CIA protocol requires "first person" format — the agent literally writes as the opposing party. Maps to **Analytical Depth** and **Narrative Coherence**.

**Pre-Mortem Analysis** (developed by cognitive psychologist Gary Klein) maps to a "what if wrong" agent that assumes the conclusion is incorrect and reasons backward to identify the most likely failure point. This is the single most powerful technique for catching overconfidence. Maps to **Intellectual Honesty** and **Quantitative Rigor**.

**Structured Self-Critique** (developed by Randolph Pherson as an evolution of Pre-Mortem) maps to a comprehensive quality review agent that evaluates across four dimensions: sources of uncertainty, analytic process used, critical assumptions, and quality/completeness of evidence. This is essentially a meta-evaluator. Maps to **all eight dimensions**.

---

## The AI quality landscape validates this rubric's timing

McKinsey now operates with **25,000 AI agents alongside 40,000 humans** (CEO Bob Sternfels confirmed at CES, January 2026, verified by McKinsey spokesperson to Business Insider), targeting parity by year-end 2026. Over **75% of McKinsey's employees** use Lilli monthly, generating 500,000+ prompts per month. McKinsey uses **blind scoring on a five-point scale** for accuracy, content richness, and distinctiveness to evaluate Lilli outputs. BCG has scaled to **36,000 custom GPTs** (per BCG's Scott Wilder to Business Insider), with approximately 90% of employees having experimented with AI and nearly 50% using it daily.

Yet quality failures are accelerating alongside adoption. McKinsey's own 2025 Global AI Survey found that **51% of organizations** reported negative consequences from AI inaccuracy, up from 44% in 2024. The HBR "judgment gap" article (David Duncan, February 2026) frames the core problem: AI handles the messy analytical tasks that once built junior consultant judgment, creating professionals who advance without ever developing the discernment needed for senior roles.

The **speed-to-quality pivot** is now industry consensus. Stanford HAI (February 2026): "The era of AI evangelism is giving way to an era of AI evaluation. The question is no longer 'Can AI do this?' but 'How well, at what cost, and for whom?'" The World Economic Forum: "If 2025 has been the year of AI hype, 2026 might be the year of AI reckoning." BCG's own Henderson Institute researchers documented **"AI brain fry"** (HBR, March 2026) — cognitive fatigue from excessive AI oversight leading to mental fog, slower decision-making, and increased errors — proving that human reviewers alone cannot maintain quality at scale.

PwC's "Learning Collective" curriculum (launched February 5, 2026) codifies **30 essential skills — 15 AI-focused and 15 human** — with the rule that "if you are teaching AI skills in this firm, you are also teaching human skills. They have to be taught together." The MCA UK survey (January 2026) reports **77% of consulting firms** have integrated AI, with 76% using it for research. Yet the futureofconsulting.ai analysis (Marin Ivezic, former Big Four partner, January 2026) argues convincingly that despite **$10B+ collective investment** since 2023, "changes remain largely internal" and firms are "layering AI on top of an outdated model without changing the model itself."

---

## Synthesis: the evaluator rubric as institutional judgment

The evidence from all six research streams converges on a single insight: **the quality bar that senior partners apply instinctively can be made explicit, and much of it can be automated**. The eight dimensions of the Keystone rubric map cleanly to tested standards:

The consulting quality bar (what partners actually reject) maps to **Actionability, Analytical Depth, and Narrative Coherence**. The Pyramid Principle and SCR framework provide concrete structural tests for coherence. The "so what" test and "trendslop" detection provide concrete content tests for depth and actionability.

The intelligence community's ICD 203 and structured analytic techniques map to **Intellectual Honesty, Source Quality, and Quantitative Rigor**. The Admiralty Code provides a two-axis source evaluation system. Words of Estimative Probability provide calibrated uncertainty language. ACH, KAC, and Pre-Mortem provide automated checks for analytical blind spots.

The AI-era evidence (BCG/Harvard study, Deloitte incidents, brain fry research) maps to **the entire rubric** by establishing that automated quality evaluation is no longer optional — it's the necessary response to AI adoption at scale, cognitive limits on human review, and catastrophic failure modes that manual processes missed.

The rubric should not aim to replace partner judgment. It should encode the **80% of quality assessment that is pattern-matching** (structural checks, source verification, precision calibration, completeness coverage) so that human reviewers can focus on the **20% that requires genuine judgment** (strategic insight quality, client-specific relevance, creative value of recommendations). This allocation mirrors both the 80/20 principle that consulting prizes and the academic finding that LLMs excel at systematic validity checks while humans are better at assessing novelty and significance.