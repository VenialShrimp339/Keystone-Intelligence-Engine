# W4B-2 Wave 4B Runtime Audit

## Scope

- Code truth reviewed only from detached worktree `/tmp/keystone-w4b2-CpI6OH` at committed target `65a612d`.
- Diff reviewed: `6406e46..65a612d`.
- Required Wave 4B authority docs were read from the main workspace because they are not present in the historical `65a612d` snapshot; they were used as memo/control material only, not as code truth.
- `W4B-1` is current `CLEARED` in `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml` and `audit/remediation/control-plane/ACTIVE-HANDOFF.md`, so this slice is not capped at `CONTINGENT`.
- Subagents used: none.

## Top-Line Verdict

`BLOCKED`

The committed runtime surface largely matches the claimed Wave 4B behavior, and the detached test matrix passed (`125 passed in 1.82s`). The blocker is narrower and load-bearing: the landed `C-15` snippet-sufficiency helper in [src/keystone/evaluator/layer1_deterministic.py](/tmp/keystone-w4b2-CpI6OH/src/keystone/evaluator/layer1_deterministic.py:32) rejects short full-sentence snippets that the Wave 4B verifier memo still treats as usable evidence text. That turns some directly supportive citations into false `UNVERIFIABLE` outcomes on the live Layer 1 path.

## Blocking Runtime Finding

### 1. `C-15` misclassifies short full-sentence evidence snippets as `snippet-thin`

- Runtime code: [src/keystone/evaluator/layer1_deterministic.py](/tmp/keystone-w4b2-CpI6OH/src/keystone/evaluator/layer1_deterministic.py:32)
  - `_has_usable_snippet()` only accepts a snippet when it is either `>= 40` words or sentence-like **and** `>= 12` words.
  - `_format_citation_for_prompt()` then rewrites anything else to `Snippet status: metadata only or snippet-thin` and hides the actual snippet text from the fact-check prompt.
- Memo contract: [audit/remediation/WAVE-4-EVALUATOR-VERIFICATION-RESEARCH.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-4-EVALUATOR-VERIFICATION-RESEARCH.md:145)
  - The approved minimum is “at least one full sentence or roughly 40+ words of source text,” not “at least 12 words if sentence-like.”
- Existing committed tests bracket only the extremes:
  - title-only is covered at [tests/unit/evaluator/test_layer1.py](/tmp/keystone-w4b2-CpI6OH/tests/unit/evaluator/test_layer1.py:177)
  - long substantive snippets are covered at [tests/unit/evaluator/test_layer1.py](/tmp/keystone-w4b2-CpI6OH/tests/unit/evaluator/test_layer1.py:208)
  - there is no committed regression for a short but complete sentence.

Detached runtime probe against the committed code path:

```text
facts_verified 0
facts_failed 0
facts_unverifiable 1
Snippet status: metadata only or snippet-thin
Content: No usable evidence text available for verification.
```

Probe setup:

- Citation snippet: `Revenue reached $50M in 2025.`
- Path exercised: `Layer1Evaluator.evaluate()` with the real `_has_usable_snippet()` / `_format_citation_for_prompt()` logic and a captured fact-decomposition prompt.

Why this is blocking:

- A short direct sentence can be enough to verify a claim, but the committed helper suppresses it before the verifier LLM sees it.
- That yields false `UNVERIFIABLE` counts in [src/keystone/models/evaluation.py](/tmp/keystone-w4b2-CpI6OH/src/keystone/models/evaluation.py:138) and false verification-gap messaging in [src/keystone/evaluator/evaluator.py](/tmp/keystone-w4b2-CpI6OH/src/keystone/evaluator/evaluator.py:243).
- This is a runtime correctness miss on one of the required checks, not just a memo-interpretation disagreement.

## Required Check Matrix

