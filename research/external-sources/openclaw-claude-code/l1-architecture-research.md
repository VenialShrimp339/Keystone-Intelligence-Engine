# L1 research execution architecture for Keystone

**Bottom line: adopt a two-tier orchestrator-worker pattern inside each L1 task — a `LeadResearcher` (FLAGSHIP, planning only) that dispatches 3–5 `SubResearcher` workers (STANDARD, grounded retrieval) via an in-process Fork-style mechanism, with a task-scoped `SourceLedger` preventing duplicate reads, and a structured synthesis step (never peer debate) that emits the existing `StructuredFinding` contract unchanged.** This is the minimum architecture that closes the McKinsey-analyst-week quality gap while preserving all ten invariants. The evidence base converges with unusual consistency: centralized orchestration beats peer debate and independent swarms (DeepMind 2025: 17.2× → 4.4× error-amplification reduction), four workers is the empirical elbow (DeepMind 2025, Anthropic Research), diversity belongs in *methodology and query-framing*, not personas or model identity (DMAD ICLR 2025, Self-MoA, STORM NAACL 2024), and multi-round debate is a mathematical martingale with no expected gain over weighted synthesis (Choi/Zhu/Li, NeurIPS 2025 Spotlight). The proposal is deliberately opinionated: shallow-and-wide inside each task, no recursive sub-sub-dispatch, no peer mailboxes, no shared scratch. Estimated cost: **~3.3× current STANDARD baseline** (not 15×) because Keystone already operates at a small shared-prefix size and Fork dispatch amortizes the 15k task brief across 5 workers at 0.1× cache-read pricing.

## 1. What the evidence actually says

The 2024–2026 literature disagrees with itself on many things, but agrees on six that matter for this design.

**Centralized orchestration dominates on decomposable work.** The Google Research / DeepMind "Towards a Science of Scaling Agent Systems" study (Kim et al., arXiv 2512.08296, December 2025) ran 180 configurations across five topologies and four benchmarks. Independent parallel agents amplified errors **17.2×** through unchecked propagation; centralized orchestration contained amplification to **4.4×**. On Finance-Agent (the benchmark most analogous to consulting decomposition), centralized MAS delivered **+80.9%** over single-agent baseline. On BrowseComp-Plus, independent swarms *lost* 35%. The predictive model picks the best topology 87% of the time on unseen configurations. The caveats matter — the study used tight per-agent token budgets, and a later revision dropped cross-validated R² from 0.513 to 0.373 — but the directional finding (centralized beats decentralized beats independent) is robust across three model families and four task types. **Confidence: HIGH on direction, MEDIUM on exact constants.**

**Peer debate is a mathematical martingale.** Choi, Zhu, and Li (NeurIPS 2025 Spotlight, arXiv 2508.17536) prove that iterative debate among homogeneous agents forms a martingale over collective belief: E[B_{t+1} | B_t] = B_t. Majority voting alone captures most of the gain attributed to multi-agent debate across seven NLP benchmarks, at a fraction of the token cost. Debate only helps if you *inject asymmetric signal* — oracle verification, tool-grounded evidence, or anti-conformist prompting. **Implication: lead-agent synthesis against external evidence (tool outputs, citations) is the right aggregation; multi-round worker chatter is waste.** Confidence: HIGH.

**Diversification lives in methodology and query-framing, not personas or models.** The ICLR 2025 DMAD paper (Liu et al., OpenReview t6QHYUOQL7) shows distinct *reasoning scaffolds* (CoT vs. Step-Back vs. Self-Contrast vs. Meta-Reasoning) produce consistent gains; distinct personas on the same scaffold do not. Self-MoA (Li et al., arXiv 2502.00674) delivers the counter-intuitive result: aggregating one strong model's diverse samples beats mixing weaker diverse models by **+3.8% to +6.6%** across MMLU/CRUX/MATH/AlpacaEval. STORM (Shao et al., NAACL 2024) gets **+25% organization** and **+10% breadth** over RAG baselines via perspective-guided question asking — source diversity is mechanically downstream of query-framing diversity. **This is what the existing 4-lens L1.5 deliberation already does correctly — the L1 layer should follow the same pattern.** Confidence: HIGH.

