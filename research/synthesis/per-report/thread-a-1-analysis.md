# Report 1: A1 — Multi-Agent Research & Analysis Systems

---

## Top Findings

**Finding 1: The generation-evaluation asymmetry is the strategic opportunity**
The research agent landscape in March 2026 is rich in research generation infrastructure and poor in research evaluation infrastructure. Every system reviewed — GPT-Researcher, STORM, 199-bio, Cranot, DeerFlow — enforces quality through prompts or probabilistic heuristics, not architecture. None has a structural veto mechanism with persistent learning. This asymmetry directly validates CAPSTONE-PLAN-v2.md's core conviction that the Evaluator is the highest-leverage component.
- Pipeline layer: L4 (Evaluator)
- Build implication: Keystone should compose generation infrastructure from existing components and invest original engineering in the Evaluator, Rejection Library, and Specification Engine.
- Evidence quality: Verified — benchmarks (DeepResearchGym 1,000 queries, DeepResearch Bench 100 PhD-level tasks), code inspection, GitHub commit analysis.

**Finding 2: Imbad0202's empirical proof that evaluation quality scales with investment**
The academic-research-skills system (10-stage pipeline) ran 100% reference/data/claim verification and caught 15 fabricated references. A post-publication audit then found 21 additional issues. This is a direct empirical demonstration: each additional evaluation pass finds more problems. The report draws the explicit conclusion — "more evaluation always produces more value" — which validates the 8-dimension rubric architecture and argues for multiple evaluation passes at different intensities.
- Pipeline layer: L4 (Evaluator), META
- Build implication: The tiered evaluation intensity model (Light/Standard/Deep) in CAPSTONE-PLAN-v2.md Section 5.5 is validated. Build the Deep tier from the start; it will always pay off on high-stakes outputs.
- Evidence quality: Credible — solo developer, small community, but the mechanism (find-more-when-you-look-more) is internally verified and logically sound.

**Finding 3: Cranot's typed knowledge graph with epistemic state tracking is a superior model for research state**
Cranot tracks research findings as typed nodes (Question, Answer, Insight, BlindSpot) with explicit state transitions (Unknown → Explored → Validated → Synthesized). The DETECT operation identifies blind spots structurally. This is fundamentally more robust than the flat pipeline model — it gives the Evaluator richer signal about what the research system knows, doesn't know, and has only partially explored.
- Pipeline layer: L1 (Research), L1.5 (Deliberation), L4 (Evaluator)
- Build implication: The confidence map in CAPSTONE-PLAN-v2.md Section 4.3 should be implemented as an epistemic state graph, not a flat JSON structure. The "absence report" concept in the plan maps to BlindSpot node detection.
- Evidence quality: Credible — active development, 202 stars, working code, but no independent benchmark.

**Finding 4: Specialized multi-agent systems beat all major commercial platforms by 8-10 RACE points**
DeepResearch Bench (100 PhD-level tasks, 22 fields) shows nvidia-aiq (55.95 RACE) and CellCog Max (56.13) leading over OpenAI Deep Research (46.45) and Claude Research (45.00). The delta is 8-10 points — meaningful. Open-source multi-agent architecture achieves this on Apache-2.0 with composable infrastructure. The conclusion is not that commercial products are bad but that purpose-built multi-agent architecture with specialized evaluation is viable and competitive.
- Pipeline layer: All layers (competitive positioning)
- Build implication: Keystone's target should be >50 RACE with >90% citation accuracy — a combination no current system achieves. The Evaluator and Rejection Library are the path to get there.
- Evidence quality: Verified — public benchmark leaderboard, multiple systems independently evaluated.

