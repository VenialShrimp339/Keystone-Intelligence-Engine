# CAPSTONE-PLAN-v2.md Internal Consistency Audit
*Conducted: 2026-04-04 | Post-synthesis (17 changes, +243 lines)*

## Verdict: PASS with 3 corrections applied, 6 evidence caveats documented

The plan is build-ready. No architectural contradictions or structural incoherence found. Three stale terminology issues were corrected in-place. Six evidence representation issues are documented below for intellectual honesty but none change architectural decisions.

---

## 1. Cross-Reference Scan

### Terminology Consistency

| Term | Expected | Status |
|------|----------|--------|
| "eight-dimension" → "ten-dimension" | All references updated | CLEAN. Zero occurrences of "eight-dimension" remain. Section 5.3 header updated. Rubric tables show 10 dimensions throughout. |
| "Rejection Library" → "Observation Library" | Historical references preserved, active references updated | CLEAN. Three remaining "Rejection Library" mentions (lines 763, 1178, 1267) are historical ("expanded from Rejection Library") -- correct usage. All active references use "Observation Library." |
| "Structured debate" → "Independent parallel analysis + structured aggregation" | L1.5 redesign reflected | CORRECTED. Two stale references found and fixed: (1) Line 18: "adversarial multi-perspective debates" → "independent parallel analyses with structured aggregation". (2) Line 300: "deliberation and debate" → "deliberation and analysis" in Task-vs-Job table. One remaining historical reference (line 353) correctly describes the OLD design being replaced. |
| Architecture diagram matches prose | Diagram reflects all synthesis updates | CLEAN. Diagram (lines 32-96) shows: CitationProcessor between L1 and L1.5, "Five-layer eval stack" and "10-dimension rubric" in L4, "Observation Library" in L4 and META, "Independent parallel analysis + structured aggregation" in L1.5. All match prose. |
| Section numbering | Sequential and correct | CLEAN. Sections 1-13 plus Appendices A-B. No gaps or duplicates. |
| Handoff contract table | Reflects CitationProcessor stage | CLEAN. Table (lines 114-121) includes Research Agent → CitationProcessor → Deliberation chain with correct quality gates. |

### Additional Cross-Reference: UNIFIED-SYNTHESIS.md
- Line 330: "8-dim rubric" → CORRECTED to "10-dim rubric"

---

## 2. Evidence Spot-Check (5 Highest-Impact Changes)

### Change 2: Deliberation Redesign (L1.5)
**Sources cited:** C2 (Prompt 11), D2 (Prompt 15), C1 (Prompt 10)

| Claim | Verified? | Issue |
|-------|-----------|-------|
| NeurIPS 2025 Spotlight: debate forms martingale | Yes, with caveat | The theorem proves debate adds noise without directional improvement (expected value unchanged). Saying "more rounds consistently degrade performance" is the empirical finding, not the mathematical proof. The plan's usage on line 355 ("additional debate rounds consistently degrade accuracy") is the empirical claim, which is supported. Acceptable. |
| DMAD (ICLR 2025): methodological > persona diversity | Yes | **Attribution issue in PLAN-CHANGELOG.md only**: DMAD appears in D2 (Prompt 15), not C2 (Prompt 11). The plan itself (line 356) doesn't cite specific report codes, so no plan correction needed. Changelog Change 2 should list D2 as the DMAD source. |
| Wu et al.: majority pressure < 5% | Yes | Accurately represented. Prompt 11 confirms. |
| DeepMind: 17.2x error amplification | Yes | Present in C1 (Prompt 10) and D2 (Prompt 15). The figure applies specifically to the independent/unstructured topology. The plan correctly frames this as motivation for structured aggregation (which avoids this amplification). |

### Change 4: Five-Layer Evaluator Stack (L4)
**Sources cited:** A2 (Prompt 2), B4 (Prompt 9), D2 (Prompt 15), B1 (Prompt 6), D1 (Prompt 14)

| Claim | Verified? | Issue |
|-------|-----------|-------|
| SOS-Bench 152K data points, 96%/13% style-substance gap | Yes | Numbers confirmed in Prompts 2 and 9. **Caveat**: Prompt 2 notes SOS-Bench "does not directly test decomposed evaluation" -- the inference that decomposed scoring fixes this is the report author's interpretation, not the paper's direct finding. The plan's design (one prompt per dimension) is architecturally sound regardless. |
| 60-68% single-judge expert agreement | Partially | Confirmed in D2 (Prompt 15) with attribution to Yu, August 2025 survey. However, Prompt 2 (A2) explicitly labels this "Plausible but no traceable source." The plan should treat this as Credible, not Verified. Does not change the architectural decision (cross-model ensemble is warranted regardless). |
| CALM: 12 bias types | Yes | Confirmed in both Prompts 2 and 9. |
| Deloitte incidents: binary citation gate | Yes | Present in B1 (Prompt 6): "Deloitte incidents prove this dimension is existential." Correctly attributed. Not present in B4 (Prompt 9), but B1 is listed as a source in the changelog. |

### Change 9: Observation Library
**Sources cited:** D1 (Prompt 14), B3 (Prompt 8), D2 (Prompt 15), A3 (Prompt 3)

