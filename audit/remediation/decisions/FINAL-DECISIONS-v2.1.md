# Final Architectural Decisions (v2.1)

*Created: 2026-04-11 | Revised: 2026-04-11 (v2.1 -- Wave 2B+ reconciliation after Wave 2A checkpoint)*
*Supersedes: FINAL-DECISIONS-v2.md*
*Inputs: 5.4 Pro Sessions 5-7, Codex static + adversarial reviews, Opus agents 1-4, REVIEW-SYNTHESIS.md, WAVE-2B-RECONCILIATION.md, PLANNING-ADDENDUM.md*
*Every model change in this document was verified against the actual source file. Governing-wave sequencing was then reconciled against the accepted round-3 planning overlay.*

---

## How to Read This

Six decisions (A-F). Decisions A-E remain the implementation foundation. Decision F records the accepted round-3 planning overlay for Wave 2B and later so the live wave order matches the architecture-first plan. Decisions are ordered by dependency. The implementation wave order at the end is the binding execution sequence.

**Notation:** `VERIFIED` tags cite the file, line, and what was confirmed.

---

## Decision A: Citation Identity & Provenance

**Issues addressed:** A01-A12 (resolved), A13 (contract defined Wave 2A, implementation deferred to Wave 3), A14 (deferred to Wave 3)

### Recommendation

Dual-layer citation identity. Source-instance IDs engagement-unique from creation. Canonical IDs assigned by CitationProcessor post-dedup. Findings rewritten to canonical IDs. Task provenance carried through confidence map.

### Verified Code State

- `VERIFIED: models/research.py:255-270` -- `FindingClaim` has no `claim_id` field. Fields: `text`, `evidence`, `citations: list[Citation]`, `confidence`, `confidence_tier`, `caveats`.
- `VERIFIED: models/citations.py:58` -- `Citation` is frozen (`model_config = ConfigDict(frozen=True)`). Cannot be mutated in-place. New fields require `model_copy(update={...})` to produce new instances.
- `VERIFIED: models/citations.py:92-114` -- `content_hash` is optional `str | None`, with validator enforcing 64-char hex. This is the field that currently stores `hash(url:title)` metadata, not actual content.
- `VERIFIED: models/citations.py:206-221` -- `WikiCompilationRecord.content_hash` is required `str` (not optional). Different semantics from `Citation.content_hash`.
- `VERIFIED: models/confidence.py:60-76` -- `HighConfidenceClaim` has no `aggregated_claim_id`. Fields: `claim`, `methodological_agreement`, `sources`, `corroboration_count`, `robustness`, `curmudgeon_challenge`, `discouq_features`.
- `VERIFIED: confidence_builder.py:95-105` -- Constructs `HighConfidenceClaim` without any ID field.
- `VERIFIED: finding_writer.py:90-98` -- Constructs `FindingClaim` without `claim_id`.
- `VERIFIED: aggregator.py:25-43` -- `AggregatedClaim` has no `aggregated_claim_id`, no `task_ids`. Has `corroboration_count` which is set to citation count (not cross-agent count).
- `VERIFIED: content_hash referenced in 20+ files` -- `dedup.py` (5 refs), `hash.py` (4), `citation/__init__.py` (4), `processor.py` (3), `wiki_builder.py` (4), `engagement_store.py` (3), `content_hasher.py` (1), `wiki_schema.py` (4), `models/citations.py` (5 incl. validator), plus 8 test files (~50+ refs).

### Concrete Model Changes

**`models/research.py` -- `FindingClaim`:**
```python
# NEW fields (Optional until producers populate them)
claim_id: str | None = Field(default=None, description="Stable claim identifier")
citation_ids: list[str] = Field(default_factory=list, description="Canonical citation IDs after processor rewrite")
```
Both optional. `finding_writer.py` will mint `claim_id` and derive `citation_ids` from embedded `citations`. Until that producer code exists, existing construction calls remain valid.

**`models/research.py` -- `StructuredFinding`:**
```python
# NEW field for partial-claim salvage
dropped_claims: list[dict] = Field(default_factory=list, description="Claims that failed validation, with reasons")
```
Optional with default. No existing code breaks.

**`models/confidence.py` -- all five tier claims:**
```python
# NEW fields (Optional until confidence_builder populates them)
aggregated_claim_id: str | None = Field(default=None, description="Links to provenance index")
task_ids: list[str] = Field(default_factory=list, description="Source task IDs")
```
Both optional with defaults. `confidence_builder.py` continues to work without them until Wave 2A adds population logic.

**`models/confidence.py` -- `ConfidenceMap`:**
```python
# NEW field
provenance_index: dict[str, list[str]] = Field(default_factory=dict, description="aggregated_claim_id -> task_ids")
```
Optional with default. No existing code breaks.

**`models/citations.py` -- `Citation`:**

The `content_hash` rename is a phased migration, not a single-wave atomic change.

*Wave 1C:* Add `metadata_hash: str | None = Field(default=None)` alongside existing `content_hash`. The old field keeps its name and validator. New code writes to `metadata_hash` for url:title hashes. Old code continues unchanged.

*Wave 2A:* Migrate all `content_hash` writers to use `metadata_hash` for metadata and `content_hash` only for actual content. Update validator if scope changes. This touches: `dedup.py`, `hash.py`, `citation/__init__.py`, `processor.py`, `wiki_builder.py`, `engagement_store.py`, `content_hasher.py`, `wiki_schema.py`, plus test files.

