# Pipeline Gap Audit — Nate Jones Corpus (Feb 1 – Apr 19 2026)

Purpose: named, prioritized list of gaps between Keystone's current implementation (`notes/PIPELINE-ATLAS.md`) and architectural directives surfaced across 78 Nate Jones Substack posts. Every gap cites the atlas section, names external evidence, lists affected files, and proposes action.

**Source materials**
- `notes/PIPELINE-ATLAS.md` — authoritative current-state reference (651 lines, fiber-optic visibility)
- 78 articles downloaded to `research/external-sources/nate-jones/2026-02-to-04/articles/`
- 9 thematic subagent analyses (Opus) preserved in this conversation's tool output (one per batch B1–B9)

**Methodology**: articles were bucketed into 9 themes (agent architecture, prompting, memory/compounding, model switching, tools/MCP, evaluation, safety, strategic, workforce/macro). Each batch subagent read 5–15 articles plus the atlas, produced per-article insights tagged by pipeline layer, then surfaced cross-article patterns. This document synthesizes across batches, deduplicates overlapping findings, and prioritizes.

---

## Top-line findings

1. **The Observation Library is the largest unrealized piece of Keystone's architecture and Nate's articles cite its pattern repeatedly.** Meta events (`ObservationRecorded`, `PatternPromoted`, `ConstraintEncoded`), Pass 3 of `ThreePassEvaluator`, cross-run institutional memory, and `client_id`-namespaced calibration all exist in the data model but emit no events and write nothing to disk. Every run starts from zero; rejection moments — the highest-value knowledge events in the pipeline — are discarded at gate boundaries.

2. **Silent failures are the dominant risk, not capability gaps.** `task.assigned_model` is reported in events but not routed. `ToolResult.tokens_used = 0` is hardcoded. `mece_passed=False` ships without halt. HITL `MODIFIED` raises instead of applying patches. Each of these produces confident-looking output where a key guarantee has quietly broken. Nate's 2026-04-19 "authoritative for six months, wrong at year two" framing names this failure mode precisely.

3. **Calibration debt compounds faster than feature debt.** Three evaluator thresholds — L3/L4 blend weight (0.8), L5 agreement floor (0.30), evaluator pass threshold (60.0) — were designed to be validated against human-scored samples and never have been. Until they are, the entire 5-layer evaluation stack rests on assumed parameters.

4. **Deep mode is a structural gateway bypass, not a mode extension.** `claude -p --allowedTools WebSearch,WebFetch` sidesteps `ToolAuthorizer`, rate limiter, circuit breaker, and the prompt-injection defenses the shallow path enforces. This is the highest-blast-radius code path in the pipeline.

5. **Keystone's strongest architectural choices have strong external validation.** Per-task fresh Evaluator (context-rot defense), tier-separated generation/evaluation (self-verification asymmetry), Haiku-banned-from-judgment, named governance actions (WARN/DEGRADE/HALT/ESCALATE), DPVI multi-agent pattern, L5 dissenter-veto-on-any-Tier-1-dissent, structural tool authorization — all converge with Nate's independently documented patterns. See "Validated design choices" below.

---

## Prioritized gap inventory

| ID | Gap | Layer(s) | Priority | Effort | Impact |
|---|---|---|---|---|---|
| GAP-01 | `task.assigned_model` reported but not routed | L1, Events | **P0** | S | High — per-task tier intent silently discarded |
| GAP-02 | Token accounting stubs (cost observability gap) | Gateway, L1, L4 | **P0** | M | High — cannot detect cost anomalies |
| GAP-03 | Evidence provider has no relevance filter | L1, Retrieval | **P0** | S | High — "memory rots" on growing corpus |
| GAP-04 | HITL `MODIFIED` discards modification payload | HITL | **P0** | M | High — accountability function non-functional |
| GAP-05 | Observation Library entirely unimplemented | Meta, L4 Pass 3 | **P0** | L | Very high — every engagement starts from zero |
| GAP-06 | `mece_passed=False` ships without halt | L0, Governance | **P0** | S | Medium — spec quality failure propagates silently |
| GAP-07 | L1 tool-call dead-letters not surfaced as governance flags | Gateway, L1 | **P0** | S | Medium — consistency with existing flag pattern |
| GAP-08 | Deep mode bypasses gateway mediation | L1, Gateway | **P1** | M | High — safety / blast-radius / injection exposure |
| GAP-09 | Evaluator calibration deferred (3 thresholds unvalidated) | L4 L3/L4/L5 | **P1** | M | Very high — every pass/fail decision is on assumed parameters |
| GAP-10 | Prompt model-version annotation + compensating-complexity audit | All prompt files | **P1** | M | Medium — prompt scaffolding degrades across model versions |
| GAP-11 | L1 synthesis prompt is inline Python, not versioned .md | L1 | **P1** | S | Medium — the load-bearing L1 prompt cannot be audited like L0/L4 |
| GAP-12 | Retrieval: `semantic_search` / `hybrid_search` identical; no causal path | Retrieval | **P1** | M | Medium — RAG fails on relational queries (Nate directly cites) |
| GAP-13 | Post-run write-back to institutional memory absent | Retrieval, Meta | **P1** | M | High — prerequisite for cross-engagement compounding |
| GAP-14 | Cross-model provider diversity (L5 slot + transport) | L4 L5, LLM_factory | **P2** | L | High — single-provider ToS/availability risk |
| GAP-15 | FastMCP real client (replace `MockMCPClient`) | Gateway | **P2** | L | Medium — gating future MCP ecosystem integration |
| GAP-16 | Prompt caching for stable per-round context | L1, L4 | **P2** | M | Medium — 10x cost discipline achievable per Nate |
| GAP-17 | Checkpoint/resume on pipeline crash | Cross-cutting | **P2** | L | Low-medium — 20 min deep runs restart from L0 today |

---

## P0 — Fix first

### GAP-01: `task.assigned_model` reported but not routed

**What's broken.** L0 `task_generator.py` populates `ResearchTask.assigned_model` per task and it flows into `AgentDispatched` events for observability. But `AgentPool` hands every agent a single shared `llm` callable resolved once from `_layer_llm("l1_research", STANDARD)`. A task whose generator assigned `FLAGSHIP` runs at STANDARD silently. The design intent (heterogeneous tier per task) exists in the data model and event stream but not in the routing logic.

**Atlas reference**: §4 ("Agent roster sources" — point 2), §11 stub table.

**External evidence**: B1 cross-pattern #4 ("per-layer model tier mixing vs a single global tier") names this as the highest-priority unresolved stub; 2026-03-25 "5 AI agents, 5 contradictory bets" specifically argues multi-model routing requires actual enforcement, not just declaration. B5 (2026-04-02 "66K tokens plugins") quantifies the 8–10x cost differential between model-aware and unaware workflows.

