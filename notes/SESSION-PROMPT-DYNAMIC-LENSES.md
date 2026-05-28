# Session: Dynamic Lens Selection (Decomposer Generalization)

## Orchestrator Disclosure

This prompt was written by an orchestrator session (Opus, 1M context) that read
the full CAPSTONE-PLAN-v2.md, JACK-ARCHITECTURAL-DIRECTIVES.md, all four
analysis files in notes/analysis/, and the complete source of: decomposer.py,
all 4 lens/synthesis prompt files, engagement_classifier.py, validator.py,
spec_engine.py, and the _prompts.py loader. The orchestrator also read the
full lens prompt content and synthesis prompt content line by line.

**The orchestrator did NOT read every file you will need to touch.** Read
files fully before modifying them.

**If you discover information that changes the plan** — a dependency the
orchestrator missed, a file structured differently than assumed, or a better
approach — **you are authorized to diverge.** However, you MUST:

1. Document every divergence under `## Plan Divergences`
2. For each: what the plan said, what you did instead, and why
3. Related but out-of-scope work goes under `## Discovered Work`

---

## Context

### The problem

`decomposer.py` line 56 hardcodes: `_LENSES = ["financial", "operational", "market"]`

Three fixed lens prompt files (`decompose_financial_lens.md`,
`decompose_operational_lens.md`, `decompose_market_lens.md`) assign
domain-specific personas (financial analyst, operations strategy consultant,
market strategy consultant). The synthesis prompt at `decompose_synthesis.md`
hardcodes `{{financial_tree}}`, `{{operational_tree}}`, `{{market_tree}}` as
named kwargs.

For a question about software architecture, molecular biology, or internal
process design, all three lenses produce nonsensical output. The first pipeline
run (April 22, 2026) decomposed "how to architect an agentic research system"
through a financial analyst lens, producing branches about revenue models and
unit economics.

This is the #1 CRITICAL finding from `notes/analysis/one-size-fits-all-audit.md`
and `notes/analysis/l0-specification-quality.md`.

### What's already been done (Phase B session)

A prior session added:
- `domain: str` field to `ClassificationResult` in `engagement_classifier.py`
- `EngagementType.DESIGN` and `EngagementType.SYNTHESIS` to the enum
- Domain is threaded into `ResearchSpec`

Your work builds on this: the domain classification is now available in the
pipeline and should be used by the lens selector to pick appropriate lenses.

### Architectural context

**CAPSTONE-PLAN-v2.md Section 3.3, Step 3** says: "Three to four Sonnet agents
with distinct consulting lenses (financial, operational, market/competitive;
optionally regulatory/risk for complex engagements) independently construct
shallow issue trees."

**Directive 1** says: "Predefined types should be templates or defaults, not
constraints."

**Directive 12** says: "Teach principles of decomposition, not specific
frameworks."

The fix: make lens selection dynamic based on the question domain, while keeping
the existing 3 consulting lenses as the default for business-domain questions.

**Branch:** `codex/owner-triage-normalization`
**Tests:** 1506+ passing (may be higher after Phase A/B sessions)

---

## Your Tasks

### Task 1: Create a `LensSelector` component

**New file:** `src/keystone/specification/lens_selector.py`

Create a `LensSelector` that takes the question, engagement_type, and domain,
and returns 2-4 `LensSpec` objects. Two implementation options — pick whichever
is simpler and more testable:

**Option A (recommended for Phase 1): Rule-based selection with LLM override**
- Define a `LENS_MENU` of 8-12 available lenses, each with:
  `name`, `description`, `id_prefix`, `focus_areas: list[str]`
- Define a `_DOMAIN_LENS_MAP` that maps domain patterns to default lens selections:
  - business/financial/market domains → `[financial, operational, market]` (the existing 3)
  - technical/architecture/technology domains → `[technical_architecture, existing_systems, evaluation_methodology]`
  - scientific/literature/synthesis domains → `[literature_landscape, methodology_assessment, existing_systems]`
  - operations/organizational domains → `[operational, organizational, market]`
  - Unknown/other → `[generalist_analytical, operational, market]`
- Pattern matching should be substring-based on the domain string (e.g., if "technical" in domain)
- Return 2-4 `LensSpec` objects

