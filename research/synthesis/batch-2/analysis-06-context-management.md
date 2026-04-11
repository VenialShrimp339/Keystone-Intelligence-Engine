# Analysis: Report 06 — Context Management
*Analyzed: 2026-04-05 | Priority: Tier 2 (HIGH) | Report quality: high*

---

## Executive Summary

This report is the most directly actionable of the Batch 2 set. It answers the four report-specific questions with empirical depth and delivers a concrete architecture for Keystone's context management. The report is well-sourced, temporally current (2025–2026), and has a high signal-to-noise ratio. The central verdict — context resets for Sonnet subagents, structured note-taking for the Opus orchestrator, file-based external memory as the continuity layer — aligns with and extends the existing plan's JIT context and scout/strike model. One finding substantially changes Component #3 scope and the Karpathy pattern is confirmed as a practical mechanism, not just a concept. The Factory.ai 37% retention figure is a critical failure-mode anchor that must inform testing.

**Three findings require immediate plan changes:** (1) Opus 4.6 largely eliminates context anxiety, which allows compaction rather than hard resets for the orchestrator — this simplifies the LeadResearcher implementation. (2) Selection over synthesis for contradiction resolution is empirically validated — this directly shapes the Deliberation phase design. (3) The "artifact bypass" pattern (structured summary + full external file) must be the canonical subagent output contract, not just a suggestion.

**No findings contradict settled decisions.** The report validates all 11 settled architectural decisions and reinforces Jack's Directives on Karpathy, iterative research, and the Specification Engine.

---

## Key Findings (ranked by implementation impact)

### 1. Opus 4.6 Eliminates Context Anxiety: Compaction Suffices for the Orchestrator

