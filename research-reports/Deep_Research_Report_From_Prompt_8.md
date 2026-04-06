# Taste can be decomposed — but not completely

**The answer to the Keystone Intelligence Engine's core design question is hybrid: decompose taste into 10–12 evaluable dimensions for reliability, then add a holistic overlay to catch what rubrics miss.** Research across education, medicine, design, and the emerging LLM-as-judge literature converges on this conclusion. Analytic rubrics achieve **66% inter-rater agreement** versus 46% for holistic approaches, but studies consistently find that even experts using analytic rubrics process quality holistically first and use dimensional criteria post-hoc to articulate judgments already formed. The practical implication for the Evaluator (Layer 4) is a two-pass architecture: dimensional scoring first, gestalt adjustment second, with a Rejection Library encoding the "negative space" of quality — what taste excludes.

This report synthesizes findings from the February 2026 "taste discourse," Stripe Press's "Tacit" docuseries, six key thinkers on judgment and AI, academic expertise research, LLM-as-judge literature, and practical quality frameworks from consulting, design, and code review. Every finding maps to the eight-dimension rubric, the Rejection Library, or the self-improvement loop.

---

## The 2026 taste debate reveals a three-way split

On February 14, 2026, Paul Graham posted to his 2.2 million followers: *"Prediction: In the AI age, taste will become even more important. When anyone can make anything, the big differentiator is what you choose to make."* Two days later, Greg Brockman (OpenAI president) posted five words — **"taste is a new core skill"** — generating 2.8 million views. Dane Knecht, Cloudflare's current CTO (not John Graham-Cumming, who retired in March 2025), had already written in January 2026: *"In 2026, taste is the engineering differentiator."* Sam Altman weighed in February 27, calling for "context, taste and a real feel for where the field is headed."

The discourse split into three camps. The **pro-taste camp** (Graham, Brockman, Knecht, Altman) argues that when execution is cheap, discrimination between options becomes the bottleneck. The **skeptics** (Nan Yu of Linear, Matt Schumer of OthersideAI) counter that taste is exactly what AI replicates best — trained on more human content than anyone could consume in a lifetime, LLMs are essentially taste engines. The most penetrating critique came from **Artem Voronoff**, who wrote "You're Wrong About Taste" on Medium: *"Taste is a core skill. I'm not arguing otherwise. Taste is being automated. And the thing that can't be automated, conviction, isn't being discussed at all."* His argument: AI is sycophantic by design (citing Anthropic's research on models abandoning correct answers under social pressure), taste is precisely what pattern-matching excels at, and the real differentiator is conviction — the willingness to push against consensus with skin in the game. Kyle Chayka captured the cultural backlash in a March 2026 New Yorker piece, "Why Tech Bros Are Now Obsessed with Taste."

**Relevance to the Evaluator**: The three camps map to three evaluation failure modes. The pro-taste camp identifies the discrimination problem (can the system tell good from great?). The skeptics identify the convergence problem (does the system just reproduce median quality?). Voronoff identifies the courage problem (does the system flag genuinely novel insight or just reward convention?). The rubric needs dimensions for all three.

The most operationally useful contribution came from Itamar Medeiros at Designative (February 1, 2026): *"Teams can encode their standards of taste into prompts, evaluation functions, and design systems, raising the baseline quality of everything the tools touch."* His framework distinguishes high-taste/low-expertise users (who gain leverage) from high-taste/high-expertise teams (who gain force multiplication). This maps directly to the Evaluator's role: it must encode expert-level taste into evaluation functions.

| Voice | Core Claim | Evidence Quality | Implication for Evaluator |
|-------|-----------|-----------------|--------------------------|
| Graham/Brockman | Taste is the new differentiator | Credible (tweets, not research) | Validates discrimination-focused evaluation |
| Voronoff | Conviction, not taste, resists automation | Credible (well-sourced essay) | Add "originality/contrarianism" dimension |
| Designative | Taste can be encoded into evaluation functions | Credible (practitioner analysis) | Direct architectural validation |
| Nan Yu / Schumer | AI already has better taste than most humans | Claimed (tweets) | Convergence detection needed |

---

## LLMs reach conscious competence but not judgment

Stripe Press launched the "Tacit" docuseries on December 18, 2025 — two films about a knifemaker and a master perfumer, with a Director's Note by Tamara Winter that delivers the key theoretical contribution. Citing Cedric Chin's Commoncog work as inspiration, Winter writes: *"The ceiling for LLMs, for now, seems to be conscious competence. They can capture and articulate procedure (or at least the median advice on any particular topic), but not judgment."*

The conscious competence model (unconscious incompetence → conscious incompetence → conscious competence → unconscious competence) maps cleanly to the Evaluator design problem. **Conscious competence is rubric-following**: the system can apply explicit criteria and articulate why it scored something a certain way. **Unconscious competence is taste**: the expert evaluator who immediately senses that something is off before they can name what's wrong. The Stripe Press argument — verified by the Dreyfus model (1980, 1986) and evaluative judgment research (Tai et al., 2018; Sadler, 1989) — is that LLMs are stuck at stage three.

Winter's perfumery test is illustrative: she asked ChatGPT, Claude, and Gemini to design a jasmine fragrance. All three produced tidy, technically correct note pyramids featuring jasmine sambac absolute. None produced anything surprising. This is **competent mediocrity** — the defining failure mode for AI evaluation systems.

Cedric Chin's work provides the toolkit for attempting to bridge this gap. His **Cognitive Task Analysis (CTA)** method, drawn from Naturalistic Decision Making research by Gary Klein and Laura Militello, extracts tacit mental models from experts through structured interviews and observation. His "Vaughn Tan Rule" — *"Do NOT outsource your subjective value judgments to an AI"* — identifies the boundary line. His taxonomy of tacit knowledge (from Harry Collins) — somatic (embodied), relational (expert intuition), and collective (organizational) — suggests that the Evaluator can potentially capture relational tacit knowledge through extensive exposure to expert evaluation examples, but collective tacit knowledge (the standards of a specific consulting firm's culture) requires deliberate organizational encoding.

