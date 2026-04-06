# Phase 1A Builder Sessions: Foundation Components
## 3 Parallel Claude Code Sessions + Track 3 (Casing Analysis)

*These 4 sessions can all run concurrently with Track 1 (Architecture Finalization).*
*Total parallel sessions: 5 (Track 1 + these 4)*

---

## Parallel Launch Overview

```
Track 1  (Architecture docs)    ──→ produces updated CAPSTONE-PLAN + IMPL-SPEC
Track 3  (Casing book analysis) ──→ produces MECE skill files for Component #5
Session 1A-1 (Component #1)     ──→ produces schemas, templates, sample specs
Session 1A-2 (Component #2)     ──→ produces updated citation models, hash utils
Session 1A-3 (HITL)             ──→ produces database, REST API, basic UI
```

All 5 are independent. No session reads or writes files owned by another:
- **Track 1** owns: `CAPSTONE-PLAN-v2.md`, `PHASE-1-IMPLEMENTATION-SPEC.md`, `CURRENT-STATE.md`, `CLAUDE.md`
- **Track 3** owns: `skills/mece-decomposition/` (new directory)
- **Session 1A-1** owns: `src/keystone/models/research.py`, `src/keystone/models/tasks.py`, `templates/`, `schemas/research_*.json`
- **Session 1A-2** owns: `src/keystone/models/citations.py`, `schemas/citation*.json`, `src/keystone/citation/`
- **Session 1A-3** owns: `src/keystone/hitl/` (new directory)

**Shared files (append-only):** `contracts.py` and `events.py`. If a session needs to add to these, it APPENDS new protocol/event classes at the end of the file. It does NOT modify existing classes.

**pyproject.toml:** Only Session 1A-3 (HITL) may modify pyproject.toml to add dependencies (FastAPI, Alembic, etc.). Other sessions should check if their needed dependencies are already listed before attempting to add them. If a dependency is missing and you are not Session 1A-3, document it in your SESSION-LOG entry and the next session will add it.

---

## Session 1A-1: Component #1 — RESEARCH.md Specification Format

### Prompt:

```
# Build Session: Component #1 — RESEARCH.md Specification Format

## Identity
You are building Component #1 of the Keystone Intelligence Engine: the schemas,
templates, and sample files that define what a RESEARCH.md engagement specification
looks like and how research tasks are structured. This is the foundation that every
other component builds on. If the schemas are wrong, everything downstream is wrong.

## PHASE 0: MANDATORY CONTEXT LOADING (read all before writing any code)

Read these files in order. Do not skip any.

1. `CLAUDE.md` — Project overview, architectural convictions
2. `JACK-ARCHITECTURAL-DIRECTIVES.md` — Jack's 14 design decisions. Pay special
   attention to:
   - Directive 1 (The Rigidity Problem): categories should be templates, not hard constraints
   - Directive 2 (MECE Issue Tree): task decomposition follows issue tree branches
   - Directive 5 (Build Philosophy): correct architecture at reduced feature depth
   - Directive 13 (Phase 1 Staging): what ships now vs. later
3. `CAPSTONE-PLAN-v2.md` Section 3 (Specification Engine) — How RESEARCH.md is used
4. `audit/PHASE-1-IMPLEMENTATION-SPEC.md` Component #1 — Your build spec
5. `audit/batch-2-analysis/MASTER-SYNTHESIS.md` Section 1 — The 10-step pipeline and
   iterative research loop that these schemas must support
6. `src/keystone/models/research.py` — **EXISTING MODEL. READ IN FULL.** You are
   updating this, not replacing it.
7. `src/keystone/models/tasks.py` — **EXISTING MODEL. READ IN FULL.** You are
   updating this, not replacing it.
8. `src/keystone/contracts.py` — Existing Protocol interfaces. Your schemas must be
   compatible with SpecificationEngineContract.
9. `src/keystone/events.py` — Existing event types.
10. `src/keystone/models/agents.py` — Agent definition models (for understanding
    how tasks connect to agents).

## YOUR DELIVERABLES

### 1. Update `src/keystone/models/tasks.py`

The existing ResearchTask and TaskDecomposition models need these Batch 2 updates:

**Add DAG dependency structure (MASTER-SYNTHESIS Change #9):**
ResearchTask needs a `dependencies` field:
```python
dependencies: list[str] = Field(
    default_factory=list,
    description="Task IDs this task depends on. Empty = no dependencies. "
    "Forms a DAG, not a flat list."
)
```

TaskDecomposition needs DAG validation:
```python
@model_validator(mode="after")
def validate_dag(self) -> TaskDecomposition:
    """Verify task dependencies form a valid DAG (no cycles)."""
    # Implement topological sort check
    ...