| Claim | Verified? | Issue |
|-------|-----------|-------|
| ECC instinct-to-skill pipeline: 100% tool call capture | Yes | Prompt 14 confirms verbatim. |
| Heuer's disconfirmation: quality defined by exclusions | Yes | Prompt 8 confirms. The synthesis slightly oversimplifies a convergent multi-source finding (Heuer + Tetlock + biological taste + Dreyfus) as just "Heuer's." |
| "Mind the Gap" ICLR 2025 Oral: saturation after 2-3 rounds | Yes | Prompt 15 confirms with paper citation. |
| Goodhart's Law at 19.3% | Yes, with framing note | Number confirmed in Prompt 3. The 19.3% is the frequency of Goodhart effects observed across sampled RL experiments, not a general failure rate. The plan uses this appropriately as motivation for multi-metric Pareto selection. |

### Change 10: Agent Isolation Strengthening
**Sources cited:** A4 (Prompt 4), A5 (Prompt 5)

| Claim | Verified? | Issue |
|-------|-----------|-------|
| AgentLeak: 68.8% leakage, 46.7% shared memory | Yes | Prompt 4 confirms. |
| No framework intercepts inter-agent messages | Yes | Prompt 4 confirms verbatim. |
| "50 tools vs 5 focused tools" Anthropic finding | Yes | **Not in Prompt 4 (A4) but IS in Prompt 5 (A5), line 97.** Changelog correctly cites A5. |
| Opus/Sonnet model mixing, 40% cost reduction | Yes | Prompt 4 confirms. |

### Change 11: Orchestration Architecture
**Sources cited:** A4 (Prompt 4), C1 (Prompt 10)

All claims verified. "No existing framework natively supports," "bolting isolation fails 46-69%," and "framework layer is thinning" all confirmed in Prompt 4.

---

## 3. Architectural Coherence

### Do the 17 changes work together as a system?

**CitationProcessor + Deliberation interaction:** COHERENT. The CitationProcessor (Change 1) produces a corroborated citation manifest with cross-agent corroboration scores. The redesigned Deliberation (Change 2) receives this manifest as input. The handoff contract (line 117) explicitly specifies this interface. The independent analysts in Phase 1 of Deliberation work from corroborated findings, not raw agent outputs.

**5-layer evaluator stack + 10-dimension rubric:** COHERENT. Layer 3 of the stack (Section 5.9, Prometheus 2) executes the 10-dimension rubric with one prompt per dimension. The three-pass architecture (Section 5.10) correctly references the 10 dimensions in Pass 1. The pre-rubric gates (Layers 1-2) operate independently of rubric dimensions.

**Observation Library + saturation-breaking:** COHERENT. Section 7.1 specifies five explicit saturation-breaking mechanisms (domain expansion, adversarial probing, deliberate hard cases, human review, multi-metric Pareto selection). These directly address the D2 finding about 2-3 round saturation. The three-category taxonomy (structural/analytical/judgment) maps to the evaluation stack layers that detect them.

**Cross-model evaluation + model mixing:** COHERENT. Section 5.11 mandates generator != evaluator model family. The model mixing strategy (Sonnet for L1 generation) combined with Prometheus 2 (different model family) for Layer 3 evaluation satisfies this constraint. Layer 5 ensemble requires cross-provider diversity.

**Claim-level handoff (Change 17) + CitationProcessor (Change 1):** COHERENT. CitationProcessor produces corroborated findings with citation manifests. Deliberation produces synthesized claims. The claim-level JSON (Section 4.4) includes source_chunk_ids and provenance_chain that trace back through the CitationProcessor. The data model supports end-to-end citation tracing.

**Task-type field (Change 13) + 10-dimension rubric (Change 5):** COHERENT. Section 3.6 specifies estimative vs. current task types. Section 5.3 notes type-specific weight profiles. The rubric dimensions are weighted differently per type (estimative → higher Calibrated Confidence weight; current → higher Source Quality weight).

### One minor gap identified:

The Evaluator's three-pass architecture (Section 5.10) specifies Pass 3 as "Observation Library negative-space scan." But the Observation Library is classified as Phase 2 build (Section 12.2, item 9). This means Phase 1's end-to-end pipeline test will run Passes 1-2 without Pass 3. This is acceptable (the plan already builds evaluator layers incrementally), but the implementation spec should note that Pass 3 is inactive until Phase 2.

---

## 4. Summary of Corrections Applied

| Location | What Changed | Why |
|----------|-------------|-----|
| CAPSTONE-PLAN-v2.md, line 18 | "adversarial multi-perspective debates" → "independent parallel analyses with structured aggregation" | Stale terminology from pre-synthesis design |
| CAPSTONE-PLAN-v2.md, line 300 | "deliberation and debate" → "deliberation and analysis" | Same |
| synthesis/UNIFIED-SYNTHESIS.md, line 330 | "8-dim rubric" → "10-dim rubric" | Rubric expanded to 10 dimensions |

## 5. Evidence Caveats (No Plan Changes Needed)

1. **Martingale claim**: Theorem proves no improvement; empirical data shows degradation. Plan uses the empirical framing, which is supported.
2. **SOS-Bench scope**: Does not directly test decomposed evaluation. The architectural inference (decompose = better) is sound but is the report author's interpretation, not the paper's.
3. **60-68% figure**: Should be classified Credible, not Verified. One source (A2) flags it as unverified. Doesn't change the architecture.
4. **DMAD attribution in changelog**: DMAD comes from D2, not C2. Changelog-only issue.
5. **Goodhart 19.3%**: Is a sampling frequency across RL experiments, not a general failure rate. Plan uses it appropriately.
6. **Heuer attribution**: The "quality defined by exclusions" finding is multi-source convergent, not Heuer alone. Minor.
