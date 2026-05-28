# Session Prompt: Phase A — Infrastructure Unblock

## Orchestrator Disclosure

This prompt was written by an orchestrator session (Opus, 1M context) that read project tracking documents (`TODO.md`, `HANDOVER.md`, `SYNTHESIS-AND-PRIORITIES.md`, all four analysis files in `notes/analysis/`), key source files (`decomposer.py`, `task_generator.py`, `spec_engine.py`, `template_registry.py`, `orchestrator.py`, `evaluator.py`, `llm_client.py`, `config.py`), prompts (`task_generation.md`, `classification.md`, `actionability.md`), models (`research.py`, `tasks.py`), and the test scripts in `scripts/`. **The orchestrator did NOT read every file you will need to touch.** You will need to read the full implementation of files before modifying them.

**If you discover information that changes the plan** — a dependency the orchestrator missed, a file that's structured differently than assumed, an adjacent fix that's necessary to make the planned change work, or a better approach — **you are authorized to diverge from this plan.** However, you MUST:

1. Document every divergence in your final output under a `## Plan Divergences` section
2. For each divergence, state: what the plan said, what you did instead, and why
3. If you discover work that's related but out of scope, note it under `## Discovered Work` rather than doing it

---

## Context

This is the Keystone Intelligence Engine — a multi-agent consulting research pipeline. The pipeline runs L0 (Specification) → L1 (Research Agents) → CitationProcessor → L1.5 (Deliberation) → L4 (Evaluator) → Renderer.

**The pipeline has been run 3 times with real LLM calls (April 22-23, 2026).** Results:
- L0: Steps 1-5 succeeded. Task generation crashed — tries to generate all 15-16 tasks in ONE LLM call, times out.
- L1 deep mode: Complete success. 28 claims, 46 real sources.
- L4 Evaluator: Fact decomposition timed out — tries to decompose the entire research output in ONE LLM call.
- No intermediate artifacts are written to disk — everything is in-memory only, making debugging impossible.

**Branch:** `codex/owner-triage-normalization`
**Tests:** 1506 passing, 0 failing as of last check
**Uncommitted changes:** Timeout fix in `src/keystone/llm_client.py` (300s → configurable, default 600s) and `src/keystone/models/config.py` (new `claude_cli_timeout_s` field). These should be committed first.

## Your Tasks

### Task 0: Commit the timeout fix

The uncommitted changes in `llm_client.py` and `config.py` are a timeout increase from 300s to a configurable 600s default. Read the diffs, verify they're correct, and commit them.

### Task 1: Task generation chunking

**File:** `src/keystone/specification/task_generator.py`

**Problem:** `TaskGenerator.generate()` sends the entire issue tree (all 15-16 leaves) to one LLM call via the `task_generation.md` prompt. For complex questions, the output JSON is 15,000+ tokens and times out at 600s.

**Fix:** Split the issue tree leaves into batches of ~5, make one LLM call per batch, then merge the results. Specifically:

1. In `generate()`, partition the issue tree leaves into groups of 5 (configurable via a parameter or constant)
2. For each batch, build a prompt with only that batch's leaves and their priority scores
3. Call the LLM for each batch (sequentially is fine — these are already retried internally)
4. Merge the `tasks` arrays from all batches
5. Run `TaskDecomposition` validation (DAG check) on the combined result
6. Handle the case where cross-batch dependencies reference task IDs from other batches — the LLM won't know about tasks in other batches, so dependencies should only reference tasks within the same batch, or the merge step should resolve cross-batch ordering by priority

**Important:** The `task_generation.md` prompt currently says "For each leaf node in the issue tree, create a ResearchTask." The prompt sent to each batch should make clear that this is a subset of the full tree, and include the full question + engagement context so the LLM has framing.

**Tests:** Add tests in `tests/unit/specification/` that verify:
- A tree with 12 leaves produces 3 batches of (5, 5, 2)
- A tree with 4 leaves produces 1 batch (no unnecessary splitting)
- The merged TaskDecomposition passes DAG validation
- Priority ordering is preserved across batches

### Task 2: Fact decomposition chunking

**File:** `src/keystone/evaluator/layer1_deterministic.py`

