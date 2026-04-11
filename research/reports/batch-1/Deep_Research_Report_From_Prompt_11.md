# Multi-agent deliberation is mostly theater — here's what actually works

**Naive multi-agent debate is mathematically equivalent to noise.** A NeurIPS 2025 Spotlight paper proves that debate between LLM agents forms a martingale — the expected value of beliefs remains unchanged across rounds — meaning majority voting alone captures virtually all performance gains previously attributed to debate. But this doesn't doom the Keystone Deliberation Layer. It means the layer must be engineered with specific, empirically validated interventions that break the martingale: cross-provider model diversity, curmudgeon agents, diversity-aware message filtering, and structured disagreement tracking. The research identifies exactly which patterns to USE, LEARN from, or SKIP, and reveals that the most promising path combines independent parallel analysis with sophisticated aggregation rather than iterative debate.

---

## The martingale problem kills naive debate architectures

The most consequential finding for Keystone comes from Choi, Zhu, and Li at the University of Wisconsin. Their paper "Debate or Vote: Which Yields Better Decisions in Multi-Agent LLMs" (NeurIPS 2025 Spotlight) models multi-agent debate as a Dirichlet-Compound-Multinomial stochastic process and proves **Theorem 2: an agent's belief in the correct answer forms a martingale**, where E[α_{i,t+1} | α_{i,t}] = α_{i,t}. Debate rounds add noise without directional improvement.

The empirical results are stark. With Qwen2.5-7B-Instruct across seven benchmarks, majority voting (no debate) achieved **0.7691 average accuracy** while the best debate variant reached only 0.7377. With Llama3.1-8B-Instruct, voting hit **0.7242** versus 0.6990 for the best debate configuration. On arithmetic tasks, voting achieved 0.99 while the best debate variant scored only 0.84 — and centralized debate collapsed to 0.43. More rounds consistently degraded performance. **Evidence quality: Verified** — peer-reviewed NeurIPS Spotlight with formal proofs and published code.

Three targeted interventions break the martingale. **MAD-Oracle** freezes correct answers once generated, creating directional drift (impractical but proves the principle). **MAD-Conformist** locks responses matching the previous round's majority vote, using majority agreement as a proxy for correctness. **MAD-Follower** adopts the majority response with 30% probability each round. Both practical variants consistently outperform vanilla debate, demonstrating that asymmetric update rules — preserving correct-leaning signals while allowing incorrect ones to be revised — are the key architectural insight.

Wu et al.'s "Can LLM Agents Really Debate?" (McGill/Mila, November 2025) reinforces this from a different angle. Across 17 different LLMs on structured logic puzzles, they find that **intrinsic reasoning strength is the dominant performance predictor** — the strongest agent's accuracy effectively upper-bounds team performance. Majority pressure suppresses independent correction to **below 5% for weak agents** facing incorrect majorities. Their diversity metric Δ(A) shows cross-model-family heterogeneity provides modest but real gains, while hiding confidence scores between agents prevents over-confidence cascades. Single-pass debate suffices; additional rounds entrench errors. **Evidence quality: Credible** — reputable institutions, rigorous methodology, but currently a preprint.

**Recommendation for Keystone: LEARN from both papers.** Design the Deliberation Layer around independent parallel analysis with structured aggregation, not iterative debate. Implement asymmetric update rules. Limit deliberation to 1-2 rounds maximum. Use majority voting as the core mechanism, with debate serving transparency and disagreement detection rather than accuracy improvement.

---

## Three competing MoA architectures reveal when diversity beats quality

The Self-MoA versus Attention-MoA versus Society of Thought trilogy appears contradictory but resolves cleanly once you distinguish task types and aggregation sophistication.

