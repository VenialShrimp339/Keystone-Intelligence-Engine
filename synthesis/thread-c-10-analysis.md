# Report 10: C1 — Specification-Driven Development

**Source report:** `research-reports/Deep_Research_Report_From_Prompt_10.md`
**Prompt:** Research specification-driven development practices, AGENTS.md/CLAUDE.md standards, Claude Code skills architecture, and the emerging toolkit for treating specification files as first-class engineering artifacts.

---

## Top Findings

**Finding 1: The "Spec-as-Source" taxonomy independently validates Keystone's core architectural bet.**
- Pipeline layer: L0 (Specification Engine) and META
- Academic paper arXiv:2602.00180 formalizes three levels of specification rigor — Spec-First (write and discard), Spec-Anchored (maintained alongside code), and Spec-as-Source (the specification IS the primary artifact). Keystone operates at Spec-as-Source level. This is the first academic taxonomy that directly and explicitly validates the plan's architectural conviction that ".md files defining methodology and quality criteria are the only irreplaceable component."
- Evidence quality: Verified (peer-reviewed paper, January 2026)
- Build implication: Use this taxonomy in architecture documentation. Cite it as the academic foundation for the plan's Specification Engine design. It gives the design rigor beyond practitioner intuition.

**Finding 2: Claude Code's .claude/ directory is a production-ready specification runtime — and the skills progressive disclosure system is exactly what the plan needs.**
- Pipeline layer: L0, L1, L1.5, L4
- The .claude/ directory with agents/, skills/, rules/, and hooks/ provides the exact deployment format for the Keystone Intelligence Engine. Critically, subagent definitions use YAML frontmatter where the `description` field drives automatic delegation — this is the mechanism for differentiating research agents, deliberation agents, and evaluation agents at the architectural level. The skills system implements three-level progressive disclosure: name/description at startup (~100 tokens per skill), full SKILL.md on match (<5,000 tokens), and reference files on demand. This is the CAPSTONE-PLAN-v2.md's Section 4.4 "three-layer loading architecture" implemented natively in Claude Code.
- Evidence quality: Verified (official Anthropic documentation)
- Build implication: The .claude/ directory structure is not a design option — it IS Keystone's deployment format. Every component in the plan's agent taxonomy maps directly: `.claude/agents/research-*.md` for L1, `.claude/agents/deliberation-*.md` for L1.5, `.claude/agents/evaluation-*.md` for L4.

**Finding 3: Google DeepMind's 17.2x error amplification finding validates L1.5 (Deliberation) as non-optional.**
- Pipeline layer: L1.5 (Deliberation)
- Paper arXiv:2512.08296 (18 researchers, Google Research + DeepMind + MIT): independent multi-agent systems amplify errors 17.2x vs. single-agent baselines. Centralized coordination contained amplification to 4.4x. Critical nuance: once single-agent baselines exceed ~45% accuracy, coordination yields diminishing returns — and sequential reasoning saw -39% to -70% degradation across all multi-agent variants.
- Evidence quality: Verified (peer-reviewed, Google/DeepMind/MIT)
- Build implication: The plan's deliberation phase is essential, not optional. But the -39% to -70% degradation in sequential reasoning is a warning against naive debate — this directly prefigures the Report 11 martingale finding (see Cross-report flags). Centralized orchestration with structured protocols, not open-ended sequential debate, is the correct design.

**Finding 4: SkillsBench empirical data establishes that focused skills outperform comprehensive documentation by 4x.**
- Pipeline layer: L0, L4
- arXiv:2602.12670 (February 2026): 84 tasks, 11 domains, 7 agent-model configurations, 7,308 trajectories. Curated skills improve pass rate by +16.2 percentage points. Self-generated skills: -1.3pp (negligible or harmful). 2-3 focused skills (+20.0pp) outperform comprehensive documentation (+5.7pp) by ~4x. Smaller models with skills can match larger models without.
- Evidence quality: Verified (first benchmark systematically evaluating agent skills)
- Build implication: Every SKILL.md in Keystone's skills/ directory must be tightly scoped. The plan's current skill design — SKILL.md + gotchas.md + constraints.md + examples/ — is the right structure. But resist the urge to make skills comprehensive; focused is better. 16 of 84 tasks showed negative deltas when skills conflicted with model priors — a warning to test skills, not just write them.

**Finding 5: KV-cache economics create a direct cost linkage between specification stability and operating cost.**
- Pipeline layer: L0, META
- Manus AI finding (not Meta, as attributed elsewhere): cached tokens cost $0.30/MTok vs $3.00/MTok uncached — a 10x cost difference. Any instability in specification files at the front of context invalidates the entire downstream KV-cache. Even a timestamp at the beginning of a system prompt destroys cache hits.
- Evidence quality: Verified (Manus AI engineering blog, production system)
- Build implication: Keystone's specification files must be designed for cache stability. RESEARCH.md should be stable within an engagement (no timestamps, no dynamic content at the front). This is an operational cost constraint, not just a quality consideration. Design RESEARCH.md structure so dynamic content (task status, progress tracking) is appended, not prepended.

