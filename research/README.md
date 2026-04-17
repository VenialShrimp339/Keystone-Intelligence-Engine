# Research

> Status: research index. Directory map only. Not current-state truth or architecture authority.

All research artifacts for the Keystone Intelligence Engine, consolidated from 6 previously scattered locations.

## Directory Structure

### reports/
Primary research inputs -- deep research reports that informed architectural decisions.

- **batch-1/** -- 16 original deep research reports (Prompts 1-16). Covers: multi-agent systems, evaluation frameworks, self-improvement, orchestration, tooling, consulting quality criteria, deliberation, generation, retrieval, specification-driven dev, academic literature, and "10x ideas."
- **batch-2/** -- 10 follow-on research reports addressing open architectural questions: iterative research patterns, dynamic agents, MECE issue trees, retrieval architecture, engagement taxonomy, context management, adaptive evaluation, MCP ecosystem, orchestration patterns, specification engine design.
- **openai-switchover/** -- 4 reports on GPT-5.4/Codex integration feasibility, behavioral differences, PydanticAI migration, and Responses API architecture.

### synthesis/
Analysis and synthesis of the research reports.

- **per-report/** -- 16 individual thread analyses (one per batch-1 report), structured as Thread A (1-5), B (6-9), C (10-13), D (14-16).
- **batch-2/** -- 11 files: per-report analyses of the 10 batch-2 reports + MASTER-SYNTHESIS.md resolving 16 architectural decisions.
- **UNIFIED-SYNTHESIS.md** -- Cross-thread synthesis identifying convergent findings across all four threads.
- **PLAN-CHANGELOG.md** -- All changes applied to CAPSTONE-PLAN-v2.md based on the 16-report synthesis.

### codebase-analysis/
Analysis of reference implementations informing Keystone's architecture.

- **nano-claude-code/** -- 10 numbered analyses (00-09) of the Python reimplementation of Claude Code (11.8K lines, 56 files). Extracts patterns for the DPVI pipeline.
- **leak-research/** -- 12 files: 10 deep research reports on the Claude Code v2.1.88 source leak + rename map + LEAK-SYNTHESIS.md cross-synthesis.

### external-sources/
Analysis of external source material beyond the commissioned research reports.

- **nate-jones/** -- 3 files synthesizing 91 Nate Jones Substack articles (Dec 2025-Mar 2026): master synthesis, cross-cutting frameworks, and capstone implications.
- **bookmarks/** -- 4 files analyzing 189+ X bookmarks and other external sources for architecture-relevant insights.

### quality-audits/
3 files auditing the quality of the research prompts themselves and the system prompt design.
