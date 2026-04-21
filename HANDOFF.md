# HANDOFF — KIE Gap Remediation

## What this is

Gap-remediation workflow for the Keystone Intelligence Engine. A prior CC
session produced a pipeline atlas and 17-gap audit from Nate Jones corpus
analysis. Four Deep Research reports on OpenClaw and Claude Code
architectures were run externally. This session verifies the gaps and
begins implementation.

**Branch:** `codex/owner-triage-normalization`

**Prior commits (already landed):**
- `1004147` pipeline gap audit from Nate corpus
- `d941291` Nate substack corpus (78 articles)
- `88a20b2` pipeline atlas
- `311d317` L3 deliverable generation build plan

## Reading order

1. `notes/PIPELINE-ATLAS.md` — current KIE state, 651 lines
2. `research/external-sources/nate-jones/2026-02-to-04-audit/GAP-AUDIT.md`
   — 17 gaps (7 P0 / 6 P1 / 4 P2)
3. Deep Research reports at
   `research/external-sources/openclaw-claude-code/s{1,2,3,4}/deep-research-report.md`
   — only needed for Tier 2 gaps (see below)

## Gap tiers

Gaps are tiered by what kind of work they need, not by subsystem.

### Tier 1 — "Just fix it" (~1 day each, no external research needed)

These are consistency fixes where the code declares one thing and does
another at runtime. Read the atlas, read the gap, read the affected
files, make the change.

| Gap | Short title | What's wrong |
|-----|------------|--------------|
| GAP-01 | Model tier routing | Spec engine assigns flagship/standard tier per task, agent pool ignores it and runs everything at standard |
| GAP-02 | Token accounting | Gateway reports tool token costs as hardcoded zero |
| GAP-04 | Client namespacing | client_id exists on every event but nothing uses it to namespace |
| GAP-06 | MECE halt | MECE validation failure logs warning and continues instead of halting |
| GAP-07 | Dead-letter flags | Tool call retry exhaustion silently swallowed instead of named failure mode |
| GAP-08 | Cost governance | Related to GAP-02, cost tracking fields exist but values are fake |
| GAP-10 | Prompt externalization | L1 research agent prompts buried in Python, every other layer uses versioned markdown |
| GAP-11 | Model-version annotation | No prompt tracks which model version it was tuned against |
| GAP-12 | Retrieval hybrid config | Retrieval stack semantic/keyword split not configured properly |

### Tier 2 — "Design then fix" (~1-3 days each, DR reports useful)

These need design thinking informed by how production systems solved the
same problems. Each gets its own CC session with its relevant DR report.

| Gap | Short title | Relevant DR report |
|-----|------------|--------------------|
| GAP-03 | Evidence filtering | S3 (memory report) — relevance filtering between retrieval and injection |
| GAP-05 | Observation Library | S3 (memory report) — post-run write-back, OpenClaw dreaming as reference |
| GAP-09 | Evaluator calibration | S4 (evaluator report) — LLM-as-judge calibration, threshold tuning |
| GAP-13 | HITL write-back | S3 (memory report) — persisting human modifications |
| GAP-15 | Deep-mode gateway | S1 (token economics) — MCP mediation for web-search tool calls |
| GAP-17 | Checkpoint/resume | S2 (prompt versioning) — session recovery semantics |

### Tier 3 — Deferred

| Gap | Short title | Why deferred |
|-----|------------|--------------|
| GAP-14 | SDK transport | Currently on claude -p subprocess with Max subscription auth. SDK requires API key (pay-per-token). Decision: stay on subprocess. Revisit if/when moving to API billing. |
| GAP-16 | Prompt caching | Requires SDK transport (GAP-14) as prerequisite. Deferred with it. |

## Deep Research validation summary

All four reports validated by independent review. Key findings:

**S1 (Token Economics): MOSTLY CLEAN.** Core content on prompt caching
mechanics, cache-break vectors, and subagent taxonomy is well-sourced.
Don't trust: specific GitHub issue numbers, the "10.2% of fleet
cache-creation tokens" metric, per-model minimum cacheable token
thresholds (may be stale post-Opus 4.7).

**S2 (Prompt Versioning): MOSTLY CLEAN.** Bootstrap hierarchy, CLAUDE.md
injection mechanics, and founder quotes are verified. Don't trust:
`steipete.me` URL (should be `steipete.com`), the "isn't that just a cron
job / isn't love just evolutionary biology" exchange (likely fabricated),
Hanselminutes #1036 (unverified).

**S3 (Long-term Memory): CLEAN.** Best report. Every claim carries
explicit confidence. Correctly identifies KAIROS/autoDream as unshipped
leak artifacts. Corrects user framing on dreaming phase order (light ->
REM -> deep, not light -> deep -> REM). Dreaming signal weights
(0.30/0.24/0.15/0.15/0.10/0.06) not primary-sourced but appropriately
flagged.