**Option B (Phase 2): LLM-driven selection**
- Make one LLM call with the question, domain, and lens menu
- LLM selects 2-4 lenses from the menu
- More flexible but adds an LLM call and potential failure mode

Go with Option A for now. The interface should support swapping to Option B
later without changing the Decomposer.

**`LensSpec` model:**
```python
class LensSpec(BaseModel):
    name: str                    # e.g., "technical_architecture"
    description: str             # e.g., "System design, component interfaces, scalability"
    id_prefix: str               # e.g., "tech" — used for node IDs in the tree
    focus_areas: list[str]       # e.g., ["Component architecture", "Interface design", ...]
    persona: str                 # e.g., "You are a systems architect..."
```

**The lens menu should include AT MINIMUM:**

| Name | Description | ID Prefix | Domain Match |
|------|-------------|-----------|--------------|
| `financial` | Revenue, costs, margins, valuation, unit economics | `fin` | business, financial, m_and_a |
| `operational` | Capabilities, processes, supply chain, execution risk | `ops` | operations, organizational, business |
| `market_competitive` | Market structure, competitive dynamics, positioning | `mkt` | business, market, competitive |
| `technical_architecture` | System design, component selection, trade-offs, scalability | `tech` | technical, technology, architecture |
| `existing_systems` | Prior art, existing solutions, what's been tried, reuse vs build | `sys` | technical, scientific, design |
| `evaluation_methodology` | Quality frameworks, assessment criteria, measurement approaches | `eval` | evaluation, scientific, quality |
| `literature_landscape` | Academic research, published findings, state of knowledge | `lit` | scientific, literature, synthesis |
| `regulatory_policy` | Regulatory requirements, compliance, policy direction | `reg` | regulatory, policy, legal |
| `organizational` | Team structure, talent, culture, change management | `org` | organizational, operations |

### Task 2: Create a generic lens prompt template

**New file:** `src/keystone/specification/prompts/decompose_generic_lens.md`

Create a parameterized version of the existing lens prompts. The structure is
identical to the existing lens prompts but with dynamic content:

```markdown
---
model: claude-opus-4-6
tuned: "2026-04"
---
You are {{persona}} constructing an issue tree for a research engagement.
Your perspective is the {{lens_name_upper}} LENS: {{lens_description}}.

## Input

**Research Question:** {{question}}
**Engagement Type:** {{engagement_type}}
**Day-1 Hypothesis:** {{day_1_hypothesis}}
**Client Context:** {{client_context}}

## Your Task

Construct a MECE issue tree from the {{lens_name}} perspective. [rest of
the MECE principles section — copy from existing lens prompts, it's
domain-neutral]

## {{lens_name_upper}} Lens Focus Areas

Consider these (use what's relevant, skip what isn't):
{{focus_areas_formatted}}

## Output Format

[Same analytical_contract as existing lens prompts, but with {{id_prefix}}
instead of hardcoded "fin_"/"ops_"/"mkt_"]
```

**Important:** The MECE Principles section and Output Format section from the
existing lens prompts are already domain-neutral. Copy them directly. Only the
persona, description, and focus areas need to be parameterized.

**Keep the existing 3 lens prompt files** (`decompose_financial_lens.md`,
`decompose_operational_lens.md`, `decompose_market_lens.md`) — they're the
gold-standard prompts for business domains and serve as reference. The generic
template should produce equivalent quality for any domain.

### Task 3: Refactor the synthesis prompt

**File:** `src/keystone/specification/prompts/decompose_synthesis.md`

Currently hardcodes:
```
### Financial Lens Tree
{{financial_tree}}

### Operational Lens Tree
{{operational_tree}}

### Market/Competitive Lens Tree
{{market_tree}}
```

And the Synthesis Strategy says: "Start with the tree that best matches the
engagement type (financial for sizing, market for evaluative, operational for
diagnostic)"

**Replace with:**
```
{{lens_trees_section}}
```

Where `lens_trees_section` is built dynamically by the Decomposer from the
actual lenses used. Format:

```
### Lens 1: Technical Architecture
{json tree}

### Lens 2: Existing Systems Landscape
{json tree}

### Lens 3: Evaluation Methodology
{json tree}
```

**Update the Synthesis Strategy** to:
```
- Start with the lens tree that most directly addresses the core question
- Use the Day-1 Hypothesis to identify which branches are most central
- Integrate branches from other lenses by merging or adding top-level branches
- Prune branches tangential to the Day-1 Hypothesis
```

