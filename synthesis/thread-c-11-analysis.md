# Report 11: C2 — Deliberation & Multi-Perspective Synthesis

**Source report:** `research-reports/Deep_Research_Report_From_Prompt_11.md`
**Prompt:** Research multi-agent deliberation architectures, debate vs. voting, MoA variants, adversarial testing tools, confidence mapping, and steelmanning enforcement for the Keystone Deliberation Layer.

---

## Top Findings

**Finding 1: Naive multi-agent debate is a mathematical martingale — it adds noise without directional improvement.**
- Pipeline layer: L1.5 (Deliberation)
- Choi, Zhu, and Li (NeurIPS 2025 Spotlight, "Debate or Vote: Which Yields Better Decisions in Multi-Agent LLMs") prove via Dirichlet-Compound-Multinomial modeling that Theorem 2 holds: an agent's belief in the correct answer forms a martingale where E[alpha_{i,t+1} | alpha_{i,t}] = alpha_{i,t}. Empirical confirmation: majority voting (no debate) achieved 0.7691 average accuracy across seven benchmarks; best debate variant reached only 0.7377. On arithmetic tasks, voting hit 0.99 while best debate variant scored 0.84, and centralized debate collapsed to 0.43. More rounds consistently degraded performance.
- Evidence quality: Verified (NeurIPS 2025 Spotlight, formal mathematical proof + empirical validation, published code)
- Build implication: This is the most consequential finding for the Deliberation Layer design. CAPSTONE-PLAN-v2.md Section 4.3 describes "a structured multi-perspective debate" — this language must be updated. The design must explicitly avoid iterative debate rounds. The correct architecture is independent parallel analysis with structured aggregation, not iterative debate. Three specific interventions break the martingale: MAD-Conformist (lock responses matching majority vote), MAD-Follower (adopt majority with 30% probability), and MAD-Oracle (freeze correct answers — impractical but proves the principle). Asymmetric update rules that preserve correct-leaning signals are the key insight.

**Finding 2: Cross-provider model diversity is a functional requirement, not a preference — for analytical tasks.**
- Pipeline layer: L1.5 (Deliberation)
- Wu et al. "Can LLM Agents Really Debate?" (McGill/Mila, November 2025): intrinsic reasoning strength is the dominant performance predictor, with the strongest agent's accuracy upper-bounding team performance. Majority pressure suppresses independent correction to below 5% for weak agents facing incorrect majorities. Cross-model-family heterogeneity provides modest but real gains. Hiding confidence scores between agents prevents over-confidence cascades. Single-pass debate suffices; additional rounds entrench errors. Korokithakis's production workflow (March 2026): "cross-company model diversity is a functional requirement rather than a preference" because same-provider models self-agree bias — they rarely robustly critique each other's outputs.
- Evidence quality: Credible for Wu et al. (preprint, McGill/Mila); Credible for Korokithakis (blog, production experience)
- Build implication: The CAPSTONE-PLAN-v2.md's plan to use "3-4 analyst personas" in Deliberation must specify cross-provider models. Claude for one perspective, GPT for another, Gemini for a third creates genuine knowledge diversity. Same-model prompting ("be bullish" vs. "be bearish") produces weaker diversity because the underlying knowledge base is identical. Confidence scores should be hidden during deliberation rounds, collected only at aggregation.

**Finding 3: Self-MoA vs. Attention-MoA resolves in favor of structured aggregation at higher model tiers.**
- Pipeline layer: L1.5 (Deliberation)
- Self-MoA (Li et al., ICLR 2025): single top model generating 4-6 diverse outputs at temperature 0.7 then aggregating outperforms mixed-model MoA by +6.6% on AlpacaEval 2.0. However, tested primarily on 7B-class models on chat-oriented benchmarks.
- Attention-MoA (Wen et al., January 2026): ensemble of frontier models with inter-agent semantic attention (cross-agent critique-and-refine + inter-layer residual connections) achieved 91.15% on AlpacaEval 2.0 LC and 9.32 on MT-Bench, beating GPT-4.1 (8.59). Adaptive early stopping reduces tokens ~11%.
- Resolution: Self-MoA tested against naive concatenation; Attention-MoA changed the aggregation mechanism. Simple aggregation fails; structured deliberation succeeds. For Keystone's analytical research at frontier scale, Attention-MoA's cross-agent critique-and-refine pattern applies.
- Evidence quality: Verified for Self-MoA (200+ configurations, ICLR 2025); Credible for Attention-MoA (preprint, January 2026; note Stale for Self-MoA — 13+ months old)
- Build implication: The aggregator model quality matters more than proposer quality (Together AI MoA finding). Use the strongest available model as aggregator, not as individual perspective agent.

