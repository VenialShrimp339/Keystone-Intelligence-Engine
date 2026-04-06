# Cleanup Session: Fix, Record, Prepare for Component #7

Your revised assessment was thorough and the findings are validated. The tool name mismatch is real (I independently verified it against the source files). The per-component acceptance criteria audit, L2/L3 resolution, and prioritization are all on target. Your pushback on the Cowork session's overcorrection was also correct and showed good judgment.

This prompt covers everything that needs to happen before we start building Component #7. There are two categories: fixes (things that are wrong and need changing) and recording (capturing your audit findings in the project's handoff system so future sessions can see them).

---

## Part 1: Fix the Tool Name Mismatch

This is the highest-priority item. Here's what I want you to think through before just renaming strings.

### The Root Cause Problem

The tool name mismatch happened because two sessions independently chose string identifiers for the same tools. This will happen again anytime a new component references tools by string, unless there's a single source of truth. Renaming strings in template_registry.py to match servers.py fixes the symptom but not the cause.

### What To Build

Create a shared constant module that both the Gateway and Spec Engine import from:

```
src/keystone/tools.py   (or src/keystone/constants/tools.py)
```

This module should define:
- A `ToolName` StrEnum (or a module-level constant dict) with every registered tool name
- Optionally, groupings (e.g., SEARCH_TOOLS, FINANCIAL_TOOLS, ACADEMIC_TOOLS) that the Spec Engine's templates can reference by group

Then update:
1. `src/keystone/gateway/servers.py` to import tool names from the shared module
2. `src/keystone/specification/template_registry.py` to import tool names from the shared module
3. `src/keystone/specification/task_generator.py` to use the shared constants in `_resolve_tools()` fallback

This way, if a future session adds a new MCP server, they add the name in one place and both Gateway and Spec Engine see it.

### The Four Missing Tools

The Spec Engine references 4 tool names that have no MCP server config: `news_search`, `industry_reports`, `patent_search`, `government_search`. For each, decide:

- **Can it map to an existing server?** `news_search` could plausibly route to `brave_search` (Brave has news results). But that's a semantic stretch for `industry_reports` or `patent_search`.
- **Should it be removed from templates until a real server exists?** If there's no server backing it, an agent assigned this tool will fail when it tries to call it. Better to remove it from the template and add it back when a server exists.
- **Should a new server config be added as a stub?** This would register the name but mark it as unavailable. The gateway already has a health status concept.

My recommendation: remove the 4 missing tool names from seed templates for now. Replace them with tools that DO have servers. The seed templates are just defaults; the Spec Engine can generate custom tool assignments. Having working defaults is better than having aspirational defaults that crash at runtime. Add a comment noting what tools should be added when servers become available.

### The `finnhub_market` Gap

The Gateway registers `finnhub_market` but NO Spec Engine template uses it. The quantitative_analyst template uses `financial_data_api` instead. When you do the rename, map `financial_data_api` -> `finnhub_market` in the quantitative and historical templates.

### Test Updates

After renaming, search all test files for the old tool name strings and update them. Run the full test suite. The 486 passing tests should still pass with zero new failures.

---

## Part 2: Fix datetime.utcnow()

You identified 9 locations (4 source, 5 tests). Fix all of them:
- Replace `datetime.utcnow()` with `datetime.now(UTC)`
- Add `from datetime import UTC` where needed
- Run the test suite and confirm the 207 warnings drop to near-zero

Small thing, but doing it now means the test output is clean for Component #7 development. When 207 warnings are scrolling by, you stop reading warnings entirely, which is how real bugs hide.

---

## Part 3: Trim pyproject.toml

Remove dependencies that aren't imported by any built component. Specifically check: `temporalio`, `docling`, `cohere`, `redis`, `pgvector`, `asyncpg`. If none of the 56 production Python files import them, remove them from pyproject.toml. They can be added back when the components that need them are built.

This prevents install failures on clean environments and keeps the dependency footprint honest.

---

## Part 4: Regenerate docs/ARCHITECTURE.md

The current version describes files that don't exist and omits files that do. Every new Claude Code session reads this file on startup (it's referenced in CLAUDE.md's orientation section).

Generate an accurate ARCHITECTURE.md from the actual codebase. Include:
- The real directory tree under `src/keystone/` (what actually exists, not what was planned)
- Module responsibilities for every module (one line each)
- The interface table (which Protocol in contracts.py each component satisfies)
- Dependency rules (what imports what, what shouldn't import what)
- A note about the shared tool name constants you just created

---

## Part 5: Record the Audit

This is important. Your audit findings currently exist only in the conversation. If this session compacts or Jack starts a new session, everything evaporates. Write it down.

### 5a: Create `audit/OVERNIGHT-AUDIT-RESULTS.md`

Take your per-component acceptance criteria audit (the MET/UNTESTED/UNMET tables from your revised output) and put them in this file. Also include:
- The tool name mismatch finding and resolution
- The L2/L3 resolution (Phase 2 deferral, not a gap)
- The list of UNTESTED criteria across all components (so future sessions know what still needs test coverage)
- The datetime.utcnow() finding
- The ARCHITECTURE.md staleness finding

### 5b: Update `CURRENT-STATE.md`

Reflect:
- The tool name mismatch has been fixed (after Part 1)
- L2/L3 are confirmed Phase 2 deferrals
- List the UNTESTED acceptance criteria as known test coverage gaps
- Update the "What's next" section: next step is Component #7

### 5c: Update `SESSION-LOG.md`

Add an entry for this audit session covering both your initial orientation pass and this cleanup pass. Follow the existing entry format (date, agent, task, files created/modified, key decisions, what comes next).

---

## Part 6: Update CLAUDE.md

Add the shared tool name constant module to the project structure section so future sessions know it exists. Also update the reference to docs/ARCHITECTURE.md if needed (it should still point to the same file, just noting it's been regenerated).

---

## Execution Order

1. Part 1 (tool name fix) -- highest priority, prevents runtime failures
2. Part 2 (datetime fix) -- quick, cleans test output
3. Part 3 (trim deps) -- quick, prevents install failures
4. Part 4 (regen ARCHITECTURE.md) -- medium effort, high compounding value
5. Part 5 (record audit) -- write the findings down
6. Part 6 (update CLAUDE.md) -- small update

Run the full test suite after Parts 1-3 to confirm everything still passes. Then do Parts 4-6.

After all of this is done, report back with:
1. The final test count and pass/fail
2. Any issues encountered during the fixes
3. Confirmation that all project handoff files are updated

Then we'll scope Component #7.
