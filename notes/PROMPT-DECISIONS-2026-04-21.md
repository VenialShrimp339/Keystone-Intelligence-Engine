# Prompt Audit Decisions — 2026-04-21

Owner decisions on findings from `notes/PROMPT-AUDIT-RESULTS.md`.
Each decision includes the rationale so future sessions understand
why, not just what.

## Context

- Owner: Jack Riddle, The Keystone Group (boutique consulting)
- Quality bar: "If I gave a team of McKinsey analysts a week to
  research this question, what would they find"
- Cost preference: quality over cost, with config toggle for
  per-user depth/cost tradeoff
- Pipeline status: never run end-to-end as of this date
- Use case: internal analytical tool, 15-20 runs per deliverable,
  output should be partner/client-ready quality

## Decisions

### 1. Expand L1.5 methodology prompts to 15-30 sentences each
**APPROVED.** Martingale finding (D1) means pipeline accuracy
depends on analyst independence. 2-3 sentence prompts produce
correlated output. Cost increase acceptable — L1.5 is 4 calls per
engagement, not 200. Config toggle can reduce to 2 analysts for
cheaper runs.

### 2. Add methodology-specific output fields to analyst output
**APPROVED.** If ACH doesn't output a diagnosticity matrix, there's
no way to verify it executed ACH. Output structure forces the
reasoning. Changes the Pydantic model but aggregator already handles
heterogeneous input.

### 3. Gestalt overlay: can it flip pass/fail?
**NO — gestalt informs score but cannot rescue a borderline failure.**
The geometric mean is the quality floor. A barely-passing report
shouldn't get +10 into pass territory. At MBB quality bar, borderline
= not good enough.

### 4. Tier 1 dimensions emphasizable through sprint contracts?
**YES.** A diagnostic engagement where intellectual honesty is
paramount should signal that. Floor gates still catch catastrophic
failures regardless of emphasis.

### 5. Unify confidence scales across L1 and L1.5?
**YES.** Three different taxonomies create silent mismatch. Align L1
to L1.5 five-tier system (>0.8 / 0.6-0.8 / 0.5-0.6 / <0.5 /
insufficient). Keep L4 ICD 203 as evaluation standard.

### 6. Judge fallback from max-confidence to median?
**YES.** Max-confidence picks the most aggressive analyst — wrong
default when parsing fails. Median is conservative and
mathematically neutral.

### 7. Completeness Tier 1 floor: 30 → 40
**APPROVED.** Likely an oversight, not calibrated. Missing key
coverage areas is a critical failure at MBB standard. Floor of 30
means "barely covers basics" can pass.

### 8. Narrative Coherence weight: 0.05 → 0.08
**APPROVED.** Take the 0.03 from Evaluative Surprise (0.05 → 0.02).
Narrative Coherence is Tier 1 but its weight makes it nearly
invisible in the composite. Evaluative Surprise is the least reliable
dimension (hardest for LLM judges). Weights still sum to 100%.

### 9. Deep research minimum claims: fixed 20 → proportional
**APPROVED.** "Produce claims proportional to the evidence found.
For a typical task, 15-30 claims; fewer is acceptable if evidence
base is narrow." Fixed floor forces padding, which is the opposite
of depth.

### 10. Priority scoring cost denominator?
**DEFERRED.** No empirical data yet to calibrate. Adding cost-based
deprioritization before knowing what "good" looks like risks
deprioritizing expensive-but-essential tasks.

## Implementation phases

**Phase A (no decisions needed):** Authority-marker instruction on
all 10 rubric prompts, absence report expansion, prompt-injection
line in deep research, hardcoded tool list → template variable,
externalize 8 L1.5 prompts to .md files.

**Phase B (decisions 1-6 above):** Methodology prompt rewrites,
synthesis prompt expansion, confidence band alignment, judge fallback
fix, Tier 1 emphasis in sprint contracts, gestalt post-pass/fail.

**Phase C (decisions 7-9 above):** Completeness floor, weight
adjustment, proportional claims, plus threshold calibration when
empirical data is available.