**S4 (Evaluator Architectures): MOSTLY CLEAN.** Structural argument is
sound. Apollo Research scheming findings verified against their blog.
Don't trust: `.hidden_ethics_model.bin` filename (fabricated, actual
attested name is `model_28_05_2025.bin`), specific SOS-Bench correlation
coefficients and percentage drops (directionally correct but exact numbers
unverified), JudgeBench quote attribution.

**Cross-report consistency:** All four reports agree on shared topics
(SYSTEM_PROMPT_DYNAMIC_BOUNDARY, CLAUDE.md injection, OpenClaw JSONL
schema, KAIROS as unshipped). No circular sourcing detected.

**Rule for downstream use:** If a DR claim grounds on a source not in the
validated source list below, verify the source exists before building on
the claim. If a claim cites a specific GitHub issue number, treat the
issue number as decorative. The described behavior may be real but the
number is likely fabricated.

## Validated source list

- **sabrina.dev/p/claude-code-source-leak-analysis** — code-level leak
  analysis, all specific quotes verified
- **deepwiki.com/openclaw/openclaw** — 72-section code wiki with
  file:line refs. **Indexed Feb 13, 2026. Predates ContextEngine
  v2026.3.7, Task Brain v2026.3.31, Active Memory v2026.4.10.**
- **ccleaks.com** (/architecture, /explore, /news) — Claude Code source
  tree documentation
- **github.com/nblintao/awesome-claude-code-postleak-insights** — curated
  meta-list of post-leak analyses
- **robotpaper.ai** reference architecture (Roy Osherove, Feb 24 2026)
- **velvetshark.com/openclaw-memory-masterclass** — first-party, author
  is OpenClaw codebase maintainer
- **Anthropic prompt caching docs** at platform.claude.com
- **MCP spec** at modelcontextprotocol.io
- **Peter Steinberger** commentary (Lex Fridman #491, steipete.com)
- **Boris Cherny** commentary (howborisusesclaudecode.com, Lenny's
  Newsletter Feb 19 2026)

## Phase 0 — Gap verification

First action in this session. Single subagent.

For each of the 17 gaps in GAP-AUDIT.md, assign:
**CONFIRMED** / **DISPUTED** / **NEEDS_CLARIFICATION** with reasoning.

Priority: gaps that are novel to this audit, prescriptive rather than
observational, or span multiple layers. Light touch on gaps already in
TODO.md pre-audit.

Output: append `## Verification Status` section to GAP-AUDIT.md. One
commit: `docs: add gap verification status to audit`.

## After Phase 0 — session-per-fix execution

Do NOT batch all fixes into one session. Each fix (or small cluster of
closely related fixes) gets its own CC session for full context focus.

**For Tier 1 gaps:** New CC session per gap or pair. The session reads the
atlas, the gap audit with verification status, and the affected files.
Implements the fix. No DR reports needed.

Suggested Tier 1 pairings:
- GAP-01 alone (model tier routing)
- GAP-02 + GAP-08 (token accounting + cost governance)
- GAP-04 alone (client namespacing)
- GAP-06 + GAP-07 (MECE halt + dead-letter flags)
- GAP-10 + GAP-11 (prompt externalization + model-version annotation)
- GAP-12 alone (retrieval config)

**For Tier 2 gaps:** New CC session per gap. The session reads the atlas,
gap audit, the specific DR report for that gap, and the affected files.
Produces a short implementation design first, gets confirmation, then
implements.

Tier 2 sessions should read the DR validation notes in this document
before trusting DR content. When the DR report is thin or suspect on a
specific point, fall back to the validated source list.

## Sequencing guidance

Tier 1 fixes have no dependencies on each other or on Tier 2. They can
run in any order. Tier 2 gaps may benefit from Tier 1 fixes being done
first (e.g., GAP-05 Observation Library is easier to build after GAP-04
client namespacing is wired). Run Tier 1 before Tier 2 when practical.

Within Tier 2, the natural order is:
1. GAP-03 (evidence filtering) — lightest design work
2. GAP-13 (HITL write-back) — small but high-value
3. GAP-05 (Observation Library) — largest piece, benefits from GAP-13
4. GAP-09 (evaluator calibration) — empirical tuning, needs scored data
5. GAP-17 (checkpoint/resume) — robustness, not urgent
6. GAP-15 (deep-mode gateway) — MCP mediation, most complex

## Out of scope

- Live inspection of any OpenClaw instance
- Re-reading OpenClaw or Claude Code source from scratch
- GAP-14 (SDK transport) and GAP-16 (prompt caching) — deferred, staying
  on claude -p with Max subscription
- Adding features not in the 17 gaps
- Cross-subsystem synthesis session (tiered sequencing resolves
  dependencies naturally)
