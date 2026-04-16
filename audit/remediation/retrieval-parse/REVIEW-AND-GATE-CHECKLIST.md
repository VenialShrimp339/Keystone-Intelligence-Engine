# Review And Gate Checklist

Date: 2026-04-14
Applies to: narrow Lane E article/PDF parse and evidence normalization

## Gate Split

This checklist separates:

- what must clear before the setup package may be promoted
- what must clear before the runtime worktree is opened
- what must clear before a candidate can be reviewed for clearance
- what remains intentionally out of scope until later bridge or Lane F work

Naming a gate here does not mean the gate is already cleared.
A gate counts only when the required review exists for the reviewed snapshot and records an explicit verdict.

## Mandatory Pre-Promotion Package Reviews

Later controller promotion of this setup package is blocked unless all of the following docs-only reviews are completed against the package snapshot:

1. scope and write-set review
2. stale-doc and conflict review
3. usefulness and end-of-day target sanity review
4. controller promotion review

Each review must record:

1. reviewer
2. reviewed snapshot
3. evidence inputs
4. explicit verdict
5. explicit statement on whether Lane H invariants remain preserved

## Pre-Open Provenance Checklist

Before the first code edit:

1. Worktree path is exactly `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-parse`.
2. Branch is exactly `codex/retrieval-mvp-parse`.
3. Worktree root commit is exactly `93a5ca8406dc0c46c96f0c6285f56ec0ab6601ea`.
4. Runtime truth is anchored to `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface` at `93a5ca8`.
5. The approved setup artifact path is recorded as `audit/remediation/retrieval-parse/NEW-LANE-SETUP-ARTIFACT.md`.
6. `git status --short` in the worktree is clean before the first code edit.
7. The main workspace remains docs-only.

## Candidate Review Packet

Each candidate must produce these files under `audit/remediation/runs/retrieval-parse/`:

1. `candidate-<commit>-implementation.md`
2. `candidate-<commit>-file-manifest.md`
3. `candidate-<commit>-parse-truth-matrix.md`
4. `candidate-<commit>-deterministic-parse-review.md`
5. `candidate-<commit>-evidence-normalization-review.md`
6. `candidate-<commit>-adversarial-review.md`
7. `candidate-<commit>-second-opinion.md`
8. `candidate-<commit>-review-synthesis.md`
9. `candidate-<commit>-blocked-or-cleared-checkpoint.md`
10. `parse-probe-results.json`

Each candidate packet must include these provenance fields:

1. `candidate_commit`
2. `candidate_parent_anchor`
3. `approved_setup_artifact`
4. `worktree_path`
5. `worktree_clean`
6. `branch`

## Required Test Matrix

These suites are mandatory and may not be substituted away:

1. `tests/unit/retrieval/test_parse_models.py`
2. `tests/unit/retrieval/test_artifact_loader.py`
3. `tests/unit/retrieval/test_article_parser.py`
4. `tests/unit/retrieval/test_pdf_parser.py`
5. `tests/unit/retrieval/test_evidence_normalizer.py`

Important: this matrix is not sufficient by itself.
The candidate must also prove deterministic parse behavior and preserved upstream artifact truth through the additional probe evidence below.

## Required Parse-Probe Evidence

The candidate packet must name and report these probes:

1. The same article artifact parses reproducibly into the same ordered section/paragraph locators.
2. The same PDF artifact parses reproducibly into the same ordered page/paragraph locators.
3. PDF parse output records parse confidence and warnings when extraction quality is degraded.
4. Evidence-normalization output preserves `artifact_id`, `canonical_url`, `content_hash`, `coverage`, and `source_family`.
5. No candidate diff touched frozen Lane H or Lane F surfaces.

At least one concrete article artifact and one concrete PDF artifact must be exercised from persisted Lane H style inputs.

## Clearance Gates

Before a candidate may clear the lane, all of these must be true:

1. Deterministic parse review is complete.
2. Evidence-normalization review is complete.
3. Adversarial review is complete.
4. Second opinion is complete.
5. Review synthesis is complete.
6. File manifest confirms no unresolved scope creep.
7. The exact named test matrix passed on the candidate snapshot.
8. The exact named parse probes passed on the candidate snapshot.
9. If graphify is available in the runtime worktree, graphify collateral was rebuilt after code-file changes and is either committed or explicitly classified; if graphify is unavailable, the candidate packet records that absence explicitly.
10. The candidate explicitly states that Lane H invariants remained unchanged.

## Later Gates That Stay Out Of Scope For Lane Open

These do not need to clear before narrow Lane E opens, but they must clear before any claim that the article/PDF retrieval layer is usable end-to-end on the canonical research path:

1. thin post-E internal bridge review
2. Lane F integration review
3. citation-schema migration review
4. SEC / EDGAR venue review
5. benchmark acceptance review
6. UI / reviewer-surface review

## Stop Conditions

Stop and return to the control plane if any of these happen:

1. A touched path falls outside the approved write set.
2. The lane starts widening into gateway, task-assignment, or fetch-contract work.
3. The lane starts widening into citation-schema or research-agent integration work.
4. The lane needs filing or paper support to justify article/PDF claims.
5. Repo state becomes unsafe to reconcile.
6. A review identifies a blocker that cannot be resolved inside the approved lane.

## Current Status

- setup package promotion: pending
- retrieval parse runtime lane open now: no
- end-to-end article/PDF retrieval layer cleared now: no
- later promotion eligibility rule: only if the required package reviews are completed and the controller explicitly promotes this package