```

**Add per-branch end product specification (MASTER-SYNTHESIS Change #10):**
ResearchTask needs:
```python
end_product: str = Field(
    description="Specific output format for this branch "
    "(e.g., 'comparison table with 8+ competitors', "
    "'sensitivity analysis with ±20% assumption variation')"
)
```

**Add issue tree branch reference:**
ResearchTask needs:
```python
issue_tree_branch_id: str | None = Field(
    default=None,
    description="ID of the issue tree branch this task derives from. "
    "Links task back to MECE decomposition."
)
```

**Make TaskCategory extensible (Directive 1: templates, not enums):**
Keep the existing StrEnum as DEFAULT categories, but add a mechanism for custom
categories. The simplest approach: add a `custom_category` field that overrides
the enum when the engagement needs a non-standard category.
```python
custom_category: str | None = Field(
    default=None,
    description="Custom category for non-standard engagements. "
    "When set, takes precedence over the standard category enum."
)
```

### 2. Update `src/keystone/models/research.py`

**Add engagement type (for the classifier in Step 1):**
```python
class EngagementType(StrEnum):
    SIZING = "sizing"
    DIAGNOSTIC = "diagnostic"
    EVALUATIVE = "evaluative"
    EXPLORATORY = "exploratory"
    STRATEGIC = "strategic"
```

Add to ResearchSpec:
```python
engagement_type: EngagementType = Field(
    description="Classified engagement type. Drives pipeline depth, "
    "agent configuration, and evaluation profiles."
)
day_1_hypothesis: str | None = Field(
    default=None,
    description="Initial testable hypothesis that anchors the research. "
    "Prevents open-ended exploration (AutoGPT failure mode)."
)
```

Add to EngagementSpec:
```python
issue_tree: dict | None = Field(
    default=None,
    description="The MECE issue tree produced by Step 3 of the Spec Engine. "
    "JSON representation of the tree structure."
)
```

### 3. Create template files

Create `templates/RESEARCH.md.template`:
A markdown template with all sections from CAPSTONE-PLAN Section 3.2, plus
the new fields (engagement_type, day_1_hypothesis). Include inline comments
explaining what each section should contain.

Create `templates/research-tasks.json.template`:
A JSON template showing the DAG structure with dependencies, end_products,
and issue_tree_branch_ids. Include 2-3 example tasks demonstrating different
categories and dependency relationships.

### 4. Create JSON Schema files

Create `schemas/research_md.schema.json`:
JSON Schema that validates RESEARCH.md structure. Must enforce:
- decision_context is non-empty
- at least one primary research question
- non_goals is non-empty (forces explicit boundary-setting)
- engagement_type is one of the 5 types

Create `schemas/research_tasks.schema.json`:
JSON Schema that validates research-tasks.json. Must enforce:
- anti_confirmatory_framing is required on every task
- assigned_tools has 3-5 elements
- passes defaults to false
- dependencies reference valid task IDs within the same decomposition
- DAG has no cycles

### 5. Create 3-5 sample RESEARCH.md files

These serve as test fixtures AND as few-shot examples for the Specification Engine.

**Sample 1:** "Evaluate the competitive position of Luminar Technologies in the
autonomous vehicle lidar market" — the canonical test case from the existing spec.
Include research-tasks.json with 10+ tasks, DAG dependencies, varied categories.

**Sample 2:** "Determine optimal expansion locations for an auto body repair chain
across the top 50 US metropolitan areas" — Jack's test case from Directive 4.
This tests whether the schema handles non-standard engagements (no "auto body
repair" category in the enum — uses custom_category).

**Sample 3:** "Evaluate potential acquisition targets in the specialty chemicals
sector for a $2B PE fund" — M&A engagement type (EVALUATIVE). Tests DAG
dependencies (target screening → financial analysis → synergy assessment).

Optional additional samples for more coverage.

### 6. Write tests

Create `tests/unit/test_research_models.py`:
- Test ResearchSpec validation (required fields, type checking)
- Test DAG validation in TaskDecomposition (valid DAG passes, cycle detected raises)
- Test anti_confirmatory_framing validator (rejects confirmatory framing)
- Test tool count validator (rejects <3 or >5 tools)
- Test passes/status invariant
- Test custom_category override

Create `tests/unit/test_schemas.py`:
- Load each sample RESEARCH.md and validate against schema
- Load each sample research-tasks.json and validate against schema
- Test that schema rejects an invalid RESEARCH.md (missing decision_context)
- Test that schema rejects invalid tasks (missing anti_confirmatory_framing)

## BUILD PROTOCOL

1. Read all context files (Phase 0) before writing any code
2. Write tests FIRST (test_research_models.py, test_schemas.py)
3. Update the existing models (research.py, tasks.py)
4. Create template files
5. Create JSON schemas
6. Create sample files
7. Run all tests: `cd /path/to/project && python -m pytest tests/unit/ -v`
8. Fix any failures
9. Integration check: verify SpecificationEngineContract in contracts.py is
   compatible with the updated EngagementSpec model

## CONSTRAINTS

- Do NOT modify `contracts.py` or `events.py` (other sessions may be editing them)
- Do NOT modify `models/citations.py` (owned by Session 1A-2)
- Do NOT create files outside your owned directories (models/research.py,
  models/tasks.py, templates/, schemas/research_*, tests/unit/test_research*,
  tests/unit/test_schemas*)
- Preserve ALL existing model fields and validators. Add to them, don't remove.
- Keep all existing imports working

## DAY-1 CODING STANDARDS (for Temporal migration readiness)
1. Pure function layers (business logic separate from I/O)
2. Pydantic models for all inter-layer data
3. Separate controller from workflow logic
4. Correlation IDs on all operations
5. Idempotent operations where possible

## SESSION COMPLETION
Write a brief entry to `SESSION-LOG.md` documenting what was built, any
decisions made, and any known issues.
```

