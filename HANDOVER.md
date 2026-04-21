# Handover

Last updated: 2026-04-21 (end of day)
Session: Gap remediation + prompt audit + UI v0.1 + checkpoint/resume + L1 architecture research

## What Changed (Gap remediation session, 2026-04-21)

Ingested HANDOFF.md (temp session doc) + 4 Deep Research reports on
OpenClaw/Claude Code architectures into `research/external-sources/
openclaw-claude-code/s{1,2,3,4}/`. Verified all 17 gaps from the Nate
corpus audit against the live codebase — all 17 CONFIRMED. Verification
status appended to `GAP-AUDIT.md`.

**Tier 1 gap fixes landed (7 commits):**

- **GAP-06** `l0_mece_failed` governance gate: WARN on LIGHT, DEGRADE
  on STANDARD, HALT on DEEP. Orchestrator checks `scope_valid` after L0.
- **GAP-07** `l1_tool_dead_letter` governance gate: orchestrator polls
  `MCPGateway.dead_letters` after L1, fires WARN (DEGRADE on DEEP).
- **GAP-01** `AgentPool` now resolves per-task LLM from
  `task.assigned_model` via an optional `llm_factory` callback.
  Falls back to shared pool LLM when factory absent or model is None.
- **GAP-11** L1 research prompts externalized to `.md` files:
  `research/prompts/{deep_research,synthesis,absence_report}.md` with
  `{{placeholder}}` substitution via `_prompts.py` loader.
- **GAP-10** Model-version YAML frontmatter added to all 27 prompt
  `.md` files. Six loaders updated with `_strip_frontmatter()`. New
  canary test `tests/canary/test_prompt_freshness.py` fails when any
  prompt is >1 version behind `CURRENT_MODEL`.
- **GAP-12** `semantic_search` now runs vector-only (embed → vector
  store); `hybrid_search` unchanged (vector + BM25 → RRF → rerank).
  New `RetrievalService.search_semantic()` method. 11 new tests.

- **GAP-02 + GAP-08** Token accounting: gateway `tokens_used`
  replaced with char-estimate, L4 trajectory captures
  `tokens_consumed`, `PipelineResult.tokens_by_layer` added.
  Cost governance: `l1_cost_ceiling` WARN gate fires when per-task
  research tokens exceed `PipelineConfig.research_token_ceiling_per_task`
  (default 50K).
- **GAP-04 Phase 1** HITL modifications now persisted to
  `/tmp/keystone/{eid}/hitl_modifications/{gate}_{ts}.json` before
  the gate raises. `ReviewGateModified` event carries
  `modifications_path`. Phase 2 (apply + resume) deferred.

All Tier 1 gaps are now complete.

- **GAP-17** Checkpoint/resume implemented: `CheckpointStore`
  (aiosqlite), 5 stage boundaries (POST_SPEC, POST_L1_CITPROC,
  POST_DELIBERATION, POST_STRUCTURING, POST_EVALUATION),
  `Pipeline.resume_with_events()`, `PipelineRunner.resume()`,
  schema versioning, TTL cleanup. Opt-in via `checkpoint_store`
  constructor parameter. 22 new tests.

**Tier 2 gaps also completed this session:**

- **GAP-03** Task-aware evidence filtering (source-family +
  Jaccard relevance ranking)
- **GAP-05** ObservationStore (aiosqlite, first slice of
  Observation Library)
- **GAP-13** Post-run observation ingest hook (emits
  `ObservationRecorded` events)

**Prompt audit completed this session (3 phases):**

- **Phase A**: Authority-marker instruction on 10 rubric prompts,
  absence report expansion, prompt-injection mitigation in deep
  research, tool list templating, 8 L1.5 prompts externalized to
  `.md` files
- **Phase B**: 5 methodology prompts rewritten (2-3 sentences →
  15-30 sentences with genuine analytical procedures), synthesis
  prompt expanded, confidence bands aligned to 5-tier system,
  judge fallback changed to median, curmudgeon challenge added,
  Tier 1 dims added to sprint contract emphasis, gestalt overlay
  clamped so it cannot flip pass/fail
- **Phase C**: Completeness floor 30→40, narrative coherence weight
  0.05→0.08 (evaluative surprise 0.05→0.02), consistency check
  contradiction vs tension guidance, WWHTB testability definition

Owner decisions on all 10 design questions logged in
`notes/PROMPT-DECISIONS-2026-04-21.md`.

**UI v0.1 built (Codex):**

FastAPI serving layer (`src/keystone/server/`) wrapping
`Pipeline.run_with_events` with WebSocket event streaming.
React+TS+Vite frontend (`frontend/`) with session sidebar, chat
panel, event log, markdown result viewer. Architecture doc at
`notes/UI-ARCHITECTURE.md` (1135 lines) with full API contracts
and 4-phase build plan. UI is paused for competitive teardown
research before v0.2.

**L1 sub-agent architecture researched:**

Deep research report at `research/external-sources/openclaw-
claude-code/l1-architecture-research.md`. Two-tier
orchestrator-worker pattern: LeadResearcher (FLAGSHIP, planning
+ synthesis) dispatches 3-5 SubResearcher workers (STANDARD) per
task. Evidence-based from DeepMind 180-config study, NeurIPS 2025
martingale proof, DMAD ICLR 2025. All 10 invariants preserved.
Phase 1 implementation prompt ready. THIS IS THE HIGHEST-PRIORITY
NEXT ENGINEERING WORK — directly determines output quality.

**New workstream flagged:** Prompt audit and optimization. All 35
pipeline prompts (27 `.md` + 8 inline Python in deliberation) were
built without owner review. Added to TODO.md as active item. Full
prompt catalog produced (9 L0 + 3 L1 + 8 L1.5 + 1 L2/L4 bridge +
14 L4 + 0 L5). L1.5 deliberation prompts still inline in Python.

**Test count:** 1501 passing (from 1404 baseline, +97 new).

**Remaining gaps:**
- GAP-09 (evaluator calibration) — blocked until first pipeline
  run produces scored data to calibrate against
- GAP-15 (deep-mode gateway) — blocked on GAP-14 (SDK transport)
- GAP-04 Phase 2 (apply HITL modifications + resume) — unblocked
  now that GAP-17 is implemented

**Deferred:** GAP-14 (SDK transport), GAP-16 (prompt caching).

**Next priority workstreams:**
1. L1 sub-agent Phase 1 implementation (prompt ready, blocked on
   nothing — launch in new CC session)
2. Competitive teardown for UI design (deep research running)
3. First actual pipeline run (unblocks GAP-09 calibration)
4. UI v0.2 (after teardown completes)

## What Changed (Audit remediation pass, 2026-04-18 follow-up)

A second session audited the pipeline-config changes and implemented
every follow-up fix the audit identified. Four source fixes + six test
coverage gaps, zero deferrals.

**Fix 1 — Research agent ``current_tier`` from config.**
:class:`ResearchAgent` and :class:`AgentPool` gained a
``current_tier: ModelTier`` kwarg (default ``STANDARD`` for
back-compat). The orchestrator resolves it from
``PipelineConfig.model_mixing.l1_research`` via
``_resolve_layer_tier_or``. ``ErrorRecovery`` now walks the fallback
chain from the correct baseline when operators retune
``l1_research`` (pre-fix, recovery always thought baseline was
STANDARD regardless of the actual LLM tier).

**Fix 2 — SprintContractGenerator through PipelineConfig.**
:class:`ModelMixingConfig` gained ``sprint_contract: str = "flagship"``
and ``_DEFAULT_LAYER_EFFORTS`` gained ``"sprint_contract": "high"``.
The orchestrator routes generator construction through
``_layer_llm("sprint_contract", FLAGSHIP, "high")`` so sprint-contract
generation is now a config-driven layer like every other LLM call site.

**Fix 3 — Removed dead config fields.** ``l2_structuring`` and
``l3_generation`` are gone from :class:`ModelMixingConfig` and
``_DEFAULT_LAYER_EFFORTS``. L2 ContentStructurer is pure Python and L3
is the MarkdownRenderer; these fields claimed to control tiers but
never mapped to an LLM call.

**Fix 4 — ``get_deep_research_callable`` honors programmatic
AppConfig.** Two halves: (a) the orchestrator now prefers
``factory.deep_research_callable()`` when ``llm_factory`` is a
:class:`LayerAwareLLMFactory`, preserving programmatic overrides that
were constructed into the factory; (b) the module-level
``get_deep_research_callable`` docstring now spells out that env vars
always flow (BaseSettings re-read) but programmatic overrides require
passing ``config`` explicitly.

**Test coverage — six gaps filled, nine tests added in a new
``tests/unit/test_remediation_coverage.py``:**
1. Sprint-contract fallback governance flag emission end-to-end
   (spies on ``ProfileExecutionPolicy.apply_flag`` during a full pipeline
   run with a raising generator).
2. ``Layer3Result.infrastructure_failure=True`` is distinguishable
   from a genuine zero-dimension rubric result (different feedback,
   empty vs populated dimension_scores, same pass/fail).
3. Two tests for :func:`get_deep_research_callable` (programmatic
   ``AppConfig`` → custom model flows; no config → default model).
4. Two tests for Layer 4 trajectory (structural: ``Evaluator._layer4._llm``
   is the primary llm; end-to-end: the factory's ``l4_evaluator``
   layer resolves to FLAGSHIP model + ``reasoning.effort="high"``).
5. Per-task :class:`Evaluator` freshness (2-task pipeline run captures
   2 distinct Evaluator instances; mutating one does not affect the
   other).
6. Two tests for ``analyst_tier`` env-var end-to-end
   (``PIPELINE__MODEL_MIXING__L1_5_ANALYSTS=flagship`` reaches
   :attr:`Deliberation._analyst_tier`; the :class:`AnalystSpawned`
   event reports ``model_tier="flagship"``).

**Verification.** 1395 → **1404 unit+canary passing** (+9 new, 3
xfailed unchanged). Ruff net-zero on touched files (pre-existing
errors unchanged, zero new). Mypy net-zero on src/ (128 errors
pre-existing, 128 post-fix). Ruff clean on the new test file after
autofixes for unused imports, sort order, zip(strict=True), and
contextlib.suppress.

## What Changed (Pipeline config + quality fixes session)

Landed a comprehensive audit sweep. Built the :class:`PipelineConfig`
system that unifies per-layer model tier assignment, per-layer
reasoning effort, research concurrency + quality thresholds, evaluator
pass threshold + L3/L4 blend weight, deliberation thresholds, and L5
low-agreement threshold — previously each was a module-level constant
or hardcoded literal. Wired :class:`LayerAwareLLMFactory` so the
``claude_cli`` path reads AppConfig (no more hardcoded CLAUDE_MODEL_MAP)
and every component that used to receive a raw tier factory now routes
through ``factory.for_layer(name)`` for config-driven tier + effort.
Owner-reviewed model-tier fixes: L0 Spec Engine runs at xhigh effort;
Layer 1 evaluator takes a dedicated STANDARD (Sonnet) extraction LLM
while Layer 3 rubric stays FLAGSHIP; Spec Engine per-step tiers
(classifier/task-generator at STANDARD, decomposer lens at STANDARD
with FLAGSHIP synthesis, clarifier/validator/scorer at FLAGSHIP);
Decomposer now honors its docstring's lens / synth split. Silent
failures surfaced: ``Layer1Result`` and ``Layer3Result`` gained
``infrastructure_failure: bool`` so failed scoring is distinguishable
from zero-score content; sprint-contract fallback emits a
``sprint_contract_fallback`` governance WARN flag per task. Dead-code
cleanup: research agent routes LLM calls through ``ErrorRecovery`` with
the fallback chain truncated at STANDARD (research never degrades to
Haiku); stripped ``slop_detected``/``slop_details`` from the 10
evaluator prompt files that asked for fields the parser never read;
``AnalystSpawned`` reports the actual analyst tier via a new
``analyst_tier`` constructor parameter; task-generator tool padding
uses distinct :data:`BASELINE_AGENT_TOOLS` instead of duplicating
``DEFAULT_TOOLS[0]``. Slop detector deleted per owner decision
(``src/keystone/quality/``, ``tests/unit/quality/``, the
``SlopDetected`` event, the ``_scrub_slop`` integration, all
imports). Baseline was 1431 unit+canary passing; final is **1395
passing + 3 xfailed** (-87 slop tests deleted, +51 new tests covering
config + tier fixes + silent-failure flags + error-recovery wiring +
tool-padding + truthful analyst-tier reporting; net delta matches the
slop-test removal). Ruff -4 net on the project; mypy net-zero; no new
errors introduced.

### Configuration system (Phase 1)

- ``src/keystone/models/config.py`` — new :class:`PipelineConfig`
  consolidates every tunable previously scattered across module-level
  constants. Nested under :class:`AppConfig.pipeline`, env-var drivable
  via ``PIPELINE__<field>=...``. Includes per-layer model-mixing
  fields, per-layer effort overrides, research knobs (default/max
  rounds, quality threshold, deep research timeout, Claude CLI and
  research concurrency), evaluator knobs (pass threshold, L3/L4 blend
  weight), deliberation knobs (dispute variance, WWHTB confidence), L5
  low-agreement threshold. The default instance exactly reproduces
  prior hardcoded behavior so unchanged call sites see no regression.
- :class:`ModelMixingConfig` expanded from 8 fields to 16 (adds the
  spec-engine per-step split + Layer 1 extraction tier).
- ``src/keystone/llm_client.py`` — :class:`LayerAwareLLMFactory`
  supersedes the tier-only factory. Still satisfies the legacy
  ``Callable[[ModelTier], LLMCallable]`` signature via ``__call__`` so
  every existing test keeps working. Adds ``for_tier(tier, effort=...)``
  and ``for_layer(name)`` access patterns. The ``claude_cli`` path now
  reads ``AppConfig.flagship_model`` / ``standard_model`` /
  ``fast_model`` instead of a hardcoded ``CLAUDE_MODEL_MAP``. Semaphores
  are instance-level so per-pipeline concurrency limits can be tuned
  without a module reload. ``CLAUDE_MODEL_MAP`` and ``_research_semaphore``
  remain as backward-compat module-level exports for tests.
- ``src/keystone/llm_settings.py`` — :data:`LAYER_REASONING_EFFORT`
  now sources from :data:`_DEFAULT_LAYER_EFFORTS` in ``config.py`` so
  a single table drives both the class default and the
  back-compat export. New :func:`get_layer_tier` /
  :func:`get_layer_effort` helpers bridge ``PipelineConfig`` to
  ``get_llm_for_tier``.
- ``src/keystone/pipeline/orchestrator.py`` — ``Pipeline.__init__``
  accepts ``pipeline_config: PipelineConfig | None``. When omitted,
  defaults come from the factory's own ``pipeline_config`` attribute
  (real factory path) or a fresh ``PipelineConfig()`` (test path).
  New private ``_layer_llm`` helper hides the factory-type branching
  so ``_build_components`` can say ``self._layer_llm("l0_specification",
  fallback_tier=FLAGSHIP, fallback_effort="xhigh")`` and the helper
  picks the right resolution path. Pipeline threads
  ``dispute_variance_threshold``, ``wwhtb_confidence_threshold``,
  research rounds / quality threshold, evaluator pass_threshold /
  layer3_weight, and ``l5_low_agreement_threshold`` into each sub-
  component at construction time.

