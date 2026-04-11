# Folder Inventory: Claude-Generated Project Files

*Produced: 2026-04-05 | Session C (pre-build audit)*

Scope: Files created or modified by Claude Code or Cowork sessions. Excludes input corpus (research-reports/, nate-synthesis/, source-analysis/, quality-audits/, reference/nano-claude-code/).

---

## Project Root

| File | Tag | Notes |
|------|-----|-------|
| `CLAUDE.md` | **CURRENT** | Auto-loaded. Restructured in Session 3, updated in Session 7. Accurate. |
| `CURRENT-STATE.md` | **CURRENT** | Living snapshot. Updated Session 7. Accurate post-scaffolding. |
| `SESSION-LOG.md` | **CURRENT** | 7 entries through Session 7. Will be updated by this session. |
| `SESSION-HANDOFF-SCAFFOLDING.md` | **ARCHIVE** | Detailed Session 6 handoff. Content fully captured in SESSION-LOG.md Session 6 entry + CURRENT-STATE.md. Useful as reference but clutters root. |
| `COWORK-SESSION-HISTORY-CONDENSED.md` | **ARCHIVE** | 60-page Cowork chat condensed. Historical value only. Planning decisions are captured in CAPSTONE-PLAN-v2.md and SESSION-LOG.md Session 3. |
| `CAPSTONE-PLAN-v2.md` | **CURRENT** | Source of truth (1,294 lines). Updated in Session 1 with 17 changes. |
| `CAPSTONE-PLAN.md` | **ARCHIVE** | Original pre-synthesis plan. Superseded entirely by v2. |
| `KICKOFF-PROMPT.md` | **ARCHIVE** | Original project kickoff. Historical context only. |
| `README.md` | **REVIEW** | Predates all Claude sessions. May not reflect current architecture. Jack should verify it matches the project's actual scope and framing before any public sharing. |
| `RESEARCH-PROMPTS-FINAL.md` | **ARCHIVE** | The 16 prompts that generated the original research reports. Historical. Useful for cross-referencing findings but not needed day-to-day. |
| `pyproject.toml` | **CURRENT** | Session 6. Needs dependency version verification on Python 3.11-3.12 (flagged in code audit). |
| `.env.example` | **CURRENT** | Session 6. Has env_prefix mismatch with config.py (flagged in code audit, HIGH severity). |
| `Makefile` | **CURRENT** | Session 6. Standard targets. `run` target references nonexistent module (acceptable placeholder). |

---

## `.claude/`

| File | Tag | Notes |
|------|-----|-------|
| `settings.json` | **CURRENT** | Model config, permissions, env overrides. |
| `agents/research-analyst.md` | **CURRENT** | Session 3. Agent definition for research synthesis subagent. |
| `agents/synthesis-lead.md` | **CURRENT** | Session 3. Agent definition for synthesis lead subagent. |
| `skills/research-synthesis/SKILL.md` | **CURRENT** | Session 3. Methodology for analyzing research reports. |
| `skills/architecture/SKILL.md` | **STALE** | Session 3. Contains 5 references to "Rejection Library" (should be "Observation Library"), 3 references to "8-dimension rubric" (should be "10-dimension"). These stale terms were updated everywhere else in Sessions 1-2 but this skill file was written before those updates propagated. |

---

## `audit/`

| File | Tag | Notes |
|------|-----|-------|
| `PHASE-1-IMPLEMENTATION-SPEC.md` | **CURRENT** | Session 2, updated Session 6 with 4 LEAK-SYNTHESIS UPDATE tags. Source of truth for build specs. |
| `GAP-TRIAGE.md` | **CURRENT** | Session 2. 8 gaps triaged. None block Phase 1. |
| `PLAN-AUDIT.md` | **CURRENT** | Session 2. Consistency audit of CAPSTONE-PLAN-v2.md. Documents 3 fixes applied + 6 evidence caveats. |
| `SESSION-CONTEXT.md` | **REDUNDANT** | Session 2. Explicitly superseded by CURRENT-STATE.md (see CURRENT-STATE.md line 4). Same orientation purpose, less information. |
| `pre-build/01-deep-research-gap-analysis.md` | **CURRENT** | Session A (today). Gap analysis of LEAK-SYNTHESIS.md vs source reports. |
| `pre-build/02-code-audit.md` | **CURRENT** | Session B (today). File-by-file audit of scaffolding code. |
| `pre-build/06-deep-research-analysis-prompt.md` | **CURRENT** | Session A output. Ready-to-paste prompt for full deep research re-analysis. |