Since `Citation` is frozen, adding `merged_from_ids` requires constructing new Citation objects with the extra field. The processor's dedup merge in `dedup.py:104-143` already constructs new `Citation` instances for merged records. Add:
```python
merged_from_ids: list[str] = Field(default_factory=list, description="Source instance IDs merged into this canonical")
```
Optional with default. Existing construction in `dedup.py` continues to work (empty list default). Processor populates it during merge.

**`models/citations.py` -- `CitationManifest`:**
```python
# NEW
aliases: list[CitationAlias] = Field(default_factory=list)
```
New `CitationAlias` model:
```python
class CitationAlias(BaseModel):
    source_instance_id: str
    canonical_citation_id: str
    engagement_id: str
    task_id: str
    agent_id: str
```
Optional with default. No existing code breaks.

**`citation/processor.py` -- new return type:**
```python
class CitationProcessorResult(BaseModel):
    manifest: CitationManifest
    canonicalized_findings: list[StructuredFinding]
```
Add `get_result() -> CitationProcessorResult` alongside existing `get_manifest()`. Existing callers use `get_manifest()` unchanged until orchestrator is updated.

### Modified Files (exhaustive)

| File | Wave | Change |
|------|------|--------|
| `models/research.py` | 1C | `claim_id`, `citation_ids` on FindingClaim; `dropped_claims` on StructuredFinding |
| `models/citations.py` | 1C | `CitationAlias`, `merged_from_ids` on Citation, `metadata_hash` on Citation, `aliases` on CitationManifest |
| `models/confidence.py` | 2A | `aggregated_claim_id`, `task_ids` on all tier claims; `provenance_index` on ConfidenceMap |
| `research_agent.py` | 1C | Engagement-unique citation IDs; shallow `citation_refs`; remove round-broadcast |
| `finding_writer.py` | 1C | Mint `claim_id`; derive `citation_ids`; salvage valid claims (partial output) |
| `citation/processor.py` | 1C | `CitationProcessorResult`; alias map; rewrite findings to canonical IDs |
| `citation/dedup.py` | 1C | Populate `merged_from_ids` during merge |
| `contracts.py` | 1C | Update CitationProcessorContract |
| `deliberation/aggregator.py` | 2A | `aggregated_claim_id`; `task_ids`; fix `corroboration_count` semantics |
| `deliberation/confidence_builder.py` | 2A | Copy provenance fields into tier claims; build `provenance_index` |
| `deliberation/deliberation.py` | 2A | Consume canonicalized findings; pass manifest into aggregation |
| `pipeline/orchestrator.py` | 2A | Use canonicalized findings; filter confidence_map by provenance |
| `citation/hash.py` | 2A | Write `metadata_hash` for url:title hashes |
| `citation/__init__.py` | 2A | Update re-exports |
| `knowledge/wiki_builder.py` | 2A | Use `metadata_hash` for metadata hashes |
| `knowledge/engagement_store.py` | 2A | Update content_hash references |
| `knowledge/content_hasher.py` | 2A | Update verification logic |
| `knowledge/wiki_schema.py` | 2A | Update field references |
| 8+ test files | 1C+2A | Update fixtures and assertions |

### Tests

- `test_source_instance_ids_unique_across_parallel_agents`
- `test_citation_processor_builds_alias_map`
- `test_citation_processor_rewrites_findings_to_canonical_ids`
- `test_task_manifest_contains_exact_canonical_citations`
- `test_shallow_synthesis_requires_explicit_citation_refs`
- `test_finding_writer_salvages_valid_claims_on_partial_failure`
- `test_confidence_map_claims_carry_task_provenance` (Wave 2A)
- `test_renderer_drops_claims_from_failed_tasks` (Wave 2A)
- `test_renderer_drops_claims_from_unevaluated_tasks` (Wave 2A)

---

## Decision B: Enforcement Model

**Issues addressed:** B01-B06 (resolved), B07 (deferred to Wave 3 -- DAG execution), B08 (Phase 1 minimum viable loop scheduled for Wave 3B), B09-B15 (resolved)

**B08 scheduling note:** Iterative research remains **Phase 1 scope**. Wave 2B keeps the enforcement surface (`max_rounds`, sufficiency, coverage, task outcomes). Wave 3B delivers the minimum viable live loop: hard cap, lightweight quality gate, novelty exhaustion, persisted round state, and refined follow-on tasks from uncovered branches, contradictions, and prior gaps. This preserves the architecture-first plan without forcing full adaptive replanning into Wave 2B.

### Recommendation

`GovernanceState` as a per-run runtime object. Enforcement via `ProfileExecutionPolicy`. Profile resolved in L0 at `ResearchSpec` construction time. Task-scoped enforcement with pipeline-level coverage recomputation. `TaskImportance` enum (PRIMARY/CRITICAL/SUPPORTING/OPTIONAL) replaces the rejected `is_critical: bool`.

### Verified Code State

