# Wave 1 Full Adversarial Review Prompt

You are conducting an adversarial review of ALL Wave 1 implementation work (Waves 1A, 1B, 1C) for the Keystone Intelligence Engine. Use parallel agents when helpful to increase quality, depth, and breadth of your review -- for example, one agent per wave, or one per concern area (model safety, concurrency, test coverage, error propagation).

---

## Project Context

**What this is:** Keystone Intelligence Engine -- a multi-agent AI system for automated consulting research. Capstone project for IU Kelley School of Business.

**Deployment context:** Claude Max subscription. LLM calls go through `claude -p` (Claude CLI). The OpenAI/Codex OAuth paths in `llm_client.py` are legacy code we no longer use. Do not flag issues in the OpenAI paths as blockers.

**Architecture:** 6-layer DPVI pipeline:
```
L0 (Specification) -> L1 (Research Agents) -> CitationProcessor ->
L1.5 (Deliberation) -> L4 (Evaluator) -> L3 (Renderer)
```

**Design document:** `audit/remediation/decisions/FINAL-DECISIONS-v2.md` -- this is the approved design. All implementation should match it.

---

## What Was Implemented (4 commits, 38 source+test files)

### Commits (oldest to newest):
```
9893a4d Wave 1A: per-run lifecycle isolation + concurrency fixes (Decision E)
0344fb2 Wave 1B: unified LLM output parsing standard (Decision D)
884552f Fix ParseError.message attribute and aggregator consistency_check logging
1583d03 Wave 1C: citation identity foundation + error recovery (Decision A producers + B prereqs)
```

### Wave 1A: Instance Lifecycle & Concurrency (Decision E)
**Goal:** Per-run component isolation + concurrency safety fixes.

**Changes:**
1. `src/keystone/pipeline/orchestrator.py` -- Moved all component construction from `Pipeline.__init__` to `run_with_events()` via `_build_components()` method. `__init__` now stores only factories and config. Added `PipelineComponents` dataclass. Tests inject mocks via `_pending_components`. `self._result` reset at top of each run.
2. `src/keystone/deliberation/deliberation.py` -- `asyncio.gather` now uses `return_exceptions=True`. Failed analysts are logged and excluded; successful outputs continue to aggregation.
3. `src/keystone/llm_client.py` -- Added `try/finally` around `proc.communicate()` in both `_call_claude_cli` and `_call_claude_cli_research`. `finally` block calls `proc.kill()` + `await asyncio.shield(proc.wait())` to prevent zombie subprocesses on `CancelledError`. Also unified legacy OpenAI auth resolver (`_resolve_openai_auth_type`).
4. `src/keystone/gateway/circuit_breaker.py` -- HALF_OPEN state now holds the lock through probe execution (preventing multi-probe). `except Exception` changed to `except BaseException` to catch `CancelledError`. Dead `HALF_OPEN` branch in `_record_failure()` is noted but not removed.

**Test changes:** `tests/unit/pipeline/test_orchestrator.py` and `tests/canary/test_architectural_guarantees.py` migrated to new `_pending_components` injection pattern. New canary tests: `test_pipeline_fresh_components_per_run`, `test_spec_engine_no_agent_config_leak`, `test_one_analyst_failure_does_not_kill_others`, `test_subprocess_killed_on_cancellation`, `test_circuit_breaker_single_probe_in_half_open`.

### Wave 1B: LLM Parsing Standard (Decision D)
**Goal:** Replace 6 ad-hoc JSON extractors with single `safe_llm_json()` utility.

**Changes:**
1. `src/keystone/llm/parsing.py` (NEW) -- `ParseError(Exception)` with `.message` and `.raw_text`. `safe_llm_json(text, required_keys, expect_list, bool_keys)` strips markdown fences, extracts JSON via bracket-counting, validates, coerces bool keys. `parse_llm_bool(value)` for True/False/"true"/"false"/"yes"/"no"/1/0.
2. 13 files modified to use `safe_llm_json` instead of ad-hoc extractors:
   - `specification/_prompts.py` -- `extract_json` delegates to `safe_llm_json`
   - `specification/engagement_classifier.py` -- `.get()` instead of bare `[]` access
   - `specification/intent_clarifier.py` -- 4 bare key accesses replaced
   - `specification/priority_scorer.py` -- bare key accesses replaced
   - `specification/task_generator.py` -- bare key accesses replaced
   - `specification/validator.py` -- `bool()` replaced with `parse_llm_bool()` (fixes `bool("false") == True` bug)
   - `research/research_agent.py` -- `_extract_json_text` replaced
   - `deliberation/analyst.py` -- `json.loads` replaced
   - `deliberation/aggregator.py` -- both `json.loads` calls replaced, added `logger.warning` on consistency_check parse failure
   - `deliberation/wwhtb.py` -- `json.loads` replaced
   - `evaluator/layer1_deterministic.py` -- `_parse_json_array` replaced with `safe_llm_json(expect_list=True)`
   - `evaluator/layer3_rubric.py` -- `ParseError` instead of silent score-50 default
   - `evaluator/sprint_contract.py` -- `_parse_contract_json` replaced

