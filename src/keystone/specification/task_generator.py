"""Step 7: Research task generation with DAG structure.

Generates research-tasks.json from a prioritized issue tree. Each leaf
node becomes one or more ResearchTasks with DAG dependencies,
anti-confirmatory framing, and per-branch end_product specifications.

Full implementation follows after template_registry and priority_scorer.
"""

from __future__ import annotations

import json
import logging

from pydantic import ValidationError

from keystone.evaluator.retry import LLMCallable, retry_llm_call
from keystone.llm.parsing import ParseError, safe_llm_json
from keystone.models.research import EngagementType, PipelineProfile, ResearchSpec
from keystone.models.tasks import (
    ModelTier,
    ResearchTask,
    TaskCategory,
    TaskDecomposition,
    TaskImportance,
    TaskType,
)
from keystone.specification._prompts import load_prompt
from keystone.specification.decomposer import IssueTree
from keystone.specification.priority_scorer import PriorityScore
from keystone.specification.template_registry import TemplateRegistry
from keystone.tool_names import ALL_TOOLS, BASELINE_AGENT_TOOLS, SYSTEM_OWNED_TOOLS

logger = logging.getLogger(__name__)

TASK_GENERATION_BATCH_SIZE = 5


def _ensure_minimum_distinct_tools(tools: list[str]) -> list[str]:
    """Pad a tool list to 3-5 distinct entries drawn from BASELINE_AGENT_TOOLS.

    ResearchTask requires 3-5 assigned tools. When a template provides fewer
    than 3, we extend with distinct agent-assignable tools rather than
    duplicating a single entry — the old behavior (``[DEFAULT_TOOLS[0]] * n``)
    produced useless "three copies of exa_search" lists. Order of existing
    tools is preserved; baseline tools are appended only when not already
    present to keep the set distinct.
    """
    distinct: list[str] = []
    seen: set[str] = set()
    for tool in tools:
        if tool in seen:
            continue
        distinct.append(tool)
        seen.add(tool)

    for baseline in BASELINE_AGENT_TOOLS:
        if len(distinct) >= 3:
            break
        if baseline in seen:
            continue
        distinct.append(baseline)
        seen.add(baseline)

    return distinct[:5]