---

## `synthesis/`

| File | Tag | Notes |
|------|-----|-------|
| `UNIFIED-SYNTHESIS.md` | **CURRENT** | Session 1. Cross-thread synthesis of 16 original research reports. ~80 tool verdicts. |
| `PLAN-CHANGELOG.md` | **CURRENT** | Session 1. Documents all 17 research-backed changes to the plan. |
| `thread-a-1-analysis.md` through `thread-d-16-analysis.md` (16 files) | **ARCHIVE** | Session 1. Per-report analyses feeding into UNIFIED-SYNTHESIS.md. Intermediate work products. Value is captured in the synthesis. Useful for audit trail but not needed for building. |

Note: Thread analyses contain "Rejection Library" terminology throughout. This is correct for their time of creation (pre-Session 1 terminology update). They are historical analysis documents, not active reference material.

---

## `reference/analysis/`

| File | Tag | Notes |
|------|-----|-------|
| `00-master-index.md` | **CURRENT** | Session 4. Quick-reference for all repo analysis findings. |
| `01-core-architecture.md` through `09-implementation-recommendations.md` (10 files) | **CURRENT** | Session 4. nano-claude-code analysis outputs. Implementation-relevant patterns for Components #4, #5, #7, #9, #11. |
| `deep-research-01-agent-teams.md` through `deep-research-10-agent-sdk-hybrid.md` (10 files) | **CURRENT** | Session 5 (research), Session 6 (renamed). Source reports for leak analysis. Gap analysis (Session A) references these. |
| `deep-research-rename-map.md` | **CURRENT** | Session 6. Maps opaque compass_artifact filenames to descriptive names. |
| `LEAK-SYNTHESIS.md` | **REVIEW** | Session 6. 45KB synthesis of leak research. Session A rated it ~60-65% complete with 5-6 decision-changing findings missed. Still useful as a starting reference but should not be treated as comprehensive. Jack should be aware of the gap analysis findings before relying on this. |

---

## `src/keystone/`

| File | Tag | Notes |
|------|-----|-------|
| `__init__.py` | **CURRENT** | Session 6. Package root, version 0.1.0. |
| `events.py` | **CURRENT** | Session 6. 29 typed pipeline events. Code audit: SOLID. |
| `contracts.py` | **CURRENT** | Session 6. 8 Protocol-based contracts. Code audit: SOLID. |
| `models/__init__.py` | **CURRENT** | Session 6. Code audit: NEEDS MINOR FIXES (missing re-exports, no model_rebuild calls). |
| `models/citations.py` | **CURRENT** | Session 6. Code audit: SOLID. |
| `models/tasks.py` | **CURRENT** | Session 6. Code audit: SOLID. |
| `models/research.py` | **CURRENT** | Session 6. Code audit: NEEDS MINOR FIXES (TYPE_CHECKING bug). |
| `models/evaluation.py` | **CURRENT** | Session 6. Code audit: NEEDS MINOR FIXES (rubric weights sum to 1.05). |
| `models/observations.py` | **CURRENT** | Session 6. Code audit: NEEDS MINOR FIXES (TYPE_CHECKING bug). |
| `models/confidence.py` | **CURRENT** | Session 6. Code audit: SOLID (borderline, same TYPE_CHECKING pattern). |
| `models/agents.py` | **CURRENT** | Session 6. Code audit: SOLID. |
| `models/config.py` | **CURRENT** | Session 6. Code audit: NEEDS MINOR FIXES (env_prefix mismatch, str instead of enum). |

