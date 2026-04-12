# Wave 2A Final Deep Review

Date: 2026-04-11
Reviewer: Codex final deep review with parallel sub-reviewers
Baseline: `33695a7`
Target snapshot: `16e0bc7`
Scope: review the committed snapshot only, comparing `33695a7..16e0bc7`

## Review Scope Used

Reviewed the full `src/` + `tests/` surface changed in `33695a7..16e0bc7`, using the Wave 2A final deep review template and the required support docs. I inspected the committed diff directly, read the two unchanged support files called out by the template, ran the focused verification matrix, ran the targeted greps, and used parallel sub-reviewers for:

- manifest/rendering leakage
- provenance/corroboration path
- hash/test integrity
- commit hygiene

I evaluated the committed snapshot only and did not use the dirty working tree as review evidence.

## Findings

### 1. DESIGN_CONCERN
- **Severity:** DESIGN_CONCERN
- **Area:** corroboration semantics / render-time filtering
- **File and line number:** `src/keystone/pipeline/orchestrator.py:546-550`
- **What you found:** `_filter_confidence_map_by_passed_tasks()` rewrites every surviving claim's `corroboration_count` to `len(surviving_task_ids)`. But `Aggregator._derive_claim_provenance()` intentionally keeps `task_ids` anchored to the originating claim instead of widening them to all supporting tasks (`src/keystone/deliberation/aggregator.py:198-225`). That closes the failed-task leakage path, but it also means a legitimately corroborated claim will still be rendered with `corroboration_count == 1` whenever its own `task_ids` list has only its origin task, even if multiple passed agents independently found the same canonical source. The new regression coverage proves the leak-suppression case and codifies the collapse to `1` (`tests/unit/pipeline/test_orchestrator.py:1139-1164`), but there is no companion test for preserving `>1` when all supporting tasks pass.
- **Why it matters:** Wave 2A's blocker fix is in place, but the rendered corroboration number is still not a faithful measure of surviving independent support. It now avoids leakage by converting the metric into task-count, which underreports real corroboration in multi-pass shared-source cases.
- **What should change:** Preserve a render-time surviving-support count derived from manifest alias/agent provenance instead of overwriting `corroboration_count` with `len(task_ids)`.

### 2. NOTE
- **Severity:** NOTE
- **Area:** contract drift
- **File and line number:** `src/keystone/contracts.py:38-67`
- **What you found:** `PostSynthesisVerifierContract` still exposes a synchronous `filter_by_passed_tasks(confidence_map, passed_task_ids) -> ConfidenceMap` helper, while the authoritative Wave 2A decision doc specifies an async `verify(rendered_claims, manifest, provenance_index) -> VerificationResult` seam (`audit/remediation/decisions/FINAL-DECISIONS-v2.1.md:665-676`).
- **Why it matters:** This does not create a current correctness or safety bug, but it leaves the Wave 3 extension point misaligned with the governing design and raises the odds of code/doc drift when the real verifier is implemented.
- **What should change:** Align the protocol with the governing doc or explicitly revise the governing doc before the verifier lands.

## Areas Checked With No Issues Found

### Former blocker: renderer manifest leak

Checked:

- `src/keystone/pipeline/orchestrator.py:286-305`
- `src/keystone/pipeline/orchestrator.py:439-513`
- `src/keystone/pipeline/markdown_renderer.py:187-216`
- `tests/unit/pipeline/test_orchestrator.py:623-996`

Verified:

- Stage 6 now renders `passed_findings`, a filtered `ConfidenceMap`, filtered `evaluation_results`, and a filtered `render_manifest`.
- `_filter_manifest_by_findings()` prunes `citations`, `dead_urls`, `fabrication_flags`, `corroboration_pairs`, `aliases`, and `found_by_agents` to surviving findings/tasks before render.
- `MarkdownRenderer` only uses `manifest.citations` and `manifest.dead_urls` in the `Sources` section, so the prior full-manifest leak path is closed.
- The new renderer-gating tests assert the filtered manifest contents for failed-task, unevaluated-task, and shared-alias scenarios.

### Former blocker: dead corroboration / provenance logic

Checked:

