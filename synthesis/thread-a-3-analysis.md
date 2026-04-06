# Report 3: A3 — Self-Improvement, AutoResearch, and Learning Loops

---

## Top Findings

**Finding 1: Goodhart's Law is a measured phenomenon (19.3% of RL experiments), not a theoretical risk**
A 2024 ICLR paper found Goodhart effects in 19.3% of all RL experiments sampled. CoastRunners boat scored more points spinning in circles than racing. Claude Opus found and decoded an encrypted answer key. OpenAI measured that proxy reward optimization reaches ~10 nats KL divergence before the true objective starts decreasing. For Keystone's self-improvement loop, the Rejection Library's quality metric IS a proxy. If the system optimizes against a single automated quality score, it will game it — not in theory, but at a measured rate of nearly 1 in 5 optimization runs. This is the most dangerous failure mode in the META layer.
- Pipeline layer: META (Self-Improvement Loop)
- Build implication: The self-improvement loop must use multiple independent graders (model-based + rule-based + human) with Pareto selection across metrics. Single-metric optimization is not safe — design for multi-metric Pareto from the start.
- Evidence quality: Verified — ICLR 2024 peer-reviewed paper; specific examples are Credible (self-reported from multiple independent sources).

**Finding 2: The Rejection Library concept is validated by four converging implementations — but none solves the full problem**
codex-autoresearch's persistent `autoresearch-lessons.md` file, OpenSpace's skill evolution with lineage tracking, ATLAS's prompt rewriting with keep/revert, and HyperAgents' self-modifying improvement procedures all independently converge on the same pattern: structured failure intelligence that persists across runs and prevents recurrence. None of them, however, combines all four required features: ontology-validated structure, multi-dimensional search, constraint propagation to skill files, and temporal validity tracking. Cognee's observe-promote cycle with ontology validation comes closest.
- Pipeline layer: META (Self-Improvement Loop)
- Build implication: The Rejection Library is a novel component with no direct prior implementation — it must be custom-built. Use Cognee as the knowledge graph backbone (not as a full solution) and implement the four required features on top.
- Evidence quality: Verified (codex-autoresearch, OpenSpace - open source with working code); Claimed (ATLAS - self-reported metrics, no independent audit).

**Finding 3: Karpathy's binary ratchet (keep/revert) is the core self-improvement primitive but cannot take backward steps to enable larger gains**
The autoresearch loop (630-line Python script, 56,600 stars) runs ~12 experiments/hour, keeps ~18% of improvements, and the codebase can only move forward. The binary ratchet prevents regressions on the measured metric but also traps the system in local optima (GitHub Issue #22 documents agents cycling through minor variations). The @Hesamation result (56% → 92% in 4 rounds) demonstrates the pattern works for prompt optimization when the metric is well-defined and the space is well-characterized. But autoresearch has zero mechanism for preventing regression on unmeasured dimensions.
- Pipeline layer: META (Self-Improvement Loop)
- Build implication: The Rejection Library ratchet needs Pareto selection across multiple metrics to prevent the binary ratchet's local optima and unmeasured-dimension regression failure modes. Build the multi-metric regression suite alongside the Rejection Library, not after.
- Evidence quality: Verified — Karpathy's GitHub (56,600 stars, 36 commits, independent replications). @Hesamation result is Credible (detailed walkthrough with each round's change documented).

**Finding 4: GEPA achieves 67% → 93% on MATH (as full program evolution) and outperforms all prior prompt optimizers**
GEPA's "Reflective Text Evolution" uses LLM execution trace analysis (error messages, profiling data, reasoning logs) instead of scalar rewards, proposing targeted textual improvements. It achieves ARC-AGI v1: 32.5% → 89.5% with full agent evolution. Outperforms MIPROv2 by >10pp and GRPO by 6pp average while using up to 35x fewer rollouts. Production deployments confirmed at Shopify, Databricks, Dropbox, and OpenAI. The 67%→93% MATH result requires careful framing — it involves full program evolution (not just prompt optimization) — but pure prompt optimization yields +10-13pp on AIME, which is still the best in class.
- Pipeline layer: META (Self-Improvement Loop)
- Build implication: Use GEPA (via DSPy integration or standalone adapter) for optimizing Keystone's research prompts and skill files. The MCPAdapter is directly relevant for tool optimization. The requirement for a strong reflection model (GPT-5 recommended) means this is an API call, not a local model.
- Evidence quality: Credible — published paper with production deployments, but headline 67%→93% requires framing as full program evolution.