**Self-MoA** (Li et al., ICLR 2025 submission) demonstrated that a single top model generating 4-6 diverse outputs at temperature 0.7 and then aggregating them outperforms mixed-model MoA by **+6.6% on AlpacaEval 2.0** and +3.8% average across MMLU, CRUX, and MATH. The mechanism is simple: mixing models introduces diversity but lowers average quality, and the quality cost typically outweighs the diversity benefit. Self-MoA needs only one API provider, making it operationally simpler. However, the study primarily used **7B-class models** and chat-oriented benchmarks — whether this holds at frontier scale on hard analytical tasks remains unvalidated. **Evidence quality: Verified** (200+ experimental configurations) but **Stale** (February 2025, 13+ months old).

**Attention-MoA** (Wen et al., January 2026) directly contradicts Self-MoA. An ensemble of small open-source models (12B-32B parameters: Mistral-Small-3.2-24B, Qwen3-32B, Gemma-3-12b, Llama-4-Scout-17B, gpt-oss-20b) with inter-agent semantic attention achieved **8.83 on MT-Bench** versus Claude-4.5-Sonnet's 8.62 and GPT-4.1's 8.59. The large configuration (Claude-4.5-Sonnet, Gemini-2.5-Pro, GPT-4.1, Qwen-Max, DeepSeek-V3.1) hit **91.15% on AlpacaEval 2.0 LC** and 9.32 on MT-Bench. The key innovation is replacing naive concatenation with a **cross-agent critique-and-refine process** where each agent generates natural language instructions to critique peer responses, plus inter-layer residual connections that maintain historical context and prevent information degradation at depth. Adaptive early stopping reduces inference tokens by ~11%. **Evidence quality: Credible** — detailed experiments but not peer-reviewed.

The resolution: **Self-MoA tested against naive concatenation; Attention-MoA fundamentally changed the aggregation mechanism.** Simple aggregation fails; structured deliberation succeeds. Both papers evaluated primarily on chat/instruction-following benchmarks — neither tests hard analytical reasoning.

**Society of Thought** (Kim, Lai, Scherrer, Agüera y Arcas, Evans — Google/UChicago/Santa Fe, January 2026) reveals something deeper. Frontier reasoning models like DeepSeek-R1 and QwQ-32B **spontaneously simulate multi-agent-like interactions within their chain of thought** — question-answering sequences, perspective shifts, conflict, and reconciliation. These behaviors emerge from RL training for accuracy alone, not explicit instruction. Causally, amplifying the internal "surprise/realization" feature (Feature 30939 in DeepSeek-R1-Llama-8B via sparse autoencoder steering) **nearly doubles accuracy from 27.1% to 54.8%** on the Countdown arithmetic task. The paper draws on Mercier and Sperber's argument that human reasoning evolved as a social process, suggesting that robust reasoning is inherently dialogical. **Evidence quality: Verified** — mechanistic interpretability with causal interventions, from very high-prestige authors.

This does *not* make explicit multi-agent deliberation redundant. A single model's internal "personas" share the same knowledge base, training biases, and blind spots. Explicit multi-agent systems win when genuine model diversity is needed, when specialized domain expertise spans multiple models, when structured disagreement must be auditable, and when context windows are insufficient for the required deliberation depth.

| Paper | Core claim | Task focus | Recommendation |
|-------|-----------|------------|----------------|
| Self-MoA | Single model beats mixed MoA | Chat + some analytical (7B) | **LEARN** — use pattern for cost-effective sampling |
| Attention-MoA | Structured multi-model beats frontier | Chat/instruction | **LEARN** — adopt semantic attention for aggregation |
| Society of Thought | Models already deliberate internally | Hard reasoning (GPQA, MATH) | **LEARN** — validates deliberation as fundamental |

---

## The implementation landscape: what's production-ready