Remove the hardcoded engagement-type-to-lens mapping ("financial for sizing,
market for evaluative, operational for diagnostic").

**Update the persona line** from "synthesizing three independently constructed
issue trees" to "synthesizing independently constructed issue trees" (the
count is now dynamic).

**Update lens_annotations** references to not assume financial/operational/market
as the only possible annotations.

### Task 4: Update the Decomposer class

**File:** `src/keystone/specification/decomposer.py`

The Decomposer needs to:
1. Accept a `LensSelector` (or use a default one)
2. Accept `domain` as a parameter to `decompose()`
3. Use the selector to get lens specs instead of `_LENSES`
4. Use the generic prompt template instead of named prompt files
5. Build the synthesis prompt with dynamic lens tree sections

**Changes to `__init__`:**
```python
def __init__(
    self,
    llm: LLMCallable | None = None,
    *,
    lens_llm: LLMCallable | None = None,
    synth_llm: LLMCallable | None = None,
    lens_selector: LensSelector | None = None,  # NEW
) -> None:
```

**Changes to `decompose()`:**
```python
async def decompose(
    self,
    question: str,
    engagement_type: EngagementType,
    day_1_hypothesis: str,
    client_context: str | None = None,
    domain: str | None = None,  # NEW
) -> IssueTree:
```

- Call `self._lens_selector.select(question, engagement_type, domain)` to get lens specs
- For each lens spec, call `_run_lens` with the generic prompt template
- Build the synthesis prompt with dynamically named trees
- Update metadata.lenses_used with actual lens names

**Changes to `_run_lens()`:**
- Instead of `load_prompt(f"decompose_{lens}_lens", ...)`, load the generic
  template with the lens spec's persona, description, focus areas, and id_prefix
- The prompt loading should work with `load_prompt("decompose_generic_lens", lens_name=..., persona=..., ...)`

**Changes to `_synthesize()`:**
- Build `lens_trees_section` from the actual lenses and their trees
- Pass it as a single kwarg instead of 3 named kwargs

**Important:** The `_LENSES` module-level constant should be removed. The
`_run_lens` method signature changes from `lens: str` to `lens: LensSpec`.

### Task 5: Thread domain through spec_engine.py

**File:** `src/keystone/specification/spec_engine.py`

The `generate_spec()` method calls `self._decomposer.decompose(...)`. It needs
to pass the domain from the classification result:

```python
tree, mece_passed = await self._decompose_with_validation(
    question,
    classification.engagement_type,
    intent.day_1_hypothesis,
    client_context,
    domain=classification.domain,  # NEW — pass through to decomposer
)
```

Update `_decompose_with_validation` to accept and pass `domain`.

### Task 6: Tests

Add tests in `tests/unit/specification/`:

1. **LensSelector tests:**
   - Business domain returns financial/operational/market lenses
   - Technical domain returns technical_architecture/existing_systems/evaluation_methodology
   - Scientific domain returns literature-appropriate lenses
   - Unknown domain returns a reasonable fallback
   - Returns 2-4 lenses (not more, not fewer)

2. **Decomposer tests:**
   - Decomposer with default LensSelector produces valid IssueTree
   - Decomposer with custom LensSelector uses the provided lenses
   - metadata.lenses_used reflects actual lenses selected
   - The generic prompt template produces valid JSON structure
   - Backward compatibility: business domain still works correctly

3. **Integration tests (mock LLM):**
   - Full decompose → validate cycle with non-business domain
   - Synthesis prompt receives dynamically named trees

### Task 7: Validate

1. `ruff format` on all changed files
2. `pytest tests/unit/ -x --tb=short` — all tests must pass
3. `ruff check src/ tests/`
4. Commit with descriptive message

## What NOT to do

- Do NOT touch `orchestrator.py` — domain threading stops at spec_engine.py
- Do NOT modify evaluator prompts or deliberation prompts
- Do NOT modify task_generator.py
- Do NOT create governance docs (LESSONS.md L#1)
- Do NOT delete the existing 3 lens prompt files — they remain as reference
  and can be used directly for business-domain questions if preferred

## Expected Output

1. Summary of what was implemented
2. Test results (count passing)
3. Files changed with one-line descriptions
4. `## Plan Divergences`
5. `## Discovered Work`
