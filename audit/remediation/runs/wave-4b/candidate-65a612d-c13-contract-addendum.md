# Candidate 65a612d C-13 Contract Addendum

- Baseline commit: `6406e46`
- Candidate parent: `6406e46`
- Candidate commit: `65a612d`
- Addendum role: retrospective authority note for truthful C-13 interpretation during Batch 2 reconcile
- Scope rule: this addendum does not widen the historical Wave 4B code surface

## Why This Addendum Exists

The original C-13 memo blended two layers in one recommended-contract sentence:

1. Step 4 schema and prompt recovery inside the current intent-clarifier seam
2. deeper downstream structural propagation of that signal into later specification or task-generation logic

`W4D-1` correctly identified that blend as the blocker. The Wave 4B setup transcribed the seam-local layer, but the blended memo wording could also be read as requiring later downstream handoff surfaces that were never part of the historical `65a612d` write set.

This addendum records the narrower historical reading that is actually supported by the cleared `65a612d` file surface.

## Addendum-Backed Contract

### Layer 1: Seam-local Step 4 recovery (`C-13A`)

For historical Wave 4B interpretation, `65a612d` contemporaneously supports only this layer:

- `src/keystone/specification/prompts/intent_clarification.md` explicitly requires `evidence_would_change`
- `src/keystone/specification/intent_clarifier.py` adds `evidence_would_change` to `IntentClarificationResult` and preserves it in the returned model
- `tests/unit/specification/test_intent_clarifier.py::TestIntentClarifier::test_result_includes_evidence_would_change` verifies that the Step 4 signal is no longer discarded at the intent-clarifier seam

### Layer 2: Downstream structural propagation (`C-13B`)

The memo also described a deeper layer: forwarding `evidence_would_change` into later anti-confirmatory framing or task-generation guidance through downstream structural carriage beyond the current intent-clarifier seam.

`65a612d` did not include that layer as code scope. Its exact committed surface did not touch:

- `src/keystone/specification/spec_engine.py`
- `src/keystone/specification/task_generator.py`
- `src/keystone/models/research.py`

No named proof artifact in the cleared `65a612d` packet demonstrates end-to-end downstream propagation of `evidence_would_change` through `ResearchSpec`, `SpecificationEngine`, `TaskGenerator`, or equivalent downstream surfaces.

## Historical Reading

Authoritative historical reading for Batch 2 reconcile:

- cleared Wave 4B candidate `65a612d` supports `C-13A`
- cleared Wave 4B candidate `65a612d` did not include `C-13B` as code scope
- no `65a612d` clearance artifact may be read as contemporaneous proof that `evidence_would_change` flowed end-to-end through downstream specification or task-generation logic

## Boundary Guardrails

- The `src/keystone/specification/prompts/task_generation.md` edit in `65a612d` remains part of `C-8/C-14` tool-selection guidance, not proof of C-13 downstream structural propagation.
- This addendum supersedes any broader unqualified C-13 closure wording elsewhere in the `65a612d` packet family.
- `W4D-1` should be rerun against this addendum-backed authority layer rather than by retroactively widening the historical Wave 4B write surface.