**Together AI's Mixture-of-Agents** (Wang et al., ICLR 2025 Spotlight, ~266 citations) remains the most practical starting point. The core is genuinely implementable in ~50 lines: define reference models, call them in parallel, concatenate outputs into an aggregator prompt. The key architectural insight is role differentiation — **final performance is more sensitive to aggregator quality than proposer quality**. Some models excel as proposers (generating diverse reference responses), others as aggregators (synthesizing coherently). The default 3-layer, 6-proposer architecture achieves 65.1% LC win rate on AlpacaEval 2.0 versus GPT-4o's 57.5%, using only open-source models. MoA-Lite (2 layers) still beats GPT-4o by 1.8%. **Evidence quality: Verified.** **Recommendation: USE** — adopt the propose-then-aggregate pattern and role differentiation as Keystone's foundation.

**Du et al.'s foundational LLM Debate** (ICML 2024) established that multi-agent debate improves factuality by +7-15% across arithmetic, GSM8K, biographies, and MMLU using ChatGPT-era models. The critical mechanistic insight for Keystone: **"ease of persuasion" functions as a confidence signal.** Facts the model is confident about are nearly impossible to change through debate; facts it's uncertain about shift easily. This naturally surfaces factual uncertainty without explicit confidence scoring. The paper also showed that all agents sometimes start wrong yet converge to correctness through cross-verification — debate genuinely produces emergent correction, not just amplification. **Evidence quality: Verified.** **Recommendation: LEARN** — steal the debate prompt pattern and the persuasion-as-confidence metric, but don't build iterative debate into the core architecture given the martingale finding.

