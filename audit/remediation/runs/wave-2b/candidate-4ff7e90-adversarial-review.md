# Candidate 4ff7e90 Adversarial Review

- Baseline commit: `16e0bc7`
- Candidate parent: `c6eecbf`
- Target commit: `4ff7e90`
- Wave: `wave-2b`
- Verdict: `BLOCKED`

## Normalization Note

This is a retrospective in-folder wrapper for the canonical historical review text in [WAVE-2B-ADVERSARIAL-REVIEW.md](../../WAVE-2B-ADVERSARIAL-REVIEW.md).

It exists so the blocked `4ff7e90` packet chain under `audit/remediation/runs/wave-2b/` is self-contained for retrospective integrity review. It does not backdate this file into the original `4ff7e90` review process.

## Historical Source Summary

The canonical adversarial review concludes that candidate `4ff7e90` is `BLOCKED` because:

- LIGHT evaluation failures can disappear from coverage (`W2B-B01`)
- task priority and importance still derive from LLM list order instead of scored priorities (`W2B-B02`)
- the effective evaluator profile still does not drive runtime evaluator selection (`W2B-B03`)
- the new sprint-contract path can still silently collapse to a bare contract, with additional observability and test-integrity concerns noted as non-clearing risks

Use the canonical top-level review for the full line-by-line reasoning and probe evidence.