**Finding 5: Information coverage (Key Point Recall) is the hardest dimension, not linguistic quality**
CMU's DeepResearchGym found that even top systems score significantly higher on Clarity and Insight than on Key Point Recall. "Linguistic fluency has outpaced comprehensive content synthesis." Systems write well but miss important information. This is the failure mode the Evaluator must be designed to catch — absence detection, not just quality of what's present.
- Pipeline layer: L4 (Evaluator), L1.5 (Deliberation)
- Build implication: The "Completeness" dimension of the 8-dimension rubric (currently 10% weight) may deserve higher weight given this finding. The absence report concept in CAPSTONE-PLAN-v2.md directly addresses this gap.
- Evidence quality: Verified — CMU's DeepResearchGym, 1,000 complex queries.

---

## Tool/Framework Verdicts

**GPT-Researcher (assafelovic/gpt-researcher)**
- v3.4.2, 25.7K stars, Apache-2.0, active development
- Planner-executor-publisher pipeline, parallel search against 20+ sources, three-tier LLM strategy, CMU benchmark leader
- Verdict: INTEGRATE (via MCP server only, do not build on its quality control layer)
- Justification: Use gptr-mcp as a callable research backend for L1 agents — it handles parallel search and initial synthesis at proven quality levels — but never rely on its ReviewerAgent (prompt-based, no structural gate) as Keystone's Evaluator.

**STORM (stanford-oval/storm)**
- ~14K stars, NAACL 2024, plateaued since January 2025
- Multi-perspective conversation simulation, 25% better article organization
- Verdict: LEARN (perspective discovery mechanism only)
- Justification: The pattern of auto-mining analytical angles before deliberation enriches L0 Specification Engine; STORM itself is unsuitable as a runtime component due to plateaued development and Wikipedia-centric design.

**199-Biotechnologies deep-research-skill**
- 58 stars, v2.3.1, Claude-locked
- 8.5-phase pipeline with validate_report.py, verify_citations.py, multi-persona red teaming
- Verdict: LEARN (patterns and structural validation scripts, not the dependency)
- Justification: Dynamic Outline Evolution, citation verification scripts, and Devil's Advocate pattern are directly applicable to L4 Evaluator design, but the system is Claude-locked and has no community — use as design reference only.

**Cranot/deep-research**
- 202 stars, active
- Typed knowledge graphs, epistemic state tracking, multi-model ensemble
- Verdict: LEARN (epistemic state model, DETECT operation)
- Justification: The typed knowledge graph with state transitions is the best model for representing research state in L1.5 Deliberation, but the codebase lacks community support for direct integration.

**DeerFlow 2.0 (ByteDance)**
- 39.1K stars, February 2026, LangGraph-based
- 9 specialized nodes, Docker-sandboxed, persistent memory
- Verdict: LEARN (orchestration patterns only)
- Justification: Proves LangGraph handles production-grade orchestration at scale and demonstrates progressive skill loading — useful for L0/L1 design — but ByteDance provenance creates jurisdictional risk and the system has no evaluator, deliberation, or specification engine.

**Imbad0202/academic-research-skills**
- 5 stars, solo developer, Claude-locked
- 10-stage pipeline, 100% reference verification, Devil's Advocate, SCR protocol
- Verdict: LEARN (design reference for Evaluator)
- Justification: The empirical finding (15 fabricated references caught, 21 more found in post-audit) is the strongest evidence available that evaluation investment directly improves quality; but the implementation is not production-viable.

**Weizhena/Deep-Research-skills**
- 4 stars, solo developer
- Items × Fields matrix specification model
- Verdict: LEARN (specification model concept only)
- Justification: The Items × Fields matrix is a clean, extensible way to model research scope in the L0 Specification Engine, but the codebase itself has no community support.

**Brave Search API**
- 35B+ page index, $5/1K requests, highest AIMultiple benchmark score (14.89), SOC 2 Type II
- Verdict: INTEGRATE
- Justification: Primary discovery layer for L1 Research Agents — broadest independent index, best benchmarks, predictable pricing, no Google/Bing dependency.

