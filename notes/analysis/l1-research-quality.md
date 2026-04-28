# L1 Research Quality Analysis: Pipeline Output vs. Batch-1 Benchmark

**Date:** 2026-04-21  
**Analyst:** Post-run analysis of first-ever L1 deep-mode execution  
**Pipeline output:** `output/l1_deep_mode_test_finding.json` — 28 claims, 46 sources  
**Benchmark:** `Deep_Research_Report_From_Prompt_1.md` — ~5,000 words, narrative markdown  
**Build on:** `notes/FIRST-RUN-ANALYSIS.md` (preliminary run observations)

---

## Orientation

The batch-1 benchmark report was produced by Claude's native deep research feature guided by a carefully crafted ~800-word prompt (A1 from `RESEARCH-PROMPTS-FINAL.md`) that named specific systems to investigate, specified sub-questions for each, and attached the full CAPSTONE-PLAN-v2.md as context. The pipeline's L1 output was produced by a single ResearchAgent running `claude -p --allowedTools WebSearch,WebFetch` against a task description of roughly 50 words. Both cover "Multi-Agent Research & Analysis Systems."

The FIRST-RUN-ANALYSIS.md established the quantitative baseline. This document goes deeper into each analysis dimension with specific textual evidence from both outputs.

---

## 1. Source Coverage

### What the pipeline found that the benchmark did not

The pipeline's most notable addition is its anti-confirmatory body of evidence — a set of academic papers that directly challenge the multi-agent thesis that underpins the entire Keystone architecture. These are genuinely important finds:

- **arXiv:2604.02460** (April 2026): "Single-Agent LLMs Outperform Multi-Agent Systems on Multi-Hop Reasoning Under Equal Thinking Token Budgets." The pipeline found this paper, published after the batch-1 report was written in March 2026. The benchmark literally could not have included it.
- **arXiv:2503.13657** (MAST taxonomy): 1,600+ annotated traces across 7 frameworks identifying 14 failure modes. The benchmark mentions failure modes discursively; the pipeline has the primary academic paper.
- **arXiv:2601.22984** (DeepHalluBench): PIES taxonomy of hallucination types in deep research agents. Not present in batch-1.
- **arXiv:2602.05930** (NeurIPS 2025 compound citation deception): 100% compound failure rate in fabricated citations. Not in batch-1.
- **Gemini Deep Research Max** (April 2026): Pipeline found the Google blog post and developer docs for the system launched April 21, 2026 — the day of the run. Batch-1 cannot have this.

The pipeline also found LangChain's **open_deep_research** (July 2025) with its specific RACE score, **Microsoft Agent Framework 1.0** absorbing AutoGen into maintenance mode (October 2025), and the **Databricks State of AI Agents 2026** report documenting 327% MAS adoption growth.

### What the benchmark found that the pipeline missed

The benchmark's superior source coverage is concentrated in its **synthesis and strategic interpretation** rather than raw source identification. Several specific topics from the A1 prompt were either missed or handled superficially in the pipeline:

- **DeerFlow 2.0** (ByteDance, 39.1K stars): The batch-1 report dedicates a paragraph to DeerFlow's production-grade LangGraph orchestration, Docker sandboxing, persistent memory, and ByteDance provenance risk. The pipeline does not have a dedicated claim for DeerFlow — it is mentioned only incidentally in the LangGraph claim as a system that "uses LangGraph."
- **Imbad0202/academic-research-skills**: The benchmark discusses this 5-star repository in detail — the 10-stage pipeline, the SCR protocol, the Devil's Advocate pattern, the 15-fabricated-references showcase — as the "strongest empirical evidence that evaluation quality scales with evaluation investment." The pipeline does not mention Imbad0202 at all.
- **Weizhena/Deep-Research-skills**: The benchmark identifies the Items × Fields matrix as a clean specification model for the Specification Engine. Missing from pipeline output.
- **199-Bio star count discrepancy**: The benchmark reports 58 stars; the pipeline reports 371 stars. The pipeline ran a month after the benchmark and found a different number, which is plausible growth — but worth flagging as a signal that the pipeline found more recent data.
- **Search infrastructure section**: The benchmark produces a detailed multi-paragraph section comparing Brave, Exa, Tavily, and SearXNG with specific pricing, benchmark scores, acquisition details, and a cost model ("$200-600/month at moderate usage"). The pipeline mentions search providers only incidentally and has no dedicated section or cost model.

