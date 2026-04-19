# Pipeline Atlas

Living reference for what the Keystone Intelligence Engine pipeline actually does, today. Every claim carries `file:line` so audit sessions can verify in seconds. When a claim goes stale, update it in-place — don't append "NOTE: 2026-05-XX" cruft.

Last verified against: branch `codex/owner-triage-normalization` @ `15e50c7`. 1404 unit+canary tests passing + 3 xfailed.

---

## 1. Data flow at a glance

```
user question ──► Pipeline.run_with_events
      │
      ▼
  L0 SpecEngine ──► EngagementSpec (issue tree + 15–50 tasks)
      │                                (HITL Gate 1 optional)
      ├─► Retrieval wiring (if retrieval_service_factory)
      │      └► ingest Lane E as institutional memory, register bridge handlers
      ▼
  L1 AgentPool ──► list[StructuredFinding]   (parallel per task)
      │                                      (shallow: gateway-mediated, 3–5 rounds;
      │                                       deep: single-turn claude -p with WebSearch/WebFetch)
      ▼
  CitationProcessor ──► CitationManifest     (dedup by URL|DOI union-find,
      │                                       URL liveness, corroboration pairs,
      │                                       canonicalized findings)
      ▼
  L1.5 Deliberation ──► ConfidenceMap        (4 parallel analyst methodologies;
      │                                       judge resolves variance > 0.04;
      │                                       WWHTB on confidence < 0.6;
      │                                       HITL Gate 2 optional)
      ▼
  L2 ContentStructurer ──► StructuredOutline + per-task section_text
      │                                      (pure Python + one LLM call per task
      │                                       for sprint-contract generation)
      ▼
  L4 Evaluator (per task, fresh instance) ──► EvaluationResult
      │       L1 fact extraction (STANDARD) → L2 citation gate (no LLM)
      │       → L3 rubric 10-dim (FLAGSHIP, or L5 wraps it)
      │       → L4 process trajectory (FLAGSHIP, blended 80/20 with L3)
      │       L5 ensemble: STANDARD=2×Opus, DEEP=2×Opus+1×Sonnet, median+dissenter-veto
      │                                      (governance flags; HALT/ESCALATE/DEGRADE/WARN)
      ▼
  Pipeline filters outline+manifest+confidence to passed_task_ids only
      ▼
  MarkdownRenderer ──► markdown string (and PipelineResult)
```

| Stage | Primary file | Default tier / effort | Prompts source | Yields |
|---|---|---|---|---|
| L0 spec engine | `specification/spec_engine.py` | per-step (see §5) | `specification/prompts/*.md` | `SpecificationGenerated`, `TasksDecomposed`, `AgentDispatched`×N |
| L0 HITL Gate 1 | `hitl/gate.py:76` | — | — | `ReviewGateCreated/Approved/Modified/Rejected` |
| L1 shallow | `research/research_agent.py:460` | STANDARD/medium | inline in Python | `ResearchStarted`, `SourceFound`, `CitationExtracted`, `FindingSynthesized`, `ResearchComplete` |
| L1 deep | `research/research_agent.py:265` | STANDARD (via `claude -p`) | inline | same 5 + `SourceFound` carrying `source_type="deep_research"` |
| CitProc | `citation/processor.py` | no LLM | — | `CitationDeduped`, `CorroborationScored`, `URLVerified`, `ManifestProduced` |
| L1.5 deliberation | `deliberation/deliberation.py` | STANDARD analyst / FLAGSHIP judge | inline `METHODOLOGY_PROMPTS` + inline judge/WWHTB | `AnalystSpawned`, `IndependentAnalysisComplete`, `AggregationComplete`, `ConfidenceMapProduced` |
| L1.5 HITL Gate 2 | `hitl/gate.py` | — | — | same gate events |
| L2 structuring | `structuring/content_structuring.py` | FLAGSHIP/high (sprint contract only) | `evaluator/prompts/sprint_contract_generation.md` | `SectionDrafted`, `SprintContractProposed`, `OutlineGenerated` |
| L4 L1 extraction | `evaluator/layer1_deterministic.py` | STANDARD/medium | `evaluator/prompts/fact_decomposition.md`, `numerical_consistency.md` | `DeterministicCheckPassed` |
| L4 L2 gate | `evaluator/layer2_citation_gate.py` | no LLM | — | `CitationGateResult` |
| L4 L3 rubric | `evaluator/three_pass.py` + `layer3_rubric.py` | FLAGSHIP/high | 10× `evaluator/prompts/<dim>.md` + `gestalt_overlay.md` | `RubricDimensionScored`×10 |
| L4 L4 trajectory | `evaluator/layer4_trajectory.py` | FLAGSHIP/high | `evaluator/prompts/process_trajectory.md` | `ProcessTrajectoryScored` |
| L4 L5 ensemble | `evaluator/layer5_ensemble.py` | FLAGSHIP + STANDARD | (same rubric prompts) | `EnsembleJudgeScored`×N, `DissenterVetoTriggered`, `EnsembleEvaluationComplete` |
| Render | `pipeline/markdown_renderer.py` | no LLM | — | (none today — L3 events are declared but unused; see §12) |

---

## 2. The spine: `Pipeline.run_with_events`

File: `src/keystone/pipeline/orchestrator.py`. Entry `run_with_events` at L337. Fresh `PipelineComponents` built per run (`_build_components`, L199), so no mutable state leaks between runs.

Stage sequence in the generator:

1. **L0 spec** (L359–376) — yields spec-engine events, retrieves the sealed `EngagementSpec`, constructs `ProfileExecutionPolicy` from `spec.research_spec.effective_pipeline_profile`, creates `GovernanceState` seeded with task list.
2. **Retrieval wiring** (L378–388, `_wire_retrieval` at L635) — if `retrieval_service_factory` is supplied, build a per-engagement `RetrievalService`, call `register_retrieval_handlers` to attach in-process `semantic_search` / `hybrid_search` handlers to the gateway, ingest Lane E records via `service.ingest_institutional(records)` (engagement_id=None so institutional chunks are visible to every engagement), yield a `ChunkIngested` summary.
3. **L1 research** (L390–428) — `_build_assignments` (L682) matches each task to an agent template, mints `AgentInstance(agent_id=f"agent_{task.id}_{hex6}", working_dir=f"/tmp/keystone/{eid}/{agent_id}")`. `AgentPool.execute_all` runs all assignments concurrently (see §6). Every `AgentResult.events` is folded into `events_by_agent` (for later Layer 4 process context), and `SearchCompleted` events collected by the retrieval bridge are folded into the relevant agent's trail. `policy.record_research_outcome` runs per task, `_raise_if_halted` halts the pipeline if governance went to HALT.
4. **CitationProcessor** (L430–440) — `process(findings, eid, client_id)` runs dedup → URL liveness → corroboration; retrieves `CitationProcessorResult.canonicalized_findings` (findings whose `claim.citation_ids` have been rewritten to canonical IDs — crucial, otherwise downstream stages reference source-instance IDs that have been merged away).
5. **L1.5 deliberation** (L442–452) — independent-parallel analysts → aggregator with judge-based dispute resolution → WWHTB → `ConfidenceMap` (see §7).
6. **L2 content structuring** (L454–499) — runs only over tasks whose `governance.task_outcomes[task.id].renderable` is True, capped at `self._max_eval_tasks` if set. Emits per-task `sprint_contract_fallback` WARN flags for any task whose contract negotiation failed (see §8).
7. **L4 evaluation** (L501–570) — per task, constructs a **fresh `Evaluator`** (L534) so per-task state never leaks, wires `extraction_llm` (STANDARD) separately from `llm` (FLAGSHIP), resolves ensemble panel via `_ensemble_panel_override` or the default `_resolve_ensemble_judges` (L972), builds `ProcessContext` from the agent's event trail, builds a task-scoped sub-manifest so Layer 2 gate only checks citations this task actually used. `policy.record_evaluation_outcome` runs per task; `policy.evaluate_coverage` and `_raise_if_halted` run after all tasks. See §9.
8. **Render filtering** (L572–604) — `passed_task_ids` built from governance (not evaluation results alone — unevaluated tasks also don't render). `_filter_confidence_map_by_passed_tasks`, `_filter_manifest_by_findings`, `filter_outline_by_passed_tasks` drop everything that didn't pass.
9. **Render** (L606–614) — `MarkdownRenderer.render(spec, passed_findings, filtered_confidence_map, render_evaluation_results, render_manifest, filtered_outline)`. Assigns `markdown_output` onto `PipelineResult`.

`PipelineResult` fields (L75): `engagement_id`, `client_id`, `spec`, `findings` (full, for record-keeping — not the filtered render set), `manifest`, `confidence_map`, `evaluation_results`, `markdown_output`, `total_tokens`, `total_events`. `findings` keeps everything; the render-side filtering is local to the `markdown_output` computation.

**Test injection seam.** `self._pending_components` (L175, L352) lets tests call `_build_components()`, mutate any field (e.g., swap in a mocked `Evaluator`), then assign to `_pending_components` before `run()`. This is the mechanism the 1404 unit tests use.

---

## 3. Layer 0 — Specification Engine

Input (`contracts.py:87`): `question: str`, `client_id: str`, `client_context: str | None`, `constraints: list[str] | None`. Nothing is preprocessed — the raw question hits the first LLM step.

Output: `EngagementSpec` (`models/research.py:205`) with `research_spec` (engagement metadata, day-1 hypothesis, questions, methodology, non-goals, effective eval + pipeline profile), `task_decomposition.tasks` (15–50 validated `ResearchTask`s), `validation_report`, and `issue_tree` (JSON dump of `IssueTree`).

### Seven steps, in order

| # | Step | File:line | Prompt | Tier / effort | Output model |
|---|---|---|---|---|---|
| 1 | Engagement classifier | `specification/engagement_classifier.py:36` | `prompts/classification.md` | STANDARD / medium | `ClassificationResult` (engagement_type, pipeline_profile, confidence, reasoning) |
| 2 | Intent clarifier | `specification/intent_clarifier.py:32` | `prompts/intent_clarification.md` | **FLAGSHIP / xhigh** | `IntentClarificationResult` (day_1_hypothesis, intent_clear, unstated_constraints, scope_boundaries, decision_context, surprising_finding) |
| 3a–c | Decomposer (3-lens) | `specification/decomposer.py:132,171` | `decompose_financial_lens.md` + `operational_lens.md` + `market_lens.md` (parallel) → `decompose_synthesis.md` | Lens STANDARD / medium · Synth **FLAGSHIP / xhigh** | `IssueTree` (root + metadata) — target 8–20 leaves, depth 2–3 |
| 4 | MECE validator | `specification/validator.py:40`, retry at `spec_engine.py:295` | `prompts/mece_validation.md` | **FLAGSHIP / xhigh** | `MECEValidationResult` (5 dimensions) |
| 5 | Priority scorer | `specification/priority_scorer.py:40` | `prompts/priority_scoring.md` | **FLAGSHIP / xhigh** | `list[PriorityScore]` (`priority_score = decision_relevance × uncertainty_reduction`) |
| 6 | ResearchSpec assembly (no LLM) | `spec_engine.py:334` | — | — | Frozen `ResearchSpec` |
| 7 | Task generator | `specification/task_generator.py:67` | `prompts/task_generation.md` | STANDARD / medium | `TaskDecomposition` (list[ResearchTask] with DAG validation) |

**Prompts live on disk** at `src/keystone/specification/prompts/`. Variables are `{{name}}`-templated and filled at call time.

**Intent clarifier excerpt** (the high-reasoning step that anchors the spec): the prompt is structured as 5 Decision-First CoT steps (decision context → surprising finding → unstated constraints → change-of-mind evidence → explicit out-of-scope) and requires: *"the Day-1 Hypothesis must be a declarative, falsifiable statement that the research will confirm, refute, or qualify."*

**MECE validator retry loop.** `_MAX_DECOMPOSE_RETRIES = 2` (`spec_engine.py:108`). On any failed dimension, full decomposition (steps 3+4) re-runs up to 3 total attempts. If all three fail, the last tree ships with `mece_passed=False` — the pipeline does NOT halt here. `validation_report.scope_valid` propagates the truth downstream.

**Task generator fallbacks** (`task_generator.py:200`): LLM-chosen tools → template-registry match (`template.tools[:5]`) → pad to 3 with `BASELINE_AGENT_TOOLS = [exa_search, brave_search, paper_search]`. Anti-confirmatory framing is validated at model level (`tasks.py:165` blocks prefixes `"find evidence for"`, `"prove that"`, `"confirm that"`, `"show that"`).

### L0 → L1 handoff (the bit you asked about)

There is NO direct call from `SpecificationEngine` to `ResearchAgent`. The orchestrator (`Pipeline`) owns the handoff.

```
Pipeline.run_with_events                          # orchestrator.py:337
  async for event in spec_engine.generate_spec(…)  # yields L0 events
  spec = await spec_engine.get_spec()              # spec_engine.py:289
  assignments = self._build_assignments(spec, template_registry)   # orchestrator.py:682
  agent_results = await c.agent_pool.execute_all(assignments)      # orchestrator.py:393
```

`_build_assignments` iterates every task; for each:
- `template_registry.match(task, etype)` returns `AgentDefinition` (system_prompt, tools list, model tier, `research_type` like `quantitative`/`contrarian`).
- Mints `agent_id = f"agent_{task.id}_{uuid.hex[:6]}"`.
- Instantiates `AgentInstance(definition=…, working_dir=f"/tmp/keystone/{eid}/{agent_id}", task_ids=[task.id])`.

`AgentPool.execute_all` (L93 of `agent_pool.py`) runs everything via `asyncio.gather` inside `_run_batch` (L122). A **new `ResearchAgent` is constructed per task** — the pool's shared `llm`/`gateway` are what get reused, not the agent instance.

**Three sources of agent capability:**
1. **Tool roster** (`task.assigned_tools`): set by L0 task generator, enforced 3–5, carried into the `ToolCall` at the gateway so only permitted tools can be called.
2. **Model tier field** (`task.assigned_model`): populated by the task generator and **reported in `AgentDispatched`** for observability, but **not actually used** — the pool hands every agent the same `llm` callable (resolved via `_layer_llm("l1_research", STANDARD)`). Per-task tier switching is a known stub (see §11).
3. **System prompt + research type** (from `match.template`): the `AgentDefinition.system_prompt` is injected into the agent's synthesis prompt; `research_type` determines the `agent_type` on `StructuredFinding`.

### L0 governance hooks

- **HITL Gate 1 (post-specification)** — `spec_engine.py:282–284`, `hitl/gate.py:76`. Skipped when `PipelineProfile == LIGHT` (`policy.should_run_hitl_gate()`) or when `db_session_factory` is None. `GateStatus.MODIFIED` **raises `GateModificationRequiredError` and halts** — modifications are not applied back into the tree (known stub).
- **Hard halt paths** at L0: any LLMCallable exhausts 3 retries → `RuntimeError`; task generation fails DAG validation after 3 attempts → `RuntimeError("Task generation failed after 3 attempts")`; gate rejected/timed out → `GateRejectedError` / `GateTimeoutError`.

---

## 4. Layer 1 — Research Agents

Two execution modes. Dispatch decision at `research/research_agent.py:202`:

```python
if self._deep_llm is not None:
    async for event in self._execute_deep(task, spec, agent): yield event
    return
async for event in self._execute_shallow(task, spec, agent): yield event
```

`deep_llm` is `None` unless `os.environ["DEEP_RESEARCH"] == "1"` at orchestrator construction time (`orchestrator.py:209`).

### Shallow mode (default)

**Entry:** `_execute_shallow` at `research_agent.py:460`.

- **Tier / effort:** STANDARD + medium (`AppConfig.standard_model` = `claude-sonnet-4-6`). Resolved via `_layer_llm("l1_research", STANDARD)` in `_build_components`.
- **Loop:** 3 rounds default, 5 hard cap (`DEFAULT_ROUNDS=3`, `MAX_ROUNDS=5`, both configurable via `PipelineConfig.research_default_rounds` / `research_max_rounds`). Each round: call all `task.assigned_tools` in parallel via `MCPGateway.execute` → synthesize via single LLM call → parse claims with `citation_refs`.
- **Evidence (Lane E) injection:** `_prepare_evidence_context` at L240 calls `EvidenceContextProvider.records_for_task(task)` (up to 20 passages default). Renders EV-NNN → `EvidencePrepRecord` lookup table as a prompt block: `"EV-001 | [article | parse=high] Title | url | p.5, para 2 | "excerpt…""`. Injected into every round's synthesis prompt alongside the SRC-NNN tool-results table.
- **Citations:** the synthesis prompt requires every claim to have a `citation_refs: ["SRC-001", "EV-002"]` array. Claims without `citation_refs` are dropped (logged DEBUG, `research_agent.py:973`). SRC-NNN resolves to the round's round-citation table; EV-NNN resolves through `self._evidence_table` via `evidence_to_citation()`.
- **Prompts: no .md files.** Both synthesis prompt (`_build_synthesis_prompt` L891) and absence report prompt (L1014) are inline Python strings. The `src/keystone/research/prompts/` directory does not exist.

Synthesis prompt ends with:
> `"Synthesize findings as JSON array of claims. Each claim MUST include citation_refs listing SRC-NNN tool-search refs and EV-NNN parsed-passage refs that support it. [...] Claims without citation_refs will be dropped."`

### Deep mode

**Entry:** `_execute_deep` at `research_agent.py:265`.

- **Tier / model:** Sonnet (STANDARD). The deep callable is `LayerAwareLLMFactory.deep_research_callable()` (`llm_client.py:475`), which shells out to `claude -p` with `--model=claude-sonnet-4-6 --effort=medium --allowedTools "WebSearch,WebFetch"`.
- **Single turn.** One `await self._deep_llm(prompt)` call. The Claude CLI runs an internal multi-turn web-research agent loop; we don't see the intermediate turns. Timeout `PipelineConfig.deep_research_timeout_s = 1200s` (20 min). Concurrency capped at `research_concurrency = 5`.
- **Tools NOT gated by MCPGateway.** WebSearch and WebFetch are provider-native. The gateway sees only `deep_research:session` audit entries (session-level), not per-fetch. Known limitation; routed through the audit log for observability but not through `ToolAuthorizer` / `InMemoryRateLimiter` / circuit breaker.
- **Prompt structure** (`_build_deep_research_prompt` L774): single flat string — no separate system message. Sections: ENGAGEMENT CONTEXT, RESEARCH QUESTIONS, YOUR SPECIFIC TASK, ACCEPTANCE CRITERIA, ANTI-CONFIRMATORY FRAMING, EXPECTED OUTPUT, optionally PARSED EVIDENCE ALREADY FETCHED (the `_evidence_block`), RESEARCH INSTRUCTIONS (7 bullets), literal JSON schema block, REQUIREMENTS (min 20 claims, every claim needs real URL, confidence rubric, ≥3 absence items). Ends with `"OUTPUT THE JSON AND NOTHING ELSE."`
- **Citations:** the deep prompt requires `claim.sources = [{url, title, content_snippet}]`. `Citation` objects are constructed directly via `_make_source_instance_id`; no SRC-NNN / EV-NNN indirection.

### Tool call mediation (shallow only)

Every tool call goes through `MCPGateway.execute(ToolCall(...))` (`mcp_gateway.py:314`). Pipeline per call:

1. `ToolAuthorizer.check(agent_id, assigned_tools, tool_name)` — raises `AuthorizationError` if `tool_name ∈ SYSTEM_OWNED_TOOLS` OR `tool_name ∉ assigned_tools`. Auth failure is immediately audit-logged.
2. `InMemoryRateLimiter.try_acquire(server_name)` — raises `RateLimitExceeded`, no gateway-level retry.
3. `CircuitBreaker.call(...)` per `server_name` — 3-failure threshold, 30s recovery (`circuit_breaker.py:56`). On `CircuitOpenError`, no retry.
4. Other exceptions: retry up to `MAX_RETRIES=3` with exponential backoff starting `BACKOFF_BASE=0.5s`.
5. `extract_citations(raw_result)` scans for structured `{url, title, text}` fields then falls back to URL regex.
6. Dead-letter on exhausted retries; original exception propagates and is swallowed by the agent's `except Exception` at `research_agent.py:547` (that tool is effectively skipped for that round).

### Error recovery (shallow synthesis calls)

`ErrorRecovery.execute_with_recovery` wraps all shallow LLM synthesis calls (`research_agent.py:571`) and the absence-report call (L1022). Deep mode does NOT use ErrorRecovery (the subprocess has its own timeout).

**Fallback chain** (`research/error_recovery.py:33`):
```python
FALLBACK_CHAIN = [ModelTier.FLAGSHIP, ModelTier.STANDARD]
```
**FAST (Haiku) is deliberately excluded** — see the comment at L37. Research never degrades to Haiku because extraction-model depth is insufficient for synthesis. Error classification: TRANSIENT → exponential backoff; MODEL_ERROR → skip remaining retries at current tier, fall to next; PERMANENT → re-raise immediately.

### Events (L1)

`ResearchStarted` → `SourceFound`×N (per round per tool hit) → `CitationExtracted`×N → `FindingSynthesized` (end of each round) → `ResearchComplete`. See `events.py:78–122`.

`SearchCompleted` (layer `"Retrieval"`) is NOT emitted by the agent — it's fired by the retrieval-bridge handler on each `semantic_search`/`hybrid_search` invocation, and folded into the agent's trail by the orchestrator at `orchestrator.py:409–411` so Layer 4 can see it.

---

## 5. CitationProcessor

File: `src/keystone/citation/processor.py`. Pure deterministic. **No LLM calls anywhere.**

### Dedup (`citation/dedup.py`)

Union-find on **URL equality OR DOI equality**. Transitive: if A shares URL with B and B shares DOI with C, all three merge. No text-similarity or LLM dedup.

Canonical ID minting (`dedup.py:68`): `CAN-{engagement_id}-{first8_hex_of_sha256_of_sorted_urls}`. Distinct prefix from source-instance IDs (`CIT-`), validated at `citations.py:107`.

Alias map: every source-instance citation ID (including the winner) gets a `CitationAlias → canonical_id`. `CitationProcessor._rewrite_findings_to_canonical` (`processor.py:225`) rewrites every `FindingClaim.citation_ids` across all findings using this map. This is why the orchestrator must use `cit_result.canonicalized_findings` for everything downstream (see orchestrator.py:439).

### Corroboration (`dedup.py:249`)

Builds `url_agents: {url → [(agent_id, citation_id)]}`. For any URL cited by 2+ different agents, emits `CorroborationPair` with `overlap_score = 1.0` (binary — same URL counts as corroborated). No partial overlap, TF-IDF, or semantic check.

### URL liveness (`citation/url_check.py`)

`batch_check_urls` with `asyncio.Semaphore(10)`. HEAD first (`follow_redirects=False`, 10s timeout). If HEAD returns 4xx/5xx → fall back to GET. Any `httpx.HTTPError` on HEAD short-circuits to `False` without attempting GET. UA: `"Keystone-Intelligence-Engine/1.0 (..; citation-verification)"`.

### `CitationManifest` fields (`citations.py:208`)

- `citations`: deduped canonical citations with `metadata_hash` (`SHA-256(url:title)`) and `url_live`
- `corroboration_pairs`: canonical-form only, self-pairs removed
- `dead_urls`: citation IDs where `url_live=False`
- `fabrication_flags`: always empty (stub; L4 citation gate populates downstream)
- `aliases`: full source→canonical map

---

## 6. Layer 1.5 — Deliberation

File: `src/keystone/deliberation/deliberation.py`. Two-phase. Drives 4 analysts in parallel then aggregates.

### Phase 1: independent parallel analysts

**Default roster** (`deliberation.py:39`):
```python
DEFAULT_ANALYST_TYPES = [ACH, QUANTITATIVE, ADVERSARIAL, HISTORICAL_ANALOGY]
```
Five types exist (`models/agents.py:44`); SCENARIO_PLANNING is optional. Practical range 1–5. Caller-configurable.

**Tier:** `STANDARD` by default (`deliberation.py:81`). The constructor's `analyst_tier` parameter is stamped onto `AnalystSpawned.model_tier` for observability; actual tier is whatever LLM is passed. `_build_components` wires `_layer_llm("l1_5_analysts", STANDARD)` by default.

**Prompts — inline only.** Methodology-specific preambles at `analyst.py:61–87` (`METHODOLOGY_PROMPTS`). No `.md` files in `deliberation/prompts/` (that directory doesn't exist). Examples:

- **ACH**: *"You are an intelligence analyst using Analysis of Competing Hypotheses (ACH) per ICD 203. For each claim, identify competing hypotheses and rate evidence diagnosticity."*
- **ADVERSARIAL**: *"You are an adversarial analyst tasked with finding weaknesses. For each claim, identify the strongest counter-argument and test for confirmation bias."*
- **HISTORICAL_ANALOGY**: *"…identify relevant historical precedents. Assess base rates and reference class forecasting."*

Output format appended by `_build_prompt` (L175): `"Respond with a JSON array: [{"index": 0, "confidence": 0.85, "source_count": 3, "reasoning": "..."}]"`.

**Isolation guarantee:** `asyncio.gather(..., return_exceptions=True)` at `deliberation.py:116`. One analyst crashing cannot abort others. No inter-analyst communication channel exists.

### Phase 2: aggregator

File: `src/keystone/deliberation/aggregator.py`.

**Variance + dispute flag.** For each claim, collect per-analyst confidences, compute `statistics.variance(confidences)`. Trigger dispute at `variance > DISPUTE_VARIANCE_THRESHOLD = 0.04` (`aggregator.py:30`; tunable via `PipelineConfig.dispute_variance_threshold`). 0.04 ≈ stddev 0.2 (a 20-point analyst spread).

**Judge prompt — also inline** (aggregator.py:237):
> *"Multiple analysts evaluated this claim with different conclusions. … Select the analyst whose assessment is best supported by the evidence. Do NOT blend or average. Pick one. Respond with JSON: {"selected_analyst": "<type>", "reasoning": "…"}"*

Fallback on parse failure: `max(scores, key=scores.get)`.

**Consistency check.** For all claims with `mean_confidence >= 0.6` (top 10), one judge call looks for direct contradictions across selected claims. Failures set `consistency_passed=False`, which feeds gap detection.

**Judge tier:** whatever `Deliberation` was given for `judge_llm`. `_build_components` wires `_layer_llm("l1_5_aggregator", FLAGSHIP)`.

### WWHTB — "What Would Have To Be True"

File: `src/keystone/deliberation/wwhtb.py`. Per-claim sequential pass. Fires **only when `mean_confidence < 0.6`** (`CONFIDENCE_THRESHOLD`, tunable via `PipelineConfig.wwhtb_confidence_threshold`).

Prompt (inline): *"For the following uncertain claim, identify the key assumptions that would have to be true for it to hold. List 2–5 specific, testable assumptions."*

Output: list of assumptions on `WWHTBResult`. Consumed by the confidence builder to populate `ModerateConfidenceClaim.sensitivity` and `WeakConfidenceClaim.recommendation`.

### ConfidenceMap tiering

File: `confidence_builder.py:48`. Rule set:

| `agreement_ratio` (`len(agreeing) / len(scores)`, where agreeing = confidence ≥ 0.5) | Tier | Class |
|---|---|---|
| `total_analysts == 0` | Insufficient | `InsufficientEvidenceClaim` |
| `> 0.8` | High | `HighConfidenceClaim` |
| `> 0.6` and ≤ 0.8 | Moderate | `ModerateConfidenceClaim` |
| `>= 0.5` and ≤ 0.6 | Weak | `WeakConfidenceClaim` |
| `< 0.5` | Contested | `ContestedClaim` |

**`ConfidenceMap.provenance_index`** (`confidence_builder.py:67`): `{aggregated_claim_id → [task_ids]}`. This is the primary L1.5 → L2 → L4 traceability index. Used by `_filter_confidence_map_by_passed_tasks` and by L2's `_claim_task_ids`.

**DiscoUQ** (`confidence.py:18`): `DiscoUQFeatures(evidence_overlap, minority_argument_strength, divergence_depth)` is defined but **not populated** by the current builder. Deferred.

### L1.5 HITL Gate 2

`deliberation.py:191–231`. Same skip logic as Gate 1. `GateStatus.MODIFIED` without `patch_applied` raises `RuntimeError` — modifications are not applied back into the `ConfidenceMap`.

---

## 7. Layer 2 — Content Structuring

File: `src/keystone/structuring/content_structuring.py`. **Pure Python plus one LLM call per task** (sprint contract), per the module docstring. Confirmed.

### Framework selection

File: `structuring/framework_selector.py`. Deterministic table at `_FRAMEWORK_MAP`:

| EngagementType | Primary (mandatory) | Secondary (optional) |
|---|---|---|
| SIZING | ESTIMATION | — |
| DIAGNOSTIC | ROOT_CAUSE | — |
| EVALUATIVE | PORTERS_FIVE_FORCES | VALUE_CHAIN |
| EXPLORATORY | LANDSCAPE_MAPPING | — |
| STRATEGIC | SCENARIO_PLANNING | SWOT |

Override path: `ContentStructurer(frameworks_override=[FrameworkHint, …])`. When non-None, **replaces the entire default** — no augmentation. That's the "novel engagement" escape hatch.

### Outline construction (`_build_outline`, L234)

Nine section types in order (sections that produce no items are omitted):

1. `EXECUTIVE_SUMMARY` — from `ConfidenceMap.high_confidence_above_80pct` only.
2. `FRAMEWORK_ANALYSIS` — one `FRAMEWORK_NOTE` item per selected framework.
3. `BRANCH` (one per issue-tree leaf) — `StructuredFinding.claims` grouped by `task.issue_tree_branch_id`, stamped with the primary framework.
4. `MODERATE` — from `ConfidenceMap.moderate_confidence_60_80pct`.
5. `WEAK` — from `weak_confidence_50_60pct`.
6. `CONTESTED` — from `contested_below_50pct`.
7. `GAPS` — from `ConfidenceMap.gaps_identified`.
8. `INSUFFICIENT` — from `insufficient_evidence`.
9. `ABSENCE` — from `StructuredFinding.absence_report` fields.

`uncovered_branch_ids` = `(known_branches ∪ branch_titles_from_issue_tree) − covered_branches` — tracks what the outline didn't cover.

### Section text renderer

File: `structuring/section_text.py`. Pure deterministic Markdown. Structure per section:

1. Title header (`task.deliverable_destination`)
2. Metadata block (framework, task ID, category, decision-usefulness target)
3. **Lede** (strongest claim by (confidence, citation count); framing varies by tier: `>=0.8` plain assertion, `>=0.6` "with moderate confidence", else explicit hedge.)
4. Evidence chain (numbered list, claim text + tier label + confidence % + evidence + citation refs + caveats)
5. Analytical significance (text-matches claim text against all ConfidenceMap tiers to pull `robustness`/`dissent`/`key_issue`/`key_disagreement`/etc.)
6. Research gaps + absence report
7. Acceptance criteria

### SprintContractGenerator — the one L2 LLM call

File: `src/keystone/evaluator/sprint_contract.py`. Prompt: `src/keystone/evaluator/prompts/sprint_contract_generation.md` (file-based). Variables filled: `task_id`, `task_category`, `task_description`, `end_product`, `task_acceptance_criteria`, `anti_confirmatory_framing`, `engagement_type`, `decision_context`, `quality_bar`.

**Tier / effort:** FLAGSHIP / high — wired via `_layer_llm("sprint_contract", FLAGSHIP, "high")` in `_build_components` (L229).

**Output:** `SprintContract` (`models/evaluation.py:401`) with `acceptance_criteria`, `dimension_emphasis` (per-rubric-dimension weight multiplier 0.7–1.5), `mandatory_elements`, `anti_patterns`.

**Fallback** (`content_structuring.py:188`): on any exception from the generator, log WARN, record `task.id` in `self._fallback_task_ids`, return a bare contract built from `task.acceptance_criteria` only (empty emphasis/mandatory/anti-patterns). The orchestrator drains `get_fallback_task_ids()` and emits per-task `sprint_contract_fallback` WARN flags (`orchestrator.py:478–499`). **Silent fallback was the audit finding that forced this** — the flag makes it observable.

---

## 8. Layer 4 — Evaluator (the five sub-layers)

File: `src/keystone/evaluator/evaluator.py`. Entry `evaluate(output_text, contract, task, manifest, spec, process_context=None)` at L155. Fresh `Evaluator` **per task** (orchestrator L534).

Sub-layer naming is confusing: the whole component is called "Layer 4" in the pipeline. Internally it has sub-layers L1–L5. Execution order: **L1 → L2 → (L3 or L5-wrapped-L3) → L4 (if process_context)**.

### Sub-layer L1 — Fact extraction (`layer1_deterministic.py`)

- **Tier / effort:** STANDARD / medium, via `extraction_llm` parameter. Orchestrator wires `_layer_llm("l4_extraction", STANDARD)` (L540). Separated from the main `llm` (FLAGSHIP) so Opus isn't wasted on fact decomposition.
- **Three sub-checks, sequential:**
  1. **FActScore decomposition** — `prompts/fact_decomposition.md` with `{{output_text}}` + `{{citation_texts}}`. Returns array of `{status, …}`. SUPPORTED increments `facts_verified`; NOT_SUPPORTED / CONTRADICTED increments `facts_failed`.
  2. **Numerical consistency** — `prompts/numerical_consistency.md`. Returns `{inconsistencies: [{metric, value_a, value_b, explanation}]}`.
  3. **URL liveness** — `batch_check_urls` on the sub-manifest. Pure network.
- **`infrastructure_failure` flag** (`evaluation.py:141`): set to `True` when any exception bubbles from `Layer1Evaluator.evaluate()`. Counts stay 0/0 but the flag distinguishes "skipped due to error" from "nothing to check." **Consumers must check the flag before treating zeros as quality signal.**
- **Event:** `DeterministicCheckPassed` (layer=`"L4"`).

### Sub-layer L2 — Citation gate (`layer2_citation_gate.py`)

- **No LLM.** `DOIVerifier.verify(doi)` via `HTTPDOIVerifier` (HEAD to `doi.org/<doi>`) for citations with `cit.doi`. URL-only citations are checked by `batch_check_urls` but a dead URL is **not** flagged as fabricated — only unreachable DOIs are.
- **Fuzzy title match** with `SequenceMatcher` and `TITLE_MATCH_THRESHOLD = 0.8`. Mismatch logs SUSPICIOUS but does **not** reject in Phase 1.
- **Gate semantics:** `gate_passed = len(fabricated) == 0`. Any fabrication → Layers 3/4/5 skipped, `EvaluationComplete(passed=False)`, feedback lists the fabricated IDs.
- **Event:** `CitationGateResult` (layer=`"L4"`).

### Sub-layer L3 — 10-dimension rubric (`three_pass.py`, `layer3_rubric.py`)

**`ThreePassEvaluator` is misnamed — only 2 passes are active.** Pass 1 (dimensional scoring) + Pass 2 (gestalt overlay). Pass 3 (Observation Library negative-space scan) is a stub (`three_pass.py:53`).

**10 dimensions** (`models/evaluation.py:66` weights, `layer3_rubric.py:37` prompt-file map):

| Dimension | Weight | Prompt | Tier |
|---|---|---|---|
| `intent_alignment` | 0.15 | `prompts/intent_alignment.md` | **Tier 1 floor 40** |
| `intellectual_honesty` | 0.10 | `intellectual_honesty.md` | **Tier 1 floor 40** |
| `completeness` | 0.08 | `completeness.md` | **Tier 1 floor 30** |
| `narrative_coherence` | 0.05 | `narrative_coherence.md` | **Tier 1 floor 40** |
| `analytical_depth` | 0.12 | `analytical_depth.md` | Tier 2 |
| `source_quality` | 0.10 | `source_quality.md` | Tier 2 |
| `quantitative_rigor` | 0.15 | `quantitative_rigor.md` | Tier 2 |
| `actionability` | 0.15 | `actionability.md` | Tier 2 |
| `evaluative_surprise` | 0.05 | `evaluative_surprise.md` | Tier 2 |
| `calibrated_confidence` | 0.05 | `calibrated_confidence.md` | Tier 2 |

Weights sum to 100% — prior weights summed to 105%, `narrative_coherence` was reduced 0.10 → 0.05 to correct (comment at `evaluation.py:59`).

**Tier 1 gate:** 4 parallel calls first (`asyncio.gather`). If **any** Tier 1 score < its floor → return `Layer3Result(final_score=0.0, weighted_total=0.0)` immediately. Tier 2 never runs. The dimension-level feedback is preserved for audit.

**Dimension prompt anatomy** (representative — `intent_alignment.md`): role → dimension definition → 5 scoring bands (0–20 … 81–100) → four named sub-criteria checks (counterfactual deletion, decision context mapping, specificity match, strategic framing) → anti-slop sub-check ("always-true test: if equally valid for the client's three closest competitors, it fails") → `{{sprint_contract_criteria}}` + `{{output_text}}` placeholders → required JSON `{score, feedback, sub_criteria_notes}` + `<completeness_check>` block. **ParseError propagates — `layer3_rubric.py:208` comment: "ParseError propagates — callers must not silently default to score=50."**

**Aggregation:** weighted geometric mean across all 10 dimensions (`exp(Σ w_i·log(x_i))`), scores floored at 0.01 to prevent `log(0)`. Then gestalt overlay (`prompts/gestalt_overlay.md` → `{adjustment: [-10, +10], rationale}`). Final: `max(0, min(100, geo_mean + gestalt_adj))`.

**Dimension emphasis** (from SprintContract): per-dimension multiplier 0.7–1.5, clamped at `layer3_rubric.py:105`. Weights renormalized before scoring.

**Tier / effort:** FLAGSHIP / high. Orchestrator wires `_layer_llm("l4_evaluator", FLAGSHIP, "high")`.

**Events:** `RubricDimensionScored` × 10 (or fewer on Tier 1 failure), all layer=`"L4"`.

### Sub-layer L4 — Process trajectory (`layer4_trajectory.py`)

Scores the **research process**, not the output text. Runs only when `process_context is not None and layer3_result.dimension_scores` (i.e., L3 produced real scores, not an infrastructure failure).

**Deterministic metrics** (extracted from the agent's event trail):

| Metric | Source |
|---|---|
| `source_count` | `ResearchComplete.sources_consulted` (preferred) or count of `SourceFound` |
| `unique_domains` | `urlparse(SourceFound.url).hostname`, distinct |
| `source_type_diversity` | distinct `SourceFound.source_type` + `"internal_corpus"` if any `SearchCompleted` events |
| `tool_utilization` | `len(tools_used) / len(assigned_tools + retrieval_tools_used)` |
| `round_count` | count of `FindingSynthesized` events |
| `branches_covered / missed` | sibling branch IDs from `issue_tree` |
| `citation_quality` | bucketing on `Citation.quality_score` (HIGH ≥0.75, MEDIUM ≥0.5, LOW <0.5) |

**Deterministic flags** (`_compute_deterministic_flags` L380). **Critical** flags (15-point penalty): `SINGLE_DOMAIN`, `LOW_TOOL_DIVERSITY`, `NO_HIGH_CONFIDENCE_CITATIONS`. **Warning** flags (5-point): `SINGLE_SOURCE_TYPE`, `LOW_DOMAIN_DIVERSITY`, `NO_MULTI_ROUND` (round_count ≤ 1), `LOW_SOURCE_COUNT` (≤ 4), `COVERAGE_GAP`.

**LLM pass:** one call to `prompts/process_trajectory.md` → `{qualitative_score (0–100), rationale, missed_inquiries, skepticism_assessment, additional_flags}`. Tier / effort: FLAGSHIP / high — the same `llm` passed to `Evaluator`, also used for L3.

**Process quality score** (L428): `0.5 * deterministic_score + 0.5 * qualitative_score`.

**L3↔L4 blend** (`_blend_layer3_layer4` L563): weighted geometric mean `exp(w·log(L3) + (1−w)·log(L4))`. Default `w = 0.8` (`evaluator.py:71`, tunable via `PipelineConfig.evaluator_layer3_weight`). Both sides floored at 0.01. Lazy process can't be hidden by prose — a near-zero L4 drags the composite down.

**Event:** `ProcessTrajectoryScored` (layer=`"L4"`).

### Sub-layer L5 — Cross-model ensemble (`layer5_ensemble.py`)

Wraps L3. Inert when `ensemble_llms=None` or `intensity == LIGHT_TOUCH`.

**Panel composition** (`orchestrator.py:972`):
- **LIGHT_TOUCH:** `None` — ensemble disabled.
- **STANDARD:** `[("flagship_a", Opus), ("flagship_b", Opus)]` — sampling stochasticity surfaces unstable scores without a weaker tier.
- **DEEP:** `[("flagship_a", Opus), ("flagship_b", Opus), ("standard_crossmodel", Sonnet)]`. **Sonnet is an INTERIM choice** (`orchestrator.py:990–996`) — meant to be swapped for GPT-5.4 / Gemini when an external provider lands. Play-favorites risk bounded to 1-of-3 votes by median.

**Haiku is never used for scoring, anywhere** (`orchestrator.py:998–1002`): *"FAST tier is deliberately NOT used as a judge. FAST stays in the research-agent fallback chain and in the Layer 1 deterministic fact decomposer where its extraction properties are appropriate, but judging a 10-dimension rubric is a reasoning task that requires at least Sonnet-class."*

**Execution:** `asyncio.gather(return_exceptions=True)` over all judges. Exceptions become failed `_JudgeRun` entries (not raised). If every judge fails → `Layer5Result.all_judges_failed=True`, zero `Layer3Result`.

**Aggregation:** per-dimension median across surviving judges. `feedback` concatenated with `[judge_id]` prefix per judge (`"[flagship_a] note; [flagship_b] note"`). `sub_criteria_notes` prefixed identically for audit.

**Dissenter veto:** for each of the 4 Tier 1 dimensions, if **any** judge's score is strictly below that dimension's Tier 1 floor, record a `VetoEvent`. **Veto fires on any dissent, not majority.** When `tier1_vetoed=True`: `final_score=0.0` (the aggregated median per-dimension scores are preserved for audit).

**Agreement level:** fraction of dimensions where `max(judge_scores) - min(judge_scores) <= 10.0` (`_AGREEMENT_THRESHOLD`, matches gestalt clamp width). With 1 survivor, trivially 1.0.

**Override hook:** `Pipeline(ensemble_panel_override=resolver)` swaps `_resolve_ensemble_judges` entirely. Signature `(intensity, llm_factory) → panel | None`.

**Events:** `EnsembleJudgeScored`×N → `DissenterVetoTriggered`×M → (aggregated `RubricDimensionScored`×10) → `EnsembleEvaluationComplete`. All layer=`"L5"` except the 10 aggregated dimension events which still carry layer=`"L4"`.

### Silent-failure paths

The codebase has explicit, audited escape hatches:

- **L1 `infrastructure_failure=True`** (`evaluator.py:159`). Any L1 exception → synthetic `Layer1Result(infrastructure_failure=True, facts_verified=0, facts_failed=0, ...)`. Evaluation continues. Model docstring (`evaluation.py:141`) explicitly warns downstream consumers.
- **L3 `infrastructure_failure=True`** (`evaluator.py:255`). Either ensemble or single-judge path raising → `Layer3Result(infrastructure_failure=True, final_score=0.0)` and `layer5_result=None`. The zero score is fed into composite — consumers must check the flag.
- **Sprint contract fallback** — L2 records `_fallback_task_ids`; orchestrator emits `sprint_contract_fallback` WARN per task (see §7).
- **L4 failure** (`evaluator.py:344`): log warning, `layer4_result=None`, composite stays at L3's final_score.
- **L5 all-judges-failed**: `l5_ensemble_infrastructure_failure` governance flag (WARN — score degraded but not a content signal).

---

## 9. The renderer (current MD only)

File: `src/keystone/pipeline/markdown_renderer.py`. 704 lines. Stateless, no LLM. Consumes the filtered `StructuredOutline` + `spec` + `findings` + `confidence_map` + `evaluation_results` + `CitationManifest`. Produces a 9-section consulting brief in Markdown.

Section order (outline-driven path): Title → Executive Summary → Analytical Framework → Key Findings (per branch, tier + evidence) → Areas of Uncertainty (moderate/weak/contested) → Evidence Gaps (gaps + insufficient + uncovered branches) → Absence Report → Evaluation Summary (pass rate, dimension averages) → Sources (numbered, inline `[N]` refs).

Legacy `outline=None` path preserved for pre-L2 callers. Both paths produce inline numbered citations keyed to the manifest.

**L3 events (`DraftGenerated`, `CitationFormatted`, `DeliverableAssembled`) are declared in `events.py` but NOT emitted today** — the renderer yields nothing; orchestrator returns `markdown_output: str` straight onto `PipelineResult`. Future PPTX/XLSX/PDF work will wire these events per format.

---

## 10. Cross-cutting

### 10.1 LayerAwareLLMFactory

File: `src/keystone/llm_client.py`. Supersedes the older `(tier) → LLMCallable` factory. Three access patterns:

- `factory(tier)` — legacy tier-only, still works (`__call__`).
- `factory.for_tier(tier, effort="high")` — tier + explicit effort.
- **`factory.for_layer(name)`** — resolves tier + effort from `PipelineConfig.model_mixing.<name>` + `PipelineConfig.layer_effort_overrides[name]`. This is the path `_build_components` uses for every layer.

**Claude CLI path** (`_call_claude_cli` L97): shells out to `claude -p <prompt> --model <id> --effort <effort> --output-format text --no-session-persistence --tools "" --system-prompt ""`. Model IDs come from `AppConfig.flagship_model` / `standard_model` / `fast_model` (`claude-opus-4-6` / `claude-sonnet-4-6` / `claude-haiku-4-5`). `CLAUDE_MODEL_MAP` retained as module-level export for backward compat but the claude_cli transport reads AppConfig.

**Deep research callable** (`deep_research_callable` L475): separate code path. `claude -p --model claude-sonnet-4-6 --effort medium --allowedTools "WebSearch,WebFetch"`. Does NOT clear `--tools` or `--system-prompt`.

**Semaphores:** `LayerAwareLLMFactory` holds instance-level semaphores sized by `PipelineConfig.claude_cli_concurrency` (default 10) and `research_concurrency` (default 5). Module-level `_claude_semaphore` / `_research_semaphore` preserved for legacy direct callers / tests.

### 10.2 PipelineConfig surface

File: `src/keystone/models/config.py:242`. Every tunable below is env-driven via `PIPELINE__<field>=...` (nested delimiter `__`).

| Field | Default | Purpose |
|---|---|---|
| `model_mixing.l0_specification` | `flagship` | L0 top-level tier |
| `model_mixing.l0_engagement_classifier` | `standard` | Step 1 |
| `model_mixing.l0_intent_clarifier` | `flagship` | Step 2 |
| `model_mixing.l0_decomposer_lens` | `standard` | Step 3a–c |
| `model_mixing.l0_decomposer_synth` | `flagship` | Step 3-synth |
| `model_mixing.l0_mece_validator` | `flagship` | Step 4 |
| `model_mixing.l0_priority_scorer` | `flagship` | Step 5 |
| `model_mixing.l0_task_generator` | `standard` | Step 7 |
| `model_mixing.l1_research` | `standard` | L1 synthesis |
| `model_mixing.l1_5_analysts` | `standard` | Deliberation analysts |
| `model_mixing.l1_5_aggregator` | `flagship` | Deliberation judge |
| `model_mixing.l4_extraction` | `standard` | L4 L1 extraction |
| `model_mixing.l4_evaluator` | `flagship` | L4 L3 rubric + L4 trajectory |
| `model_mixing.sprint_contract` | `flagship` | Sprint contract generator |
| `model_mixing.extraction` | `fast` | Generic extraction fallback |
| `layer_effort_overrides` | per-layer | effort: low/medium/high/xhigh |
| `research_default_rounds` | 3 | Shallow-mode loop default |
| `research_max_rounds` | 5 | Shallow-mode hard cap |
| `research_quality_threshold` | 0.8 | Claim confidence short-circuit |
| `claude_cli_concurrency` | 10 | Global `claude -p` ceiling |
| `research_concurrency` | 5 | Deep-research `claude -p` ceiling |
| `deep_research_timeout_s` | 1200 | 20 min |
| `evaluator_pass_threshold` | 60.0 | Composite score pass bar |
| `evaluator_layer3_weight` | 0.8 | L3/L4 blend weight |
| `dispute_variance_threshold` | 0.04 | Aggregator judge trigger |
| `wwhtb_confidence_threshold` | 0.6 | WWHTB trigger |
| `l5_low_agreement_threshold` | 0.30 | `l5_low_agreement` gate trigger |

Default `_DEFAULT_LAYER_EFFORTS` (`config.py:223`): L0 all at xhigh or medium; L1.5 aggregator at xhigh; L4 evaluator at high; L4 extraction at medium; extraction at low.

### 10.3 Event stream (summary)

Base `PipelineEvent` (`events.py:23`) carries `event_id`, `engagement_id`, `client_id`, `timestamp`, `layer`. 37 concrete event classes, union `AnyPipelineEvent` at L516. Layer tags: `L0`, `L1`, `L1.5`, `L2`, `L3`, `L4`, `L5`, `META`, `HITL`, `Retrieval`, `CitationProcessor`.

Consumers typically filter by layer tag. Note: L4's internal sub-layers emit `layer="L4"` for most events but L5 events carry `layer="L5"` — a consumer filtering `layer="L4"` to "see all evaluator events" will miss the ensemble.

### 10.4 Governance (`ProfileExecutionPolicy`)

File: `src/keystone/governance/policy.py`. Three pipeline profiles (`PipelineProfile.LIGHT/STANDARD/DEEP`) set the enforcement matrix. Gates are `QualityFlag(gate, action, severity)`. Actions:

| Action | Effect |
|---|---|
| `WARN` / `DEGRADE` | `GovernanceState.degraded = True` |
| `HALT` / `ESCALATE` | `GovernanceState.halted = True` (orchestrator's `_raise_if_halted` halts the pipeline) |

**Gates the pipeline raises:**

| Gate | Trigger | Action |
|---|---|---|
| `l4_citation_fabrication` | L2 citation gate failed | **HALT** |
| `l4_layer1_discrepancies` | facts_failed>0 or numerical issue or dead URL | WARN (LIGHT) / DEGRADE (STANDARD, DEEP) |
| `l4_rubric_threshold` | `not result.passed` | DEGRADE (STANDARD) / ESCALATE (DEEP) |
| `l5_ensemble_infrastructure_failure` | `Layer5Result.all_judges_failed` | WARN |
| `l5_ensemble_dissenter_veto` | Tier 1 veto and not passed and profile != LIGHT | **ESCALATE** (always — DEGRADE would hide the signal on STANDARD) |
| `l5_ensemble_degraded_panel` | Some but not all judges failed | WARN |
| `l5_low_agreement` | `agreement_level < 0.30`, ≥2 judges, no veto/all-fail | WARN (STANDARD) / ESCALATE (DEEP) |
| `sprint_contract_fallback` | L2 fallback fired | WARN (per-task) |
| `evaluation_coverage` | LIGHT: all must pass; STANDARD: all PRIMARY + ≥60% overall; DEEP: all PRIMARY/CRITICAL + ≥80% overall | **HALT** |

### 10.5 HITL gates

File: `src/keystone/hitl/gate.py`. Two firing sites: after L0 spec emit (`spec_engine.py:282`) and after L1.5 deliberation complete (`deliberation.py:191`). Both skip on `PipelineProfile.LIGHT` via `policy.should_run_hitl_gate()` or when `db_session_factory is None`.

**Phase 1 impl:** DB polling at 1s interval, default timeout 3600s. Phase 2: Temporal Signal (no interface change).

**`MODIFIED` status is a stub** — reviewer modifications are delivered as JSON but NOT applied back into the issue tree / task list / confidence map. The gate raises `GateModificationRequiredError` / `RuntimeError` and halts.

### 10.6 Retrieval wiring

File: `src/keystone/gateway/retrieval_bridge.py`. `register_retrieval_handlers(gateway, service, event_sink)` attaches IN_PROCESS handlers for `semantic_search` and `hybrid_search` to the gateway.

**`semantic_search` and `hybrid_search` are `SYSTEM_OWNED_TOOLS`** (`tool_names.py:93`). `ToolAuthorizer.check` blocks them from appearing in any `ResearchTask.assigned_tools` — agents cannot call retrieval tools directly via the gateway's tool-exec path. Known stub: a system-path that lets shallow-mode agents invoke retrieval via an orchestrator-side helper is on the roadmap (TODO.md).

**Lane E is institutional memory.** `service.ingest_institutional(records)` ingests with `engagement_id=None`, so every engagement sees the corpus. Inter-agent isolation is enforced structurally via `exclude_engagement_id=<caller.engagement_id>` injected by the bridge handlers — any future chunk ingested with a non-None engagement_id (sibling agent's in-progress work) is hidden from other agents in the same engagement.

**Current stubs** (`retrieval_bridge.py:17`): `semantic_search` and `hybrid_search` both delegate to the same `RetrievalService.search` pipeline. Splitting them at the service layer (semantic-only vs hybrid+BM25) is a follow-up.

---

## 11. Known stubs / deferred items

Consolidated list of things the codebase explicitly flags as incomplete. Cross-reference against Nate-audit findings — if something maps, it's a known gap, not a new discovery.

| Area | Stub | Source |
|---|---|---|
| L0 Step 5 | Priority scoring lacks `/estimated_cost` denominator (full VOI formula) | `priority_scorer.py:6` |
| L0 HITL | `MODIFIED` responses raise instead of applying patches | `hitl/gate.py:209` |
| L0 task→agent | `task.assigned_model` reported in events but not routed to pool LLM selection | `agent_pool.py` (shared `llm`) |
| L1 shallow | Shallow agents can't invoke `semantic_search`/`hybrid_search` (structurally blocked; system-path helper TODO) | `tool_names.py:84`, TODO.md |
| L1 deep | Deep mode bypasses `ToolAuthorizer` / rate limiter / circuit breaker for WebSearch/WebFetch | `research_agent.py:276–291` |
| L1 deep | Deep-mode EV-ref enforcement (keeping Lane E SHA-256 + locator on Citations) | TODO.md |
| L1 token accounting | `ToolResult.tokens_used = 0` hardcoded; shallow-mode synthesis uses char-heuristic | `mcp_gateway.py:404`, `research_agent.py:590` |
| L1 task-aware evidence | Evidence provider returns "all records" default; no filter on `task.required_sources` | TODO.md |
| CitProc | `fabrication_flags` always empty — field reserved for L4's citation gate to populate downstream | `citations.py:229`, `processor.py:204` |
| Retrieval | `semantic_search` and `hybrid_search` run identical code path | `retrieval_bridge.py:17` |
| Retrieval | LLM-backed query router (currently `RuleBasedQueryRouter`) | TODO.md |
| Retrieval | voyage-finance-2 vs voyage-3 benchmark on ≥1000 chunks | TODO.md |
| Retrieval | Integration smoke test end-to-end against live PG | TODO.md |
| L1.5 | `DiscoUQFeatures` defined on `HighConfidenceClaim` but not populated by builder | `confidence_builder.py` |
| L2 | Framework execution is deterministic-only; LLM-augmented (Porter's matrix, scenario shocks, Value Chain stage analysis) deferred Phase 2 | TODO.md |
| L2 | Bidirectional sprint-contract negotiation (Generator ↔ Evaluator counter-propose) — schema supports, logic deferred Phase 2 | TODO.md |
| Evaluator L3 | "Three-pass" is really two passes — Pass 3 (Observation Library negative-space scan) is a placeholder | `three_pass.py:53` |
| Evaluator L4 | `tokens_consumed` from process-trajectory LLM call not captured in totals | TODO.md |
| Evaluator L4 | `layer3_weight` calibration against human-scored samples | TODO.md |
| Evaluator L5 | Agreement threshold + low-agreement threshold calibration against human samples | TODO.md |
| Evaluator L5 | DEEP panel's `standard_crossmodel` slot should be external provider (GPT-5.4 / Gemini) | TODO.md |
| Evaluator L5 | Full-pipeline integration test asserting 3-judge-per-task + ordering + seeded dissent surfacing dissenter_veto | TODO.md |
| Evaluator L5 | Cost observability: per-task judge-count × call-count | TODO.md |
| Contracts | `PostSynthesisVerifierContract` protocol defined but not implemented — orchestrator uses a local `_filter_confidence_map_by_passed_tasks` helper | `contracts.py:41` |
| Contracts | `GenerationContract` signature drift — takes `contracts: list[SprintContract]` but the real renderer takes outline + manifest + spec + evaluation_results + confidence_map + findings | `contracts.py:263`, `orchestrator.py:607` |
| Gateway | Real-MCP phase: FastMCP-based client replacing `MockMCPClient` so `edgartools-mcp` (and other stdio servers) actually launch | TODO.md |
| MCP | Phase 2: route deep-mode tool calls through `MCPGateway.call_tool` (not just the audit log) once provider-native WebSearch/WebFetch have gateway-owned wrappers | TODO.md |
| Docling | Integration smoke test against real SEC filing PDF once docling installed | TODO.md |
| Renderer | L3 events (`DraftGenerated`/`CitationFormatted`/`DeliverableAssembled`) declared but not emitted by today's MarkdownRenderer | `events.py:286–308` |
| Renderer | PPTX/XLSX/PDF outputs — parked per user direction 2026-04-19; Markdown is the only deliverable today | — |

---

## 12. How to update this doc

This file is the reference. When the codebase drifts:

- **Layer added or removed** → update §1 diagram + §1 table + add/remove a §N section.
- **Prompt file changed** → update the relevant §3–§8 row; quote the new directive if it changes behavior.
- **Tier / effort change** → update §10.2 table and the relevant layer row.
- **New governance gate** → §10.4 row.
- **Stub resolved** → delete the §11 row. Don't append "(resolved 2026-05-XX)" — git blame is the history.
- **Major architectural shift** → re-verify everything and bump the `Last verified against:` line at the top.

For audit sessions using this atlas: every claim has a file:line. If you find a mismatch, trust the code — then fix the atlas.