### Model-tier fixes (Phase 2)

- **Fix A — L0 xhigh** (``orchestrator._build_components``): L0 spec
  engine constructs its LLM via ``_layer_llm("l0_specification",
  fallback_tier=FLAGSHIP, fallback_effort="xhigh")``. The real factory
  reads ``PipelineConfig.layer_effort_overrides["l0_specification"]
  = "xhigh"``. L0 is the most critical layer; it now runs at maximum
  reasoning depth.
- **Fix B — Layer 1 STANDARD extraction** (``evaluator.Evaluator``):
  new ``extraction_llm`` constructor parameter fed into
  ``Layer1Evaluator``. Orchestrator wires this to
  ``_layer_llm("l4_extraction", fallback_tier=STANDARD)``. Opus is no
  longer wasted on fact decomposition; Layer 3 rubric scoring keeps
  its FLAGSHIP LLM.
- **Fix C — Spec engine per-step tiers** (``SpecificationEngine``):
  ``__init__`` accepts ``classifier_llm``, ``clarifier_llm``,
  ``decomposer_lens_llm``, ``decomposer_synth_llm``,
  ``mece_validator_llm``, ``priority_scorer_llm``,
  ``task_generator_llm`` kwargs. Orchestrator supplies each via
  ``_layer_llm`` with layer names that resolve to the owner-reviewed
  tier assignments. Legacy single-``llm`` construction is preserved
  for tests.
- **Fix D — Decomposer split** (``Decomposer``): ``__init__`` accepts
  ``lens_llm`` and ``synth_llm`` separately. The three-lens
  decomposition runs against ``lens_llm`` (STANDARD), the synthesis
  meta-agent runs against ``synth_llm`` (FLAGSHIP), matching the
  docstring that always claimed this split.

### Silent-failure fixes (Phase 3)

- **Fix E — Layer1Result infrastructure_failure**: new boolean field
  on ``Layer1Result``. Set to ``True`` when the evaluator catches an
  exception from ``Layer1Evaluator.evaluate``; counts stay at 0/0 but
  downstream consumers can distinguish "fact-checking skipped due to
  error" from "no facts to check".
- **Fix F — Layer3Result infrastructure_failure**: mirror field on
  ``Layer3Result``. Set to ``True`` both when
  ``ThreePassEvaluator.run`` raises and when the Layer 5 ensemble
  path raises. Prevents silent zero-score corruption of downstream
  analytics.
- **Fix G — Sprint contract fallback governance flag**: new
  ``self._fallback_task_ids: set[str]`` on ``ContentStructurer``
  records task IDs whose contract came from the task-derived
  fallback path. Orchestrator drains the set after ``structure()``
  and emits a per-task ``sprint_contract_fallback`` WARN
  ``QualityFlag`` via ``policy.apply_flag``. Operators now see every
  fallback; previously it was silent.

### Dead-code and cleanup (Phase 4)

- **Fix H — ErrorRecovery wiring + FALLBACK_CHAIN truncation**:
  ``ResearchAgent._execute_shallow`` and ``_generate_absence_report``
  now route LLM calls through ``self._error_recovery.execute_with_
  recovery(..., current_tier=STANDARD)`` instead of
  ``retry_llm_call``. ``FALLBACK_CHAIN`` truncated to ``[FLAGSHIP,
  STANDARD]`` — FAST removed. Research tasks must never degrade to
  Haiku; extraction-only paths (e.g. Layer 1 fact decomposition via
  extraction_llm) retain FAST via their own wiring.
- **Fix I — Strip slop_detected / slop_details** from 10 evaluator
  prompts (``actionability.md`` et al.). The rubric scorer never
  parsed these fields; they were dead prompt surface.
- **Fix J — AnalystSpawned truthful tier reporting**:
  ``Deliberation.__init__`` takes an ``analyst_tier: ModelTier``
  parameter (default STANDARD matches the historic hardcoded value);
  the ``AnalystSpawned`` event reports whatever was passed in.
  Orchestrator supplies ``analyst_tier`` derived from
  ``PipelineConfig.model_mixing.l1_5_analysts`` so mixed-tier
  ensembles produce truthful observability events.
