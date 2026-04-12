"""Research task data models for the Keystone Intelligence Engine.

Based on Component #1 schemas and CAPSTONE-PLAN-v2.md Section 3.6.
Tasks are the unit of work dispatched to L1 research agents. The
Specification Engine (L0) decomposes a RESEARCH.md into 15-50 tasks.
"""

from __future__ import annotations

from collections import defaultdict, deque
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TaskCategory(StrEnum):
    """The analytical domain a research task belongs to."""

    MARKET_SIZING = "market_sizing"
    COMPETITIVE_LANDSCAPE = "competitive_landscape"
    FINANCIAL_ANALYSIS = "financial_analysis"
    TECHNOLOGY_ASSESSMENT = "technology_assessment"
    REGULATORY = "regulatory"
    STRATEGIC_POSITIONING = "strategic_positioning"


class TaskType(StrEnum):
    """ICD 203 intelligence type classification.

    Estimative tasks (forward-looking, probabilistic) weight Calibrated
    Confidence higher. Current tasks (situation updates, timeliness)
    weight Source Quality higher.
    """

    ESTIMATIVE = "estimative"
    CURRENT = "current"


class ModelTier(StrEnum):
    """Available model tiers for task assignment.

    Flagship for L0/L4 (judgment), Standard for L1 (throughput),
    Fast for extraction/classification, Light for filtering/routing.
    """

    FLAGSHIP = "flagship"
    STANDARD = "standard"
    FAST = "fast"
    LIGHT = "light"


class TaskStatus(StrEnum):
    """Lifecycle state of a research task."""

    PENDING = "pending"
    CLAIMED = "claimed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PASSED = "passed"


class TaskImportance(StrEnum):
    """How essential a task is to pipeline publishability."""

    PRIMARY = "primary"
    CRITICAL = "critical"
    SUPPORTING = "supporting"
    OPTIONAL = "optional"


class ResearchTask(BaseModel):
    """A discrete research task assigned to a single L1 agent.

    Design decisions from CAPSTONE-PLAN-v2.md Section 3.6:
    1. Tasks are JSON, not Markdown (models corrupt Markdown less than JSON).
    2. Each task carries explicit acceptance criteria (sprint contracts).
    3. The `passes` field can only be flipped by the Evaluator, never the agent.
    4. Anti-confirmatory framing is mandatory on every task.
    5. Deliverable destinations tagged from Day 1.
    6. Task type drives evaluation weight profiles.
    7. Decision-usefulness threshold enforced (Level 3 minimum for client-facing).
    """

    model_config = ConfigDict(frozen=False)

    id: str = Field(description="Unique task identifier, format task_NNN")
    engagement_id: str = Field(description="Parent engagement for multi-tenancy isolation")
    client_id: str = Field(description="Client identifier for data sandboxing")
    category: TaskCategory = Field(description="Analytical domain")
    type: TaskType = Field(description="ICD 203 classification: estimative or current")
    target_decision_usefulness: int = Field(
        ge=1,
        le=5,
        description="Minimum decision-usefulness level (1=informational, 5=decision-making). "
        "Client-facing requires >= 3.",
    )
    description: str = Field(description="What this task should investigate")
    required_sources: list[str] = Field(
        default_factory=list,
        description="Source types required (industry_reports, financial_data, academic, etc.)",
    )
    acceptance_criteria: list[str] = Field(
        description="Sprint contract criteria the Evaluator grades against"
    )
    deliverable_destination: str = Field(
        description="Where findings map in the final output (e.g., 'Section 2: Market Landscape')"
    )
    passes: bool = Field(
        default=False,
        description="Quality gate flag. Only the Evaluator can set this to True.",
    )
    priority: int = Field(
        ge=1, description="Execution priority (1 = highest)"
    )
    importance: TaskImportance = Field(
        default=TaskImportance.SUPPORTING,
        description="Task importance for governance and coverage policy.",
    )
    anti_confirmatory_framing: str = Field(
        description="Evaluative framing requiring evidence both for and against. "
        "Must not be confirmatory ('find evidence for X').",
    )
    assigned_tools: list[str] = Field(
        description="3-5 MCP tools this agent may use (structural enforcement via gateway)"
    )
    assigned_model: ModelTier = Field(
        default=ModelTier.STANDARD,
        description="Which model tier runs this task",
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="Current lifecycle state",
    )
    assigned_agent_id: str | None = Field(
        default=None, description="ID of the agent that claimed this task"
    )

    # --- Batch 2 additions ---

    dependencies: list[str] = Field(
        default_factory=list,
        description="Task IDs this task depends on. Empty = no dependencies. "
        "Forms a DAG, not a flat list.",
    )
    end_product: str = Field(
        description="Specific output format for this branch "
        "(e.g., 'comparison table with 8+ competitors', "
        "'sensitivity analysis with +/-20% assumption variation')",
    )
    issue_tree_branch_id: str | None = Field(
        default=None,
        description="ID of the issue tree branch this task derives from. "
        "Links task back to MECE decomposition.",
    )
    custom_category: str | None = Field(
        default=None,
        description="Custom category for non-standard engagements. "
        "When set, takes precedence over the standard category enum.",
    )

    @property
    def effective_category(self) -> str:
        """Return custom_category if set, otherwise the standard category value."""
        return self.custom_category if self.custom_category is not None else self.category.value

    @field_validator("assigned_tools")
    @classmethod
    def validate_tool_count(cls, v: list[str]) -> list[str]:
        if len(v) < 3 or len(v) > 5:
            raise ValueError("Each task must have 3-5 assigned tools (per agent specialization)")
        return v

    @field_validator("anti_confirmatory_framing")
    @classmethod
    def validate_not_confirmatory(cls, v: str) -> str:
        confirmatory_patterns = ["find evidence for", "prove that", "confirm that", "show that"]
        lower = v.lower()
        for pattern in confirmatory_patterns:
            if lower.startswith(pattern):
                raise ValueError(
                    f"Anti-confirmatory framing must not start with '{pattern}'. "
                    "Use evaluative framing: 'evaluate whether..., "
                    "including evidence both for and against'"
                )
        return v

    @model_validator(mode="after")
    def validate_passes_not_self_set(self) -> ResearchTask:
        if self.passes and self.status != TaskStatus.PASSED:
            raise ValueError("passes=True requires status=PASSED (only Evaluator sets this)")
        return self