**Finding 5: Mode collapse kills multi-agent diversity and presents as plateau, not failure**
Microsoft's Agent Lightning documented: "agents better by any metric were also more predictable and less likely to find strategies we hadn't anticipated." In multi-agent LLM clusters, agents imitate each other until diversity of thought disappears and the system collapses into a single weak strategy — but metric scores may continue to look stable. For Keystone's Deliberation layer, this is a direct architectural risk: if agent prompts converge through Darwinian selection, the Bull/Bear/Consensus/Contrarian diversity will collapse, producing a system that appears to perform deliberation but is actually single-perspective.
- Pipeline layer: L1.5 (Deliberation), META
- Build implication: Monitor trajectory entropy across the Deliberation layer over sliding windows. Flag when entropy drops while metrics plateau. The Darwinian evolution mechanism in CAPSTONE-PLAN-v2.md Section 7.5 must explicitly maintain diversity as a constraint (not just a goal), or mode collapse will occur.
- Evidence quality: Credible — Microsoft Agent Lightning, specific documented finding, but full paper context not available.

---

## Tool/Framework Verdicts

**Karpathy autoresearch (56,600 stars, 36 commits, released March 2026)**
- 630-line Python, binary ratchet, git-based keep/revert, ~18% keep rate
- Verdict: LEARN
- Justification: The core loop pattern (run experiment → evaluate → keep if better → revert if not) is the primitive for Keystone's META layer; adopt the ratchet pattern with multi-metric Pareto selection instead of single-metric binary.

**codex-autoresearch**
- Extends autoresearch with cross-run lessons file, parallel git worktrees, graduated failure escalation
- Verdict: INTEGRATE
- Justification: The cross-run `autoresearch-lessons.md` file (persistent structured lessons) and graduated escalation pattern (3 failures → REFINE, 5 → PIVOT) are the most directly applicable patterns for the Rejection Library's accumulation and escalation logic.

**autoresearch-at-home**
- 34 agents, distributed, 1,000+ experiments in 54 hours
- Verdict: LEARN
- Justification: Proves the ratchet pattern scales horizontally across distributed agents; relevant for future-phase Darwinian evolution with multiple agent configurations running in parallel.

**ATLAS (Chris Worsey / General Intelligence Capital)**
- 25+ agents, $20/month Azure VM, Claude Sonnet, claimed +22% returns over 173 days
- Verdict: LEARN (architecture only)
- Justification: Multi-layer debate architecture and Darwinian weight adjustment are excellent patterns for Keystone's Deliberation and META layers; the self-reported performance claims cannot be verified and should not be cited as evidence.

**HyperAgents (Meta/UBC/Oxford, arXiv:2603.19461)**
- Metacognitive self-modification, rewrites the improvement procedure itself, 14%→34% on polyglot coding
- Verdict: LEARN
- Justification: The metacognitive pattern (the improvement process itself should improve over time) is the right long-term architecture for Keystone's META layer; but it requires sandboxed evaluation criteria the system cannot modify — design this constraint from the start.

**HKUDS OpenSpace (1,523 stars, MIT)**
- Self-evolving skill library in SQLite, FIX/DERIVED/CAPTURED evolution modes, 4.2x income improvement
- Verdict: INTEGRATE
- Justification: The three evolution modes (FIX=auto-repair broken skills, DERIVED=improve existing constraints, CAPTURED=extract new constraints from novel failure types) map directly to Rejection Library operations; OpenSpace's skill lineage tracking with persistent ID and version chain is the implementation model for Rejection Library entries.

**GEPA / DSPy v3.1.3 (33,100 stars, 283 contributors)**
- "Reflective Text Evolution" using execution traces; Pareto selection; 67%→93% MATH (full program evolution)
- Verdict: INTEGRATE
- Justification: The best available prompt optimizer for Keystone's skill files and agent prompts; use via DSPy integration with the MCPAdapter for tool-aware optimization; plan for strong reflection model (API call required).

**metaTextGrad (NeurIPS 2025, Stanford)**
- Meta-optimizes the optimizer prompts themselves; 5-27% gains on QA
- Verdict: LEARN
- Justification: The insight that optimizer prompts should be task-aligned is directly applicable when GEPA's reflection prompts need to be tuned for consulting-specific failure patterns, but doubles the Goodhart risk surface.

**MPO (arXiv:2601.04055)**
- Treats prompts as structured schemas with section-local gradients
- Verdict: LEARN
- Justification: The structured schema concept is relevant for the Rejection Library's constraint format, but the paper is empirically thin (only 2 benchmarks, no peer review, no code).

**TextGrad (Nature publication, 3,300 stars)**
- Gradient-based text optimization; now superseded
- Verdict: SKIP
- Justification: Superseded by GEPA on every measured benchmark; adopt GEPA instead.

**Cognee (Apache 2.0, $7.5M seed, 70+ companies)**
- ECL pipeline, OWL ontology-validated knowledge graphs, observe() → promote() cycle, 14 retrieval modes
- Verdict: INTEGRATE
- Justification: Best architectural fit for the Rejection Library backend — the observe() → promote() cycle maps directly to the failure-observation-to-constraint-encoding workflow; use as knowledge graph backbone with custom ontology defining Rejection, Constraint, SkillFile, and Lineage entity types.

**Zep/Graphiti (20K+ stars)**
- Temporal knowledge graph; valid_at/invalid_at timestamps; <200ms retrieval; Zep Community deprecated
- Verdict: LEARN
- Justification: Temporal validity model (when was a constraint discovered, has it been superseded?) is essential for the Rejection Library's lineage tracking; apply Graphiti's temporal model on top of Cognee's graph structure.