- `VERIFIED: models/research.py:88` -- `ResearchSpec` is frozen (`model_config = ConfigDict(frozen=True)`). Cannot be mutated after construction. Profile MUST be set in `_build_research_spec()`.
- `VERIFIED: spec_engine.py:302-349` -- `_build_research_spec()` constructs ResearchSpec. Does NOT include `pipeline_profile`. `classification.pipeline_profile` is available (line 147-151) but only logged.
- `VERIFIED: specification/engagement_classifier.py:18-28` -- `PipelineProfile` already exists as `StrEnum` with LIGHT, STANDARD, DEEP. `ClassificationResult` carries `pipeline_profile` at line 35.
- `VERIFIED: specification/engagement_classifier.py:14` -- imports `EngagementType` from `keystone.models.research`. If `models.research` imported `PipelineProfile` from `engagement_classifier`, it would create a circular import. Fix: move `PipelineProfile` definition to `models/research.py` (alongside `EngagementType`). `engagement_classifier.py` imports it from there. `specification/__init__.py` re-exports for backward compatibility.
- `VERIFIED: models/tasks.py:63-148` -- `ResearchTask` has `priority: int` and `target_decision_usefulness: int` but NO importance/criticality field. `frozen=False` at line 76.
- `VERIFIED: orchestrator.py:68-119` -- `Pipeline.__init__` stores all components as instance fields. `_result: PipelineResult | None = None` stored on instance.
- `VERIFIED: agent_pool.py:147-158` -- Failed agents return `AgentResult(finding=None, error=exc)`. `get_successful_findings()` filters them out silently. No `StructuredFinding` produced for failed tasks.
- `VERIFIED: hitl/gate.py:58-131` -- `create_and_wait_for_gate()` returns `GateResponse` on approve/modify. Raises `GateRejectedError` on reject, `GateTimeoutError` on timeout.
- `VERIFIED: error_recovery.py:64-73` -- `ErrorRecovery.__init__` accepts `llm_factory: Callable | None = None`. The factory parameter exists but is never wired from `Pipeline`.

### Profile Resolution (frozen-model safe)

Add to `ResearchSpec` (set at construction time only):
```python
recommended_pipeline_profile: PipelineProfile | None = Field(
    default=None, description="Classifier recommendation"
)
effective_pipeline_profile: PipelineProfile = Field(
    default=PipelineProfile.STANDARD, description="Active profile for this run"
)
profile_source: str = Field(
    default="classifier", description="'classifier' or 'user_override'"
)
```

`PipelineProfile` moved to `models/research.py` (avoids circular import with `engagement_classifier.py` which imports `EngagementType` from the same module). `engagement_classifier.py` and `specification/__init__.py` import from `models.research`. `governance/models.py` imports from `models.research`. All current import sites (`engagement_classifier.py`, `specification/__init__.py`, `test_engagement_classifier.py`, `test_architectural_guarantees.py`) updated to import from the new canonical location.

In `spec_engine.py:_build_research_spec()`, add to the constructor call:
```python
recommended_pipeline_profile=classification.pipeline_profile,
effective_pipeline_profile=classification.pipeline_profile,
profile_source="classifier",
```

User override: if provided via pipeline entry point, pass override value into `_build_research_spec` and set `profile_source="user_override"`.

### TaskImportance Enum

Add to `models/tasks.py`:
```python
class TaskImportance(StrEnum):
    PRIMARY = "primary"        # The main research question. Must pass for Standard+.
    CRITICAL = "critical"      # Essential supporting task. Must pass for Deep.
    SUPPORTING = "supporting"  # Valuable but not blocking. May degrade.
    OPTIONAL = "optional"      # Nice-to-have. May be dropped.
```

Add to `ResearchTask`:
```python
importance: TaskImportance = Field(
    default=TaskImportance.SUPPORTING,
    description="Task importance for enforcement policy"
)
```

Default is SUPPORTING (safe). Task generator sets PRIMARY for the primary question's task, CRITICAL for key dependencies in Deep mode.

### GovernanceState (simplified, per-run)

```python
# governance/models.py

class EnforcementAction(StrEnum):
    HALT = "halt"
    ESCALATE = "escalate"
    DEGRADE = "degrade"
    WARN = "warn"

class EnforcementScope(StrEnum):
    TASK = "task"
    PIPELINE = "pipeline"

class QualityFlag(BaseModel):
    gate: str
    action: EnforcementAction
    scope: EnforcementScope
    severity: Literal["info", "warn", "error", "critical"]
    message: str
    task_id: str | None = None

class ResearchStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED_NO_OUTPUT = "failed_no_output"
    NOT_RUN = "not_run"

class TaskOutcome(BaseModel):
    task_id: str
    importance: TaskImportance
    research_status: ResearchStatus
    evaluation_status: Literal["passed", "failed", "not_evaluated"]
    renderable: bool
    flags: list[QualityFlag] = Field(default_factory=list)

class GovernanceState(BaseModel):
    profile: PipelineProfile
    degraded: bool = False
    halted: bool = False
    flags: list[QualityFlag] = Field(default_factory=list)
    task_outcomes: dict[str, TaskOutcome] = Field(default_factory=dict)
```

### Enforcement Matrix (corrected)

The matrix uses `N/A` for gates that do not apply to a profile (not `SKIP`). Failure modes are split by scope (task vs pipeline) and output state.

| Gate | Scope | Light | Standard | Deep |
|------|-------|-------|----------|------|
| L0 spec parse fails | PIPELINE | HALT | HALT | HALT |
| L0 MECE validation fails | PIPELINE | N/A | DEGRADE | ESCALATE |
| HITL Gate 1 | PIPELINE | N/A | ESCALATE | ESCALATE |
| L1 task failed_no_output (after retries) | TASK | HALT | *coverage* | *coverage* |
| L1 task partial_output | TASK | DEGRADE | DEGRADE | DEGRADE (SUPPORTING/OPTIONAL only) |
| L1 max rounds, no sufficiency | TASK | DEGRADE | DEGRADE | ESCALATE |
| Manifest integrity issue (no fabrication) | TASK | WARN | DEGRADE | DEGRADE |
| HITL Gate 2 | PIPELINE | N/A | ESCALATE | ESCALATE |
| L4 citation fabrication detected | TASK | HALT | HALT | HALT |
| L4 Layer 1 deterministic discrepancies | TASK | WARN | DEGRADE | DEGRADE |
| L4 Layer 3 rubric threshold miss | TASK | N/A | DEGRADE | ESCALATE |
| Evaluation coverage incomplete | PIPELINE | HALT | HALT | HALT |