---

## Tool/Framework Verdicts

**CLAUDE.md hierarchy (.claude/ directory)**
- Version/maturity: Production, official Anthropic
- What it does: Primary specification format for Claude Code; provides agents/, skills/, rules/, hooks/ subdirectories; YAML frontmatter for subagent delegation
- Verdict: BUILD — this IS Keystone's deployment format; every agent role in the plan must be defined here

**SKILL.md progressive disclosure**
- Version/maturity: Production, official Anthropic
- What it does: Three-level lazy loading of skill content — startup loads only metadata, execution loads full SKILL.md, deep execution loads reference files
- Verdict: BUILD — implement all Keystone skills, methodology docs, and evaluation rubrics using this pattern; it's the native implementation of the plan's three-layer loading architecture

**AGENTS.md standard (AAIF/Linux Foundation)**
- Version/maturity: De facto standard, donated to Linux Foundation December 2025; 20+ tools; 60K+ repos
- What it does: Cross-tool agent specification format; Claude Code does NOT auto-load it (uses CLAUDE.md instead)
- Verdict: LEARN — adopt the format conventions for cross-tool compatibility, but CLAUDE.md is primary; don't build around AGENTS.md as the primary spec surface

**Skills API (skill_id, Messages API beta)**
- Version/maturity: Beta header skills-2025-10-02, production Anthropic API
- What it does: Exposes skills programmatically via /v1/skills endpoints; custom skills callable by skill_id; pre-built PPTX/DOCX/XLSX/PDF skills
- Verdict: BUILD — use for exposing Keystone methodologies as API-callable skills in L3 generation; the pre-built PPTX/DOCX skills directly serve Layer 3a/3b

**Context editing (84% token reduction)**
- Version/maturity: Production Anthropic platform feature
- What it does: Clears stale tool calls from context window during long sessions; 84% token reduction in 100-turn web search evaluation
- Verdict: BUILD — enable for all long-running research sessions; critical for L1 research agents processing tens of thousands of tokens

**GitHub Spec Kit (4-phase workflow, constitution.md)**
- Version/maturity: ~81.4K GitHub stars, under official github organization, 658 commits
- What it does: Specify → Plan → Tasks → Implement workflow with Markdown artifacts; constitution.md for non-negotiable project principles; /analyze command for cross-artifact consistency
- Verdict: LEARN — adapt the 4-phase pattern for consulting research lifecycle (Brief → Methodology → Execution → Delivery); implement constitution.md as Keystone's quality constitution

**Kiro EARS notation**
- Version/maturity: Public preview, VS Code-based, up to $39/month at GA
- What it does: Requirements expressed as "WHEN [trigger], THE SYSTEM SHALL [response]" — human-readable and machine-parseable
- Verdict: LEARN — adapt EARS syntax for writing L0 acceptance criteria in research-tasks.json; the WHEN/SHALL pattern makes criteria testable by the Evaluator

**BMAD-METHOD (Zod validation, CI)**
- Version/maturity: Community project, Credible
- What it does: Closest existing system to spec-as-engineering-artifact; Zod-based validation with 19 rules, CI integration, compilation pipeline
- Verdict: LEARN — adapt the validation pipeline pattern for CI checks on Keystone's .claude/ spec files; closest existing analog to the META-layer spec quality pipeline the report recommends building

**AgentShield (ECC)**
- Version/maturity: Open-source, GitHub Action available, 102 static security rules, 1,282 tests, 98% coverage
- What it does: Security auditor for CLAUDE.md, settings.json, MCP servers, hooks, agent definitions; detects prompt injection, permission misconfiguration, configuration drift
- Verdict: BUILD — integrate into CI/CD for spec security scanning; this directly addresses the MCP security risk flagged in Report 13 (C4)

**ECC Instinct System (Continuous Learning v2)**
- Version/maturity: ~100K GitHub stars, Credible
- What it does: Watches coding sessions, converts patterns into atomic "instincts" with confidence scores (0.3-0.9), clusters into skills via /evolve
- Verdict: LEARN — adapt confidence-scored pattern learning for META-layer spec refinement; this is the bottom-up learning loop to complement the Rejection Library's top-down constraint encoding

**OpenCode**
- Version/maturity: ~129K GitHub stars, Go-based, 75+ LLM providers
- What it does: Provider-neutral alternative to Claude Code; .opencode/ directory structure
- Verdict: SKIP — Keystone is Claude-native; multi-model adds complexity without commensurate benefit; the .claude/ directory is the deployment surface