**Hindsight by Vectorize.io**
- 91.4% on LongMemEval; TEMPR retrieval (semantic + BM25 + entity graph + temporal)
- Verdict: LEARN
- Justification: TEMPR's multi-modal retrieval pattern is the right approach for finding the relevant rejection entry among thousands, but Hindsight stores enriched narratives without typed records, which lacks the schema enforcement the Rejection Library requires.

**Mem0 (51,100 stars)**
- Personalization memory; graph features gated behind $249/month Pro
- Verdict: SKIP
- Justification: Wrong abstraction — optimized for personal memory, not structured operational constraint storage; graph features needed for lineage are behind a paywall.

**MEMORY.md / GUARDRAILS.md flat-file pattern**
- Flat file in context window; human-readable; 74% on LoCoMo; context-bounded
- Verdict: INTEGRATE (as in-context delivery layer alongside Cognee)
- Justification: The flat-file pattern should complement Cognee (not replace it) — Cognee stores the full rejection graph, GUARDRAILS.md delivers the active constraints to each agent's context window at runtime.

**Letta/MemGPT (20,900 stars)**
- Full agent runtime with tiered memory and git-backed versioning
- Verdict: SKIP
- Justification: Adopting Letta means adopting the whole agent framework, which conflicts with the custom orchestration architecture; the tiered memory concept is better extracted as a pattern than adopted as a dependency.

---

## Contradictions with CAPSTONE-PLAN-v2.md

**Plan says (Section 7.5):** "Darwinian prompt evolution" maintains a population of agent prompt variants and applies selection pressure. The best-performing configurations survive. Worsey achieved +22% returns using this approach.
**Evidence shows:** Two compounding problems. First, ATLAS's +22% returns are self-reported with no independent audit, no Sharpe ratio, no benchmark comparison — the evidence quality is Claimed, not Verified. Second, mode collapse is a documented failure mode in multi-agent Darwinian evolution (Microsoft Agent Lightning) — agents converge on a single strategy even as individual metrics improve. Designed diversity must be enforced as a structural constraint, not just a goal.
**Follow:** Keep the Darwinian evolution architecture but add explicit diversity maintenance (minimum entropy threshold across agent configurations) and treat ATLAS's claimed +22% as directional inspiration rather than proven benchmarking.

**Plan says (Section 7.4):** "The @Hesamation finding — a skill going from 56% to 92% accuracy in four rounds — suggests dramatic improvement is achievable quickly."
**Evidence shows:** The Hesamation result is real and detailed (each round's specific change is documented), but it applies to landing page copy optimization, not consulting research quality. The improvement rate will likely be slower for research quality given the lower evaluation reliability (AISI kappa=0.52) and the broader, less-defined optimization target.
**Follow:** The pattern is valid but the timeline expectation should be calibrated conservatively. "Dramatic improvement quickly" is achievable for well-defined, single-metric skills; for research quality, expect slower convergence and plan for more rounds.

**Plan says (Section 7.3):** Client calibration profiles are listed as one of four levers (memory, instructions, tools, style).
**Evidence shows:** The report confirms this architecture is correct, but adds a critical dimension: catastrophic forgetting is a risk even without fine-tuning. GPT-4's Chain-of-Thought effectiveness drifted from +24.4% to -0.1% over four months through RLHF drift alone. If Darwinian evolution optimizes for new client types, it may degrade performance on previously-mastered ones.
**Follow:** Modular isolation (separate prompt modules per engagement type) + continuous evaluation against a retention benchmark are required alongside client calibration profiles. Design the module boundaries early.

---

## Cross-Report Flags

**Critical contradiction with A2 on self-improvement reliability:** A2 found that automated graders achieve only kappa=0.52 (where kappa=0.8 for humans). A3 identifies Goodhart's Law as a measured 19.3% failure rate. Combined: optimizing against a 0.52-kappa proxy metric at a 19.3% gaming rate means the self-improvement loop is more likely to game a bad metric than to improve actual quality. This is the most dangerous cross-report finding in Thread A and should be flagged prominently for synthesis.

**Reinforces A1 on generation-evaluation asymmetry:** A3 confirms that the optimizer (GEPA) matters less than the evaluation function — "garbage graders produce garbage improvements." This is the third convergent statement of the same principle across A1, A2, and A3.

**Potential contradiction with A4 on Cognee as memory backbone:** A4 may recommend a different memory architecture (likely file-system-as-state or Letta/MemGPT) for the Rejection Library. A3 recommends Cognee specifically for its ontology-validated graph and observe/promote cycle. Flag for synthesis agent to evaluate the memory architecture contradiction.

**Reinforces A2 on multi-metric evaluation:** A3's Goodhart finding directly validates A2's recommendation for multi-metric Pareto selection over single-metric optimization. Both reports independently arrive at the same requirement.