**Finding 4: Society of Thought — frontier models already simulate multi-agent deliberation internally, which validates but doesn't eliminate the case for explicit deliberation.**
- Pipeline layer: L1.5 (Deliberation), L1
- Kim, Lai, Scherrer, Aguera y Arcas, Evans (Google/UChicago/Santa Fe, January 2026): frontier reasoning models (DeepSeek-R1, QwQ-32B) spontaneously simulate multi-agent-like interactions within their chain of thought. Amplifying the "surprise/realization" feature (Feature 30939) via sparse autoencoder steering nearly doubles accuracy from 27.1% to 54.8% on Countdown arithmetic.
- Evidence quality: Verified (mechanistic interpretability with causal interventions, high-prestige authors, Science-level venue)
- Build implication: Explicit multi-agent deliberation adds value specifically when genuine knowledge diversity is needed (different models know different things), structured disagreement must be auditable (Confidence Map is a product), or context windows are insufficient for required deliberation depth. For Keystone, where the Confidence Map itself is a deliverable and auditable reasoning is required, explicit multi-agent architecture remains justified.

**Finding 5: DiscoUQ provides production-ready structured disagreement tracking for the Confidence Map.**
- Pipeline layer: L1.5 (Deliberation)
- DiscoUQ (Jiang et al., March 2026): extracts linguistic structure features (evidence overlap, minority argument strength, divergence depth — surface/intermediate/deep) and embedding geometry features (cluster distances, dispersion, cohesion). AUROC 0.802 vs 0.098 ECE for baselines. Largest improvements in the "weak disagreement" tier (50-60% agreement) where simple vote counting fails — exactly the contested/moderate zone where the Confidence Map adds most value.
- Evidence quality: Credible (preprint, March 2026)
- Build implication: Use DiscoUQ's feature taxonomy as the Confidence Map's underlying data model. The five-tier confidence taxonomy proposed in the report (High >80% / Moderate 60-80% / Weak 50-60% / Contested <50% / Insufficient evidence) maps cleanly to the plan's confidence map JSON structure. The "weak confidence" tier (50-60% agreement) is the most important to instrument well.

---

## Tool/Framework Verdicts

**Together AI MoA (propose-then-aggregate)**
- Version/maturity: ICLR 2025 Spotlight, ~266 citations, ~50 lines to implement
- What it does: Define reference models, call in parallel, concatenate into aggregator prompt; role differentiation between proposers and aggregators
- Verdict: BUILD — adopt propose-then-aggregate as Keystone's L1.5 foundation; aggregator quality more important than proposer quality; default 3-layer, 6-proposer achieves 65.1% LC win rate

**LangGraph**
- Version/maturity: v1.0 stable, 24K+ stars, used by Uber/LinkedIn/Klarna
- What it does: Explicit state machines with checkpointing, conditional routing, human-in-the-loop gates; best for complex pipelines with cycles
- Verdict: BUILD — use as L1.5 orchestration runtime; explicit state machines handle the reject/regenerate cycle from L4 Evaluator back to L1.5; checkpointing enables recovery from mid-deliberation failures

**ReConcile (confidence-weighted voting)**
- Version/maturity: ACL 2024, production-ready
- What it does: Confidence-weighted roundtable discussion among diverse LLMs; up to 11.4% improvement over single-agent; GPT-4 improves 10% through discussion with other agents
- Verdict: BUILD — adopt confidence-weighted aggregation as the default aggregation mechanism for the Confidence Map