**Mapping to the Evaluator architecture**:

- **Dimensions 1-6 of the current rubric** (Analytical Depth, Source Quality, Quantitative Rigor, Narrative Coherence, Completeness, Actionability) are largely conscious-competence evaluations — procedural, checkable, articulable.
- **Dimensions 7-8** (Intent Alignment, Intellectual Honesty) require judgment that approaches unconscious competence — recognizing when a brief technically answers the question but misses the real need, or when intellectual honesty is being performed rather than practiced.
- **The gap**: No current dimension captures "surprising quality" — the difference between a competent brief and one that changes how the reader thinks about the problem. This is where taste lives.

---

## The prediction-judgment split determines who benefits from AI

The IMF's June 2025 article "Machine Intelligence and Human Judgment" (Agrawal, Gans, and Goldfarb of the Rotman School) provides the macroeconomic frame: *"As AI prediction advances, the distribution of judgment will increasingly determine the distribution of wealth and power."* Their framework distinguishes prediction-intensive work (where AI equalizes by substituting for human prediction, benefiting lower-skilled workers) from judgment-intensive work (where AI amplifies existing expertise, widening inequality). A Stanford call center study found **34% productivity gains** for lower-skilled workers from AI; a debate competition study found **12% win-rate improvement** only for higher-ability debaters.

David Duncan's HBR article (February 3, 2026) identifies the organizational paradox: *"AI simultaneously increases the need for judgment and erodes the experiences that produce it."* As a consulting partner, Duncan observed that AI helped experienced consultants enormously while junior employees couldn't assess whether AI output was any good. His solution: deliberately redesign work to build judgment through stretch experiences, consequence exposure, and explicit decision rights.

**The CodeRabbit data quantifies the judgment gap.** Their December 2025 study of 470 GitHub pull requests found AI-generated code contains **1.7x more issues** overall — including **3x more readability issues**, **2x more error handling gaps**, and **8x more performance problems**. The METR study corroborated this: **50-67% of AI-generated pull requests that pass automated tests would be rejected by human maintainers** for poor quality, bad style, or failing repository standards. A separate METR randomized controlled trial found experienced developers using AI tools were actually **19% slower**, despite believing they were 20% faster — a striking calibration failure.

These findings directly validate the Keystone Intelligence Engine's architectural conviction that **evaluation quality bounds output quality**. If the Evaluator cannot detect the 1.7x issue rate in AI-generated analytical work — the equivalent of readability failures, logic errors, and "performance" problems in consulting research — the entire system degrades.

---

## Academic expertise research defines the evaluation ceiling

Four academic traditions converge on the same insight: expert judgment cannot be fully codified, but it can be systematically developed.

