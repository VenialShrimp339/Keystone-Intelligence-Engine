# Codex Session Wrapper

This file is the Codex-facing wrapper around the shared repo standards.
It does not replace `AUTHORITY-INDEX.md` or `SESSION-STANDARD.md`.

Read these first:

1. `AUTHORITY-INDEX.md`
2. `SESSION-STANDARD.md`
3. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
4. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`

For founder doctrine, use `FOUNDER-INTENT-DOCTRINE.md`.
For historical rationale, use `SESSION-LOG.md` only after the authority stack.

## graphify

- If `graphify-out/GRAPH_REPORT.md` exists, read it before answering architecture or codebase questions.
- If `graphify-out/wiki/index.md` exists, prefer it over raw graph files.
- If graphify artifacts are absent, continue and note that they were not available.
- After modifying code files, run `python3 -c "from graphify.watch import _rebuild_code; from pathlib import Path; _rebuild_code(Path('.'))"` to rebuild the graph.