class TaskDecomposition(BaseModel):
    """The full task list output by the Specification Engine (L0).

    This is the research-tasks.json structure from CAPSTONE-PLAN-v2.md Section 3.6.
    """

    project: str = Field(description="Human-readable project name")
    engagement_id: str = Field(description="Parent engagement for multi-tenancy isolation")
    client_id: str = Field(description="Client identifier for data sandboxing")
    research_md_path: str = Field(description="Path to the RESEARCH.md file")
    specification_version: int = Field(
        ge=1, description="Version number of the specification"
    )
    decomposition_rationale: str = Field(
        description="Why the question was decomposed this way"
    )
    tasks: list[ResearchTask] = Field(
        description="15-50 discrete research tasks"
    )

    @model_validator(mode="after")
    def validate_dag(self) -> TaskDecomposition:
        """Verify task dependencies form a valid DAG (no cycles, no dangling refs)."""
        task_ids = {t.id for t in self.tasks}

        # Check all dependency references are valid task IDs
        for task in self.tasks:
            for dep in task.dependencies:
                if dep not in task_ids:
                    raise ValueError(
                        f"Invalid dependency: task '{task.id}' depends on "
                        f"'{dep}' which does not exist in this decomposition"
                    )

        # Topological sort via Kahn's algorithm to detect cycles
        adjacency: dict[str, list[str]] = defaultdict(list)
        in_degree: dict[str, int] = {t.id: 0 for t in self.tasks}
        for task in self.tasks:
            for dep in task.dependencies:
                adjacency[dep].append(task.id)
                in_degree[task.id] += 1

        queue = deque(tid for tid, deg in in_degree.items() if deg == 0)
        visited_count = 0
        while queue:
            node = queue.popleft()
            visited_count += 1
            for neighbor in adjacency[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if visited_count != len(self.tasks):
            raise ValueError(
                "Cycle detected in task dependencies. "
                "Task dependencies must form a directed acyclic graph (DAG)."
            )

        return self
