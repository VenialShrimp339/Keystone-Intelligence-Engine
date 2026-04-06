---
name: architecture
description: Deep reference for the Keystone Intelligence Engine 6-layer DPVI pipeline architecture, handoff contracts, component specifications, and design rationale. Use when making or evaluating architectural decisions, designing components, or mapping findings to pipeline layers.
---

# Keystone Architecture Reference

This skill provides the architectural detail needed to make and evaluate design decisions. For the full specification, always read the relevant sections of CAPSTONE-PLAN-v2.md directly.

## The DPVI Pattern

Decompose-Parallelize-Verify-Iterate. Independently discovered by four organizations building production AI systems. The convergent workflow pattern that eliminates the "jagged frontier" — when DPVI is applied, unreliable AI outputs become structurally reliable.

- **Decompose:** Specification Engine breaks research question into 15-50 discrete, independent tasks with explicit acceptance criteria
- **Parallelize:** Research Agents execute independently in strict isolation (no shared intermediate findings)
- **Verify:** Evaluator grades every output against sprint contracts and 10-dimension rubric
- **Iterate:** Failed sections regenerate; meta-layer evolves the system based on Observation Library

## Layer-by-Layer Specifications

### META-LAYER: Self-Improvement Loop
**Purpose:** Make the 20th engagement meaningfully better than the 5th.
**Components:** Observation Library (primary driver), Darwinian prompt evolution, trajectory storage, skill library growth, client calibration profiles.
**Key insight:** Self-improvement is driven by structured outcome analysis (Observation Library captures both successes and failures), not score optimization.

### LAYER 0: Specification Engine
**Purpose:** Translate vague questions into precise, executable RESEARCH.md specifications.
**This layer IS the system.** Quality ceiling = specification quality.
**Key operations:** Intent clarification → pre-flight scope validation → fit assessment → specification quality threshold → agent dispatch.
**Three-discipline model:** Must operate at Level 3 (Intent Engineering), not just Level 2 (Context Engineering). Before dispatching agents: What decision does this inform? What would a surprising finding look like? What constraints aren't stated?

### LAYER 1: Parallel Research Agents
**Purpose:** Fan out across data sources with strict isolation.
**Critical constraint:** Agents CANNOT access each other's intermediate findings. All convergence happens in Deliberation.
**Why isolation matters:** Cross-contamination causes confirmation bias. Agents investigating competing hypotheses must be isolated until Layer 1.5.
**Architecture:** Hub-and-spoke (not peer-to-peer). n(n-1)/2 coordination costs make P2P scale-prohibitive.

### LAYER 1.5: Deliberation
**Purpose:** Independent parallel analysis + structured aggregation to surface consensus, contested claims, and gaps.
**Analyst methodologies:** ACH, quantitative, adversarial, historical analogy, scenario planning (methodology-based, not debate roles; see DeliberationAnalystType enum).
**Requirements:** Mandatory steelmanning of opposing views. Blind evaluation (strip agent identifiers to prevent anchoring). Confidence mapping across claims. Explicit gap detection.

### LAYER 2: Content Structuring & Reasoning
**Purpose:** Skill-driven analysis using consulting frameworks. Sprint contracts define quality specs per section.
**Key concept:** Sprint contracts are negotiated BEFORE generation, not evaluated after. The generator and evaluator agree on what "good" looks like for each section before work begins.

### LAYER 3: Generation
**Purpose:** Produce Goldman-grade deliverables with citation enforcement and anti-slop principles.
**Goldman-grade test:** "Would a domain expert at a top firm call this solid on its own merits?" — not "impressive for AI."
**Anti-slop:** Every number traceable to a source. No unsourced assertions. Human reviewer evaluates analysis, not fact-checks data.

### LAYER 4: Evaluator
**THE most important component.** More important than any generator.
**10-dimension rubric** calibrated to consulting quality standards.
**Must catch:** Factual errors, analytical shallowness, missing perspectives, false precision, generic frameworks applied without adaptation, style-over-substance (well-formatted but analytically weak).
**Critical finding (SOS-Bench):** Naive LLM judges rate well-formatted wrong answers higher than poorly-formatted correct ones. Sarcasm causes 96% scoring loss vs factual errors causing only 13% loss. The Evaluator must be specifically hardened against this.
**Observation Library feed:** Every evaluation outcome (rejection or success) → structured entry (what happened, why, constraint or reinforced pattern) → permanent architectural constraint or validated approach.

## Handoff Contracts

Every pipeline boundary has explicit I/O/quality definitions:

| Boundary | Input | Output | Quality Gate |
|----------|-------|--------|-------------|
| Spec Engine → Research Agent | RESEARCH.md + task | Structured finding + citations | Spec quality threshold |
| Research Agent → Deliberation | Findings, confidence, gaps | Synthesized position, evidence map | All findings independently produced |
| Deliberation → Structuring | Confidence map, consensus/contested | Narrative outline, evidence mapping | Steelmanned opposing views present |
| Structuring → Evaluator | Section draft + sprint contract | Score + specific feedback | 10-dimension rubric |
| Evaluator → Self-Improvement | Observation entry (rejection or success) | Constraint encoding or pattern reinforcement | Root cause identified |

When output quality is low, trace backward through these contracts to diagnose exactly which handoff degraded the signal.

## Design Principles for Component Decisions

When evaluating any tool, framework, or architectural choice:

1. **Does it enforce quality structurally or hope for compliance?** Structural > prompt-based.
2. **Does it compose with the pipeline or require rebuilding around it?** Composable > monolithic.
3. **Does it contribute to the Observation Library / self-improvement loop?** Compounding > static.
4. **Is it model-agnostic in principle?** (Even if we use frontier models in practice.)
5. **Does it make the system debuggable?** (Trace failures to specific handoff contracts.)