**"*coverage*" for failed_no_output:** The task is non-renderable. Pipeline continues. Whether the pipeline itself halts depends on coverage policy below.

**Coverage policy:**
- Light: every rendered task must be evaluated and passed. (Evaluation coverage incomplete = HALT.)
- Standard: PRIMARY task must pass. >= 60% of tasks must pass.
- Deep: all PRIMARY and CRITICAL tasks must pass. >= 80% must pass.

**HITL `modified` semantics:** If `GateResolution.status == "modified"`, the pipeline checks `patch_applied`. If `patch_applied == False`, the pipeline halts with a message that modifications are not yet supported in this phase. It does not silently continue.

### Error Recovery Wiring

Wire `llm_factory` into `ErrorRecovery` from `Pipeline`. Per-call fallback chains:
- L0 spec: `[FLAGSHIP, STANDARD]`
- L1 research: `[STANDARD, FAST]`
- L1.5 aggregation/judge: `[FLAGSHIP, STANDARD]`
- L4 evaluator: `[FLAGSHIP, STANDARD]` (never FAST)

### Wave 2B additions accepted in reconciliation

Wave 2B is not just the original governance matrix work. The accepted overlay expands it with five execution-path fixes that complete the Phase 1 enforcement surface:

1. **E-1 epsilon fix:** `evaluator/layer3_rubric.py` must use epsilon `0.01` instead of a `1.0` floor in the geometric mean. This is a correctness fix, not a later calibration preference.
2. **E-9 SprintContractGenerator wiring:** `Pipeline` / `orchestrator.py` must call `SprintContractGenerator.generate()` instead of constructing a bare sprint contract inline.
3. **E-10 evaluation-profile routing:** `effective_pipeline_profile` from `ResearchSpec` must be passed into `Evaluator` construction and become load-bearing before domain-specific profiles arrive in Wave 3.
4. **E-6 dimension emphasis:** rubric scoring must apply `dimension_emphasis` multipliers rather than dropping that field on the floor.
5. **E-7 prompt field consumption:** rubric prompts must receive `mandatory_elements` and `anti_patterns` from the generated sprint contract.

**Sequencing inside Wave 2B:** `E-9` is a hard prerequisite for `E-6` and `E-7`. `E-10` lands alongside the governance wiring. `E-1` lands in the same wave and does not wait for Wave 5 calibration.

### Modified Files

| File | Wave | Change |
|------|------|--------|
| `models/research.py` | 1A | Profile fields on ResearchSpec |
| `models/tasks.py` | 1A | `TaskImportance` enum, `importance` field on ResearchTask |
| `governance/__init__.py` | 1A | New package |
| `governance/models.py` | 1A | GovernanceState, QualityFlag, TaskOutcome, etc. |
| `governance/policy.py` | 2B | ProfileExecutionPolicy, enforcement lookup |
| `spec_engine.py` | 2B | Populate profile in `_build_research_spec()`; L0 gate enforcement |
| `orchestrator.py` | 2B | Build GovernanceState; consult policy at gates; filter by task_outcomes; call `SprintContractGenerator.generate()`; pass routed profile into `Evaluator` |
| `evaluator.py` | 2B | Update task_outcomes with evaluation results; accept routed profile and generated sprint-contract fields |
| `evaluator/layer3_rubric.py` | 2B | Use epsilon `0.01`; apply `dimension_emphasis`; inject `mandatory_elements` and `anti_patterns` into rubric prompts |
| `evaluator/sprint_contract.py` | 2B | Generator becomes the only supported sprint-contract construction path for orchestrator wiring |
| `hitl/schemas.py` | 2B | Define `GateResolution` model (wraps `GateResponse` with `status`, `patch_applied` fields) |
| `gate.py` | 2B | Return `GateResolution` (from `hitl/schemas.py`); block on unapplied modifications |
| `contracts.py` | 2B | Update `HITLGateContract` return type to `GateResolution`; align protocol with implementation |
| `deliberation/deliberation.py` | 2B | Gate 2 profile-gating (skip for Light); consume `GateResolution` with `patch_applied` check; same semantics as Gate 1 |
| `error_recovery.py` | 1C | Wire `llm_factory` from Pipeline |
| `finding_writer.py` | 1C | Salvage valid claims; record dropped claims |
| `task_generator.py` | 2B | Set `importance` based on issue-tree position |

### Tests

- `test_research_spec_carries_pipeline_profile_from_l0`
- `test_frozen_research_spec_profile_set_at_construction`
- `test_enforcement_matrix_light_profile`
- `test_enforcement_matrix_standard_profile`
- `test_enforcement_matrix_deep_profile`
- `test_failed_no_output_task_non_renderable`
- `test_partial_output_degrade_supporting_only`
- `test_light_coverage_halts_on_unevaluated_rendered`
- `test_hitl_modified_halts_when_not_applied`
- `test_error_recovery_uses_wired_llm_factory`
- `test_coverage_policy_standard_requires_primary_pass`
- `test_geometric_mean_uses_epsilon_floor`
- `test_orchestrator_uses_sprint_contract_generator`
- `test_orchestrator_passes_profile_to_evaluator`
- `test_dimension_emphasis_applied_in_layer3`
- `test_rubric_prompts_include_mandatory_elements_and_anti_patterns`

---

## Decision C: Deep Research Formalization

**Issues resolved:** C01-C03

### Recommendation

Deep research remains experimental but auditable. Add audit events and governance visibility for the gateway bypass. Wire template registry prompts into both deep and shallow execution paths.

### Verified Code State