**Exa**
- $85M Series B, $700M valuation, 1B+ people, 70M+ companies index, sub-450ms latency
- Verdict: INTEGRATE
- Justification: Primary semantic search layer for L1 Research Agents — "Find Similar" search and category-based search for companies/papers/people are capabilities no other provider offers.

**Tavily**
- Acquired by Nebius for $275M Feb 2026, /research endpoint GA
- Verdict: INTEGRATE (for content extraction; do not use /research endpoint as pipeline replacement)
- Justification: Use Tavily for search+extraction collapsing into one call for L1 agents; do not use the /research endpoint as it removes control over quality enforcement at L4.

**SearXNG**
- 27.4K stars, AGPL-3.0, self-hosted, free
- Verdict: INTEGRATE (as free fallback and development layer)
- Justification: Zero-cost development and backup search layer for L1 agents during iteration; eliminates API costs before production validation.

**LangGraph**
- 24K stars, Elastic-2.0 for API, production-validated at NVIDIA
- Verdict: INTEGRATE (patterns and orchestration backbone)
- Justification: DeerFlow 2.0 proves LangGraph handles production-grade orchestration at 39K-star maturity; typed state, conditional edges, and Send API for dynamic fan-out are the best-documented orchestration patterns and should serve as L0/L1 pipeline backbone.

---

## Contradictions with CAPSTONE-PLAN-v2.md

**Plan says:** The confidence map output from L1.5 Deliberation is a flat JSON structure with high/moderate/contested/gaps arrays.
**Evidence shows:** Cranot's epistemic state graph (typed nodes with state transitions) is a substantially richer model that enables structural detection of blind spots and contradictions — not just categorization of findings. The flat JSON is readable but loses structural relationships between claims.
**Follow:** Adopt the epistemic state graph model over the flat JSON. The plan's confidence map concept is correct; the data structure should be upgraded. This is an improvement, not a contradiction.

**Plan says:** "LangGraph for orchestration" is listed in the USE category.
**Evidence shows:** The report recommends using LangGraph for orchestration patterns but flags security concerns (3 CVEs in March 2026, including CVSS 9.3) and Elastic-2.0 licensing as concerns for production use.
**Follow:** Use LangGraph patterns and, if adopting the library directly, pin versions and monitor CVE advisories. The concerns are real but manageable; they don't invalidate LangGraph as the orchestration foundation.

**Plan says:** STORM is listed as a potential L1.5 Deliberation inspiration.
**Evidence shows:** STORM's perspectives are cooperative information-gathering heuristics, not adversarial analytical positions. They generate breadth, not contested depth. Development has plateaued since January 2025. STORM does not map to Keystone's Bull/Bear/Consensus deliberation model.
**Follow:** The report correctly identifies that STORM's perspective discovery mechanism (auto-mining analytical angles) is worth learning, but STORM itself is unsuitable as a runtime component. Follow the evidence — limit STORM's influence to early specification enrichment.

---

## Cross-Report Flags

**Reinforces A4 (Orchestration):** The finding that LangGraph handles production orchestration at scale (DeerFlow 39K stars, NVIDIA deployment) should align with A4's framework evaluation. Expect A4 to have a compatible verdict.

**Reinforces A2 (Evaluation):** The Imbad0202 empirical finding (evaluation quality scales with investment, 15+21 fabricated references caught) directly supports A2's expected finding that the Evaluator is the highest-leverage component. The two reports should converge on this conclusion.

**May contradict A4 on LangGraph:** This report recommends LangGraph as a USE (integrate), but A4 may come to a different conclusion based on security posture, licensing, or build-vs-buy analysis. Flag for synthesis.

**Reinforces A5 (Deep Research Tooling):** The search API verdict (Brave + Exa + Tavily as the production stack) should align with A5's tooling evaluation. Both reports are expected to converge on this search configuration.

**New architectural suggestion for all threads:** The epistemic state graph model (Cranot) as an upgrade to the flat confidence map is an architectural implication that could affect L1.5 Deliberation design across all threads.