### Source authority

Both outputs cite authoritative sources. The pipeline is somewhat stronger on academic citation (NAACL 2024, EMNLP 2024, ICLR 2024 papers with proper arXiv IDs). The benchmark, written for a human audience, uses inline references that are not independently verifiable as URLs. The pipeline has 46 real, crawled URLs. However, every source in the pipeline has the same `quality_score: 0.7` regardless of whether it is a peer-reviewed paper (NAACL 2024) or a Medium blog post (Cobus Greyling analysis). The uniform scoring means the downstream citation processor cannot distinguish authoritative from derivative sources.

---

## 2. Analytical Depth per Topic

### GPT-Researcher

**Pipeline (claim 1):** Reports the architecture (planner/executor), quantifies it (20+ sources, ~3 min, ~$0.10, deep mode ~$0.40), names the AG2 integration and its 8-agent pipeline, caveats with "benchmarks from own documentation." Two sentences of architecture, one sentence of caveats.

**Batch-1 report:** Spends a full paragraph on the architecture, then a second paragraph exclusively on its quality control failure: "Its hallucination strategy is 'scrape 20+ sites and assume the most frequent information is correct' — a probabilistic heuristic, not structural enforcement. The ReviewerAgent scores quality 1-10 via LLM prompting, but there is no architectural gate that can reject substandard output." It then draws the strategic implication: GPT-Researcher's weakness is Keystone's differentiation.

The pipeline correctly reports what GPT-Researcher does. The benchmark explains why that matters for Keystone's design.

### STORM

**Pipeline (claims 2, 18, 20):** Claim 2 reports the +25% organization / +10% breadth metric and the perspective-guided architecture. Claim 18 identifies the two failure modes (source bias transfer, over-association) as structural architectural limitations, citing the original NAACL paper. Claim 20 provides an "adapt" verdict explaining why STORM is not a drop-in for consulting-grade output.

**Batch-1 report:** "But the perspectives are cooperative information-gathering heuristics (event planner, cultural critic), not adversarial analytical positions (bull vs. bear). They generate breadth, not contested depth." This is a sharper analytical cut than the pipeline achieves. The benchmark also notes that STORM's development "plateaued since January 2025 — a classic academic project trajectory" — the pipeline has no health assessment for any system's maintenance trajectory.

The pipeline has the academic facts. The batch-1 report has the consulting interpretation — why cooperative heuristics are insufficient for the deliberation model Keystone is building.

### 199-Biotechnologies

**Pipeline (claim 9):** Lists the 8-phase pipeline phases by name, reports the 4 research modes with time estimates, mentions the red-teaming personas, validate_report.py (9 checks), verify_citations.py, auto-continuation, and the claim that it outputs "McKinsey-style HTML, Markdown, and PDF." A dense 3-sentence claim with good enumeration.

**Batch-1 report:** Covers the same facts but then pushes to the analytical layer: "its `validate_report.py` (9 structural checks) and `verify_citations.py` (DOI/URL verification) provide real structural enforcement" — and then immediately qualifies: "But the source credibility scoring (0-100) is semi-cosmetic — scores are LLM-generated heuristics, not backed by domain authority databases, and the personas are prompt-based role-playing within a single model, not genuinely diverse perspectives." This distinction — structural enforcement vs. cosmetic scoring — is exactly the type of discrimination Keystone needs to make about its own design.

The pipeline's claim about 199-Bio reads like a well-structured README summary. The benchmark's paragraph reads like a consultant's assessment.

---

## 3. Strategic Synthesis

This is the largest gap between the two outputs.

The batch-1 report opens with a thesis statement that holds for the entire document: "Every open-source research agent system reviewed enforces quality through prompts, not architecture." That observation is then used as a lens through which every individual system finding is interpreted. When the report covers GPT-Researcher's ReviewerAgent, it is placed in evidence of this thesis. When it covers 199-Bio's validate_report.py, it distinguishes structural checks (genuine) from credibility scoring (cosmetic). The thesis creates hierarchy and meaning.

The pipeline produces 28 independent claims. There is no hierarchical claim that sits above the others and organizes them. The three "verdict" claims (26-28: adopt open_deep_research, adapt STORM, skip MetaGPT/AutoGen) appear at the end but are isolated evaluations, not a unified framework. There is no pipeline equivalent to the benchmark's closing argument: "Keystone doesn't need to outperform GPT-5.2 at generation. It needs to outperform everyone at knowing when generation isn't good enough."