---

## Session 1A-2: Component #2 — Citation Data Model

### Prompt:

```
# Build Session: Component #2 — Citation Data Model

## Identity
You are building Component #2 of the Keystone Intelligence Engine: the citation
data model, content-hash provenance utilities, and JSON schemas for the citation
pipeline. Citations are the atomic unit of evidence provenance. Every claim in
the system traces back to citations. If citations are wrong, nothing is trustworthy.

## PHASE 0: MANDATORY CONTEXT LOADING

Read these files in order:

1. `CLAUDE.md` — Project overview
2. `JACK-ARCHITECTURAL-DIRECTIVES.md` — Directives 5, 8, 13 are most relevant
3. `CAPSTONE-PLAN-v2.md` Section 4.3-4.4 (Deliberation, claim-level IR) and
   Section 6.2 (Retrieval Architecture)
4. `audit/PHASE-1-IMPLEMENTATION-SPEC.md` Component #2 — Your build spec
5. `audit/batch-2-analysis/MASTER-SYNTHESIS.md` — Sections on retrieval split
   (#3a/#3b) and knowledge accumulation (content-hash provenance)
6. `src/keystone/models/citations.py` — **EXISTING MODEL. READ IN FULL.** You are
   updating this, not replacing it.
7. `src/keystone/models/confidence.py` — Confidence map models (these consume claims)
8. `src/keystone/contracts.py` — CitationProcessorContract defines the interface
   your models must support.
9. `src/keystone/events.py` — Existing event types.

## YOUR DELIVERABLES

### 1. Update `src/keystone/models/citations.py`

**Add content-hash provenance (MASTER-SYNTHESIS: knowledge accumulation):**

The Karpathy compiled wiki pattern requires content-hash provenance to trace
propositions back to source material. Add to Citation:
```python
content_hash: str | None = Field(
    default=None,
    description="SHA-256 hash of the source content at access time. "
    "Enables provenance tracking in compiled wiki (Karpathy pattern). "
    "None for citations not yet hash-verified."
)
```

Add to Claim:
```python
proposition_hashes: list[str] = Field(
    default_factory=list,
    description="Content hashes of the specific propositions supporting this claim. "
    "Enables fine-grained provenance from claim -> proposition -> source."
)
```

**Add wiki compilation metadata:**
```python
class WikiCompilationRecord(BaseModel):
    """Tracks how a citation's content was compiled into the engagement wiki."""

    citation_id: str
    engagement_id: str
    raw_path: str = Field(description="Path in raw/ directory")
    compiled_path: str | None = Field(
        default=None, description="Path in compiled/ directory (None if not yet compiled)"
    )
    content_hash: str = Field(description="SHA-256 of source content")
    compiled_at: datetime | None = Field(default=None)
```

### 2. Create `src/keystone/citation/` module

This is the first implementation code in the citation processing pipeline.

**`src/keystone/citation/__init__.py`** — Package init

**`src/keystone/citation/hash.py`** — Content hashing utilities:
```python
def compute_content_hash(content: str) -> str:
    """SHA-256 hash of source content for provenance tracking."""

def compute_proposition_hash(proposition: str, source_content_hash: str) -> str:
    """Hash linking a specific proposition to its source content."""

def verify_content_hash(content: str, expected_hash: str) -> bool:
    """Verify content hasn't changed since hash was computed."""
```

**`src/keystone/citation/dedup.py`** — Citation deduplication:
```python
def deduplicate_citations(citations: list[Citation]) -> list[Citation]:
    """Merge citations referring to the same source (same URL or DOI).

    When merging:
    - Combine found_by_agents lists
    - Keep highest quality_score
    - Preserve all metadata from the most complete record
    """

