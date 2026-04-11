# Wave 2A: Citation Identity Completion

## How to use this file

Start a fresh Claude Code session:
```bash
cd /Users/jackriddle/Desktop/Keystone-Intelligence-Engine && claude --model 'claude-opus-4-6[1m]' --dangerously-skip-permissions
```

Then paste this prompt:
```
Read audit/remediation/WAVE-2A-SETUP.md and execute the team creation prompt inside it.
```

---

## Context for the new session lead

**What was done in Session 20 (Wave 1):**
- Wave 1A: Per-run lifecycle isolation, concurrency fixes (Decision E)
- Wave 1B: Unified LLM parsing -- `safe_llm_json` replaces 6 ad-hoc extractors (Decision D)
- Wave 1C: Citation identity foundation -- source-instance IDs, claim_id minting, partial-claim salvage, CitationProcessorResult with alias map, ErrorRecovery wiring, HITL event emission (Decision A producers + B prereqs)
- Codex adversarial reviews caught 2 regressions, both fixed: task manifest dedup regression (orchestrator now uses canonicalized findings), task generator validation gap (required_keys + non-empty check)

**What's already done from the Wave 2A deliverable list:**
- Orchestrator already uses `get_result()` for canonicalized findings (pulled forward into Session 20 Codex fix commit `38bba2a`). You do NOT need to change orchestrator.py for this item.

**What's added to Wave 2A scope from Codex review:**
- Mint fresh canonical IDs in `dedup.py` instead of reusing the dedup winner's source-instance ID. Currently `_merge_group()` keeps `best.citation_id` as the canonical ID, which means canonical IDs leak source provenance and are unstable across dedup winner selection. Mint IDs like `CAN-{engagement_id}-{group_index:03d}`.

---

## Team creation prompt

```
Read audit/remediation/decisions/FINAL-DECISIONS-v2.md and audit/remediation/BUILD-PROCESS.md.

Create an agent team for Wave 2A (Citation Identity Completion, Decision A part 2). Spawn 2 teammates:

- Implementer (use the kie-implementer agent type): Implement Wave 2A from FINAL-DECISIONS-v2.md. Changes are grouped into 5 tasks:

  TASK 1 -- Provenance model fields (models/confidence.py):
    - Add aggregated_claim_id: str | None = None to all 5 tier claim models (HighConfidenceClaim, ModerateConfidenceClaim, WeakConfidenceClaim, ContestedClaim, InsufficientClaim)
    - Add task_ids: list[str] = [] to all 5 tier claim models
    - Add provenance_index: dict[str, list[str]] = {} to ConfidenceMap
    - All optional with defaults. Run tests after.

  TASK 2 -- Aggregator provenance + corroboration fix (deliberation/aggregator.py):
    - Add aggregated_claim_id (mint UUID-based ID per aggregated claim)
    - Add task_ids (collect from input findings' task_id via the claims)
    - Fix corroboration_count semantics: currently set to citation count, should be cross-agent corroboration count
    - Run tests after.

  TASK 3 -- ConfidenceBuilder provenance + Deliberation wiring (confidence_builder.py, deliberation.py):
    - confidence_builder.py: copy aggregated_claim_id and task_ids from AggregatedClaim into tier claims. Build provenance_index on ConfidenceMap.
    - deliberation.py: pass manifest into aggregation call so aggregator can access canonical citation info. Update deliberate() to use canonicalized findings if available.
    - Run tests after. Named test: test_confidence_map_claims_carry_task_provenance.

  TASK 4 -- Mint fresh canonical IDs + metadata_hash migration (dedup.py, hash.py, citation/__init__.py, wiki_builder.py, engagement_store.py, content_hasher.py, wiki_schema.py):
    - dedup.py: _merge_group() should mint a fresh canonical ID (e.g., CAN-{engagement_id}-{group_hash[:8]}) instead of reusing best.citation_id. Update deduplicate_with_aliases() accordingly. The winner's source-instance ID becomes an alias like all others.
    - hash.py: functions that compute url:title hashes should write to metadata_hash, not content_hash. content_hash reserved for actual content hashes.
    - citation/__init__.py: update re-exports if needed.
    - wiki_builder.py: use metadata_hash for metadata hashes.
    - engagement_store.py: update content_hash references where they mean metadata.
    - content_hasher.py: update verification logic.
    - wiki_schema.py: update field references.
    - CRITICAL: content_hash has 50+ references across the codebase. Grep before and after. Do NOT break existing code that correctly uses content_hash for actual content.
    - Run tests after each file.

  TASK 5 -- PostSynthesisVerifier contract + orchestrator provenance filtering + renderer gating:
    - Define PostSynthesisVerifierContract Protocol in contracts.py (interface only, implementation is Wave 3).
    - Orchestrator: filter confidence_map by task provenance (only include claims from tasks that passed evaluation).
    - Named tests: test_renderer_drops_claims_from_failed_tasks, test_renderer_drops_claims_from_unevaluated_tasks.
    - Run tests after.

  Work through these one at a time. Run tests after each change. Report what you changed and what tests pass/fail after each one.

- Reviewer (use the kie-reviewer agent type, read-only): After EACH change the implementer makes, read the modified file and verify:
  1. Does the change match what FINAL-DECISIONS-v2.md specifies?
  2. Are there downstream files that reference the changed code and need updating?
  3. Do the test results confirm the change works?
  4. For the metadata_hash migration: grep for content_hash before and after to verify no references were missed or wrongly changed.
  Report findings to the implementer via message. If you find a BLOCKER, tell the implementer to stop.

Coordinate through the shared task list. Create one task per change (5 tasks total). The implementer claims and completes tasks. The reviewer verifies before the next task starts.
```

---

## What to watch for during Wave 2A

1. **content_hash migration is the highest-risk item.** 50+ references across the codebase. The migration is "use metadata_hash for url:title hashes, keep content_hash for actual content." Many existing references to content_hash actually mean metadata hashes. The implementer must read each file and determine which semantic is intended before changing anything.

2. **Provenance chain end-to-end.** After Wave 2A, you should be able to trace: FindingClaim.claim_id -> AggregatedClaim.aggregated_claim_id -> tier claim.aggregated_claim_id -> ConfidenceMap.provenance_index -> task_ids. This chain must be complete.

3. **Fresh canonical IDs break alias assumptions.** Wave 1C's alias map maps source-instance IDs to the winner's source-instance ID. After minting fresh canonical IDs, the alias map must map ALL source-instance IDs (including the winner) to the new canonical ID. Update the alias construction in `deduplicate_with_aliases()`.

4. **Orchestrator already uses canonicalized findings.** Don't re-do this work. The change was made in commit `38bba2a`.

5. **Deliberation currently receives original (non-canonicalized) findings.** After Wave 2A, deliberation should consume canonicalized findings from the citation processor result, not the raw agent findings. The orchestrator already does `findings = cit_result.canonicalized_findings` before passing to deliberation, so this may already work -- but verify.

---

## After Wave 2A completes

1. Run Codex adversarial review on the wave diff:
   ```bash
   git diff HEAD~1..HEAD -- src/ tests/
   ```
   Use `audit/remediation/WAVE1-FULL-ADVERSARIAL-REVIEW-PROMPT.md` as a template for the review prompt structure.

2. Fix any Codex-identified issues.

3. Commit the wave. Clean stopping point.

4. Start Wave 2B (Enforcement Model) in a new session. Wave 2B is the highest-risk wave -- it depends on everything from Waves 1A through 2A.