**CIR3 Curmudgeon Agent pattern**
- Version/maturity: Peer-reviewed ScienceDirect 2025
- What it does: Dedicated devil's advocate agent with explicit challenge mandate; external diversity score to prevent Collective Cognitive Convergence collapse
- Verdict: BUILD — implement as the fourth agent in the Deliberation phase (Bull/Bear/Consensus/Curmudgeon replaces the plan's Bull/Bear/Consensus/Contrarian); the Curmudgeon role is more structurally enforced than "Contrarian"

**DAR (Diversity-Aware Retention)**
- Version/maturity: Preprint March 2026, Credible
- What it does: Selects subset of agent responses that maximally disagree before broadcasting; preserves authentic dissent without modification
- Verdict: BUILD — use DAR-style filtering at the Phase 2 aggregation step to ensure the aggregator engages with maximum disagreement points, not just the majority view

**DiscoUQ**
- Version/maturity: Preprint March 2026, Credible
- What it does: Structured disagreement tracking via linguistic + embedding geometry features; AUROC 0.802
- Verdict: BUILD — use as the Confidence Map feature extraction engine; the linguistic + geometry feature combination is the right data model for the confidence map JSON structure

**MAJ-EVAL**
- Version/maturity: ICLR 2026 submission, Verified
- What it does: Auto-constructs evaluator personas from domain-specific documents; multi-agent in-group debate produces evaluations better aligned with human expert ratings
- Verdict: BUILD — auto-construct evaluator personas from Keystone methodology documents to assess whether the Confidence Map captures relevant analytical dimensions; this is the L4 Evaluator's quality assessment of the Deliberation Layer's output

**Promptfoo**
- Version/maturity: 25.6K GitHub stars, MIT, acquired by OpenAI March 2026
- What it does: Multi-turn deliberation quality testing; Crescendo/GOAT/Hydra strategies; YAML-based CI/CD integration; custom policy plugins
- Verdict: BUILD — use for deliberation quality regression testing; build YAML test suites that check Confidence Map structure, steelmanning presence, and minority argument engagement

**PyRIT**
- Version/maturity: Microsoft, v0.11.0, 3.4K stars, 100+ internal red team operations
- What it does: Adversarial robustness testing; Crescendo and TAP orchestrators for multi-turn propagation; XPIA testing for cross-agent prompt injection
- Verdict: BUILD — use for adversarial testing of the deliberation chain; cross-agent prompt injection is the primary attack surface (adversarial input to one agent propagates through deliberation chain)

**Garak (NVIDIA)**
- Version/maturity: v0.13.3, 6.9K stars, Verified
- What it does: Systematic LLM vulnerability scanner ("nmap of LLM security"); probe/detector/score/report pattern; primarily single-turn
- Verdict: LEARN — adopt probe/detector pattern for custom deliberation scanners; use directly for pre-deployment model vulnerability screening before assembling agents into deliberation

**AutoGen SocietyOfMindAgent**
- Version/maturity: Active but Microsoft shifting strategic focus; maintenance mode
- What it does: Wraps group chat team as single agent; no deliberation-specific logic (no voting, convergence detection, structured debate)
- Verdict: SKIP — strategic risk from maintenance mode; no deliberation logic to build on; adopt team-as-agent wrapper pattern but build on LangGraph

**CrewAI**
- Version/maturity: 45.9K stars, 1.3M+ monthly PyPI installs; v1.12.2
- What it does: Role-based agent teams; good for rapid prototyping; lacks production-grade state management and checkpointing
- Verdict: LEARN — suitable for rapid prototyping of deliberation configurations, but LangGraph is the production runtime; no checkpointing is a dealbreaker for L1.5

**DeepTeam**
- Version/maturity: v1.0.0, ~1.3K stars, Credible
- What it does: 40-50 vulnerability types, multi-turn attacks, single-agent focused
- Verdict: LEARN — adopt vulnerability-metric-attack architecture but too immature for production integration; revisit in 6 months

**A-HMAD (role specialization + learned consensus)**
- Version/maturity: November 2025 journal paper, Credible (no public code repository)
- What it does: Role-specialized agents (+3.5% over homogeneous); dynamic routing; trained consensus module (+5% on disagreement cases)
- Verdict: LEARN — adopt role specialization concept; reproducibility concerns prevent direct integration; build trained aggregation concept from scratch

---

## Contradictions with CAPSTONE-PLAN-v2.md

**Contradiction 1 (CRITICAL): The plan describes "structured multi-perspective debate" in Section 4.3 — the martingale proof shows this design will underperform majority voting.**
- Plan says: "a structured multi-perspective debate" with personas "each constructing a thesis from the shared findings"; "a synthesis round runs where each critiques the others' positions"
- Evidence shows: Iterative debate between agents is a mathematical martingale — the synthesis round where personas critique each other is exactly the pattern that NeurIPS 2025 proves doesn't improve outcomes beyond majority voting. The debate adds noise, not signal.
- Resolution: Follow the evidence over the plan. Restructure L1.5 as two phases: (1) Independent Parallel Analysis with no inter-agent communication, (2) Structured Aggregation with one curmudgeon challenge round. The plan's core intuition (multiple perspectives + structured synthesis) is correct; the mechanism (iterative debate) is wrong.
- Specific change needed: Section 4.3 should be rewritten to remove "synthesis round runs where each critiques the others' positions" and replace with DAR-style filtering into a strong aggregator with one curmudgeon challenge.

**Contradiction 2: The plan describes having agents "construct a thesis FROM the shared findings" — they should analyze independently first.**
- Plan says: Deliberation spawns analyst personas "each constructing a thesis from the shared findings" — implying they all see the same research output simultaneously
- Evidence shows: Wu et al. and the martingale finding both confirm that independent analysis before any deliberation produces better outcomes; simultaneous access to shared findings creates anchoring before deliberation begins
- Resolution: Agents should analyze independently with assigned perspectives before seeing each other's work. Only at the aggregation phase do outputs converge. The plan needs to specify that perspective agents receive the research findings independently, not as a shared broadcast.

**Contradiction 3: The plan doesn't specify cross-provider model diversity as a requirement.**
- Plan says: Multiple personas (Bull/Bear/Consensus/Contrarian) but doesn't mandate cross-provider models
- Evidence shows: Cross-provider diversity is a "functional requirement," not a preference; same-provider models self-agree bias means homogeneous agents converge on shared biases
- Resolution: Follow the evidence. Add cross-provider model diversity as an explicit L1.5 architectural requirement. Cost note: DeepSeek V3.2 at $0.28/M input tokens can fill the cost-effective analytical role.

**Contradiction 4: The plan's Confidence Map structure is broadly right but needs the DiscoUQ feature taxonomy.**
- Plan says: Confidence map with high_confidence, moderate_confidence, contested, gaps_identified, absence_report (JSON structure in Section 4.3)
- Evidence shows: DiscoUQ's five-tier taxonomy (High/Moderate/Weak/Contested/Insufficient Evidence) adds a critical "Weak confidence" tier (50-60% agreement) where simple methods fail most. The DiscoUQ feature set (evidence overlap, minority argument strength, divergence depth, embedding geometry) gives the plan's confidence map computational grounding.
- Resolution: Adopt the five-tier structure. The plan's current four-tier structure misses the "weak confidence" tier that's most important to instrument. Add embedding geometry features to the confidence map JSON.

---

## Cross-Report Flags

**Flag 1 (reinforces C1/Report 10):** The DeepMind 17.2x error amplification finding (Report 10, Verified) and the martingale proof (this report, Verified) converge on the same architectural conclusion from different research traditions. This is strong convergent validation: unstructured multi-agent debate is harmful, not just ineffective. Both findings should be cited together when justifying the L1.5 two-phase architecture.

**Flag 2 (reinforces C3/Report 12):** The aggregator model quality finding (Together AI MoA: final performance more sensitive to aggregator than proposer quality) has implications for L3 generation. The same model doing synthesis in L2/L3 should be the strongest available, not just the cheapest. This connects to the "anti-slop" requirement — aggregation quality directly determines output quality.

**Flag 3 (reinforces C4/Report 13):** The adversarial propagation risk in multi-agent deliberation (adversarial input to one agent propagates through the deliberation chain via inter-agent message passing) is the same attack vector as the MCP security finding in Report 13. Both require treating all inter-agent messages as untrusted data. The mitigation strategies (message sanitization, per-agent output validation, invariant checks) should be shared infrastructure across L1.5 and the retrieval layer.

**Flag 4 (potential conflict with Thread A):** The Anthropic multi-agent research system finding (Claude Opus 4 as lead researcher spawning 3-5 Sonnet subagents, 90.2% improvement over single-agent) validates the plan's orchestration design but notably lacks deliberation. This system achieves high performance through parallel research alone. This is relevant to Thread A's orchestration report — the debate vs. aggregation question has implications for the orchestration framework choice. LangGraph's explicit state machines are better suited for the two-phase deliberation architecture than CrewAI's linear workflow model.

**Flag 5 (validates Thread B on evaluation):** The MAJ-EVAL finding (auto-construct evaluator personas from domain documents for better human alignment) directly informs Thread B's Evaluator design. If the L4 Evaluator uses auto-constructed personas from Keystone methodology documents, it should be calibrated against the same consulting standards that the L1.5 Deliberation phase is trying to satisfy. The Evaluator and Deliberation Layer share a quality standard that should be explicitly encoded.

**Flag 6 (97% multi-turn jailbreak claim):** Verified (arXiv:2503.10619, ICON January 2026). The deliberation chain is a multi-turn system. Adversarial testing via PyRIT's Crescendo attack should be a pre-deployment requirement, not optional security testing. The 97% success rate means deliberation chains are almost certainly exploitable without mitigations.