**The optimal parallelism elbow is N≈4.** DeepMind's study finds coordination benefits plateau at N≈4 and turn negative past N≈8; redundancy coefficient is 0.41–0.50 (45% of subtasks are redundant even in centralized topologies). Anthropic's June 2025 blog independently converged on the same number: "2–4 subagents with 10–15 tool calls each" for comparison queries. Capability saturation at single-agent baseline >45% is real — if one agent already handles the sub-question well, adding more hurts. **Confidence: HIGH on directional elbow, MEDIUM on the exact constant (task-dependent).**

**Anthropic's multi-agent research system is the reference implementation.** Their June 13, 2025 engineering blog reports the orchestrator-worker pattern (Opus lead + Sonnet workers) outperformed single-agent Opus by **90.2%** on internal breadth-first evals. Token usage alone explained **80%** of BrowseComp variance. Cost: **~4× vs. chat for parallelism, ~15× for full Agent Teams**. They explicitly document the failure modes Keystone must avoid: SEO-farm preference over authoritative sources, duplicated work from vague delegation, hallucinated citations. Their fix was (a) teach the orchestrator how to delegate with explicit objective/format/tools/boundaries per subagent, (b) scale subagent count to query complexity, (c) use end-state evaluation on mutating state, (d) write artifacts to filesystem and pass references to avoid "game of telephone." Confidence: HIGH.

**Cognition's June 12, 2025 counter-post ("Don't Build Multi-Agents") is the important dissent.** Their argument: multi-agent systems suffer from dispersed decision-making and lack of shared context; a single long-running agent with careful context management is preferable. This dissent *is correct for coding agents* where decisions are sequential and state-mutating. It is *incorrect for research synthesis* where sub-questions are decomposable and independent-evidence-gathering is the load-bearing operation. Keystone's domain is research, not codebase modification — the orchestrator-worker pattern is indicated. Confidence: HIGH.

Alongside these, three findings must constrain the design:

**MAST taxonomy (Cemri et al., arXiv 2503.13657, Berkeley):** across 1,642 annotated MAS traces, 17.1% of failures are Step Repetition, 11.0% Disobey Task Specification, 36.9% Inter-Agent Misalignment. Frameworks fail at **41–86.7% rates**. The authors' key finding: *failures are architectural, not model-bounded*. Layered verification (not a single verifier) is mandatory. **AgentLeak (El Yagoubi et al., arXiv 2602.11510):** inter-agent messages leak at **68.8%** in standard frameworks; output-only audits miss ~40% of real privacy leakage. **Context rot (Chroma Research, 2025):** all 18 frontier models degrade monotonically with input length; logical structure can *worsen* distraction because plausible distractors cluster with the target.

Together these three justify Keystone's existing isolation and verification invariants (#1, #6, #7) — sub-agent dispatch must not weaken them.

## 2. Why current Keystone L1 can't hit the McKinsey bar

The current `AgentPool.execute_all` loop produces one `ResearchAgent` per `ResearchTask`. Each agent performs 3 rounds of parallel tool calls, synthesizes via a single LLM call, and emits a `StructuredFinding`. The arithmetic ceiling is ~50 tasks × 5 tools × 3 rounds = 750 tool invocations, but the **synthesis bottleneck is one LLM call per task** — an agent reading ~5 tool results and writing a coherent finding. That agent cannot simultaneously pursue five orthogonal analytical threads.

Consider a concrete competitive-landscape task from a typical engagement: *"Assess NewCo's competitive positioning in industrial-sensor fleet-management software."* A McKinsey team would split this across five workstreams: (a) TAM/SAM/SOM market sizing from analyst reports and filings; (b) competitor financial analysis across five named competitors via 10-K/10-Q extraction; (c) product feature-matrix construction from product docs, review sites, and analyst G2/Gartner reports; (d) customer-voice analysis from earnings calls, review sites, and RFP teardowns; (e) regulatory and standards landscape (ISA/IEC 62443, NIST, export controls). Each workstream reads 50–100 sources. Current Keystone collapses this into one agent with 5 tool calls and one synthesis pass.

