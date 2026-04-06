# Report 14: D1 — Best AI Agent Systems by Individuals/Small Teams

## Source
`research-reports/Deep_Research_Report_From_Prompt_14.md`

---

## Top Findings

### Finding 1: The specification layer dominates system quality — proven across 6 independent systems
**Pipeline layer affected:** L0 (Specification Engine)
**Evidence quality:** Verified

Every successful project in this report converged independently on the same conclusion: the specification layer, not the model layer, determines output quality. The proof is Superpowers (120K stars): it produces identical results across 8 different LLM platforms (Claude Code, Cursor, Codex CLI, OpenCode, Gemini CLI, Qwen Code, Goose CLI, Auggie). If the implementing model were doing real cognitive work, platform-switching would degrade quality. It doesn't. ATLAS's finding that its synthesis/decision agent was downweighted to minimum weight (0.3) confirms the same from the orchestration side: even sophisticated 4-layer systems can't compensate for weak specification at the synthesis layer.

**What it means for the build:** The CAPSTONE-PLAN-v2.md already designates L0 as the highest-value component, but this report provides concrete implementation guidance that the plan lacks. Superpowers' key technique — writing plans "as if for an enthusiastic junior engineer with poor taste, no judgment, no project context, and an aversion to testing" — is the most actionable framing for RESEARCH.md task decomposition found in any report. Every task description in the research-tasks.json should be written at this level of specificity.

---

### Finding 2: Subagent review loops are waste; critique-with-loop-back to retrieval is not
**Pipeline layer affected:** L4 (Evaluator), L1 (Research Agents)
**Evidence quality:** Verified

Superpowers ran regression testing: dispatching a fresh agent to review plans added 25 minutes of execution time without improving plan quality (5 versions x 5 trials, identical quality scores). An inline self-review checklist replaced the entire review layer at 1/50th the cost, catching 3-5 bugs per run in ~30 seconds. This directly challenges any design that adds agents to solve quality problems. However, the 199-bio 8-phase pipeline demonstrates that critique-with-loop-back is different: Phase 7 (Critique) triggers additional targeted searches when gaps are detected, not a fresh agent reviewing the same information. The distinction is: review loops over identical information = waste; retrieval gaps + targeted new information + loop-back = genuine quality improvement.

**What it means for the build:** The Evaluator should not dispatch a new research agent to re-research a rejected finding. It should identify the specific gap that caused rejection, add that gap as a new targeted retrieval task, and loop only the gap-filling retrieval. This is more efficient and more effective than full re-generation.

---

### Finding 3: ATLAS proved the orchestration/synthesis layer is always the bottleneck — and quantified it
**Pipeline layer affected:** L1.5 (Deliberation), L2 (Content Structuring)
**Evidence quality:** Credible (self-reported, not independently audited, but specific and mechanistic)

ATLAS's 25-agent system (+22% returns over 173 days) discovered empirically that its CIO synthesis agent was the bottleneck. The Darwinian evolution mechanism downweighted it to 0.3 — the minimum — over 378 trading days. Over 54 prompt modification attempts, only 16 survived (30% keep rate). The system's own self-improvement identified that the synthesis layer's specification quality was the binding constraint, not the specialist agents. This is the strongest production evidence that investing in synthesis/orchestration quality yields more return than adding more specialist agents.

**What it means for the build:** Layer 1.5 (Deliberation) and L2 (Content Structuring) deserve more engineering investment than the plan currently allocates. The synthesis layer should be the most carefully specified, most heavily evaluated component after L4. Consider implementing ATLAS's rolling quality score mechanism for the synthesis agents specifically.

---

### Finding 4: The instinct-to-skill evolution system in everything-claude-code is the best existing implementation of the Rejection Library concept
**Pipeline layer affected:** META (Self-Improvement Loop)
**Evidence quality:** Credible (deployed production system, well-documented architecture)

Everything-claude-code's instinct-to-skill pipeline is architecturally the closest existing system to CAPSTONE-PLAN-v2.md's Rejection Library. Hooks capture every tool call and outcome at 100% reliability. A background Haiku agent detects patterns and creates atomic YAML+Markdown "instincts" with confidence scores (0.3–0.9), domain tags, evidence trails, and confidence decay when contradicted. The `/evolve` command clusters related instincts into full skills. Version 2.1 adds project-scoped instincts that can promote to global scope. This is more granular and immediate than the plan's current Rejection Library design, which operates at the rejection/constraint level rather than the individual tool call level.

**What it means for the build:** The plan describes the Rejection Library as a collection of structured rejection entries. This report shows a more granular and automatic mechanism: capture every tool call outcome (not just rejections), detect patterns, create tentative instincts, cluster into skills. The plan's mechanism is a subset of what ECC does. Upgrade the design to capture positive patterns (what works) alongside negative patterns (what fails), not just rejections.