**Key correctness fixes:** `bool("false") == True` bug in MECE validator eliminated. Silent score-50 fabrication in rubric evaluator eliminated.

**Test changes:** `tests/unit/llm/test_parsing.py` (NEW, 23 tests). `tests/unit/specification/test_validator.py` -- added `test_mece_validator_string_false_fails_dimension`.

### Wave 1C: Citation Identity Foundation (Decision A producers + B prerequisites)
**Goal:** Dual-layer citation identity, partial-claim salvage, error recovery wiring, HITL event emission.

**Changes:**
1. `src/keystone/models/research.py` -- `FindingClaim` gets `claim_id: str | None = None` and `citation_ids: list[str] = []`. `StructuredFinding` gets `dropped_claims: list[dict] = []`.
2. `src/keystone/models/citations.py` -- `Citation` (FROZEN) gets `metadata_hash: str | None = None` (with SHA-256 validator) and `merged_from_ids: list[str] = []`. New `CitationAlias` model. `CitationManifest` gets `aliases: list[CitationAlias] = []`.
3. `src/keystone/research/research_agent.py` -- Engagement-unique source-instance citation IDs via `_make_source_instance_id()`. Shallow mode uses `citation_refs` pattern (SRC-NNN references in synthesis prompt). Deep mode keeps per-claim `sources` array (intentionally asymmetric -- documented in code).
4. `src/keystone/research/finding_writer.py` -- Per-claim `claim_id` minting. `citation_ids` derived from embedded citations. Partial-claim salvage: valid claims preserved, invalid ones recorded in `dropped_claims` with reasons. Zero valid claims raises `FindingValidationError` (not silent COMPLETE).
5. `src/keystone/citation/processor.py` -- `CitationProcessorResult` model with `manifest` and `canonicalized_findings`. `get_result()` method. Alias map built during processing. `_rewrite_findings_to_canonical()` rewrites claim `citation_ids` from source-instance to canonical.
6. `src/keystone/citation/dedup.py` -- `deduplicate_with_aliases()` populates `merged_from_ids` during merge. Emits `CitationAlias` per group member.
7. `src/keystone/contracts.py` -- `CitationProcessorContract` Protocol updated with `get_result()`.
8. `src/keystone/pipeline/orchestrator.py` -- `ErrorRecovery(llm_factory=self._llm_factory)` passed to `AgentPool` in `_build_components()`.
9. `src/keystone/research/agent_pool.py` -- Accepts and passes through `error_recovery` parameter.
10. `src/keystone/hitl/gate.py` -- `event_collector: list | None = None` parameter (backward-compatible). Emits `ReviewGateCreated`, `ReviewGateApproved`, `ReviewGateModified`, `ReviewGateRejected`.

**Known gap:** `ReviewDecisionSubmitted` event is defined in `events.py` but has zero emission sites. Deferred to Wave 2B HITL instrumentation.

**Test changes:** `tests/unit/citation/test_processor.py` -- 4 new tests (alias map, canonical rewriting, task manifest, get_result guard). `tests/unit/research/test_finding_writer.py` -- 6 new tests (claim_id, citation_ids, salvage, all-dropped raises). `tests/unit/research/test_error_recovery.py` -- `test_error_recovery_uses_wired_llm_factory`. `tests/unit/hitl/test_gate.py` -- 4 new event emission tests. `tests/canary/test_architectural_guarantees.py` -- `test_source_instance_ids_unique_across_parallel_agents`.

---

## Known Issues & Deferrals (from prior reviews)

These were identified during the session's real-time and adversarial reviews and intentionally deferred:

1. **Evaluator fail-open on parse failure** (layer1_deterministic.py) -- `_fact_check()` returns `claims=[]` and `_numerical_consistency()` returns `parsed={}` on ParseError. Broken parsing looks like "nothing wrong." Deferred to Wave 2B governance.
2. **sprint_contract.py ParseError -> {} fallback** -- Falls back to task defaults on parse failure. Logs warning but produces seemingly valid contract. Deferred to Wave 2B quality flags.
3. **gestalt_overlay 0.0 fabrication** (layer3_rubric.py) -- Parse failure defaults to neutral 0.0 adjustment. Defensible but fabricated. Deferred.
4. **ParseError not retried** -- `retry_llm_call()` retries transport errors only. Parse failures after successful LLM call are not retried. Pre-existing. Deferred to Wave 2B error recovery.
5. **Concurrent `pipeline.run()` races** -- `self._result` and `_pending_components` are instance state. Two concurrent runs would race. Pipeline not designed for concurrent use. Not a regression.
6. **`_strip_fences` regex edge case** -- Triple backticks inside JSON string values would truncate. Practically irrelevant for LLM output.
7. **Citation ID agent_id truncation** -- 8-char truncation could collide for agents with similar prefixes. Mitigated but not eliminated.
8. **`ReviewDecisionSubmitted` not emitted** -- Defined in events.py, zero emission sites. Deferred to Wave 2B.
9. **Dead `HALF_OPEN` branch in `_record_failure()`** -- Unreachable after the probe was moved inline. Misleading but not buggy.
10. **`test_parse_failure_does_not_fabricate_score`** tests parsing utility only, not the actual scorer. Name is misleading.

