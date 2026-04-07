# Current State
*Last updated: 2026-04-07 | Updated by: Session 16 (Planning/Orchestrator)*

---

## Where we are

**Phase:** Phase 1 build complete. All structural testing done. First real end-to-end pipeline run was IN PROGRESS when session was killed (machine transport).

**Build status:** 10 components + pipeline orchestrator + LLM client factory + markdown renderer. 722 unit tests + 108 integration tests. All passing. Provider migrated from Anthropic to OpenAI (Codex OAuth via ChatGPT Pro).

**Wave 4a (component pressure tests):** COMPLETE. All 4 sessions audited. 8 bugs found and fixed total. GPT-5.4 produces valid JSON for all prompts. Real Exa/Brave search works via SimpleMCPClient. Evaluator scoring works but is artificially low (~44/100 for good input) due to citation metadata gap.

**Wave 4b (full pipeline integration):** Session 13 was IN PROGRESS when killed. The prompt is ready at WAVE-4B-PIPELINE-INTEGRATION-PROMPT.md. Re-launch it.

## What needs to happen next (in order)

### 1. Re-launch Session 13: Full Pipeline Integration
The prompt is in WAVE-4B-PIPELINE-INTEGRATION-PROMPT.md. This session runs the complete L0->L1->CitProc->L1.5->L4->Markdown pipeline with real GPT-5.4 + real Exa/Brave search. It saves all artifacts to output/first_real_run/. It was killed before completing.

### 2. Fix Citation Metadata Gap (autonomous, after Session 13)
The evaluator pressure test (Session 11) revealed that:
- FActScore (Layer 1) is non-functional: 0/63 facts verified because citations carry only title + publication, no content excerpts
- Source quality (Layer 3) scores ~10/100 because citations lack url_live, crossref_verified, domain authority metadata
- This causes geometric mean to drag ALL scores to ~44, making the 60-point pass threshold unreachable

Fix requires:
- Research agents capture content_snippet from search results
- CitationProcessor populates url_live, crossref_verified on each citation
- Citation model may need a content_snippet field added

This is one targeted session after Session 13 completes.

### 3. Jack Reviews the Deliverable
Read output/first_real_run/deliverable.md as a consultant. Score it. This is Phase 1 Done criterion #8: "at least one test engagement produces output that Jack rates as approaching Keystone quality (>= 70/100)."

### 4. Evaluator Calibration (Component #10)
After Jack scores 10+ real outputs, calibrate the evaluator's rubric against his human scores. Needs 0.80+ Spearman correlation.

## What's complete

| Component | Status | Tests |
|-----------|--------|-------|
| #1 RESEARCH.md format | Built | Model tests |
| #2 Citation model + utils | Built | ~30 unit + 13 integration |
| #3b Knowledge accumulation | Built | 45 unit |
| #4 MCP Gateway | Built | 75 unit + SimpleMCPClient for real search |
| #5 Specification Engine (L0) | Built + pressure tested | 58 unit + 41 integration |
| #6 Evaluator Stack (L4) | Built + pressure tested | 77 unit + 25 integration |
| #7 Research Agent Pipeline | Built + pressure tested | 64 unit + 16 integration |
| #8 CitationProcessor | Built + pressure tested | 15 unit + 13 integration |
| #9 Deliberation | Built + pressure tested | 78 unit + 14 integration |
| #HITL | Built | 42 unit |
| Pipeline Orchestrator | Built | 27 unit + 1 e2e mock |
| LLM Client Factory | Built + smoke tested | 33 unit + 3 integration |
| Markdown Renderer | Built | 15 unit |

**Total: 722 unit tests + 108 integration tests = 830 tests**

## Known architectural gaps (from Wave 4a pressure testing)

1. **Citation metadata gap:** FActScore and source_quality scoring require content excerpts + verification metadata that aren't captured. Root cause: research agents store title/URL but not content snippets from search results.
2. **Task count below spec:** GPT-5.4 produces ~13 tasks (spec says 15-50). Prompt tuning needed, not a code bug.
3. **Codex OAuth latency:** 680-900s per full evaluation. Standard API key would be faster. Jack chose OAuth-only for now.
4. **URL liveness rate:** 62% for research citations. Market research sites block HEAD requests. Not a code bug.

## Key files for orientation

- CLAUDE.md -- auto-loaded, project overview
- JACK-ARCHITECTURAL-DIRECTIVES.md -- authoritative design decisions
- CAPSTONE-PLAN-v2.md -- architecture source of truth
- OPENAI-SWITCHOVER-PLAN.md -- OpenAI migration spec
- WAVE-4B-PIPELINE-INTEGRATION-PROMPT.md -- prompt to re-launch for Session 13
- audit/PHASE-1-IMPLEMENTATION-SPEC.md -- component specs + acceptance criteria
- docs/ARCHITECTURE.md -- code architecture (needs regeneration)
- reference/BUILD-PRACTICES-PLAYBOOK.md -- parallel session management patterns

## What's blocked

| Blocker | Needed for | Action |
|---------|-----------|--------|
| Session 13 completion | First real deliverable | Re-launch the prompt |
| Citation metadata fix | Realistic evaluator scores | One targeted session after Session 13 |
| Jack's quality review | Evaluator calibration (#10) | Read deliverable.md when produced |
| Jack's casing ebooks | Directive 12 skill file | Drop PDFs in reference/casing-books/ |

## Auth setup (confirmed working)

- Codex CLI: v0.118.0, logged in via ChatGPT Pro
- ~/.codex/auth.json: valid, refresh_token present
- .env: OPENAI_AUTH_TYPE=codex_oauth, CODEX_AUTH_FILE=~/.codex/auth.json
- Models confirmed accessible: gpt-5.4, gpt-5.4-mini (smoke test passed)
- Search APIs: EXA_API_KEY and BRAVE_SEARCH_API_KEY configured and tested