def find_corroboration_pairs(
    findings: list[StructuredFinding],
) -> list[CorroborationPair]:
    """Identify claims independently discovered by 2+ agents.

    Two claims corroborate if they reference the same citation
    (after deduplication) AND make substantively similar assertions.
    """
```

**`src/keystone/citation/url_check.py`** — URL liveness verification:
```python
async def check_url_liveness(url: str, timeout: float = 10.0) -> bool:
    """Check if a URL is reachable. HEAD request with fallback to GET."""

async def batch_check_urls(
    citations: list[Citation], concurrency: int = 10
) -> dict[str, bool]:
    """Check URL liveness for all citations concurrently."""
```

### 3. Create JSON Schema files

**`schemas/citation.schema.json`** — Validates Citation entity
**`schemas/claim.schema.json`** — Validates Claim entity
**`schemas/citation_manifest.schema.json`** — Validates CitationManifest output

All schemas must enforce:
- citation_id starts with "CIT-"
- claim_id starts with "CLM-"
- quality_score is 0-1
- confidence is 0-1
- content_hash is valid hex string when present

### 4. Write tests

**`tests/unit/test_citation_models.py`:**
- Test Citation creation and validation
- Test content_hash field (valid hex, None allowed)
- Test Claim with proposition_hashes
- Test CitationManifest assembly
- Test corroboration pair detection

**`tests/unit/test_citation_hash.py`:**
- Test compute_content_hash produces consistent SHA-256
- Test compute_proposition_hash links proposition to source
- Test verify_content_hash detects content changes

**`tests/unit/test_citation_dedup.py`:**
- Test deduplication merges same-URL citations
- Test deduplication merges same-DOI citations
- Test found_by_agents are combined correctly
- Test highest quality_score is preserved

**`tests/unit/test_url_check.py`:**
- Test URL check with mock HTTP responses (use pytest-httpx or responses library)
- Test batch checking with concurrency
- Test timeout handling
- Test fallback from HEAD to GET

## BUILD PROTOCOL

1. Read all context files
2. Write tests FIRST
3. Update citations.py model
4. Create citation/ module with hash, dedup, url_check
5. Create JSON schemas
6. Run all tests: `python -m pytest tests/unit/test_citation* -v`
7. Fix failures
8. Verify compatibility with CitationProcessorContract in contracts.py

## CONSTRAINTS

- Do NOT modify `models/research.py` or `models/tasks.py` (owned by Session 1A-1)
- Do NOT modify `contracts.py` or `events.py` (shared, append-only)
- Do NOT create files outside your owned directories
- Preserve ALL existing model fields and validators

## SESSION COMPLETION
Write a brief entry to `SESSION-LOG.md`.
```

---

## Session 1A-3: HITL Infrastructure

### Prompt:

```
# Build Session: HITL Infrastructure — Human-in-the-Loop Review Gates

## Identity
You are building the Human-in-the-Loop (HITL) infrastructure for the Keystone
Intelligence Engine. This is a new component not yet in the codebase. It
implements the two mandatory human review gates (Jack's Directive 7):

1. **Post-Specification gate:** After the Spec Engine produces the issue tree
   and agent configs, a human reviews and approves/modifies/rejects before
   research begins.
2. **Post-Deliberation gate:** After Deliberation produces the confidence map,
   a human reviews before content generation.

These gates are NON-NEGOTIABLE. The system runs autonomously between gates.

## PHASE 0: MANDATORY CONTEXT LOADING

Read these files in order:

1. `CLAUDE.md` — Project overview
2. `JACK-ARCHITECTURAL-DIRECTIVES.md` — **Directive 7 is your primary requirement.**
   Also read Directives 5 and 13 for staging guidance.
3. `CAPSTONE-PLAN-v2.md` — Search for "human review" and "HITL" references.
   Key locations: Section 3.4 (verification), Section 12 (implementation).
4. `audit/PHASE-1-IMPLEMENTATION-SPEC.md` — This component is NEW and may not
   have a full spec yet. Use the MASTER-SYNTHESIS description instead.
5. `audit/batch-2-analysis/MASTER-SYNTHESIS.md` — Section 1 describes the HITL
   state machine (Step 8 of the 10-step pipeline). Section 8 describes the
   new HITL infrastructure component.
6. `PARALLEL-EXECUTION-PLAN.md` — Contains the HITL component spec with table
   schemas.
7. `src/keystone/contracts.py` — Read SpecificationEngineContract and
   DeliberationContract. Your gates integrate at these boundaries.
8. `src/keystone/events.py` — You will ADD new event types (append-only).
9. `src/keystone/models/` — Read all models to understand the data types that
   flow through the gates (EngagementSpec, ConfidenceMap, AgentDefinition).

## WHAT TO BUILD

### 1. Database schema: `src/keystone/hitl/models.py`

Use SQLAlchemy 2.0 with async support. Three tables:

```python
class ReviewGate(Base):
    """A human review checkpoint in the pipeline."""
    __tablename__ = "review_gates"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # UUID
    engagement_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    client_id: Mapped[str] = mapped_column(String, nullable=False)
    gate_type: Mapped[str] = mapped_column(
        String, nullable=False
    )  # "post_specification" | "post_deliberation"
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="pending"
    )  # "pending" | "approved" | "modified" | "rejected"
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationships
    items: Mapped[list["ReviewItem"]] = relationship(back_populates="gate")
    decision: Mapped["ReviewDecision | None"] = relationship(back_populates="gate")