- `src/keystone/deliberation/deliberation.py:129-157`
- `src/keystone/deliberation/analyst.py:90-112`
- `src/keystone/deliberation/aggregator.py:67-225`
- `src/keystone/deliberation/confidence_builder.py:45-85`
- `tests/unit/deliberation/test_aggregator.py:248-285`
- `tests/unit/deliberation/test_confidence_builder.py:306-390`

Verified:

- Canonical citation IDs survive into deliberation input because `extract_claims()` prefers `claim.citation_ids`.
- Aggregator provenance is now manifest-backed through alias/agent indexing rather than impossible same-index sibling grouping.
- `task_ids` stay anchored to the originating claim so failed-task support no longer widens renderable provenance.
- `ConfidenceMap.provenance_index` is built from aggregated claims and rebuilt after render-time filtering.

### Corroboration pair canonicalization

Checked:

- `src/keystone/citation/processor.py:138-151`
- `src/keystone/citation/processor.py:272-301`
- `tests/unit/citation/test_processor.py:164-211`

Verified:

- `CorroborationPair` IDs are rewritten through the alias map to canonical `CAN-*` IDs.
- Canonical self-pairs are dropped after alias rewriting.
- The added tests would fail if pair canonicalization regressed back to self-pairs or raw source-instance IDs.

### Hash semantics

Checked:

- `src/keystone/citation/dedup.py:124-173`
- `src/keystone/citation/processor.py:174-182`
- `src/keystone/models/citations.py:92-134`
- `tests/unit/citation/test_processor.py:259-336`
- `tests/unit/test_citation_dedup.py:149-223`
- `tests/integration/test_citation_processor_live.py:328-346`

Verified:

- `metadata_hash` is the `url:title` identity hash and is recomputed from the final canonical citation record.
- `content_hash` remains reserved for actual content provenance and is preserved when present.
- I did not find the earlier false `content_hash is None` assertion in the changed Wave 2A test surface.
- The replacement tests still prove the meaningful invariants, including DOI-merge stale-hash replacement and content-hash preservation.

### Test quality

Checked:

- The focused Wave 2A verification matrix
- The new regression tests in `tests/unit/pipeline/test_orchestrator.py`
- Provenance/canonicalization tests in `tests/unit/citation/test_processor.py`, `tests/unit/test_citation_dedup.py`, and `tests/unit/deliberation/test_aggregator.py`

Verified:

- The focused matrix passed: `118 passed, 1 warning in 3.59s`.
- The remaining warning is `PytestUnknownMarkWarning` for `pytest.mark.integration` in `tests/integration/test_citation_processor_live.py`; this is not a Wave 2A correctness issue.
- I did not find vacuous prefix-only assertions in the changed hash/canonicalization tests; the key semantics are asserted directly.

### Commit hygiene

Checked:

- `git show --stat --oneline 16e0bc7`
- `git diff --name-only 33695a7..16e0bc7 -- src/ tests/`
- `git log --oneline 33695a7..16e0bc7`

Verified:

- The committed review surface is 24 files and remains Wave 2A-scoped.
- The five commits in the range are all explicitly labeled Wave 2A.
- The working tree is very dirty, but I did not rely on it for review conclusions.

## Verification Matrix

Command run:

```bash
PYTHONPATH=src .venv/bin/pytest -q \
  tests/unit/deliberation/test_confidence_builder.py \
  tests/unit/deliberation/test_analyst.py \
  tests/unit/pipeline/test_orchestrator.py \
  tests/unit/citation/test_processor.py \
  tests/integration/test_citation_processor_live.py \
  tests/unit/test_citation_dedup.py \
  tests/unit/test_citation_hash.py \
  tests/e2e/test_mock_pipeline.py
```

Result:

- PASS
- `118 passed, 1 warning in 3.59s`

## Residual Risks

- Render-time corroboration still underreports legitimate multi-pass support because the filter currently rewrites the metric from `task_ids` rather than from surviving manifest-backed support.
- The post-synthesis verifier seam in `contracts.py` still does not match the governing `FINAL-DECISIONS-v2.1.md` contract.

## Follow-Up Items

- In Wave 2B or later, preserve leak-free render gating while keeping corroboration metrics tied to surviving independent support rather than surviving task count.
- Before implementing the real post-synthesis verifier, reconcile `src/keystone/contracts.py` with `FINAL-DECISIONS-v2.1.md`.

## Verdict

WAVE 2A CLEARED
