# CAPSTONE-PLAN-v2.md Changelog
*Changes applied: 2026-04-04 | Based on 16-report research synthesis*

Every change below is backed by specific findings from the research synthesis. Changes are marked in the plan with `[SYNTHESIS UPDATE]` tags.

---

## Change 1: Architecture Diagram -- Add CitationProcessor Stage

**Section:** 2 (Architecture Overview), architecture diagram
**What changed:** Added CitationProcessor as a named stage between L1 (Research) and L1.5 (Deliberation).
**Why:** Reports A5 and C3 independently found that Anthropic's own production multi-agent research system uses a dedicated CitationAgent for post-processing source attribution. Cross-agent corroboration (facts found independently by 2+ agents) should receive elevated confidence. Without this discrete stage, citation accuracy degrades at scale because agents lack visibility into each other's findings.
**Evidence:** A5 (Anthropic Engineering blog, 90.2% improvement), C3 (five-layer citation chain), D3 (PROV-AGENT W3C standard).
**Confidence:** Verified (Anthropic's own production architecture).
**What this enables:** Lossless citation chain from source to deliverable; cross-agent corroboration scoring; citation manifest for Evaluator verification.

---

## Change 2: Deliberation Phase Redesign

**Section:** 4.3 (The Deliberation Phase: From Findings to Thesis)
**What changed:** Replaced "structured multi-perspective debate with synthesis round" with two-phase architecture: (1) Independent Parallel Analysis using different analytical methodologies, (2) Structured Aggregation with curmudgeon challenge. Added cross-provider model diversity as a requirement. Replaced persona diversity (bull/bear) with methodological diversity (ACH, quantitative, adversarial, historical analogy).
**Why:** NeurIPS 2025 Spotlight ("Debate or Vote") formally proved that multi-agent debate forms a martingale -- more rounds consistently degrade performance. DMAD (ICLR 2025) proved methodological diversity outperforms persona diversity. Wu et al. found majority pressure suppresses independent correction below 5%. Google DeepMind found unstructured multi-agent networks amplify errors 17.2x.
**Evidence:** C2 (NeurIPS 2025 Spotlight, formal proof + empirical), D2 (DMAD ICLR 2025, Attention-MoA), C1 (DeepMind 17.2x amplification).
**Confidence:** Verified (NeurIPS Spotlight, ICLR, Google DeepMind peer-reviewed).
**What this enables:** Genuinely diverse analytical perspectives. Auditable Confidence Map. Prevention of conformity cascade. Architecturally sound deliberation that actually improves over aggregation-only.

---

## Change 3: Confidence Map Structure Upgrade

**Section:** 4.3, confidence map JSON
**What changed:** Upgraded from four-tier structure (high/moderate/contested/gaps) to five-tier taxonomy based on DiscoUQ: High (>80%), Moderate (60-80%), Weak (50-60%), Contested (<50%), Insufficient Evidence. Added DiscoUQ feature taxonomy (evidence overlap, minority argument strength, divergence depth, embedding geometry). Added ACH matrix structure.
**Why:** DiscoUQ achieves AUROC 0.802 vs 0.098 ECE for baselines. Largest improvements in the "weak disagreement" tier (50-60% agreement) -- exactly where simple voting fails. D3 found ACH matrix is the natural data structure. The plan's four-tier structure misses the "weak confidence" tier that is most important to instrument well.
**Evidence:** C2 (DiscoUQ, March 2026 preprint), D3 (ACH matrix from ICD 203).
**Confidence:** Credible (DiscoUQ is a preprint; ACH is Verified as CIA standard methodology).
**What this enables:** Computational grounding for confidence assessments. Detection of genuine disagreement vs. noise. Precise routing of claims to appropriate presentation format in deliverables.

---

## Change 4: Evaluator Architecture -- Five-Layer Stack

**Section:** 5 (The Evaluator), new subsection on evaluation stack architecture
**What changed:** Specified the Evaluator as a five-layer stack: (1) deterministic verification (FActScore, citation URL liveness, numerical consistency), (2) citation validation (CrossRef/Semantic Scholar existence checks as pre-rubric binary gate), (3) multi-rubric scoring (Prometheus 2 with decomposed 10-dimension rubric, separate prompt per dimension), (4) process trajectory evaluation (Agent-as-a-Judge), (5) diverse judge ensemble (PoLL 2-3 models from different families). Added pre-rubric gate: any fabricated citation causes immediate rejection. Added requirement: never score multiple dimensions in a single prompt.
**Why:** SOS-Bench (152K data points, ICLR 2025) proved holistic LLM judging systematically rewards style over substance (96% loss from sarcasm vs. 13% from factual errors). Single LLM judges achieve only 60-68% expert agreement in specialized domains. CALM identified 12 bias types. Deloitte incidents proved citation fabrication requires binary gate, not scoring.
**Evidence:** A2 (SOS-Bench, CALM, "Play Favorites"), B4 (28-failure-mode taxonomy, five-layer stack specification), D2 (60-68% ceiling), B1 (Deloitte incidents), D1 (0.80+ Spearman calibration standard).
**Confidence:** Verified (all key findings from ICLR 2025 peer-reviewed papers).
**What this enables:** Evaluation that resists style-over-substance bias. Ungameable deterministic foundation. Multi-model bias mitigation. Binary gate for citation integrity.

---

## Change 5: Rubric Expanded to 10 Dimensions

**Section:** 5.3 (The Eight-Dimension Judgment Rubric)
**What changed:** Added two new dimensions: Evaluative Surprise (5%) and Calibrated Confidence (5%). Adjusted weights: Analytical Depth 15%->12%, Completeness 10%->8%. Added evaluation type column (machine-checkable / expert-checkable / judgment-dependent). Added sub-criteria: trendslop detection in Actionability, deletion test in Completeness, precision calibration in Quantitative Rigor, ICD 203 probability language in Calibrated Confidence, counterfactual deletion test in Intent Alignment.
**Why:** B3 found taste is 65% decomposable into dimensions and 35% holistic. The two new dimensions address the conscious-competence ceiling (Evaluative Surprise detects competent mediocrity) and calibrated uncertainty expression (Calibrated Confidence operationalizes ICD 203). B1/B2 independently found trendslop is a structural LLM bias (15K+ trials, HBR March 2026). B2 found information overload actively degrades decisions (Federal Reserve research).
**Evidence:** B3 (Dreyfus model, Jonnson & Balan 2018 meta-analysis), B1 (HBR March 2026 trendslop study), B2 (counterfactual deletion test, ICD 203), B4 (absence failures 2x more common than hallucinations).
**Confidence:** Verified for trendslop (named researchers, 15K+ trials). Credible for Evaluative Surprise (Stripe Press "Tacit" docuseries, practitioner research). Verified for ICD 203 (US government directive).
**What this enables:** Detection of competent mediocrity. Calibrated uncertainty expression. Anti-trendslop enforcement. Information overload penalty.

---

## Change 6: Evaluator Calibration Target Quantified

**Section:** 5.4 (Calibration Against Keystone Standards)
**What changed:** Added specific calibration threshold: 0.80+ Spearman correlation from 100-200 expert-scored samples. Made this a binary gate before the Evaluator is considered production-ready. Added requirement for continuous re-calibration (every 5-10 engagements, not one-time setup). Added Cohen's Kappa tracking between human and automated scores.
**Why:** D1 established this as Anthropic's own production standard ("Demystifying Evals for AI Agents," January 2026). Without hitting this threshold, automated evaluator scores are noise, not signal. B3 found that without systematic expert calibration, the Evaluator drifts toward rewarding mediocrity.
**Evidence:** D1 (Anthropic production standard), B3 (Ericsson 3F loop, CodeRabbit 1.7x issues data), A2 (AISI Cohen's Kappa 0.52 for automated graders).
**Confidence:** Verified (Anthropic published standard).
**What this enables:** Concrete, measurable quality gate for the Evaluator itself. Prevents evaluator drift. Provides the calibration data needed for the self-improvement loop.

---

## Change 7: Two-Pass Evaluation Architecture

**Section:** 5 (new subsection following rubric)
**What changed:** Added three-pass evaluation flow: (1) dimensional scoring (10-dimension rubric, separate prompt per dimension), (2) holistic gestalt overlay (+-5-10% adjustment for emergent quality signals that dimensional scoring misses), (3) Observation Library negative-space scan (anti-pattern check against accumulated constraints). Added Kahneman noise audit: score outputs using multiple independent passes and adopt the lower score when passes diverge.
**Why:** B3 found evaluation is 65% dimensional, 35% holistic. The Dreyfus model warns that rubrics alone create a ceiling at competence level without reaching proficiency. B3 found the Observation Library is more important as a real-time evaluation mechanism than as a retrospective learning tool. B2 found noise audit via parallel evaluation implements Kahneman's decision hygiene.
**Evidence:** B3 (Jonnson & Balan inter-rater agreement, Dreyfus model, Heuer's disconfirmation principle), B2 (Kahneman Noise framework, ~4% ChatGPT performance variation).
**Confidence:** Verified (published meta-analysis, established assessment research).
**What this enables:** Detection of emergent quality beyond dimensional criteria. Architectural implementation of "taste." Noise reduction in evaluation scores.

---

## Change 8: Cross-Model Evaluation Requirement

**Section:** 5 (added to Evaluator architecture)
**What changed:** Added mandatory requirement: the primary generation model cannot be used as the primary evaluation model. If Claude generates, evaluation must include at least one judge from a different model family (GPT, Gemini). Cross-provider model diversity specified for evaluation ensemble.
**Why:** "Play Favorites" (2025) identified a causal mechanism: models favor text with lower perplexity, and their own outputs have the lowest perplexity. CALM found self-enhancement bias correlates with self-recognition capability. Google FACTS Grounding benchmark explicitly uses mixed judges. Claude-3.5 has 39% bandwagon susceptibility.
**Evidence:** A2 ("Play Favorites" causal mechanism), B4 (CALM 12 bias types, Claude-3.5 specific vulnerabilities), D2 (PoLL diverse panel pattern).
**Confidence:** Verified (peer-reviewed, causal mechanism identified).
**What this enables:** Breaks the perplexity-based self-evaluation bias. Reduces systematic scoring inflation on own outputs.

---

## Change 9: Observation Library (Expanded Rejection Library)

**Section:** 7.1 (The Rejection Library)
**What changed:** Expanded scope from rejections-only to full Observation Library. Captures all tool call outcomes (successes and failures), detects patterns in both directions, promotes validated patterns to skills via instinct-to-skill pipeline. Added three-category taxonomy: Category 1 (structural failures, machine-checkable), Category 2 (analytical failures, expert-checkable), Category 3 (judgment failures, human-calibrated). Added saturation-breaking mechanisms: domain expansion, adversarial probing, deliberate hard cases, periodic human review.
**Why:** D1 found ECC's instinct-to-skill pipeline captures every tool call at 100% reliability and is more granular than rejection-only capture. B3 found quality is better defined by what it excludes than what it includes (Heuer's disconfirmation, biological taste research). D2 found self-improvement saturates after 2-3 iterations without new failure signals (ICLR 2025 Oral). A3 found Goodhart's Law at 19.3%.
**Evidence:** D1 (ECC 112K stars, production-deployed), B3 (Heuer ACH, Tetlock superforecasting), D2 ("Mind the Gap" ICLR 2025 Oral), A3 (Goodhart ICLR 2024).
**Confidence:** Verified for saturation ceiling (ICLR Oral). Credible for ECC instinct pipeline (production but not peer-reviewed).
**What this enables:** Captures positive patterns (reinforcement, not just correction). Prevents Goodhart gaming through multi-metric selection. Explicit mechanism for escaping improvement saturation.

---

## Change 10: Agent Isolation Strengthened with Empirical Evidence

**Section:** 4.1 (Parallel Research Execution Under Strict Isolation)
**What changed:** Added AgentLeak empirical evidence: 68.8% inter-agent data leakage in standard frameworks, 46.7% from shared memory. Added advisory file locks and write-ahead logging for crash recovery. Added per-agent tool specialization requirement (3-5 domain-specific tools, not full suite). Added model mixing strategy (Opus for L0/L4, Sonnet for L1, Haiku for extraction).
**Why:** A4 found that no framework provides mechanisms to intercept inter-agent messages. Anthropic's own finding: "a model loaded with 50 different tools performs worse than specialized agents with 5 focused tools." Anthropic's multi-agent system: Opus as lead, Sonnet for subagents, 40% cost reduction.
**Evidence:** A4 (AgentLeak benchmark, 4,979 traces, February 2026), A5 (Anthropic tool specialization finding), A4 (Anthropic model mixing, 90.2% improvement).
**Confidence:** Verified (peer-reviewed benchmark, Anthropic Engineering blog).
**What this enables:** Measured prevention of data leakage. Cost-optimized model deployment. Performance-optimized tool loading.

---

## Change 11: Orchestration Architecture Specified

**Section:** 12 (Implementation Roadmap), with implications for Section 2
**What changed:** Specified custom orchestration architecture: PydanticAI for agent definition and type-safe handoff contracts, Temporal for durable execution with crash recovery and human-in-the-loop gates, MCP for tool integration with gateway architecture, AG-UI for output streaming. Replaced implicit "pick a framework" with explicit build-custom rationale.
**Why:** A4 found no existing framework natively supports Keystone's combination of requirements. AgentLeak showed bolting isolation onto frameworks fails 46-69%. The framework layer is thinning (AWS Strands: "We no longer needed complex orchestration"). Durable value lies in specification, evaluation, and observability.
**Evidence:** A4 (AgentLeak, framework-by-framework evaluation, "framework layer is thinning"), C1 (Claude Code as native deployment surface).
**Confidence:** Verified (benchmark data, documented framework limitations).
**What this enables:** Strict isolation guaranteed by architecture. Crash recovery for long-running research. Human-in-the-loop gates at pipeline boundaries. Type-safe handoff contracts.

---

## Change 12: Retrieval Architecture Specified

**Section:** 6.2 (Unified Retrieval Architecture) and new retrieval subsections
**What changed:** Added hybrid search (dense + BM25 + RRF) as non-negotiable for financial documents. Specified pgvector + pgvectorscale as primary vector store. Added Semantic Router for <5ms query routing. Added dual-path retrieval (Text2SQL for quantitative, vector for qualitative). Added Docling for structure-aware PDF parsing. Added Bifrost for dual-layer caching with per-source TTLs. Added source quality scoring framework (Admiralty Code + composite formula).
**Why:** C4 found plan-based multi-hop retrieval is 40% vs. 100% accuracy on FRAMES benchmark. Hybrid search improves NDCG by 26-31%. pgvector achieves 28x lower latency than Pinecone at 75% less cost. Structure-aware chunking achieves 87.7% vs. poor results from fixed-size chunking.
**Evidence:** C4 (FRAMES benchmark, BEIR aggregate, Timescale pgvector benchmarks, Docling Enterprise RAG Challenge).
**Confidence:** Verified (multiple independent benchmarks).
**What this enables:** Correct retrieval on complex multi-hop consulting queries. Financial document parsing that preserves table structure. Cost-effective vector search with SQL join capability.

---

## Change 13: Task-Type Field Added to research-tasks.json

**Section:** 3.6 (Research Initiation)
**What changed:** Added "type" field to each task: "estimative" (forward-looking, probabilistic) or "current" (situation updates, timeliness). Evaluator applies type-specific weight profiles. Added "target_decision_usefulness" field (Level 3 minimum for client-facing).
**Why:** B2 found ICD 203's distinction between estimative and current intelligence requires different quality criteria. Market sizing requires uncertainty quantification as primary; competitive monitoring requires timeliness. B2's five-level decision-usefulness rubric provides the scoring scaffold.
**Evidence:** B2 (ICD 203 Verified; five-level decision-usefulness rubric Credible).
**Confidence:** Verified for ICD 203 distinction. Credible for five-level rubric design.
**What this enables:** Type-appropriate evaluation. Different weight profiles for different research tasks. Minimum decision-usefulness threshold enforcement.

---

## Change 14: Causal Inference as Phase 2 Capability

**Section:** 12.2 (Phase 2) and 4.4 (Content Structuring)
**What changed:** Added causal inference agent using DoWhy as a Phase 2 deliverable. L2 Content Structuring designed in Phase 1 to accept causal analysis outputs as first-class input type.
**Why:** D3 found CausalAgent (ACM IUI 2026) demonstrates end-to-end causal inference using Keystone's exact tech stack (LangGraph + RAG + MCP). MATMCD achieves 66.7% reduction in causal errors. No existing consulting AI tool provides causal analysis -- this is white-space capability.
**Evidence:** D3 (CausalAgent Verified, DoWhy 1M+ installs, MATMCD ACL 2025 peer-reviewed).
**Confidence:** Verified (peer-reviewed, production libraries).
**What this enables:** Transition from correlation-reporting to mechanism-identification. Genuine capability expansion beyond any competitor. Confounded relationship detection.

---

## Change 15: Anti-Slop Enforcement Structured

**Section:** 5.8 (The Anti-Slop Standard)
**What changed:** Added Antislop Sampler reference (8K+ pattern suppression). Structured anti-slop as a dedicated Evaluator sub-check (not a separate pipeline) with triggered Redraft Specialist subagent. Added specific detection signals: generic openings, listicle structures, excessive hedging, buzzwords, AI-characteristic patterns appearing 1000x more frequently than in human text.
**Why:** C3 found the four-agent ASS v3.0 pipeline maps to L3/L4 interaction. The key insight: drafter stays intentionally naive while detector is maximally critical. Antislop Sampler achieves 90% slop reduction while maintaining benchmark performance.
**Evidence:** C3 (Antislop Sampler arXiv benchmarked; ASS v3.0 GitHub implementation Credible).
**Confidence:** Verified for Antislop Sampler. Credible for ASS pipeline.
**What this enables:** Structural slop detection. Triggered redraft without full regeneration. Pattern-based enforcement beyond prompt instructions.

---

## Change 16: Cost Model Validated and Documented

**Section:** 12 (Implementation Roadmap), new cost subsection
**What changed:** Added validated cost model: $7-$85/engagement with optimization (prompt caching, Batch API, model tiering). 0.3-2.7% of engagement revenue. Verification consumes 72% of tokens. Optimize for quality, not cost.
**Why:** A5 calculated costs from Anthropic's published API rates. A4 found verification dominates token usage. Combined, the economic case for full deployment is closed.
**Evidence:** A5 (reproducible cost model from published rates), A4 (ICLR 2025 verification cost finding).
**Confidence:** Verified (independently reproducible).
**What this enables:** Business case validation. Informed infrastructure budgeting. Decision to optimize for quality over cost savings.

---

## Change 17: Claim-Level Intermediate Representations at L1->L2 Handoff

**Section:** 4.4 (Content Structuring via Sprint Contracts)
**What changed:** Added requirement that L2 receives synthesized claims (not raw agent outputs). Handoff contract between L1 and L2 defined at the claim level: each claim includes source_chunk_ids, confidence, corroboration count, and provenance chain. Referenced STORM finding that outline quality predicts final output quality (+25% perceived organization).
**Why:** D2 found deep research quality depends on claim-level intermediate representations and DAG structure, not report length (Microsoft Research, ICLR 2026). Systems that separate claim synthesis from report generation produce higher-quality output.
**Evidence:** D2 (Microsoft Research "Characterizing Deep Research," ICLR 2026; STORM NAACL 2024).
**Confidence:** Verified (peer-reviewed).
**What this enables:** Structured handoff between research and structuring. Claim-level citation tracing. Quality metrics at the claim level, not just the section level.

---

## Summary of Changes

| # | Section | Nature | Key Evidence | Confidence |
|---|---|---|---|---|
| 1 | 2 (Architecture) | Addition: CitationProcessor | A5, C3, D3 | Verified |
| 2 | 4.3 (Deliberation) | Redesign: debate -> aggregation | C2, D2, C1 | Verified |
| 3 | 4.3 (Confidence Map) | Upgrade: 4-tier -> 5-tier + ACH | C2, D3 | Credible/Verified |
| 4 | 5 (Evaluator) | Addition: five-layer stack | A2, B4, D2 | Verified |
| 5 | 5.3 (Rubric) | Expansion: 8 -> 10 dimensions | B3, B1, B2 | Verified/Credible |
| 6 | 5.4 (Calibration) | Addition: 0.80+ Spearman target | D1 | Verified |
| 7 | 5 (Evaluation flow) | Addition: three-pass architecture | B3, B2 | Verified |
| 8 | 5 (Cross-model) | Addition: mandatory cross-model | A2, B4 | Verified |
| 9 | 7.1 (Rejection Library) | Expansion: Observation Library | D1, B3, D2, A3 | Verified/Credible |
| 10 | 4.1 (Isolation) | Strengthening with empirical data | A4 | Verified |
| 11 | 12 (Orchestration) | Specification: custom build | A4, C1 | Verified |
| 12 | 6.2 (Retrieval) | Specification: hybrid search + pgvector | C4 | Verified |
| 13 | 3.6 (Task format) | Addition: type + decision-usefulness | B2 | Verified |
| 14 | 12.2 (Phase 2) | Addition: causal inference | D3 | Verified |
| 15 | 5.8 (Anti-slop) | Specification: structured enforcement | C3 | Verified/Credible |
| 16 | 12 (Cost) | Addition: validated cost model | A5, A4 | Verified |
| 17 | 4.4 (Handoff) | Addition: claim-level representations | D2 | Verified |
