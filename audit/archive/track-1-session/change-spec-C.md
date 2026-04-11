# Change Specification C: Sections 7 and 12
*Subagent C | Changes #39–48 | 2026-04-05*

This file specifies all 10 assigned changes to CAPSTONE-PLAN-v2.md. The orchestrator applies these after reconciling with Change Specs A and B. Nothing in this file modifies the document directly.

---

## Summary of Changes

| # | Section | Title | Phase |
|---|---------|-------|-------|
| 39 | §7.1 | Reframe Observation Library as CBR system with R4 cycle | Phase 2 (interface in Phase 1) |
| 40 | §7.1 | Add 5-tier knowledge artifact hierarchy with dual-axis metadata | Phase 2 (schema in Phase 1) |
| 41 | §7.7 | Add three-type extraction: strategy tips, recovery tips, optimization tips | Phase 2 |
| 42 | §7.1 | Add flexon-based problem archetype tagging | Phase 2 |
| 43 | §12.0 | Remove "Claude Agent SDK for execution substrate" | Phase 1 |
| 44 | §12.0 | Add error recovery Layers 1-2 as Phase 1 requirement | Phase 1 |
| 45 | §12.0 | Add database state machine HITL as Phase 1 implementation | Phase 1 |
| 46 | §12.0 | Add 5 mandatory Day-1 coding standards for Temporal migration readiness | Phase 1 |
| 47 | §12.1 | Replace Academix with paper-search-mcp in server list | Phase 1 |
| 48 | §12.1 | Add Finnhub MCP for market data | Phase 1 |

---

## Change #39: Reframe Observation Library as CBR System with R4 Cycle

**MASTER-SYNTHESIS Reference:** Section 9, Change #39; Section 1 ("Orchestration Pattern"); Decision 6 rationale in analysis-10-specification-engine.md.

**Phase Classification:** [Phase 2] — with interface stub required in Phase 1.

**Phase Rationale:** The Observation Library is explicitly listed as Phase 2 item #9 in §12.2. However, Directive 5 ("build the architecture correctly but stage feature depth") requires that the CBR integration point be defined in Phase 1 so the Specification Engine can query it (or skip gracefully when empty). The full R4 implementation — including similarity retrieval, reuse adaptation, and population-level Retain — is Phase 2. The Spec Engine's entry-point hook must be wired in Phase 1 even when the library is empty.

**Location in CAPSTONE-PLAN-v2.md:** Section 7, subsection 7.1, around line 761–823. The change augments the existing §7.1 prose. It does not replace the three-tier category taxonomy or the JSON examples.

### What exists now:

```
### 7.1 The Observation Library: Primary Self-Improvement Engine `[SYNTHESIS UPDATE]`

The v1 plan described self-improvement through score optimization and Darwinian prompt evolution. The v2 plan added the Rejection Library. The v3 update expands this to a full **Observation Library** that captures all tool call outcomes — successes and failures — following ECC's instinct-to-skill pipeline...

The Observation Library is:
- **The primary input to self-improvement** — captures both positive patterns (reinforcement) and negative patterns (correction)
- **A compounding asset** — every observation makes the next project better
- **Transferable across engagement types** — a lesson about weak competitive analysis applies everywhere
- **The most durable thing the system creates** — survives model upgrades, architecture changes, team transitions
- **A real-time evaluation mechanism** — the negative-space scan in Pass 3 of the three-pass evaluation architecture (Section 5.10)
```

### What it should say:

Add the following subsection immediately after the five bullet-point list ending with "A real-time evaluation mechanism" and before the "Saturation-breaking mechanisms" paragraph. Tag with `[BATCH 2 UPDATE]`:

---

**`[BATCH 2 UPDATE]` The Observation Library as a Case-Based Reasoning System.** The Observation Library is not merely a passive log — it is an active retrieval system that the Specification Engine queries at the start of every engagement. The architectural paradigm is **Case-Based Reasoning (CBR)** with the R4 cycle (Aamodt & Plaza, "Case-Based Reasoning: Foundational Issues, Methodological Variations, and System Approaches," 1994):

- **Retrieve:** At Specification Engine entry (before hypothesis generation), query the library for structurally similar past engagements using pgvector similarity search against the problem description, engagement type, and problem archetype tag. The query seeds the hypothesis space with patterns that worked (or failed) in analogous prior cases.
- **Reuse:** The retrieved case(s) are adapted to the current context — not applied verbatim. The Spec Engine uses them as priors, not templates. A "network optimization under demand uncertainty" case from a hospital engagement informs an auto shop expansion engagement because the structural problem is the same, not because the domain matches.
- **Revise:** During the engagement, findings that diverge from retrieved cases update the working hypothesis. The revised solution is tracked in the orchestrator's `research-state.md` scratchpad.
- **Retain:** After the engagement concludes, the L4 Evaluator scores the trajectory, and new observations are encoded into the library following the three-type extraction taxonomy (see §7.7). High-confidence cross-engagement learnings are promoted to the cross-engagement knowledge base.

**Phase 1 implementation note:** The Observation Library does not exist in Phase 1. The Spec Engine's CBR query at entry must be optional/bypass-able when the library is empty. The integration point (the function call, the data schema, the response format) must be wired in Phase 1; the library is initialized with seed entries (known AutoGPT failure modes, consulting anti-patterns) before the first production engagement in Phase 2. This follows Directive 5: the interface is correct from Day 1; the feature depth is staged.

---

The "Observation Library is:" bullet list should be updated to add a sixth bullet:

- **An active retrieval system (CBR), not a passive log** — the Specification Engine queries it at engagement start via similarity search; retrieved cases seed hypothesis generation and agent configuration before any new research begins

### Preservations:

- All three-tier category taxonomy (Category 1/2/3) and the two JSON observation examples must remain unchanged.
- The five existing bullet points in the "The Observation Library is:" list must remain; the sixth bullet is an addition.
- The saturation-breaking mechanisms paragraph and all subsequent §7.x subsections are unchanged.

### Cross-section references:

- **Section 3 (Specification Engine):** Change #39 mandates an explicit CBR query step at Spec Engine entry. Changes #1–10 in the MASTER-SYNTHESIS (assigned to a different subagent) must include this integration point in the Specification Engine 10-step flow at Step 1 (Problem Framing). The two subagents' outputs must be consistent: §7.1 describes the CBR system; §3 describes where the Spec Engine calls it.
- **Section 12.2 (Phase 2 sequence):** §12.2 item 9 ("Observation Library infrastructure") remains Phase 2. No change to that line needed — the CBR framing adds precision without changing the phasing.

### Directive compliance:

- **Directive 5 (Build philosophy):** Compliant. The interface (CBR query hook at Spec Engine entry) is wired in Phase 1; the Observation Library itself is Phase 2 feature depth. This is exactly the "right interfaces, stage feature depth" pattern.
- **Directive 6 (FITFO Standard):** The CBR Retrieve step is the mechanism that operationalizes FITFO — cross-domain pattern retrieval enables the system to handle novel engagements using structural analogies from prior cases.
- **Directive 8 (Karpathy KBs):** The R4 cycle is fully compatible with the Karpathy compiled wiki pattern. The Retain step writes to the compiled wiki. The Retrieve step queries it via pgvector. No contradiction.
- **Directive 13 (Phase 1 depth staging):** The CBR Observation Library query at Spec Engine entry is listed in Directive 13 as deferred to Phase 2 ("CBR Observation Library query at Spec Engine entry — Observation Library doesn't exist in Phase 1"). This change resolves that tension by specifying that the *query hook* is Phase 1 (wired but bypassed when library is empty) while the *populated library* is Phase 2.

---

## Change #40: Add 5-Tier Knowledge Artifact Hierarchy with Dual-Axis Metadata

**MASTER-SYNTHESIS Reference:** Section 9, Change #40; analysis-05-engagement-taxonomy.md Finding #6 ("Five-tier knowledge artifact hierarchy from MBB knowledge management").

**Phase Classification:** [Phase 2] — Pydantic schema must be defined in Phase 1 before the component is built.

**Phase Rationale:** The Observation Library component ships in Phase 2. The schema, however, must be designed before build (Directive 5). The five-tier artifact type enum and dual-axis metadata fields should appear in `src/keystone/` Pydantic models in Phase 1 so the Phase 2 build has correct interfaces from the start.

**Location in CAPSTONE-PLAN-v2.md:** Section 7, subsection 7.1, immediately after the CBR system text added in Change #39, and before the "Saturation-breaking mechanisms" paragraph.

### What exists now:

The existing §7.1 has no structured knowledge artifact hierarchy. The three-tier failure taxonomy (Category 1/2/3) describes the severity of a single observation, not the type of artifact in the library.

### What it should say:

Add the following block immediately after the new CBR section added in Change #39, tagged `[BATCH 2 UPDATE]`:

---

**`[BATCH 2 UPDATE]` Knowledge Artifact Hierarchy.** Not all Observation Library entries are equally reusable. Drawing from McKinsey, Bain, and BCG knowledge management practice (synthesized from published methodology and PPK job descriptions, 2025–2026), the library implements a **five-tier artifact classification**:

| Tier | Artifact Type | Description | Reusability |
|------|--------------|-------------|-------------|
| 1 | Raw engagement output | Full trajectory record, frozen RESEARCH.md, unfiltered agent logs | Engagement-scoped only |
| 2 | Sanitized engagement summary | Client-anonymized findings, key decisions, evaluator scores | Cross-engagement retrieval |
| 3 | Reusable analytical template | Methodology extracted from high-scoring sections, abstracted to problem type | Cross-engagement, cross-client |
| 4 | Benchmark data | Validated numerical benchmarks (market sizes, growth rates, cost structures) with provenance and date | Cross-engagement, time-bounded |
| 5 | Published methodology | Skill file entries validated across 3+ engagements; permanent Observation Library canon | System-wide |

Tier 1 entries are never surfaced to agents from other engagements. Tiers 2–5 are retrievable. Tier 5 promotion requires L4 Evaluator validation across at least three separate engagements before an entry is classified as canonical.

**Dual-axis metadata.** Every entry from Tier 2 upward carries a dual-axis metadata schema with two primary axes and five secondary dimensions:

- **Primary axis 1 — Industry vertical:** Operations, Growth, M&A, Restructuring/Turnaround (from Jack's Directive #4 engagement scope) plus industry tags (Technology, Healthcare, Financial Services, Industrials, Consumer, etc.)
- **Primary axis 2 — Functional capability:** Competitive analysis, Market sizing, Regulatory landscape, Financial modeling, Operational diagnostics, Supply chain, Location optimization, etc.
- **Secondary dimension 1 — Problem archetype (flexon type):** See §7.1 flexon tagging (Change #42)
- **Secondary dimension 2 — Engagement analytical type:** SIZING, DIAGNOSTIC, EVALUATIVE, EXPLORATORY, STRATEGIC
- **Secondary dimension 3 — Geography:** Global, North America, EMEA, APAC, specific market
- **Secondary dimension 4 — Confidence level:** High (validated 3+ times), Medium (validated 1–2 times), Low (single observation)
- **Secondary dimension 5 — Date and recency:** Entry date, last-validated date; entries older than 18 months are flagged for re-validation before use

The Pydantic model for `ObservationEntry` should define these fields from Day 1. The CBR Retrieve step queries across both primary axes and the problem archetype dimension. Engagement-type similarity is the secondary filter.

---

### Preservations:

- The three-tier category taxonomy (Category 1/2/3: Structural/Analytical/Judgment failures) is orthogonal to the five-tier artifact hierarchy and must be preserved. Categories describe the nature of an observation; tiers describe its reusability level. They are separate classification dimensions on the same entry.
- The two JSON observation examples remain unchanged.

### Cross-section references:

- **src/keystone/ Pydantic models:** The `ObservationEntry` Pydantic model (or equivalent) must be created in Phase 1. This is a coding task, not a documentation task; it should appear in the Phase 1 implementation spec for Component #9 or as a standalone pre-build data model task.
- **Section 3 (Specification Engine):** The CBR Retrieve query must be executable against this schema. The dual-axis metadata plus problem archetype dimension are the retrieval inputs. Consistency with the Spec Engine's engagement classifier output (which produces the 5-type analytical taxonomy) is required.

### Directive compliance:

- **Directive 5 (Build philosophy):** Compliant. Schema defined in Phase 1, full implementation in Phase 2.
- **Directive 4 (Engagement scope):** The industry vertical axis directly maps to Keystone's full engagement scope (Operations, Growth, M&A, Restructuring/Turnaround).

---

## Change #41: Add Three-Type Extraction: Strategy Tips, Recovery Tips, Optimization Tips

**MASTER-SYNTHESIS Reference:** Section 9, Change #41; analysis-10-specification-engine.md Finding #6 and Change 4; analysis-05-engagement-taxonomy.md Change item 3.

**Phase Classification:** [Phase 2] — This is the Retain step of the CBR cycle; it runs after each completed engagement, which is Phase 2 behavior.

**Phase Rationale:** Extraction from completed engagements is a Phase 2 operation (requires completed engagements and a functioning Observation Library). The extraction taxonomy, however, should be defined in Phase 1 as part of the `ObservationEntry` schema so the Phase 2 build does not require schema changes.

**Location in CAPSTONE-PLAN-v2.md:** Section 7, subsection 7.7 ("The Instinct -> Skill Evolution Pipeline"), around line 901–909. The change augments the existing three-step pipeline (Recognition -> Articulation -> Encoding) without replacing it.

### What exists now:

```
### 7.7 The Instinct → Skill Evolution Pipeline

The three-step process for encoding constraints (Jones, "Rejection as Compounding Asset," Mar 10, 2026):

1. **Recognition** — notice what went wrong (Evaluator rejection, low-scoring section, client feedback)
2. **Articulation** — express it precisely enough to be machine-actionable (the step where most systems fail — they recognize problems but can't articulate them precisely enough for automated enforcement)
3. **Encoding** — embed it in the specification layer (skill file update, constraint addition, rubric refinement)

Temporary patterns (instincts) live in the Observation Library. Validated patterns that generalize across engagements are promoted to permanent skills. Patterns that don't generalize are pruned. This is more practical than ML-based self-improvement — it starts working immediately and compounds with every project.
```

### What it should say:

Retain the existing three-step Recognition -> Articulation -> Encoding pipeline. Append the following after the final paragraph, tagged `[BATCH 2 UPDATE]`:

---

**`[BATCH 2 UPDATE]` Three-Type Extraction Taxonomy (CBR Retain Step).** The Encoding step produces three distinct extraction types, based on trajectory-informed memory research (arXiv 2603.10600, March 2026). Each completed engagement generates entries across all three types via L4 Evaluator post-project analysis:

**Strategy tips** capture successful analytical approaches that should be repeated. Format: `{problem_type} -> {approach} -> {outcome}`. Example: "When assessing competitive moats in capital-intensive industries, cross-reference capacity expansion announcements with financing activities — this surfaced a 2-year first-mover window in three of four engagements." Strategy tips are the positive-pattern counterpart to the Rejection Library's original focus. They represent the R4 cycle's Reuse content.

**Recovery tips** capture failure modes and how they were corrected. Format: `{failure_signal} -> {root_cause} -> {correction}`. Example: "If the Evaluator flags Intellectual Honesty below 6/10 for a regulatory section, the root cause is almost always absence of the dissenting regulatory view — add an explicit regulatory risk scenario before finalizing." Recovery tips encode the Recognition and Articulation steps into machine-actionable form.

**Optimization tips** capture efficiency patterns — approaches that produced high-quality outputs with lower token cost or fewer research rounds. Format: `{task_type} -> {optimization} -> {quality_impact}`. Example: "For M&A target screening with 20+ candidates, a two-phase approach (Haiku for coarse filter, Sonnet for detailed analysis on top 5) reduced token cost 68% with no measurable quality drop on the 10-dimension rubric." Optimization tips are specific to the system's operational context and are not derivable from general LLM research.

All three extraction types use the same `ObservationEntry` Pydantic schema with a `tip_type: Literal["strategy", "recovery", "optimization"]` discriminator field. The CBR Retrieve step returns entries across all three types, ranked by structural similarity. The L4 Evaluator's post-project analysis pass is the primary extraction mechanism; human review gates provide additional signal for Category 3 (Judgment Failure) entries.

The three-step Instinct -> Skill Evolution pipeline maps directly to the R4 cycle's Retain step: Recognition = detecting the pattern, Articulation = classifying it as strategy/recovery/optimization and expressing it in the entry format, Encoding = writing it to the Observation Library and propagating it to skill files.

---

### Preservations:

- The existing three-step Recognition -> Articulation -> Encoding pipeline must remain. The three-type taxonomy elaborates the Encoding step; it does not replace the pipeline.
- The existing paragraph about instincts vs. permanent skills and the pruning process must remain.

### Cross-section references:

- **Section 7.4 (Autoresearch Ratchet):** Step 4 of the autoresearch ratchet ("Processes Observation Library entries — encodes new constraints into skill files and promotes validated patterns to permanent skills") is now specified concretely: "processing" means running the three-type extraction. No edit to §7.4 is required; this change makes the mechanism explicit in §7.7.
- **src/keystone/ Pydantic models:** The `tip_type` discriminator field must be part of the `ObservationEntry` schema defined in Phase 1.

### Directive compliance:

- **Directive 5 (Build philosophy):** Compliant. Schema designed in Phase 1; extraction pipeline runs in Phase 2.
- **Directive 13 (Phase 1 depth staging):** The full CBR Observation Library is Phase 2. The schema definition in Phase 1 is the correct architectural discipline.

---

## Change #42: Add Flexon-Based Problem Archetype Tagging

**MASTER-SYNTHESIS Reference:** Section 9, Change #42; analysis-05-engagement-taxonomy.md Finding #4 ("McKinsey flexons as cross-domain pattern matching primitives").

**Phase Classification:** [Phase 2] — explicitly listed as Phase 2 in Directive 13.

**Phase Rationale:** Directive 13 explicitly defers "Flexon-based problem archetype tagging" to Phase 2. The `problem_archetype` field must appear in the `ObservationEntry` Pydantic schema in Phase 1 (so Phase 2 doesn't require schema migrations), but the archetype classification logic and the associated retrieval patterns are Phase 2 features.

**Location in CAPSTONE-PLAN-v2.md:** Section 7, subsection 7.1, as a new named paragraph within the `[BATCH 2 UPDATE]` Knowledge Artifact Hierarchy block added in Change #40. Specifically, it expands the "Secondary dimension 1 — Problem archetype (flexon type)" entry with a full definition.

### What exists now:

No mention of flexons or problem archetype tagging exists anywhere in §7 of the current document.

### What it should say:

Replace the brief parenthetical "(See §7.1 flexon tagging (Change #42))" placeholder in Change #40's Secondary dimension 1 entry with the following inline expansion within the `[BATCH 2 UPDATE]` hierarchy block:

---

**`[BATCH 2 UPDATE]` Problem Archetype Tagging (Flexon Classification).** [Phase 2] Every Observation Library entry from Tier 2 upward carries a `problem_archetype` tag drawn from McKinsey's "flexon" framework (McKinsey Quarterly, published methodology), which classifies problems by their structural logic rather than their industry or domain:

- **Systems/networks flexon:** Problems involving interconnected nodes where value flows from network structure. Examples: hub-and-spoke logistics optimization, distribution network design, competitive ecosystem mapping, platform business model analysis. The auto shop expansion test case from Directive #4 falls here — "analyze optimal retail expansion locations" is structurally a network optimization problem regardless of the industry.
- **Machine/optimization flexon:** Problems where inputs transform to outputs via a process that can be optimized against measurable criteria. Examples: operational cost reduction, process throughput analysis, supply chain efficiency, manufacturing yield optimization.
- **Living system/evolutionary flexon:** Problems where the subject adapts to interventions, making static analysis insufficient. Examples: competitive dynamics (competitors respond to market entry), regulatory evolution, organizational change management, consumer behavior shifts.
- **Social/political flexon:** Problems driven by competing stakeholder interests, power dynamics, and legitimacy considerations. Examples: M&A integration, regulatory approval pathways, organizational restructuring, stakeholder alignment.

The flexon classification enables cross-domain retrieval that domain-only tagging cannot provide. An engagement about "hospital network expansion" and an engagement about "auto shop chain expansion" are different industries but share the systems/networks flexon — both retrieve the same pattern of analytical approaches, and the Observation Library correctly surfaces lessons across the industry boundary. This is the mechanism for the FITFO Standard (Directive #6): when the system encounters an unfamiliar domain, it retrieves structurally analogous cases from familiar domains.

**Phase 2 implementation note:** The `problem_archetype` field in the `ObservationEntry` schema is defined in Phase 1 as an `Optional[Literal["systems_networks", "machine_optimization", "living_system", "social_political"]]` field. Flexon classification logic (an Haiku-tier classifier applied to each entry at ingest) ships with the Phase 2 Observation Library build. Until then, the field is nullable and population is manual.

---

### Preservations:

- All other §7 content unchanged.
- The flexon framework does not replace the engagement type taxonomy (SIZING, DIAGNOSTIC, EVALUATIVE, EXPLORATORY, STRATEGIC) — it is orthogonal. The five-type taxonomy classifies the analytical mode; flexons classify the structural problem logic. Both dimensions appear on every entry.

### Cross-section references:

- **Section 3 (Specification Engine):** The CBR Retrieve step at Spec Engine entry can use the engagement's preliminary flexon classification (derived from the problem description) as a retrieval signal. This is a Phase 2 capability. The Spec Engine's engagement classifier (Phase 1) should output a preliminary flexon tag alongside the five-type classification.
- **src/keystone/ Pydantic models:** The `ObservationEntry` Pydantic model must include the `problem_archetype` Optional field. This is a Day-1 schema decision.

### Directive compliance:

- **Directive 6 (FITFO Standard):** Flexon tagging is the concrete mechanism for cross-domain FITFO. "What structurally similar problem has been solved in another domain?" is now answerable by querying the library filtered on `problem_archetype`.
- **Directive 13 (Phase 1 depth staging):** Fully compliant. Flexon tagging explicitly listed as Phase 2 deferred. Schema field defined in Phase 1, classification logic deferred.

---

## Change #43: Remove "Claude Agent SDK for Execution Substrate"

**MASTER-SYNTHESIS Reference:** Section 9, Change #43; Section 6 ("Claude Agent SDK Role" contradiction resolution); Decision 15; analysis-09-orchestration-patterns.md Finding #5.

**Phase Classification:** [Phase 1] — This is a correction to the current plan's orchestration stack description. The Agent SDK is not in the Phase 1 build; the plan should not say it is.

**Phase Rationale:** The plan currently describes Agent SDK as part of the core orchestration stack. This is incorrect framing that could mislead the Phase 1 builder. Correcting it is a Phase 1 action.

**Location in CAPSTONE-PLAN-v2.md:** Section 12, subsection 12.0, the orchestration stack bullet list, around line 1099–1104.

### What exists now:

```
### 12.0 Orchestration Architecture `[SYNTHESIS UPDATE]`

**Custom orchestration, not framework adoption.** The AgentLeak benchmark (February 2026) demonstrated that bolting isolation onto existing frameworks fails at 46-69% leakage rates. No existing framework natively supports Keystone's combination of strict agent isolation, durable execution with crash recovery, type-safe handoff contracts, and human-in-the-loop gates. The framework layer is thinning (AWS Strands: "We no longer needed complex orchestration"). Durable value lies in specification, evaluation, and observability — not in the orchestration layer itself.

The orchestration stack:

- **PydanticAI** for agent definition and type-safe handoff contracts. Every pipeline boundary (Section 2, Handoff Contracts table) is enforced by Pydantic schema validation. Invalid handoffs fail at the schema level, not at runtime.
- **Temporal** for durable execution. Research engagements run for minutes to hours. Temporal provides crash recovery (resume from last checkpoint, not from scratch), human-in-the-loop gates (pause pipeline for human review at configurable boundaries), and execution history for debugging and trajectory storage.
- **MCP (Model Context Protocol)** for tool integration with a **gateway architecture**. 66% of community MCP servers have security findings. All MCP tool calls route through a gateway that enforces: per-agent tool authorization (only assigned tools accessible), rate limiting, input sanitization, and audit logging. The gateway is the structural enforcement of per-agent tool specialization.
- **AG-UI** for output streaming. Real-time visibility into agent progress for the human operator during engagement execution.
```

### What it should say:

Replace the entire orchestration stack list (four bullets) with the following updated version. The opening rationale paragraph is unchanged. Tag the new/changed bullets with `[BATCH 2 UPDATE]`:

---

The orchestration stack:

- **PydanticAI** for agent definition and type-safe handoff contracts. Every pipeline boundary (Section 2, Handoff Contracts table) is enforced by Pydantic schema validation. Invalid handoffs fail at the schema level, not at runtime. All standard research agents use PydanticAI calling the Claude API directly — this is the primary agent execution path.
- **Custom async orchestration (Phase 1) / Temporal (Phase 2) `[BATCH 2 UPDATE]`** for durable execution. In Phase 1, the pipeline controller uses `asyncio.gather()` for parallel research fan-out and a PostgreSQL database state machine for human-in-the-loop gates and crash recovery checkpointing. Temporal is deferred to Phase 2: research engagements run for minutes to hours, and Temporal provides the full crash-recovery and workflow-durability guarantees needed for production reliability. Five Day-1 coding standards enforced from Phase 1 ensure zero-rework migration (see §12.0 below).
- **MCP (Model Context Protocol)** for tool integration with a **gateway architecture**. 66% of community MCP servers have security findings. All MCP tool calls route through a gateway that enforces: per-agent tool authorization (only assigned tools accessible), rate limiting, input sanitization, and audit logging. The gateway is the structural enforcement of per-agent tool specialization.
- **AG-UI** for output streaming. Real-time visibility into agent progress for the human operator during engagement execution.
- **`[BATCH 2 UPDATE]` Agent SDK: NOT in the primary stack.** The Claude Agent SDK (anthropic-ai/claude-agent-sdk, renamed September 2025) is Claude-only with proprietary ToS and introduces Node.js subprocess overhead. It is not the execution substrate for standard research agents. Agent SDK is reserved as a conditional future option for specific pipeline nodes requiring Claude Code's full runtime capabilities (computer use, code execution, file system access). No Phase 1 component depends on it.

---

### Preservations:

- The opening rationale paragraph ("Custom orchestration, not framework adoption...") is unchanged.
- AG-UI bullet is unchanged.
- MCP gateway bullet is unchanged.

### Cross-section references:

- No other sections currently reference "Claude Agent SDK" or "execution substrate." This change is self-contained.
- The Phase 1 vs. Phase 2 split for Temporal (custom async -> Temporal) is a clarification that must be consistent with the build order added in Change #45 and #46 below.

### Directive compliance:

- **Directive 10 (Confirmed decisions):** PydanticAI is confirmed as the agent framework. Temporal is confirmed as deferred to Phase 2. Both are preserved.
- **Directive 14 (Quality standard):** Removing a mischaracterized dependency (Agent SDK) and accurately describing the actual Phase 1 orchestration path is a quality improvement.

---

## Change #44: Add Error Recovery Layers 1-2 as Phase 1 Requirement

**MASTER-SYNTHESIS Reference:** Section 9, Change #44; Decision 10; analysis-09-orchestration-patterns.md Finding #1.

**Phase Classification:** [Phase 1] — Error recovery Layers 1-2 (retry + fallback) ship with the first research agent. Justified by Claude API having 62 incidents in 90 days (StatusGator monitoring data, independent verification).

**Phase Rationale:** Claude API reliability is a confirmed operational constraint, not an edge case. Shipping research agents that collapse on rate-limit or temporary API errors is a structural quality failure. Layer 1 (retry with tenacity) takes hours to implement; Layer 2 (model fallback chain) takes a day. The cost of deferral is measured in broken engagements.

**Location in CAPSTONE-PLAN-v2.md:** Section 12, subsection 12.0, immediately after the five-bullet orchestration stack (after Change #43 edits). Add a new named paragraph.

### What exists now:

No error recovery specification exists in §12.0. The Phase 2 items include general "self-improvement loop" infrastructure but no retry/fallback specification. The Phase 1 build order in §12.1 does not mention error recovery.

### What it should say:

Add the following block immediately after the orchestration stack bullet list in §12.0, before §12.1:

---

**`[BATCH 2 UPDATE]` Error Recovery: Four-Layer Defense, Layers 1-2 in Phase 1.**

Claude API has 62 incidents in 90 days with a median duration of 1 hour 19 minutes (StatusGator independent monitoring, March 2026). A research pipeline that fails on API errors is not production-quality. The four-layer error recovery stack ships in stages:

**Layer 1 — Retry with exponential backoff (Phase 1, ships with Component #7):** All Claude API calls use `tenacity` with 1-second base, 60-second cap, full jitter, 5 maximum attempts. Retry on status codes 429 (rate limit), 500 (server error), 529 (overloaded), and connection timeout. Never retry 400 (bad request), 401 (auth), or 413 (payload too large). Honor `Retry-After` and `X-RateLimit-*` response headers.

**Layer 2 — Model fallback chain (Phase 1, ships with Component #7):** When the primary model is unavailable after Layer 1 exhaustion, fall back through: Opus 4.6 → Sonnet 4.6 → Haiku 4.5 → cached/template response. Retry primary 2-3 times before falling back — do not fail over on first retry. Each research agent must return a structured `success: bool` and `fallback_used: Optional[str]` field so the orchestrator always knows what it received.

**Layer 3 — Error classification (Phase 1, ships with pipeline controller):** Classify errors as retriable (temporary API unavailability), permanent (malformed request), or quality-related (technically successful response but output fails schema validation). Quality-related failures trigger regeneration, not retry. The pipeline controller owns this classification logic; agent code does not.

**Layer 4 — PostgreSQL checkpointing (Phase 1, ships with HITL infrastructure):** Completed pipeline stages write their outputs to `agent_results` table before the next stage begins. On crash recovery, the orchestrator reads the last checkpoint and resumes from that point rather than restarting from scratch. This is the same `agent_results` table used by the HITL state machine (see §12.0 HITL section below).

**Partial-result continuation:** If 3 of 5 research agents complete but 2 fail after Layer 1-2 exhaustion, the pipeline combines the available results with a reduced-coverage notice and retries the failed agents independently before proceeding to CitationProcessor. The orchestrator must never silently drop agent results — every gap is logged and surfaced to the HITL review gate.

---

### Preservations:

- No existing §12.0 content is deleted by this change.

### Cross-section references:

- **Section 12.1 (Phase 1 build order):** The new build order (Change #47/#48 below) must place error recovery specification in Component #7 (Research Agent pipeline). The error recovery is baked into Component #7, not a separate component.
- **Section 4 (Research & Analysis):** The research agent pipeline section should reference the retry policy. That section is assigned to a different subagent (changes #11-22); note the dependency so the orchestrator can coordinate.

### Directive compliance:

- **Directive 7 (HITL gates):** Layer 4 checkpointing is the mechanism that makes HITL gates crash-resilient. If the pipeline crashes between Gate 1 approval and Gate 2, the checkpoint allows resumption without requiring the human to re-review Gate 1.
- **Directive 14 (Quality standard):** A system that fails silently on API errors does not meet the Goldman-grade quality standard. Error recovery is a foundational quality requirement.

---

## Change #45: Add Database State Machine HITL as Phase 1 Implementation

**MASTER-SYNTHESIS Reference:** Section 9, Change #45; Decision 11; analysis-09-orchestration-patterns.md Finding #4.

**Phase Classification:** [Phase 1] — Jack's two non-negotiable HITL gates (Directive #7) are required from the start. Temporal is deferred. The database state machine is the only viable Phase 1 path.

**Phase Rationale:** Jack's Directive #7 confirms two non-negotiable gates: (1) after Spec Engine produces issue tree/task list, (2) after Deliberation produces confidence map. Temporal (which was the original HITL mechanism in the plan) is deferred to Phase 2. The database state machine fills this gap cleanly and maps to Temporal Signals in Phase 2 with no agent code changes.

**Location in CAPSTONE-PLAN-v2.md:** Section 12, subsection 12.0, immediately after the error recovery block added in Change #44.

### What exists now:

The existing plan lists Temporal as the HITL mechanism without specifying a Phase 1 interim path. The bullet for Temporal says: "human-in-the-loop gates (pause pipeline for human review at configurable boundaries)" — which implies Temporal handles HITL, but Temporal is Phase 2. This leaves a functional gap.

### What it should say:

Add the following block immediately after the error recovery section in §12.0, tagged `[BATCH 2 UPDATE]`:

---

**`[BATCH 2 UPDATE]` Human-in-the-Loop Gates: Phase 1 Implementation.**

Jack's Directive #7 specifies two non-negotiable gates: (1) human reviews and approves or modifies the issue tree and task list before research begins, (2) human reviews the confidence map before content generation. These gates are not deferred to Phase 2. Temporal (Phase 2) provides the production-grade durable HITL implementation; the Phase 1 implementation uses a **PostgreSQL database state machine** that maps cleanly to Temporal Signals in Phase 2 with no changes to agent code.

**Three-table schema:**

- `pipeline_runs`: One row per engagement. Fields: `run_id` (UUID), `engagement_id`, `status` (CREATED → RUNNING → AWAITING_REVIEW → APPROVED → COMPLETED → FAILED), `created_at`, `completed_at`.
- `review_gates`: One row per gate instance. Fields: `gate_id` (UUID), `run_id` (FK), `gate_type` (SPEC_APPROVAL | DELIBERATION_APPROVAL), `status` (PENDING → APPROVED | MODIFIED | REJECTED), `artifact_path` (path to artifact for review), `reviewer_decision`, `reviewer_notes`, `created_at`, `decided_at`, `timeout_at`.
- `agent_results`: One row per agent execution. Fields: `result_id` (UUID), `run_id` (FK), `agent_id`, `agent_type`, `status` (RUNNING | COMPLETED | FAILED | FALLBACK_USED), `output_path`, `fallback_model`, `token_count`, `created_at`.

**Three review flows from Day 1:**
- **Approve:** Gate status transitions to APPROVED; orchestrator resumes next pipeline stage.
- **Modify:** Human edits the artifact (issue tree or confidence map) via the web UI. Edits are schema-validated before acceptance. Orchestrator receives the modified artifact.
- **Reject:** Gate status transitions to REJECTED with reviewer notes. Notes are injected as context into the next pipeline stage (for Gate 1: Spec Engine reruns with rejection feedback; for Gate 2: Deliberation reruns).

**Default gate timeouts:** Gate 1 (Spec Engine issue tree approval): 1 hour. Gate 2 (Deliberation confidence map approval): 24 hours. On timeout, the pipeline is paused with a notification; it does not proceed without a decision.

**Web UI requirements:** The review interface must display the artifact prominently alongside a collapsible "Agent Reasoning" panel showing: sources consulted, key analytical decisions, confidence levels, token usage per agent, and divergence points surfaced by TiCoder (when available). The reasoning panel is not cosmetic — it is the mechanism by which the reviewer makes an informed decision. Without it, the gate becomes a rubber stamp.

**Phase 2 upgrade path:** When Temporal ships, wrap each agent's `run()` call with `@workflow.defn`, replace `asyncio.gather()` with Temporal activity calls, and replace polling/asyncio event notification with Temporal Signals. The three-table schema maps to Temporal's workflow state. No agent code changes are required — only the orchestration layer migrates.

---

### Preservations:

- The Temporal bullet in the orchestration stack (updated in Change #43) describes Phase 2 Temporal behavior. The database state machine description here is the Phase 1 implementation of the same gates. Both exist and are complementary.

### Cross-section references:

- **Section 12.1 (Phase 1 build order):** The new build order must include `#HITL PostgreSQL state machine` as a parallel item in the first block (no dependencies, 2-3 days). See Change #47/#48 for the full build order update.
- **Section 3 (Specification Engine), Step 8:** The HITL gate at Spec Engine output (Step 8 in the 10-step flow) writes to `review_gates` and polls for approval before proceeding to research execution. This must be reflected in the Spec Engine spec assigned to the other subagents.

### Directive compliance:

- **Directive 7 (HITL gates):** Directly implements both non-negotiable gates with approve/modify/reject flows.
- **Directive 5 (Build philosophy):** The database state machine is the "reduced feature depth" version of Temporal's full durability model. The interface (agent writes to `review_gates`, polls for status) is the same in Phase 1 and Phase 2.

---

## Change #46: Add 5 Mandatory Day-1 Coding Standards for Temporal Migration Readiness

**MASTER-SYNTHESIS Reference:** Section 9, Change #46; Section 1 ("Orchestration Pattern"); analysis-09-orchestration-patterns.md Finding #3.

**Phase Classification:** [Phase 1] — These are non-negotiable coding standards for all Phase 1 pipeline code. They are pure software discipline with no extra feature cost.

**Phase Rationale:** These five standards are low-cost to implement upfront and prevent expensive rearchitecting when Temporal arrives in Phase 2. They are not optional suggestions — they are mandatory acceptance criteria for every Phase 1 pipeline layer. Missing any one of them creates a migration obstacle.

**Location in CAPSTONE-PLAN-v2.md:** Section 12, subsection 12.0, immediately after the HITL state machine block added in Change #45.

### What exists now:

No coding standards appear in §12. The existing §12.0 lists technologies but specifies no implementation requirements for the code that uses them.

### What it should say:

Add the following block immediately after the HITL state machine section, tagged `[BATCH 2 UPDATE]`:

---

**`[BATCH 2 UPDATE]` Mandatory Day-1 Coding Standards: Temporal Migration Readiness.**

These five standards are non-negotiable acceptance criteria for every Phase 1 pipeline layer. They exist because Temporal migration in Phase 2 requires them, and retrofitting them after the fact requires rewriting every pipeline component. Build them in from Day 1. They are not extra work — they are the correct way to build the pipeline.

**Standard 1 — Pure function layers:** Every pipeline layer must implement a pure async function as its primary entry point:

```python
async def run_layer(input: LayerInput) -> LayerOutput:
    ...
```

No side effects in the layer function itself. I/O (database writes, file writes, API calls) is handled by injected dependencies, not inline. This is the precondition for Temporal's activity function wrapping.

**Standard 2 — Pydantic inter-layer data:** All data crossing a pipeline boundary must be a Pydantic model. No dicts, no untyped JSON, no raw strings at layer boundaries. This is already required by Settled Decision #8 (protocol-based contracts); this standard reinforces it as a coding-level requirement, not just an architectural aspiration.

**Standard 3 — Separate pipeline controller:** The orchestration logic (what runs next, in what order, with what inputs) must live in a dedicated controller module (`src/keystone/pipeline/`), not inside agent code. An agent's `run()` method produces outputs; it does not decide what happens to them. The controller makes sequencing decisions. This is the precondition for wrapping orchestration logic in Temporal `@workflow.defn` classes.

**Standard 4 — Correlation IDs from Day 1:** Every pipeline run generates a UUID at creation. This UUID is logged with every operation, API call, database write, and error in that run. Use structured logging: `logger.info("agent_complete", run_id=run_id, agent_id=agent_id, status=status)`. These become Temporal workflow IDs in Phase 2 with no log format changes.

**Standard 5 — Idempotent layers:** Given the same input, a layer must always produce the same output. Layers must not depend on external mutable state that could differ between executions. This is the precondition for Temporal's event history replay. Practical implication: if a layer writes to a database, it must be safe to call twice with the same input (use upsert, not insert).

**Violation handling:** A pipeline layer that fails any of the five standards must not be merged to main. These standards should appear in the project's CONTRIBUTING.md and be verified in code review. The five standards are also the primary migration checklist when Temporal is introduced in Phase 2 — if all five are satisfied, wrapping each layer with Temporal activities is mechanical.

---

### Preservations:

- No existing §12.0 content removed by this change.

### Cross-section references:

- **docs/ARCHITECTURE.md:** The five standards should also appear in the Architecture document's coding conventions section. This is a cross-file dependency; the builder session should update both files.
- **All Phase 1 components (#5, #7, #9):** Components #5 (Specification Engine), #7 (Research Agent pipeline), and #9 (Deliberation) are explicitly cited in analysis-09 as the primary targets for these standards.

### Directive compliance:

- **Directive 5 (Build philosophy):** Defining the interfaces correctly in Phase 1 (pure functions, typed data, separate controller) is precisely the "build the architecture correctly" instruction.
- **Directive 13 (Phase 1 depth staging):** Temporal deferred to Phase 2. The five standards ensure Phase 2 migration is mechanical, not a rewrite.

---

## Change #47: Replace Academix with paper-search-mcp in Server List / Update Phase 1 Build Order

**MASTER-SYNTHESIS Reference:** Section 9, Change #47; Decision 9; analysis-08-mcp-ecosystem.md Finding #3 and Changes table.

**Phase Classification:** [Phase 1] — Tool selection update. Affects Component #4 (MCP Gateway) and §12.1 (Phase 1 build order).

**Phase Rationale:** Academix (`xingyulu23/Academix`) covers 5 academic sources. `paper-search-mcp` (`openags/paper-search-mcp`) covers 21+ sources with a free-first full-text fallback chain. The upgrade is unambiguous at no added cost. Academix does not appear explicitly in §12 of the current document, but the build order must be updated alongside this change.

**Location in CAPSTONE-PLAN-v2.md:** Two locations:

1. **Section 12, subsection 12.1** — The Phase 1 build order needs complete replacement per the MASTER-SYNTHESIS Section 10 updated sequence.
2. **Section 6.2** — Line 727 already mentions `paper-search-mcp` (Semantic Scholar + OpenAlex via paper-search-mcp). No change needed there; it is already correct.

### What exists now (§12.1 build order):

```
### 12.1 Phase 1: The Core Pipeline (Build First)

**Principle: Ship the core pipeline fast, then iterate to quality** (Jones, "Compressed Window," Feb 14, 2026)...

**Phase 1 deliverables (build in this order):**

1. **RESEARCH.md specification format** — Define the engagement specification structure...
2. **Specification Engine (Layer 0)** — Build the decomposition and specification verification pipeline...
3. **Evaluator with ten-dimension rubric (Layer 4)** — The ten-dimension rubric, Observation Library capture, sprint contract grading, and anti-confirmatory checking...
4. **Research Agent pipeline with strict isolation (Layer 1)** — Parallel agents, file-system coordination...
5. **CitationProcessor** — Discrete stage between L1 and L1.5...
6. **Deliberation (Layer 1.5)** — Independent parallel analysis...
7. **Retrieval infrastructure** — pgvector + pgvectorscale, hybrid search...
8. **End-to-end pipeline test** — Run a complete research question through the pipeline...
```

### What it should say:

Replace the "Phase 1 deliverables (build in this order):" section (items 1-8) with the following, tagged `[BATCH 2 UPDATE]`. Preserve the "Principle: Ship the core pipeline fast..." paragraph unchanged.

---

**`[BATCH 2 UPDATE]` Phase 1 deliverables (updated build order):**

The following items in the first block have no dependencies on each other and can be built in parallel:

**Parallel block (no dependencies):**

- **#1 RESEARCH.md specification format (S+, 2-3 days)** — Define the engagement specification structure: add Day-1 Hypothesis field, per-branch "end product" specification, engagement type (5-type taxonomy), max_rounds override, scope-change sensitivity, and priority_score as a computed field in research-tasks.json. Encode DAG dependency structure (not flat task list). Test by manually writing specifications for 3-5 sample research questions. This is the foundation everything else builds on.

- **#2 Citation data model (S, 1-2 days)** — Define the Pydantic citation schema with content-hash provenance field for wiki compilation integrity. No scope change from prior plan. Build before any research agent is implemented.

- **#3a Source Discovery (L, 1-2 weeks)** — Retrieval infrastructure: pgvector + ParadeDB (BM25 + RRF fusion), Voyage-finance-2 embeddings, contextual retrieval at ingest (Haiku-generated preamble per chunk), Cohere Rerank v3.5 (top 150 → rerank → top 20), Docling for structure-aware parsing, Brave Search + Exa for external discovery. **Note:** Semantic Router and Bifrost are REMOVED from this component per the Batch 2 retrieval analysis.

- **#3b Knowledge Accumulation (M, 3-5 days)** — Compiled markdown wiki per engagement following the Karpathy three-layer pattern (`raw/` for full subagent artifacts, `compiled/` for orchestrator-synthesized findings, `INDEX.md` auto-maintained). Content-hash provenance per proposition. Human-designed schemas. #3b can begin before or after #3a — they are independent.

- **#4 MCP Gateway (M, 1 week)** — Tool integration gateway. Evaluate IBM ContextForge in the first 2 days of this component; adapt if the authorization model supports per-agent tool lists, build custom if not. **Updated server list:** Exa MCP (primary semantic search), Brave Search MCP (independent keyword index), EdgarTools MCP (SEC filings), FRED MCP (macroeconomic data), **paper-search-mcp** (academic search, 21+ sources — replaces Academix), doi-mcp (citation verification). Add circuit breaker parameters (10s tool call timeout, 15s overall budget, exponential backoff with jitter). Add `transport_type` and `security_approved` fields to tool registry schema.

- **#HITL PostgreSQL state machine (S, 2-3 days)** — Three-table schema (`pipeline_runs`, `review_gates`, `agent_results`), REST API, web UI with artifact display and collapsible agent reasoning panel. Approve/modify/reject flows. Must ship before Component #5 and Component #9 are integrated, since both write to `review_gates`. See §12.0 HITL specification for full schema.

**Sequential block (each depends on all parallel items above):**

- **#5 Specification Engine (XL, 2-3 weeks)** — 10-step pipeline (see §3 for full specification). Includes engagement classifier, intent clarifier, issue tree decomposition with heterogeneous consulting lenses, MECE verification, VOI-inspired priority scoring, dynamic agent configuration via template registry, human review gate integration (Gate 1, writes to `review_gates`), iterative research feedback loop. Observation Library CBR query at entry is wired but bypassed when library is empty. Estimated 2-3 weeks.

- **#6 Evaluator stack Layers 1-3 (XL, 2-3 weeks)** — Ten-dimension rubric with geometric mean aggregation. Tier 1 (universal gates) / Tier 2 (adaptive dimensions) rubric split. 3-4 engagement-type evaluation profiles for Phase 1 (expand to 8-10 in Phase 2). Sprint contract: Evaluator proposes criteria, Generator reviews. Calibrate against 10+ past Keystone deliverables before production use. Target: 0.80+ Spearman correlation against expert human scores.

- **#7 Research Agent pipeline (L+, 1-2 weeks)** — Parallel agents with strict isolation. Error recovery Layers 1-2 baked in: `tenacity` retry (1s base, 60s cap, full jitter, 5 attempts), model fallback chain (Opus → Sonnet → Haiku → cached). Subagent output contract: structured summary (~1,500 tokens, 3-7 claims, per-claim confidence scores, source counts) plus full artifact written to `{engagement_id}/memory/raw/`. Template registry replaces enum dispatch for agent configuration.

- **#8 CitationProcessor (M, 3-5 days)** — Discrete stage between L1 and L1.5. Source deduplication, cross-agent corroboration scoring, URL liveness verification, citation manifest generation, content-hash provenance for wiki compilation.

- **#9 Deliberation (L+, 1-2 weeks)** — Claim-level selection (not synthesis/blending). Per-claim confidence scores and source counts required from upstream subagents. "What Would You Have to Believe?" step for findings below high confidence. Human review gate integration (Gate 2, writes to `review_gates`). Cross-provider model diversity for at least one analyst.

- **#10 Evaluator calibration (M, 1 week)** — Calibrate 3-4 engagement-type profiles against Keystone deliverables. Per-dimension bias detection.

- **#11 End-to-end pipeline test (M, 3-5 days)** — Run a complete research question through the pipeline. Must exercise both HITL gates (approve/modify/reject). Must validate multi-round iterative research loop. Must verify information fidelity (confirm 37% retention failure mode does not occur). This is the capstone's existence proof.

---

### Preservations:

- The "Principle: Ship the core pipeline fast, then iterate to quality" paragraph must remain as the section's opening.
- The `[SYNTHESIS UPDATE]` tag on §12.1's heading (if present) should be updated to `[BATCH 2 UPDATE]` to reflect this version's changes.

### Cross-section references:

- **Section 12.2 (Phase 2):** Phase 2 item numbering remains unchanged (items 9-14). The Phase 1 item numbering above does not conflict.
- **Section 6.2 (Retrieval Architecture):** Line 727 already correctly shows `paper-search-mcp`. Verify no Academix mention exists in §6 (confirmed: no matches found).

### Directive compliance:

- **Directive 5 (Build philosophy):** The parallel block reflects correct dependency analysis — RESEARCH.md, citation model, retrieval, MCP, and HITL have no dependencies on each other and should be built in parallel to compress the timeline.
- **Directive 9 (Component #3 concern):** #3a and #3b are now correctly separated. Build #3a first; #3b can follow independently.

---

## Change #48: Add Finnhub MCP for Market Data

**MASTER-SYNTHESIS Reference:** Section 9, Change #48; Decision implicit in Component #4 update; analysis-08-mcp-ecosystem.md Finding #4.

**Phase Classification:** [Phase 1] — MCP server addition to Component #4. Specified as a supplementary server (not in the MVP gateway config by default, but available for engagements requiring market data).

**Phase Rationale:** Finnhub MCP provides free market data at 60 requests/minute — workable for a 3-5 agent consulting research system. The prior plan had no market data server specified. This fills a capability gap that would otherwise force agents to use general web search for data that should be retrieved from a structured financial data source.

**Location in CAPSTONE-PLAN-v2.md:** Section 12, subsection 12.1, within the new build order block created in Change #47. Specifically, the #4 MCP Gateway bullet's server list must include Finnhub.

### What exists now:

The server list for Component #4 (as updated by Change #47) does not yet include Finnhub. The current document has no market data MCP server specified anywhere.

### What it should say:

This change is incorporated directly into the #4 MCP Gateway bullet in Change #47's build order. The full updated text appears in Change #47. For clarity, the specific addition is:

In the #4 MCP Gateway server list, after the MVP gateway config (6 servers), add the following supplementary server entry:

---

**Supplementary servers (not in MVP gateway config by default; loaded per engagement type):**

- **Finnhub MCP** (`cfdude/mcp-finnhub`, stdio transport, free tier) — Real-time and historical market data: stock quotes, earnings, financial statements, IPO calendars, market news sentiment. Free tier: 60 requests/minute. Suitable for consulting research (not high-frequency trading). For engagements requiring more detailed financial statements, add **FMP MCP** (Financial Modeling Prep, 250 requests/day free tier) as a secondary. Do not integrate Alpha Vantage (25 requests/day free tier is effectively unusable for multi-agent parallelism). `[BATCH 2 UPDATE]`

---

Additionally, update the §12.5 "What Specifically Changed" priority table to add a row for MCP server updates. Insert the following row in the Component column after the CitationProcessor row:

| MCP Gateway (Component #4) | Not specified (Academix for academic) | **HIGH** | paper-search-mcp replaces Academix (21+ vs 5 sources); Finnhub MCP adds market data capability; IBM ContextForge evaluated as gateway starting point |

### Preservations:

- All existing §12.5 table rows are unchanged.
- Finnhub is specified as a supplementary server, not a default MVP server. The 6-server MVP list (Exa, Brave, EdgarTools, FRED, paper-search-mcp, doi-mcp) is unchanged.

### Cross-section references:

- **Section 6.2 (Retrieval Architecture):** The public sources list in §6.2 (line 727) may warrant a note that Finnhub MCP is available for market data queries, but §6.2 is not assigned to this subagent. Flag for the orchestrator: §6.2 should mention Finnhub as a supplementary tool in the search API stack.

### Directive compliance:

- **Directive 4 (Engagement scope):** M&A and Growth engagements require market data. Finnhub MCP fills this capability gap without requiring agents to use less structured web search APIs for financial data.
- **Directive 11 (Configurable pipeline depth):** Finnhub as a supplementary server (not default) is the correct implementation of configurable pipeline depth for tool availability — heavier engagements activate more servers.

---

## Change Summary and Orchestrator Notes

### Dependencies between changes in this spec

| Change | Depends on |
|--------|-----------|
| #39 (CBR framing) | None — §7.1 addition |
| #40 (5-tier hierarchy) | #39 — adds content to the CBR block |
| #41 (extraction types) | #39 — adds to §7.7's Retain step |
| #42 (flexon tagging) | #40 — expands the hierarchy's secondary dimension 1 |
| #43 (remove Agent SDK) | None — §12.0 bullet replacement |
| #44 (error recovery) | #43 — follows Agent SDK removal in §12.0 |
| #45 (HITL state machine) | #44 — follows error recovery in §12.0 |
| #46 (Day-1 standards) | #45 — follows HITL state machine in §12.0 |
| #47 (build order + Academix) | #43, #44, #45, #46 — §12.1 build order references §12.0 additions |
| #48 (Finnhub MCP) | #47 — adds to the server list created in #47 |

### Dependencies on other subagents' changes

- **Change #39 depends on changes from the Spec Engine subagent (Section 3):** The CBR Retrieve step at Spec Engine entry (Change #39) must be reflected in Section 3's 10-step flow (Step 1: Problem Framing and Classification). The orchestrator must verify consistency between the §7.1 CBR description and §3's Step 1 description.
- **Change #45 HITL depends on Section 3 (Spec Engine) and Section 4 (Research):** The `review_gates` write at Gate 1 (Spec Engine output) must appear in §3's Step 8 specification. Gate 2 (Deliberation output) must appear in §9's Deliberation specification. Both are assigned to other subagents.
- **Change #44 (error recovery in #7) must be consistent with Section 4 changes** assigned to other subagents. The retry policy, fallback chain, and partial-result handling in §12.0/#44 must match whatever the Section 4 subagent specifies for Component #7.
- **Change #47 build order includes §3b Knowledge Accumulation:** The §3b spec references the Karpathy three-layer pattern. The Section 6 subagent (assigned retrieval changes #30-38) may also touch this component. Verify no duplication.

### Tags to use in the final document

All additions in this spec use `[BATCH 2 UPDATE]` tags. The existing `[SYNTHESIS UPDATE]` tags in §7.1 and §12.0 should be preserved. Do not remove or replace existing tags.

### Style notes

- §7 prose style: flowing, explanatory, slightly academic. Match the existing tone in §7.1-§7.8. Avoid bullet-heavy formatting except where tables or code blocks add clarity.
- §12 prose style: more technical and action-oriented. Bullet lists for build order items are correct. Code blocks for schemas and function signatures are appropriate.
- Citation format used in this document: (Author, "Title," Date). The CBR citation follows this: (Aamodt & Plaza, "Case-Based Reasoning: Foundational Issues, Methodological Variations, and System Approaches," 1994).
