# Jack's Pre-Build Reading List

*Produced: 2026-04-05 | Session C (pre-build audit)*

The scaffolding is architecturally sound. Code audit found 0 NEEDS REWORK ratings, 7 NEEDS MINOR FIXES (all fixable in 1-2 hours). This list is calibrated accordingly: focused on decision review, not damage control.

---

## Priority 1: Must read before building

### 1. `audit/pre-build/05-execution-readiness.md` (this session's output)
- **Why:** Synthesizes all audit findings into a build/no-build decision with specific action items.
- **What to look for:** Whether the recommended build sequence matches your intuition. Whether the "over-engineered" flags resonate or feel wrong.
- **Read time:** 10 min
- **Depends on:** Nothing

### 2. `CAPSTONE-PLAN-v2.md` -- Sections 2-5 only (lines ~100-700)
- **Why:** This is the source of truth. Every model, contract, and event in the codebase derives from it. You haven't reviewed the 17 research-backed changes from Session 1.
- **What to look for:** The deliberation redesign (Section 4.3) -- do you agree independent parallel analysis is better than debate for your use case? The 10-dimension rubric weights (Section 5.3) -- the weights sum to 110% (math error), and Session B flagged this. The 5-tier confidence taxonomy (Section 4.3) -- is this the right granularity for consulting deliverables?
- **Read time:** 25-30 min
- **Depends on:** Nothing

### 3. `audit/PHASE-1-IMPLEMENTATION-SPEC.md` -- Components #1-#4 only (first ~270 lines)
- **Why:** These are the specs you'll be building against starting tomorrow. The acceptance criteria and I/O contracts are what your builder agents will target.
- **What to look for:** Component #3 (pgvector + hybrid search) is scoped as L (1-2 weeks). Is that realistic for 6 weeks total? The Semantic Router for query classification, Docling for PDF parsing, Bifrost-pattern caching -- are all three needed for MVP, or can any be deferred? Component #4 lists 6 MCP servers -- do you have or can you get API keys for Exa, Brave, FRED, and EdgarTools?
- **Read time:** 15 min
- **Depends on:** Reading #2 first gives context

---

## Priority 2: Read within first few days

### 4. `audit/pre-build/02-code-audit.md`
- **Why:** Details every issue in the scaffolding code. The HIGH-severity items (TYPE_CHECKING bug, env_prefix mismatch) need fixing before any model instantiation works.
- **What to look for:** The systematic TYPE_CHECKING bug affects 3 model files. Estimated 15-minute fix but must happen first. The rubric weights sum error is inherited from the plan itself -- you'll need to decide which dimension to adjust.
- **Read time:** 12 min
- **Depends on:** Nothing

### 5. `audit/pre-build/01-deep-research-gap-analysis.md`
- **Why:** The LEAK-SYNTHESIS.md that informed the scaffolding is ~60-65% complete. Five decision-changing findings were missed. Most affect Components #4 and #7 (not #1-#2), so they're not blocking immediate work.
- **What to look for:** The 5-6 decision-changing items listed in the executive assessment. Decide whether the full re-analysis (prompt in `06-deep-research-analysis-prompt.md`) should run before or in parallel with Components #1-#2.
- **Read time:** 15 min
- **Depends on:** Nothing

### 6. `docs/ARCHITECTURE.md`
- **Why:** The module map and dependency rules are the structural backbone. The coherence check at the bottom maps all 11 components to their models and contracts.
- **What to look for:** The 3 noted gaps (SearchQuery/SearchResults, ToolCall/ToolResult, Outline/SectionDraft). The dependency DAG: does the layering make sense to you?
- **Read time:** 8 min
- **Depends on:** Skim #2 first

---

## Priority 3: Skim when relevant

### 7. `reference/analysis/LEAK-SYNTHESIS.md`
- **Why:** 45KB of findings from the Claude Code leak mapped to your pipeline. Useful reference during Component #4 and #7 building, but the gap analysis (#5 above) is the more important read.
- **What to look for:** Section 4 (MCP Gateway patterns) when building Component #4. Section 5 (agent isolation patterns) when building Component #7.
- **Read time:** 20 min (skim), 45 min (full)
- **Depends on:** Read #5 first to know what's missing

### 8. `reference/analysis/09-implementation-recommendations.md`
- **Why:** Maps all 11 components to concrete nano-claude-code implementation patterns. The bridge between "what the plan says" and "how Claude Code actually implemented similar things."
- **What to look for:** The 5 ADOPT patterns. Whether the recommended patterns feel over-engineered for a 6-week capstone.
- **Read time:** 10 min
- **Depends on:** Nothing

---

## Total estimated reading time: ~2-3 hours

Priority 1 (must-read): ~50-55 min
Priority 2 (first few days): ~35 min
Priority 3 (when relevant): ~30 min skim