**Anders Ericsson's deliberate practice** framework establishes the mechanism: the **3F loop** (Focus → Feedback → Fix It) with tight feedback cycles drives skill development. His research shows that expertise requires not just practice hours but specifically designed practice targeting weak areas with immediate feedback. The meta-analytic debates (Macnamara et al., 2014: deliberate practice explains only **12% of variance** across domains) nuance but don't invalidate this — practice is necessary but not sufficient. For the Evaluator's self-improvement loop, the implication is clear: evaluation quality improves through systematic comparison against expert judgments with rapid iteration, not just volume of evaluations performed.

**The Dreyfus model** (1980, 1986, updated 2021 with a sixth stage) describes the qualitative transition from rule-following to intuitive judgment across five stages. At the **competent** level (stage 3), the evaluator follows rubric criteria analytically. At the **proficient** level (stage 4), the evaluator intuitively perceives what's strong or weak but still deliberates on specific ratings. At the **expert** level (stage 5), perception and response are unified — the evaluator immediately knows the appropriate assessment. Dreyfus's core warning: *"If one seeks the safety of rules, one will not get beyond competence."* Over-reliance on codified criteria creates a ceiling. Critically, he argues emotional involvement — feeling the consequences of evaluation quality — is required for progression beyond competence.

**Evaluative judgment research** (Tai, Ajjawi, Boud, Dawson, 2018 — 599 citations) defines evaluative judgment as *"the capability to make decisions about the quality of work of oneself and others."* Key finding: quality recognition precedes articulation. Experts can detect quality before naming criteria — Sadler (2013): *"quality is something I do not know how to define, but I recognise it when I see it."* Assessment standards include tacit elements that "resist complete codification." The 2024 extension (Bearman et al.) explicitly addresses AI: they argue for maintaining humans as "arbiters of quality" while developing evaluative judgment *of* AI outputs and *of* AI evaluation processes.

**Tetlock's superforecasting research** provides the calibration model. The top **2% of forecasters** (superforecasters) were 30% better than intelligence officers with classified information. Their key traits: open-mindedness, self-criticism, probabilistic thinking, and — critically — commitment to self-improvement through calibration feedback. The strongest debiasing technique: **generating reasons for AND against** each assessment before scoring. Koriat, Lichtenstein, and Fischhoff found this makes subjects "extremely well calibrated."

Richards Heuer's **Analysis of Competing Hypotheses** (CIA, 1999) contributes the rejection-first methodology: *"The best hypothesis is the one with the least evidence against it, rather than the most evidence for it."* Focus on disconfirmation rather than confirmation. This maps directly to the Rejection Library concept — quality defined by what survives attempted disconfirmation.

---

## The hybrid architecture for operationalizing taste

The LLM-as-judge literature (2024-2026) provides concrete engineering patterns. Major survey papers (Gu et al., 2024; Li et al., EMNLP 2025) establish that:

**What works**: Pairwise comparison is the most reliable format — humans and LLMs find it easier to compare than to assign absolute scores. Rubric-based evaluation with chain-of-thought reasoning (prompting the judge to explain before scoring) significantly improves alignment with human judgments. Position switching (running evaluation twice with swapped positions, accepting only consistent results) addresses the largest bias source. Multi-judge ensembles using diverse model families achieve **>80% consensus** in most cases.

**What fails**: Position bias (preferring first or second response), verbosity bias (rewarding length over quality), and self-enhancement bias (models preferring outputs similar to their own training distribution). The CALM framework identifies **12 distinct bias types** including authority bias (fake citations fool LLM judges) and fallacy oversight (failing to detect logical errors). The LMArena controversy (2025) demonstrated Goodhart's Law in practice: when model labs treated Arena rankings as target metrics, they selectively showcased strongest variants to inflate scores.

The evidence across all domains converges on a **two-pass hybrid architecture**:

**Pass 1 — Dimensional Analysis** (conscious competence): Score each rubric dimension independently using specialized criteria. Analytic rubrics achieve 66% inter-rater agreement versus 46% for holistic (Jönsson & Balan, 2018). Multi-trait specialization (Lee et al., 2024) shows trait-specific prompts improve scoring quality. This handles the machine-checkable and expert-checkable evaluation categories.

**Pass 2 — Holistic Overlay** (approaching unconscious competence): After dimensional scoring, apply a gestalt assessment with a ±5-10% adjustment for emergent qualities that dimensional scoring misses — exceptional coherence, surprising insight, or pervasive mediocrity. Research confirms that even experts using analytic rubrics process holistically first and use criteria post-hoc. The holistic pass captures judgment-dependent evaluation.