**Problem:** `Layer1Evaluator._fact_check()` sends the ENTIRE research output (potentially 28 claims, 3,500 words, 46 citations) to one LLM call via `fact_decomposition.md`. The output JSON (one entry per atomic fact) can be 15,000-20,000 tokens. This times out on any non-trivial finding.

**Fix:** Chunk the output text into sections of ~5-8 claims, process each chunk independently, and aggregate results. Specifically:

1. Split the `output_text` into chunks. The natural split point is per-claim if the text is structured as claims, or by paragraph/section if it's narrative prose. Read the actual implementation to understand the input format.
2. For each chunk, build the `fact_decomposition.md` prompt with just that chunk's text and the relevant citations
3. Call the LLM for each chunk
4. Merge the fact-check results (concatenate the atomic-fact arrays)
5. Compute aggregate metrics (supported/unsupported/not-found counts) across all chunks

**Important:** Read `fact_decomposition.md` and the `_fact_check` method carefully before implementing. The citation texts are passed alongside the output text — each chunk should only receive the citations that are actually referenced in that chunk's text, not all 46 citations.

**Tests:** Add tests that verify:
- A finding with 3 claims produces 1 chunk (no unnecessary splitting)
- A finding with 15 claims produces multiple chunks
- Aggregate metrics are correct across chunks
- The existing test suite still passes

### Task 3: Process visibility — write intermediate outputs

**File:** Primarily `src/keystone/pipeline/orchestrator.py`

**Problem:** Every layer's output exists only in memory. When the pipeline crashes or produces bad output, there's no way to inspect what each layer produced without adding print statements.

**Fix:** After each major pipeline stage completes, write the intermediate output to `output/{engagement_id}/`. The orchestrator already has access to the engagement_id and all intermediate results.

Write these files:
- `output/{engagement_id}/l0_classification.json` — after Step 1
- `output/{engagement_id}/l0_intent_clarification.json` — after Step 2
- `output/{engagement_id}/l0_issue_tree.json` — after Steps 3-4
- `output/{engagement_id}/l0_tasks.json` — after Steps 6-7
- `output/{engagement_id}/l1_findings/{task_id}.json` — per-task after L1
- `output/{engagement_id}/citation_manifest.json` — after CitationProcessor
- `output/{engagement_id}/l15_confidence_map.json` — after Deliberation
- `output/{engagement_id}/l4_evaluation.json` — after Evaluator
- `output/{engagement_id}/final_brief.md` — after Renderer

**Implementation approach:**
- Read the orchestrator's `run()` method to understand where each stage's results are available
- The writes should be best-effort (don't crash the pipeline if a write fails — log a warning)
- Use `pathlib.Path` and `model_dump_json(indent=2)` for Pydantic models
- The output directory should be configurable via `PipelineConfig` or a constructor parameter, defaulting to `output/`
- Some intermediate results (like the classification and intent clarification) are currently internal to `SpecificationEngine.generate_spec()` and not exposed to the orchestrator. For these, either:
  - (a) Add file writes inside `spec_engine.py` itself (simpler, less clean), or
  - (b) Expand the `SpecificationGenerated` event or `EngagementSpec` to carry the intermediate data (cleaner, more work)
  - Choose (a) for this session — it's infrastructure, not architecture

**Tests:** Test that the output directory is created and files are written. Mock the filesystem if needed, or use `tmp_path` fixtures.

### Task 4: Validate

1. Run `ruff format` on all changed files
2. Run `pytest tests/unit/ -x --tb=short` — all 1506+ tests must pass
3. Run `ruff check src/ tests/`
4. Commit all changes with descriptive commit message(s)

## What NOT to do

- Do NOT modify any prompt content (`.md` files in `prompts/` directories) beyond what's structurally necessary for chunking
- Do NOT change `EngagementType`, `TaskCategory`, or any model enums — that's Phase B work happening in a parallel session
- Do NOT refactor the orchestrator's pipeline flow — just add file writes at the existing stage boundaries
- Do NOT add new pipeline events unless necessary for the visibility work

## Expected Output

When you're done, provide:
1. Summary of what was implemented
2. Test results (count passing)
3. Files changed
4. `## Plan Divergences` — any places you deviated from this plan and why
5. `## Discovered Work` — any related issues you found that should be addressed in future sessions