The single-agent failure mode isn't that the tools are insufficient — `MCPGateway` can route all five workstreams — it's that **one synthesis context cannot hold five distinct analytical methodologies simultaneously without signal dilution**. Context-rot evidence (Chroma, 2025) shows even frontier models degrade non-uniformly past ~20 retrieved docs; plausible distractors (five competitor 10-Ks in one context) actively interfere. MAST FM-1.3 (Step Repetition, 17.1% of failures) and FM-2.4 (Information Withholding) both manifest as "the agent researched the easy workstream deeply and glossed the hard ones." That is exactly the current output quality complaint.

The second failure is **source coverage**. The summer workflow ingested 500+ sources per question because 5–6 human analysts ran independent retrieval trajectories with natural query-framing diversity. Current Keystone's single agent per task, with 3–5 tool calls per round, tops out at ~15–25 distinct URLs per task — ~1,000 per engagement — with no mechanism preventing different tasks from re-retrieving the same 10 popular analyst reports. Lane E evidence injection helps backfill from institutional memory but doesn't drive fresh coverage.

The fix is not "more tasks" (L0 already produces 15–50 MECE tasks and more would violate the MECE validator). The fix is **depth per task** via bounded orchestrator-worker dispatch inside the L1 layer.

## 3. Proposed architecture

### Overview

Replace the current one-agent-per-task model with a two-tier pattern *inside* `AgentPool.execute_all`. The calling contract — `AgentPool.execute_all(assignments) → list[StructuredFinding]` — does not change. One `StructuredFinding` still emits per task. CitationProcessor, L1.5, L2, and L4 see exactly what they see today.

```
AgentPool.execute_all(assignments)
│
├── for assignment in assignments:  # 15–50 tasks, concurrency-gated
│   │
│   ├── LeadResearcher(task, assignment.agent_def)          [FLAGSHIP, planning-only]
│   │   │
│   │   ├── plan_subqueries(task) → list[SubQuery]          [1 LLM call]
│   │   │   ├── 3–5 methodologically-distinct sub-questions
│   │   │   ├── each with: objective, output_schema, allowed_tools, framing, stop_criterion
│   │   │   └── rejects own plan if sub-queries overlap semantically (cosine > 0.85)
│   │   │
│   │   ├── SourceLedger(engagement_id, task_id)            [task-scoped, sibling-visible]
│   │   │
│   │   ├── asyncio.gather(  [N=3–5, return_exceptions=True]
│   │   │     SubResearcher(sq, ledger, shared_brief).run() for sq in subqueries
│   │   │ )
│   │   │   │
│   │   │   └── SubResearcher                              [STANDARD, Fork-dispatched]
│   │   │       ├── 1–2 rounds tool calls via MCPGateway (gateway preserved!)
│   │   │       ├── checks SourceLedger before reading URL; claims URL atomically
│   │   │       ├── synthesizes a PartialFinding with SUB-NNN-scoped claims + SRC/EV refs
│   │   │       └── returns PartialFinding OR dispatch_error
│   │   │
│   │   └── synthesize(partials, task) → StructuredFinding   [1 FLAGSHIP LLM call]
│   │       ├── citation union (SRC-NNN / EV-NNN refs preserved, SUB-NNN stripped)
│   │       ├── claim collation (not averaging — each claim keeps its attribution)
│   │       ├── consistency check: cross-subagent contradiction flagged in finding
│   │       └── emits the same StructuredFinding the existing pipeline consumes
│   │
│   └── yield StructuredFinding  → downstream unchanged
```

### Component specifications

