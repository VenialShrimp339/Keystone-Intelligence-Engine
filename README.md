# Keystone Intelligence Engine — Claude Code Project

**30 files | 1.1MB | Ready for Claude Code**

## Setup

1. Point Claude Code at this directory
2. `CLAUDE.md` loads automatically — lean project context + working rules
3. Skills and agents in `.claude/` load on demand

### Getting started

```
# Analyze Thread A reports (landscape):
"Read reports 1-5 in research-reports/. For each, cross-reference with RESEARCH-PROMPTS-FINAL.md and produce a structured analysis following the research-synthesis skill methodology."

# Or invoke the research-analyst agent directly:
"@research-analyst Analyze Report 1 (A1: Multi-Agent Research Systems)"
```

## File Structure

### Root (read first)
| File | What |
|------|------|
| `CLAUDE.md` | Project context, working rules, evidence standards. Loaded every session. |
| `CAPSTONE-PLAN-v2.md` (1051 lines) | **Source of truth.** Full 6-layer pipeline architecture. |
| `RESEARCH-PROMPTS-FINAL.md` | 16 finalized research prompts. Maps prompt numbers → topics. |
| `CAPSTONE-PLAN.md` | V1 for comparison. |

### .claude/ (Claude Code configuration)
```
.claude/
├── settings.json                          # Project-level permissions
├── skills/
│   ├── research-synthesis/SKILL.md        # Analysis methodology, phases, evidence tiers
│   └── architecture/SKILL.md             # Pipeline layers, handoff contracts, design principles
└── agents/
    └── research-analyst.md                # Report analysis agent (Opus, structured output)
```

### research-reports/ (16 files, ~508KB)
| Reports | Thread | Topic |
|---------|--------|-------|
| 1-5 | A1-A5 | Open source landscape, evaluation frameworks, self-improvement, orchestration, deep research tooling |
| 6-9 | B1-B4 | What partners value, decision-useful research, quality of thought, AI failure modes |
| 10-13 | C1-C4 | Specification-driven dev, deliberation, report generation, data retrieval |
| 14-16 | D1-D3 | Best small-team AI systems, academic papers, 10x ideas |

### nate-synthesis/ (3 files, ~164KB)
| File | What |
|------|------|
| `SYNTHESIS.md` | Master synthesis of 91 articles. Core thesis + validated frameworks. |
| `CAPSTONE-IMPLICATIONS.md` | How the 91 articles reshape the capstone architecture. |
| `FRAMEWORKS.md` | 76 named frameworks + 112-term concept dictionary. |

### source-analysis/ (4 files, ~164KB)
| File | What |
|------|------|
| `BOOKMARK-ARCHITECTURE-INSIGHTS.md` | Distilled insights from 189 bookmarks, organized by pipeline layer. |
| `NEW-BOOKMARKS-SYNTHESIS-APR4.md` | 20 April 4 bookmarks with architecture-changing findings. |
| `source-by-source-analysis.md` | Deep analysis of 39 X bookmarks → architecture decisions. |
| `external-sources-analysis.md` | 12 key external source analyses. |

### quality-audits/ (3 files, ~116KB)
Audit of all 16 research prompts, system prompt analysis, cross-cutting analysis.

## What's NOT Included (and Why)

- 91 individual Nate article analyses — distilled into the 3 synthesis docs
- 6 raw X bookmark analysis files (230KB) — distilled into BOOKMARK-ARCHITECTURE-INSIGHTS.md
- OpenClaw/Merlin workspace files — not capstone-relevant