Empty pipeline module directories (Session 6 scaffolding, all empty): `agents/definitions/`, `citation/`, `deliberation/`, `evaluator/`, `gateway/`, `generation/`, `meta/`, `retrieval/`, `specification/`, `structuring/`, `tools/`. All **CURRENT** -- placeholders matching ARCHITECTURE.md planned structure.

---

## `docs/`

| File | Tag | Notes |
|------|-----|-------|
| `ARCHITECTURE.md` | **CURRENT** | Session 6. Code architecture, module map, dependency rules, coherence check. Code audit: SOLID. |

---

## `tests/`

| File | Tag | Notes |
|------|-----|-------|
| `__init__.py` | **CURRENT** | Session 6. Empty init. |
| `unit/__init__.py` | **CURRENT** | Session 6. Empty init. |
| `unit/models/__init__.py` | **CURRENT** | Session 6. Empty init. |
| `integration/__init__.py` | **CURRENT** | Session 6. Empty init. |
| `e2e/__init__.py` | **CURRENT** | Session 6. Empty init. |

Empty test subdirectories (Session 6 scaffolding): `unit/agents/`, `unit/citation/`, `unit/deliberation/`, `unit/evaluator/`, `unit/gateway/`, `unit/retrieval/`, `unit/specification/`. All **CURRENT** -- ready for test files during build.

---

## Other Directories

| Directory | Tag | Notes |
|-----------|-----|-------|
| `calibration/` | **CURRENT** | Session 6. Empty subdirs: `calibration_samples/`, `canary_set/`, `scoring_worksheet/`. Placeholders for Component #10 (evaluator calibration). |
| `scripts/` | **CURRENT** | Session 6. Empty. Placeholder for build/deploy scripts. |
| `templates/` | **CURRENT** | Session 6. Empty. Placeholder for RESEARCH.md template (Component #1). |

---

## MISSING Files

| File | Why it should exist | When to create |
|------|--------------------|----------------|
| `src/keystone/retrieval/` models (SearchQuery, SearchResults) | Noted as gap in Session 6 and code audit. Needed for Component #3. | When building Component #3. |
| `src/keystone/gateway/` models (ToolCall, ToolResult) | Same. Needed for Component #4. | When building Component #4. |
| `src/keystone/structuring/` models (Outline, SectionDraft) | Same. Needed for Component #2/L2. | When building L2. |

---

## Recommended Cleanup Actions

**Delete (redundant):**
1. `audit/SESSION-CONTEXT.md` -- explicitly superseded by CURRENT-STATE.md. Contains accurate but less complete information.

**Archive (move to `archive/` folder):**
2. `CAPSTONE-PLAN.md` -- original v1 plan, fully superseded by v2.
3. `KICKOFF-PROMPT.md` -- historical kickoff, no build relevance.
4. `COWORK-SESSION-HISTORY-CONDENSED.md` -- historical planning session, decisions captured elsewhere.
5. `SESSION-HANDOFF-SCAFFOLDING.md` -- detailed Session 6 notes, content in SESSION-LOG.md.
6. `RESEARCH-PROMPTS-FINAL.md` -- original 16 research prompts, reference-only.
7. `synthesis/thread-*-analysis.md` (16 files) -- intermediate work products, value captured in UNIFIED-SYNTHESIS.md.

**Update (stale terminology):**
8. `.claude/skills/architecture/SKILL.md` -- Replace "Rejection Library" with "Observation Library" (5 occurrences). Replace "8-dimension rubric" with "10-dimension rubric" (3 occurrences).

**Fix before building (from code audit):**
9. Fix TYPE_CHECKING imports in research.py, observations.py, confidence.py (or add model_rebuild() in __init__.py).
10. Fix env_prefix mismatch between config.py and .env.example.
11. Fix RUBRIC_WEIGHTS sum (1.05 -> 1.00) in evaluation.py.

**No action needed:**
- "Rejection Library" references in synthesis/thread-* files are historical and correct for their context.
- "Rejection Library" in CAPSTONE-PLAN-v2.md lines 763, 1178, 1267 are historical ("expanded from Rejection Library") per PLAN-AUDIT.md.
- "Rejection Library" in CLAUDE.md is correct usage ("Observation Library -- Expanded from Rejection Library").