**A-HMAD** (Zhou and Chen, November 2025) adds three innovations over vanilla debate: role-specialized agents (solver, verifier, strategic planner, domain expert) yielding +3.5% over homogeneous agents; dynamic routing that selects relevant agents per round; and a learned consensus module achieving +5% accuracy on disagreement cases. The learned consensus module is trained on debate transcripts with known ground truth — a trainable weighted voting mechanism using consistency, confidence, and reliability features. **Evidence quality: Credible** — peer-reviewed journal but not a top ML venue, and no public code repository found despite claims. **Recommendation: LEARN** — adopt role specialization (maps directly to Keystone's bull/bear/contrarian/consensus) and the concept of trained aggregation, but build from scratch given reproducibility concerns.

**Anthropic's multi-agent research system** (June 2025) is the closest verified production analog to Keystone. Claude Opus 4 as lead researcher spawns 3-5 Claude Sonnet 4 subagents in parallel, each with independent research tasks. Multi-agent **outperformed single-agent Opus 4 by 90.2%** on internal research evaluation. Token usage explains 80% of performance variance. Multi-agent uses ~15× more tokens than chat. Key lessons: effort scaling rules embedded in prompts (simple = 1 agent; complex = 10+ subagents), "start wide then narrow" search strategy, and end-state evaluation rather than turn-by-turn analysis. Critical failures included agents spawning 50 subagents for simple queries and consistently preferring SEO-optimized content farms over authoritative sources. **Evidence quality: Verified** — first-party engineering blog. **Recommendation: USE** as primary architecture reference for the research orchestration layer, but note it lacks the deliberation/debate component Keystone needs.

**AutoGen's SocietyOfMindAgent** wraps a group chat team as a single agent — architecturally elegant but containing no deliberation-specific logic (no voting, no convergence detection, no structured debate). Known encapsulation bugs in v0.4+, and Microsoft is shifting strategic focus to a broader Agent Framework, putting AutoGen into maintenance mode. **Evidence quality: Verified.** **Recommendation: SKIP** for production — adopt the team-as-agent wrapper pattern but build on LangGraph instead.

**Korokithakis's production workflow** (March 2026) uses Claude Opus 4.6 as architect, Sonnet 4.6 for implementation, and Codex + Gemini + Opus as cross-provider reviewers. The key insight: **cross-company model diversity is a "functional requirement rather than a preference"** because models from the same provider exhibit self-agreement bias — they rarely robustly critique each other's outputs. This is confirmed by multiple academic studies showing homogeneous agents converge on shared biases. **Evidence quality: Credible.** **Recommendation: LEARN** — adopt cross-provider diversity as a Deliberation Layer requirement.

**Evans et al. "Agentic AI and the next intelligence explosion"** (Science, March 2026) provides the theoretical foundation: intelligence is "fundamentally plural, social, and relational" and agents should be able to "spawn internal societies of thought" with recursive sub-deliberations. The paper advocates drawing from organizational science — team composition, hierarchy, role differentiation, conflict norms — to design agent systems. **Evidence quality: Verified.** **Recommendation: LEARN** — use as intellectual framework for Deliberation Layer design principles.

---

## Adversarial testing tools and the propagation risk

The Deliberation Layer creates a compound attack surface: adversarial input to one agent can propagate through the deliberation chain via inter-agent message passing — functionally identical to indirect prompt injection.

**Promptfoo** (25.6k GitHub stars, MIT license, acquired by OpenAI March 2026) is the most mature tool. Multi-turn strategies including Crescendo (gradual escalation), GOAT (generative offensive agent tester), and Hydra are directly applicable to testing deliberation chains. Custom policy plugins can define deliberation-specific quality criteria. YAML-based configs enable CI/CD integration for regression testing. The Node.js foundation creates some friction with Python AI stacks. **Evidence quality: Verified.** **Recommendation: USE** for deliberation quality evaluation and regression testing.

**PyRIT** (Microsoft, 3.4k stars, v0.11.0, used in 100+ internal red teaming operations including Bing Chat and Copilot) is the strongest fit for adversarial robustness testing. Its Crescendo and TAP (Tree of Attacks with Pruning) orchestrators directly model how adversarial inputs propagate through multi-turn systems. The memory system tracks conversation state across sessions. Python-native integration is clean. Cross-domain prompt injection (XPIA) testing is directly relevant to agents processing each other's outputs. **Evidence quality: Verified.** **Recommendation: USE** for adversarial robustness testing of the deliberation chain.

**Garak** (NVIDIA, 6.9k stars, v0.13.3) is a systematic LLM vulnerability scanner — the "nmap of LLM security." Excellent for baseline per-model scanning before assembling agents into deliberation, but primarily single-turn and not designed for multi-agent interaction testing. **Evidence quality: Verified.** **Recommendation: LEARN** — adopt the probe/detector/score/report pattern for custom deliberation scanners; use directly for pre-deployment model vulnerability screening.

**DeepTeam** (Confident AI, ~1.3k stars, v1.0.0) covers 40-50 vulnerability types with multi-turn attack capabilities, but is relatively new and designed for single-agent systems. **Evidence quality: Credible.** **Recommendation: LEARN** — adopt patterns but too immature for production integration.

On the claimed statistics: **"prompt injection found in 73% of production deployments" is unverifiable.** Multiple security vendor blogs cite this figure, often attributing it to OWASP's 2025 Top 10 for LLM Applications, but the actual OWASP document contains no such percentage. The statistic appears to be circular-cited marketing content. **"Multi-turn jailbreaks reach 97% success in 5 turns" is verified** — from the Siege/Tempest paper (arXiv:2503.10619) achieving 97% on GPT-4 using BFS-style tree search on JailbreakBench, corroborated by ICON (January 2026) at 97.1% across eight LLMs. However, newer models show lower susceptibility, and real-world rates vary by attack framework and target.

The practical implication: the Deliberation Layer must treat all inter-agent messages as untrusted data. Recommended mitigations include sanitizing inter-agent messages, per-agent output validation, deliberation invariant checks (e.g., "bull-case agent must maintain positive thesis"), message provenance tracking, and redundant deliberation instances for high-stakes queries.

---

## How to build the Confidence Map and enforce genuine steelmanning

**DiscoUQ** (Jiang et al., March 2026) provides the most complete framework for structured disagreement tracking. Rather than binary agree/disagree, it extracts two complementary feature families: **linguistic structure features** (evidence overlap, minority argument strength, divergence depth — surface/intermediate/deep) and **embedding geometry features** (cluster distances, dispersion, cohesion of reasoning embeddings). It achieves AUROC 0.802 with calibration ECE of 0.036 versus 0.098 for baselines. Critically, the **largest improvements come in the "weak disagreement" tier** where simple vote counting fails — exactly the contested/moderate zone where the Confidence Map adds most value. **Evidence quality: Credible.** **Recommendation: USE** as the foundation for Confidence Map feature extraction.

**MAJ-EVAL** (Chen et al., submitted ICLR 2026) auto-constructs evaluator personas from domain-specific documents, then runs multi-agent in-group debate to produce evaluations that better align with human expert ratings than conventional metrics or single-LLM judges. For Keystone, this means auto-constructing evaluator personas from consulting methodology documents to assess whether the Confidence Map captures relevant analytical dimensions. **Evidence quality: Verified.** **Recommendation: USE** as the Deliberation Layer's quality evaluation framework.

**ReConcile** (ACL 2024) implements confidence-weighted roundtable discussion among diverse LLMs (ChatGPT, Bard, Claude2), achieving up to **11.4% improvement** over single-agent baselines. Even GPT-4 improves by 10% through discussion with other agents. The confidence-weighted voting architecture is production-ready. **Evidence quality: Verified.** **Recommendation: USE** — adopt confidence-weighted aggregation.

For the Confidence Map structure, the research supports a five-tier taxonomy:

| Level | Criteria | Keystone action |
|-------|---------|----------------|
| **High confidence** | >80% agreement, strong evidence overlap, deep convergence | Present as established finding |
| **Moderate confidence** | 60-80% agreement, moderate evidence overlap | Present with explicit caveats |
| **Weak confidence** | 50-60% agreement, low evidence overlap | Flag for human review — DiscoUQ shows this is where simple methods fail most |
| **Contested** | <50% agreement, strong minority arguments | Present both sides with steelmanned arguments |
| **Insufficient evidence** | Agents acknowledge knowledge gaps | Flag as requiring additional research |

For steelmanning enforcement, three mechanisms have empirical support. **Diversity-Aware Retention (DAR)** (March 2026) selects the subset of agent responses that maximally disagree with each other and the majority before broadcasting, preserving authentic dissent without modification. **The Curmudgeon Agent pattern** from CIR3 (peer-reviewed, ScienceDirect 2025) deploys a dedicated devil's advocate agent whose explicit role is to challenge majority positions, coupled with an external diversity score to prevent Collective Cognitive Convergence collapse. **Agent anonymization** reduces identity-driven sycophancy and self-bias during debate rounds. Additional validated mechanisms include hiding confidence scores during deliberation (collecting them only at aggregation), requiring explicit agree/disagree statements with justification, and using sparse communication topologies that sustain independent reasoning longer.

---

## Answering the six architectural questions

**A. Debate vs. Independent Analysis + Aggregation.** The evidence strongly favors **independent parallel analysis with structured aggregation**, not iterative debate. The martingale proof (Verified) shows naive debate adds noise. Wu et al. (Credible) show single-pass suffices. The optimal hybrid: run independent analyses from diverse models with assigned perspectives, then aggregate using confidence-weighted voting with a curmudgeon challenge round — one structured critique pass, not open-ended debate.

**B. Perspective Maintenance.** Four mechanisms prevent convergence to polite agreement: (1) different model families for each perspective (Claude for bear case, GPT for bull case, Gemini for contrarian) create genuine blind-spot diversity; (2) DAR-style diversity-aware filtering broadcasts only dissenting messages, forcing engagement with counterarguments; (3) agent anonymization strips identity cues that trigger sycophancy; (4) the curmudgeon agent pattern explicitly rewards challenging the majority. Critically, **hide confidence scores during deliberation** — visibility triggers over-confidence cascades that amplify majority pressure.

**C. Cross-Company Model Diversity vs. Same-Model Diverse Prompting.** Cross-company diversity produces genuinely different analytical outputs because models have different training data, RLHF preferences, and architectural biases. Same-model prompting (e.g., "be bullish" vs. "be bearish") produces weaker diversity because the underlying knowledge base and reasoning patterns are identical. Self-MoA shows same-model sampling works well for simple tasks where quality dominates, but for analytical research where detecting blind spots matters, **cross-provider diversity is a functional requirement** (confirmed by Korokithakis's production experience, Wu et al.'s diversity metric, and ReConcile's cross-model results). The cost differential is manageable: multi-provider APIs add operational complexity but not dramatically higher per-token costs, especially with DeepSeek V3.2 at $0.28/M input tokens filling a cost-effective analytical role.

**D. Working Systems for Analytical Research.** No production multi-agent deliberation system specifically for analytical research (not coding, not chat) was found in the literature. Anthropic's multi-agent research system is the closest analog but uses parallel independent search, not deliberation. The Aragora project (open-source) implements 3-agent debate with decision receipts but lacks production validation. **This is a genuine gap** — the Keystone Intelligence Engine would be novel in applying deliberation specifically to consulting research.

**E. Confidence Map Structure.** Use the five-tier taxonomy above, powered by DiscoUQ's disagreement feature extraction. For each claim in the Confidence Map, track: vote distribution, evidence overlap score, minority argument strength, divergence depth (surface/intermediate/deep), and embedding-space cluster geometry. The "weak confidence" tier (50-60% agreement) is the most critical to instrument well — this is where simple methods fail and where human reviewers need the most guidance.

**F. Steelmanning Enforcement.** The curmudgeon agent pattern (CIR3) plus DAR-style diversity-aware filtering are the two strongest mechanisms. Supplement with: explicit agree/disagree requirements in each agent's output format, anonymization during deliberation, sparse communication topology (not all-to-all), and a post-deliberation steelmann verification step where a separate agent checks whether minority positions were engaged substantively rather than dismissed.

---

## Recommended Keystone Deliberation Layer architecture

Based on the full evidence base, the Deliberation Layer should implement a **two-phase architecture**:

**Phase 1 — Independent Parallel Analysis.** Four agents with assigned perspectives (bull, bear, contrarian, consensus) generate independent analyses using different model providers. No inter-agent communication. Each agent produces structured output: thesis, key evidence, confidence signals, and explicit uncertainties. This captures the proven value of diversity and independent reasoning without the martingale problem of iterative debate.

**Phase 2 — Structured Aggregation with Curmudgeon Challenge.** A strong aggregator model receives all four analyses. DAR-style filtering highlights maximum disagreement points. A dedicated curmudgeon agent challenges the emerging consensus on contested claims. The aggregator produces the Confidence Map using DiscoUQ-style feature extraction: vote distribution, evidence overlap, minority argument strength, and divergence depth. One structured critique round maximum.

**Orchestration: LangGraph** — explicit state machines, checkpointing, conditional routing, human-in-the-loop gates. CrewAI is suitable for rapid prototyping but lacks production-grade state management. AutoGen should be skipped due to maintenance mode.

**Testing: Promptfoo** for deliberation quality regression testing (YAML test suites), **PyRIT** for adversarial robustness testing (Crescendo/TAP attacks against the deliberation chain), **MAJ-EVAL** for output quality evaluation with auto-constructed consulting personas.

**Cost architecture:** Tier 1 (routine queries): single frontier model, ~$0.01-0.05. Tier 2 (standard deliberation): 3 mixed-provider agents × 1 round + aggregation, ~$0.10-0.50. Tier 3 (deep deliberation): 4 frontier agents + curmudgeon + 2 aggregation rounds, ~$1-5. Route based on initial query complexity assessment.

## Conclusion

The field's most important recent discovery is negative: **naive multi-agent debate is a martingale that doesn't systematically improve outcomes beyond majority voting.** This finding, now proven mathematically, should fundamentally reshape how the Keystone Deliberation Layer is built. The path forward is not iterative debate but rather independent diverse analysis with sophisticated aggregation — using cross-provider model diversity for genuine perspective differences, curmudgeon agents and diversity-aware filtering for steelmanning enforcement, and DiscoUQ-style structured disagreement tracking for the Confidence Map.

The Society of Thought finding adds a crucial nuance: frontier reasoning models already simulate multi-agent deliberation internally, meaning explicit multi-agent architecture adds value primarily when it provides genuine knowledge diversity (different models know different things) or auditable structured disagreement (the Confidence Map itself is a product, not just an accuracy mechanism). For consulting research where both knowledge diversity and auditable reasoning matter, the multi-agent approach remains justified — but only when engineered with the specific interventions the evidence supports.

| Finding | Evidence | Recommendation |
|---------|----------|----------------|
| "Debate or Vote" — debate is a martingale | **Verified** (NeurIPS 2025 Spotlight) | **LEARN** — design around this constraint |
| Wu et al. — diversity & reasoning strength dominate | **Credible** (preprint, McGill/Mila) | **LEARN** — maximize agent quality, use heterogeneous models |
| Self-MoA — single model beats mixed MoA | **Verified** (ICLR 2025) | **LEARN** — use for cost-effective sampling on simple tasks |
| Attention-MoA — structured multi-model beats frontier | **Credible** (preprint, Jan 2026) | **LEARN** — adopt semantic attention aggregation pattern |
| Society of Thought — internal deliberation emerges | **Verified** (Google/UChicago, Jan 2026) | **LEARN** — validates deliberation as fundamental mechanism |
| Together AI MoA — propose-then-aggregate | **Verified** (ICLR 2025 Spotlight) | **USE** — adopt as architectural foundation |
| Du et al. LLM Debate — persuasion as confidence | **Verified** (ICML 2024) | **LEARN** — steal persuasion-as-confidence metric |
| A-HMAD — role specialization + learned consensus | **Credible** (journal, Nov 2025) | **LEARN** — adopt role specialization concept |
| AutoGen SocietyOfMindAgent | **Verified** (active but maintenance mode) | **SKIP** — strategic risk, no deliberation logic |
| Evans et al. Science 2026 | **Verified** (Science) | **LEARN** — theoretical framework for compositional intelligence |
| Korokithakis cross-provider workflow | **Credible** (blog, March 2026) | **LEARN** — cross-provider diversity as requirement |
| Anthropic multi-agent research | **Verified** (engineering blog, June 2025) | **USE** — primary architecture reference for orchestration |
| Promptfoo | **Verified** (25.6k stars, OpenAI acquisition) | **USE** — deliberation quality testing |
| PyRIT | **Verified** (Microsoft, 100+ operations) | **USE** — adversarial robustness testing |
| Garak | **Verified** (NVIDIA, 6.9k stars) | **LEARN** — probe/detector pattern |
| DeepTeam | **Credible** (v1.0.0, early) | **LEARN** — vulnerability-metric-attack architecture |
| MAJ-EVAL | **Verified** (ICLR 2026 submission) | **USE** — output quality evaluation |
| DiscoUQ | **Credible** (preprint, March 2026) | **USE** — Confidence Map feature extraction |
| ReConcile | **Verified** (ACL 2024) | **USE** — confidence-weighted voting |
| DAR diversity-aware retention | **Credible** (preprint, March 2026) | **USE** — steelmanning enforcement |
| CIR3 curmudgeon agent | **Verified** (peer-reviewed journal) | **USE** — perspective maintenance |
| LangGraph | **Verified** (v1.0, most popular framework) | **USE** — orchestration runtime |
| 73% prompt injection prevalence | **Claimed** — unverifiable, not from OWASP | Treat as marketing statistic |
| 97% multi-turn jailbreak success | **Verified** (with caveats — specific tool/model) | Design inter-agent message sanitization |