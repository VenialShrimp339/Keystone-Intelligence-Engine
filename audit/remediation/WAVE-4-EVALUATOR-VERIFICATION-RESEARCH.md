# Wave 4 Evaluator Verification Research

*Date: 2026-04-12 | Scope: C-11, C-15 | Purpose: freeze the evaluator-verification boundary so Wave 4B can fix the wrong verification object without pretending full claim-support verification already exists*

---

## Purpose

This memo covers the Wave 4 research tranche for:

- `C-11`: Eval-L2 claim-support verification design
- `C-15`: Eval-L1 snippet-sufficiency / verification-object design

The goal is not to widen the evaluator stack opportunistically.
The goal is to compare the feasible options, freeze the minimum snippet-quality policy, define the Phase 1 / Wave 4B boundary, and explicitly mark where a true claim-support verifier becomes a new capability rather than a prompt tweak.

## Accepted Boundary

- Baseline runtime: cleared Wave 3B commit `5cc9585`
- Current evaluator reality:
  - `Layer1Evaluator` already performs a weak fact-check proxy using `title + publication + content_snippet`
  - `Layer2CitationGate` checks citation existence, DOI validity, and URL liveness, not whether a citation supports the attached claim
  - there is no dedicated claim-support verification stage between Layer 2 and Layer 3
- The 4B-ready slice may stay inside the existing evaluator stack.
- This memo does **not** authorize:
  - source fetching at evaluation time
  - a new evaluator stage or new agent without an explicit controller checkpoint
  - pretending title-only or metadata-only citation text is a reliable verification object
  - solving the separate D-3a policy question for citations that have neither DOI nor URL

Any design that requires new source-fetch infrastructure, new stage boundaries, or a dedicated claim-support agent must be labeled `new capability` and kept out of Wave 4B.

## Runtime Consumer Summary

| Item | Observed problem | Runtime consumer | Recommended classification | Dependency note |
|---|---|---|---|---|
| `C-11` | Citation existence is checked, but claim-to-source support is not reliably established | `src/keystone/evaluator/layer2_citation_gate.py`, `src/keystone/evaluator/evaluator.py`, future claim-support verifier surface | `new capability` | A real solution needs a claim-support object or stage, not just stricter DOI/URL checks |
| `C-15` | Layer 1 treats title/publication metadata and thin snippets as if they were meaningful evidence text | `src/keystone/evaluator/layer1_deterministic.py`, `src/keystone/evaluator/prompts/fact_decomposition.md`, `src/keystone/evaluator/evaluator.py` | `existing-seam code` | Safe if the fix stays inside the current evaluator stack and does not fetch new source content |

## C-11: Claim-Support Verification Design

### Observed problem

- Source artifact: `audit/remediation/round-3/CONTENT-SYNTHESIS-v2.md` `C-11`
- Live code surfaces:
  - `src/keystone/evaluator/layer2_citation_gate.py`
  - `src/keystone/evaluator/evaluator.py`
- Related live behavior:
  - Layer 2 verifies whether a DOI resolves or a URL is live
  - Layer 1 does a weaker claim-to-citation proxy, but only against whatever citation text is available locally

So the current stack can reject a fabricated DOI, but it can still pass a real citation attached to an unsupported claim if the supporting object is weak or absent.

### Accepted boundary

- Claim-support verification is not the same as citation existence.
- A true fix must operate on a meaningful claim-to-evidence object.
- The 4B-ready slice must not fake a solution by tightening DOI or URL checks alone.
- If the design requires:
  - new source fetches
  - a new claim-support stage
  - a new verification agent
  then it is `new capability`.

### Feasible options