class ReviewItem(Base):
    """An artifact displayed to the human reviewer."""
    __tablename__ = "review_items"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    gate_id: Mapped[str] = mapped_column(ForeignKey("review_gates.id"))
    item_type: Mapped[str] = mapped_column(
        String, nullable=False
    )  # "issue_tree" | "agent_config" | "confidence_map" | "divergence_points" | "sprint_contract"
    content_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)

    gate: Mapped["ReviewGate"] = relationship(back_populates="items")


class ReviewDecision(Base):
    """The human's decision on a review gate."""
    __tablename__ = "review_decisions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    gate_id: Mapped[str] = mapped_column(ForeignKey("review_gates.id"), unique=True)
    decision: Mapped[str] = mapped_column(
        String, nullable=False
    )  # "approve" | "modify" | "reject"
    modifications_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_by: Mapped[str] = mapped_column(String, nullable=False)
    decided_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    gate: Mapped["ReviewGate"] = relationship(back_populates="decision")
```

### 2. Database migrations: `src/keystone/hitl/migrations/`

Create an Alembic migration (or raw SQL migration file) that creates all three tables.
Include indexes on engagement_id and gate_type for query performance.

### 3. HITL service: `src/keystone/hitl/service.py`

The business logic layer (pure functions where possible):

```python
class HITLService:
    """Manages the lifecycle of human review gates."""

    async def create_gate(
        self, engagement_id: str, client_id: str, gate_type: str,
        items: list[dict]
    ) -> ReviewGate:
        """Create a new review gate with artifacts for human review."""

    async def get_gate(self, gate_id: str) -> ReviewGate:
        """Retrieve a gate with all its items and decision."""

    async def get_pending_gates(
        self, engagement_id: str | None = None
    ) -> list[ReviewGate]:
        """List all pending review gates, optionally filtered by engagement."""

    async def submit_decision(
        self, gate_id: str, decision: str, decided_by: str,
        modifications: dict | None = None, reasoning: str | None = None
    ) -> ReviewDecision:
        """Record a human decision on a gate.

        State transitions:
        - pending -> approved (proceed to next pipeline stage)
        - pending -> modified (apply modifications, then proceed)
        - pending -> rejected (abort or restart this pipeline stage)

        Rejected gates halt the pipeline. Modified gates update the
        relevant artifacts (issue tree, agent configs, etc.) before proceeding.
        """

    async def wait_for_decision(
        self, gate_id: str, poll_interval: float = 1.0, timeout: float = 3600.0
    ) -> ReviewDecision:
        """Block until a human decision is made on this gate.

        Used by the pipeline orchestrator to pause at gate boundaries.
        Default timeout: 1 hour.
        """
```

### 4. REST API: `src/keystone/hitl/api.py`

FastAPI router with these endpoints:

```
GET  /api/v1/gates                    — List all gates (filterable by status, engagement_id)
GET  /api/v1/gates/{gate_id}          — Get gate details with items and decision
POST /api/v1/gates                    — Create a new gate (used by pipeline)
POST /api/v1/gates/{gate_id}/decide   — Submit a decision (used by human reviewer)

GET  /api/v1/health                   — Health check
```

Request/response schemas should use Pydantic models for validation.

### 5. Basic web UI: `src/keystone/hitl/static/`

A minimal HTML page (single file, no framework needed) that:
- Lists pending review gates
- Clicking a gate shows its items (issue tree, agent configs, etc.)
- Provides Approve / Modify / Reject buttons
- Modify opens a text area for modifications JSON and reasoning
- Submits the decision via the REST API

This is Phase 1 minimal. Rich UI with agent reasoning panels is Phase 2.
Functional over pretty. The goal is "a human can review and decide" not
"beautiful dashboard."

### 6. Add HumanReviewGateContract to contracts.py

**APPEND ONLY.** Add at the end of contracts.py:

```python
@runtime_checkable
class HumanReviewGateContract(Protocol):
    """Contract for Human-in-the-Loop review gates.

    Gates pause the pipeline at two mandatory checkpoints (Directive 7):
    1. Post-specification: human reviews issue tree + agent configs
    2. Post-deliberation: human reviews confidence map
    """

    async def create_and_wait(
        self,
        engagement_id: str,
        client_id: str,
        gate_type: str,
        items: list[dict],
    ) -> AsyncIterator[AnyPipelineEvent]:
        """Create a gate and wait for human decision.

        Yields GateCreated, then blocks until decision.
        Yields GateDecided with the result.
        """
        ...

    async def get_decision(self) -> dict:
        """Return the human's decision."""
        ...