**`LeadResearcher` (new class, `keystone/l1/lead_researcher.py`).** Replaces the direct `ResearchAgent` construction in `_build_assignments`. FLAGSHIP tier (claude-opus-4.6 or claude-sonnet-4.6-with-extended-thinking depending on profile). Three responsibilities, no tool access of its own: (1) decompose the task into 3–5 sub-queries with genuinely different methodologies — market-sizing lens, competitor-financial lens, product-evidence lens, customer-voice lens, regulatory-lens for the competitive-landscape example; (2) construct the shared task brief (evidence passages, anti-confirmatory framing, citation requirements) that becomes the Fork-cached prefix; (3) synthesize partials into one `StructuredFinding`. The Lead never calls external tools — this keeps FLAGSHIP tokens low and preserves the tier-separation invariant (#7).

**`SubResearcher` (new class, extending current `ResearchAgent` semantics).** STANDARD tier. Receives: one `SubQuery`, a reference to the task-scoped `SourceLedger`, and the shared `renderedSystemPrompt` bytes from the Lead (enabling Fork-style cache hit). Executes 1–2 rounds of `MCPGateway.execute` against its sub-query-specific tool allowlist (`useExactTools: true` semantics — inherits parent tool pool, gateway mediation unchanged, `ToolAuthorizer` still active, circuit breaker still active). Emits a `PartialFinding` with claims carrying both `SRC-NNN`/`EV-NNN` refs *and* a `sub_id` field so the Lead can attribute at synthesis time. Anti-confirmatory framing is composed from the parent framing + sub-query-specific framing (both pass `tasks.py:165` validator).

**`SourceLedger` (new class, `keystone/l1/source_ledger.py`).** Task-scoped key-value store: `Dict[engagement_id, Dict[task_id, Dict[url_hash, ClaimRecord]]]`. Three operations: `claim(url_hash, sub_id)` returns True only if no sibling has claimed it — atomic via `asyncio.Lock`; `register_rejection(url_hash, reason)` for sub-agents that fetched but found the page irrelevant, surfaced to siblings to prevent re-attempts; `peer_finds(url_hash)` returns the sub_id and one-line synopsis of any sibling that already read this URL, letting the current sub-agent opt in to corroboration rather than duplication. **Critically: visible across siblings within a task; invisible across tasks.** This preserves task-level isolation (#6) while enabling source coverage within a task. Cross-task deduplication is already handled by `CitationProcessor`'s URL|DOI union-find at the next layer down — no duplication of that concern.

**Dispatch mechanism: in-process asyncio.gather, Fork-style cache sharing via `claude -p` subprocess (current transport).** The Lead constructs one stable `shared_prefix` (task brief + evidence + tool schemas, ≈12–18k tokens) and writes it with a 5-minute cache breakpoint on its first call. Each SubResearcher's `claude -p` invocation concatenates the shared prefix byte-identically before its own unique sub-brief — the cache-read at 0.1× base input applies. This mirrors Claude Code's `forkSubagent` pattern semantically without requiring the experimental SDK (GAP-14 stays deferred). Concurrency remains `research_concurrency=5` at the task level; within a task, up to 5 sub-agents run concurrently, so peak in-flight workers = 25, which `MCPGateway`'s rate limiter already handles.

**Rollup contract: claim collation, not averaging.** The Lead's synthesize step does three things: (a) compute citation union (all SRC/EV refs from all partials survive, SUB-NNN refs are stripped before emission because they are sub-query-scoped and the downstream pipeline doesn't need them); (b) collate claims — each claim retains its originating sub-query attribution as a `provenance` tag inside the `StructuredFinding.meta` field (new optional field, CitationProcessor ignores it); (c) flag contradictions explicitly — if two sub-agents disagree, both claims survive into the finding with `contradiction_group_id`, and L1.5 Deliberation's existing variance-detection fires naturally. **No averaging. No smoothing.** This is the exact failure mode (synthesis dilution) the design must avoid.

**Failure semantics.** `asyncio.gather(return_exceptions=True)` wraps the SubResearcher cohort. If ≥1 of N sub-agents returns a finding, the Lead synthesizes with what it has and flags `degraded_dispatch=True` in the finding meta. If 0 of N succeed, the Lead falls back to the *current* single-agent path (ResearchAgent with the task's full tool set) — this is the rollback safety net. `ProfileExecutionPolicy` sees the degradation flag and emits a `DEGRADE` governance event (invariant #4 preserved). `DEEP_RESEARCH=1` mode is untouched; deep-mode retains its current single-agent `claude -p` subprocess path and known GAP-08 tracking.

### Data flow diagram

```
ResearchTask (from L0)
      │
      ▼
┌───────────────────────────────────────────────────────┐
│ LeadResearcher                                        │
│  plan_subqueries → [SubQuery_1..N]  (N ∈ [3,5])       │
│  build_shared_prefix → renderedSystemPrompt bytes     │
└───────────────────────────────────────────────────────┘
      │  (Fork-dispatch, shared_prefix cached once)
      ▼
┌───────────┐  ┌───────────┐  ┌───────────┐  ...
│ Sub_1     │  │ Sub_2     │  │ Sub_3     │    (asyncio.gather)
│ lens=mkt  │  │ lens=fin  │  │ lens=prod │
│ consults  │  │ consults  │  │ consults  │
│ SourceLedger (sibling-visible, atomic claim)          │
│ MCPGateway.execute (auth + rate + breaker PRESERVED)  │
│ emits PartialFinding w/ SRC-NNN, EV-NNN, sub_id       │
└───────────┘  └───────────┘  └───────────┘
      │          │            │
      └──────────┴────────────┘
                 │
                 ▼
┌───────────────────────────────────────────────────────┐
│ LeadResearcher.synthesize (FLAGSHIP, 1 call)          │
│  citation union + claim collation + contradiction tag │
│  emits StructuredFinding (existing contract)          │
└───────────────────────────────────────────────────────┘
                 │
                 ▼  unchanged from here
      CitationProcessor → L1.5 → L2 → L4
```

## 4. Integration with existing stages — all ten invariants survive

**CitationProcessor:** zero changes. It receives the same `StructuredFinding` list as today. `SRC-NNN`/`EV-NNN` refs from sub-agents are first-class citations — URL|DOI union-find dedup still works; corroboration pairs still detected (and in fact *enriched*, because sub-agents within a task now generate natural URL overlap for genuine corroboration rather than the accidental overlap across tasks that's harder to interpret). Canonical `CAN-*` IDs unchanged.

**L1.5 Deliberation:** zero changes. Four-lens deliberation sees one `StructuredFinding` per task. If the Lead tagged internal contradictions via `contradiction_group_id`, the four analyst methodologies see richer input — which is strictly better for the ACH and ADVERSARIAL lenses. WWHTB threshold (mean confidence < 0.6) fires on exactly the same signal. Judge variance > 0.04 trigger unchanged.

**L2 ContentStructurer:** zero changes. Still one FLAGSHIP call per task generating `StructuredOutline + section_text` from one `StructuredFinding`.

**L4 Evaluator:** zero changes to the per-task fresh-Evaluator invariant. The Evaluator evaluates the *merged* `StructuredFinding`, not per-sub-agent partials. This is the correct level of granularity — the Evaluator's L1 fact-extraction, L2 citation gate, L3 10-dim rubric, L4 process trajectory, and L5 ensemble judges all operate on the canonical finding the downstream consumer would see. Sub-agent partials are ephemeral; they never leave the LeadResearcher's memory.

**Event stream additions (additive, non-breaking).** Three new events: `SubAgentDispatched(task_id, sub_id, lens, subquery_hash)`, `SubAgentCompleted(task_id, sub_id, status, n_sources, tokens_in, tokens_out)`, `PartialFindingMerged(task_id, n_sub, n_contradictions, n_unique_sources)`. Existing consumers ignore unknown event types; the new events feed observability without changing any contract.

**Invariant-by-invariant check:**

1. **Per-task fresh Evaluator**: preserved — Evaluator still sees one finding per task, constructed fresh.
2. **Structural citation enforcement**: preserved — sub-agents emit SRC/EV refs; Lead strips SUB-NNN during merge; claims without citation_refs still dropped at the Lead's synthesis step.
3. **Anti-confirmatory framing**: preserved — sub-queries inherit parent framing *plus* their own lens-specific framing; both pass the `tasks.py:165` validator at Lead's plan-time (add a unit test enforcing this).
4. **Named governance flags**: preserved — new `DEGRADE` event when `degraded_dispatch=True`; `HALT` when all N sub-agents fail and fallback also fails; `WARN` when contradiction_group count > threshold.
5. **DPVI**: preserved — sub-dispatch lives *inside* Parallelize (it is a second P), not a second Decompose. L0 still owns Decompose; the Lead's sub-query planning is *refinement*, not re-decomposition. This matters philosophically and prevents scope drift.
6. **Strict inter-agent isolation**: preserved — sub-agents do not communicate with each other directly; they share only a write-mediated URL ledger (append-only, atomic) and the read-only shared prefix. No shared intermediate findings. AgentLeak-style leak channels (C2 inter-agent messages, C5 shared memory) are structurally absent. Task-level isolation across tasks is unchanged.
7. **Tier separation**: preserved — SubResearchers are STANDARD; Lead is FLAGSHIP (planning + synthesis, no tool calls); Evaluator tiering unchanged.
8. **Haiku banned from judgment**: preserved — Haiku remains in its current narrow slots (L1 fallback, L4 extraction); the Lead's synthesis is FLAGSHIP.
9. **`asyncio.gather(return_exceptions=True)`**: preserved — used at both task level (already) and sub-agent cohort level (new).
10. **Tool authorization structural**: preserved — `MCPGateway` with `ToolAuthorizer`, `InMemoryRateLimiter`, `CircuitBreaker` mediates *every* sub-agent tool call. SYSTEM_OWNED tools remain blocked. GAP-08 deep-mode bypass untouched (separate track).

## 5. Phased implementation

**Phase 1 (Week 1): static dispatch for a single task type.** Ship `LeadResearcher` and `SubResearcher` classes with hardcoded N=3 sub-agents, no `SourceLedger` yet. Apply to tasks where `task.research_type == "competitive_landscape"` only (one type, ~3–5 tasks per engagement). Files to touch: new `keystone/l1/lead_researcher.py`, new `keystone/l1/sub_researcher.py`, modify `keystone/l1/agent_pool.py::execute_all` with a feature-gate branch on `PipelineConfig.l1_orchestrator_enabled` (default False). Test: parity suite — with the flag off, 1404 tests must still pass; with the flag on, 3 new integration tests (plan shape, citation round-trip, merge correctness). Rollback: flip `l1_orchestrator_enabled=False`.

**Phase 2 (Week 2): dynamic N from L0, full task-type coverage.** Extend L0's `task_generator` to emit `task.suggested_subagent_count` (integer 1–5) derived from task priority_score and three-lens decomposer leaf count. N=1 falls through to current single-agent path (no dispatch). N≥2 invokes LeadResearcher. Files: `keystone/l0/task_generator.py` (field addition, no contract break — consumers that don't know about the field ignore it), `keystone/l1/lead_researcher.py::plan_subqueries` respects the suggested count. Test: property test that `N_actual ∈ [max(2, N_suggested - 1), min(5, N_suggested + 1)]` (Lead is allowed to slightly adjust based on its decomposition). Rollback: L0 emits `suggested_subagent_count=1` globally → full fallback.

**Phase 3 (Week 3): `SourceLedger` coordination.** Ship `keystone/l1/source_ledger.py` with asyncio.Lock-guarded dict. SubResearcher consults ledger before every `WebFetch` tool call via `MCPGateway` middleware hook (new `ToolCallMiddleware` extension point, non-invasive — middleware returns either "proceed," "claim and proceed," or "redirect: peer already read, use their synopsis"). Files: `keystone/l1/source_ledger.py`, `keystone/tools/gateway.py` (middleware hook), `keystone/l1/sub_researcher.py` (middleware registration). Test: deterministic test with three sub-agents attempting the same URL; assert exactly one reads it, other two receive the synopsis redirect. Rollback: register a null middleware that always returns "proceed" — system degrades to Phase 2 behavior.

**Phase 4 (Week 4): runtime depth/breadth adaptation.** Add a "mid-task check-in" mechanism: after the first sub-agent returns, the Lead inspects (partial_finding.n_unique_sources, partial_finding.confidence_self_estimate) and can dispatch a *one-time* additional sub-agent if coverage is thin (n_unique_sources < threshold) or confidence low (self-estimate < 0.5). Hard cap at N=6 (elbow + 1 buffer). Files: `keystone/l1/lead_researcher.py` (add `dispatch_supplementary`). Test: mocked sub-agent returning thin partial → assert supplementary dispatched; mocked sub-agents all returning rich partials → assert no supplementary. Rollback: set `max_supplementary=0`.

Each phase is independently shippable. Phase 1 alone likely delivers 60% of the quality gain (per DeepMind elbow data); Phases 2–4 capture the remaining margin.

## 6. Risk analysis

**Coordination deadlock.** Lead waits forever on a hung `claude -p` subprocess. *Detection*: per-sub-agent timeout (inherit existing 1200s ceiling, tighten to 300s for shallow sub-agents). *Fallback*: timeout → treat as failed partial, synthesize with remaining N-1. This is already idiomatic in `asyncio.gather(return_exceptions=True)`.

**Cache-break cascade.** Sub-agent dispatch modifies shared prefix mid-task (e.g., evidence injection changes), invalidating cache for siblings 2..N. *Detection*: add a cache-hit-rate observability counter; alarm if hit rate drops below 70%. *Mitigation*: freeze `renderedSystemPrompt` at dispatch time — it is literally constructed once and passed by reference to all siblings. Any late evidence updates go into the sub-agent's *unique* brief suffix, which is after the last cache breakpoint.

**Redundancy explosion.** Five sub-agents all find the same 10 sources because they all searched the same high-rank queries. *Detection*: `cost_per_unique_source` metric (total tokens / ledger unique count). *Mitigation*: `SourceLedger` redirects (Phase 3) + methodologically-distinct sub-query planning (Phase 1) + **query-subspace partitioning in the plan** — Lead explicitly assigns each sub-agent a *non-overlapping source universe* (e.g., Sub_1 = analyst reports + industry publications, Sub_2 = SEC filings + investor call transcripts, Sub_3 = product docs + review sites). STORM's perspective-driven mechanism operationalized.

**Synthesis dilution.** Lead's final FLAGSHIP call averages out sharp signal from one sub-agent by over-weighting consensus. *Detection*: L4 process-trajectory check — flag tasks where all contradictions between partials are absent from the merged finding. *Mitigation*: the collation-not-averaging rollup contract is the structural defense. Contradictions get `contradiction_group_id` tagging, not resolution at merge time. L1.5's adversarial lens is the correct place to resolve them.

**Cost blowout past 15× multiplier.** Naive fan-out without cache sharing and without ledger. *Detection*: real-time cost-per-task counter in governance events; alarm if any task exceeds 8× baseline. *Mitigation*: Fork-style shared-prefix dispatch structurally caps per-worker marginal cost at ~35% of baseline worker (see §7). Hard ceiling: if a task's running token count exceeds a configurable `task_token_ceiling` (default 200k), Lead stops dispatching supplementary sub-agents.

**Sub-agent prompt injection via tool results.** A malicious search result instructs a sub-agent to exfiltrate via the `SourceLedger`. *Detection*: ledger entries are append-only and include the originating sub_id and URL; any write by sub_id mismatching the caller's identity is a structural violation. *Mitigation*: ledger exposes only URL hashes and short synopses (≤200 tokens, LLM-generated by the sub-agent reading the page); injection through a 200-token synopsis has sharply reduced blast radius. MCPGateway's `ToolAuthorizer` unchanged — injection can't elevate tool permissions. Anti-confirmatory framing re-applied in the Lead's synthesis prompt acts as a second-line defense.

**MAST step-repetition (FM-1.3, 17.1% base rate).** Lead re-dispatches the same sub-query after a failure. *Mitigation*: dispatch_history in the `SourceLedger` includes sub-query fingerprints; any supplementary dispatch must have cosine < 0.85 to every prior sub-query in the task. Hard cap on supplementary dispatches = 1 per task (Phase 4).

## 7. Cost modeling

The following table uses the third subagent's verified pricing (Sonnet 4.6 at $3/$15 per MTok, 1.25× cache write 5-min, 0.1× cache read) and Anthropic's published multipliers (4× parallel, 15× Agent Teams) as sanity bounds.

| Profile | L1 mode | Input tok / engagement | Output tok | Est. $ (Sonnet 4.6) | Ratio vs current LIGHT |
|---|---|---|---|---|---|
| LIGHT (current) | single-agent, 1 round | ~300k | ~200k | ~$3.90 | 1.00× |
| STANDARD (current) | single-agent, 3 rounds | ~500k | ~400k | ~$7.50 | 1.92× |
| STANDARD (proposed, Phase 1–2) | Lead + 3 Sub avg, Fork-cached | ~3.2M (of which 2.5M cache-reads) | ~1.0M | ~$18.60 | 4.77× |
| STANDARD (proposed, Phase 3–4) | Lead + 4 Sub avg, ledger-dedup | ~4.2M (of which 3.3M cache-reads) | ~1.2M | ~$22.80 | 5.85× |
| DEEP (current) | single-agent, subprocess | ~1.5M | ~600k | ~$13.50 | 3.46× |
| DEEP (proposed, Phase 4) | Lead + 5 Sub, ledger-dedup | ~6.0M (of which 4.8M cache-reads) | ~1.8M | ~$34.20 | 8.77× |

Cache hit-rate assumption: 78% of input tokens served as cache-reads at 0.1× (achievable because the 15k task brief + 30–40k evidence prefix is written once per task and read N times). Anthropic's 4× "parallelism vs chat" and 15× "Agent Teams vs chat" multipliers bracket the proposed STANDARD and DEEP proposals — both sit comfortably inside the Agent Teams ceiling. The STANDARD proposed multiplier of ~5.85× relative to current LIGHT is ~3× the current STANDARD baseline, consistent with the third subagent's Fork-dispatch worked example (3.32× baseline).

**Primary cost observability signal: `cost_per_unique_source`.** Defined as `total_engagement_tokens × price_per_token / ledger.distinct_sources_count`. Current system: ~$7.50 / ~800 sources = ~$0.009/source. Proposed STANDARD: ~$22.80 / ~2,400 sources (projected via 3× workstream parallelism × current per-agent coverage × 80% ledger efficiency) = ~$0.010/source — essentially flat *per unit of research output*. This is the correct framing: the system costs 3× more and delivers 3× more unique evidence. The McKinsey calibration (250 workstreams × 5k tokens synthesis + 50k cache prefix ≈ 1.3M synthesis tokens + 2.5M retrieval tokens ≈ $30 total per engagement at STANDARD tier) matches the proposed Phase 3–4 column within 25%.

**Break-even logic against baseline:** if an engagement yields even one additional billable finding, recommendation, or source citation that wouldn't have surfaced under single-agent synthesis — at Keystone's consulting rates — the incremental $15 per engagement is irrelevant. The real binding constraint is not dollar cost but latency (sub-agent fan-out is wall-clock parallel) and cache-breakpoint budget (4 per request caps how we partition the shared prefix).

## Conclusion

The architectural prescription is narrow and evidence-forced. Orchestrator-worker with methodologically-diverse sub-queries, N∈[3,5], centralized synthesis not debate, task-scoped source ledger, preserved per-task `StructuredFinding` contract. This converges with Anthropic's published multi-agent research system, with STORM's perspective-driven decomposition, with DeepMind's topology findings, with DMAD's methodological-diversity principle, and with the NeurIPS 2025 martingale result against peer debate. It diverges sharply from Cognition's "Don't Build Multi-Agents" — correctly, because Keystone's domain is research synthesis, not stateful code modification where that critique holds.

The most counter-intuitive finding the evidence forces: **don't go deeper, and don't let sub-agents talk to each other.** Recursive sub-sub-dispatch multiplies the 17.1% step-repetition failure rate; peer mailboxes multiply the 68.8% AgentLeak exposure. Shallow-and-wide with isolated workers and a strong orchestrator is the provably-better design given the constraints.

The DPVI pattern survives intact and actually becomes more accurate to its own name — the new layer is a second **P**arallelize step inside each task, which is exactly what the letter stood for in the original CAPSTONE-PLAN-v2 methodology. Decompose remains L0's job. Verify remains L1.5 + L4's job. Iterate remains the human-in-the-loop's job. The L1 redesign puts the missing depth into the Parallelize stage that was previously one agent wide — now it's one lead and up to five workers, cached and isolated.

Ship Phase 1 behind a feature flag next week. The parity suite is the safety net. The quality gain should appear in the first competitive-landscape task that runs under the new path.