- **What:** Anthropic's March 2026 "Harness Design" post (Prithvi Rajasekaran) reports that Opus 4.6 "largely eliminated context anxiety," allowing the team to drop context resets entirely for that model. Context anxiety = models losing coherence on long tasks and prematurely wrapping up as they approach perceived context limits. For Sonnet subagents, context resets remain the correct strategy.
- **Evidence basis:** Anthropic internal engineering post, March 2026. Primary source from the model creator.
- **Evidence quality:** Verified — Anthropic's own engineering team reporting on their own production system.
- **Temporal check:** March 2026. Current. Matches the model versions in Keystone's target stack (Opus 4.6, Sonnet 4.6).
- **Conflicts with existing?** The existing plan specifies the LeadResearcher saves its plan to external Memory because context exceeds 200K. This remains correct but the motivation shifts: it's not anxiety prevention, it's capacity management between rounds. Compaction within a round is now validated as safe.
- **Verdict:** ADOPT immediately. Use Claude Agent SDK compaction for the Opus orchestrator within a single round. Between rounds, persist state to `research-state.md` and start the next round by reading that file — not to prevent anxiety but to handle context budget across rounds.
- **Justification:** This simplifies the LeadResearcher loop significantly. No need to engineer hard reset logic for the orchestrator. Sonnet subagents still get clean context windows per task (already settled in Directive #5 on agent isolation).
- **Keystone impact:** Component #5 (Specification Engine / orchestration). LeadResearcher implementation across rounds. Reduces implementation complexity.
- **Contradicts:** Nothing in the existing plan. Extends and clarifies it.

---

### 2. 13.9–85% Performance Degradation from Context Length Alone — Even With Perfect Retrieval

- **What:** Du et al. (October 2025) shows performance drops 13.9–85% purely from context length, independent of content quality. Even when irrelevant tokens are masked completely (replaced with whitespace), 30,000 masked tokens still cause at least 7.9% performance loss. NVIDIA's RULER benchmark confirms effective context is 50–65% of advertised window size, with production ceiling recommended at 70–80%. This is a "cognitive tax" that cannot be avoided by adding better content.
- **Evidence basis:** Peer-reviewed academic paper (Du et al.), independent benchmark (RULER/NVIDIA). Corroborated by Chroma Research (18 frontier LLMs, July 2025) and "Lost in the Middle" (Liu et al., Stanford/Meta).
- **Evidence quality:** Verified — multiple independent empirical studies with reproducible results.
- **Temporal check:** October 2025, July 2025, RULER independent. All post-2024. Highest confidence tier.
- **Conflicts with existing?** The existing plan mentions 200K truncation as a concern but does not operationalize specific utilization targets.
- **Verdict:** ADOPT. Encode the 70–80% utilization ceiling as a hard operational constraint, not a guideline. Specific targets: Opus 4.6 orchestrator — keep under 140–160K tokens (70–80% of 200K). Sonnet subagents — keep under 100K tokens for high accuracy. Position research plan and critical instructions at context start, most recent findings at context end. Never bury critical information in the middle.
- **Justification:** Multiple independent replication means this is not artifact. The RULER finding (only 50–65% of advertised window is effective) is especially important for Sonnet 4.6, whose effective context may be well below its theoretical maximum.
- **Keystone impact:** Component #7 (Research Agent context loading), Component #5 (Specification Engine orchestration). JIT context loading already addresses this; the finding quantifies why it matters and sets the operational threshold.
- **Contradicts:** Nothing. Quantifies and hardens the existing instinct to minimize agent context.

---

### 3. Artifact Bypass Pattern: Structured Summary Plus Full External File Is the Required Subagent Contract

- **What:** Subagents return a structured ~1,500-token summary (Pydantic schema: 3–7 key claims with confidence ratings, status, source references) AND write full research artifacts to an external file. The orchestrator reads the structured summary for synthesis and selectively reads the full artifact when needed. This is the "artifact bypass" pattern. Without it, multi-session information retention via LLM summarization is only 37% (Factory.ai). Aggressive compression causes 30–50 point drops in groundedness scores.
- **Evidence basis:** Anthropic's multi-agent system post (June 2025) for the 1,000–2,000 token condensed summary target. Factory.ai evaluation for the 37% retention figure. Academic QA benchmarks for the 30–50 point groundedness drop.
- **Evidence quality:** Factory.ai = credible (production evaluation, active company). Academic benchmarks = verified. Anthropic post = verified.
- **Temporal check:** June 2025, 2025 academic. Current.
- **Conflicts with existing?** The existing plan has agents return "condensed 1-2 page summaries." The artifact bypass pattern is the mechanical implementation of this — the existing plan assumed summaries were the only output. This finding says summaries alone are insufficient; full artifacts must be persisted externally.
- **Verdict:** ADOPT. This is a required change to the subagent output contract. The 37% retention figure is the failure mode to guard against — it means pure summarization loses two-thirds of the research. Pydantic schema for the structured output is the right enforcement mechanism.
- **Justification:** The 37% figure is alarming enough to treat as a hard constraint, not a risk. The artifact bypass pattern adds minimal overhead (agents write to a file in their working directory, which already exists per Directive #5 on filesystem-based isolation) while preserving full fidelity.
- **Keystone impact:** Component #7 (Research Agent output contract). Component #9 (Deliberation — has access to full artifacts, not just summaries, for synthesis). Component #2 (Citation data model — citations should reference artifact files, not just claim IDs). Changes the L1→L1.5 handoff spec.
- **Contradicts:** Nothing settled. Requires updating the handoff contract spec in PHASE-1-IMPLEMENTATION-SPEC.md Component #7.

---

### 4. Selection Over Synthesis for Contradictions — 81% Win Rate Versus 51.2%

- **What:** "When Agents Disagree" (2025) shows that judge-based selection (evaluate competing claims, pick best-supported) achieves 81% win rate against single-model baselines. Synthesis-based aggregation (blending contradictory candidates) scores only 51.2% — near chance. Synthesis "introduces incoherence, conflicting perspectives, and diluted arguments." KARMA multi-agent system's Conflict Resolution Agent: disabling it lowered correctness 4.9%.
- **Evidence basis:** Academic paper, 2025. KARMA system empirical evaluation. Quantified win rates.
- **Evidence quality:** Verified — empirical with specific numbers. Independent corroboration from KARMA.
- **Temporal check:** 2025. Current.
- **Conflicts with existing?** The existing plan has Deliberation as "independent parallel analysis + structured aggregation." "Structured aggregation" is ambiguous about selection vs. synthesis. This finding resolves the ambiguity: aggregation must be selection-based, not synthesis-based.
- **Verdict:** ADOPT. Deliberation aggregation must be implemented as claim-level selection (judge evaluates competing claims against source evidence, selects best-supported) not claim-level blending. The orchestrator is the judge. Subagents must provide explicit confidence scores and source counts — without these, evidence-weighted selection is impossible.
- **Justification:** The delta is too large to ignore (81% vs 51.2%). This is not a minor preference; blending produces near-random quality. The claim-level IR already in the plan (Settled Decision #6) provides the structure needed for selection. Confidence scores on claims enable evidence-weighted selection.
- **Keystone impact:** Component #9 (Deliberation design). The aggregation logic must be redesigned from blending to selection. Subagent output schema must include per-claim confidence scores and source counts as required fields.
- **Contradicts:** Nothing in settled decisions. Sharpens the meaning of "structured aggregation."

---

### 5. Karpathy Pattern Confirmed for Within-Engagement Knowledge — Three-Layer Implementation

- **What:** The report validates Karpathy's LLM Knowledge Bases pattern and provides a concrete three-layer implementation for research pipelines: `raw/` (full subagent outputs per round), `compiled/` (orchestrator-synthesized findings by topic), `INDEX.md` (auto-maintained by orchestrator after each round). The "Compound Loop" extension: agents dump raw outputs, compiler organizes, validator checks quality, verified briefings feed back to all agents. Letta benchmark: simple filesystem memory (74.0%) beats Mem0 specialized graph variant (68.5%).
- **Evidence basis:** Karpathy's own documented pattern (April 2026 — note: future-dated in report, likely referring to a published article). Letta benchmark empirical results. Community extensions.
- **Evidence quality:** Karpathy = credible (authoritative practitioner). Letta benchmark = verified (quantified, reproducible). Community extensions = claimed.
- **Temporal check:** April 2026, 2025 benchmarks. Current. The Karpathy publication date matches today's date — this is the freshest finding in the batch.
- **Conflicts with existing?** Jack's Directive #8 already flagged the Karpathy pattern as high-value. This report provides the concrete three-layer implementation. No conflict; adds implementation specificity.
- **Verdict:** ADOPT. Implement the three-layer findings directory (`raw/`, `compiled/`, `INDEX.md`) as the within-engagement external memory architecture. The orchestrator maintains `INDEX.md` after each round's synthesis. Subagents write to `raw/` (artifact bypass pattern, Finding #3). The orchestrator compiles to `compiled/` for cross-round navigation. This is the mechanical implementation of Jack's Karpathy Directive.
- **Justification:** The Letta benchmark proves file-based memory outperforms specialized tools. Three-layer structure matches Keystone's multi-round architecture naturally (each round produces new `raw/` entries, orchestrator compiles between rounds). The pattern is also reversible — add database substrate later if concurrent write conflicts materialize.
- **Keystone impact:** Component #3 (retrieval system — within-engagement knowledge). Component #5 (Specification Engine — orchestrator's between-round synthesis writes to `compiled/`). Component #7 (Research Agents write to `raw/`). Reduces Component #3 scope for within-engagement use case (no embeddings needed here).
- **Contradicts:** Nothing. Implements Jack's Directive #8 mechanically.

---

### 6. ETH Zurich Warning: Human-Written Memory Files Work, LLM-Generated Files Hurt

- **What:** ETH Zurich AGENTbench study finds human-written memory files improve agent performance ~4%, but LLM-generated memory files hurt performance ~2%. The delta is 6 percentage points. Implication: the structure of memory files should be human-designed; agents fill in content, they do not design the schema.
- **Evidence basis:** ETH Zurich research (AGENTbench). Academic study.
- **Evidence quality:** Verified — peer-reviewed, named institution.
- **Temporal check:** Date not specified in report. Assume 2024-2025. Credible.
- **Conflicts with existing?** No explicit conflict. The existing plan defers schema design to the system, not humans. This finding says the file structure must be human-defined — which aligns with the "Specification layer IS the system" conviction.
- **Verdict:** ADOPT. The `raw/`, `compiled/`, `INDEX.md` structure (Finding #5) must be human-designed upfront. Agents populate entries according to a fixed template. The orchestrator fills in `INDEX.md` using a defined schema, not free-form. This is consistent with the plan's emphasis on structure over intent.
- **Justification:** 6-point delta is meaningful. The risk of LLM-generated memory structure is that it drifts toward whatever the LLM finds natural, which may not be optimized for downstream retrieval. Human-designed schemas prevent this.
- **Keystone impact:** Component #3 and #5 implementation. The memory file schemas must be designed by humans (Jack + the build team) and specified in RESEARCH.md templates, not emergent from agent behavior.
- **Contradicts:** Nothing.

---

### 7. Microsoft Azure SRE Lessons: 5 Core Tools, Not 100+; Limit to 4 Handoffs Maximum

- **What:** Microsoft Azure SRE Agent started with 100+ tools and 50+ specialized sub-agents, then collapsed to 5 core tools and a handful of generalists. Multi-agent handoffs showed bimodal failure — more than 4 handoffs almost always failed due to discovery problems, system prompt fragility, and infinite loops. Their advice: "Invest context budget in capabilities, not constraints" — move domain knowledge from system prompts into files agents read on demand.
- **Evidence basis:** Microsoft Azure SRE Agent production post-mortem. First-party production system data.
- **Evidence quality:** Verified — production system, quantified failure mode.
- **Temporal check:** Date not specified. Likely 2025. Credible.
- **Conflicts with existing?** The existing plan already limits agents to 3-5 tools (Settled Decision #5). The handoff depth concern is new. Keystone's pipeline has well-defined handoff stages: L0→L1→CitationProcessor→L1.5→L2→L3→L4. That is 6 stage transitions, which could exceed the 4-handoff failure threshold depending on implementation.
- **Verdict:** ADAPT. The "4 handoff" failure mode is a warning about sequential chaining, not parallel dispatch. Keystone's pipeline stages are not agent-to-agent sequential handoffs in the Microsoft sense — they are orchestrated stage transitions with structured contracts. The concern applies most directly to any attempt to chain subagents together (e.g., a research agent spawning a follow-up agent as a direct call). Do not chain subagents. All coordination goes through the orchestrator. The pipeline stages are orchestrator-driven, not agent-driven.
- **Justification:** The failure mode is autonomous agent chaining, not pipeline stage transitions. Keystone's architecture already prevents this via the orchestrator-as-hub pattern. Still: document the 4-handoff warning as a constraint on any future agentic extensions. The "domain knowledge in files" advice directly validates JIT context loading.
- **Keystone impact:** Component #5 (orchestration design). Any Component #7 extension that spawns follow-up agents must route through the orchestrator, not chain directly.
- **Contradicts:** Nothing settled.

---

### 8. KV-Cache Hit Rate Is the Single Most Important Production Cost Metric

- **What:** Manus (now Meta) found KV-cache hit rate is the most important production cost metric. Cached input tokens cost 10x less than uncached. Maximizing cache hit rate requires: stable prompt prefixes (system prompts and context that don't change across calls), append-only context growth (don't reorder or regenerate earlier content).
- **Evidence basis:** Manus/Meta production system insight (via Anthropic's Agents SDK analysis). First-party production data.
- **Evidence quality:** Credible — active production system, quantified cost ratio.
- **Temporal check:** 2025-2026. Current.
- **Conflicts with existing?** Not addressed in existing plan. New finding.
- **Verdict:** ADOPT for Phase 2. Phase 1 focus is correctness, not cost. But design the system so caching is possible: write stable system prompts, use append-only context patterns, define the research plan as a stable prefix that all subagents receive in the same form. Don't optimize prematurely but don't make design choices that preclude caching.
- **Justification:** At 10x cost difference for cached vs. uncached tokens, and given the plan's $12–100/engagement cost target, KV-cache optimization could be the difference between profitable and unprofitable production use. The architectural cost of enabling caching upfront is low (stable prefixes, append-only patterns). The cost of retrofitting is high.
- **Keystone impact:** Component #4 (MCP Gateway has the context budget and token tracking). Component #5 (research plan template design — make it a stable prefix). Monitoring metrics to add.
- **Contradicts:** Nothing.

---

### 9. Dedicated Citation Agent as a Final Pipeline Step Is Proven Architecture

- **What:** Anthropic's production multi-agent research system uses a dedicated CitationAgent as a final post-processing step, receiving all documents and the research report to identify and validate specific citation locations. Perplexity AI uses 6-stage pipeline with pre-embedded citations. Elicit scales to 1,000 papers and 20,000 data points with sentence-level citations. The separation of citation validation from research discovery is the pattern.
- **Evidence basis:** Anthropic production system (June 2025). Perplexity and Elicit are production systems.
- **Evidence quality:** Verified (Anthropic production). Credible (Perplexity, Elicit production).
- **Temporal check:** June 2025. Current.
- **Conflicts with existing?** Keystone's existing plan already includes CitationProcessor as a dedicated stage between L1 and L1.5. This finding confirms that architecture is correct and extends it: the CitationProcessor should also include a final validation pass against the full report output (not just dedup and corroboration during L1→L1.5).
- **Verdict:** ADOPT. The existing CitationProcessor architecture is validated. Add an end-of-pipeline citation validation step as part of L4 (Evaluator) — or as a dedicated CitationAgent that runs after L3 generation. The PROV-AGENT framework (W3C PROV extension, August 2025) provides a principled metadata schema for provenance tracking.
- **Justification:** Anthropic uses this exact pattern in their closest architectural analogue to Keystone. The separation of discovery (agents report source IDs) from validation (CitationAgent verifies attribution in final output) prevents citation drift in generation.
- **Keystone impact:** Component #8 (CitationProcessor). Suggests a second citation pass should be added to L4 or as a post-L3 step.
- **Contradicts:** Nothing.

---

### 10. Structure-Driven Retrieval Outperforms Similarity-Driven Retrieval for Agent Memory

- **What:** King's College London ("Beyond RAG for Agent Memory," February 2026) identifies three failure modes for vector RAG in agent memory: redundant top-k retrieval (same facts in many phrasings), pruning that breaks evidence chains, similarity-based retrieval misses logical structure. Structure-driven retrieval consistently outperforms similarity-driven retrieval for agent memory tasks. RAG remains appropriate for searching across large unprocessed source corpora.
- **Evidence basis:** Academic paper, King's College London, February 2026.
- **Evidence quality:** Verified — peer-reviewed, named institution.
- **Temporal check:** February 2026. Highest confidence tier.
- **Conflicts with existing?** The existing plan uses pgvector + hybrid search for Component #3. This finding does NOT say RAG is wrong for source discovery — it says RAG is wrong for agent memory (organized, already-processed knowledge). This is exactly the Karpathy pattern distinction: RAG for discovery, compiled wikis for accumulated knowledge.
- **Verdict:** ADOPT this distinction as a hard design principle. Two separate retrieval regimes: (1) Vector/hybrid RAG for finding unprocessed sources (MCP tools: Exa, Brave, academic APIs). (2) Filesystem-based compiled wiki for organized findings (Karpathy pattern). Do not use RAG to navigate the compiled findings directory. The orchestrator reads `INDEX.md` and navigates via file paths, not vector search.
- **Justification:** Directly validates the Karpathy distinction from Jack's Directive #8. The failure modes (broken evidence chains, missed logical structure) are exactly what would happen if the orchestrator tried to RAG across accumulated findings. Index navigation is the correct pattern.
- **Keystone impact:** Component #3 scope clarification. Reduces the within-engagement RAG use case. Component #3 is now explicitly scoped to external source discovery only, not internal memory retrieval.
- **Contradicts:** Nothing settled. Clarifies Component #3 scope.

---

### 11. Hierarchical Agent Structures Lose Only 5% Accuracy With Faulty Agents vs. 24% for Chains

- **What:** Multi-agent resilience research shows hierarchical structures (one coordinator overseeing peer agents) suffer only ~5% accuracy loss with faulty agents. Chain structures suffer 24% loss. Two safeguards recover up to 96% of lost performance: "Challenger" pattern (agents question each other's outputs) and "Inspector" pattern (independent reviewer). Keystone's Deliberation phase naturally implements Inspector.
- **Evidence basis:** Multi-agent resilience academic research, 2025. Quantified results.
- **Evidence quality:** Verified — empirical with specific numbers.
- **Temporal check:** 2025. Current.
- **Conflicts with existing?** Keystone already uses a hierarchical structure (orchestrator + parallel subagents). This confirms that choice. The Challenger pattern is not currently in the plan.
- **Verdict:** ADOPT the validation of hierarchical structure. INVESTIGATE the Challenger pattern for Phase 2 (not Phase 1 MVP). Adding explicit claim-level confidence scores (Finding #4) is the prerequisite for effective selection during Deliberation; the Challenger pattern adds an adversarial review layer on top.
- **Justification:** The 5% vs 24% loss difference validates the orchestrator-hub architecture. The Challenger pattern is interesting but adds implementation complexity — defer to Phase 2 once the basic pipeline is running.
- **Keystone impact:** Component #9 (Deliberation). Architecture validation. Phase 2 extension candidate.
- **Contradicts:** Nothing.

---

## Architectural Decisions This Enables

**Decision A: External Memory Architecture (within-engagement)**
Three-layer Karpathy pattern is the confirmed implementation: `{engagement_id}/memory/raw/`, `{engagement_id}/memory/compiled/`, `{engagement_id}/memory/INDEX.md`. Human-designed schemas, orchestrator-maintained index. This resolves Jack's Directive #3 (how findings from round N inform round N+1) — the answer is: orchestrator compiles round N findings into `compiled/` and updates `INDEX.md` between rounds; subagents in round N+1 receive selected excerpts from `compiled/` in their JIT context.

**Decision B: Subagent Output Contract**
Pydantic schema required. Two-part output: (1) structured summary ~1,500 tokens with 3–7 claims, per-claim confidence score, per-claim source count, status, gaps; (2) full artifact written to `{engagement_id}/memory/raw/round_{N}/{agent_id}.md`. Orchestrator reads (1) for synthesis decisions; reads (2) when deeper detail is needed for Deliberation. This closes the existing L1→L1.5 handoff spec gap.

**Decision C: Deliberation Aggregation Mode**
Claim-level selection, not synthesis. Orchestrator acts as judge: evaluate competing claims from different rounds against source evidence, select best-supported. Requires per-claim confidence scores and source counts in subagent outputs. The 81% vs 51.2% empirical result makes synthesis an unacceptable implementation.

**Decision D: Orchestrator Context Strategy**
Opus 4.6: compaction within a round is safe. Between rounds, persist to `research-state.md`, read at round start. Hard ceiling: 140–160K tokens (70–80% of 200K). Sonnet subagents: clean context window per task, ceiling 100K tokens. Research plan at context start, most recent findings at context end.

**Decision E: Two-Phase Citation Architecture**
CitationProcessor between L1 and L1.5 (dedup, corroboration, manifest generation) is confirmed correct. Add a second citation validation pass — CitationAgent after L3 generation verifies attribution in the final report against the source registry. Source registry is a `sources.json` or SQLite file; subagents register sources at discovery time with structured metadata and unique IDs.

---

## Changes to Existing Plan

### Requires Update to PHASE-1-IMPLEMENTATION-SPEC.md

**Component #7 (Research Agent) — Output Contract Change (HIGH PRIORITY)**
Current spec: agents return condensed 1–2 page summaries.
Required change: agents return Pydantic-schemaed structured summary (~1,500 tokens) AND write full artifacts to external file. Update the handoff contract to include: `claims: list[ClaimOutput]`, `status: Literal["complete", "partial", "blocked"]`, `gaps: list[str]`, `artifact_path: str`. Each `ClaimOutput` must include: `text`, `confidence: float`, `source_ids: list[str]`, `source_count: int`.

**Component #9 (Deliberation) — Aggregation Logic Change (HIGH PRIORITY)**
Current spec: structured aggregation (implementation undefined).
Required change: explicitly specify selection over synthesis. Aggregation = judge-based claim selection. Add per-claim selection rationale field to Deliberation output.

**Component #3 (Retrieval) — Scope Clarification (MEDIUM PRIORITY)**
Current spec: pgvector + hybrid search for all retrieval.
Required change: Split retrieval into two regimes. Component #3 scoped to external source discovery only (Exa, Brave, academic APIs via MCP). Within-engagement knowledge retrieval uses filesystem-based Karpathy pattern (`INDEX.md` navigation), not vector search. This reduces Component #3 scope and may address Jack's over-engineering concern (Directive #9).

**Component #5 (Specification Engine) — Between-Round Protocol Addition (MEDIUM PRIORITY)**
Add specification of the between-round state persistence and resumption protocol. Orchestrator writes `research-state.md` (research plan, confidence map, open questions, stopping condition status) at end of each round. Reads it at start of next round. This is the mechanical answer to Jack's Directive #3 question: "how do findings from round N inform round N+1?"

**Post-L3 Citation Validation Step (LOW PRIORITY — Phase 2)**
Add CitationAgent as final pipeline step after L3 generation. Validates attribution in the final report against the source registry. Not Phase 1 MVP but should be in the architectural spec so the data contracts are designed to support it from day one.

### Monitoring Metrics to Add
- Context utilization % per agent per round (alert at 75%, hard ceiling at 80%)
- KV-cache hit rate (Phase 2 cost optimization target)
- Information retention sampling (verify key subagent findings survive into final report; 37% is the failure-mode floor to guard against)

---

## Open Questions Remaining

**Q1: Who triggers the between-round synthesis — the orchestrator or a dedicated compiler agent?**
The Karpathy "Compound Loop" uses a separate compiler and validator. For Keystone MVP, the orchestrator doing its own compilation is simpler. But at scale (3–5 Sonnet agents, 2–4 rounds, 50–200 sources), offloading compilation to a dedicated Haiku pass may reduce orchestrator context pressure. Not resolved. Recommendation: orchestrator compiles in MVP; monitor context utilization; add dedicated compiler if orchestrator hits 70% threshold during compilation.

**Q2: What is the stopping condition for iterative research (Jack's Directive #3)?**
This report does not address stopping conditions. It describes how findings from round N inform round N+1 (via compiled memory) but not when to stop. This remains the single biggest architectural gap, as Jack identified. Report 01 (iterative research) likely addresses this more directly.

**Q3: `sources.json` file vs. SQLite for the source registry — which for Phase 1?**
The report notes SQLite when concurrent writes are needed. With 3–5 subagents writing in parallel, concurrent writes are expected. `sources.json` with advisory locks (already in settled decisions) may be sufficient for Phase 1. SQLite is the safer long-term choice. Recommend: SQLite from day one — it is not more complex to implement and advisory locks on JSON files are a footgun at scale.

**Q4: How does the `research-state.md` orchestrator persistence interact with the RESEARCH.md engagement specification?**
RESEARCH.md is the static engagement spec. `research-state.md` is the dynamic per-round state. The schemas should be designed to reference each other (RESEARCH.md → immutable; research-state.md → mutable, updated each round). The current plan does not specify this relationship. Needs to be resolved before Component #5 build.

**Q5: Does "claim-level selection" in Deliberation require full cross-claim consistency checking?**
Selecting the best-supported individual claims could produce an incoherent set if selected claims contradict each other. The report does not address this. The 5% Narrative Coherence rubric weight exists partly for this reason. A post-selection consistency pass may be needed. Flag for Component #9 design.
