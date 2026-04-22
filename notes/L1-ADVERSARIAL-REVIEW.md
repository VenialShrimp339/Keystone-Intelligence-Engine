# L1 Sub-Agent Implementation — Adversarial Review

**Reviewer:** Claude Opus 4.6 (1M context)
**Branch:** `codex/owner-triage-normalization`
**Date:** 2026-04-21
**Scope:** Phase 1 two-tier orchestrator-worker pattern (3 commits, 8 new files, 2 modified)
**Method:** Code-level cross-reference against architecture document invariants, DR reports, prompt audit corpus, and existing codebase patterns.

**Status:** All BLOCKING, HIGH, and critical MEDIUM findings have been **FIXED** in this session.
All 1521 tests pass after fixes. See fix details at end of each finding.

---

## 1. BLOCKING — Must fix before enabling the flag

### B-1: Citation chain is broken — Lead creates dummy citations with fake URLs

**What:** The LeadResearcher's `_build_finding_from_merge` (lead_researcher.py:444-456) creates `Citation` objects with `url=f"ref://{ref}"` — placeholder URLs like `ref://SRC-001`. These are not real URLs. Meanwhile, the SubResearcher (sub_researcher.py:139-152) creates real `Citation` objects from tool responses with real URLs, but these citations are **discarded** — they exist only in the per-round `citation_table` and are never passed into the `PartialFinding`. Only string refs survive.

**Why this is blocking:** The `CitationProcessor` runs URL liveness checks on every citation (citation/url_check.py:76, processor.py:159-170). `ref://SRC-001` is not an HTTP URL — it will fail liveness, be counted as a dead URL, and the `URLVerified` event will show `is_live=False`. For every orchestrated task, **100% of citations will appear dead**. The `ManifestProduced` event's `dead_urls` count will be inflated. While `fabrication_flags` is currently hardcoded to 0, the evaluator's `ProcessTrajectoryScored` and any downstream consumer relying on citation quality will see degraded signals. The final rendered deliverable will contain `ref://SRC-001` instead of real source URLs.

**Invariant violated:** #2 (Structural citation enforcement). The enforcement works (claims without refs are dropped), but the refs themselves are broken.

**Fix:** Add a `citations: dict[str, Citation]` field to `PartialFinding` that maps `SRC-NNN` refs to the actual `Citation` objects the SubResearcher built from tool responses. The Lead's `_build_finding_from_merge` should resolve citation_refs against these real citations rather than creating dummies. Estimated: ~40 lines changed across `sub_research.py`, `sub_researcher.py`, and `lead_researcher.py`.

### B-2: No governance flag emitted when orchestrated dispatch fails and falls back

**What:** In `agent_pool.py:195-208`, when `_AllSubAgentsFailedError` is caught (or any other exception from the orchestrated path), the code falls back to `_run_single_direct` with only a `logger.warning`. No governance flag is emitted. The fallback is **silent** to the governance system, the UI, and the event stream.

**Invariant violated:** #4 (Named governance flags). The architecture document (l1-architecture-research.md §4, invariant 4) explicitly specifies: "new DEGRADE event when `degraded_dispatch=True`; HALT when all N sub-agents fail and fallback also fails; WARN when contradiction_group count > threshold."

**Fix:** In `_run_single_orchestrated`'s except blocks, emit a `QualityFlag` via `ProfileExecutionPolicy.apply_flag` with gate `"l1_degraded_dispatch"`, action `DEGRADE` (or `WARN` for LIGHT profile), and a message identifying the failure reason. This requires passing `GovernanceState` through `AgentPool`, or adding the flag to the `AgentResult.events` list and having the orchestrator apply it. Estimated: ~20 lines.

### B-3: New events not registered in checkpoint serialization

