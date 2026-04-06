"""Knowledge Accumulation module (Component #3b).

Implements the Karpathy wiki pattern: raw subagent artifacts are compiled
into structured markdown wikis with auto-maintained indexes and
content-hash provenance tracking.

Three-layer structure per engagement:
  raw/       -- Full subagent artifacts (verbatim, immutable after write)
  compiled/  -- Orchestrator-synthesized findings
  INDEX.md   -- Auto-maintained navigation index
"""