- `VERIFIED: research_agent.py` -- Deep research builds its own prompt. Shallow sends `task.description` into tool queries. Template registry `system_prompt` is not consumed by either path.
- `VERIFIED: specification/template_registry.py` -- Rich `system_prompt` definitions exist per agent type but are not used at runtime.

### Concrete Changes

| File | Wave | Change |
|------|------|--------|
| `events.py` | 3 | Add `DeepResearchInvoked` event |
| `research_agent.py` | 3 | Emit event; prepend template `system_prompt` to deep prompt; use template material in shallow synthesis |
| `orchestrator.py` | 3 | Record `gateway_bypassed=True` in governance when deep mode used |

### Tests

- `test_deep_research_emits_invocation_event`
- `test_template_prompt_wired_in_deep_mode`
- `test_template_prompt_wired_in_shallow_mode`
- `test_gateway_bypass_visible_in_governance`

---

## Decision D: LLM Output Parsing Standard

**Issues resolved:** D01-D10

### Recommendation

Single `safe_llm_json()` utility replaces ALL existing JSON extraction. `parse_llm_bool()` for boolean coercion. `ParseError` exception for failures. Every caller either recovers explicitly or surfaces a `QualityFlag`. No silent fallbacks.

### Verified Code State

Six existing JSON extraction implementations:
- `VERIFIED: specification/_prompts.py:34-58` -- regex, dict only, greedy `{.*}` with DOTALL
- `VERIFIED: research_agent.py` -- bracket-counting `_extract_json_text`, most robust
- `VERIFIED: evaluator/layer1_deterministic.py:116-157` -- rfind-based
- `VERIFIED: evaluator/layer3_rubric.py:186-208` -- separate extractor
- `VERIFIED: evaluator/sprint_contract.py:75-88` -- find/rfind braces, returns `{}` on failure
- `VERIFIED: deliberation/analyst.py, aggregator.py, wwhtb.py` -- bare `json.loads`, no fence handling

### Concrete Implementation

New file: `src/keystone/llm/parsing.py`

```python
class ParseError(Exception):
    def __init__(self, message: str, raw_text: str): ...

def safe_llm_json(
    text: str,
    *,
    required_keys: Sequence[str] = (),
    expect_list: bool = False,
    bool_keys: frozenset[str] = frozenset(),
) -> dict | list:
    """Single entry point for parsing LLM JSON output.
    Raises ParseError on failure. Never returns None. Never silently defaults."""

def parse_llm_bool(value: object) -> bool:
    """True: True, "true", "yes", 1. False: False, "false", "no", 0.
    Anything else: raise ValueError."""
```

### Modified Files (exhaustive -- all 6 extractors replaced)

| File | Wave | Change |
|------|------|--------|
| `llm/parsing.py` | 1B | NEW: `safe_llm_json`, `parse_llm_bool`, `ParseError` |
| `specification/_prompts.py` | 1B | `extract_json` delegates to `safe_llm_json` |
| `specification/engagement_classifier.py` | 1B | Replace `data["engagement_type"]` with safe_llm_json + `.get()` |
| `specification/intent_clarifier.py` | 1B | Replace 4 bare key accesses |
| `specification/priority_scorer.py` | 1B | Replace bare key accesses |
| `specification/task_generator.py` | 1B | Replace bare key accesses |
| `specification/validator.py` | 1B | Replace `bool()` with `parse_llm_bool()` |
| `research/research_agent.py` | 1B | Replace `_extract_json_text` with `safe_llm_json`; fix dead isinstance |
| `deliberation/analyst.py` | 1B | Replace `json.loads` with `safe_llm_json` |
| `deliberation/aggregator.py` | 1B | Replace both `json.loads` calls |
| `deliberation/wwhtb.py` | 1B | Replace `json.loads` |
| `evaluator/layer1_deterministic.py` | 1B | Replace `_parse_json_array` with `safe_llm_json(expect_list=True)` |
| `evaluator/layer3_rubric.py` | 1B | Replace score extraction; ParseError instead of silent 50 |
| `evaluator/sprint_contract.py` | 1B | Replace `_parse_contract_json` with `safe_llm_json` |

### Tests

- `test_safe_llm_json_strips_fences`
- `test_safe_llm_json_handles_nested_fences`
- `test_safe_llm_json_extracts_array`
- `test_safe_llm_json_validates_required_keys`
- `test_safe_llm_json_coerces_bool_keys`
- `test_safe_llm_json_rejects_prose_as_json`
- `test_parse_llm_bool_string_false_is_false`
- `test_parse_llm_bool_rejects_unknown_values`
- `test_mece_validator_string_false_fails_dimension`
- `test_aggregator_judge_fenced_json`
- `test_parse_failure_does_not_fabricate_score`

---

## Decision E: Instance Lifecycle & Concurrency

**Issues resolved:** E01-E08

### Recommendation

Split into E1 (per-run lifecycle isolation, Wave 1A) and E2 (concurrency cleanup, Wave 3). E1 must land before any other decision because governance, citation identity, and parsing all assume per-run state isolation.

### Verified Code State

- `VERIFIED: orchestrator.py:68-119` -- `Pipeline.__init__` stores: `_spec_engine`, `_agent_pool`, `_citation_processor`, `_deliberation`, `_evaluator`, `_renderer`, `_result`, `_template_registry`.
- `VERIFIED: spec_engine.py:193` -- `self._agent_configs = []` then appended to. Reuse mixes configs.
- `VERIFIED: test_architectural_guarantees.py` -- Canary tests monkeypatch: `pipeline._spec_engine.generate_spec`, `pipeline._spec_engine.get_spec`, `pipeline._agent_pool.execute_all`, `pipeline._agent_pool.get_successful_findings`, `pipeline._deliberation.deliberate`, `pipeline._deliberation.get_confidence_map`, `pipeline._citation_processor.process`, `pipeline._citation_processor.get_manifest`, `pipeline._renderer.render`.