Cross-cutting patterns that the pipeline does not identify:
- The observation that every system reviewed uses prompts, not architecture, for quality enforcement
- The pattern that academic projects (STORM, 199-Bio) plateau after publication while production systems (GPT-Researcher, DeerFlow) accelerate
- The finding that the open-source nvidia-aiq stack achieves competitive parity with top proprietary systems, meaning "open infrastructure is viable for building competitive research systems"
- The information theory insight (from Data Processing Inequality) connecting the single-agent vs. multi-agent debate to a principled theoretical framework

The pipeline found arXiv:2604.02460 (the single-agent > multi-agent paper) but presents it as a standalone claim. The benchmark would have used it as evidence in a structured argument about when multi-agent architecture actually helps.

---

## 4. Actionability

### Pipeline verdicts (claims 26-28)

The pipeline produces three verdicts:
- **Adopt open_deep_research** (LangChain): "supervisor-researcher pattern with reflection, parallel dispatch, and iteration guards directly maps to Keystone's L1 AgentPool architecture; MIT license and LangGraph substrate make it the most reusable open-source component"
- **Adapt STORM/Co-STORM**: "perspective-guided question generation pattern and dynamic mind map are components worth incorporating, but STORM's Wikipedia-style output format... make it unsuitable as a drop-in"
- **Skip MetaGPT and AutoGen**: "neither provides reusable components specific to the research-synthesis-citation-evaluation pipeline Keystone requires"

These are directionally correct and grounded. The open_deep_research verdict is the best — it connects the architectural pattern to a specific Keystone component (L1 AgentPool) and cites the MIT license as a concrete reason.

### Benchmark USE/LEARN/SKIP matrix

The batch-1 matrix is substantially more detailed:

**USE directly (6 items):** GPT-Researcher's MCP server, Brave Search API, Exa API, Tavily API, SearXNG, LangGraph. Each has a one-sentence rationale that is specific and implementation-ready. "Brave Search API as the primary search provider — broadest index, best benchmarks, predictable pricing, production-mature."

**LEARN from (14 items):** Each LEARN entry specifies exactly what to steal and how. "199-Bio's Dynamic Outline Evolution (Phase 4.5) — restructure the report outline after evidence gathering to prevent specification lock-in." The pipeline has no equivalent of this. It tells you to "adapt" STORM but does not tell you which STORM components to extract or what to do with them.

**SKIP (7 items):** The benchmark names specific reasons for each skip. For the 199-bio search-cli: "1 GitHub star, Rust-only, no community; build custom search orchestration instead." For STORM as a runtime component: "development plateaued 14+ months ago, Wikipedia-centric design requires heavy rework." These specific rationales help a developer understand why the skip verdict was reached.

The pipeline has 3 verdicts at the level of system categories. The benchmark has 27 verdicts at the level of individual components. The granularity difference is roughly 9x.

---

## 5. Anti-Confirmatory Quality

This is the area where the pipeline is closest to matching — and in one respect, exceeds — the benchmark.

The pipeline contains three genuinely anti-confirmatory claims:

- **Claim 14 (arXiv:2604.02460):** "single-agent LLMs consistently match or outperform multi-agent systems on multi-hop reasoning tasks when reasoning token budgets are held equal... grounding the result in the Data Processing Inequality." The pipeline found an April 2026 paper that directly challenges the multi-agent premise of the entire Keystone system. That is real anti-confirmatory research.
- **Claim 15 (MDPI Electronics 2025):** "the best-performing configuration was a single-agent strategy... achieving 100% recall, 70.4% precision, F1 of 82.6%... outperforming all multi-agent alternatives tested." Same direction.
- **Claim 20 (verdict on STORM):** acknowledges STORM's limitations directly in the verdict.