---

### Finding 5: LLM-as-judge requires calibration against human judgment; uncalibrated error rates exceed 50%
**Pipeline layer affected:** L4 (Evaluator)
**Evidence quality:** Verified (multiple independent sources cited)

Galileo's 2026 research documents position bias, length bias, and agreeableness bias in automated evaluators. The gold standard: calibrate against human judgment with a target of 0.80+ Spearman correlation using 100-200 expert-scored samples. This is not aspirational — the report cites this as the production standard from Anthropic's "Demystifying Evals for AI Agents" (January 9, 2026). Three-tier grading stack: code-based graders (L1, deterministic), model-based graders (L2, calibrated), human graders (L3, calibration reference). Capability evals that reach high pass rates "graduate" to regression suites.

**What it means for the build:** The CAPSTONE-PLAN-v2.md specifies an eight-dimension rubric calibrated against Keystone deliverables but does not quantify the calibration target or process. This report gives a concrete number: 0.80+ Spearman correlation from 100-200 expert-scored samples. This should be a Phase 1 build deliverable, not an aspiration. Without hitting this threshold, the Evaluator's rejections are noise rather than signal.

---

## Tool/Framework Verdicts

### LangGraph v1.x
- 100M+ monthly framework downloads, production at Klarna/Uber/JPMorgan/BlackRock, time-travel debugging, state forking, durable checkpointing for long-running tasks
- **Verdict: INTEGRATE**
- The only mature runtime with both the checkpointing system Keystone needs for long-running research tasks and the time-travel debugging required to diagnose pipeline failures.

### 199-bio 8-phase deep-research-skill
- 8-phase autonomous pipeline (Scope → Plan → Retrieve → Triangulate → Outline → Synthesize → Critique → Package), First Finish Search adaptive quality thresholds, critique loop-back to retrieval when gaps detected
- **Verdict: INTEGRATE as research agent skeleton**
- This is the closest existing implementation to Keystone's L1 research agent design; the critique loop-back to retrieval is the self-healing mechanism the plan describes but doesn't specify.

### ATLAS Darwinian prompt evolution mechanism
- Rolling Sharpe ratio scoring per agent, worst performer gets prompt rewritten, 5-day test, keep or revert, 30% keep rate over 378 days
- **Verdict: LEARN**
- The mechanism transfers directly to research quality scoring, but requires defining a research quality metric (not Sharpe ratio) before the loop can run; design in Phase 1, implement in Phase 3.

### everything-claude-code instinct-to-skill pipeline
- Hook-based capture of all tool calls, Haiku background agent for pattern detection, YAML+Markdown atomic instincts with confidence decay, `/evolve` clustering into skills
- **Verdict: INTEGRATE**
- This is a more granular and automatic implementation of the Rejection Library concept; adopt the hook-and-observe pattern for the META layer.

### Engram MCP server (199-bio)
- BM25 + ColBERT + Knowledge Graph hybrid search, Jina v5 semantic search at ~9ms/query on Apple Silicon, temporal memory decay, 80% on LOCOMO benchmark
- **Verdict: INTEGRATE**
- The temporal decay model (important memories persist, trivial ones fade) is architecturally superior to pure vector similarity for trajectory storage.

### AIDE tree-search variant of autoresearch
- Population-based tree search instead of linear ratchet, escapes local optima, GitHub: WecoAI/AIDE
- **Verdict: LEARN**
- The linear ratchet in Karpathy's original hits local optima (documented in Issue #22); AIDE's tree-search is the fix. Design the META loop to support population-based variants.

### Atomic Agents (BrainBlend AI)
- Schema-aligned chaining where agents connect through matching Pydantic input/output schemas
- **Verdict: LEARN**
- The schema-alignment approach to handoff contracts is concrete engineering for what CAPSTONE-PLAN-v2.md calls "handoff contracts"; study for the handoff contract design.

### Generator-Reflector-Curator pattern (47billion, 2026)
- Generator produces output, Reflector evaluates and refines, Curator extracts learnings into persistent playbook; +10.6% on agent benchmarks without model fine-tuning
- **Verdict: INTEGRATE**
- This is the closed loop between evaluation and memory that the plan describes but doesn't specify mechanically; +10.6% benchmark improvement is directly reproducible.

### Artemis (TurinTech, arxiv:2512.09108)
- Population-based evolutionary optimization of full agent configurations (prompt + tools + workflow); 9.3–36.9% improvements across 4 agent systems
- **Verdict: LEARN**
- The "entire agent as optimizable genome" concept is the long-term direction for META-layer evolution; defer implementation to Phase 3.