### E1: Per-Run Lifecycle (Wave 1A)

Move component construction from `__init__` to `run_with_events()`:

```python
class Pipeline:
    def __init__(
        self,
        llm_factory: Callable[[ModelTier], LLMCallable],
        gateway: MCPGateway,
        db_session_factory: Callable | None = None,
        max_eval_tasks: int | None = None,
    ) -> None:
        # Keep only factories and config
        self._llm_factory = llm_factory
        self._gateway = gateway
        self._db_session_factory = db_session_factory
        self._max_eval_tasks = max_eval_tasks

    async def run_with_events(self, question, client_id, ...):
        # Build fresh per run
        spec_engine = SpecificationEngine(...)
        agent_pool = AgentPool(...)
        citation_processor = CitationProcessor()
        deliberation = Deliberation(...)
        renderer = MarkdownRenderer()
        # ... use local variables throughout
```

**Test migration strategy: component injection is the PRIMARY mechanism.**

`run_with_events()` accepts optional component overrides via keyword arguments. This is the only supported way for tests to replace components. Tests do not monkeypatch instance attributes.

```python
async def run_with_events(
    self,
    question: str,
    client_id: str,
    *,
    # Component overrides for testing (None = build fresh)
    spec_engine: SpecificationEngine | None = None,
    agent_pool: AgentPool | None = None,
    citation_processor: CitationProcessor | None = None,
    deliberation: Deliberation | None = None,
    renderer: MarkdownRenderer | None = None,
    **kwargs,
):
    _spec_engine = spec_engine or SpecificationEngine(...)
    _agent_pool = agent_pool or AgentPool(...)
    _citation_processor = citation_processor or CitationProcessor()
    _deliberation = deliberation or Deliberation(...)
    _renderer = renderer or MarkdownRenderer()
    # ... use these throughout
```

**Specific canary test migrations (all 9 patch points covered):**

| Current patch | New approach |
|--------------|-------------|
| `pipeline._spec_engine.generate_spec` | Pass pre-configured `SpecificationEngine` mock via `spec_engine=` kwarg |
| `pipeline._spec_engine.get_spec` | Same mock object |
| `pipeline._agent_pool.execute_all` | Pass pre-configured `AgentPool` mock via `agent_pool=` kwarg |
| `pipeline._agent_pool.get_successful_findings` | Same mock object |
| `pipeline._citation_processor.process` | Pass mock via `citation_processor=` kwarg |
| `pipeline._citation_processor.get_manifest` | Same mock object |
| `pipeline._deliberation.deliberate` | Pass mock via `deliberation=` kwarg |
| `pipeline._deliberation.get_confidence_map` | Same mock object |
| `pipeline._renderer.render` | Pass mock via `renderer=` kwarg |

Tests that use components directly (not through Pipeline) need no changes:
- `test_l0_validation_state_is_truthful`: uses `SpecificationEngine` directly.
- `test_evaluator_fallback_constructors_produce_valid_models`: uses `Evaluator` directly.
- `test_claim_level_citations_are_narrower_than_round_level`: uses `ResearchAgent` directly.
- `test_deep_research_emits_audit_equivalent_events`: uses `ResearchAgent` directly.

### E2: Concurrency Cleanup (Wave 3)

| File | Change |
|------|--------|
| `deliberation/deliberation.py` | Per-analyst `try/except` wrapper around `asyncio.gather` |
| `llm_client.py` | `try/finally` around `proc.communicate()` to kill on CancelledError |
| `gateway/circuit_breaker.py` | Hold lock through probe execution in HALF_OPEN |
| `hitl/service.py` | Shorter-lived polling sessions; idempotent decision submission |

### Tests

- `test_pipeline_fresh_components_per_run`
- `test_spec_engine_no_agent_config_leak`
- `test_one_analyst_failure_does_not_kill_others` (Wave 3)
- `test_subprocess_killed_on_cancellation` (Wave 3)
- `test_circuit_breaker_single_probe_in_half_open` (Wave 3)

---

## Decision F: Accepted Round-3 Planning Overlay (Wave 2B+)

**Issues resolved:** D-1, D-2, D-8, D-9, and the calibration-sequencing call for D-3 / D-4 / D-5 / D-6 / D-7 / D-10

### Recommendation

Preserve the architecture-first plan exactly where the overlay says it matters: temporarily incomplete is acceptable; architecturally false is not. Do **not** narrow Phase 1 into a research-prep MVP. Keep dual-axis taxonomy, thin real Pipeline-L2, and a minimum viable live iterative loop in the Phase 1 plan. Keep Phase 1 output scoped to **decision-informing analysis**. Keep calibration-policy changes deferred to Wave 5 except for the `E-1` epsilon bug fix that lands in Wave 2B.

### F1. Dual-axis taxonomy (Wave 3)

The accepted overlay keeps the plan's dual-axis taxonomy and rejects collapsing everything into a single engagement-type axis.

**Concrete changes:**
- Add `DomainCategory` to `models/research.py`.
- Add `domain_category` plus `secondary_types: list[EngagementType]` to `ClassificationResult`.
- Update the classification prompt to emit both axes.
- Route `domain_category` into template matching instead of collapsing on `custom_category`.
- Expand evaluation-profile mapping at minimum for M&A and Restructuring.

**Provisional-weight rule:** M&A / Restructuring profile weights are explicitly provisional until Wave 5 calibration against real Jack-scored outputs. Wave 3 adds the profile paths; Wave 5 decides the final numbers.

### F2. Thin Pipeline-L2 (Wave 3B)