- **Fix K — Task generator tool padding**: new
  :data:`BASELINE_AGENT_TOOLS = [EXA_SEARCH, BRAVE_SEARCH,
  PAPER_SEARCH]` in ``tool_names.py``. New
  ``_ensure_minimum_distinct_tools`` helper in ``task_generator.py``
  pads short template tool lists with distinct baseline tools instead
  of duplicating ``DEFAULT_TOOLS[0]`` (which produced useless "three
  copies of exa_search" lists).

### Slop detector deletion (Phase 5)

- Deleted ``src/keystone/quality/`` (entire package:
  ``patterns.py``, ``slop_detector.py``, ``__init__.py``).
- Deleted ``tests/unit/quality/`` (83 tests for the slop detector
  plus 4 ``TestSlopFiltering`` cases in
  ``tests/unit/structuring/test_content_structuring.py``).
- Removed ``SlopDetected`` event class and its entry in the
  ``AnyPipelineEvent`` union from ``src/keystone/events.py``.
- Removed ``_scrub_slop``, the ``slop_detector`` constructor
  parameter, and the ``_slop_detector`` instance state from
  ``ContentStructurer``. Section text is now passed through to the
  evaluator as rendered, with no intermediate pattern-match scrub.

## Files touched (this session)

**Modified source:**
- ``src/keystone/models/config.py`` (+ :class:`PipelineConfig`,
  expanded :class:`ModelMixingConfig`, :data:`_DEFAULT_LAYER_EFFORTS`)
- ``src/keystone/llm_settings.py`` (rewritten to bridge
  :class:`PipelineConfig`)
- ``src/keystone/llm_client.py`` (+ :class:`LayerAwareLLMFactory`,
  config-driven claude model + effort, instance semaphores, optional
  effort kwarg on ``get_llm_for_tier``)
- ``src/keystone/pipeline/orchestrator.py`` (per-layer LLM wiring,
  sprint-contract fallback governance flag, config threading)
- ``src/keystone/evaluator/evaluator.py`` (+ ``extraction_llm``
  parameter + infrastructure_failure tagging on L1/L3 fallbacks)
- ``src/keystone/specification/spec_engine.py`` (+ per-step LLM
  kwargs)
- ``src/keystone/specification/decomposer.py`` (lens/synth split)
- ``src/keystone/specification/task_generator.py`` (+
  ``_ensure_minimum_distinct_tools`` baseline padding helper)
- ``src/keystone/deliberation/deliberation.py`` (+ ``analyst_tier``
  parameter + config-driven deliberation thresholds)
- ``src/keystone/deliberation/aggregator.py`` (+
  ``dispute_variance_threshold`` constructor parameter)
- ``src/keystone/deliberation/wwhtb.py`` (+ ``confidence_threshold``
  kwarg)
- ``src/keystone/research/research_agent.py`` (ErrorRecovery wire-
  up, config-driven rounds/quality threshold, drop unused
  ``retry_llm_call`` import)
- ``src/keystone/research/agent_pool.py`` (propagate research knobs)
- ``src/keystone/research/error_recovery.py`` (FALLBACK_CHAIN
  truncated to ``[FLAGSHIP, STANDARD]``)
- ``src/keystone/governance/policy.py`` (+
  ``low_agreement_threshold`` constructor parameter)
- ``src/keystone/structuring/content_structuring.py`` (slop scrub
  removed, ``_fallback_task_ids`` tracker added)
- ``src/keystone/events.py`` (``SlopDetected`` removed from class
  and union)
- ``src/keystone/models/evaluation.py`` (+ ``infrastructure_failure``
  fields on L1/L3 results)
- ``src/keystone/tool_names.py`` (+ :data:`BASELINE_AGENT_TOOLS`)
- ``src/keystone/evaluator/prompts/*.md`` (10 prompt files — slop
  fields stripped from output contract)

**Deleted:**
- ``src/keystone/quality/`` (entire package)
- ``tests/unit/quality/`` (entire package)

**Modified tests:**
- ``tests/unit/test_llm_client.py`` (``LAYER_REASONING_EFFORT``
  assertions updated for the expanded layer set)
- ``tests/canary/test_architectural_guarantees.py``
  (``infrastructure_failure`` fields included in L1/L3 fallback
  result assertions)
- ``tests/unit/research/test_error_recovery.py`` (chain expectations
  updated; added ``test_research_never_degrades_to_haiku``)
- ``tests/unit/deliberation/test_deliberation.py`` (+
  ``test_analyst_spawned_tier_reflects_constructor_override``)
- ``tests/unit/specification/test_task_generator.py`` (+
  ``TestEnsureMinimumDistinctTools`` class with 6 tests)
- ``tests/unit/structuring/test_content_structuring.py`` (``TestSlopFiltering``
  class removed)
- ``tests/unit/evaluator/test_evaluator.py``,
  ``tests/unit/evaluator/test_layer3.py`` (slop_detected / slop_details
  stripped from mock dimension responses)

**New tests:**
- ``tests/unit/test_pipeline_config.py`` (23 tests — config
  defaults, layer tier/effort resolution, env-var routing, factory
  access patterns)
- ``tests/unit/test_model_tier_fixes.py`` (8 tests — evaluator
  extraction_llm flow, decomposer lens/synth split, spec-engine
  per-step wiring)
- ``tests/unit/test_silent_failure_fixes.py`` (8 tests —
  infrastructure_failure flag surfacing + sprint-contract fallback
  tracking)
- ``tests/unit/research/test_research_agent_error_recovery.py`` (4
  tests — chain truncation, recovery-path log assertion)

## Test baseline

``pytest tests/unit/ tests/canary/`` = **1395 passed + 3 xfailed**
(vs. 1431 prior). Net delta: +51 new tests, -87 slop tests deleted.
Ruff on ``src/keystone/`` net-clean (-4 errors vs baseline). Mypy
strict net-zero (128 errors vs baseline 128). Zero new ruff or mypy
errors introduced by this session.

---

## Previous Session (kept for continuity)

Session: Layer 5 remediation — judge panel redesign + audit fixes

## What Changed (L5 remediation session)

Responded to the Layer 5 audit by redesigning the judge panel away from
Haiku (FAST tier) — an extraction/classification model without the
reasoning depth required for nuanced 10-dimension rubric scoring — and
landed every audit finding: low-agreement and reduced-panel governance
gates, a configurable judge-panel override on ``Pipeline``, the
``MinorityVetoTriggered`` → ``DissenterVetoTriggered`` rename, per-judge
attribution on aggregated ``sub_criteria_notes``, and the seven missing
tests. Baseline was 1332 unit+canary passing; final is **1431 +
3 xfailed unchanged (+99 new tests)**. Ruff/mypy on touched files are
net-clean (zero new errors; mypy actually -1).

### Judge panel redesign (evaluator/orchestrator)

- STANDARD profile: ``[("flagship_a", Opus), ("flagship_b", Opus)]``.
  Two independent Opus runs — sampling stochasticity exposes unstable
  rubric scores without admitting a weaker tier. Zero Play Favorites
  risk (neither judge is the Sonnet tier that L1 generates with).
- DEEP profile: ``[("flagship_a", Opus), ("flagship_b", Opus),
  ("standard_crossmodel", Sonnet)]``. Sonnet adds cross-model diversity
  inside the Anthropic family. Play Favorites risk bounded to 1-of-3
  votes by median aggregation and surfaced via ``agreement_level``.
  **The ``standard_crossmodel`` slot is an INTERIM choice** — intended
  to be replaced by an external provider (GPT-5.4 / Gemini) when one is
  integrated into the LLM client factory. Tracked in TODO.md under "L5
  ensemble follow-ups."
- LIGHT_TOUCH: no ensemble (unchanged).
- Haiku (FAST) is no longer used for any evaluator scoring path. It
  remains in the L1 fallback chain (``error_recovery.FALLBACK_CHAIN``)
  and extraction-only Layer 1 paths, where its classification strengths
  are appropriate.

### ``Pipeline(ensemble_panel_override=...)``

New optional constructor param: a callable ``(intensity, llm_factory) ->
panel | None``. When supplied, the orchestrator calls it instead of
``_resolve_ensemble_judges``. Default preserves the built-in mapping.
Ops can tune panel composition per deployment without patching source.

### Rename: ``MinorityVetoTriggered`` → ``DissenterVetoTriggered``

Veto fires on ANY Tier 1 dissent below floor, not strictly a numeric
minority. The old name overstated the constraint. Renamed across:
``events.py`` class + union entry, ``evaluator.py`` yield site,
``contracts.py`` docstring, ``layer5_ensemble.py`` / ``evaluator.py`` /
``models/evaluation.py`` docstrings and field descriptions, and both
test files. Governance gate renamed from ``l5_ensemble_tier1_veto`` to
``l5_ensemble_dissenter_veto``.

### New governance gates (policy.py)

- ``l5_ensemble_degraded_panel`` (WARN): fires when at least one judge
  failed but not all of them. Surfaces silent panel shrinkage so ops
  know the ensemble signal is weaker than designed.
- ``l5_low_agreement`` (WARN under STANDARD, ESCALATE under DEEP):
  fires when ``agreement_level < 0.30`` and no Tier 1 veto. Single
  most valuable ensemble signal — inter-judge disagreement — now
  surfaces as an actionable flag instead of staying buried on
  ``Layer5Result``. Suppressed under LIGHT and skipped for single-judge
  ensembles (where agreement is trivially 1.0).

### Per-judge attribution on ``sub_criteria_notes``

``layer5_ensemble._aggregate_dimension_scores`` now prefixes each
aggregated sub-criteria note with ``[judge_id]``, mirroring the style
already applied to ``feedback``. Audit trail traces every concern back
to the judge that raised it.

### New tests (+99 over 1332 baseline; 1431 + 3 xfailed final)

- ``tests/unit/evaluator/test_layer5_ensemble.py``:
  ``TestSingleJudgeEnsemble``, ``TestMixedDimensionCoverage``,
  ``TestSubCriteriaAttribution``, ``TestDimensionEmphasisThroughEnsemble``
  — plus rename of ``TestMinorityVeto`` → ``TestDissenterVeto``.
- ``tests/unit/evaluator/test_evaluator.py``:
  ``TestEnsembleEvaluatorIntegration`` exercising end-to-end event
  ordering (``EnsembleJudgeScored`` → ``DissenterVetoTriggered`` →
  ``EnsembleEvaluationComplete`` → ``EvaluationComplete``), veto event
  emission, ``RubricDimensionScored.weight`` tracking the ensemble's
  profile, and L5-veto-cannot-be-lifted-by-L4-process-quality.
- ``tests/unit/governance/test_policy.py``:
  ``test_low_agreement_emits_warn_under_standard``,
  ``test_low_agreement_escalates_under_deep``,
  ``test_low_agreement_suppressed_when_already_vetoed``,
  ``test_degraded_panel_warns_when_one_judge_fails``. Existing
  ``test_tier1_veto_*`` fixtures now use coherent ``Layer3Result``-bearing
  ``JudgeScore`` fixtures (via ``_judge_layer3`` helper) instead of the
  prior ``succeeded=True, layer3_result=None`` incoherence.

### Files touched

**Modified source:**
- ``src/keystone/pipeline/orchestrator.py`` (new judge panel,
  ``ensemble_panel_override`` parameter, resolver plumbing)
- ``src/keystone/evaluator/evaluator.py`` (DissenterVetoTriggered
  import + yield, docstring updates, feedback wording)
- ``src/keystone/evaluator/layer5_ensemble.py`` (docstring wording,
  sub_criteria_notes attribution)
- ``src/keystone/events.py`` (DissenterVetoTriggered class + union
  entry)
- ``src/keystone/models/evaluation.py`` (VetoEvent + Layer5Result
  docstring wording)
- ``src/keystone/governance/policy.py`` (gate rename, two new gates,
  ``_low_agreement_gate`` helper, TYPE_CHECKING for Layer5Result)
- ``src/keystone/contracts.py`` (docstring rename)

**Modified tests:**
- ``tests/unit/evaluator/test_layer5_ensemble.py`` (class rename + 4
  new test classes)
- ``tests/unit/evaluator/test_evaluator.py`` (4 new integration tests
  under ``TestEnsembleEvaluatorIntegration``)
- ``tests/unit/governance/test_policy.py`` (fixture helper
  ``_judge_layer3``, new low-agreement + degraded-panel tests, gate
  rename, coherent JudgeScore fixtures)

### Governance event stream (updated)

Per task, under STANDARD ensemble profile:
1. ``DeterministicCheckPassed`` (L1)
2. ``CitationGateResult`` (L2)
3. 2 × ``EnsembleJudgeScored`` (L5)
4. 0..M × ``DissenterVetoTriggered`` (L5)
5. 10 × ``RubricDimensionScored`` (L4)
6. ``EnsembleEvaluationComplete`` (L5)
7. ``ProcessTrajectoryScored`` (L4, optional)
8. ``EvaluationComplete`` (L4)

---

## Previous Session (kept for continuity)

Session: Slop detector — deterministic LLM-prose quality filter for L2

## What Changed (Slop detector session)

Added `keystone.quality`: a deterministic pattern-matcher that catches the
verbal tics LLMs over-use ("it's important to note that," "delve into,"
"leverage cutting-edge solutions," "a tapestry of synergies," etc.) before
the Evaluator scores a section. No LLM calls — pure regex with word-boundary
awareness, sub-millisecond on a ten-kilobyte brief. Baseline was 1311
unit+canary passing; running `pytest tests/unit/` now yields **1407
passing** (+96 new). Zero new ruff or mypy errors on touched files.

### New package `src/keystone/quality/`

- `patterns.py`: 300 curated patterns across 9 categories (FILLER, BUZZWORD,
  HEDGING, FALSE_TRANSITION, SUPERLATIVE, AI_TELL, LLM_TIC,
  CORPORATE_FILLER, WEAK_OPENER) with severities HIGH/MEDIUM/LOW. Each
  pattern is a `SlopPattern` (phrase, regex, category, severity, optional
  replacement, optional note). 183 HIGH, 105 MEDIUM, 12 LOW. Replacements
  are grammatically correct (`"delve into" → "examine"`, not
  `"delve" → "examine"` which would leave "examine into" stranded).
  `StrEnum` subclasses match the rest of the project's conventions.
- `slop_detector.py`: `SlopDetector`, `SlopMatch`, `SlopReport`. `detect()`
  returns all matches with line/col offsets and a count breakdown by
  severity and category. Overlap resolution keeps the longest match
  (so "it is important to note that" wins over inner "important"). `clean()`
  applies HIGH/MEDIUM replacements right-to-left (so offsets stay valid),
  then a `_tidy()` pass collapses double spaces, strips leading
  whitespace, removes space-before-punctuation, capitalizes sentence
  starts, and capitalizes the first letter after a markdown list marker.
  `LOW`-severity patterns are never auto-edited even when a replacement is
  configured — defense against aggressive edits.

### New event `SlopDetected`

- `src/keystone/events.py`: emitted from L2 per task when a section draft
  has at least one slop match. Carries `task_id`, `section_id`,
  `total_count`, `high_count`, `medium_count`, `low_count`,
  `top_categories` (sorted by match count, most first), and `cleaned`
  (True when auto-replacements changed the stored text). Folded into
  `AnyPipelineEvent`.

### Integration into L2 `ContentStructurer`

- `src/keystone/structuring/content_structuring.py`: constructor gains a
  `slop_detector: SlopDetector | None` parameter (default constructs one
  with `DEFAULT_PATTERNS`). After `render_task_section_text`, the raw
  text is handed to `_scrub_slop`, which runs `detect` + `clean` in one
  pass and returns `(cleaned_text, SlopDetected | None)`. The cleaned
  text is stored under `task_id` — the Evaluator grades the cleaned
  version. Event emission order per task is now
  `SectionDrafted -> SlopDetected? -> SprintContractProposed?`
  with each event conditional on whether there is anything to report.

### Tests

- `tests/unit/quality/test_slop_detector.py` (83 tests, 11 classes): one
  class per category, plus `TestPatternDatabase` (shape invariants),
  `TestWordBoundaries` (no false positives inside "paradigmatic",
  "developer", etc.), `TestClean` (deletion, substitution, idempotence,
  markdown list preservation, empty/no-match/all-slop), `TestSeverity
  Filtering` (`min_severity` + `at_or_above`), `TestReportShape`
  (offsets, line/col, ordering), and `TestConsultingIntegration` on a
  realistic consulting paragraph.
- `tests/unit/structuring/test_content_structuring.py`: new
  `TestSlopFiltering` class (4 tests): slop event emitted per task when
  the rendered section text has matches, stored section text is scrubbed,
  a clean finding produces no HIGH/MEDIUM event, and an injected
  `SlopDetector` replaces the default for testability.

### Files touched

**Added source:**
- `src/keystone/quality/__init__.py`
- `src/keystone/quality/patterns.py`
- `src/keystone/quality/slop_detector.py`

**Modified source:**
- `src/keystone/events.py` (`SlopDetected` + union entry)
- `src/keystone/structuring/content_structuring.py` (detector injection
  + `_scrub_slop` helper + event threading)

**Added tests:**
- `tests/unit/quality/__init__.py`
- `tests/unit/quality/test_slop_detector.py`

**Modified tests:**
- `tests/unit/structuring/test_content_structuring.py` (`TestSlopFiltering`
  + `_sloppy_finding` helper)

---

## Previous Session (kept for continuity)

Session: Evaluator Layer 5 — cross-model ensemble with minority veto

## What Changed (Layer 5 session)

Added Layer 5 to the Evaluator stack: a cross-model ensemble that wraps
Layer 3 when `ensemble_llms` is provided. PoLL (Panel of LLM Judges)
pattern addresses the SOS-Bench single-judge bias (ICLR 2025: holistic
LLM judging penalizes TONE 7× more than FACTUAL ERRORS, Play Favorites
self-scoring, 60–68% expert-agreement ceiling). Layer 5 runs 2–3
`ThreePassEvaluator` instances in parallel, aggregates per-dimension
scores by median, and applies a minority veto on Tier 1 dimensions:
if any judge scores any Tier 1 dimension below its floor, the
aggregated `Layer3Result.final_score` is forced to 0.0. Baseline was
1311 unit+canary passing; final is **1332 passing (+21 new tests)**.
3 xfailed unchanged. Ruff debt on touched files net-reduced (29→21
errors); mypy: zero new errors introduced (the 6 remaining on touched
files are all pre-existing).

### Architecture

- **Wrap point:** `ThreePassEvaluator.run()`. Each judge is a separate
  `ThreePassEvaluator` (so Phase 2 Observation Library scan applies
  per-judge when it lands). `Layer3RubricScorer` and
  `ThreePassEvaluator` now accept `judge_id: str | None = None`, which
  threads into `retry_llm_call` description strings so logs are
  judge-distinguishable (e.g. `rubric_intent_alignment[flagship]`).
- **Judge panel selection** (orchestrator `_resolve_ensemble_judges`):
  - LIGHT_TOUCH → `ensemble_llms=None`; L5 inert.
  - STANDARD → `[("flagship", Opus), ("fast", Haiku)]`. Excludes STANDARD
    tier because L1 agents generate with Sonnet → Play Favorites risk.
    Cost: 22 L3 LLM calls/task (vs 33).
  - DEEP → `[("flagship", Opus), ("standard", Sonnet), ("fast", Haiku)]`.
    All three tiers; Play Favorites risk mitigated by minority veto
    and `agreement_level` signal.
- **Aggregation math:**
  - Per dimension: `statistics.median(judge_scores)` for both Tier 1
    and Tier 2. Median is the observable aggregated score and is NOT
    overwritten when a Tier 1 veto fires (preserves audit signal).
  - Tier 1 veto: separate `any(judge_score < floor)` check, computed
    independently. If True for any Tier 1 dim → `tier1_vetoed=True`
    and `final_score = 0.0`.
  - Weighted total: `weighted_geometric_mean(median_scores, weights)`
    (reuses the existing function in `layer3_rubric.py`).
  - Gestalt: median of per-judge gestalts (post-aggregation of
    dimensional scores, preserving `Layer3Result.weighted_total` /
    `gestalt_adjustment` / `final_score` separation).
  - Agreement level: fraction of dimensions where
    `max_judge_score - min_judge_score <= 10` (matches gestalt clamp
    width). When only one judge scored a dimension (e.g. other bailed
    at Tier 1), that dimension counts as trivially concordant.
- **Graceful degradation:** `asyncio.gather(..., return_exceptions=True)`.
  Exceptions are captured as `JudgeScore(succeeded=False, error=...)`.
  Aggregation runs over survivors. If **all** judges fail,
  `Layer5Result.all_judges_failed=True` and the ensemble returns a zero
  `Layer3Result` — consistent with the existing Layer 3 exception path.

### Event stream

The ensemble path emits events in this order (per task):
1. `DeterministicCheckPassed` (L1)
2. `CitationGateResult` (L2)
3. N × `EnsembleJudgeScored` (layer `"L5"`, one per judge with per-judge
   scores + success flag)
4. 0..M × `MinorityVetoTriggered` (layer `"L5"`, one per vetoed Tier 1
   dimension, carries dissenting judge IDs + min_judge_score)
5. 10 × `RubricDimensionScored` (layer `"L4"`, aggregated-median scores
   — the existing `len(rubric_events) == 10` invariant in
   `test_evaluator.py` is preserved; per-judge detail is in the L5
   events above)
6. `EnsembleEvaluationComplete` (layer `"L5"`)
7. `ProcessTrajectoryScored` (L4, if `process_context` provided)
8. `EvaluationComplete` (L4)

### Governance gates

Two new gates in `record_evaluation_outcome`:
- **`l5_ensemble_tier1_veto`** (action `ESCALATE`): fires when
  `result.layer5_results.tier1_vetoed` and `not result.passed` and
  profile is not LIGHT. Always `ESCALATE` rather than `HALT` or
  `DEGRADE` because judge disagreement is ambiguous evidence, not a
  definitive rejection — it warrants human review regardless of profile.
- **`l5_ensemble_infrastructure_failure`** (action `WARN`): fires when
  `result.layer5_results.all_judges_failed` — distinguishes ensemble
  model-availability failure from content failure. Does not block.

Existing `l4_rubric_threshold` gate still fires in parallel for veto
failures (a veto produces `passed=False`), so operators get both
signals and can distinguish ensemble-driven rejections from
single-judge rejections.

### New models (src/keystone/models/evaluation.py)

- `JudgeScore(judge_id, judge_tier, layer3_result | None, succeeded,
  error | None)` — per-judge pass record
- `VetoEvent(dimension, floor_threshold, min_score,
  dissenting_judge_ids, judge_scores)` — per-dimension veto record
- `Layer5Result(judges_used, judge_scores, aggregated_dimension_scores,
  ensemble_weighted_total, ensemble_gestalt_adjustment,
  ensemble_final_score, tier1_vetoed, veto_events, agreement_level,
  all_judges_failed, failed_judge_ids)` — full ensemble output
- `EvaluationResult.layer5_results: Layer5Result | None` — additive,
  None for LIGHT_TOUCH or single-judge mode. No existing `EvaluationResult`
  construction breaks (field is optional with `None` default).

### Files touched

**New source:**
- `src/keystone/evaluator/layer5_ensemble.py` (EnsembleL3Evaluator +
  internal `_JudgeRun` dataclass + `_short_error` helper)

**Modified source:**
- `src/keystone/evaluator/evaluator.py` (ensemble_llms param,
  dispatch single-judge vs ensemble in `evaluate()`, emit new L5 events,
  propagate layer5_results through `_build_result`)
- `src/keystone/evaluator/three_pass.py` (judge_id param)
- `src/keystone/evaluator/layer3_rubric.py` (judge_id param + threaded
  into retry descriptions)
- `src/keystone/evaluator/__init__.py` (export EnsembleL3Evaluator)
- `src/keystone/models/evaluation.py` (JudgeScore, VetoEvent,
  Layer5Result, EvaluationResult.layer5_results)
- `src/keystone/models/__init__.py` (re-exports)
- `src/keystone/events.py` (EnsembleJudgeScored,
  MinorityVetoTriggered, EnsembleEvaluationComplete + union entries)
- `src/keystone/pipeline/orchestrator.py` (_resolve_ensemble_judges
  helper; pass `ensemble_llms` to Evaluator per intensity)
- `src/keystone/governance/policy.py` (l5_ensemble_tier1_veto,
  l5_ensemble_infrastructure_failure gates)
- `src/keystone/contracts.py` (EvaluatorContract.evaluate docstring)

**New tests:**
- `tests/unit/evaluator/test_layer5_ensemble.py` (18 tests: construction,
  aggregation math, minority veto, judge failure, gestalt aggregation,
  agreement level, retry description signature)

**Updated tests:**
- `tests/unit/governance/test_policy.py` (new `TestEnsembleGovernanceGates`
  class, 3 tests: tier1_veto escalates under STANDARD, tier1_veto
  skipped under LIGHT, all_judges_failed warns)

## Previous Session (kept for continuity)

Session: Audit remediation — integration-session findings fixed end to end

## What Changed (Audit remediation session)

An orchestrator audit of the prior integration session produced 7
recommended fixes and test-coverage gaps. All 7 are now landed.
Baseline was 1299 unit+canary passing; final is **1311 passing (+12
new tests)**. 3 xfailed unchanged. Lint and mypy debt on touched
files net-reduced (ruff 18→13 errors, mypy 18→15 errors); no new
errors introduced.

### Fix 1 — Bridge inter-agent isolation + Lane E as institutional memory

- `src/keystone/gateway/retrieval_bridge.py`: `_run_search` now
  injects `exclude_engagement_id = call.engagement_id` when the
  caller did not specify one. Inter-agent isolation is enforced
  structurally on the bridge path instead of relying on per-service
  `engagement_context` (which a `SearchQuery` object bypasses).
- `src/keystone/pipeline/orchestrator.py`: Lane E records are now
  ingested via `service.ingest_institutional(records)` (engagement_id
  =None). Lane E is pre-fetched reference material, not mid-research
  agent output, so it's meant to be visible everywhere. Institutional
  chunks pass the bridge's exclude filter; any future mid-research
  chunk tagged with the active engagement_id gets hidden from sibling
  agents automatically.
- New test `test_bridge_isolates_caller_engagement_by_default`: Lane E
  institutional passages remain visible while sibling-agent chunks
  tagged with the caller's engagement_id are hidden.

### Fix 2 — Docstring alignment for engagement_context semantics

- `src/keystone/pipeline/orchestrator.py`: Pipeline constructor
  docstring now describes what actually happens — Lane E ingested as
  institutional memory, inter-agent isolation enforced by the bridge.
- `src/keystone/retrieval/search/retrieval_service.py`:
  `engagement_context` docstring now spells out that the bridge
  bypasses the auto-apply by passing a `SearchQuery` object and
  enforces isolation itself, and that `engagement_context` mainly
  protects string-form callers.

### Fix 3 — `register_in_process_handler` docstring correction

- `src/keystone/gateway/mcp_gateway.py`: docstring previously claimed
  handlers receive "the raw parameters dict from the ToolCall" but
  the type and implementation pass the full `ToolCall`. Updated to
  match reality so readers don't design handlers that throw away
  `agent_id` / `engagement_id` / `client_id`.

### Fix 4 — Multi-run regression test

- `tests/unit/pipeline/test_orchestrator_retrieval.py`:
  `test_second_run_reregisters_fresh_service_and_events` runs
  `Pipeline.run()` twice on the same Pipeline instance with a
  retrieval factory. Asserts (a) a fresh `RetrievalService` is built
  per run, (b) handler objects registered on the gateway differ
  between runs (fresh closures), and (c) `SearchCompleted` /
  `ChunkIngested` events from run 1 don't leak into run 2.

### Fix 5 — Gateway authorizer rejects system-owned tools

- `src/keystone/gateway/auth.py`: `ToolAuthorizer.check` now rejects
  any `tool_name` in `SYSTEM_OWNED_TOOLS` regardless of
  `assigned_tools`. Defense-in-depth behind the template-level canary
  — if a template regression ever slipped `semantic_search` into an
  agent's assigned tools, this second gate still blocks the call.
- `tests/unit/gateway/test_in_process_dispatch.py`:
  - New `FAKE_IN_PROCESS_TOOL` for generic IN_PROCESS dispatch tests
    (so the system-owned gate doesn't interfere).
  - New `TestSystemOwnedToolGating` class: three tests proving
    `semantic_search` and `hybrid_search` are blocked at the
    authorizer even with `assigned_tools=[system_owned_tool]`, and a
    direct unit call on `ToolAuthorizer.check` confirming the rule.
  - Existing `TestInProcessDispatch` tests migrated off
    `semantic_search` onto `FAKE_IN_PROCESS_TOOL` — the generic
    dispatch mechanism is unchanged; only the tool used to exercise
    it differs.
  - `test_register_bridge_on_gateway` now invokes the handler
    directly (not through `gateway.execute`) because the gateway path
    is correctly blocked for system-owned tools.
- `tests/unit/pipeline/test_orchestrator_retrieval.py`:
  `test_search_events_are_yielded` mock now calls the handler
  directly, simulating the orchestrator's internal retrieval path
  rather than an agent path (the agent path is structurally
  impossible after Fix 5).

### Fix 6 — Layer 4 consumes SearchCompleted

- `src/keystone/evaluator/layer4_trajectory.py`:
  `_compute_deterministic_metrics` now reads `SearchCompleted` events
  from the trajectory. When present, the agent's
  `tool_utilization` formula extends both numerator and denominator
  with the retrieval tool names used (so the ratio stays ≤ 1.0 and
  agents that used internal retrieval register as using a tool). A
  synthetic `internal_corpus` label is added to the source-type set
  so `source_type_diversity` increases by one when any
  `SearchCompleted` events are present.
- The metrics dict now also surfaces `retrieval_calls` (integer count
  of SearchCompleted events) and `retrieval_tools_used` (sorted list
  of tool names) for observability.
- New `TestSearchCompletedInDeterministicMetrics` class in
  `tests/unit/evaluator/test_layer4_trajectory.py` — five tests
  covering: no search events → metrics unchanged; internal_corpus
  added to source types; tool_utilization shifts with retrieval;
  ratio cannot exceed 1.0; multiple repeats of the same retrieval
  tool deduplicate for utilization purposes.

### Fix 7 — Remaining coverage gaps

- `test_evidence_records_without_factory_are_silently_dropped`:
  canary for the documented behavior. Records present + factory
  absent → no `ChunkIngested`, no `SearchCompleted`, no handlers on
  the gateway. Would catch a future regression that tries to ingest
  without wiring a service.
- `test_lane_e_institutional_is_visible_to_agent_search`: end-to-end
  orchestrator test ingesting Lane E via the institutional path and
  verifying the passage is reachable through the bridge handler with
  the caller's engagement_id threaded as `exclude_engagement_id`.

### Files touched

**Modified source:**
- `src/keystone/gateway/retrieval_bridge.py` (structural isolation)
- `src/keystone/gateway/auth.py` (system-owned rejection)
- `src/keystone/gateway/mcp_gateway.py` (docstring + drop unused
  import + `raise ... from None` on the CircuitOpen propagation)
- `src/keystone/pipeline/orchestrator.py` (institutional Lane E
  ingest + docstring + drop unused `failed_count`)
- `src/keystone/retrieval/search/retrieval_service.py` (docstring)
- `src/keystone/evaluator/layer4_trajectory.py` (SearchCompleted
  consumption)

**Modified tests:**
- `tests/unit/gateway/test_in_process_dispatch.py` (FAKE_IN_PROCESS
  tool refactor + new TestSystemOwnedToolGating +
  test_bridge_isolates_caller_engagement_by_default +
  test_register_bridge_on_gateway updated for direct handler call)
- `tests/unit/pipeline/test_orchestrator_retrieval.py` (mock path
  migrated to handler + TestMultiRunRetrievalWiring class with three
  tests)
- `tests/unit/evaluator/test_layer4_trajectory.py` (new
  TestSearchCompletedInDeterministicMetrics class, 5 tests)

---

## Previous Session (kept for continuity)

Session: Pipeline integration — gateway IN_PROCESS dispatch + retrieval wiring + canary remediation

## What Changed (Integration session)

This session connected the retrieval stack to the orchestrator so the
pipeline actually uses what prior sessions built, added an
IN_PROCESS tool-dispatch path to the gateway, introduced a
production-wired gateway factory, and cleaned up the three
pre-existing canary failures. Baseline was 1257 unit passing; final
is **1299 unit+canary passing (+42 new tests)** with 3 xfailed
pre-existing (unchanged). Lint and mypy debt on touched files
decreased; no new errors introduced.

### Fix 1 — Gateway IN_PROCESS dispatch

- `MCPGateway.register_in_process_handler(tool_name, handler)` attaches
  a `Callable[[ToolCall], Awaitable[Any]]` handler for tools whose
  registry entry declares `TransportType.IN_PROCESS`. The handler
  receives the full `ToolCall` (agent_id, engagement_id, client_id,
  parameters) and returns a JSON-serializable payload.
- `MCPGateway.execute` now checks the registry's transport type; for
  IN_PROCESS it routes through the handler, otherwise through the
  MCP client. Authorization, rate-limiting, circuit-breaker, retry,
  and audit logging wrap both paths identically.
- An IN_PROCESS tool without a registered handler raises a clear
  `RuntimeError` at the first call so misconfigurations are visible
  immediately instead of falling through to a non-existent MCP server.

### Fix 2 — Production-wired gateway factory

- New `src/keystone/gateway/factory.py::build_mcp_gateway` assembles an
  `MCPGateway` with every component pre-wired:
  - `ToolRegistry` populated via `register_all_tools`
  - `InMemoryRateLimiter(build_default_rate_limits())` so EDGAR stays
    under SEC's 10 req/sec ceiling and retrieval gets its 50 req/sec
    budget without per-caller configuration
  - `ToolAuthorizer` bound to the populated registry
  - `AuditLogger()` with defaults
- Every component remains injectable for tests / alternate deployments.
- Exported as `keystone.gateway.build_mcp_gateway`.

### Fix 3 — Retrieval bridge

- New `src/keystone/gateway/retrieval_bridge.py` maps `semantic_search`
  and `hybrid_search` tool names to `RetrievalService.search`. It
  translates gateway parameter dicts into `SearchQuery` instances
  (including `exclude_engagement_id`) and serializes `RetrievalResult`
  back to a plain dict shaped so the gateway's citation extractor
  picks up URLs and titles.
- Handlers emit `SearchCompleted` via an optional event sink so every
  retrieval-tool call shows up in the pipeline event stream with
  `agent_id`, `engagement_id`, `tool_name`, query preview, result
  count, and latency.

### Fix 4 — Orchestrator retrieval wiring

- `Pipeline` constructor now accepts `retrieval_service_factory:
  Callable[[str], RetrievalService] | None`. The factory takes the
  freshly-assigned engagement_id and returns a service; the canonical
  use is `factory = lambda eid: build_retrieval_service(...,
  engagement_context=eid)` so agent searches auto-exclude current-
  engagement chunks.
- After L0 produces the engagement_id, the orchestrator:
  1. Calls the factory to build a per-run service.
  2. Registers `register_retrieval_handlers(gateway, service,
     event_sink=search_events.append)`.
  3. If `evidence_records` is non-empty, calls
     `service.ingest(records, engagement_id=eid)` and emits
     `ChunkIngested` summarizing the batch.
  4. After agents complete, folds collected `SearchCompleted` events
     into each agent's event trail (keyed on `agent_id`) so Layer 4
     sees internal-retrieval usage per agent.
- When no factory is injected, the pipeline runs exactly as before —
  retrieval wiring is opt-in so existing callers are unaffected.

### Fix 5 — Events

- `ChunkIngested` (layer `Retrieval`): per-batch summary with
  `artifact_count`, `chunk_count`, `chunks_created`, `chunks_updated`,
  `chunks_skipped`.
- `SearchCompleted` (layer `Retrieval`): per-call metadata with
  `agent_id`, `tool_name`, `query_preview` (truncated to 120 chars),
  `result_count`, `latency_ms`.
- Both added to `AnyPipelineEvent` union.

### Fix 6 — Pre-existing canary failures

Three canary tests were listed as pre-existing failures in TODO.md.
All three now pass:

- `test_failed_evaluation_blocks_rendering`: reworked to assert the
  governance-halt behaviour (fabricated citation triggers
  `l4_citation_fabrication` or `evaluation_coverage` halt flag with
  `EnforcementAction.HALT`). The renderer is never reached, so the
  fabricated content is trivially excluded — satisfying the original
  architectural claim more strongly than post-hoc filtering.
- `test_pipeline_fresh_components_per_run`: wraps `pipeline.run(...)`
  in `try/except RuntimeError` because zero findings trip the
  STANDARD-profile coverage gate (pass_ratio=0). Component freshness
  is captured before `run()` returns, so halt behaviour does not
  compromise the invariant under test.
- `test_spec_engine_no_agent_config_leak`: same halt-tolerant pattern
  as above; the `_agent_configs` assertion is about the fresh
  engine's initial state, which is set at `__init__` regardless of
  pipeline outcome.
- Same test now also asserts `first.content_structurer is not
  second.content_structurer`, covering the freshness-per-run invariant
  for the L2 component (TODO item #8).

### Fix 7 — Stale `_parse_score_json` import

`tests/integration/test_evaluator_live.py` imported `_parse_score_json`
from `keystone.evaluator.layer3_rubric`, which had been removed in
favour of the unified `safe_llm_json` / `ParseError` API in
`keystone.llm.parsing`. Import and all four test cases updated
accordingly; the garbage-input test now asserts `ParseError` instead
of the old empty-dict return value.

### Files touched

**New source:**
- `src/keystone/gateway/factory.py`
- `src/keystone/gateway/retrieval_bridge.py`

**Modified source:**
- `src/keystone/events.py` (added `ChunkIngested`, `SearchCompleted`,
  union entries)
- `src/keystone/gateway/__init__.py` (new re-exports)
- `src/keystone/gateway/mcp_gateway.py` (IN_PROCESS dispatch + handler
  registration)
- `src/keystone/pipeline/orchestrator.py` (retrieval wiring +
  `ChunkIngested` emission + `SearchCompleted` event fold-in)

**New tests:**
- `tests/unit/gateway/test_factory.py` (12 tests)
- `tests/unit/gateway/test_in_process_dispatch.py` (13 tests, split
  across dispatch / bridge / search-completed event groups)
- `tests/unit/pipeline/test_orchestrator_retrieval.py` (5 tests)

**Updated tests:**
- `tests/canary/test_architectural_guarantees.py` (three
  pre-existing failures fixed + content_structurer freshness assertion)
- `tests/integration/test_evaluator_live.py` (stale import)

## Previous Session (kept for continuity)

## What Changed (Isolation + audit hardening)

A fresh-eyes review concluded that the inter-agent isolation filter was
mechanically correct but architecturally weak (opt-in rather than
opt-out), and flagged three deep-mode audit cleanups. Three fixes
landed. Baseline was 1246 passing; final is **1257 passing (+11)**.
Zero new ruff or mypy errors on any touched file (pre-existing warnings
on legacy files unchanged).

### Fix 1 — Make ingest engagement_id required (structure over intent)

- `SemanticChunker.chunk(records, *, engagement_id)` is now a required
  keyword-only parameter. The former `= None` default is gone; callers
  must explicitly declare which engagement produced the chunks
  (``None`` is still accepted but must be named, making the
  institutional-memory path deliberate).
- `RetrievalService.ingest(records, *, engagement_id)` mirrors the
  same contract.
- New `RetrievalService.ingest_institutional(records)` wraps
  `ingest(..., engagement_id=None)` so cross-engagement ingest reads
  as an intent-named call instead of a naked `None`.
- Every test-suite caller was updated to pass `engagement_id=None`
  (institutional-memory semantics) or a real engagement id; three new
  regression tests pin the required-kwarg behaviour.

### Fix 2 — Make search isolation default-on via engagement_context

- `RetrievalService.__init__` gained an optional
  `engagement_context: str | None` parameter. When set, every
  string-form `search()` call auto-applies it as
  `exclude_engagement_id` so current-engagement chunks from sibling
  agents stay hidden by default. Aggregator / system callers that
  need full-corpus access construct the service without an
  `engagement_context`.
- `RetrievalService.engagement_context` is exposed as a read-only
  property for observability.
- A raw `SearchQuery` instance is honored literally: the service does
  **not** rewrite the caller's `exclude_engagement_id=None` into the
  service-level context. The docstring on `SearchQuery.exclude_
  engagement_id` records this: raw-None is read as an explicit
  opt-out, because a caller that builds their own query object is
  trusted to name their intent. This differs from the orchestrator's
  prompt, which described raw-None as opt-out without carving out the
  string-form-inherits semantic; in practice the distinction matters
  only when someone mixes SearchQuery-building with a context-bound
  service, and the safer default (string-form inherits, SearchQuery
  doesn't) preserves the "structure over intent" win without
  surprising callers who explicitly hand-built a query.
- Six new tests cover: property exposure, string-form inheritance,
  explicit kwarg override, raw SearchQuery opt-out, raw SearchQuery
  with explicit exclude, and the "no context = full corpus" path.

### Fix 3 — Deep-mode audit cleanup

- `AuditEntry.latency_ms` + `AuditLogger.log_call(..., latency_ms)`
  are now `float | None`. Structlog kwargs preserve `None` rather
  than rounding it. Deep-mode per-source entries set `latency_ms=None`
  (a single `claude -p` session cannot be disaggregated into
  per-fetch timings).
- New `ResearchAgent._audit_deep_session` emits one session-level
  audit entry per deep call:
  - **Success path** (end of `_execute_deep`): real elapsed
    `latency_ms`, `tool_name="deep_research:session"`, result =
    `{n_sources, n_claims}`.
  - **Failure path** (`execute()`'s except block before shallow
    fallback): real elapsed `latency_ms`, same `tool_name`, the
    original exception attached so compliance can see the failed
    attempt.
- `_audit_deep_source` dropped its dead `except AttributeError`
  branch — `MCPGateway.audit_logger` is a concrete property.
- Two new tests cover the success + failure session audit paths;
  existing per-source parity test updated to pin `latency_ms is None`
  on per-source entries and `>= 0.0` on the wrapping session entry.

### Files Touched

| File | Change |
|---|---|
| `src/keystone/retrieval/search/chunker.py` | `chunk(..., engagement_id=...)` required. |
| `src/keystone/retrieval/search/retrieval_service.py` | `ingest(..., engagement_id=...)` required; new `ingest_institutional()`; `__init__(..., engagement_context=...)` + `engagement_context` property; string-form search auto-applies context. |
| `src/keystone/retrieval/search/models.py` | `SearchQuery.exclude_engagement_id` docstring documents auto-apply + raw-None opt-out semantics. |
| `src/keystone/gateway/audit_log.py` | `AuditEntry.latency_ms` + `log_call` accept `float \| None`; structlog kwarg preserves None. |
| `src/keystone/research/research_agent.py` | `_audit_deep_source` passes `latency_ms=None`, dead `except AttributeError` dropped; new `_audit_deep_session` emits success + failure session entries; `execute()` captures `deep_start` and records the failed-session entry before shallow fallback. |
| `tests/unit/retrieval/search/test_chunker.py` | Updated every `chunker.chunk(records)` to pass `engagement_id=None`. |
| `tests/unit/retrieval/search/test_bm25_index.py` | Same propagation. |
| `tests/unit/retrieval/search/test_vector_store.py` | Same propagation. |
| `tests/unit/retrieval/search/test_hybrid_search.py` | Same propagation. |
| `tests/unit/retrieval/search/test_retrieval_service.py` | `service.ingest(records, engagement_id=None)` everywhere. |
| `tests/unit/retrieval/search/test_engagement_isolation.py` | Added `TestRequiredEngagementId` (3 tests) + `TestEngagementContext` (6 tests); renamed the former "defaults engagement_id to None" test to reflect the explicit-None semantic. |
| `tests/unit/research/test_research_agent_deep.py` | Updated per-source audit test to account for the new session entry; added success + failure session-audit tests. |

### Test delta

- 1246 → **1257** unit tests pass (+11). Breakdown:
  - +3 tests for required-engagement-id (chunker, ingest, institutional alias)
  - +6 tests for engagement_context behaviour
  - +2 tests for deep-session audit (success + failure)
- Zero new ruff errors on touched files; baseline count held at 14
  (pre-existing E501 on deep-research prompt text, TC001/TC003 on
  runtime-needed Pydantic model imports, F401 `dataclasses.field` in
  audit_log, I001 import ordering). Mypy strict clean on the retrieval
  package; `research_agent.py` retains its 12 pre-existing errors (all
  in legacy shallow-mode helpers, unrelated to this session).

### Design choices that differ from the orchestrator prompt

- **SearchQuery with raw-None is opt-out, but string-form inherits.**
  The prompt described only the opt-out semantic. I carved out the
  string-form-inherits case because otherwise the common path
  (`service.search("text")`) would still miss isolation when the
  service has a context. Callers that build their own `SearchQuery`
  are treated as naming their intent explicitly; string callers get
  the safe default. Net: the structure-over-intent win is actually
  achieved for the path agents will use.
- **`engagement_id` stayed `str | None` (not `str`).** The prompt
  did not mandate a type change. Keeping `None` as a legal value
  preserves the institutional-memory semantic; the "opt-in" problem
  the prompt targeted was the implicit `= None` *default*, which is
  now gone.

---

## Previous session: Comprehensive remediation — all deferred audit findings

## What Changed (Comprehensive remediation)

Eleven fixes from three separate audits landed in one pass. No item
was deferred. Baseline was 1212 unit tests passing; final is **1246
unit tests passing (+34)**. Zero new ruff or mypy errors on any
touched file (pre-existing warnings on legacy files unchanged).

### Retrieval-stack audit (7 fixes)

1. **PG connection errors wrapped as `VectorStoreError`.** Every
   asyncpg transport failure inside `PgVectorStore._get_pool`,
   `ensure_schema`, `upsert_chunks`, `search_similar`,
   `delete_by_artifact_id`, and `count` now surfaces as
   `VectorStoreError`, so `HybridSearcher`'s graceful-degradation
   catch block fires when PostgreSQL is unreachable. The
   store-docstring claim about `keystone_schema_version` was
   simultaneously removed (no such row exists).
2. **Docstring drift removed.** `vector_store.py` module docstring
   no longer references the fictional `keystone_schema_version` row.
3. **PG-unavailable degradation test.** Two new tests in
   `test_hybrid_search.py` point a live `PgVectorStore` at
   `postgresql://nobody@127.0.0.1:1/...`: one asserts
   `HybridSearcher.search` returns BM25-only results (no exception);
   the other pins that the raw asyncpg failure becomes a
   `VectorStoreError` so future refactors cannot regress.
4. **Canary test for system-owned exclusion.** New
   `test_system_owned_tools_never_appear_in_templates` in
   `tests/canary/test_architectural_guarantees.py` walks every seed
   template + every registry-loaded template and asserts the
   intersection with `SYSTEM_OWNED_TOOLS` is empty.
5. **`RetrievalService.search` docstring.** Explicitly documents the
   hybrid-stage `candidate_pool` / `top_k` rewrite so callers
   understand why the shape they pass in is internally cloned.
6. **Factory with dimension validation.** New
   `src/keystone/retrieval/search/factory.py` exposes
   `build_retrieval_service(app_config, retrieval_config)` with
   startup cross-checks:
   - `RetrievalConfig.embedding_dimension` must match the embedder's
     `dimension` attribute.
   - Vector store's `dimension` attribute must match the config.
   - When the embedder defaults to `voyage-finance-2`, the dimension
     must equal `VOYAGE_FINANCE_DIM` (1024).
   - Missing Voyage key raises `RetrievalFactoryError`; missing
     Cohere key falls back to `PassthroughReranker` instead of
     hard-failing.
   12 new tests cover every branch, including dimension mismatch.
7. **Inter-agent isolation scoping.** Implements the Founder Intent
   Doctrine "Inter-Agent Isolation" invariant + AgentLeak finding.
   - New `ChunkMetadata.engagement_id: str | None`.
   - New `SearchQuery.exclude_engagement_id: str | None`.
   - `PgVectorStore._build_filters` pushes the exclusion into a
     SQL `WHERE` clause (`engagement_id IS NULL OR <> $N`) so
     institutional memory always passes.
   - `InMemoryVectorStore._matches_filters` applies the same rule.
   - `HybridSearcher` threads the filter into the vector path AND
     post-filters the BM25 path (BM25 has no metadata filter).
   - `SemanticChunker.chunk(records, engagement_id=...)` tags every
     emitted chunk.
   - `RetrievalService.ingest(records, engagement_id=...)` and
     `RetrievalService.search(query, exclude_engagement_id=...)`
     expose the plumbing to callers.
   9 new tests covering chunker tagging, ingest propagation, PG
   filter-clause construction, and end-to-end exclusion semantics.

### Streams A + B deferred (2 fixes)

8. **Deep-mode audit-log parity.** `ResearchAgent._execute_deep`
   now writes an `AuditLogger.log_call` entry for every observed
   web source. `MCPGateway.audit_logger` was exposed as a public
   property so the research agent can reuse the gateway's logger
   without threading a new constructor argument. Tool names are
   tagged `deep_research:WebFetch` / `deep_research:WebSearch` so
   Layer 4 tool-utilization metrics and compliance review both see
   deep-mode activity. 2 new tests in
   `test_research_agent_deep.py`.
9. **Nested issue tree test.** `_collect_leaf_titles` now has
   regression coverage at depth 3 and depth 4, plus malformed-child
   resilience and `label`-alias fallback. 4 new tests in
   `test_content_structuring.py::TestCollectLeafTitlesNested`.

### Renderer + Layer 4 deferred (2 fixes)

10. **L4 process flags surfaced in rendered brief.** New
    `_render_process_assessment` helper in `markdown_renderer.py`
    produces a one-line bullet under each task's PASS/FAIL line:
    `Process Assessment: 72/100 -- Flags: LOW_DOMAIN_DIVERSITY,
    NO_MULTI_ROUND`. No flags -> `no process flags raised`. L4
    absent -> no bullet at all. Wired into both the outline and
    legacy rendering paths. 3 new tests.
11. **`ProcessTrajectoryScored` integration test.** New
    `TestProcessTrajectoryIntegration` in `test_evaluator.py` runs
    `Evaluator.evaluate(..., process_context=ctx)` end-to-end and
    asserts the event is emitted with the expected fields
    (`layer`, `task_id`, `process_quality_score`,
    `qualitative_score`, `source_count`, `round_count`,
    `tool_utilization`, `flag_count`) plus the negative case
    (no `process_context` -> no event, no `layer4_results`).

## Files Touched (Comprehensive remediation)

| File | Change |
|---|---|
| `src/keystone/retrieval/search/vector_store.py` | asyncpg error wrapping in every public method + `_get_pool`; docstring cleanup; `_build_filters` exclusion clause; `_matches_filters` exclusion rule; `_metadata_from_dict` rehydrates `engagement_id`. |
| `src/keystone/retrieval/search/retrieval_service.py` | `ingest(..., engagement_id=...)`, `search(..., exclude_engagement_id=...)`, expanded docstring for hybrid pool rewrite + isolation semantics, `_coerce_query` threads the exclusion. |
| `src/keystone/retrieval/search/hybrid_search.py` | Threads `exclude_engagement_id` into vector-store filters AND post-filters BM25 output. |
| `src/keystone/retrieval/search/chunker.py` | `chunk(..., engagement_id=...)` + stamps each `ChunkMetadata`. |
| `src/keystone/retrieval/search/models.py` | `ChunkMetadata.engagement_id` + `SearchQuery.exclude_engagement_id`. |
| `src/keystone/retrieval/search/factory.py` | **NEW** — `build_retrieval_service` with dimension cross-checks + `RetrievalFactoryError`. |
| `src/keystone/retrieval/search/__init__.py` | Export factory + error. |
| `src/keystone/gateway/mcp_gateway.py` | `audit_logger` property exposed. |
| `src/keystone/research/research_agent.py` | `_audit_deep_source` + `_deep_tool_name_for_url` so deep-mode fetches hit the gateway's AuditLogger. Docstring updated. |
| `src/keystone/pipeline/markdown_renderer.py` | `_render_process_assessment` helper wired into outline + legacy evaluation summary. |
| `tests/unit/retrieval/search/test_hybrid_search.py` | +2 PG-unavailable tests. |
| `tests/unit/retrieval/search/test_factory.py` | **NEW** — 12 factory tests. |
| `tests/unit/retrieval/search/test_engagement_isolation.py` | **NEW** — 9 isolation tests. |
| `tests/canary/test_architectural_guarantees.py` | +1 canary test for system-owned tool exclusion. |
| `tests/unit/research/test_research_agent_deep.py` | +2 deep-mode audit-log tests. |
| `tests/unit/structuring/test_content_structuring.py` | +4 `_collect_leaf_titles` nested-tree tests. |
| `tests/unit/pipeline/test_markdown_renderer.py` | +3 L4 render tests. |
| `tests/unit/evaluator/test_evaluator.py` | +2 `ProcessTrajectoryScored` integration tests. |

## Design Choices (Comprehensive remediation)

- **Isolation is a `None`-default scoping filter, not a new layer.**
  Existing institutional-memory ingest keeps working unchanged
  (both `ingest()` and `chunk()` default `engagement_id=None`).
  Callers opt in by passing the engagement ID explicitly; stored
  `None` values always pass the exclusion filter. No flag flip
  changes historical query behavior.
- **BM25 exclusion post-filter, not index-level filter.** rank_bm25
  has no metadata. Rather than rebuild the index per agent, we
  post-filter the BM25 top-k in `HybridSearcher.search`. BM25
  candidate pools are small (≤150), so the cost is negligible.
- **Factory injects over constructs.** `build_retrieval_service`
  accepts `embedder=`, `vector_store=`, `reranker=` overrides so
  tests and custom deployments reuse the cross-check guarantee
  without a separate test-mode factory.
- **Deep-mode audit parity, not deep-mode gateway routing.** We
  chose to restore observability (AuditLogger entries) instead of
  rerouting deep-mode tool calls through `MCPGateway.call_tool`
  — the latter requires wrapping provider-native tools and is
  still deferred to Phase 2. L4 process-trajectory can now count
  deep-mode tool utilization accurately because every web fetch
  registers as a tool call in the audit log.
- **Process-flag rendering is one line per task, not a subsection.**
  Reviewers see the flag list alongside the PASS/FAIL verdict,
  not buried under a separate heading. Mirrors the per-task
  feedback formatting already in place.

## Test delta

- 1212 → **1246** unit tests pass (+34).
- New tests: 12 factory + 9 engagement isolation + 2 hybrid PG-
  unreachable + 2 deep-mode audit + 4 nested-leaf-title + 3 L4-
  render + 2 L4 integration = 34 net new.
- Pre-existing canary failures (noted in TODO) remain as-is;
  the new canary test for system-owned tool exclusion is clean.

---

## What Changed (Retrieval stack)

Built the full retrieval search sub-package under
`src/keystone/retrieval/search/`. This is the system's long-term memory:
Lane E produces `EvidencePrepRecord` instances, this package ingests
them (chunk → embed → dual-index), and agents query it through the
gateway via `semantic_search` / `hybrid_search`.

Architecture is the standard modern-RAG pipeline:

    chunker → embedder → pgvector + BM25 → RRF fusion → Cohere rerank

Every stage is split behind a Protocol so tests use in-memory test
doubles and production wires real clients. Graceful degradation is
wired in: if Voyage or Cohere is down, the service still serves
results (BM25-only, or unranked RRF) rather than failing hard.

- **Infrastructure bring-up.** PostgreSQL 17 (`brew services start
  postgresql@17`) + pgvector 0.8.2 built from source against the
  homebrew PG 17 headers + `keystone` database with `CREATE
  EXTENSION vector`. The live test
  (`tests/unit/retrieval/search/test_vector_store.py::TestPgVectorStoreLive`)
  round-trips ingest → search → delete against the real DB; it skips
  gracefully when no DB is reachable.
- **Package layout.** `src/keystone/retrieval/search/` holds nine
  modules (`models.py`, `embeddings.py`, `chunker.py`,
  `vector_store.py`, `bm25_index.py`, `hybrid_search.py`,
  `reranker.py`, `query_router.py`, `retrieval_service.py`) plus
  `__init__.py` re-exports. Tests live under
  `tests/unit/retrieval/search/` (eight test files, 123 tests).
- **Pydantic v2 models.** `DocumentChunk`, `ChunkMetadata`,
  `SearchQuery`, `RetrievalResult`, `IngestResult`, `QueryRoute`,
  plus the `RetrievalSource` and `QueryClassification` enums.
  Metadata is frozen and carries the full provenance chain
  (artifact_id, canonical_url, content_hash, locator, source_family,
  parse_confidence) preserved from Lane E.
- **Embeddings.** `EmbeddingClient` Protocol + `VoyageEmbeddingClient`
  (voyage-finance-2, 1024-dim, batched at 128/call, `query` vs
  `document` input_type) + `InMemoryEmbeddingClient` for tests
  (SHA-256 derived, unit-normed, deterministic). Errors wrap into
  `EmbeddingError`/`EmbeddingDimensionError` so callers can decide
  between retry and fallback.
- **Chunker.** `SemanticChunker` groups `EvidencePrepRecord` by
  artifact, respects passage boundaries (never splits a passage
  mid-sentence unless it exceeds `max_tokens`), and applies the
  Anthropic contextual-retrieval preamble (`Source: ... | Section:
  A > B | Page N`) to each chunk's `content` while preserving the
  unprefixed text in `raw_text`. Chunk IDs are deterministic
  `{artifact_id}:{seq:04d}` so re-ingest is idempotent.
- **Vector store.** `VectorStore` Protocol + `PgVectorStore` (asyncpg
  pool, HNSW index on `vector_cosine_ops`, JSONB metadata column,
  cosine-distance search with `<=>`) + `InMemoryVectorStore` for
  tests. Schema bootstrap is idempotent; filters support
  `artifact_id` and `source_family`.
- **BM25.** `BM25Index` Protocol + `InMemoryBM25Index` (rank_bm25
  BM25Okapi, lowercased-word tokenizer). Rebuilt on each ingest so
  it stays in sync with the vector store.
- **Hybrid search.** `HybridSearcher` runs both retrievers in parallel
  via `asyncio.gather`, then applies Reciprocal Rank Fusion with the
  standard `k=60` constant: `score(d) = Σ 1/(k + rank_i(d))`.
  Weights per retriever are configurable via `HybridSearchConfig`;
  zero-weighting either side skips its fetch entirely. A dead vector
  store or embedder drops the vector path without crashing the
  search.
- **Reranker.** `RerankerClient` Protocol + `CohereReranker`
  (rerank-v3.5 via `cohere.AsyncClientV2`, preserves chunk identity)
  + `PassthroughReranker` for tests and the graceful-degradation
  path. The retrieval service catches `RerankerError` and falls back
  to the pre-rerank RRF list.
- **Query router.** `RuleBasedQueryRouter` classifies queries as
  `QUANTITATIVE` / `QUALITATIVE` / `HYBRID` from regex signals
  (currency, percent, fiscal year, metric term, explanatory verbs,
  qualitative terms). Confidence scales 0.5 / 0.6 / 0.9 with signal
  count. LLM-backed router can replace this without touching
  callers.
- **RetrievalService.** Top-level orchestrator. `ingest()` wipes the
  artifact from both indexes first, then writes the embedded chunks
  atomically. `search()` runs hybrid + reranker; a reranker failure
  or empty result falls back to the hybrid list. `classify()`
  delegates to the router.
- **Gateway registration.** Added `TransportType.IN_PROCESS` to
  `ToolEntry`; registered `semantic_search` and `hybrid_search` in
  `TOOL_CONFIGS` with `server_name="keystone-retrieval"`, shared
  server-level rate limit (50 req/sec default),
  `config["system_owned"]=True`. Both tools live in a new
  `RETRIEVAL_TOOLS` / `SYSTEM_OWNED_TOOLS` list in `tool_names.py`
  and are intentionally absent from `SEARCH_TOOLS`, `DEFAULT_TOOLS`,
  and `FINANCIAL_TOOLS` — the Specification Engine must not
  auto-assign them. Tool count is now **11** across **8** unique
  upstream servers; `tests/unit/test_tool_registry.py` and
  `tests/unit/gateway/test_tool_registry.py` assertions updated.
- **Config.** New `RetrievalConfig` model in
  `src/keystone/models/config.py` (database_url,
  embedding_dimension, voyage_model, cohere_rerank_model,
  chunk_size_tokens, chunk_overlap_tokens, hybrid_top_k_candidates,
  rerank_top_k, rrf_k). `AppConfig` gained `keystone_database_url`,
  `voyage_api_key`, `cohere_api_key` fields for env-loaded
  settings.
- **pyproject.toml.** New `retrieval-search` optional extra
  (asyncpg + pgvector + voyageai + cohere + rank-bm25) and combined
  `retrieval` extra now pulls in all three retrieval groups.
  Added `voyageai.*`, `asyncpg.*`, `rank_bm25.*` to the mypy
  `ignore_missing_imports` override list.

Test delta: **1212 passed** (was 1089). +123 new search tests
distributed across `test_models.py` (13), `test_chunker.py` (13),
`test_embeddings.py` (13), `test_vector_store.py` (16 — including
3 live-DB tests), `test_bm25_index.py` (12),
`test_hybrid_search.py` (10), `test_reranker.py` (11),
`test_query_router.py` (11), `test_retrieval_service.py` (12),
`test_gateway_registration.py` (9). Plus 4 updated assertions in
the two tool-registry test files (11 tools / 8 servers). Zero new
ruff errors on touched files; `mypy` strict clean on every new
source file (14 source files, 0 errors under strict). 3 live
pgvector tests run against the real DB and pass.

## New files (Retrieval stack)

| File | Purpose |
|---|---|
| `src/keystone/retrieval/search/__init__.py` | Package re-exports. |
| `src/keystone/retrieval/search/models.py` | `DocumentChunk`, `ChunkMetadata`, `SearchQuery`, `RetrievalResult`, `IngestResult`, `QueryRoute`, `RetrievalSource`/`QueryClassification` enums. |
| `src/keystone/retrieval/search/embeddings.py` | `EmbeddingClient` Protocol, `VoyageEmbeddingClient`, `InMemoryEmbeddingClient`, `EmbeddingError`/`EmbeddingDimensionError`. |
| `src/keystone/retrieval/search/chunker.py` | `SemanticChunker`, `count_tokens`. Passage-aware chunking + contextual preamble. |
| `src/keystone/retrieval/search/vector_store.py` | `VectorStore` Protocol, `PgVectorStore` (asyncpg + HNSW + JSONB), `InMemoryVectorStore`, `VectorStoreError`. |
| `src/keystone/retrieval/search/bm25_index.py` | `BM25Index` Protocol, `InMemoryBM25Index` (rank_bm25), `tokenize`. |
| `src/keystone/retrieval/search/hybrid_search.py` | `HybridSearcher`, `HybridSearchConfig`, `DEFAULT_RRF_K=60`. |
| `src/keystone/retrieval/search/reranker.py` | `RerankerClient` Protocol, `CohereReranker` (rerank-v3.5), `PassthroughReranker`, `RerankerError`. |
| `src/keystone/retrieval/search/query_router.py` | `QueryRouter` Protocol, `RuleBasedQueryRouter`. |
| `src/keystone/retrieval/search/retrieval_service.py` | `RetrievalService` orchestration entry point. |
| `tests/unit/retrieval/search/` | 8 test files + conftest.py + 123 tests. |

## Changed files (Retrieval stack)

| File | Change |
|---|---|
| `pyproject.toml` | New `retrieval-search` optional extra (asyncpg + pgvector + voyageai + cohere + rank-bm25). Combined `retrieval` extra now pulls all three retrieval groups. Added voyageai/asyncpg/rank_bm25 to mypy override list. Removed stale "add back later" comments for deps that just got added. |
| `src/keystone/models/config.py` | Added `RetrievalConfig` (database_url, embedding_dimension, voyage_model, cohere_rerank_model, chunk_size_tokens, chunk_overlap_tokens, hybrid_top_k_candidates, rerank_top_k, rrf_k). Extended `AppConfig` with `keystone_database_url`, `voyage_api_key`, `cohere_api_key`. |
| `src/keystone/models/__init__.py` | Exports `RetrievalConfig`. |
| `src/keystone/tool_names.py` | Added `SEMANTIC_SEARCH`/`HYBRID_SEARCH` enum members + `RETRIEVAL_TOOLS`/`SYSTEM_OWNED_TOOLS` semantic groupings. |
| `src/keystone/gateway/tool_registry.py` | New `TransportType.IN_PROCESS` variant for system-owned tools. |
| `src/keystone/gateway/servers.py` | `RETRIEVAL_SERVER_NAME`/`RETRIEVAL_MAX_REQ_PER_SEC` constants, two new `TOOL_CONFIGS` entries, shared server-level rate limit (50/sec). |
| `tests/unit/test_tool_registry.py`, `tests/unit/gateway/test_tool_registry.py` | Updated assertions: `len(TOOL_CONFIGS)==11`, `unique_server_count==8`. |

## Design Choices (Retrieval stack)

- **pgvector over a dedicated vector DB.** The retrieval engine sits
  inside the Keystone process and already requires PostgreSQL for
  HITL gates. A second service (Pinecone / Weaviate / Qdrant)
  doubles the deployment surface and the failure modes. pgvector is
  native to PG, supports HNSW indexes, and `<=>` is just another
  index type — one DB to back up, one connection pool to manage.
- **voyage-finance-2 as default embedder.** FinMTEB shows ~49%
  improvement over general-purpose embeddings on finance corpora.
  The dimension (1024) matches the pgvector default schema so the
  index can be rebuilt in place if a future model shares the
  dimension. Swapping to another provider only requires a new
  `EmbeddingClient` implementation.
- **Hybrid + RRF, not linear fusion.** Cosine similarity lives on
  [-1, 1] and BM25 is unbounded, so linear combinations drift as
  the corpus grows. Reciprocal Rank Fusion only looks at ranks,
  which makes it robust across heterogeneous retrievers. `k=60` is
  the literature's canonical choice.
- **Chunks carry full provenance, not just text.** Every retrieval
  result traces back to `(artifact_id, content_hash, locator)` so
  citations can be verified against Lane H's stored bytes without
  re-parsing. `record_ids` on `ChunkMetadata` preserves the link to
  Lane E's `EvidencePrepRecord.record_id` when multiple passages
  fold into one chunk.
- **Contextual retrieval preamble baked into `content`, original
  text preserved in `raw_text`.** Citations quote `raw_text`
  verbatim; embedding and BM25 both index `content` which includes
  the preamble. Anthropic's benchmark showed a 67% reduction in
  retrieval failures from this single change.
- **Reranker is a soft dependency.** When Cohere is unavailable the
  retrieval service logs and falls back to the RRF-ordered list.
  Search traffic stays alive at degraded quality instead of
  hard-failing.
- **System-owned tools, not task-assignable.** `semantic_search` and
  `hybrid_search` never appear in `DEFAULT_TOOLS`/`SEARCH_TOOLS`/
  `FINANCIAL_TOOLS`. They're invoked by the gateway / orchestrator
  through the retrieval service; the Specification Engine must not
  hand them out as agent tools. `SYSTEM_OWNED_TOOLS` in
  `tool_names.py` is the single source of truth for the exclusion
  list.
- **Delete-then-upsert on re-ingest.** The ingest path wipes the
  artifact's chunks from both indexes before inserting the new
  ones, so the vector store and BM25 index never disagree about
  what chunks exist for an artifact. This also keeps chunk_ids
  stable: `{artifact_id}:{seq:04d}` is deterministic, so repeat
  ingests produce the same IDs and idempotent overwrites.

## Key Commands

```bash
# One-time infrastructure (PostgreSQL + pgvector):
brew services start postgresql@17
export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"
# pgvector was built + installed from /tmp/pgvector against PG 17
createdb keystone
psql keystone -c 'CREATE EXTENSION IF NOT EXISTS vector;'

# Install Python deps:
source .venv/bin/activate
pip install -e ".[dev,retrieval-search]"

# Test matrix:
pytest tests/unit/ -q                                        # 1212 tests
pytest tests/unit/retrieval/search/ -q                       # 123 search tests
pytest tests/unit/retrieval/search/test_vector_store.py \
    ::TestPgVectorStoreLive -v                              # 3 live-DB tests

# Lint + type:
ruff check src/keystone/retrieval/search/ tests/unit/retrieval/search/
mypy src/keystone/retrieval/search/                          # 0 errors
```

## Environment

- `KEYSTONE_DATABASE_URL` (default `postgresql://localhost/keystone`)
- `VOYAGE_API_KEY` — for VoyageEmbeddingClient
- `COHERE_API_KEY` — for CohereReranker
- `KEYSTONE_TEST_DATABASE_URL` — optional override for live-DB tests

## Integration Shape (Retrieval stack)

```python
from keystone.retrieval.search import (
    RetrievalService, SemanticChunker, VoyageEmbeddingClient,
    PgVectorStore, InMemoryBM25Index, CohereReranker,
    RuleBasedQueryRouter,
)

service = RetrievalService(
    chunker=SemanticChunker(target_tokens=384, max_tokens=512),
    embedder=VoyageEmbeddingClient(api_key=cfg.voyage_api_key),
    vector_store=PgVectorStore(dsn=cfg.database_url, dimension=1024),
    bm25_index=InMemoryBM25Index(),
    reranker=CohereReranker(api_key=cfg.cohere_api_key),
    router=RuleBasedQueryRouter(),
)
await service.ensure_ready()
await service.ingest(evidence_records)
results = await service.search("How did cloud revenue grow in FY2024?", top_k=20)
```

## Gotchas (Retrieval stack)

- **pgvector requires native compilation.** The extension binary was
  built from source against PostgreSQL 17's dev headers (`make
  PG_CONFIG=/opt/homebrew/opt/postgresql@17/bin/pg_config install`).
  Upgrading PG will require rebuilding pgvector.
- **BM25 scores drop to zero on tiny corpora.** rank_bm25's IDF
  formula `log(N - n + 0.5) - log(n + 0.5)` is negative when
  N=1 or 2 and the term appears in every document. Our
  implementation drops non-positive scores so hybrid search doesn't
  get polluted by noise, but this means standalone BM25 tests need
  multi-document corpora to behave sensibly. See
  `test_bm25_index.py::test_add_chunks_replaces_same_id` for the
  padding pattern.
- **Voyage SDK's `Client` isn't in `__all__`.** Mypy with
  `implicit_reexport=False` flags `voyageai.Client`. The
  `VoyageEmbeddingClient._build_default_client` casts through
  `Any` to silence it without blanket `type: ignore`.
- **SearchQuery enforces `candidate_pool >= top_k`.** Callers that
  want just 5 results still need to pass `candidate_pool>=5`. The
  retrieval service transparently bumps the pool up to the hybrid
  minimum before running the search.
- **Reranker failures are silent (logged + fallback).** Downstream
  callers cannot tell whether they got the reranked top-k or the
  pre-rerank hybrid list. If a caller needs to know, inspect
  `result.source` — `RERANKED` vs `HYBRID`.

## What Did Not Change (Retrieval stack)

- No modifications to Lane E parsers, the orchestrator, the
  evaluator, deliberation, content structurer, or renderer. The
  retrieval service is standalone; orchestrator integration
  (pipe normalizer output into `service.ingest(...)` and expose
  `service.search(...)` to agents via the gateway) is a follow-up
  session.
- No changes to the MCP gateway's client dispatch layer. The
  `IN_PROCESS` transport type is declarative only — wiring the
  retrieval service to actually handle `call_tool("semantic_search",
  ...)` dispatch is a follow-up, once the real MCP client phase
  lands.

---

## Previous session: Evaluator Layer 4 — Process Trajectory Evaluation

### What Changed (Layer 4)

Added a fourth evaluation layer that scores the RESEARCH PROCESS, not
the output text. Layers 1-3 can be fooled by a lazy or narrow research
process that happens to produce plausible-sounding prose; Layer 4 reads
the agent's pipeline event trail and surfaces that pattern.

- **New package entry:** `src/keystone/evaluator/layer4_trajectory.py`
  holds the `Layer4Evaluator` class, a frozen `ProcessContext`
  dataclass, deterministic metric extraction (source count, unique
  domains, source-type diversity, tool utilization from `SourceFound`
  events, synthesis round count from `FindingSynthesized` events, issue
  tree sibling coverage, citation quality distribution from the task
  manifest), and deterministic flag computation.
- **New model:** `Layer4Result` in `src/keystone/models/evaluation.py`
  with deterministic metrics, LLM assessment (qualitative score +
  rationale + missed inquiries + skepticism assessment), a composite
  `process_quality_score` (0-100), and a `process_flags` list. Values
  come from the new `ProcessFlag` enum
  (`single_source_type`, `single_domain`, `low_domain_diversity`,
  `no_multi_round`, `low_tool_diversity`, `low_source_count`,
  `coverage_gap`, `no_high_confidence_citations`,
  `missing_anti_confirmatory_evidence`, `narrow_inquiry`).
- **Wire into the Evaluator:** `evaluate()` now accepts an optional
  `process_context`. When provided and Layers 1-3 pass, Layer 4 runs
  after Layer 3; the overall score becomes the weighted geometric mean
  of the L3 final score and the L4 process score (default 80% L3,
  20% L4, tunable via `Evaluator(layer3_weight=...)`). A L1/L2 failure
  or a Tier 1 rubric floor failure still short-circuits — Layer 4
  never lifts a failing content evaluation.
- **New event:** `ProcessTrajectoryScored` (layer `L4`) carries
  `process_quality_score`, `qualitative_score`, source / domain /
  round counts, tool utilization, and `flag_count` for observability.
- **New prompt:** `src/keystone/evaluator/prompts/process_trajectory.md`
  asks a senior research methodologist to assess strategy soundness,
  missed inquiries, anti-confirmatory framing, and source-quality
  appropriateness for the claim types. Output is a strict JSON schema
  with a `qualitative_score`, rationale, missed-inquiry list,
  skepticism assessment, and an `additional_flags` array.
- **Orchestrator plumbing:** `run_with_events` now accumulates each
  agent's event trail into `events_by_agent`, maps `task.id` → the
  `AgentInstance` that handled it, and builds a `ProcessContext` per
  task before calling `evaluator.evaluate(..., process_context=ctx)`.
  When an agent or events are missing, `process_context` is `None` and
  Layer 4 is skipped for that task.
- **Contract:** `EvaluatorContract.evaluate` in `contracts.py` gained
  the `process_context: ProcessContext | None = None` parameter.

Test delta: **1089 passed** (was 1058). 31 new Layer 4 unit tests cover
helpers (`_extract_domain`, `_find_sibling_branch_ids`,
`_blend_layer3_layer4`), deterministic metric extraction from event
trails, each flag rule (good process / narrow research / single-round /
single-domain / low tool diversity / coverage gap / no HIGH-confidence
citations), score blending (critical vs warning penalties, floors,
merge dedup), and the full `Layer4Evaluator` happy path + LLM failure
fallback + unknown-flag silencing. Zero new ruff errors on touched
files. mypy strict clean on `evaluator.py`, `layer4_trajectory.py`,
`events.py`, `models/evaluation.py`.

## New files (Layer 4)

| File | Purpose |
|---|---|
| `src/keystone/evaluator/layer4_trajectory.py` | `Layer4Evaluator`, `ProcessContext`, deterministic metric + flag extraction. |
| `src/keystone/evaluator/prompts/process_trajectory.md` | LLM prompt for strategy / missed inquiries / skepticism assessment. |
| `tests/unit/evaluator/test_layer4_trajectory.py` | 31 tests across helpers, metrics, flags, scoring, and the full evaluator. |

## Changed files (Layer 4)

| File | Change |
|---|---|
| `src/keystone/models/evaluation.py` | Added `ProcessFlag` (StrEnum), `Layer4Result` (deterministic metrics + LLM assessment + `process_quality_score` + flags), and `layer4_results` on `EvaluationResult`. |
| `src/keystone/events.py` | Added `ProcessTrajectoryScored` and extended `AnyPipelineEvent` union. |
| `src/keystone/evaluator/evaluator.py` | Added `layer3_weight` constructor param + `DEFAULT_LAYER3_WEIGHT = 0.8`, optional `process_context` parameter on `evaluate`, Layer 4 step, `_blend_layer3_layer4`, composite score wiring through `_build_result` (new `l4` + `composite_score` args, L4-aware feedback string, emits `Layer4Result` into `EvaluationResult.layer4_results`). |
| `src/keystone/evaluator/__init__.py` | Exports `Layer4Evaluator` and `ProcessContext`. |
| `src/keystone/contracts.py` | `EvaluatorContract.evaluate` signature now includes `process_context: ProcessContext | None = None`. |
| `src/keystone/pipeline/orchestrator.py` | Accumulates per-agent event trail into `events_by_agent`, builds `agent_by_task`, calls `_build_process_context(task, agent_by_task, events_by_agent, spec)` before each evaluator invocation, and passes `process_context=...` through. |

## Design Choices (Layer 4)

- **Deterministic metrics + one LLM call.** Flag rules run entirely
  off event data and the citation manifest — no LLM judgment needed
  for `single_domain`, `no_multi_round`, `low_tool_diversity`, etc.
  The LLM contributes the qualitative score, the missed-inquiries
  list, and the skepticism assessment, each tied to the actual task
  and the sampled source list so the review is subject-specific. The
  prompt explicitly forbids restating the deterministic metrics.
- **Weighted geometric mean, not arithmetic.** `_blend_layer3_layer4`
  uses `exp(w_L3 * log(L3) + w_L4 * log(L4))` so a very weak L4
  drags the composite below the arithmetic mean. An L4 score near
  zero lowers a strong L3 into the 10-20 range — reviewers get a
  loud signal that the process was insufficient, even when the prose
  reads well.
- **L4 never lifts a failing L1/L2/L3.** The composite replaces the
  L3 final score only when Layer 4 actually ran. A Tier 1 floor
  failure returns final_score=0 before Layer 4 is touched, and L2
  fabrication short-circuits at Layer 2. The pass/fail threshold is
  still checked against the composite (default 60).
- **`ProcessContext` is frozen, narrow, and optional.** A dataclass
  bundling `agent_id`, the `ResearchTask`, the `AgentInstance`, the
  agent's events (pre-filtered by the orchestrator), and the
  engagement's issue tree. Frozen to keep Layer 4 from mutating
  shared state. `None` disables L4 rather than crashing, so tests
  and downstream callers can opt in gradually.
- **Tool utilization reads `SourceFound.source_type` first, then
  falls back to `tool://` URL hosts.** Deep-mode agents emit
  `source_type="deep_research"` (a non-tool label); shallow-mode
  agents emit the tool name as `source_type` and also encode it in
  the `tool://` URL scheme. The extractor handles both.
- **Issue-tree coverage is per-task by necessity.** The evaluator
  runs one task at a time, so `issue_tree_branches_covered` is
  simply `[task.issue_tree_branch_id]` if set and the sibling branch
  ids surface as `issue_tree_branches_missed` for the LLM to weigh.
  Engagement-level coverage enforcement stays in governance, not L4.

## Key Commands

```bash
source .venv/bin/activate
pytest tests/unit/ -q                                          # 1089 tests
pytest tests/unit/evaluator/test_layer4_trajectory.py -q       # 31 L4 tests
ruff check <new paths>                                         # clean
mypy src/keystone/evaluator/evaluator.py \
     src/keystone/evaluator/layer4_trajectory.py \
     src/keystone/models/evaluation.py \
     src/keystone/events.py                                    # clean
```

## Integration Shape (Layer 4)

```python
from keystone.evaluator import Evaluator, ProcessContext

# Build ProcessContext from the orchestrator's per-task event trail
context = ProcessContext(
    agent_id=agent.agent_id,
    task=task,
    agent=agent,
    events=events_by_agent[agent.agent_id],
    issue_tree=spec.issue_tree,
)

# Optional: tune composite weighting (default 80/20)
evaluator = Evaluator(llm=flagship_llm, layer3_weight=0.8)

async for event in evaluator.evaluate(
    output_text, contract, task, manifest, spec, process_context=context,
):
    ...  # ProcessTrajectoryScored and EvaluationComplete now carry composite
result = await evaluator.get_result()
assert result.layer4_results is not None
assert result.overall_score <= result.layer3_results.final_score  # L4 lowers or equals
```

## Gotchas (Layer 4)

- **Layer 4 is skipped without a `ProcessContext`.** Backwards
  compatible: callers that don't supply `process_context` get the
  old L3-only composite. Tests that only care about Layers 1-3 need
  no changes.
- **`_blend_layer3_layer4` floors each side at 0.01 before
  logarithm.** A hard-zero L4 score produces a composite near
  `L3^0.8 * 0.01^0.2 ≈ L3^0.8 * 0.4`, not zero. This is intentional
  — the composite should be very low, not nonexistent.
- **Unknown flags from the LLM are dropped silently** (logged at
  debug). Expand `ProcessFlag` if the prompt's vocabulary grows.
- **Tool utilization penalizes more than mere underuse.** A task
  with 3 assigned tools but only 1 exercised scores ≤0.34 and
  triggers `low_tool_diversity`. Tune `_LOW_TOOL_UTILIZATION_MAX`
  if deep-mode agents with a single `deep_research` "tool" flag
  false-positive — in practice deep mode emits `source_type` that
  doesn't match any assigned tool name, so this is a genuine signal
  not a bug.
- **`passed` now keys off the composite.** Downstream code that
  keyed off `overall_score` is unchanged; code that keyed off
  `layer3_results.final_score` for "did the content pass?" should
  keep doing that.

## What Did Not Change (Layer 4)

- No changes to Layer 1 (deterministic), Layer 2 (citation gate), or
  Layer 3 (rubric scoring). All three remain byte-for-byte identical.
- No changes to the CitationProcessor, Deliberation, Content
  Structurer, Specification Engine, or Renderer.
- No changes to the HITL gate, governance policy, or tool registry.

---

## Previous session: Outline-driven rendering — L3 renderer consumes full StructuredOutline

## What Changed (Outline-driven rendering)

The renderer previously consumed only the `FRAMEWORK_ANALYSIS` facet of the
L2 outline and rebuilt every other section from the raw `ConfidenceMap` +
`StructuredFinding` inputs. L2 was paying to build 9 section types and the
renderer was throwing 8 of them away. `MarkdownRenderer` has been rewritten
to traverse `StructuredOutline.sections` end-to-end.

**Section layout (outline-driven path):**

1. Title + engagement metadata
2. **Executive Summary** — confidence distribution line, high-confidence
   headlines with `[HIGH]` badges and inline `[N]` citation refs,
   uncovered-branch caveat
3. **Analytical Framework** — renders from the `FRAMEWORK_ANALYSIS`
   section's items when L2 populated it; falls back to `outline.frameworks`
   for callers that construct outlines without running the full structurer
4. **Key Findings** — one `### subsection` per `BRANCH` section (titled
   by the issue-tree branch); each claim shows tier + confidence badge
   (`[HIGH, 85%]`), inline citations, `Evidence:`, `Caveats:`, and optional
   analytical `note`
5. **Areas of Uncertainty** — subsections for `MODERATE (60-80%)`,
   `WEAK (50-60%)`, `CONTESTED (<50%)`; each carries an italic preamble
   and stamps claims with the tier badge
6. **Evidence Gaps** — `GAPS` (what we looked for but couldn't find),
   `INSUFFICIENT` (evidence too sparse to assess, `[INSUFFICIENT]` badge),
   plus an `Uncovered Issue-Tree Branches` subsection when
   `outline.uncovered_branch_ids` is non-empty
7. **Absence Report** — `ABSENCE` items; the section is omitted entirely
   when no absence items exist
8. **Evaluation Summary** — summary table (tasks, pass rate, avg score)
   plus a per-dimension average table when any `Layer3Result` is present;
   then per-task PASS/FAIL line (renamed from "Quality Assessment")
9. **Sources** — numbered list; number 1. in Sources == `[1]` inline

**Legacy (`outline=None`) path preserved.** Every pre-existing renderer
test keeps passing with the original output format; only the outline path
switches to the new structure.

**Inline citations.** `MarkdownRenderer._build_citation_index(manifest)`
assigns each citation a 1-based index in manifest order.
`_format_inline_citations([...], index)` emits `[1][2]`-style refs,
falling back to the raw citation ID when an ID is absent from the manifest.

**Dimension scores.** New helper `_dimension_score_table(results)` rolls
up `EvaluationResult.layer3_results.dimension_scores` across tasks,
averaging per `RubricDimension`. Silent no-op when no results carry
Layer 3 data.

## Test delta

- **1058 passed** (was 1027). +31 new renderer tests split into 10
  section-focused classes: `TestOutlineDrivenStructure`,
  `TestOutlineExecutiveSummary`, `TestOutlineAnalyticalFramework`,
  `TestOutlineKeyFindings`, `TestOutlineUncertainty`,
  `TestOutlineEvidenceGaps`, `TestOutlineAbsenceReport`,
  `TestOutlineEvaluationSummary`, `TestOutlineInlineCitations`,
  `TestOutlineEmpty`. Each covers the renderable section + a
  "section empty" fallback path.
- Zero new ruff errors on touched files; pre-existing errors on both
  files cleared incidentally (`pytest` unused import, I001 sort). Final
  state: `ruff check` clean on `markdown_renderer.py` and
  `test_markdown_renderer.py`.
- mypy strict delta: −1 error (baseline 9, now 8 — a function now has an
  explicit `claim: FindingClaim` annotation in the legacy helper). All
  remaining errors are pre-existing in the legacy path.
- Pre-existing unrelated test failure in the untracked work-in-progress
  `tests/unit/evaluator/test_layer4_trajectory.py` (ImportError on
  `DEFAULT_LAYER3_WEIGHT`) — failing on baseline too, not in scope.

## Changed files

| File | Change |
|---|---|
| `src/keystone/pipeline/markdown_renderer.py` | Rewritten. Outline-driven path with 8 section renderers plus shared citation-index / sources / title helpers. Legacy path retained verbatim for `outline=None`. Module-level `_TIER_LABELS`, `_sections_of_type`, `_confidence_counts`, `_section_type_to_tier`, `_dimension_score_table` helpers. |
| `tests/unit/pipeline/test_markdown_renderer.py` | Added outline fixtures (`_full_outline`, `_exec_item`, `_branch_item`, `_moderate_item`, `_weak_item`, `_contested_item`, `_gap_item`, `_insufficient_item`, `_absence_item`, `_eval_result_with_layer3`) and 10 new test classes (31 tests). Removed unused `pytest` import; fixed I001 sort. |
| `TODO.md` | Moved "Outline-driven rendering" from `Up Next` to `Done`. |

## Orchestrator

No change required. `orchestrator.py` already passes the filtered
`StructuredOutline` to `c.renderer.render(...)` at `pipeline/orchestrator.py:377`.
The outline-driven path is automatically active in production wiring.

## Gotchas

- `uncovered_branch_ids` now surfaces in two places: the Executive
  Summary caveat line (count only) and the Evidence Gaps subsection
  (IDs listed). Both are derived from the same field — changing the
  field's semantics would require updating both.
- The legacy-path helpers (`_render_executive_summary`, `_render_key_findings`,
  `_render_uncertainty`, `_render_gaps`, `_render_quality`,
  `_render_framework`) are still reachable when `outline=None`. They
  keep the old section names ("Research Gaps", "Quality Assessment") for
  backwards-compatible behavior; those names do not appear in the
  outline-driven path.
- `_format_inline_citations` preserves caller-provided ordering of
  citation IDs. That means a claim with `citation_ids=["CIT-002",
  "CIT-001"]` renders as `[2][1]`, not `[1][2]` — L2 controls the order.
- `MarkdownRenderer._format_claim_item` is a `@staticmethod` because
  branch items carry every piece of their own presentation context
  (`evidence`, `caveats`, `confidence_tier`, `confidence`, `note`).
  Calling `self._format_inline_citations` through the class name inside
  a static method is intentional.

---

## Previous session: Post-audit remediation (Streams A + B cleanup)

## What Changed (Audit remediation)

Three fixes from the Stream A + Stream B audit report landed in this pass.
Nothing else was touched.

- **`SprintContractNegotiated` → `SprintContractProposed`.** The event
  was misnamed: the underlying `SprintContractGenerator` is documented as
  "Phase 1 unilateral proposal," with bidirectional negotiation deferred
  to Phase 2 (Directive #13). Renamed across `events.py`, the L2
  contract docstring, `ContentStructurer`, and every test.
- **`frameworks_for_engagement` + `primary_framework` accept an override.**
  New optional `override: list[FrameworkHint] | None` parameter bypasses
  the default engagement-type → framework mapping. `ContentStructurer`
  constructor now takes `frameworks_override` and threads it through.
  This gives the Specification Engine a seam to inject custom frameworks
  for engagements that don't fit the five canonical types (Directive #1
  "predefined types are templates, not constraints"). An explicit empty
  list is respected — it signals "no framework applies," not "fall back
  to defaults."
- **`edgartools` and `docling` moved to optional extras.** Both are
  now under `[project.optional-dependencies]` as `retrieval-edgar`,
  `retrieval-docling`, and a combined `retrieval` extra. Minimal
  installs no longer pull torch + the 258M Granite-Docling model. Import
  gating was already in place: docling is imported lazily inside
  `DoclingBackend._build_default_converter` (the `ImportError` branch
  already returns a `DOCLING_UNAVAILABLE` warning), and edgartools is
  referenced only as a subprocess command string in `servers.py` — it is
  never imported by Keystone code.

Test delta: **1027 passed** (+4 new `TestFrameworkSelection` cases for
override, empty-override, mandatory-first selection, and structurer
threading). Zero new ruff errors on touched files. mypy strict delta is
zero (baseline error in `contracts.py:376` is pre-existing and
unrelated).

## Changed files (Audit remediation)

| File | Change |
|---|---|
| `src/keystone/events.py` | Renamed `SprintContractNegotiated` → `SprintContractProposed`; added docstring note about Phase 1/Phase 2 framing; updated `AnyPipelineEvent` union. |
| `src/keystone/contracts.py` | Updated `ContentStructuringContract.structure` docstring to reference the renamed event. |
| `src/keystone/structuring/framework_selector.py` | Added `override` parameter to `frameworks_for_engagement` and `primary_framework`. Module docstring cites Directive #1. |
| `src/keystone/structuring/content_structuring.py` | Renamed event import/yield; added `frameworks_override` constructor parameter; threaded override through `frameworks_for_engagement` and `primary_framework`. |
| `pyproject.toml` | Moved `edgartools` and `docling` out of `dependencies` into `[project.optional-dependencies]` (`retrieval-edgar`, `retrieval-docling`, `retrieval`). |
| `tests/unit/structuring/test_content_structuring.py` | Renamed event references; added 4 override tests. |
| `tests/unit/pipeline/test_orchestrator.py` | Renamed event references. |

## Install note

Runtime retrieval backends are now opt-in:

```bash
pip install -e ".[dev]"                  # tests + tooling, no retrieval extras
pip install -e ".[dev,retrieval]"        # add edgartools + docling
pip install -e ".[dev,retrieval-edgar]"  # EDGAR only
```

---

## Previous session: Stream A -- Retrieval Depth (EDGAR + deep research + Docling)

## What Changed (Stream A)

- Added `edgartools` MCP server integration in the gateway: three tool
  names (`edgar_filings`, `edgar_financials`, `edgar_company_facts`)
  share one upstream server (`edgartools-mcp`), declare the SEC
  `EDGAR_IDENTITY` User-Agent contract, and are rate-limited to SEC's
  10 req/sec cap through the new `SERVER_RATE_LIMITS` /
  `build_default_rate_limits` helpers.
- Wrote 20 new gateway tests covering EDGAR registration, SEC
  compliance config, shared-bucket rate limiting, authorization, tool
  discovery, description-budget headroom, and end-to-end MCPGateway
  dispatch.
- Added 26 unit tests for `ResearchAgent` deep mode (prompt
  construction, response parsing, event emission, shallow fallback,
  absence-report generation) and 12 unit tests for the underlying
  `_call_claude_cli_research` subprocess transport (argv, timeout,
  non-zero exit, concurrency cap, UTF-8 decode). None hit real
  `claude -p` or web traffic.
- Built the Docling PDF backend at
  `src/keystone/retrieval/docling_backend.py`. `DoclingBackend`
  implements the existing `PDFTextBackend` protocol, lazy-loads
  docling, captures errors as warning codes, and slots into
  `PDFParser(backend=DoclingBackend())`. 19 new tests drive it with an
  in-process fake converter -- the real docling library is never
  imported during tests.
- Registered `edgartools>=5.0.0` and `docling>=2.0.0` in
  `pyproject.toml`; added mypy overrides for `edgartools.*`,
  `edgar.*`, and `docling_core.*`.
- Full unit suite: **1023 passed** (was 1004 pre-session; +19 net
  after accounting for the adjusted `test_tool_registry` counts).
  `ruff check` clean on every new or touched file. `mypy --strict`
  clean on `servers.py`, `tool_names.py`, and `docling_backend.py`.

## New files (Stream A)

| File | Purpose |
|---|---|
| `src/keystone/retrieval/docling_backend.py` | `DoclingBackend` PDF text extractor using the Granite-Docling pipeline; lazy import + defensive error handling. |
| `tests/unit/gateway/test_edgar_integration.py` | 20 tests: EDGAR MCP registration, SEC User-Agent + rate-limit contract, shared-bucket behaviour, gateway dispatch. |
| `tests/unit/research/test_research_agent_deep.py` | 26 tests: deep-mode prompt construction, response parsing, events, fallback to shallow. |
| `tests/unit/test_llm_client_deep_research.py` | 12 tests: `_call_claude_cli_research` subprocess argv / timeout / exit handling + `get_deep_research_callable`. |
| `tests/unit/retrieval/test_docling_backend.py` | 19 tests: DoclingBackend happy path, failure modes, PDFParser integration. |

## Changed files (Stream A)

| File | Change |
|---|---|
| `src/keystone/tool_names.py` | Added `EDGAR_FINANCIALS`, `EDGAR_COMPANY_FACTS`, and the `EDGAR_TOOLS` grouping constant. |
| `src/keystone/gateway/servers.py` | Added `EDGAR_IDENTITY_ENV`, `EDGAR_MAX_REQ_PER_SEC`, `EDGAR_SERVER_NAME`; expanded EDGAR to three tool entries sharing one server; added `SERVER_RATE_LIMITS` + `build_default_rate_limits()`. |
| `src/keystone/retrieval/__init__.py` | Exports `DoclingBackend` + `DOCLING_PIPELINE_TAG`. |
| `pyproject.toml` | Added `edgartools`, `docling` deps; mypy overrides for `edgartools.*`, `edgar.*`, `docling_core.*`. |
| `tests/unit/test_tool_registry.py` & `tests/unit/gateway/test_tool_registry.py` | Updated tool-count assertions: `len(TOOL_CONFIGS) == 9`, `unique_server_count == 7`. |

## Design Choices (Stream A)

- **EDGAR = one server, three tool names.** All three EDGAR tool
  entries use `server_name="edgartools-mcp"` so the gateway's rate
  limiter, circuit breaker, and audit log aggregate per-agency.
  Agents can be authorized for a subset (e.g. financials-only) but
  can never collectively exceed SEC's 10 req/sec ceiling because the
  token bucket is shared at the server level.
- **SEC User-Agent via `EDGAR_IDENTITY`.** edgartools reads the
  identity string from that env var. Every EDGAR tool's
  `config.identity_env` points at it so deployment docs have a single
  source of truth. `rate_limit_per_second: 10` is recorded in the
  config dict as a documentation aid alongside the enforced bucket in
  `SERVER_RATE_LIMITS`.
- **DoclingBackend is lazy.** Docling is an expensive dependency
  (torch + the 258M Granite-Docling model). The backend stores an
  optional injected converter and only imports docling on the first
  `extract` when one was not supplied. Tests never touch the real
  library.
- **DoclingBackend never raises.** Empty bytes, non-PDF input, docling
  `ImportError`, conversion exceptions, encrypted PDFs, and non-SUCCESS
  status all degrade to empty pages + a warning code, matching the
  existing `BasicPDFTextBackend` vocabulary so downstream scoring
  logic stays uniform.
- **Deep-mode tests mock subprocess at the boundary.** The `_FakeProc`
  helper captures kill / wait / communicate calls without spawning a
  real process; `_patched_create` records argv so regression tests can
  pin `--allowedTools WebSearch,WebFetch`, `--no-session-persistence`,
  the 1200s default timeout, and Sonnet model selection.

## Key Commands

```bash
source .venv/bin/activate
pytest tests/unit/ -q                                    # 1023 tests
pytest tests/unit/gateway/test_edgar_integration.py -q   # 20 EDGAR tests
pytest tests/unit/research/test_research_agent_deep.py -q
pytest tests/unit/test_llm_client_deep_research.py -q
pytest tests/unit/retrieval/test_docling_backend.py -q
ruff check <new paths>                                   # clean
mypy src/keystone/gateway/servers.py \
     src/keystone/retrieval/docling_backend.py           # clean
```

## Integration Shape (Stream A)

```python
# EDGAR: agents request any of three tool names; gateway aggregates
# traffic through the same edgartools-mcp server under one rate bucket.
from keystone.gateway.servers import build_default_rate_limits, register_all_tools
from keystone.gateway.rate_limiter import InMemoryRateLimiter
from keystone.gateway.tool_registry import ToolRegistry

limiter = InMemoryRateLimiter(build_default_rate_limits())
registry = ToolRegistry()
register_all_tools(registry)  # edgar_filings + edgar_financials + edgar_company_facts

# Docling: swap the PDF backend at construction time. Pure stdlib
# BasicPDFTextBackend still works for simple PDFs; DoclingBackend
# handles complex layouts and tables.
from keystone.retrieval import DoclingBackend, PDFParser

parser = PDFParser(backend=DoclingBackend())
parsed = parser.parse(fetched_artifact)
```

## Gotchas (Stream A)

- DoclingBackend ships without docling installed; the first `extract`
  call on a system without docling returns warning code
  `DOCLING_UNAVAILABLE` (empty pages). `pyproject.toml` declares docling
  as an optional extra under `retrieval-docling` (post-audit) — install
  with `pip install -e ".[retrieval]"` when you need it.
- `SERVER_RATE_LIMITS` is a declarative default. Existing call sites
  still build ad-hoc limiters (e.g. `test_research_agent.py`). The
  helper exists for production wiring and tests that want
  SEC-accurate throttling.
- Changing the number of registered MCP tools requires updating
  `tests/unit/test_tool_registry.py::TestServerConfigs` and
  `tests/unit/gateway/test_tool_registry.py::TestServerConfigs`
  (they now assert `len(TOOL_CONFIGS) == 9` and
  `unique_server_count == 7`).

## Next Steps (Stream A)

- Wire `build_default_rate_limits()` into the production gateway
  initialization so EDGAR traffic is clamped at 10 req/sec without
  per-caller configuration.
- Real-MCP phase: plug a FastMCP-based client into the gateway so the
  `edgartools-mcp` stdio server is actually spawned; the current
  `MockMCPClient` only validates registry + routing wiring.
- DoclingBackend: once docling is installed, add an integration smoke
  test that parses a real SEC filing PDF and verifies table-extraction
  quality.

## What Did Not Change (Stream A)

- No modifications to orchestrator, deliberation, evaluator, citation
  processor, spec engine, content structurer, or renderer.
- No modifications to Lane E parsers (`article_parser.py`,
  `pdf_parser.py`, `evidence_normalizer.py`) -- DoclingBackend is a
  new drop-in backend; `PDFParser` itself is unchanged.
- No changes to the deep-research prompt or parsing logic in
  `research_agent.py`. The 26 new tests only observe existing
  behaviour.

---

## Prior session: Stream B -- L2 Content Structuring (output quality)

- **Built L2 Content Structuring** between L1.5 Deliberation and L4
  Evaluator. Previously the pipeline went
  L0 -> L1 -> CitProc -> L1.5 -> L4 -> Render; it now runs
  L0 -> L1 -> CitProc -> L1.5 -> **L2** -> L4 -> Render.
- New package `src/keystone/structuring/` (3 files, 738 lines):
  `ContentStructurer`, `filter_outline_by_passed_tasks`,
  `frameworks_for_engagement`, `primary_framework`,
  `render_task_section_text`.
- New model module `src/keystone/models/structuring.py` (171 lines):
  `StructuredOutline`, `StructuredSection`, `OutlineItem`,
  `AnalyticalFramework`, `FrameworkHint`, `OutlineSectionType`,
  `OutlineItemType`.
- Orchestrator now builds an `outline`, drafts per-task section text,
  and negotiates per-task sprint contracts through L2; the L4 eval
  loop consumes those artifacts directly.
- `MarkdownRenderer.render()` gained an optional
  `outline: StructuredOutline | None` parameter; when present it
  renders an "Analytical Framework" section derived from the
  engagement type.
- `ContentStructuringContract` Protocol in `contracts.py` updated to
  the real L2 signature; `test_protocol_contracts.py` now verifies
  `ContentStructurer` conforms.
- Stream B tests: 31 new (27 L2 + 3 renderer outline + 1 Protocol
  conformance). End of Stream B: 1004 / 1004 unit tests pass.

(Design notes, integration shape, and gotchas for Stream B were
recorded at session end; see commit history for the detailed log.)

## Still open

- Fix stale import in `tests/integration/test_evaluator_live.py`
  (`_parse_score_json` removed from `layer3_rubric.py`). Not blocking
  unit tests.
- Pre-existing canary failures noted by Stream B
  (`tests/canary/test_architectural_guarantees.py` governance flag
  threshold).
- Bidirectional sprint-contract negotiation between
  `SprintContractGenerator` and the Evaluator (Phase 2).
- LLM-augmented framework execution in L2 (currently only labels
  sections; does not populate framework artifacts).