| Option | What it does | Strengths | Failure mode | Recommendation |
|---|---|---|---|---|
| `A. Snippet-based entailment inside the current stack` | Judge whether a claim is supported by the available `content_snippet` | Uses current data, localizes changes to evaluator surfaces | Still blind when snippets are thin, absent, or irrelevant; requires explicit insufficiency handling | Useful only after `C-15` fixes the verification object; still partial |
| `B. Similarity-only proxy` | Compare claim text to snippet text using lexical or embedding similarity | Faster and cheaper than a judge | Topic overlap is not evidentiary support; vulnerable to polished unsupported claims | Reject as the primary design |
| `C. Dedicated claim-support verifier / source reader` | Verify each claim against richer source text or fetched content | Best fidelity and clearest architecture | Requires a new stage or fetch capability | Defer as `new capability` |

### Recommended contract

`C-11` should be treated as a **post-Wave-4B capability design**, not a prompt-only rewrite.

The accepted future design target is:

1. Citation existence remains a Layer 2 gate.
2. Claim-support verification becomes a distinct support-check step that evaluates:
   - claim text
   - cited snippet or source excerpt
   - support status: `SUPPORTED`, `NOT_SUPPORTED`, `CONTRADICTED`, or `UNVERIFIABLE`
3. This support-check step must only run on evidence objects that pass the snippet-sufficiency policy defined in `C-15`.

What Wave 4B should **not** do:

- claim that live DOI/URL checks already solve claim support
- add a cosine-similarity shortcut and treat it as evidence verification
- bundle a new source-fetch subsystem into a "content tweak" wave

### Adversarial examples

| Failure mode | Why current existence checks miss it | Desired future behavior |
|---|---|---|
| Real citation, unsupported claim | DOI resolves, URL is live, but the source says something else or nothing relevant | Claim-support verifier returns `NOT_SUPPORTED` or `CONTRADICTED` |
| Real citation, irrelevant snippet | Citation exists, but the stored snippet is off-topic | Verifier returns `UNVERIFIABLE` rather than guessing |
| Authority laundering | Prestigious source is cited to inflate credibility without supporting the claim | Support check fails even though the source is real |

### Negative example

Bad implementation:

- treating DOI validity as proof of claim support
- switching Layer 2 from "existence" to "support" without a claim-level evidence object
- using similarity or keyword overlap as the only support test
- quietly widening the evaluator into a new fetch-and-read architecture under the label of "prompt polish"

### Regression test ideas

- future capability test: `tests/unit/evaluator/test_layer2.py::test_real_citation_unsupported_claim_does_not_pass_support_check`
- future capability test: `tests/unit/evaluator/test_evaluator.py::test_claim_support_stage_runs_after_existence_gate`
- future capability test: `tests/unit/evaluator/test_evaluator.py::test_irrelevant_snippet_yields_unverifiable_not_supported`

## C-15: Snippet Sufficiency And The Correct Verification Object

### Observed problem

- Source artifact: `audit/remediation/round-3/CONTENT-SYNTHESIS-v2.md` `C-15`
- Live code surface: `src/keystone/evaluator/layer1_deterministic.py`
- Live prompt surface: `src/keystone/evaluator/prompts/fact_decomposition.md`

Current state:

- Layer 1 builds citation text as:
  - `title`
  - `publication`
  - optional `content_snippet`
- if `content_snippet` is missing, the prompt still tries to judge support from title/publication metadata
- resulting claims can become `NOT_SUPPORTED` for the wrong reason:
  - not because the source refutes the claim
  - but because the system never had meaningful source text to verify against

That is a wrong verification object, not a legitimate failure.

### Accepted boundary

- Title plus publication metadata is never sufficient evidence text for factual verification.
- A thin or absent snippet should not silently become a failed fact check.
- The 4B-ready slice may update Layer 1 statuses and reporting, but must stay inside the current evaluator stack.
- The 4B-ready slice must **not** fetch source content on demand.

### Recommended contract

Wave 4B should adopt a **snippet-sufficiency policy** for Layer 1:

1. `title` + `publication` alone are metadata, not verification text.
2. A citation is `snippet-thin` when its evidence text is absent or too small to ground the claim.
3. Claims that rely only on snippet-thin citations should be marked `UNVERIFIABLE`, not `NOT_SUPPORTED`.

Minimum usable snippet rule:

- a citation is usable for claim verification only when it includes substantive source text beyond metadata
- practical minimum for the 4B-ready slice:
  - at least one full sentence or roughly 40+ words of source text
  - and not just the title repeated in excerpt form

Counting / reporting rule:

- `SUPPORTED` increments `facts_verified`
- `NOT_SUPPORTED` and `CONTRADICTED` increment `facts_failed`
- `UNVERIFIABLE` must be surfaced separately
  - preferred: an explicit count or field in the Layer 1 result surface
  - minimum acceptable fallback: evaluator feedback names the unverifiable count so it cannot disappear into a clean pass narrative

### Why this fits inside the current evaluator stack

- It does not require a new evaluator stage.
- It does not require network fetches.
- It corrects the verification object the current Layer 1 prompt already consumes.
- It creates a clean prerequisite for any later `C-11` claim-support verifier.

### Adversarial examples

| Failure mode | Current bad behavior | Required 4B behavior |
|---|---|---|
| Title-only academic citation | Claim becomes `NOT_SUPPORTED` because the title lacks the quantitative detail | Claim becomes `UNVERIFIABLE` |
| Empty snippet on a real report | Layer 1 counts a false failure | Layer 1 records insufficiency rather than a false negative |
| Thin snippet that names the topic but not the fact | System overstates verification confidence | Claim remains `UNVERIFIABLE` until a richer excerpt exists |

### Negative example

Bad implementation:

- continuing to treat metadata-only citations as valid verification text
- converting every thin-snippet claim into `NOT_SUPPORTED`
- hiding unverifiable claims by counting them neither as failures nor as explicit warnings
- "fixing" the problem by live-fetching source pages in Wave 4B without a controller checkpoint

### Regression test ideas

- `tests/unit/evaluator/test_layer1.py::test_title_only_citation_yields_unverifiable_not_not_supported`
- `tests/unit/evaluator/test_layer1.py::test_empty_snippet_does_not_increment_failed_fact_count`
- `tests/unit/evaluator/test_layer1.py::test_substantive_snippet_still_supports_claim_checking`
- `tests/unit/evaluator/test_evaluator.py::test_light_or_standard_evaluation_surfaces_unverifiable_claims`

## 4B-Ready Scope Vs Deferred Scope

### 4B-ready scope

- `C-15`: fix the verification object inside Layer 1 by adopting the snippet-sufficiency policy above and surfacing `UNVERIFIABLE` rather than false `NOT_SUPPORTED`

### Deferred as `new capability`

- `C-11`: true claim-support verification beyond citation existence
- any source-fetching verifier
- any new evaluator stage inserted between existing Layers 2 and 3

## Recommended Future Write Surfaces

### 4B-ready surfaces

- `src/keystone/evaluator/layer1_deterministic.py`
- `src/keystone/evaluator/prompts/fact_decomposition.md`
- `src/keystone/evaluator/evaluator.py`
- `src/keystone/models/evaluation.py` if an explicit `UNVERIFIABLE` count is added to Layer 1 results
- `tests/unit/evaluator/test_layer1.py`
- `tests/unit/evaluator/test_evaluator.py`

### Deferred capability surfaces

- `src/keystone/evaluator/layer2_citation_gate.py`
- future claim-support verifier module if the controller opens a new capability lane
- `tests/unit/evaluator/test_layer2.py`
- `tests/unit/evaluator/test_evaluator.py`

## Final Classification

- `C-15` is `existing-seam code` if it stays inside Layer 1 / evaluator result reporting and does not fetch new source content.
- `C-11` is `new capability`.

Wave 4B should carry only the `C-15` guardrail slice.
True claim-support verification must wait for a later capability checkpoint.