Pipeline-L2 remains **Phase 1 scope**, but as a thin real layer instead of a full deliverable-generation stack.

**Concrete changes:**
- Add a `StructuredOutline` model under `models/`.
- Add `src/keystone/structuring/content_structuring.py`.
- Insert Pipeline-L2 between Deliberation and Evaluation / Rendering.
- Make the renderer consume `StructuredOutline` instead of raw `ConfidenceMap`.
- Keep framework selection behind a registry-style seam even if Phase 1 ships with a small seeded set.

**Out of scope inside Phase 1 L2:** no narrative prose generation, no section-level sprint-contract negotiation, no full skills-library progressive loading, no cross-section coherence optimizer.

### F3. Minimum viable live iterative loop (Wave 3B)

Iterative research is **not deferred out of Phase 1**. The minimum viable live loop is the binding plan for Wave 3B.

**Concrete changes:**
- Wrap research execution in profile-driven round control with `LIGHT=1`, `STANDARD=2-3`, `DEEP=3-5`, hard max `5`.
- Persist and reload a round-to-round research-state scratchpad carrying intent, findings, gaps, branch coverage, and stop-condition status.
- Compute issue-tree branch coverage between rounds.
- Use a lightweight sufficiency / quality gate between rounds.
- Treat novelty exhaustion as a first-class stop signal using duplicate / overlap heuristics in Phase 1.
- Generate round `N+1` work from uncovered branches, contradictions, open gaps, and prior findings rather than replaying raw task text unchanged.

**Still deferred:** semantic novelty search, ADaPT-style reactive decomposition, and a full adaptive replanner.

### F4. Decision-informing analysis (Wave 4 research / 4B implementation)

Phase 1 output remains **decision-informing analysis**, not stakeholder-specific recommendation framing.

**Concrete changes:**
- Rewrite actionability evaluation so it grades decision-informing specificity, quantified tradeoffs, implications, and clear "so what" logic.
- Do **not** require implementation timelines, stakeholder-specific playbooks, or recommendation-packaging behavior in Phase 1.
- Treat this as content-layer research in Wave 4, then implement the resulting prompt/rubric changes in Wave 4B.

### F5. Calibration sequencing (Wave 5)

The only calibration-related item that moves forward is `E-1` in Wave 2B. Everything else stays explicitly sequenced after real outputs exist.

**Wave 5 mandate:**
- Produce 5-10 real outputs.
- Have Jack score them pass/fail (and note strong/weak dimensions).
- Use those results to resolve D-3 through D-7 and D-10 empirically instead of by intuition.

### Modified Files / Wave Mapping

| File | Wave | Change |
|------|------|--------|
| `models/research.py` | 3 | `DomainCategory`; dual-axis classification fields |
| `specification/engagement_classifier.py` | 3 | Emit `domain_category` and `secondary_types` |
| `specification/prompts/classification.md` | 3 | Dual-axis prompt output |
| `specification/template_registry.py` | 3 | Route on `domain_category` |
| `evaluator/rubric_config.py` | 3 | Add provisional M&A / Restructuring profile mappings |
| `models/` | 3B | `StructuredOutline` model |
| `structuring/content_structuring.py` | 3B | Thin Pipeline-L2 implementation |
| `pipeline/orchestrator.py` | 3B | Round loop, research-state continuity, Pipeline-L2 wiring |
| `pipeline/markdown_renderer.py` | 3B | Consume `StructuredOutline` |
| `evaluator/prompts/actionability.md` | 4B | Decision-informing-analysis framing |

### Tests

- `test_classifier_emits_domain_category_and_secondary_types`
- `test_template_registry_routes_on_domain_category`
- `test_renderer_consumes_structured_outline`
- `test_iterative_loop_stops_on_cap_quality_or_novelty`
- `test_round_n_plus_1_tasks_use_prior_findings_and_open_gaps`
- `test_actionability_prompt_grades_decision_informing_specificity`

---

## Mandatory Adjunct Fixes

These are not separate decisions but prerequisites or small fixes that must ship alongside the decisions they enable.

### HITL Event Emission (Wave 1C)

Emit `ReviewGateCreated`, `ReviewDecisionSubmitted`, and resolution events from `gate.py`/`service.py`. Events already defined in `events.py`. Zero emission sites currently exist. Small, testable fix.

### PostSynthesisVerifier Contract (Wave 2A)

Define the interface for a post-synthesis verification stage:
```python
class PostSynthesisVerifierContract(Protocol):
    async def verify(
        self,
        rendered_claims: list[str],
        manifest: CitationManifest,
        provenance_index: dict[str, list[str]],
    ) -> VerificationResult: ...
```
Full implementation in Wave 3. The contract ensures A's provenance chain has a terminal consumer and is testable end-to-end.

### DAG Execution (Wave 3) -- addresses B07

Topological batch dispatch in orchestrator. Tasks grouped by dependency depth. Each batch executes in parallel. When a dependency fails:
- If `failed_no_output`: dependent tasks marked `NOT_RUN`, handled by coverage policy.
- If `partial`: dependent tasks may proceed with reduced context.

### Provenance Sidecar (Wave 3) -- addresses A14

Generate `<engagement_id>.provenance.md` alongside each deliverable. Records sources consulted vs. accepted vs. rejected, verification status, and paths to intermediate artifacts.

---

## Implementation Wave Order (binding)

### Wave 1A: Lifecycle + Data Model Prerequisites

**Decisions:** E1 + B data models