**Affected files**: `src/keystone/research/agent_pool.py` (accept `task` parameter in `_run_single`, resolve per-task LLM); `src/keystone/pipeline/orchestrator.py:682` (`_build_assignments` — pass task LLM selection through to the pool); `src/keystone/research/research_agent.py` (accept per-task LLM instead of shared pool LLM).

**Recommended action**. Wire `task.assigned_model` through `AgentPool.execute_all` into each `ResearchAgent` instantiation. Fallback to shared `llm` if `assigned_model=None`. Add a test that a task dispatched at FLAGSHIP reaches `ResearchAgent._llm` at FLAGSHIP tier.

---

### GAP-02: Token accounting stubs (cost observability gap)

**What's broken.** Three stubs compose a single cost-blindness problem. (a) `ToolResult.tokens_used = 0` is hardcoded in `mcp_gateway.py:404` with a comment "Phase 1: not tracked at gateway level." (b) Shallow-mode synthesis token count uses `len(prompt) // 4` char-heuristic in `research_agent.py:590`. (c) L4 process-trajectory LLM call's `tokens_consumed` is not captured in any aggregate (TODO.md). `PipelineResult.total_tokens` is assembled from unreliable inputs; no per-layer or per-task cost breakdown exists.

**Atlas reference**: §11 stubs ("L1 token accounting is approximate"; "L4 Layer 4 follow-up: capture `tokens_consumed`").

**External evidence**: B5 (2026-04-02) is the most direct — "Measure what you burn. If you don't know your per-call token cost, you're flying blind." Also Nate's 66K-tokens-of-plugins field observation and the 90% prompt-caching discount he demonstrates requires token measurement to benefit from. B4 (2026-04-14 Sora economics) frames inference cost per unit revenue as the binding enterprise constraint, not benchmark scores.