class TaskGenerator:
    """Generate research-tasks.json from a prioritized issue tree.

    For each leaf node:
    1. Create ResearchTask with DAG dependencies
    2. Assign anti-confirmatory framing
    3. Specify end_product per branch
    4. Match to agent template (via TemplateRegistry)
    5. Assign 3-5 tools from matched template
    """

    def __init__(self, llm: LLMCallable, registry: TemplateRegistry) -> None:
        self._llm = llm
        self._registry = registry

    async def generate(
        self,
        tree: IssueTree,
        priorities: list[PriorityScore],
        engagement_type: EngagementType,
        spec: ResearchSpec,
    ) -> TaskDecomposition:
        """Generate a TaskDecomposition from the issue tree.

        When the issue tree has more than ``TASK_GENERATION_BATCH_SIZE``
        leaves, the priorities are partitioned into batches and each
        batch is processed with a separate LLM call.  Results are merged,
        IDs are reassigned sequentially by priority, and cross-batch
        dependency references are cleaned.

        If the LLM produces cyclic dependencies, catches ValidationError
        and retries (max 2 retries per batch).
        """
        priority_ranks = self._build_priority_ranks(priorities)

        if len(priorities) > TASK_GENERATION_BATCH_SIZE:
            return await self._generate_batched(
                tree, priorities, engagement_type, spec, priority_ranks
            )

        return await self._generate_single(tree, priorities, engagement_type, spec, priority_ranks)

    async def _generate_single(
        self,
        tree: IssueTree,
        priorities: list[PriorityScore],
        engagement_type: EngagementType,
        spec: ResearchSpec,
        priority_ranks: dict[str, int],
    ) -> TaskDecomposition:
        """Original single-call generation path for small trees."""
        prompt = self._build_prompt(tree, priorities, engagement_type, spec)

        last_error: Exception | None = None
        for attempt in range(3):
            try:
                raw = await retry_llm_call(
                    self._llm, prompt, description=f"task_generation_attempt_{attempt}"
                )
                data = safe_llm_json(raw, required_keys=("tasks",))
                tasks = self._parse_tasks(data, spec, engagement_type, priority_ranks)
                if not tasks:
                    raise ValueError("LLM returned empty tasks list")
                return TaskDecomposition(
                    project=spec.title,
                    engagement_id=spec.engagement_id,
                    client_id=spec.client_id,
                    research_md_path=f"engagements/{spec.engagement_id}/RESEARCH.md",
                    specification_version=spec.specification_version,
                    decomposition_rationale=data.get(
                        "decomposition_rationale",
                        tree.metadata.synthesis_rationale,
                    ),
                    tasks=tasks,
                )
            except (ParseError, ValidationError, ValueError, KeyError) as exc:
                last_error = exc
                logger.warning("Task generation attempt %d failed: %s", attempt + 1, exc)

        raise RuntimeError(f"Task generation failed after 3 attempts: {last_error}")

    async def _generate_batched(
        self,
        tree: IssueTree,
        priorities: list[PriorityScore],
        engagement_type: EngagementType,
        spec: ResearchSpec,
        priority_ranks: dict[str, int],
    ) -> TaskDecomposition:
        """Multi-batch task generation for large issue trees."""
        sorted_priorities = sorted(
            priorities,
            key=lambda p: (
                -p.priority_score,
                -p.decision_relevance,
                -p.uncertainty_reduction,
                p.branch_id,
            ),
        )
        batches = [
            sorted_priorities[i : i + TASK_GENERATION_BATCH_SIZE]
            for i in range(0, len(sorted_priorities), TASK_GENERATION_BATCH_SIZE)
        ]
        logger.info(
            "Task generation: %d leaves -> %d batches of <=%d",
            len(priorities),
            len(batches),
            TASK_GENERATION_BATCH_SIZE,
        )

        all_tasks: list[ResearchTask] = []
        for batch_idx, batch in enumerate(batches):
            batch_leaf_ids = [p.branch_id for p in batch]
            prompt = self._build_prompt(tree, batch, engagement_type, spec)
            prompt += (
                f"\n\n## Batch Context\n"
                f"This is batch {batch_idx + 1} of {len(batches)}. "
                f"Generate tasks ONLY for these leaf nodes: "
                f"{', '.join(batch_leaf_ids)}. "
                f"Dependencies should only reference task IDs within this batch."
            )

            last_error: Exception | None = None
            for attempt in range(3):
                try:
                    raw = await retry_llm_call(
                        self._llm,
                        prompt,
                        description=f"task_generation_b{batch_idx + 1}_attempt_{attempt}",
                    )
                    data = safe_llm_json(raw, required_keys=("tasks",))
                    tasks = self._parse_tasks(data, spec, engagement_type, priority_ranks)
                    if not tasks:
                        raise ValueError("LLM returned empty tasks list")
                    all_tasks.extend(tasks)
                    break
                except (ParseError, ValidationError, ValueError, KeyError) as exc:
                    last_error = exc
                    logger.warning(
                        "Task generation batch %d attempt %d failed: %s",
                        batch_idx + 1,
                        attempt + 1,
                        exc,
                    )
            else:
                raise RuntimeError(
                    f"Task generation batch {batch_idx + 1} failed after 3 attempts: {last_error}"
                )

        all_tasks.sort(key=lambda t: t.priority)
        id_map: dict[str, str] = {}
        for i, task in enumerate(all_tasks):
            new_id = f"task_{i + 1:03d}"
            id_map[task.id] = new_id
            task.id = new_id

        valid_ids = set(id_map.values())
        for task in all_tasks:
            task.dependencies = [id_map.get(d, d) for d in task.dependencies]
            task.dependencies = [d for d in task.dependencies if d in valid_ids]

        return TaskDecomposition(
            project=spec.title,
            engagement_id=spec.engagement_id,
            client_id=spec.client_id,
            research_md_path=f"engagements/{spec.engagement_id}/RESEARCH.md",
            specification_version=spec.specification_version,
            decomposition_rationale=(
                f"Multi-batch generation ({len(batches)} batches, {len(all_tasks)} tasks)"
            ),
            tasks=all_tasks,
        )

    def _build_prompt(
        self,
        tree: IssueTree,
        priorities: list[PriorityScore],
        engagement_type: EngagementType,
        spec: ResearchSpec,
    ) -> str:
        _system_owned = set(SYSTEM_OWNED_TOOLS)
        _assignable_tools = [t for t in ALL_TOOLS if t not in _system_owned]
        return load_prompt(
            "task_generation",
            question=spec.questions[0].question if spec.questions else "",
            engagement_type=engagement_type.value,
            engagement_id=spec.engagement_id,
            client_id=spec.client_id,
            issue_tree=json.dumps(tree.model_dump(), indent=2),
            priorities=json.dumps([p.model_dump() for p in priorities], indent=2),
            day_1_hypothesis=spec.day_1_hypothesis or "",
            available_tools=", ".join(_assignable_tools),
        )

    def _parse_tasks(
        self,
        data: dict,
        spec: ResearchSpec,
        engagement_type: EngagementType,
        priority_ranks: dict[str, int],
    ) -> list[ResearchTask]:
        """Parse LLM output into validated ResearchTask objects."""
        tasks_raw = data.get("tasks", [])
        tasks: list[ResearchTask] = []

        for i, t in enumerate(tasks_raw):
            task_id = t.get("id", f"task_{i + 1:03d}")
            branch_id = t.get("issue_tree_branch_id")
            priority_rank = priority_ranks.get(branch_id or "")
            if priority_rank is None:
                priority_rank = self._coerce_priority(t.get("priority")) or (i + 1)

            # Match template for tool assignment
            category = self._resolve_category(t.get("category", "strategic_positioning"))
            temp_task = ResearchTask(
                id=task_id,
                engagement_id=spec.engagement_id,
                client_id=spec.client_id,
                category=category,
                type=TaskType(t.get("type", "estimative")),
                target_decision_usefulness=t.get("target_decision_usefulness", 3),
                description=t.get("description", ""),
                required_sources=t.get("required_sources", []),
                acceptance_criteria=t.get("acceptance_criteria", ["Meets quality bar"]),
                deliverable_destination=t.get("deliverable_destination", "Section TBD"),
                priority=priority_rank,
                importance=self._resolve_importance(
                    priority_rank=priority_rank,
                    spec=spec,
                    target_decision_usefulness=t.get("target_decision_usefulness", 3),
                ),
                anti_confirmatory_framing=t.get(
                    "anti_confirmatory_framing", "Evaluate evidence both for and against"
                ),
                assigned_tools=self._resolve_tools(t, category, engagement_type),
                assigned_model=ModelTier(t.get("assigned_model", "standard")),
                end_product=t.get("end_product", "Structured analysis with supporting evidence"),
                dependencies=t.get("dependencies", []),
                issue_tree_branch_id=branch_id,
                custom_category=t.get("custom_category"),
            )
            tasks.append(temp_task)

        return sorted(tasks, key=lambda task: task.priority)

    def _resolve_category(self, raw: str) -> TaskCategory:
        """Map raw category string to TaskCategory, defaulting gracefully.

        For unknown values, attempts semantic matching before falling back
        to STRATEGIC_POSITIONING. The caller preserves the original string
        via custom_category on the ResearchTask.
        """
        try:
            return TaskCategory(raw)
        except ValueError:
            lower = raw.lower()
            if any(
                kw in lower
                for kw in (
                    "tech",
                    "architecture",
                    "engineering",
                    "software",
                    "system",
                    "design",
                    "implementation",
                )
            ):
                return TaskCategory.TECHNOLOGY_ASSESSMENT
            if any(kw in lower for kw in ("market", "sizing", "tam", "sam")):
                return TaskCategory.MARKET_SIZING
            if any(kw in lower for kw in ("compet", "landscape", "rival")):
                return TaskCategory.COMPETITIVE_LANDSCAPE
            if any(kw in lower for kw in ("financ", "revenue", "cost", "valuation")):
                return TaskCategory.FINANCIAL_ANALYSIS
            if any(kw in lower for kw in ("regulat", "compliance", "legal", "policy")):
                return TaskCategory.REGULATORY
            return TaskCategory.STRATEGIC_POSITIONING

    def _resolve_tools(
        self,
        task_data: dict,
        category: TaskCategory,
        engagement_type: EngagementType,
    ) -> list[str]:
        """Resolve tool assignments: use LLM-provided if valid, else template match."""
        registered = set(ALL_TOOLS)
        tools = task_data.get("assigned_tools", [])
        if isinstance(tools, list):
            # Filter to only registered tool names
            valid_tools = [t for t in tools if t in registered]
            if 3 <= len(valid_tools) <= 5:
                return valid_tools

        # Fall back to template tools. Build the temp task with distinct
        # baseline tools so the template matcher does not receive a
        # contrived duplicate list.
        temp_task = ResearchTask(
            id="temp",
            engagement_id="temp",
            client_id="temp",
            category=category,
            type=TaskType.ESTIMATIVE,
            target_decision_usefulness=3,
            description="temp",
            acceptance_criteria=["temp"],
            deliverable_destination="temp",
            priority=1,
            anti_confirmatory_framing="Evaluate whether this is the case, including evidence both for and against",
            assigned_tools=list(BASELINE_AGENT_TOOLS),
            end_product="temp",
        )
        match = self._registry.match(temp_task, engagement_type)
        template_tools = list(match.template.tools[:5])
        return _ensure_minimum_distinct_tools(template_tools)

    def _resolve_importance(
        self,
        *,
        priority_rank: int,
        spec: ResearchSpec,
        target_decision_usefulness: int,
    ) -> TaskImportance:
        """Assign task importance from scored task priority for Wave 2B policy."""
        if priority_rank == 1:
            return TaskImportance.PRIMARY

        if spec.effective_pipeline_profile == PipelineProfile.DEEP and priority_rank <= 3:
            return TaskImportance.CRITICAL

        if target_decision_usefulness <= 2 and priority_rank > 5:
            return TaskImportance.OPTIONAL

        return TaskImportance.SUPPORTING

    def _build_priority_ranks(
        self,
        priorities: list[PriorityScore],
    ) -> dict[str, int]:
        ordered = sorted(
            priorities,
            key=lambda score: (
                -score.priority_score,
                -score.decision_relevance,
                -score.uncertainty_reduction,
                score.branch_id,
            ),
        )
        return {priority.branch_id: index for index, priority in enumerate(ordered, start=1)}

    def _coerce_priority(self, raw: object) -> int | None:
        if not isinstance(raw, int):
            return None
        return raw if raw >= 1 else None