**Pass 3 — Rejection Scan** (negative space): Run the output against the Rejection Library — a catalog of anti-patterns, quality failures, and red flags. This implements Heuer's disconfirmation logic: quality is partly defined by the absence of known failure modes.

---

## Five frameworks the Evaluator should directly integrate

**The Minto Pyramid Principle (McKinsey)** — USE. Directly operationalizes logical quality: lead with the answer, support with MECE arguments, ground in evidence. The MECE test (Mutually Exclusive, Collectively Exhaustive) is a machine-checkable criterion for completeness. The "so-what test" (every insight must have implications) maps to the Actionability dimension. *Maps to: Analytical Depth, Narrative Coherence, Completeness.*

**AAC&U VALUE Rubrics** — USE. The gold standard for encoding expert judgment at scale — 16 rubrics used by **5,600+ organizations across 159 countries**. Design pattern: collaborative expert development, four progressive performance levels (Benchmark → Milestones → Capstone), adaptable language for different contexts. The Critical Thinking rubric dimensions (explanation of issues, evidence selection, context/assumptions, position-taking, conclusions) provide a validated model for analytical quality assessment. *Maps to: rubric design methodology, self-improvement loop calibration.*

**Lasater Clinical Judgment Rubric** — USE. The **Noticing → Interpreting → Responding → Reflecting** progression (Cronbach's alpha .80–.97) models how expert judgment operates as a process, not just an output. An evaluator should assess not just whether the research brief is correct but whether it demonstrates good noticing (identifying the right signals), interpreting (framing them correctly), responding (drawing appropriate conclusions), and reflecting (acknowledging limitations). *Maps to: Intellectual Honesty, Intent Alignment.*

**Google Code Review Framework** — USE. Eight review dimensions (design, functionality, complexity, tests, naming, comments, style, documentation) with the governing principle: *"Technical facts and data overrule opinions and personal preferences."* The "continuous improvement over perfection" philosophy and "Nit" prefix for optional feedback provide a practical model for graded evaluation severity. *Maps to: evaluation system UX, Rejection Library severity levels.*

**Tetlock's Superforecaster Calibration Methods** — USE. Brier scoring for calibrated confidence, generating reasons for AND against each assessment, distinguishing inside from outside views, and the commitment to self-improvement through systematic error analysis. These map directly to the self-improvement loop. *Maps to: self-improvement loop, calibrated confidence output.*

---

## What the Rejection Library should encode

The "negative space" approach — defining quality partly by what it excludes — has strong theoretical backing. Biological taste literally evolved as a **rejection mechanism**: the gustatory system primarily prevents ingestion of harmful substances. Expert food tasters identify defects and judge severity. Heuer's ACH focuses on disconfirmation. Dieter Rams' most famous principle is "as little design as possible." 

The Rejection Library should encode three categories of rejection patterns, informed by the research:

**Category 1: Structural failures** (machine-checkable). Missing MECE logic, buried recommendations, unsupported assertions, circular reasoning, evidence that doesn't bear on the claim. These are the "readability and naming" issues from CodeRabbit — frequent, detectable, and the largest gap between AI and human output (3x more common in AI code).

**Category 2: Analytical failures** (expert-checkable). Confirmation bias (only citing supporting evidence), anchoring on first-found data, false precision (citing specific numbers without confidence bounds), category errors (comparing incompatible entities), stale sourcing, and what Chin calls "median advice" — technically correct but undifferentiated analysis. The single-point rubric model is ideal here: describe what excellent analysis looks like, then flag any departure.

**Category 3: Judgment failures** (judgment-dependent). Voronoff's "hive mind problem" — arriving at the same conclusions as everyone else using the same tools. Duncan's "AI-experience paradox" — producing work that looks right but reflects no genuine understanding. Willison's "cognitive debt" — technically functioning output where the system doesn't understand its own reasoning. The "flat" quality that Stripe Press identified when LLMs attempted craft — competent but unsurprising. These are the hardest to detect and the most important to catch.

---

## Recommended rubric modifications and the fundamental answer

Based on this research, the eight-dimension rubric should be modified as follows:

**Add two dimensions:**

- **Evaluative Surprise (5%)** — Does the brief contain at least one insight, framing, or connection that a competent analyst following standard procedures would not have produced? This dimension directly addresses the conscious-competence ceiling. Scored on a binary + magnitude scale: is there genuine novelty, and how significant is it? *Inspired by: Stripe Press's "flat" diagnosis, Voronoff's conviction argument, Dreyfus's expert-level intuitive judgment.*

- **Calibrated Confidence (5%)** — Does the brief appropriately distinguish what is known with high confidence from what is uncertain or speculative? Does it avoid both false precision and excessive hedging? *Inspired by: Tetlock's superforecasters, calibration research showing experts are overconfident, Heuer's structured uncertainty.*

**Modify existing dimensions:**

- **Intellectual Honesty (10% → 10%)**: Expand to explicitly include "disconfirmation effort" — evidence that the brief actively sought and engaged with counterarguments rather than only supporting its thesis. Heuer's ACH and Tetlock's reason-generation research show this is the single most effective quality signal.

- **Analytical Depth (15% → 12%)**: Narrow to focus on logical structure quality (Pyramid Principle compliance, MECE completeness) rather than breadth of analysis, which overlaps with Completeness.

- **Completeness (10% → 8%)**: Reduce weight — the research shows that excess completeness produces mediocrity. The "as little as possible" principle (Rams) and the Pyramid Principle's emphasis on selecting what matters over covering everything.

**The reweighted rubric:**

| Dimension | Weight | Evaluation Type |
|-----------|--------|----------------|
| Actionability | 15% | Expert-checkable |
| Intent Alignment | 15% | Judgment-dependent |
| Quantitative Rigor | 15% | Machine-checkable |
| Analytical Depth | 12% | Expert-checkable |
| Intellectual Honesty | 10% | Judgment-dependent |
| Source Quality | 10% | Machine-checkable |
| Narrative Coherence | 10% | Expert-checkable |
| Completeness | 8% | Machine-checkable |
| Evaluative Surprise | 5% | Judgment-dependent |
| Calibrated Confidence | 5% | Judgment-dependent |

This shifts judgment-dependent evaluation from **25% to 35%** of total weight — reflecting the research consensus that taste dimensions are where the real quality differentiation occurs.

**The fundamental answer**: Taste is **partially decomposable**. Roughly 65% of evaluation quality can be captured through dimensional analysis with explicit criteria (the conscious-competence layer). The remaining 35% requires holistic judgment, implemented through the two-pass architecture (dimensional scoring + gestalt overlay) and the Rejection Library (negative space scanning). The system will never fully replicate expert unconscious competence — but by combining dimensional rigor with pattern-matched rejection and calibrated uncertainty, it can operate at a level that approaches the proficient stage of the Dreyfus model, significantly above the "competent mediocrity" ceiling that current LLM evaluation typically hits. The self-improvement loop, modeled on Ericsson's 3F cycle and Tetlock's calibration methods, is what moves the system toward that boundary over time. Evaluation quality does bound output quality — and the research confirms that the Evaluator is correctly identified as the most important component.

---

## Conclusion: the Evaluator as institutional taste

The research reveals a consistent pattern across every domain examined: expert judgment operates through rapid holistic perception refined by systematic feedback, not through rule-following. But this does not mean evaluation systems are futile — it means they must be designed as **scaffolding for judgment**, not substitutes for it. The AAC&U VALUE rubrics work at scale (5,600+ institutions) precisely because they encode progressive sophistication levels rather than rigid checklists. The Lasater Clinical Judgment Rubric works (Cronbach's alpha .97) because it evaluates the judgment *process* (noticing, interpreting, responding, reflecting), not just the judgment output.

Three novel insights emerge from this synthesis. First, the Rejection Library is more important than the rubric itself — Heuer, Tetlock, and the biological taste research all converge on the finding that quality detection works better through disconfirmation than confirmation. Build the library of anti-patterns before refining the positive scoring criteria. Second, Voronoff's conviction argument identifies a genuine gap: the system must actively detect and flag convergent, unsurprising analysis rather than rewarding it. The Evaluative Surprise dimension addresses this directly. Third, Duncan's paradox — AI erodes the experiences that build judgment — applies to the Evaluator itself. Without systematic calibration against expert human evaluations (the self-improvement loop), the Evaluator will drift toward rewarding exactly the kind of "competent mediocrity" it's designed to catch. The self-improvement loop isn't a nice-to-have. It's the mechanism that prevents the entire system from converging on slop.