---

## How to Review

### Getting the diff

Run this to see all source+test changes:
```bash
git diff 49b1183..HEAD -- src/ tests/
```

Or per-wave:
```bash
# Wave 1A
git diff 49b1183..9893a4d -- src/ tests/
# Wave 1B
git diff 9893a4d..884552f -- src/ tests/
# Wave 1C
git diff 884552f..1583d03 -- src/ tests/
```

### Parallel agent strategy

Spawn parallel agents for maximum coverage:

**Agent 1: Model & Frozen-Model Safety**
- Read ALL Pydantic models that were modified: `models/research.py`, `models/citations.py`
- Verify frozen models (`Citation`) are never mutated in-place anywhere. Grep for `.field =` assignments on Citation objects.
- Check that all new fields have defaults and don't break existing constructors.
- Grep for every construction site of `FindingClaim`, `Citation`, `StructuredFinding`, `CitationManifest` across the entire codebase. Verify none break.

**Agent 2: Concurrency & Error Handling**
- Review `circuit_breaker.py` lock semantics: is the HALF_OPEN probe truly single-caller? Can `BaseException` handling cause state corruption?
- Review `llm_client.py` subprocess cleanup: is `asyncio.shield(proc.wait())` correct? What about event loop teardown?
- Review `deliberation.py` gather fallback: does `return_exceptions=True` + zip ordering work correctly? What if the analyst list is empty?
- Review `orchestrator.py` `_pending_components` race: can two concurrent `run_with_events()` calls both consume the same injected components?

**Agent 3: Citation Identity & Provenance Chain**
- Trace the full citation lifecycle: creation in `research_agent.py` -> dedup in `dedup.py` -> alias map in `processor.py` -> canonical rewrite in `_rewrite_findings_to_canonical` -> downstream consumers.
- Verify source-instance IDs are truly engagement-unique. Can two agents produce the same ID?
- Verify the alias map is exhaustive: every source-instance ID must map to exactly one canonical ID. No orphans.
- Verify `merged_from_ids` correctly tracks which citations were merged.
- Verify `CitationProcessorResult.canonicalized_findings` has correct `citation_ids` after rewrite.

**Agent 4: Parsing & Error Propagation**
- Read `llm/parsing.py`. Test edge cases: empty input, whitespace, valid JSON without fences, nested fences, arrays, prose-with-embedded-JSON.
- For each of the 13 call sites, verify: (a) the correct `safe_llm_json` options are passed, (b) `ParseError` is caught or propagated appropriately, (c) no silent fallbacks were introduced.
- Check that `parse_llm_bool` covers all edge cases. What about `"TRUE"`, `"YES"`, `"1"`, `" true "` with whitespace?
- Verify the `bool("false") == True` bug is actually fixed in `validator.py`. Read the test.

**Agent 5: Test Coverage & Correctness**
- For EVERY new test, verify it tests what its name claims. Read the test body, not just the name.
- Check for tests that would pass even if the feature were broken (vacuous tests).
- Grep for the 20+ named tests from the design doc and verify each exists.
- Check that canary tests (adversarial, end-to-end style) actually exercise the runtime path, not just mock the entire thing.
- Run `git diff 49b1183..HEAD -- tests/` and review every test change.

### What to challenge

1. **Does the implementation match FINAL-DECISIONS-v2.md?** Read the design doc for Decisions A, D, and E. Cross-reference every "Modified Files" table entry against what was actually changed.

2. **Are there files the design doc says to modify that were NOT modified?** The design doc lists files per wave. Were any skipped?

3. **Are there files that WERE modified but SHOULDN'T have been?** Scope creep or drive-by changes.

4. **Does the partial-claim salvage actually work?** Trace: LLM returns 5 claims, 2 are invalid. Does the finding contain 3 valid claims + 2 dropped? Does the finding status say PARTIAL? What if 0 are valid? What if ALL are valid?

5. **Is the citation_refs pattern correct?** In shallow mode, the synthesis prompt should reference citations by SRC-NNN, and the LLM's response should include `citation_refs` that map back. Trace this end-to-end.

6. **Error recovery wiring -- is it complete?** `Pipeline -> AgentPool -> ResearchAgent -> ErrorRecovery`. Does `ErrorRecovery.llm_factory` actually get used for fallback? What tier does it fall back to?

7. **HITL event emission -- backward compatible?** Existing callers of `create_and_wait_for_gate()` that don't pass `event_collector` should work unchanged. Verify with grep.

8. **Cross-wave interactions.** Wave 1B modified `research_agent.py` (safe_llm_json). Wave 1C modified it again (citation IDs, citation_refs). Are the changes compatible? Any merge conflicts resolved incorrectly?

### Output format

For each finding:
- **Severity:** BLOCKER / DESIGN_CONCERN / WARNING / NOTE
- **Wave:** 1A / 1B / 1C
- **File and line number**
- **What you found** (specific, with evidence)
- **Why it matters**
- **What should change** (one sentence)

Do NOT fix anything. Report only. Be adversarial -- assume the implementation is wrong until you prove otherwise.
