# Lessons

Append-only. Each entry: what went wrong, root cause, prevention rule.

---

## L#1 — Governance spiral

**Caught:** Sessions 7-30+, multiple Codex agents (April 2026)
**Root cause:** CLAUDE.md told every session to "read the authority stack first," which pointed to control-plane YAML, which pointed to lane packets, which pointed to review artifacts. Each session internalized the bureaucracy and produced more of it.
**Symptom:** 45K lines of audit docs (3x the source code), 22 worktrees, zero code commits in a week+
**Prevention:** CLAUDE.md points to code and commands, not governance docs. No control planes, lane packets, authority stacks, promotion decisions, or review sidecars. Build features, not documents. One session, one feature.