### OpenClaw (Steinberger)
- Autonomous always-on agent, SKILL.md universal format, 135K+ exposed instances, ClawHavoc supply chain attack planted 800+ malicious skills
- **Verdict: LEARN (architecture) / SKIP (direct integration)**
- The SKILL.md format convention is worth adopting; the open ecosystem model is a documented security failure. Do not expose any Keystone skill ecosystem without cryptographic signing and sandboxed execution.

### AgentShield (everything-claude-code)
- Three-agent red-team/blue-team/auditor pipeline, 1,282 tests, 98% coverage, 102 static analysis rules
- **Verdict: LEARN**
- The three-agent red-team pattern is directly applicable for testing the Evaluator's anti-gaming robustness before production deployment.

### Dexter (virattt)
- Autonomous financial research agent with built-in LLM-as-judge evaluation suite using LangSmith
- **Verdict: LEARN**
- Closest existing analog to Keystone's research agent with integrated evaluation; study the evaluation suite design for Keystone's L4.

### TradingAgents (Tauric Research)
- Multi-agent debate between fundamental, sentiment, and technical analysts before risk management evaluation
- **Verdict: LEARN**
- The multi-analytical-perspective debate pattern maps directly to Keystone's L1.5 Deliberation design.

---

## Contradictions with CAPSTONE-PLAN-v2.md

### Contradiction 1: The plan describes the Rejection Library as operating on rejections; this report shows the better implementation captures all tool calls, not just rejections

**What the plan says:** "Every evaluator rejection → structured entry → permanent constraint." The Rejection Library is triggered by failure.

**What the evidence shows:** ECC's instinct-to-skill pipeline captures every tool call and outcome at 100% reliability, not just failures. Positive patterns (what worked) are as valuable as negative patterns (what failed). The `/evolve` mechanism clusters both types.

**Which to follow:** The evidence. The plan's Rejection Library should be upgraded to an Observation Library: capture all tool calls, flag both successes and failures, detect patterns in both directions. This is more informative and enables the system to reinforce effective approaches, not only avoid ineffective ones.

---

### Contradiction 2: The plan doesn't quantify the evaluator calibration target; this report provides a specific production standard

**What the plan says:** "Calibrate [the rubric] against actual Keystone deliverables scored by experienced consultants." Process is described but no threshold specified.

**What the evidence shows:** Anthropic's production standard is 0.80+ Spearman correlation from 100-200 expert-scored samples. Below this threshold, automated evaluator scores are unreliable signal.

**Which to follow:** The evidence. Add 0.80+ Spearman as a hard requirement before the Evaluator is considered production-ready. This makes the calibration phase a binary gate, not a subjective assessment.

---

### Contradiction 3: The plan implies the synthesis/orchestration layer is coordination infrastructure; this report shows it is the quality ceiling

**What the plan says:** Section 4.1 describes parallel research agents under strict isolation and the Deliberation layer synthesizing findings. The emphasis is on the research agent quality.

**What the evidence shows:** ATLAS's Darwinian evolution discovered empirically that the synthesis layer was the bottleneck, not the specialist agents. The MAESTRO framework confirms MAS architecture (not model selection or tool changes) is the dominant driver. The orchestration bottleneck is universal across all production systems reviewed.

**Which to follow:** The evidence modifies the plan's priority ordering. L1.5 (Deliberation) and L2 (Content Structuring) should be treated with the same engineering intensity as L0 (Specification Engine), not as coordination infrastructure.

---

## Cross-Report Flags

**Reinforces Report D2 (Academic Papers):** The MAST taxonomy finding that specification and system design issues cause 36.9% of failures aligns with D1's finding that the specification layer determines quality. Both reports independently converge on the same root cause of agent system failures.

**Reinforces Report D3 (10x Ideas):** D1's finding about the synthesis layer being the bottleneck connects to D3's finding about causal inference as a synthesis capability. If the synthesis layer is the quality ceiling, investing in richer synthesis methods (causal vs. correlational) is the highest-leverage improvement.

**Potentially contradicts Report A1/A2 (not read by this thread):** D1 reports that LLM-as-judge error rates exceed 50% without calibration, which would affect the Evaluator design in Report A2. Flag for synthesis: the calibration requirement (0.80+ Spearman from 100-200 samples) should be consistent across all evaluator-related reports.

**Flags for synthesis agent:** The ECC instinct-to-skill pipeline (112K stars, production-deployed) is the strongest existing implementation of CAPSTONE-PLAN-v2.md's META-layer design. If Report A3 on self-improvement loops reached different conclusions, the two should be reconciled. The ECC implementation should be a primary reference for META-layer design regardless of what other reports found.
