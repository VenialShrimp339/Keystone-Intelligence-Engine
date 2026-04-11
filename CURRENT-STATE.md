# Current State
*Last updated: 2026-04-11 | Updated by: Session 20 (Wave 1 Implementation)*

---

## Where we are

**Phase:** Wave 1 complete (1A + 1B + 1C). Wave 2A is next.

**What happened today (April 11, Session 20):**
1. Implemented Waves 1A, 1B, 1C using agent teams (Lead + Implementer + Reviewer)
2. 6 commits, 38 source+test files changed, 52 new tests added (721 -> 773)
3. 3 adversarial reviews (2 Codex, 1 internal) caught 4 regressions, all fixed
4. Key fixes: per-run lifecycle isolation, unified JSON parsing (6 extractors -> 1), citation identity with dual-layer IDs, partial-claim salvage, HITL event emission

## What needs to happen next (in order)

### 1. Wave 2A: Citation Identity Completion (Decision A pt.2)
Start a fresh session. This is the most file-heavy wave.

Deliverables:
1. Aggregator: `aggregated_claim_id`, `task_ids`, fixed `corroboration_count` semantics
2. ConfidenceBuilder: copy provenance into tier claims, build `provenance_index`
3. Deliberation consumes manifest + canonicalized findings
4. Orchestrator filters confidence_map + manifest by task provenance
5. `metadata_hash` migration (phase 2 of `content_hash` rename) -- touches 8+ files
6. PostSynthesisVerifier contract definition
7. Mint fresh canonical IDs in dedup (deferred from Wave 1C Codex review)

Files to modify: `aggregator.py`, `confidence_builder.py`, `deliberation.py`, `orchestrator.py`, `hash.py`, `citation/__init__.py`, `wiki_builder.py`, `engagement_store.py`, `content_hasher.py`, `wiki_schema.py`, `dedup.py`, `models/confidence.py`, plus test files.

### 2. Codex Review of Wave 2A
After Wave 2A completes, run adversarial review scoped to the wave diff.

### 3. Wave 2B: Enforcement Model (Decision B)
Highest-risk wave. Depends on 2A provenance fields. GovernanceState, ProfileExecutionPolicy, enforcement matrix, coverage policy, task outcomes.

### 4. Waves 3-4
Wave 3: Deep research events, DAG scheduling, post-synthesis verifier, remaining concurrency items. Wave 4: Polish, documentation, dead code cleanup.

## Remediation tracking

| Phase | Status |
|-------|--------|
| Phase 1A-1D: Audit + issue consolidation | Complete |
| Phase 2: Architectural decisions | Complete (FINAL-DECISIONS-v2.md) |
| Phase 3 Wave 1A: Lifecycle + concurrency | **Complete** (commit `9893a4d`) |
| Phase 3 Wave 1B: LLM parsing | **Complete** (commits `0344fb2`, `884552f`) |
| Phase 3 Wave 1C: Citation identity foundation | **Complete** (commit `1583d03`) |
| Post-Wave 1 Codex fixes | **Complete** (commit `38bba2a`) |
| Phase 3 Wave 2A: Citation identity completion | **Next** |
| Phase 3 Wave 2B: Enforcement model | Pending |
| Phase 3 Wave 3: Completeness | Pending |
| Phase 3 Wave 4: Polish | Pending |
| Phase 4: Final validation | Pending |

## Architecture summary

```
L0 (Spec Engine)    -> claude -p --tools "" --model opus    (fast, controlled reasoning)
L1 (Research)       -> claude -p --allowedTools "WebSearch,WebFetch" --model sonnet  (deep multi-turn web research)
L1.5 (Deliberation) -> claude -p --tools "" --model sonnet/opus  (fast, controlled reasoning)
L4 (Evaluator)      -> claude -p --tools "" --model opus    (fast, controlled reasoning)
```

All on Max subscription. Zero API cost.

## What's complete