**Deliverables:**
1. Per-run component construction in `Pipeline` with component-injection kwargs (E1)
2. Canary test migration to use component injection (all 9 patch points)
3. Move `PipelineProfile` from `specification/engagement_classifier.py` to `models/research.py`; update all import sites
4. `ResearchSpec` profile fields (set in `_build_research_spec()`)
5. `TaskImportance` enum on `ResearchTask`
6. `GovernanceState` / `TaskOutcome` / `QualityFlag` skeleton in new `governance/` package

**Why first:** Everything else assumes per-run isolation and these model fields.

### Wave 1B: LLM Parsing Standard

**Decision:** D

**Deliverables:**
1. `safe_llm_json`, `parse_llm_bool`, `ParseError` in `llm/parsing.py`
2. Replace all 6 existing extractors + all bare dict["key"] sites (14 files)

**Why here:** Independent of A. Can proceed in parallel with 1C if files don't overlap (they share `research_agent.py`, so sequence 1B before 1C).

### Wave 1C: Citation Identity Foundation + Error Recovery

**Decision:** A (producer path) + B prerequisites

**Deliverables:**
1. Engagement-unique citation IDs in `research_agent.py`
2. `claim_id` minting in `finding_writer.py`
3. Shallow `citation_refs` pattern (remove round-broadcast)
4. FindingWriter partial-claim salvage
5. ErrorRecovery `llm_factory` wiring
6. `CitationProcessorResult` with canonicalized findings + alias map
7. HITL event emission from gate/service

**Why here:** Producers must populate new fields before Wave 2 makes them load-bearing.

### Wave 2A: Citation Identity Completion

**Decision:** A (canonical rewrite + provenance)

**Deliverables:**
1. Aggregator: `aggregated_claim_id`, `task_ids`, fixed `corroboration_count`
2. ConfidenceBuilder: copy provenance into tier claims, build `provenance_index`
3. Deliberation consumes manifest + canonicalized findings
4. Orchestrator filters confidence_map + manifest by task provenance
5. `metadata_hash` migration (phase 2 of content_hash rename)
6. PostSynthesisVerifier contract definition

### Wave 2B: Enforcement Model

**Decision:** B (full governance)

**Deliverables:**
1. `ProfileExecutionPolicy` with enforcement lookup
2. Profile-owned L0 gate enforcement in `spec_engine.py`
3. Task-scope enforcement in orchestrator
4. Coverage policy computation
5. GateResolution with `patch_applied` blocking
6. Evaluator updates task_outcomes
7. Task generator sets `importance`
8. `E-1`: geometric mean epsilon fix (`0.01`)
9. `E-9`: orchestrator calls `SprintContractGenerator.generate()`
10. `E-10`: routed evaluation profile passed from `ResearchSpec` into `Evaluator`
11. `E-6`: apply `dimension_emphasis` in rubric scoring
12. `E-7`: inject `mandatory_elements` and `anti_patterns` into rubric prompts

**Why after 2A:** Enforcement filtering depends on provenance fields from 2A. `E-9` must land before `E-6` / `E-7`, and `E-10` must land before Wave 3 expands the profile map.

### Wave 3: Completeness

**Decisions:** C + E2 + F1

**Deliverables:**
1. Deep research audit events + template prompt wiring (C)
2. DAG topological batch dispatch
3. PostSynthesisVerifier implementation
4. Deliberation gather fallback (E2)
5. Subprocess cleanup (E2)
6. Circuit breaker fix (E2)
7. HITL polling cleanup (E2)
8. Provenance sidecar generation
9. Dual-axis taxonomy: `DomainCategory`, `secondary_types`, prompt update, template routing
10. Provisional M&A / Restructuring profile expansion in `rubric_config.py`

### Wave 3B: Thin Pipeline-L2 + Live Iterative Loop

**Decisions:** F2 + F3

**Deliverables:**
1. `StructuredOutline` model
2. Thin `content_structuring.py` Pipeline-L2 layer
3. Renderer consumes `StructuredOutline`
4. Profile-driven round loop with persisted research-state continuity
5. Branch coverage computation between rounds
6. Lightweight sufficiency gate
7. Novelty-exhaustion stop condition
8. Round `N+1` work generated from uncovered branches, contradictions, and prior gaps

### Wave 4: Polish + Content Research

Documentation fixes, schema alignment, dead code, test improvements per MASTER-ISSUE-LIST DOC-*, DRIFT-*, TEST-* items, plus the content-layer research sessions needed to align prompts/rubrics/templates with the accepted decision-informing-analysis stance.

### Wave 4B: Content Implementation

Implement the Wave 4 content designs: decision-informing actionability framing, prompt/rubric/template revisions, and related content-layer fixes that depend on the completed research pass.

### Wave 5: Calibration

Produce 5-10 real outputs, have Jack score them, and resolve the remaining calibration-policy decisions empirically. This is where the provisional M&A / Restructuring profile weights become final (or change).

---

## Highest-Risk Element

Decision B remains the highest implementation risk. Not because governance is wrong, but because it sits on top of the most prerequisites: per-run lifecycle (E1), canonical citation identity (A), provenance filtering (A), partial-output semantics (FindingWriter salvage), model fallback (ErrorRecovery wiring), frozen-model profile resolution, and now the reconciled Wave 2B adjuncts (`E-1`, `E-9`, `E-10`, `E-6`, `E-7`). If any prerequisite is incomplete, governance tests will pass against incorrect runtime behavior.

The corrected wave order now is: `E1 -> D -> A producers -> A canonicalization -> B + Wave 2B adjuncts -> F1 dual-axis taxonomy -> F2/F3 Pipeline-L2 + live loop -> F4 content implementation -> F5 calibration`. That preserves the architecture-first plan without falsely shrinking Phase 1.

**If you want to discuss any decision before implementation begins, flag it now.**