**Affected files**: `src/keystone/gateway/mcp_gateway.py` (populate `ToolResult.tokens_used` from provider response); `src/keystone/research/research_agent.py:590` (replace char heuristic with provider-reported token count or at least tokenizer-based count); `src/keystone/evaluator/layer4_trajectory.py` (capture trajectory LLM call's `tokens_consumed` into `Layer4Result`); `src/keystone/pipeline/orchestrator.py` (`PipelineResult` — add per-layer token breakdown: `{l0_tokens, l1_tokens, l1_5_tokens, l4_tokens}`).

**Recommended action**. Phase a: instrument the gateway to capture provider-reported tokens on all LLM calls (needs transport update). Phase b: add a governance flag `l4_cost_ceiling` that fires WARN when per-task evaluation cost exceeds a configured threshold. The threshold itself becomes a `PipelineConfig` field calibrated per intensity profile.

---

### GAP-03: Evidence provider has no relevance filter

**What's broken.** `EvidenceContextProvider.records_for_task(task)` returns up to 20 passages per task with no filter on `task.required_sources`, `task.issue_tree_branch_id`, or semantic relevance to task description. All tasks within an engagement see the same corpus dump, capped by count.

**Atlas reference**: §4 ("Evidence (Lane E) injection"), §11 stubs ("Task-aware evidence selection — replace default 'all records' with filter keyed off `ResearchTask.required_sources` / category / source_family").

**External evidence**: B1 cross-pattern #3 ("unstructured context accumulation degrades performance — 'memory rots'") — 2026-04-04 Cowork/Lindy analysis and 2026-04-03 "80% plumbing" both argue that accumulated-without-lifecycle context degrades agent performance below clean-start baseline. B2 (2026-02-05 "AI output feels generic") frames this as the RLHF median-output problem: without task-specific context, the model produces statistically average output. B3 (2026-03-26 "credentials vs artifacts") names "context architecture" as a hire-able skill defined specifically by "knowing what to include versus omit."

**Affected files**: `src/keystone/research/evidence_context.py` (`EvidenceContextProvider.records_for_task` — add filters); `src/keystone/models/tasks.py` (add optional `required_sources: list[str]` filter hint to `ResearchTask`); `src/keystone/specification/task_generator.py` (populate `required_sources` from issue-tree branch context during generation).

**Recommended action**. Add a deterministic filter first: exclude records whose domain/source-family is outside `task.required_sources` when that field is populated. Phase 2: semantic ranking against task description before the 20-passage cap. The cap itself is correct per B5 — don't remove it; just make the selection task-aware.

---

### GAP-04: HITL `MODIFIED` discards modification payload

**What's broken.** `GateStatus.MODIFIED` raises `GateModificationRequiredError` / `RuntimeError` and halts. The reviewer's modification JSON is delivered but not applied back to the issue tree (Gate 1) or confidence map (Gate 2). Gates present data but don't close the write-back loop.

**Atlas reference**: §3 governance hooks, §10.5 HITL, §11 stubs.

**External evidence**: B2 (2026-02-06 Claude constitution) — good prompt architecture reduces MODIFIED necessity but doesn't eliminate it. B3 (2026-03-10 "rejections compound") — "Expert rejection is the only part of an AI workflow that has compounding value… the constraint produced at the moment of rejection is more durable than the output that triggered it." Every `MODIFIED` response is exactly this compounding-value moment and Keystone discards it. B3 (2026-03-13 "two-door principle") — agent-readable AND human-readable on the same data is the design requirement; current gates are read-only from the human side. B9 (2026-03-21 "contextual stewardship") names gate modification application as the emerging human role.

**Affected files**: `src/keystone/hitl/gate.py:209` (apply patch instead of raising); `src/keystone/specification/spec_engine.py:282–284` (accept modified issue tree back into spec); `src/keystone/deliberation/deliberation.py:191–231` (accept modified ConfidenceMap).

**Recommended action**. Two-phase fix. Phase 1: persist the modification JSON to the retrieval store as a tagged constraint (`constraint_type="hitl_modification"`, namespaced by `client_id`) before halting — this captures the compounding value even before application logic exists. Phase 2: apply the modification to the live artifact (issue tree / confidence map) and resume the pipeline. Phase 1 is a day of work; Phase 2 is a sprint.

---

### GAP-05: Observation Library entirely unimplemented

**What's broken.** The data model, events, and contract all exist. The subsystem does not. (a) `ObservationLibraryContract` is defined in `contracts.py:336` but has no concrete implementation. (b) Events `ObservationRecorded`, `PatternPromoted`, `ConstraintEncoded` are declared in `events.py:432–457` and in `AnyPipelineEvent` but never emitted. (c) Pass 3 of `ThreePassEvaluator` is a placeholder at `three_pass.py:53`. (d) Every `Pipeline.run` builds fresh components; no cross-run persistence exists. (e) `client_id` threads through every event and `PipelineResult` but drives no per-client differentiation.

**Atlas reference**: §8 Layer 3 "three-pass is really two passes", §11 stubs (multiple entries).

**External evidence**: Overwhelming. B3 is almost entirely about this. 2026-03-02 "AI starts from zero" — core argument. 2026-03-10 "rejections compound" — the economic case for encoding. 2026-03-20 "three primitives" — Keystone has tools, lacks memory and proactivity. 2026-03-30 "SKILL.md accumulates where prompts evaporate" — concrete bootstrap pattern. 2026-04-17 "memory replaced the model as the moat" — competitive positioning argument. 2026-04-18 Karpathy Triplet (one editable surface, one metric, one time budget) — operational spec for how to implement. B2 (2026-02-05) "every mistake becomes a rule" — the CLAUDE.md discipline as a living specification. B6 (2026-03-18) factorial stress-test methodology and (2026-04-13) dark code comprehension gate both surface the need for a persistent-constraint library.

**Affected files**: new `src/keystone/observation/` package needed; `src/keystone/evaluator/three_pass.py:53` (wire Pass 3 when library exists); `src/keystone/events.py` (META events — already declared, just need emitters); `src/keystone/pipeline/orchestrator.py` (post-run hook to ingest evaluation outcomes as tagged chunks into `RetrievalService`).

**Recommended action**. Bootstrap the library from existing pipeline outputs rather than designing it from first principles (per 2026-03-30 "build from outputs, not intentions"): (1) add a post-run hook in `orchestrator.run_with_events` that ingests the run's `evaluation_results` into the retrieval store with metadata `{client_id, engagement_type, passed, dimension_scores, governance_flags}`; (2) implement a read path in `three_pass.py` Pass 3 that queries for prior runs matching the current task's engagement type and surfaces recurring failure patterns as Gestalt-equivalent overlays; (3) emit `ObservationRecorded` on ingest, `PatternPromoted` when a pattern reaches a threshold of N recurrences, `ConstraintEncoded` when a pattern is written back into a prompt file. This is a multi-sprint project but the first slice (post-run ingest with metadata) is a day of work and starts the data accumulating.

---

### GAP-06: `mece_passed=False` ships without halt

**What's broken.** After 3 decomposition attempts fail, the MECE validator marks `mece_passed=False` on the `ValidationReport` and the pipeline continues to dispatch agents against a tree known to be mutually-non-exclusive or non-exhaustive. A warning is logged but no governance flag fires.

**Atlas reference**: §3 MECE Validation step, §3 governance hooks ("halt scenarios").

**External evidence**: B6 (2026-04-13 "dark code") names this failure mode directly: "The spec is the comprehension artifact. If you can't write a clear spec, you don't understand what you're building." Shipping a failed spec is the comprehension-skipped anti-pattern. B8 (2026-04-05 "OpenClaw deployments spreading") — "automated dysfunction" is produced when agents execute on misspecified intent at machine speed.

**Affected files**: `src/keystone/specification/spec_engine.py:295` (MECE retry loop); `src/keystone/governance/policy.py` (new gate `l0_mece_failed` with configurable action).

**Recommended action**. Add a new governance gate `l0_mece_failed` that fires per pipeline profile: LIGHT=WARN (today's behavior), STANDARD=DEGRADE (mark results as degraded), DEEP=HALT (refuse to proceed with a failed spec — DEEP deliverables are the highest-blast-radius and deserve the strictest gate). The user can still override via profile selection.

---

### GAP-07: L1 tool-call dead-letters not surfaced as governance flags

**What's broken.** When all 3 retries of a tool call exhaust in `MCPGateway.execute`, a `DeadLetter` record is appended to `self._dead_letters` and the original exception is caught by `research_agent.py:547`'s broad `except Exception` — that tool is silently skipped for that round. The governance layer receives no named flag. Every other failure mode in Keystone has a named `QualityFlag(gate, action, severity)` (atlas §10.4); this one is swallowed.

**Atlas reference**: §4 (gateway pipeline step 6), §11 stubs.

**External evidence**: B1 cross-pattern #2 ("silent failures vs named failure modes") — Keystone's named-failure-mode architecture is ahead of the field, and this gap is an inconsistency with its own pattern. 2026-04-06 "Your AI Agent Depends on Six Layers" — "standard failure modes and recovery patterns" is the explicit missing infrastructure, and Keystone has the pattern for everything except tool-call dead-letters.

**Affected files**: `src/keystone/research/research_agent.py:547` (instead of bare `except Exception`, emit a `QualityFlag(gate="l1_tool_dead_letter", action=WARN, task_id=task.id)`); `src/keystone/governance/policy.py` (register the flag).

**Recommended action**. Small fix, high consistency value. Replace the swallowing `except Exception` with a flag-emitting handler. Under DEEP profile, consider promoting to DEGRADE (a task that lost a tool call may have reduced coverage).

---

## P1 — Structural

### GAP-08: Deep mode bypasses gateway mediation

**What's broken.** `_execute_deep` at `research_agent.py:265` shells out to `claude -p --allowedTools WebSearch,WebFetch`. This sidesteps `ToolAuthorizer`, `InMemoryRateLimiter`, `CircuitBreaker`, audit-log-per-call (session-level only), retry policy. Provider-native tools are invoked inside the Claude CLI subprocess and Keystone sees only the session's final output. Prompt injection on fetched content, irreversibility of any action taken, and rate-limit coordination are all outside Keystone's safety envelope.

**Atlas reference**: §4 "Tools NOT gated by MCPGateway", §11 stubs.

**External evidence**: B4 (2026-02-02 "Lobster/OpenClaw") documents the OpenClaw exposed-instance vulnerability pattern; B5 (2026-03-17 "Claude organized 900 Drive files") explicit prompt-injection warning when agent has authenticated web access; B7 (2026-02-22 "Trust Architecture") core thesis that structural safety > instruction safety; B7 (2026-03-16 Grigorev terraform-destroy incident) irreversibility as the un-flagged failure mode. All four point to the same gap: deep mode is exactly the modality most capable of high-blast autonomous action with the fewest structural controls.

**Affected files**: `src/keystone/research/research_agent.py:265` (deep path); `src/keystone/llm_client.py:475` (`deep_research_callable`); `src/keystone/gateway/mcp_gateway.py` (extension needed to wrap provider-native tools).

**Recommended action**. Phase 1 (near-term): add prompt-injection sanitization on `_evidence_block` before injection into deep prompt; cap deep-mode tasks per engagement via `PipelineConfig.deep_research_max_tasks`; emit a `l1_deep_mode_unmediated` WARN flag every time deep runs. Phase 2 (long-term, matches TODO.md): route deep-mode tool calls through `MCPGateway.call_tool` via gateway-owned WebSearch/WebFetch wrappers — this closes the gap fully but requires provider cooperation and is a multi-month effort.

---

### GAP-09: Evaluator calibration deferred (three thresholds unvalidated)

**What's broken.** Three parameters at the heart of L4 have never been calibrated against human-scored samples: (a) `evaluator_layer3_weight = 0.8` — the L3/L4 blend geometric-mean weight; (b) `l5_low_agreement_threshold = 0.30` — the agreement-level floor for the `l5_low_agreement` governance gate; (c) `evaluator_pass_threshold = 60.0` — the composite score above which evaluation passes. Every pass/fail decision in the pipeline rests on these three assumed values.

**Atlas reference**: §10.2 PipelineConfig table, §11 stubs (three entries).

**External evidence**: B6 is the densest citation. 2026-03-18 factorial stress-testing methodology for decision research; 2026-04-16 Amdahl's Law applied to evaluation (can't optimize what you don't measure); 2026-04-07 "7.6% vs 92.4%" — unvalidated rubric weights produce plausible scores without genuine quality signal. B9 (2026-03-21) "your best people should be writing evals" — the calibration activity itself is what encodes domain expertise; deferring it is deferring the moat.

**Affected files**: `src/keystone/models/config.py:242` (PipelineConfig — the three fields); validation infrastructure doesn't exist yet.

**Recommended action**. Build a minimal calibration harness before adding new evaluator features: (1) collect 20–50 prior engagement outputs Jack has personally scored; (2) run the current evaluator on them; (3) compute Spearman correlation between evaluator scores and Jack's scores; (4) sweep the three thresholds to find values that maximize agreement on a held-out subset. This is a few days of work and unblocks every subsequent calibration decision. The atlas note already frames this as a P1 stub — this audit elevates it because every other evaluator gap depends on it.

---

### GAP-10: Prompt model-version annotation + compensating-complexity audit

**What's broken.** No prompt file in Keystone carries the model version it was tuned against. Procedural instructions written for a specific model's quirks (MECE retry loop at 3 attempts, explicit per-round citation-formatting instructions in L1 synthesis, anti-hallucination prefixes in various prompts) are compensating complexity that becomes drag when the model improves. No periodic audit exists.

**Atlas reference**: §10.2, §11 stubs (implicit).

**External evidence**: B4 (2026-02-11 "January obsolete") — three-month model generation cycles make any scaffolding stale within a quarter; B4 (2026-04-01 "Every workaround you built for the last model is now breaking the next one") — the directive is named: "Every piece of 'how' you encode into your system is a bet against the model getting smarter." B2 (2026-02-27 "4 prompting disciplines") — Prompt Craft (scaffolding) is the lowest-altitude discipline and the one most vulnerable to model updates.

**Affected files**: every `.md` prompt in `src/keystone/specification/prompts/` and `src/keystone/evaluator/prompts/` (add frontmatter: `# Model: claude-opus-4-6 (tuned 2026-03-XX)`); inline Python prompts in `research/research_agent.py`, `deliberation/analyst.py`, `deliberation/aggregator.py`, `deliberation/wwhtb.py` (add analogous comment headers); new audit script `tests/canary/test_prompt_freshness.py` that fails if any prompt's tuned-for-model is >2 versions behind `AppConfig.flagship_model`.

**Recommended action**. Batch edit: add model-version frontmatter to every prompt file (~20 files, ~1 hour). Then on each model version bump (e.g., 4.6 → 4.7), run a regression canary that executes a fixed engagement spec and compares dimension scores and tool-utilization metrics against the prior version's baseline. Drops > 5% on any dimension trigger the "compensating complexity" audit for the relevant prompt.

---

### GAP-11: L1 synthesis prompt is inline Python, not versioned .md

**What's broken.** `_build_synthesis_prompt` at `research_agent.py:891` and `_build_deep_research_prompt` at `:774` construct L1 prompts as inline Python f-strings. Every other layer with LLM calls has its prompts in `.md` files (L0, L4 L1/L3/L4, sprint contract, gestalt overlay, process trajectory). L1 and L1.5 inline-construct their prompts, which means these load-bearing prompts can't be audited in a diff, can't be versioned independently, can't have model-version annotations added (GAP-10), and are harder for non-engineers to review.

**Atlas reference**: §4 "Prompts: no .md files. Both synthesis prompt and absence report prompt are inline Python strings. The `src/keystone/research/prompts/` directory does not exist." §6 "Prompts — inline only."

**External evidence**: B1 (2026-02-21 "Skills as versioned mountable instruction packages") — the SKILL.md pattern is exactly versioned-prompt-as-artifact. B2 (2026-03-27 DESIGN.md) "DESIGN.md is a lossless context format… agent-readable and human-readable." B5 (2026-02-10 "200 lines of markdown = $285B sell-off") — markdown prompt files carry the analytical leverage; keeping them inline defeats the pattern.

**Affected files**: create `src/keystone/research/prompts/synthesis.md` with `{{task_description}}`, `{{round_number}}`, `{{anti_confirmatory_framing}}`, `{{source_table}}`, `{{evidence_block}}`, `{{wiki_context}}` placeholders; same for `absence_report.md` and deep-mode `deep_research.md`; refactor `_build_synthesis_prompt`, `_build_deep_research_prompt`, and the absence-report prompt builder to load + substitute rather than f-string.

**Recommended action**. Mechanical refactor with full test coverage. ~1 day of work. Enables every subsequent prompt-engineering improvement to apply uniformly to L1 and L1.5.

---

### GAP-12: Retrieval semantic/hybrid conflation + causal query gap

**What's broken.** Two issues in one gap. (a) `semantic_search` and `hybrid_search` are registered as distinct tools but both delegate to the same `RetrievalService.search` code path (per `retrieval_bridge.py:17` comment). (b) The router is `RuleBasedQueryRouter` using regex signals; an LLM-backed router is on TODO.md. (c) Both paths use vector similarity + BM25, which cannot handle causal/relational queries across time per B2 (2026-03-05) — "find the chain of decisions that led to the current vulnerability" requires causal reasoning, not topical similarity.

**Atlas reference**: §10.6 retrieval wiring, §11 stubs.

**External evidence**: B2 (2026-03-05) is the explicit citation for the causal-query gap. B4 (2026-04-01) "agentic RAG" argues model-directed retrieval outperforms pipeline RAG — validates the broader stub of giving shallow agents system-path access to retrieval tools.

**Affected files**: `src/keystone/gateway/retrieval_bridge.py` (differentiate the two tool handlers — `semantic_search` = pure vector, `hybrid_search` = vector + BM25 + rerank); `src/keystone/retrieval/search/query_router.py` (replace `RuleBasedQueryRouter` with an LLM-backed classifier at STANDARD tier); new component for causal-chain retrieval deferred to later (requires graph construction over the corpus — out of scope for near-term).

**Recommended action**. Phase 1: split the two tool implementations — trivial fix, high consistency value. Phase 2: LLM-backed router. Phase 3: causal-query path is its own research project; defer until the first two ship and the accumulated corpus is large enough to justify graph construction.

---

### GAP-13: Post-run write-back to institutional memory absent

**What's broken.** `RetrievalService.ingest_institutional(records)` exists and is called once per engagement in `_wire_retrieval` before any research runs. Nothing writes back after the run. `PipelineResult.findings` (full, unfiltered), `evaluation_results`, `confidence_map` are returned to the caller and then discarded. The retrieval store grows with pre-run Lane E ingests; it does not grow with run outputs.

**Atlas reference**: §10.6 Retrieval wiring, §11 stubs.

**External evidence**: B3 is the densest citation. 2026-04-17 "memory replaced the model as the moat" — specific argument that accumulated context is the durable differentiator. 2026-03-13 "time-bridging" — 18-month old findings accessible as easily as today's. 2026-03-02 Open Brain pattern — Nate's personal implementation is a write-back loop. B3 cross-pattern #1 identifies this as "the single most-cited structural failure across all 8 articles" in the memory batch.

**Affected files**: `src/keystone/pipeline/orchestrator.py` (after `PipelineResult` is assembled but before `run_with_events` returns, ingest structured outputs); `src/keystone/retrieval/search/retrieval_service.py` (may need a new `ingest_run_outputs(pipeline_result, client_id, engagement_id)` method that converts findings/confidence/eval into chunk records).

**Recommended action**. Gated by GAP-05 (Observation Library). When that gap is addressed, this write-back is the first concrete slice. Chunk strategy: one chunk per passed `FindingClaim` tagged `{client_id, engagement_type, confidence_tier, passed=True}`; one chunk per `EvaluationResult` tagged `{client_id, engagement_type, dimension_scores_summary}`. Stored with `engagement_id=client_id` (not `None`) so client-specific retrieval namespacing works.

---

## P2 — Strategic / future-facing

### GAP-14: Cross-model provider diversity (L5 slot + transport)

**What's broken.** Two related exposures. (a) L5 ensemble's `standard_crossmodel` slot is an interim Sonnet placeholder explicitly flagged (`orchestrator.py:990–996`) as intended for GPT-5.4 / Gemini swap. (b) `_call_claude_cli` is a subprocess-only transport — no HTTP SDK path exists. If Anthropic blocks subscription OAuth from third-party tools (as they did for OpenClaw on 2026-01-09 per B4 2026-04-08), Keystone's LLM transport breaks without notice. The subprocess coupling runs deeper than the tier abstraction in `LayerAwareLLMFactory`.

**Atlas reference**: §8 L5 panel composition, §10.1 LayerAwareLLMFactory, §11 stubs.

**External evidence**: B4 (2026-04-08 "512K lines of leaked code") — Anthropic ToS-enforcement pattern; B4 (2026-04-14 Anthropic blacklisting) — government/regulatory risk; B9 (2026-03-03 "$700B cloud bet") — every hyperscaler is every model provider's competitor; B2 (2026-03-19) — multi-model orchestration as easily replicable moat; B4 (2026-03-04) — 94% vs 87% instruction compliance gap between Claude and GPT, with context-retention degradation past 60–70% window capacity on non-Claude models.

**Affected files**: `src/keystone/llm_client.py` (new HTTP SDK transport paths for OpenAI + Gemini in addition to the CLI); `src/keystone/pipeline/orchestrator.py:990–996` (the `_resolve_ensemble_judges` `standard_crossmodel` slot); `AppConfig` (new `openai_model`, `gemini_model` fields).

**Recommended action**. HTTP SDK path first (unblocks everything downstream and removes subprocess-lock-in). Then populate the L5 slot. Critical detail per B4: cap input length at 60% of any external provider's advertised context window (not 100%) — non-Claude models degrade past that threshold.

---

### GAP-15: FastMCP real client

**What's broken.** The MCP client in the gateway is `MockMCPClient`. Real MCP servers (`edgartools-mcp` and others) cannot actually launch. Gateway mediation works for in-process retrieval handlers but not for external MCP integration. Flagged in TODO.md.

**Atlas reference**: §11 stubs.

**External evidence**: B2 (2026-03-27) MCP as "USB-C for AI" and growing adoption; B4 (2026-03-31) Apple iOS 26.1 shipping system-level MCP support — the ecosystem is accelerating; B5 (2026-04-11) compression advantages accrue closest to metal, meaning middleware layers need to not inflate overhead.

**Affected files**: `src/keystone/gateway/mcp_gateway.py` (replace `MockMCPClient` with FastMCP-based client); gateway transport tests.

**Recommended action**. Low urgency until an external MCP server integration is actually required for an engagement. When that moment arrives, this becomes unblocking. Keep on backlog with acceptance criteria defined (must support stdio transport, must handle server lifecycle errors as circuit-breakable events).

---

### GAP-16: Prompt caching for stable per-round context

**What's broken.** Shallow-mode L1 resubmits the same system prompt, tool definitions, and accumulated citation table 3–5 times per task across rounds. L4 L3 rubric scoring makes 10 parallel LLM calls, each with nearly-identical prompt context (just dimension name varies). L5 ensemble multiplies this by 2–3 judges. Anthropic's prompt caching provides 90% cost discount on repeated content; Keystone uses it nowhere.

**Atlas reference**: §10.1 LayerAwareLLMFactory, §10.2 PipelineConfig.

**External evidence**: B5 (2026-04-02 "66K tokens of plugins") is the primary citation — explicit 90% discount claim. Same article for measurement (GAP-02) and caching are the same author's argument.

**Affected files**: `src/keystone/llm_client.py` (cache-control header support — requires SDK transport from GAP-14); call sites in `research_agent.py`, `layer3_rubric.py`, `layer5_ensemble.py`.

**Recommended action**. Blocked on GAP-14 (HTTP SDK transport needed for cache-control headers). Once SDK is in, the L4 rubric and L5 ensemble are the highest-value cache targets — 10–30x cost reduction on evaluation with no quality change.

---

### GAP-17: Checkpoint/resume on pipeline crash

**What's broken.** `Pipeline.run_with_events` builds fresh components at start and has no intermediate persistence. If the process crashes after L1 completes and before L1.5 starts (a 30-minute deep-research run at that point), the entire pipeline restarts from L0. No checkpoint, no resume.

**Atlas reference**: §2 spine; not in §11 but called out in B1.

**External evidence**: B1 (2026-04-03 "80% plumbing") — "resuming a conversation is not the same thing as resuming a workflow. Without workflow state, your agent can't survive a crash mid-tool-execution without potentially duplicating a write."

**Affected files**: `src/keystone/pipeline/orchestrator.py` (add per-stage persistence hook — SQLite via existing `aiosqlite` dep is probably sufficient); new `pipeline/checkpoints.py` for serialization of `EngagementSpec`, `StructuredFinding[]`, `CitationManifest`, `ConfidenceMap`, `StructuredOutline` to disk at each stage boundary.

**Recommended action**. Lower priority than the evaluator calibration and observation library work. Nice-to-have for long deep-research runs but single-engagement workflow can tolerate rerun cost for now. Revisit when deep-mode volume justifies the engineering.

---

## Cross-cutting patterns

**1. The write-back gap is pervasive.** GAP-04 (HITL modifications), GAP-05 (Observation Library), GAP-13 (post-run memory), all three implicit in GAP-09 (calibration requires accumulating scored data). Keystone has extraordinary machinery for producing outputs within a run and almost none for persisting what was learned. The retrieval stack is correctly architected — it's just being used one-directionally. A single design principle ("every rejection/correction/outcome gets ingested into the retrieval store tagged by `client_id`") closes four of these gaps with one pattern.

**2. Observability inconsistency within an otherwise consistent design.** Keystone has a named-governance-flag architecture that is ahead of most agent stacks. The gaps are places where that pattern was not applied: tool-call dead-letters (GAP-07), `mece_passed=False` (GAP-06), cost thresholds (GAP-02), model-tier routing mismatch (GAP-01). Each is a small fix; collectively they close the gap between design intent and implementation.

**3. L1 is under-instrumented relative to L0 and L4.** L0 has file-based prompts per step, explicit tier config, HITL gate, event emission at every step. L4 has file-based prompts per dimension, three sub-layers of deterministic/extraction/rubric, infrastructure-failure flags, ensemble panel, governance gates. L1's shallow path has inline prompts (GAP-11), hardcoded token accounting (GAP-02), silently-swallowed failures (GAP-07), and a shared-pool LLM that ignores per-task tier intent (GAP-01). L1 is the pipeline's execution engine and should be at L0/L4 parity on instrumentation.

**4. Deep mode is structurally different from shallow mode and the gap is under-appreciated.** Deep bypasses tool authorization, rate limiting, circuit breaking, per-call auditing, and structural isolation. It produces high-quality research via Claude's internal multi-turn loop. But it is also the highest-blast-radius code path in the pipeline with the fewest guardrails. GAP-08 addresses the structural bypass; several P0 gaps (observability, prompt injection) have deep-mode-specific dimensions worth considering separately.

**5. Calibration debt is not a future-work item.** GAP-09's three unvalidated thresholds sit under every evaluator decision. Nothing downstream (rubric tuning, dissenter-veto sensitivity, profile selection) is meaningful until these are calibrated. The good news: the calibration is a days-of-work task, not a quarters-of-work one — 20–50 scored prior outputs + a spreadsheet gets most of the value.

---

## Validated design choices (explicit non-gaps)

These are architectural decisions Nate's articles independently validate. Listed so future work doesn't re-litigate them.

1. **Per-task fresh `Evaluator` + per-task fresh `ResearchAgent`** — context-rot defense per B2 (2026-02-07).
2. **Tier separation: STANDARD for extraction/research, FLAGSHIP for judgment/evaluation** — self-verification asymmetry, Nate's "Opus for reasoning, Sonnet for execution" (B2, B4, B5, B9).
3. **Haiku banned from judgment paths** — multiple field observations (B5, B7, B9) corroborate; Haiku is correctly retained for L4 extraction and L1 fallback chain.
4. **Named governance actions (WARN/DEGRADE/HALT/ESCALATE)** — ahead of the field per B1 cross-pattern #2.
5. **`asyncio.gather(return_exceptions=True)` for analyst and judge isolation** — one failed analyst/judge can't abort the cohort (B6 cross-patterns).
6. **DPVI multi-agent decompose-parallelize-verify-iterate** — B8 (2026-03-11) "jagged frontier was measurement error" argues this is THE mechanism by which reliability improves beyond single-shot.
7. **L5 dissenter-veto on ANY Tier 1 dissent (not majority)** — structural hedge against scheming-aware judges per B7 (2026-03-09).
8. **Structural tool authorization via `ToolAuthorizer` + `SYSTEM_OWNED_TOOLS` blocklist** — B7 (2026-02-22) "Trust Architecture": instruction-based safety fails; structural enforcement does not.
9. **L4 as verification infrastructure** — B8 (2026-02-01, 2026-03-11, 2026-04-05, 2026-04-19) all argue trust/verification IS the product, not overhead.
10. **L0 as specification-quality investment** — B8, B9 (GDPVal vs Remote Labor Index: 70% vs 2.5%) — specification is the task-vs-job divider.
11. **Stateless-per-run `PipelineComponents`** — correct isolation invariant per B9 (2026-03-03) against stateful-runtime lock-in; the write-back gap (GAP-05/13) is the complementary pattern, not a contradiction.
12. **Intent clarifier FLAGSHIP/xhigh as L0 step 2** — B8 (2026-02-18 dark factory) — specification quality is the binding constraint on output quality; resource allocation is correctly placed.
13. **Anti-confirmatory framing validated structurally at `tasks.py:165`** — B7 (2026-03-09 "intent engineering") explicitly endorses structural prompt-prefix blocks.
14. **Sprint contract `dimension_emphasis` / `mandatory_elements` / `anti_patterns`** — B2 (2026-04-15 SOUL.md) exactly this pattern; the sprint contract is Keystone's SOUL.md per task.
15. **Citation gate HALT on any fabrication** — B6 (2026-04-13 dark code), B8 (2026-04-19 authoritative-for-six-months) — confident-fabricated outputs are the dominant risk, and halting is the right response.

---

## Recommended next steps (ROI-ranked)

1. **Evaluator calibration harness** (GAP-09) — unblocks every subsequent evaluator decision; days of work.
2. **`task.assigned_model` routing** (GAP-01) — small fix, removes silent tier-intent loss; hours of work.
3. **`mece_passed=False` governance gate** (GAP-06) — small fix, completes the halt-on-spec-failure pattern; hours of work.
4. **Tool-call dead-letter governance flag** (GAP-07) — small fix, restores consistency with the named-failure-mode pattern; hours of work.
5. **HITL `MODIFIED` persistence to retrieval store (Phase 1)** (GAP-04) — captures compounding-value moments before application logic exists; a day of work.
6. **Evidence provider task-aware filter** (GAP-03) — addresses the memory-rots pattern; a day of work.
7. **Post-run ingest hook** (GAP-13) — starts accumulating cross-run data; a day of work. Combined with #5 this is the first actual slice of GAP-05 (Observation Library).
8. **L1 prompt externalization to `.md` files** (GAP-11) — enables every subsequent prompt-engineering improvement to apply uniformly; a day of work.
9. **Model-version frontmatter on all prompts + canary test** (GAP-10) — protects against prompt-scaffolding decay; a day of work.
10. **Token accounting instrumentation (Phase 1 — populate `ToolResult.tokens_used`)** (GAP-02) — enables cost governance and caching; a day of work.

Ten items. Each is a day or less. Completing them brings Keystone from "architecturally complete with silent gaps" to "consistent pattern enforcement across the stack." Everything after is structural (deep-mode gateway, Observation Library full build, external provider diversity) and belongs in a different scope of work.

---

*Generated 2026-04-19 from 78-article Nate Jones Substack corpus analysis + `notes/PIPELINE-ATLAS.md`. Per-article raw insights available in the originating subagent analyses; this document is the synthesis.*

---

## Verification Status

*Verified 2026-04-21 against branch `codex/owner-triage-normalization` @ `bddc2b8`.*

| ID | Status | Summary |
|---|---|---|
| GAP-01 | CONFIRMED | `task.assigned_model` is never read inside `AgentPool._run_single` or `ResearchAgent`; all agents share the pool-level `llm` |
| GAP-02 | CONFIRMED | Three stubs confirmed: `tokens_used=0` in `mcp_gateway.py:404`, `// 4` heuristic in `research_agent.py:324,590`, L4 trajectory has no `tokens_consumed` capture |
| GAP-03 | CONFIRMED | `records_for_task` returns all records when no `task_filter` is provided; already tracked in TODO.md |
| GAP-04 | CONFIRMED | `GateStatus.MODIFIED` path sets `patch_applied=False` then raises `GateModificationRequiredError` at `gate.py:209`; modification JSON is never applied |
| GAP-05 | CONFIRMED | `ObservationLibraryContract` is Protocol-only (`contracts.py:337`), `Pass 3` is a no-op placeholder (`three_pass.py:53`), `src/keystone/observation/` does not exist, no code ever `yield`s `ObservationRecorded`/`PatternPromoted`/`ConstraintEncoded` |
| GAP-06 | CONFIRMED | After all MECE retries, `_decompose_with_validation` returns `(tree, False)` with a warning log; orchestrator does not inspect `spec.validation_report.scope_valid` or fire any governance flag |
| GAP-07 | CONFIRMED | `research_agent.py:547` has a bare `except Exception` that logs a warning and continues; no `QualityFlag` is raised; `dead_letters` property exists on `MCPGateway` but is never polled by agent or orchestrator |
| GAP-08 | CONFIRMED | `_execute_deep` docs explicitly state gateway mediation does not apply; `deep_llm(prompt)` call at `research_agent.py:316` bypasses `ToolAuthorizer`, rate limiter, and circuit breaker; already tracked in TODO.md |
| GAP-09 | CONFIRMED | All three values present as hardcoded defaults: `evaluator_pass_threshold=60.0` (`config.py:312`), `evaluator_layer3_weight=0.8` (`config.py:318`), `l5_low_agreement_threshold=0.30` (`config.py:343`); already tracked in TODO.md |
| GAP-10 | CONFIRMED | No prompt file in `src/keystone/specification/prompts/` or `src/keystone/evaluator/prompts/` contains model-version frontmatter or annotation |
| GAP-11 | CONFIRMED | `src/keystone/research/prompts/` does not exist; `_build_synthesis_prompt` (`research_agent.py:891`) and `_build_deep_research_prompt` (`research_agent.py:774`) are pure f-string inline builders |
| GAP-12 | CONFIRMED | Both `semantic_search` and `hybrid_search` handlers in `retrieval_bridge.py` call the same `_run_search` → `service.search` code path; already tracked in TODO.md |
| GAP-13 | CONFIRMED | After `PipelineResult` is assembled at `orchestrator.py:616`, there is no write-back to any retrieval store; `ingest` calls only appear in `_wire_retrieval` for pre-run Lane E records |
| GAP-14 | CONFIRMED | `standard_crossmodel` slot wires to `llm_factory(ModelTier.STANDARD)` at `orchestrator.py:1015` with explicit code comment "INTERIM slot"; already tracked in TODO.md |
| GAP-15 | CONFIRMED | `MockMCPClient` instantiated at `mcp_gateway.py:256` as the default client; class defined at line 82 with canned responses; already tracked in TODO.md |
| GAP-16 | CONFIRMED | No `cache_control`, `prompt_caching`, or related Anthropic caching fields appear anywhere in `llm_client.py`; already tracked in TODO.md |
| GAP-17 | CONFIRMED | No checkpoint, intermediate persistence, or resume mechanism exists in `orchestrator.py`; pipeline state is pure in-memory; crash at any stage requires full restart from L0 |

---

### GAP-01: CONFIRMED
`AgentPool._run_single` (`agent_pool.py:130-175`) constructs every `ResearchAgent` with the same pool-level `self._llm` and `self._current_tier`. The `task.assigned_model` field on `ResearchTask` is never read inside `_run_single` or anywhere in `ResearchAgent.execute`. The `current_tier` kwarg added in the audit-remediation pass is used only to set the fallback baseline for `ErrorRecovery`, not to select a different LLM callable per task. An operator who sets `task.assigned_model = ModelTier.FLAGSHIP` on high-priority tasks will find that all tasks still run at the pool-level tier.

### GAP-02: CONFIRMED
Three distinct stubs verified: (a) `mcp_gateway.py:404` hardcodes `tokens_used=0` with a `# Phase 1: not tracked at gateway level` comment; (b) `research_agent.py:590` accumulates `self._tokens_consumed += len(synthesis_prompt) // 4` (char-count / 4 heuristic) for shallow synthesis rounds, and line 324 does `(len(prompt) + len(raw_response)) // 4` for deep mode; (c) `layer4_trajectory.py` has no reference to `tokens_consumed` — the process-trajectory LLM call's token cost is silently uncounted. Already partially tracked in TODO.md ("L4 Layer 4: capture `tokens_consumed`...").

### GAP-03: CONFIRMED
`EvidenceContextProvider.records_for_task` (`evidence_context.py:223-242`): when `self._task_filter is None` (the default), it returns `list(self._records)` — all records up to the `max_passages_per_task` cap of 20. No category, source_family, or `required_sources` filtering is applied. The docstring explicitly notes this is "intentionally simple in this first iteration." Already tracked in TODO.md as "Task-aware evidence selection."

### GAP-04: CONFIRMED
`create_and_wait_for_gate` (`gate.py:175-210`): when `resolved.status == GateStatus.MODIFIED`, the `GateResolution` is built with `patch_applied=False` (line 178), a `ReviewGateModified` event is emitted, and then line 209-210 raises `GateModificationRequiredError` with the message "modifications are not yet supported in this phase." The reviewer's `decision.modifications` dict is present in memory but is never applied to the spec or deliberation output before the error is raised. The pipeline halts on modification rather than applying the patch.

### GAP-05: CONFIRMED
`ObservationLibraryContract` exists only as a `Protocol` in `contracts.py:337` — no implementation class exists anywhere in `src/keystone/`. The directory `src/keystone/observation/` does not exist. `ThreePassEvaluator.run` (`three_pass.py:49-55`) has a literal `# Pass 3: Observation Library scan (STUB for Phase 2)` comment and assigns `_observation_scan = None` before returning `dimensional_result` unchanged. The three events `ObservationRecorded`, `PatternPromoted`, and `ConstraintEncoded` are declared in `events.py:432-561` and included in `AnyPipelineEvent` but are never emitted by any code in `src/`.

### GAP-06: CONFIRMED
`spec_engine.py:307-332`: after `_MAX_DECOMPOSE_RETRIES + 1` attempts all fail MECE validation, the method logs a warning and returns `(tree, False)`. The caller at line 190 receives `mece_passed = False`, sets `ValidationReport(scope_valid=False)` on the spec, and the orchestrator proceeds directly to agent dispatch. Neither `spec_engine.py` nor `orchestrator.py` inspects `spec.validation_report.scope_valid` to fire a governance flag or halt. The `ProfileExecutionPolicy` has no method for L0 quality failures.

### GAP-07: CONFIRMED
`research_agent.py:547-554`: the `except Exception` block catches all tool-call failures, logs a `WARNING`, and silently continues to the next tool and round. The `MCPGateway.execute` path (`mcp_gateway.py:442-467`) appends a `DeadLetter` to `self._dead_letters` and re-raises `last_error`, but that re-raise is caught here. `MCPGateway.dead_letters` is a property that accumulates these records, but neither `AgentPool`, `ResearchAgent`, nor `orchestrator.py` ever reads it to emit a governance flag. No `l1_tool_dead_letter` gate or equivalent exists in `governance/policy.py`.

### GAP-08: CONFIRMED
`research_agent.py:265-293` and the docstring at lines 278-290 explicitly document that `_execute_deep` "bypasses MCPGateway for the tool calls themselves" — the `self._deep_llm(prompt)` call at line 316 is a direct LLM callable, not routed through `MCPGateway.execute`. `ToolAuthorizer`, `RateLimiter`, and `CircuitBreaker` are skipped. Audit logging is partially restored for per-source and session entries, but the structural safety controls do not apply. Already tracked in TODO.md as "Phase 2: route deep-mode tool calls through `MCPGateway.call_tool`."

### GAP-09: CONFIRMED
All three values confirmed as unvalidated defaults in `config.py`: `evaluator_pass_threshold: float = Field(default=60.0)` at line 311, `evaluator_layer3_weight: float = Field(default=0.8)` at line 317, `l5_low_agreement_threshold: float = Field(default=0.30)` at line 342. No calibration study, ground-truth dataset, or sensitivity analysis is referenced anywhere in the codebase. Already tracked in TODO.md ("calibrate the 10-point agreement-level threshold...against human-scored samples").

### GAP-10: CONFIRMED
Spot-checked `src/keystone/specification/prompts/classification.md` and `src/keystone/evaluator/prompts/intent_alignment.md` — both begin immediately with prose content, no YAML frontmatter, no `<!-- model: claude-opus-4 -->` comment, no model-version annotation of any kind. This applies uniformly to all 9 spec prompts and 15 evaluator prompts. There is no convention or tooling to detect prompt-model version drift.

### GAP-11: CONFIRMED
`src/keystone/research/prompts/` does not exist (directory lookup confirmed). Both prompt builders are inline f-string methods: `_build_deep_research_prompt` at `research_agent.py:774-864` (90 lines of inline f-string) and `_build_synthesis_prompt` at `research_agent.py:891-937`. These are the load-bearing L1 synthesis prompts but they cannot be audited, diffed, or versioned the way the L0 `.md` prompt files under `src/keystone/specification/prompts/` can.

### GAP-12: CONFIRMED
`retrieval_bridge.py:66-85`: `semantic_search` and `hybrid_search` are two thin closures that both call `_run_search(service=service, call=call, tool_name=..., event_sink=event_sink)`. The `_run_search` function calls `service.search(query)` identically for both. The module docstring at line 17-21 explicitly acknowledges "teasing the two paths apart at the service layer is a follow-up." Already tracked in TODO.md.

### GAP-13: CONFIRMED
After `_render_and_assemble` assembles `PipelineResult` at `orchestrator.py:616`, execution returns. No post-run write-back to the retrieval store occurs — there is no call to `service.ingest`, `service.ingest_institutional`, or any equivalent. The only ingest calls in the orchestrator are in `_wire_retrieval` (line 666), which runs at the start of Stage 1b to load pre-existing Lane E records into the per-run service. Engagement findings, citations, and evaluation results are returned to the caller and discarded.

### GAP-14: CONFIRMED
`orchestrator.py:1012-1015`: the `standard_crossmodel` slot explicitly calls `llm_factory(ModelTier.STANDARD)` — Sonnet — with an inline comment "INTERIM slot: swap to an external provider (GPT-5.4 / Gemini) when one is integrated." No HTTP transport, API key wiring, or second-provider SDK import exists anywhere in `src/keystone/`. Already tracked in TODO.md.

### GAP-15: CONFIRMED
`mcp_gateway.py:82` defines `class MockMCPClient` returning canned responses. `mcp_gateway.py:256` instantiates it as the default: `self._client: MCPClient = client or MockMCPClient()`. The `simple_client.py` file exists in the gateway package but does not implement a real FastMCP client. Already tracked in TODO.md.

### GAP-16: CONFIRMED
`llm_client.py` contains no references to `cache_control`, `prompt_caching`, or any Anthropic caching API. The `_client_cache` dict and `_cached_token` field are internal Python-object caches for reusing `AsyncOpenAI` client instances and auth tokens respectively — not Anthropic prompt caching. The `system` message and static per-round context blocks that would benefit most from caching are sent uncached on every call. Already tracked in TODO.md.

### GAP-17: CONFIRMED
`orchestrator.py` contains no checkpoint writes, intermediate persistence, or resume logic. `run_with_events` is a single async generator; all state (spec, findings, citations, confidence map, evaluation results) lives in local variables. If the process crashes after L1 completes but before L4 finishes (e.g., during a DEEP profile with 20+ minute research), the entire run must restart from L0. The HITL gate uses `aiosqlite` (via `HITLService`) for gate-review state, but that is gate-review state, not pipeline stage state.