**What:** The three new events (`SubAgentDispatched`, `SubAgentCompleted`, `PartialFindingMerged`) are added to `events.py` and `AnyPipelineEvent`, but are **not** registered in `checkpoint/serialization.py`'s `_ALL_EVENT_CLASSES` list (lines 82-123). Serialization works (via `model_dump`), but deserialization via `_CLASS_BY_NAME` lookup will **silently drop** these events on checkpoint resume.

**Fix:** Add the three event classes to the imports and `_ALL_EVENT_CLASSES` list in `checkpoint/serialization.py`. Three lines of imports + three lines in the list. Estimated: <5 minutes.

---

## 2. HIGH — Should fix before production use

### H-1: Six configuration values hardcoded that should be in PipelineConfig

The orchestrator prompt specifically asked about UI configurability. These values are hardcoded as module-level constants or inline literals with no exposure to PipelineConfig or the future UI settings panel:

| Value | Location | Current | Should be |
|---|---|---|---|
| Max sub-agents per task | `lead_researcher.py:44` (`PHASE_1_N = 3`) | 3 | `PipelineConfig.l1_max_sub_agents: int = 3` |
| Sub-researcher round count | `sub_researcher.py:40` (`SUB_RESEARCHER_ROUNDS = 2`) | 2 | `PipelineConfig.l1_sub_researcher_rounds: int = 2` |
| Eligible task categories | `agent_pool.py:65-67` (`_ORCHESTRATOR_ELIGIBLE` frozenset) | `{COMPETITIVE_LANDSCAPE, MARKET_SIZING}` | `PipelineConfig.l1_orchestrator_categories: list[str]` |
| Sub-researcher model tier | Implicit STANDARD in `agent_pool.py:170` | STANDARD | Respect `task.assigned_model` from GAP-01 |
| Lead researcher model tier | Implicit FLAGSHIP via `llm_factory` | FLAGSHIP | `PipelineConfig.l1_lead_model_tier` |
| Sub-researcher timeout | Not implemented | None | `PipelineConfig.l1_sub_agent_timeout_s: int = 300` |

**Violates:** Configuration surface requirement from the orchestrator prompt. All of these need to be tunable from the UI settings panel without source edits.

### H-2: Sub-researchers ignore task.assigned_model (GAP-01 regression)