**Oracle Agent Spec / Open Agent Spec**
- Version/maturity: Python SDK, YAML-based
- What it does: YAML-based declarative agent language targeting AutoGen/LangGraph ecosystem
- Verdict: SKIP — YAML-based, targets different ecosystem; not relevant to Claude Code/.claude/ deployment

**markdownlint-cli2**
- Version/maturity: Mature, GitHub Actions integration, 53 rules
- What it does: Structural validation of Markdown files in CI
- Verdict: BUILD — run on every PR modifying .claude/ spec files; cheapest structural quality gate available

**antigravity-awesome-skills**
- Version/maturity: v9.0.0, 1,326+ indexed skills, ~27-28K GitHub stars
- What it does: Curated SKILL.md collection installable via npx; bundles for various development domains
- Verdict: LEARN — study the taxonomy and bundling approach; no directly usable consulting research skills, but the bundle organization pattern is worth stealing

---

## Contradictions with CAPSTONE-PLAN-v2.md

**Contradiction 1: The plan references "skills" but doesn't map explicitly to .claude/skills/ architecture**
- Plan says: Section 4.4 describes "three-layer loading architecture" with skill directories containing SKILL.md, gotchas.md, constraints.md, examples/
- Evidence shows: Claude Code's native .claude/skills/ structure is identical to this design, including progressive disclosure at exactly the three levels described
- Resolution: Follow the evidence. The plan's skill architecture should be formalized as native .claude/skills/ directories. This is not a contradiction so much as the plan independently converging on a design that already exists natively — and which should be explicitly named as the deployment format.

**Contradiction 2: The plan describes RESEARCH.md as a novel concept; evidence shows it maps to existing spec-as-source patterns**
- Plan says: "RESEARCH.md — a new concept that serves as the file every agent reads" (Section 3.2)
- Evidence shows: RESEARCH.md is Keystone's implementation of the "Spec-as-Source" level in the arXiv:2602.00180 taxonomy; it's not a new concept but the highest-maturity level of an established pattern
- Resolution: The design is correct. Call it Spec-as-Source to signal academic credibility and alignment with the emerging consensus; keep calling it RESEARCH.md as the implementation name.

**Contradiction 3: The plan mentions AGENTS.md without clearly specifying CLAUDE.md primacy**
- Plan says: Brief references to AGENTS.md in agent definition discussions (Appendix, Section 7.7)
- Evidence shows: Claude Code does NOT auto-load AGENTS.md; it uses CLAUDE.md hierarchy. AGENTS.md is for cross-tool compatibility only.
- Resolution: Follow the evidence. All primary spec work goes into CLAUDE.md and .claude/ hierarchy. AGENTS.md can be maintained as a cross-tool compatibility artifact, but don't design around it.

**Contradiction 4: The 84% token reduction claim**
- Plan doesn't reference this specific claim
- Evidence shows: The 84% figure is from context editing (a platform feature), not from SKILL.md progressive disclosure specifically. Separate from the 69% line reduction and 54% initial token reduction from community projects
- Resolution: Use the 84% figure only when referring specifically to context editing as a feature; don't conflate with skill loading efficiency

---

## Cross-Report Flags

**Flag 1 (reinforces C2/Report 11):** The DeepMind 17.2x error amplification finding for unstructured multi-agent systems directly supports Report 11's martingale finding. Both point to the same conclusion: structured deliberation with centralized coordination is required, not optional. The two findings from different angles (error amplification vs. belief dynamics) converge on the same architectural prescription.

**Flag 2 (reinforces C4/Report 13):** The KV-cache economics finding (specification stability = cost efficiency) connects to Report 13's caching architecture. The specification layer and the retrieval caching layer must be designed together — instability in RESEARCH.md invalidates retrieval caches downstream.

**Flag 3 (reinforces Thread B on evaluation):** The SkillsBench finding that 16 of 84 tasks showed negative deltas when skills conflicted with model priors suggests that the L4 Evaluator should include a skill-conflict detection dimension. A skill that actively degrades performance needs to be flagged and pruned — the META-layer self-improvement loop must be bidirectional (add constraints AND prune counterproductive ones).

**Flag 4 (potentially conflicts with Thread A on orchestration):** The report recommends CLAUDE.md/Claude Code as the native deployment surface. Thread A's orchestration research (Report 4) may recommend LangGraph or CrewAI as orchestration frameworks. These are not mutually exclusive — Claude Code can orchestrate LangGraph subagents — but the deployment surface decision (Claude Code vs. framework-first) should be addressed explicitly in the synthesis.

**Flag 5 (validates META-layer design):** The ECC Instinct System's confidence-scored pattern learning (0.3-0.9 confidence, /evolve promotion) is a direct analog to the Rejection Library's instinct-to-skill evolution pipeline described in CAPSTONE-PLAN-v2.md Section 7.7. The plan's META-layer design is validated as an established pattern, not a novel invention.