```

### 7. Add HITL events to events.py

**APPEND ONLY.** Add at the end of events.py:

```python
class GateCreated(PipelineEvent):
    """A human review gate has been created and is awaiting decision."""
    gate_id: str
    gate_type: str  # "post_specification" | "post_deliberation"
    item_count: int

class GateDecided(PipelineEvent):
    """A human has made a decision on a review gate."""
    gate_id: str
    decision: str  # "approve" | "modify" | "reject"
    decided_by: str
    has_modifications: bool
```

### 8. Write tests

**`tests/unit/test_hitl_models.py`:**
- Test ReviewGate creation with valid/invalid states
- Test state transitions (pending → approved, pending → modified, pending → rejected)
- Test that resolved gates cannot be re-decided

**`tests/unit/test_hitl_service.py`:**
- Test create_gate with items
- Test submit_decision with approve
- Test submit_decision with modify (includes modifications_json)
- Test submit_decision with reject
- Test get_pending_gates filtering
- Test that deciding a non-pending gate raises error

**`tests/integration/test_hitl_api.py`:**
- Test full lifecycle: create gate → get gate → decide → verify state
- Test that API rejects invalid decisions
- Test health endpoint

Use an in-memory SQLite database for tests (SQLAlchemy supports this).
Tests should not require a running PostgreSQL instance.

## BUILD PROTOCOL

1. Read all context files
2. Write database models first (models.py)
3. Write tests
4. Implement service layer
5. Implement API
6. Create basic web UI
7. Run tests: `python -m pytest tests/ -v -k hitl`
8. Fix failures
9. APPEND contract and events to shared files
10. Verify the contract is compatible with SpecificationEngineContract
    and DeliberationContract (the gates sit between these)

## DEPENDENCY SETUP

This session needs:
- SQLAlchemy 2.0+ (should be in pyproject.toml)
- FastAPI + uvicorn
- asyncpg (for PostgreSQL) — but tests use SQLite
- Alembic (for migrations)

Check pyproject.toml for these. If missing, add them.

## CONSTRAINTS

- Do NOT modify existing classes in `contracts.py` — only APPEND new ones
- Do NOT modify existing classes in `events.py` — only APPEND new ones
- Do NOT modify any files in `models/` (owned by other sessions)
- The HITL infrastructure must work with both PostgreSQL (production) and
  SQLite (testing). Use SQLAlchemy's async engine abstraction.

## PHASE 1 STAGING (Directive 13)

BUILD now:
- Database schema (3 tables)
- Service layer (all CRUD + wait_for_decision)
- REST API (all endpoints)
- Basic web UI (functional, not pretty)
- Contract and events

STUB (Phase 2):
- Rich web UI with agent reasoning visualization
- WebSocket real-time updates
- Notification system (email/Slack when gate is pending)
- Audit trail for compliance

## SESSION COMPLETION
Write a brief entry to `SESSION-LOG.md`.
```

---

## Track 3: Casing Book Analysis (Claude Code Session)

### Setup

Place downloaded casing books (PDF, EPUB, or any format) in:
`references/casing-books/`

The prompt handles format detection and reading automatically. PDFs with issue tree
diagrams are fine — Claude Code reads PDFs natively with vision and can see the
diagram layouts. No manual conversion needed.

### Prompt:

````markdown
# Track 3: MECE Decomposition Skill Files from Casing Literature

## Identity
You are analyzing consulting case interview methodology books to extract the
PRINCIPLES of how expert consultants decompose problems into MECE (Mutually
Exclusive, Collectively Exhaustive) issue trees. Your output becomes a set of
skill files that teach AI agents how to perform this decomposition.

This is NOT about memorizing frameworks. It's about learning the METHODOLOGY
of structured problem decomposition so the system can handle ANY consulting
engagement — including domains it has never seen before (Jack's Directive 6:
the FITFO Standard).

## PHASE 0: CONTEXT LOADING

Read these files first to understand how the skill files will be used:

1. `CLAUDE.md` — Project overview
2. `JACK-ARCHITECTURAL-DIRECTIVES.md` — Pay special attention to:
   - Directive 2 (MECE Issue Tree Decomposition): the flow and requirements
   - Directive 6 (FITFO Standard): handle novel problems without predefined skills
   - Directive 12 (Casing Principles Over Example Libraries): PRINCIPLES, not templates