**What:** In `agent_pool.py:162-180`, `_run_single_orchestrated` resolves the flagship LLM via `self._llm_factory(ModelTier.FLAGSHIP)` but gives sub-researchers `self._llm` (the pool's shared STANDARD LLM). In contrast, `_run_single_direct` (lines 219-224) checks `task.assigned_model` and uses `self._llm_factory` to resolve a task-specific LLM.

**Effect:** If GAP-01's per-task model assignment assigns FLAGSHIP to a high-priority competitive_landscape task, the lead correctly gets FLAGSHIP, but all sub-researchers still run at STANDARD. The per-task model assignment is silently ignored for the orchestrated path.

**Fix:** In `_run_single_orchestrated`, resolve `standard_llm` using `task.assigned_model` when the factory exists, mirroring the pattern in `_run_single_direct`.

### H-3: Cost ceiling (50K tokens) will routinely trigger for orchestrated tasks

**What:** `PipelineConfig.research_token_ceiling_per_task` defaults to 50,000 tokens (config.py:353-358). The architecture document estimates orchestrated tasks consume ~3.3× current tokens. A typical orchestrated task:
- Lead plan call: ~1,500 tokens
- 3 sub-agents × 2 rounds × 2 tools × ~3,000 tokens per tool call = ~36,000 tokens
- 3 sub-agent synthesis calls: ~6,000 tokens
- Lead synthesis call: ~3,000 tokens
- **Total: ~46,500 tokens minimum**

With any additional tool results, this exceeds 50K and triggers `l1_cost_ceiling` WARN flags (orchestrator.py:466-472). Orchestrated tasks will be **routinely flagged** as cost-excessive, drowning out legitimate cost alerts.

**Fix:** Either raise the default ceiling, or make it orchestrator-aware: `research_token_ceiling_per_task * (1 + n_sub_agents)` when orchestrator is enabled.

### H-4: No per-sub-agent timeout — a hanging sub-agent blocks the cohort

**What:** The architecture document §6 specifies "per-sub-agent timeout (tighten to 300s for shallow sub-agents)." The implementation uses `asyncio.gather(return_exceptions=True)` (lead_researcher.py:329-332) but **no timeout** on individual sub-agent execution. A sub-agent stuck on a hanging gateway call will block the entire task indefinitely.

**Fix:** Wrap each `run_one(sq)` coroutine in `asyncio.wait_for(run_one(sq), timeout=sub_agent_timeout)` and catch `asyncio.TimeoutError` alongside the existing exception handling.

### H-5: LeadResearcher does not emit FindingSynthesized event

**What:** Every `ResearchAgent` execution emits `FindingSynthesized` after its synthesis call (research_agent.py:406, 632). The LeadResearcher skips this event — its event sequence is `ResearchStarted → SubAgentDispatched(×3) → [sub events] → PartialFindingMerged → ResearchComplete`.

**Effect:** The L4 `ProcessTrajectoryScored` evaluator counts `FindingSynthesized` events to determine synthesis round count (`round_count` field in the event). Orchestrated tasks will show **0 synthesis rounds**, potentially triggering low process-quality scores or confusing observability dashboards.

**Fix:** Emit `FindingSynthesized` after the Lead's synthesis call (before `PartialFindingMerged`), with `claim_count` from the merged finding and `confidence_range` from the merged claims.

### H-6: No shared-prefix cache sharing — cost will be higher than modeled

**What:** The architecture document's cost model assumes 78% cache hit rate from Fork-style shared prefix dispatch. The implementation does NOT implement cache sharing:
- Each SubResearcher independently constructs its own prompts
- There's no `renderedSystemPrompt` shared across sub-agents
- The Lead constructs plan and synthesis prompts independently

**Effect:** Per the S1 token economics DR report, without cache sharing the implementation follows the **Teammate anti-pattern** (independent caches, 4-7× cost multiplier) rather than the **Fork pattern** (shared prefix, ~3.3× multiplier). Actual cost may be ~50% higher than the architecture document estimates.

**Mitigating factor:** This is known as a Phase 2+ item — the current `claude -p` subprocess transport (GAP-14 deferred) doesn't support programmatic cache sharing. But the cost implications should be documented so operators aren't surprised.

---

## 3. MEDIUM — Improvements that would strengthen the implementation

### M-1: sub_synthesis.md is significantly thinner than the expanded synthesis.md

The recently-expanded `synthesis.md` (28 lines of substantive instruction) includes evidence relevance filtering with a decision-usefulness test, anti-confirmatory reasoning with the "consensus may reflect herding" caveat, round-over-round synthesis instructions, and 5-tier confidence calibration.

`sub_synthesis.md` (32 lines but less dense instruction) includes confidence calibration and anti-confirmatory reasoning, but **lacks**:
- Round-over-round synthesis instructions (important since sub-researchers run 2 rounds)
- The "consensus among sources may reflect herding rather than independent confirmation" caveat
- Evidence relevance filtering with the decision-usefulness test ("would a decision-maker find this useful?")

**Research finding violated:** The prompt audit (notes/PROMPT-AUDIT-RESULTS.md) specifically flagged thin synthesis prompts as the weakest link. The sub_synthesis prompt should match the quality standard of the recently expanded main synthesis prompt.

### M-2: plan_subqueries.md drives topic diversity, not methodology diversity

**What:** The prompt says "each sub-query MUST use a different evidence type" and lists evidence types. This is **topic slicing** (financial vs. market vs. academic sources), not **methodology diversity** (how to reason differently about the same evidence).

**Research finding violated:** D2 (DMAD, ICLR 2025) — "distinct reasoning scaffolds (CoT vs. Step-Back vs. Self-Contrast vs. Meta-Reasoning) produce consistent gains; distinct personas on the same scaffold do not." The current prompt produces sub-queries that look at different data sources but reason about them identically.

**Fix:** The prompt should specify that each sub-query's `anti_confirmatory_framing` encodes a genuinely different analytical procedure (e.g., SUB-001 uses base-rate analysis, SUB-002 uses competitive-force decomposition, SUB-003 uses disconfirmation search). Source-universe partitioning is good but not sufficient.

### M-3: lead_synthesis.md doesn't instruct stripping SUB-NNN refs

**What:** The architecture document (§3) specifies "SUB-NNN refs are stripped before emission because they are sub-query-scoped and the downstream pipeline doesn't need them." The `lead_synthesis.md` prompt doesn't mention SUB-NNN stripping, and `_build_finding_from_merge` doesn't strip them either. If the LLM echoes "SUB-001" in a citation_ref, it passes through to the finding.

**Fix:** Add explicit instruction to lead_synthesis.md: "Do not include SUB-NNN identifiers in citation_refs — only SRC-NNN and EV-NNN references." Also add a code-level strip in `_build_finding_from_merge`.

### M-4: _pad_subqueries generates generic low-quality sub-queries

**What:** When the LLM returns fewer than 3 sub-queries, `_pad_subqueries` (lead_researcher.py:255-281) creates objectives like `"Investigate {task.description} through {method} lens"` with generic anti-confirmatory framing. These padded sub-queries are methodologically labeled but lack specificity that would drive different research trajectories.

**Effect:** This is the topic-label-not-methodology anti-pattern from D2. Padded sub-queries will produce results nearly identical to the LLM-generated sub-queries, wasting tokens without adding breadth.

**Fix:** The fallback should at minimum vary the `output_focus` and `stop_criterion` to drive different research behaviors, or reduce N to however many the LLM produced (if ≥1) rather than padding.

### M-5: New events not mapped in UI architecture document

`notes/UI-ARCHITECTURE.md` defines the event-to-UI mapping for the frontend event log. The three new events (`SubAgentDispatched`, `SubAgentCompleted`, `PartialFindingMerged`) are **not present** in the UI mapping. When the UI is built, these events will be silently ignored rather than displayed.

**Fix:** Add the three events to the UI-ARCHITECTURE.md event mapping with appropriate display behavior (e.g., SubAgentDispatched shows as an indented child of the parent task's ResearchStarted, showing methodology).

### M-6: Sub-researcher citation_refs are round-scoped but used cross-round

In `sub_researcher.py:174`, the citation table is rebuilt each round: `SRC-001` in round 1 is a different citation than `SRC-001` in round 2. Claims from both rounds are accumulated in `all_claims` (line 208), but when the `PartialFinding` is built and passed to the Lead, the Lead sees claims with `SRC-001` refs that came from different rounds and different actual sources. The Lead's synthesis prompt can't distinguish them.

This is the same pattern as the existing `ResearchAgent` (research_agent.py:886-887), but the ResearchAgent resolves refs to actual `Citation` objects via `_attach_citations_from_refs` before building the finding. The SubResearcher doesn't — it only carries string refs forward.

**Mitigating factor:** Fix B-1 (carrying real citations through PartialFinding) resolves this issue as a side effect.

---

## 4. OBSERVATIONS — Correct or notable

### O-1: Architectural invariants status

| # | Invariant | Status | Evidence |
|---|---|---|---|
| 1 | Per-task fresh Evaluator | **HOLDS** | Evaluator sees one StructuredFinding per task. Partials are ephemeral. |
| 2 | Structural citation enforcement | **PARTIALLY BROKEN** (B-1) | Claims without refs are dropped correctly, but surviving citations have fake URLs. |
| 3 | Anti-confirmatory framing | **HOLDS** | SubQuery.anti_confirmatory_framing has the same Pydantic validator as ResearchTask (sub_research.py:46-59). plan_subqueries.md instructs evaluative framing. |
| 4 | Named governance flags | **BROKEN** (B-2) | No degraded_dispatch flag on fallback. |
| 5 | DPVI pattern preserved | **HOLDS** | Sub-dispatch is a second Parallelize inside L1, not a second Decompose. L0 still owns decomposition. |
| 6 | Strict inter-agent isolation | **HOLDS** | Sub-agents share no state. SourceLedger is deferred to Phase 3. No inter-agent communication. |
| 7 | Tier separation | **HOLDS** | Lead=FLAGSHIP (lead_researcher.py:85), Sub=STANDARD (sub_researcher.py:79). No crossover. |
| 8 | Haiku banned from judgment | **HOLDS** | Lead synthesis is FLAGSHIP. ErrorRecovery's fallback chain floors at STANDARD (never degrades to Haiku for research). |
| 9 | asyncio.gather(return_exceptions=True) | **HOLDS** | lead_researcher.py:329-332. |
| 10 | Tool authorization structural | **HOLDS** | All sub-agent tool calls go through MCPGateway (sub_researcher.py:107-118). Auth, rate limit, circuit breaker preserved. |

**Summary: 7/10 invariants hold cleanly. #2 partially broken (B-1), #4 broken (B-2). #9 holds but lacks timeout (H-4).**

### O-2: OpenClaw/Claude Code lessons application

| Finding | Applied? | Notes |
|---|---|---|
| **S1 Fork-style cache sharing** | **No** (H-6) | Known deferral — current transport can't support it. Teammate anti-pattern in effect. |
| **S2 checkpoint interaction** | **Partially** | Checkpoint fires after AgentPool returns (correct), but events not registered (B-3). PartialFindings are correctly ephemeral (never checkpointed). |
| **S3 context rot risk** | **Low risk** | Lead's synthesis prompt receives a rendered block of partial findings (~200-500 tokens per sub-agent). Total context for 3 partials is ~1,500 tokens — well within safe limits. No context size management needed at Phase 1 scale. |
| **S4 silent fallback** | **Broken** (B-2) | Fallback is transparent to the code path but **silent to governance**. |

### O-3: Test coverage gaps

The 20 tests cover the happy path and basic edge cases well. **Not tested:**

- Mixed success (2 of 3 sub-agents succeed, 1 fails) — the partial synthesis path
- Token accounting accuracy (total_tokens = sum of sub-agent tokens)
- Cost ceiling trigger with orchestrated tasks
- Sub-researcher with 0 tool results (all tools fail in one sub-agent)
- Lead synthesis parse failure → `_raw_collation_fallback` path
- Evidence provider integration (`evidence_provider` is accepted but untested)
- Deep mode bypass (orchestrator should be disabled when `deep_llm` is provided)
- `_pad_subqueries` tool-split logic correctness
- Sub-query anti-confirmatory validator triggering from LLM output

### O-4: Code quality is good

- New classes follow existing codebase patterns (async generator → `get_finding()` contract)
- Error handling is consistent (broad `except Exception` with `BLE001` noqa, matching `research_agent.py`)
- No import cycles detected
- `ruff check` passes clean on all new files
- Pydantic v2 models with proper validators
- TYPE_CHECKING guards used correctly for circular import avoidance

### O-5: PartialFinding correctly scoped as ephemeral

The `PartialFinding`, `PartialClaim`, and `SubQuery` models live in `models/sub_research.py` and never appear in the `StructuredFinding` contract. The docstring correctly notes "downstream stages never see them." This preserves the architectural boundary.

### O-6: The `_AllSubAgentsFailedError` naming

The class uses a leading underscore (private convention) but is imported in `agent_pool.py` and `test_lead_sub_researcher.py`. If it's part of the cross-module interface, it should be renamed `AllSubAgentsFailedError`. Minor naming issue.

---

## 5. Prompt Quality Assessment

### plan_subqueries.md
- **Strengths:** Specifies 3 sub-queries, requires different evidence types, enforces anti-confirmatory framing, mandates tool coverage.
- **Weaknesses:** Drives source-universe diversity (good) but not methodology diversity (M-2). Doesn't encode different *reasoning procedures* per sub-query. Doesn't reference the "methodology > persona" finding (D2, DMAD ICLR 2025). Output format is correct (JSON array).
- **Quality vs. expanded prompts:** Below the bar set by the Phase A/B/C prompt audit. The expanded methodology prompts in L1.5 (after audit) are 15-30 sentences encoding actual analytical procedures. This prompt is closer to the pre-audit quality level.

### sub_synthesis.md
- **Strengths:** Methodology-scoped, includes confidence calibration, anti-confirmatory instruction, citation enforcement.
- **Weaknesses:** Thinner than the expanded `synthesis.md` (M-1). Lacks round-over-round synthesis (sub-researchers run 2 rounds), lacks the herding caveat, lacks the decision-usefulness filter.
- **Quality vs. synthesis.md:** ~60% of the instructional density.

### lead_synthesis.md
- **Strengths:** Explicit "CLAIM COLLATION, not averaging" instruction. Contradiction tagging preserved. Citation union instructions clear. Confidence calibration for merged claims is well-structured. Absence report synthesis instruction is good.
- **Weaknesses:** Doesn't instruct SUB-NNN stripping (M-3). Doesn't reference which methodology produced which claim in the output format (the `contradiction_note` field does reference methodology, but there's no `source_methodology` field on regular claims).
- **Quality vs. expanded prompts:** Solid. This is the strongest of the three new prompts.

---

## 6. Integration Risk Summary

| System | Risk | Severity |
|---|---|---|
| **Checkpoint (GAP-17)** | New events silently dropped on resume | **BLOCKING** (B-3) |
| **Token accounting (GAP-02)** | Sub-agent tokens are accumulated correctly in `StructuredFinding.tokens_consumed` | OK |
| **Cost ceiling (GAP-08)** | 50K ceiling will routinely trigger for orchestrated tasks | **HIGH** (H-3) |
| **Evidence filtering (GAP-03)** | `evidence_provider` is wired through to sub-researchers | OK (untested) |
| **UI event mapping** | New events not in UI-ARCHITECTURE.md | **MEDIUM** (M-5) |
| **CitationProcessor** | Dummy citations with ref:// URLs will fail liveness checks | **BLOCKING** (B-1) |

---

## Verdict: SHIP WITH FIXES

The architecture is sound. The two-tier pattern is correctly implemented with proper isolation, asyncio.gather dispatch, and additive event design. The code quality is good and follows existing codebase patterns. 7 of 10 invariants hold cleanly.

**However, three issues must be resolved before enabling `l1_orchestrator_enabled=True`:**

1. **B-1 (Citation chain):** Without real citations passing through PartialFinding, orchestrated tasks produce findings with fake URLs that will fail downstream processing. This is the most architecturally significant fix — it requires adding a `citations` field to `PartialFinding` and mapping refs to real citations in the Lead's merge.

2. **B-2 (Governance flag):** The silent fallback violates invariant #4 and means operators have no signal when orchestrated dispatch degrades. Quick fix — emit a governance flag in the except blocks.

3. **B-3 (Checkpoint serialization):** Three lines of imports + three entries in a list. Trivial but must be done.

The HIGH issues (H-1 through H-6) should be addressed before the first production pipeline run with the flag enabled, particularly H-1 (PipelineConfig exposure for UI) and H-4 (sub-agent timeout).

**Estimated fix effort:** B-1 is ~2 hours. B-2 and B-3 are ~30 minutes combined. HIGH issues are ~1 day total.