| required check | verdict | basis |
|---|---|---|
| `D-2` actionability runtime behavior | `CLEARED` | [src/keystone/evaluator/prompts/actionability.md](/tmp/keystone-w4b2-CpI6OH/src/keystone/evaluator/prompts/actionability.md:5) rewrites the dimension around decision-informing specificity, tradeoffs, thresholds, and recommendation-creep penalties; the detached matrix includes [tests/unit/evaluator/test_layer3.py](/tmp/keystone-w4b2-CpI6OH/tests/unit/evaluator/test_layer3.py:374). |
| shared `ScoredClaim` envelope preservation | `CLEARED` | [src/keystone/deliberation/analyst.py](/tmp/keystone-w4b2-CpI6OH/src/keystone/deliberation/analyst.py:168) keeps the shared envelope explicit and does not widen `ScoredClaim`; detached matrix includes [tests/unit/deliberation/test_analyst.py](/tmp/keystone-w4b2-CpI6OH/tests/unit/deliberation/test_analyst.py:125). |
| sprint-contract 10-dimension exposure and contradiction handling without the 10-claim cap | `CLEARED` | [src/keystone/evaluator/prompts/sprint_contract_generation.md](/tmp/keystone-w4b2-CpI6OH/src/keystone/evaluator/prompts/sprint_contract_generation.md:34) exposes all 10 dimensions; [src/keystone/evaluator/layer3_rubric.py](/tmp/keystone-w4b2-CpI6OH/src/keystone/evaluator/layer3_rubric.py:102) prevents Tier 1 de-emphasis below baseline; [src/keystone/deliberation/aggregator.py](/tmp/keystone-w4b2-CpI6OH/src/keystone/deliberation/aggregator.py:271) removes the `[:10]` truncation while preserving boolean `consistency_passed`; detached matrix includes [tests/unit/evaluator/test_sprint_contract.py](/tmp/keystone-w4b2-CpI6OH/tests/unit/evaluator/test_sprint_contract.py:172), [tests/unit/evaluator/test_layer3.py](/tmp/keystone-w4b2-CpI6OH/tests/unit/evaluator/test_layer3.py:281), and [tests/unit/deliberation/test_aggregator.py](/tmp/keystone-w4b2-CpI6OH/tests/unit/deliberation/test_aggregator.py:311). |
| tool-selection and template-enrichment runtime behavior inside the existing envelope | `CLEARED` | [src/keystone/specification/prompts/task_generation.md](/tmp/keystone-w4b2-CpI6OH/src/keystone/specification/prompts/task_generation.md:39) adds registered-tool heuristics only; [src/keystone/specification/task_generator.py](/tmp/keystone-w4b2-CpI6OH/src/keystone/specification/task_generator.py:60) still loads that prompt on the live task-generation path; [src/keystone/specification/template_registry.py](/tmp/keystone-w4b2-CpI6OH/src/keystone/specification/template_registry.py:34) enriches existing archetype prompts without widening tool/model envelopes; detached matrix includes [tests/unit/specification/test_task_generator.py](/tmp/keystone-w4b2-CpI6OH/tests/unit/specification/test_task_generator.py:288), [tests/unit/specification/test_template_registry.py](/tmp/keystone-w4b2-CpI6OH/tests/unit/specification/test_template_registry.py:126), and [tests/unit/specification/test_template_registry.py](/tmp/keystone-w4b2-CpI6OH/tests/unit/specification/test_template_registry.py:138). |
| `UNVERIFIABLE` handling for thin or absent snippets | `BLOCKED` | Title-only and long-snippet paths pass, but the committed helper rejects short full-sentence evidence as `snippet-thin`, creating false `UNVERIFIABLE` outcomes on the live Layer 1 path. |
| manifest compliance and denylist compliance | `CLEARED` | `git diff --name-only 6406e46..65a612d` matched the candidate manifest exactly; `comm -23` against the manifest surface returned empty, `comm -12` against the Wave 4B denylist returned empty, and no touches landed in `spec_engine.py`, `task_generator.py`, or `models/research.py`. |

## Runtime Proof Run

Detached matrix rerun from `/tmp/keystone-w4b2-CpI6OH`:

```bash
PYTHONPATH=src /Users/jackriddle/Desktop/Keystone-Intelligence-Engine/.venv/bin/pytest -q \
  tests/unit/deliberation/test_analyst.py \
  tests/unit/deliberation/test_aggregator.py \
  tests/unit/research/test_research_agent.py \
  tests/unit/specification/test_intent_clarifier.py \
  tests/unit/specification/test_task_generator.py \
  tests/unit/specification/test_template_registry.py \
  tests/unit/evaluator/test_layer1.py \
  tests/unit/evaluator/test_layer3.py \
  tests/unit/evaluator/test_sprint_contract.py \
  tests/unit/evaluator/test_evaluator.py \
  tests/e2e/test_mock_pipeline.py
```

Result:

```text
125 passed in 1.82s
```

Interpretation:

- The landed packet is broadly wired and load-bearing.
- The blocker survives that green matrix because the committed tests do not cover the short-full-sentence snippet edge between title-only metadata and 40+ word snippets.

## Memo-Conformity Uncertainty vs Runtime Failure

Memo/control uncertainty:

- The required Wave 4B control-plane and packet docs are not present in historical `65a612d`, so they had to be read from the current docs workspace as authority material only.
- That provenance wrinkle does not drive the verdict.

Runtime failure:

- The blocking disposition comes from the detached committed code path itself: [src/keystone/evaluator/layer1_deterministic.py](/tmp/keystone-w4b2-CpI6OH/src/keystone/evaluator/layer1_deterministic.py:32) suppresses a short full-sentence snippet that the approved Wave 4B `C-15` contract still allows as usable evidence text.

BLOCKED