3. `CAPSTONE-PLAN-v2.md` Section 3 — How the Specification Engine uses issue trees
4. `audit/batch-2-analysis/MASTER-SYNTHESIS.md` Section 1 — The 10-step pipeline,
   specifically Steps 3 (Issue Tree Decomposition) and 4 (MECE Verification)
5. Check if `.claude/skills/` exists and read any existing skill files to match
   the format convention.

## PHASE 1: BOOK INGESTION

Read all files in `references/casing-books/`. Handle each by format:

**For PDFs:** Read natively using your PDF reading capability (page by page if
needed). You CAN see diagrams, flowcharts, and issue tree visuals — extract the
structural logic they convey, not just surrounding text. When a diagram shows an
issue tree, capture: the root question, the branching dimension chosen for the
first cut, the number of levels, and the logic connecting parent to child nodes.

**For EPUB/MOBI:** Convert to text first:
```bash
# Install if needed
pip install ebooklib beautifulsoup4 --break-system-packages
```
Then write a quick Python script to extract chapter text. Structure doesn't matter
much — you're reading for principles, not preserving formatting.

**For any other format (.doc, .docx, .txt, .html):** Read directly or convert
as appropriate. The goal is access to the full text content.

**IMPORTANT:** Read EVERY chapter of EVERY book. Do not skim or sample. The most
valuable decomposition principles are often buried in advanced chapters, worked
examples, or appendices — not in the introductory "what is MECE" material. The
quality of your extraction determines the quality of the system's core analytical
capability.

**When you encounter issue tree diagrams:**
- Describe the tree structure explicitly (root > branches > sub-branches)
- Note what decomposition PRINCIPLE the diagram illustrates
- Note whether the tree uses a financial lens, operational lens, etc.
- If the diagram shows a common anti-pattern (for comparison), capture that too

## PHASE 2: EXTRACTION

Work through the books systematically. For each major principle you identify,
note which book(s) and chapter(s) it came from. Cross-reference across books —
when multiple authors describe the same principle differently, synthesize the
strongest version.

### 2.1 Decomposition Decision Rules
- How do experts decide the FIRST CUT? (By what dimension do they split the root node?)
- What signals indicate horizontal expansion (more branches at same level) vs.
  vertical deepening (more levels below a branch)?
- How is the right granularity for leaf nodes determined?
- When is 2 levels enough? When do you need 4-5?
- How do you handle cross-cutting concerns that resist clean branching?
- How does the nature of the question (sizing vs. diagnostic vs. evaluative)
  change the decomposition strategy?

### 2.2 MECE Verification Methodology
- Specific checks for mutual exclusivity (not just "make sure they don't overlap")
- Specific checks for collective exhaustiveness (not just "make sure nothing is missing")
- The most common MECE violations and their telltale signatures
- How to handle the "residual bucket" problem (catch-all "Other" branches that
  mask incomplete decomposition)
- The "deletion test": remove each branch and check if the parent's question
  can still be fully answered with the remaining branches

### 2.3 Consulting Lenses
- What are the standard analytical lenses (financial, operational, market,
  regulatory, organizational, customer, technological, competitive)?
- When does each lens produce the most insight?
- How do different lenses produce structurally different trees for the same problem?
- Why do heterogeneous lenses (3-4 agents with different lenses simultaneously)
  produce better trees than homogeneous lenses?

### 2.4 Hypothesis-Driven Decomposition
- How a Day-1 Hypothesis shapes the tree (decompose TOWARD testability)
- How to frame each branch as a testable sub-hypothesis
- How to prevent the hypothesis from biasing the decomposition toward confirmation
- The relationship between the hypothesis and the "so what" of each branch