| Component | Status | Tests | Wave 1 Changes |
|-----------|--------|-------|----------------|
| #1 RESEARCH.md format | Built | 54 unit | -- |
| #2 Citation model + utils | Built | 61 unit + 13 integration | 1C: metadata_hash, merged_from_ids, CitationAlias, aliases on manifest |
| #3b Knowledge accumulation | Built | 45 unit | -- |
| #4 MCP Gateway | Built | 75 unit | 1A: circuit breaker HALF_OPEN fix, BaseException |
| #5 Specification Engine (L0) | Built + tested | 58 unit + 41 integration | 1B: safe_llm_json in all 6 spec/ files |
| #6 Evaluator Stack (L4) | Built + tested | 77 unit + 25 integration | 1B: safe_llm_json, ParseError instead of silent defaults |
| #7 Research Agents (L1) | Built + deep research | 64 unit + 16 integration | 1B: safe_llm_json. 1C: engagement-unique citation IDs, citation_refs, claim_id minting, partial-claim salvage |
| #8 CitationProcessor | Built + tested | 15 unit + 13 integration | 1C: CitationProcessorResult, alias map, canonical rewrite, deduplicate_with_aliases |
| #9 Deliberation (L1.5) | Built + tested | 78 unit + 14 integration | 1A: per-analyst exception handling. 1B: safe_llm_json |
| #HITL | Built | 42 unit | 1C: event emission (Created/Approved/Modified/Rejected) |
| Pipeline Orchestrator | Built + deep wiring | 27 unit + 1 e2e | 1A: per-run lifecycle via PipelineComponents. 1C: ErrorRecovery wiring, canonicalized findings |
| LLM Client (Claude CLI) | Built | 35 unit + 3 integration | 1A: subprocess cleanup with asyncio.shield |
| LLM Parsing (NEW) | Built | 23 unit | 1B: safe_llm_json, parse_llm_bool, ParseError |
| Markdown Renderer | Built | 15 unit | -- |
| **Total** | **11 components** | **773 unit + ~120 integration** | |

## Known gaps (honest assessment)

| Gap | Impact | Fix Wave | Status |
|-----|--------|----------|--------|
| Canonical IDs = source-instance IDs | Unstable canonical layer | 2A | Deferred |
| metadata_hash migration incomplete | content_hash overloaded | 2A | Deferred |
| Provenance not carried through confidence | Can't trace claims to tasks | 2A | Deferred |
| Evaluator fail-open on ParseError | Broken parsing looks "clean" | 2B | Deferred |
| Enforcement gates all fail-open | Quality signals advisory only | 2B | Deferred |
| ErrorRecovery wired but not called | No model-tier fallback at runtime | 2B | Deferred |
| Analyst failure inflates confidence | 3/4 agreement becomes 3/3 | 2B | Deferred |
| HITL modify is dead code | Human modifications ignored | 2B | Deferred |
| ReviewDecisionSubmitted not emitted | Submission timestamp not observable | 2B | Deferred |
| ParseError not retried | Transport retries only | 2B | Deferred |
| Dead HALF_OPEN branch in _record_failure | Misleading code | 4 | Deferred |
| 5/7 MCP tools are stubs | Shallow mode limited | Low priority | -- |
| No web UI | Terminal only | Phase 2 | -- |

## Key files for orientation

- `CLAUDE.md` -- Auto-loaded project instructions with verification rules
- `CURRENT-STATE.md` -- This file
- `JACK-ARCHITECTURAL-DIRECTIVES.md` -- 14 authoritative design directives
- `SESSION-LOG.md` -- Full session history (Sessions 1-20)
- `CAPSTONE-PLAN-v2.md` -- Architecture source of truth (1,294 lines)
- `audit/remediation/decisions/FINAL-DECISIONS-v2.md` -- Implementation-ready decisions
- `audit/remediation/BUILD-PROCESS.md` -- How to build without repeating mistakes
- `audit/remediation/AGENT-TEAMS-SETUP.md` -- Agent team configuration for implementation
- `audit/remediation/WAVE1-FULL-ADVERSARIAL-REVIEW-PROMPT.md` -- Full Wave 1 review prompt (reusable pattern)

## Auth setup

- Claude CLI: Max subscription, authenticated via `claude login`
- LLM_PROVIDER=claude_cli in .env
- ANTHROPIC_API_KEY: NOT SET (critical -- setting it switches to API billing)
- Models: claude-opus-4-6 (flagship), claude-sonnet-4-6 (standard), claude-haiku-4-5 (fast)
- Search APIs: EXA_API_KEY and BRAVE_SEARCH_API_KEY in .env
- Deep research: DEEP_RESEARCH=1, DEEP_RESEARCH_TIMEOUT=1200