The batch-1 report handles counter-evidence differently. It acknowledges the failure modes (GPT-Researcher's hallucination heuristic, STORM's plateaued development, 199-Bio's cosmetic credibility scoring) but never presents a systematic challenge to the multi-agent thesis itself. The report was written to validate Keystone's architectural convictions — which were not yet challenged by the April 2026 Data Processing Inequality paper. The pipeline has a claim that, if taken seriously, should make Keystone's architects rethink the L1 multi-agent assumption.

However, the pipeline's anti-confirmatory claims are not integrated into any argument. Claim 14 appears as a peer item alongside GPT-Researcher's star count and STORM's benchmarks. A human analyst reading the pipeline output has to supply the inference: "this is important and challenges our architecture." The benchmark would have used this finding as the opening of a section titled "The Single-Agent Challenge" and drawn implications.

---

## 6. Absence Report Quality

The pipeline produces 9 structured absence items. The benchmark produces none (no equivalent section exists).

The pipeline's best absence items are genuine and decision-relevant:

- "No published benchmark directly evaluates consulting-grade analytical quality (MECE structure, hypothesis-driven framing, executive communication, actionability)... all existing benchmarks measure factual accuracy, citation quality, or report breadth — not strategic analytical structure." This is a true gap with direct implications for Keystone's evaluator design.
- "No evidence found of any multi-agent research system that has been validated for MBB-grade consulting deliverable quality (partner review, client acceptance) in documented case studies." This is the most important absence — it means Keystone is genuinely building something that doesn't have a proven analogue.
- "No rigorous comparison of fractal/recursive multi-agent architectures (Cranot-style) vs. breadth-first scatter-gather architectures (GPT-Researcher style) on research depth metrics." This points to an open architectural question with no empirical resolution.
- "No primary source paper or technical documentation from OpenAI was found describing the internal architecture of Deep Research." Accurately flags the epistemic limitation of all OpenAI architecture claims.

The one weakness in the absence report: some items describe expected gaps rather than actively searched-for and not-found evidence. "No documentation found on how any of these systems handles proprietary or non-public data" is legitimate but slightly generic. A stronger absence report would specify the search queries run to find this.

The benchmark's lack of any absence report is a genuine gap. The pipeline wins this dimension.

---

## 7. Prompt Quality Gap

This is the single largest driver of the quality difference and deserves careful analysis.

### The A1 prompt (benchmark)

The A1 prompt in RESEARCH-PROMPTS-FINAL.md is 850+ words of structured research guidance. Its key structural properties:

**Named systems with sub-questions:** "GPT-Researcher... I need to understand its full pipeline, how it handles quality control, and where its architecture breaks down for consulting-grade output." "199-Biotechnologies... I need to understand its actual output quality, whether its credibility scoring is meaningful or cosmetic, and what its failure modes are." Each system comes with a research agenda that tells the model what to evaluate, not just what to find.

**Named search topics with specific leads:** "Exa ($85M Series B, built its own index with 1B+ people, 50M+ companies, 100M+ papers, sub-450ms latency)." This is not a search query — it is pre-populated context that the researcher can verify and extend. The model doesn't start from zero.

**Explicit analytical framework:** "For each system, analyze: (1) Architecture... (2) Quality control... Is quality enforced structurally or through prompt instructions? (3) Search infrastructure... (4) Strengths... (5) Weaknesses... (6) Components we could directly use... (7) Maintenance trajectory." The 7-dimension framework for every system produces structured comparative analysis.

**Attached context files:** CAPSTONE-PLAN-v2.md and SYNTHESIS.md were attached. The model knew what it was researching for — a specific six-layer pipeline architecture — and could evaluate each system against that architecture's requirements.

**The key question:** "Which existing components should we compose rather than rebuild, and where do we need to build something genuinely new?" This frames the entire research task as a build vs. buy decision, which generates the USE/LEARN/SKIP matrix.

### The pipeline's task description

The deep_research.md prompt template is well-structured. The actual task description the agent received was approximately this form:

```
ENGAGEMENT CONTEXT:
- Title: Multi-Agent Research & Analysis Systems
- Client Decision Context: [~1 sentence]
- Quality Standard: [~1 sentence]

RESEARCH QUESTIONS: [2-3 questions]

YOUR SPECIFIC TASK: [~50 words describing the topic]

ACCEPTANCE CRITERIA: [~3-4 items]
```

The template includes good research instructions (cross-reference, follow citations, note absences, seek contrarian evidence). But the task description itself — generated by L0 from a question string — had no named systems, no sub-questions per system, no analytical framework for evaluation, and no architectural context. The model had to decide from scratch what systems to research and what questions to ask about them.

### Quantified impact

The benchmark had 8 named systems to investigate with 7 analysis dimensions each = 56 specified research sub-tasks. The pipeline agent self-generated its research agenda from a blank slate. The pipeline found 15 systems. But it generated a flatter, more encyclopedic coverage rather than the 7-dimension comparative analysis the prompt demanded of the benchmark.

The benchmark prompt's "Is quality enforced structurally or through prompt instructions?" is a single question that generates the most important strategic insight in the entire report. The pipeline never asks this question and therefore never generates the "every system enforces quality through prompts, not architecture" synthesis.

---

## 8. Structural Format

### JSON claims array

The pipeline output is a flat JSON array of 28 claims, each with text, evidence, citations, confidence, and caveats. This structure has genuine advantages:

- Every claim is independently verifiable with real URLs
- Confidence scores allow downstream filtering
- Claims can be compared programmatically
- The structure is machine-readable for the CitationProcessor, L1.5 Deliberation, and L4 Evaluator

But the atomic claim structure creates analytical losses:

**Hierarchy loss:** The 28 claims have no parent-child relationships. Claim 1 (GPT-Researcher architecture) and Claim 19 (LangGraph patterns) are peers. A reader cannot tell which findings are primary (the ones that should drive decisions) and which are supporting detail.

**Narrative loss:** The benchmark flows from "landscape survey" to "patterns worth stealing" to "what must be built new" — a logical sequence that builds an argument. The pipeline's claims are in rough research order (systems first, then failure modes, then verdicts), but there is no sectioning, no transitions, and no cumulative argument.

**Implicit claim loss:** The benchmark's most important strategic claim — "The research agent landscape in March 2026 is rich in research generation infrastructure and poor in research evaluation infrastructure. This asymmetry is Keystone's strategic opportunity." — is a synthetic observation that does not map to any single source. It emerges from the synthesis of all the individual system assessments. The pipeline's JSON format can only emit claims grounded in specific sources.

**McKinsey-stack loss:** A consulting brief has a Situation-Complication-Resolution structure, a recommendation pyramid (headline → supporting logic → evidence), and an executive summary. None of this is producible by a JSON array of equal-weight claims.

The MarkdownRenderer can convert claims to prose, but it cannot reconstruct the analytical hierarchy that the JSON format never captured. This is a lossy encoding problem — information is destroyed at the claim-generation step, not at the rendering step.

---

## 9. Recency and Accuracy

### Recency

The pipeline has a clear advantage on the most recent sources:
- Gemini Deep Research Max (April 21, 2026) — found day-of-run
- arXiv:2604.02460 (April 2026) — post-benchmark
- Microsoft Agent Framework absorbing AutoGen (October 2025) — post-benchmark
- LangChain open_deep_research (July 2025) — post-benchmark
- Databricks State of AI Agents 2026 — post-benchmark

The benchmark's GPT-Researcher star count (25.7K as of March 2026) differs from the pipeline's (26.6K as of April 2026) — plausible growth over one month.

### Accuracy concerns

Two claims in the pipeline output warrant scrutiny:

**Claim 7 (OpenAI Deep Research):** Sources this to a Medium analysis by Cobus Greyling — a secondary source describing OpenAI's architecture through reverse engineering. The benchmark acknowledges the same limitation. Both are forced to use secondary sources because OpenAI has not published a technical report. The pipeline correctly caveats: "OpenAI has not published a technical paper; architecture details come from third-party analysis."

**Claim 11 (CrewAI's MASLeak vulnerability >79%):** The evidence cites an academic security research paper alongside a commercial review article. The 79% figure is from a specific study and may not generalize to all CrewAI configurations. The caveat "Security vulnerabilities may be partially mitigatable through better system prompt design" is appropriate but understates the severity. The benchmark does not mention this security finding.

**Claim 10 (Cranot/deep-research, confidence 0.78):** The lowest-confidence claim in the output. No published benchmarks; all claims come from the maintainer's own documentation. The batch-1 benchmark correctly identifies that "multi-model ensembles... produces genuinely diverse perspectives because different model families have different training biases. This is fundamentally more robust than 199-Bio's persona prompting within a single model" — a strong positive claim about Cranot not validated by external evidence. The pipeline is appropriately more skeptical.

**Quality score uniformity:** Every source, whether arXiv:2402.14207 (NAACL 2024 peer-reviewed) or a Medium blog post, has `quality_score: 0.7`. This is a metadata gap. The pipeline's CitationProcessor should differentiate source authority, but as of this run, all 46 sources are treated as equal quality.

---

## 10. What Would Close the Gap

These recommendations are ordered by impact-to-effort ratio, not by implementation complexity.

### Priority 1: Research task specification depth (highest leverage, medium effort)

The single largest quality driver is the difference between a 50-word task description and an 850-word research agenda. The fix is to generate richer task specifications in L0 before they reach the research agents.

**Specific changes:**
- The `TaskGenerator` in L0 should produce, for each research task, a list of named entities to investigate (systems, papers, companies) and 4-7 evaluation dimensions per entity type. For a competitive landscape task, this means: name the 8-10 most important systems based on domain knowledge, then ask "for each: architecture, quality control mechanism, search infrastructure, maintenance health, and what Keystone should learn or avoid."
- The task `acceptance_criteria` should include at least one synthesis question — not just "find X" but "determine whether X is better characterized as Y or Z." Synthesis questions force the agent to do comparative analysis rather than enumeration.
- The task specification should include known leads — like the A1 prompt pre-populates Brave Search API details, Exa funding round, and Imbad0202's star count. Known leads let the agent verify and extend rather than discover from scratch, which produces deeper coverage per unit of search.

This change requires: modifying `TaskGenerator` to accept domain leads as input, extending the task model with `named_entities` and `evaluation_dimensions` fields, and updating the `deep_research.md` template to surface these in the prompt.

### Priority 2: Synthesis layer that produces hierarchical claims (high leverage, high effort)

The pipeline needs a post-L1 synthesis step that takes 28 atomic claims and produces a narrative hierarchy: thesis claim → supporting claims → evidence. This is different from the existing L1.5 Deliberation, which does cross-analyst aggregation of an already-flat structure.

**Specific changes:**
- Add a `NarrativeSynthesizer` component between L1 and L1.5. Input: flat claims array. Output: claim hierarchy with a top-level thesis, 3-5 major finding clusters, and supporting claims nested under each.
- The synthesis prompt should explicitly ask: "What is the single most important insight that emerges from these claims? What pattern connects more than half of the findings? Which findings are primary (decision-driving) vs. supporting (evidence for a primary claim)?"
- The synthesis output should map to a Situation-Complication-Resolution structure, not just a topic cluster.

Without this component, the MarkdownRenderer can never produce consulting-grade narrative because the hierarchy was never extracted.

### Priority 3: System health assessment per source/system (medium leverage, low effort)

The benchmark assesses STORM's "development plateaued since January 2025 — a classic academic project trajectory." The pipeline has no maintenance health assessment for any system.

**Specific changes:**
- Add an evaluation dimension to every system research task: "Maintenance trajectory: recent commits, community health, whether it's accelerating or plateauing."
- The `deep_research.md` template should explicitly instruct: "For each system evaluated, assess whether its development is accelerating, stable, or declining based on commit recency, community activity, and adoption signals."
- Map the health assessment to one of three tags: ACCELERATING / STABLE / DECLINING. This produces actionable signal (a DECLINING system is a skip candidate regardless of technical quality).

### Priority 4: Source quality differentiation (medium leverage, low effort)

Every source in the pipeline output has `quality_score: 0.7`. The CitationProcessor and L1.5 Deliberation cannot distinguish a peer-reviewed NAACL paper from a Medium blog post.

**Specific changes:**
- Replace the uniform 0.7 default with a rule-based quality tier: academic papers with DOIs or arXiv IDs get 0.9; government/regulatory sources get 0.85; official project documentation (GitHub READMEs, official docs) gets 0.75; industry analysis and blog posts get 0.6; self-reported (project's own README claims) gets 0.5.
- The L4 Evaluator's citation gate should penalize claims whose confidence exceeds the quality tier of their supporting sources.
- Surface the source tier in the claim's `caveats` field when the primary source is a blog post or self-reported document.

### Priority 5: Named-entity research coverage check (medium leverage, medium effort)

The batch-1 report covers DeerFlow, Imbad0202, and Weizhena — three systems named in the A1 prompt that the pipeline missed entirely. The pipeline self-selected its research agenda and chose differently.

**Specific changes:**
- The L0 task generator should produce a `required_coverage` list for competitive landscape tasks: named entities that must appear in the research output. If a claim does not mention a required entity, the task is considered incomplete and re-queued.
- The deep_research agent should receive this list explicitly: "These entities must be covered: [GPT-Researcher, STORM, 199-Bio, Cranot, DeerFlow, Imbad0202, Weizhena]. Do not submit output that does not address all of them."
- The `absence_report` format should specifically list required entities that were not found, not just topics searched unsuccessfully.

### Priority 6: Strategic framing in the task description (medium leverage, low effort)

The A1 prompt's key question — "Which existing components should we compose rather than rebuild?" — generates the USE/LEARN/SKIP matrix. The pipeline produced 3 verdict claims; the benchmark produced 27.

**Specific changes:**
- Every competitive landscape task should explicitly include a "build vs. compose" evaluation dimension: "For each system, determine whether Keystone should: USE directly (integrate without rebuilding), LEARN from (extract the pattern, build our own), or SKIP (not relevant or not production-ready)."
- The `acceptance_criteria` should require a structured decision table, not just individual verdicts. "Output must include a USE/LEARN/SKIP categorization for at minimum 8 systems with specific rationale for each category assignment."
- The synthesis prompt should include: "Produce a decision matrix with three columns: USE, LEARN, SKIP. Every system or component evaluated must appear in exactly one column."

### Priority 7: Anti-confirmatory claims as a structured pipeline requirement

The pipeline found the Data Processing Inequality paper (arXiv:2604.02460) and treated it as a peer claim alongside GPT-Researcher's star count. A consultant would have flagged it as a critical finding that challenges the engagement's premise.

**Specific changes:**
- Add a required `challenge_claims` array to the StructuredFinding output, distinct from the main `claims` array. Claims in this array must specifically address why the multi-agent approach might be wrong or when it fails.
- The synthesis stage should explicitly process `challenge_claims` before `claims` — a claim challenging the thesis should appear in the executive section, not buried at position 14 of 28.
- The L4 Evaluator should check that at least one `challenge_claim` with confidence >0.80 exists in every research finding. If absent, the evaluator should flag: "No high-confidence counter-evidence found — research may be confirmatory."

### Priority 8: Iterative research with gap-fill loops (high leverage, very high effort)

The batch-1 benchmark was produced through a multi-turn deep research session where the model could search → read → follow citations → search again. The pipeline runs one deep-mode session. For the level of coverage the benchmark achieved, the pipeline needs iterative research.

**Specific changes:**
- Implement a gap-fill loop: after the first research pass produces claims, run a gap-assessment prompt against the absence_report. For each absence item rated as "decision-critical," spawn a targeted research sub-agent to fill the gap.
- The gap-fill agent should receive: the existing claims (so it doesn't re-research what's already covered) and a specific research question derived from the absence item.
- Cap the loop at 2-3 iterations to prevent unbounded cost.

This is architecturally close to the LeadResearcher/SubResearcher pattern already built in the codebase (from the `c495d73` commit). The missing piece is the gap-assessment step that decides which absences merit a sub-agent.

---

## Summary Assessment

The pipeline's first run produced work that is:
- **Factually accurate** — claims are well-supported and appropriately caveated
- **Well-sourced** — 46 real URLs including primary academic papers
- **Timely** — found sources the benchmark literally could not have (April 2026 papers)
- **Anti-confirmatory** — challenged the multi-agent premise with peer-reviewed evidence the benchmark lacks
- **Structured** — the absence report is the pipeline's clearest advantage over the benchmark

The pipeline's work is not yet:
- **Analytically synthesized** — no cross-cutting thesis emerges from the 28 claims
- **Strategically actionable** — 3 system-level verdicts vs. 27 component-level verdicts
- **Narratively structured** — flat JSON array rather than Situation-Complication-Resolution hierarchy
- **Complete in coverage** — 3 of 8 named systems from the A1 prompt were missed (DeerFlow, Imbad0202, Weizhena)
- **Depth-differentiated** — each system gets 2-4 sentences regardless of its strategic importance

The gap is not a model capability failure. It is a prompt specification failure (50-word task vs. 850-word research agenda) combined with an output structure constraint (atomic claims vs. hierarchical narrative) and a missing synthesis layer (no component converts claims → argument → brief).

All three root causes are buildable. Of the eight priorities above, Priority 1 (task specification depth) and Priority 3 (system health assessment) are low-hanging fruit achievable in a single session. Priority 2 (narrative synthesis layer) is the architectural investment that unlocks the rest — without it, the MarkdownRenderer will continue to produce formatted claim lists rather than consulting briefs.