### 2.5 Anti-Patterns (Critical)
- Trees that are too broad (laundry list: 10+ first-level branches, no depth)
- Trees that are too deep (analysis paralysis: 5+ levels before any research)
- Trees that are non-MECE despite looking structured
- Trees that are MECE but not USEFUL (technically correct but analytically empty)
- Framework cramming (forcing a problem into a standard framework that doesn't fit)
- The "boiling the ocean" anti-pattern (trying to decompose everything at once
  instead of shallow start with adaptive deepening)

### 2.6 Adaptation During Research (ADaPT pattern)
- How should a tree evolve as new information comes in?
- When do you ADD branches (new insight opens new avenue)?
- When do you PRUNE branches (research shows this branch is irrelevant)?
- When do you RESTRUCTURE (the first cut was wrong, need different dimensions)?
- How do you maintain MECE properties during evolution?
- The principle: start shallow (2-3 levels, 8-20 leaf nodes), deepen adaptively

## PHASE 3: OUTPUT SKILL FILES

Create these files in `skills/mece-decomposition/`:

### `skills/mece-decomposition/SKILL.md`
**The core methodology file.** 2,000-4,000 words.

This is what a Sonnet-class agent reads before attempting decomposition. It must be:
- CONCRETE and OPERATIONAL (not abstract theory)
- Written as INSTRUCTIONS the agent follows, in second person
- Include IF/THEN decision rules where possible
- Organized by phase: First Cut > Branch Development > Validation > Adaptation
- Include worked examples where they illustrate a principle (but examples serve
  the principle, not the other way around)

### `skills/mece-decomposition/principles.md`
**The theoretical grounding.** 1,000-3,000 words.

Why the decision rules work. The expert reasoning behind each principle. The
cognitive science of structured problem decomposition. Opus-class agents read
this for deeper understanding when the simple rules aren't enough.

### `skills/mece-decomposition/gotchas.md`
**Common decomposition failures.** 1,000-2,000 words.

Format for each gotcha:

> **## [Name of Anti-Pattern]**
> **What it looks like:** [Description]
> **How to detect it:** [Specific diagnostic criteria]
> **Why it happens:** [Root cause]
> **How to fix it:** [Concrete remediation steps]
> **Example:** [Brief illustration]

### `skills/mece-decomposition/validation.md`
**Step-by-step validation checklist.** 500-1,000 words.

This is what the MECE Verification step (Step 4 of the Spec Engine) uses.
Each check should be:
- Binary (pass/fail, not subjective judgment)
- Automatable by an LLM (specific enough that a Sonnet agent can apply it)
- Independent (each check tests one thing)

### `skills/mece-decomposition/lens-library.md`
**The consulting lenses catalog.** 1,000-2,000 words.

For each lens:
- What it is (1-2 sentences)
- When to apply it (engagement types, question types)
- How it shapes decomposition (what becomes the first cut, what goes deeper)
- What it tends to miss (blind spots)
- Complementary lenses (which other lenses fill its gaps)

## PHASE 4: QUALITY SELF-CHECK

After producing all files, test your output against these criteria:

1. **Operational test:** Could a Sonnet agent, reading only SKILL.md, produce a
   meaningfully better issue tree than without it? If the SKILL.md just says
   "be MECE," it fails.

2. **Novelty test:** Does SKILL.md help with a problem the agent has NEVER seen?
   (e.g., "analyze optimal warehouse locations for a pet food distributor").
   If the skill only works for familiar consulting problems, it fails Directive 6.

3. **Specificity test:** Are the decision rules specific enough to be actionable?
   "Consider financial impacts" fails. "If the problem involves resource allocation,
   the first cut should separate demand-side from supply-side factors" passes.

4. **Anti-pattern test:** Could gotchas.md help an agent DETECT its own bad
   decomposition? Read each gotcha and ask: "Is the detection criterion specific
   enough that I could check for this automatically?"

5. **Diagram coverage test:** Did you extract structural principles from the issue
   tree diagrams you encountered? If you only used surrounding text and ignored
   diagram structure, go back and capture the visual logic.

If any test fails, revise before finalizing.

## SESSION COMPLETION
Write a brief entry to `SESSION-LOG.md`.
````

---

## Execution Sequence Summary

**Immediate parallel launch (5 sessions):**

| Session | Duration | Produces | Blocks |
|---------|----------|----------|--------|
| Track 1 (Arch docs) | 2-3 hrs | Updated CAPSTONE-PLAN, IMPL-SPEC | Phase 1B builder sessions |
| Track 3 (Casing books) | 1-2 hrs | MECE skill files | Component #5 (Phase 1C) |
| Session 1A-1 (#1 Schemas) | 1-2 days | Templates, schemas, samples | Components #5, #7 |
| Session 1A-2 (#2 Citations) | 1-2 days | Updated models, hash utils | Components #7, #8 |
| Session 1A-3 (HITL) | 2-3 days | Database, API, basic UI | Components #5, #9 |

**After these complete, next parallel wave:**

| Session | Depends On | Duration |
|---------|-----------|----------|
| Track 2A (SemanticCite eval) | Track 1 | 1-2 hrs |
| Track 2B (mcp-gateway eval) | Track 1 | 1-2 hrs |
| Track 2C (VectorChord eval) | Track 1 | 1-2 hrs |
| Phase 1B-1 (#3a Source Discovery) | 1A-2, Track 2C | 1-2 weeks |
| Phase 1B-2 (#4 MCP Gateway) | Track 2B | 1 week |

**Then Phase 1C (the big ones):**

| Session | Depends On | Duration |
|---------|-----------|----------|
| Phase 1C-1 (#5 Spec Engine) | 1A-1, 1A-3, HITL, Track 3 | 2-3 weeks |
| Phase 1C-2 (#6 Evaluator) | 1A-1, 1A-2 | 2-3 weeks |
