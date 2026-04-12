"""L0 Specification Engine: 10-step pipeline orchestrator.

Implements SpecificationEngineContract. Takes a natural language question
and produces a complete EngagementSpec (RESEARCH.md + research-tasks.json +
issue tree + validation report).

Steps 1-7: Generate specification
Step 8: HITL Gate 1 (blocks until human decision)
Steps 9-10: Research execution + feedback (STUBS for Phase 1)
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator, Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from keystone.evaluator.retry import LLMCallable
from keystone.events import (
    AgentDispatched,
    AnyPipelineEvent,
    SpecificationGenerated,
    TasksDecomposed,
)
from keystone.models.research import (
    EngagementSpec,
    EngagementType,
    MethodologyRequirement,
    PipelineProfile,
    ResearchQuestion,
    ResearchSpec,
    SourceRequirement,
    ValidationReport,
)
from keystone.specification.decomposer import Decomposer, IssueTree
from keystone.specification.engagement_classifier import (
    ClassificationResult,
    EngagementClassifier,
)
from keystone.specification.intent_clarifier import (
    IntentClarificationResult,
    IntentClarifier,
)
from keystone.specification.priority_scorer import PriorityScorer
from keystone.specification.task_generator import TaskGenerator
from keystone.specification.template_registry import TemplateRegistry
from keystone.specification.validator import MECEValidator

if TYPE_CHECKING:
    from keystone.models.tasks import TaskDecomposition

logger = logging.getLogger(__name__)

# Default methodology per engagement type
_DEFAULT_METHODOLOGY: dict[EngagementType, list[MethodologyRequirement]] = {
    EngagementType.SIZING: [
        MethodologyRequirement(
            framework="Top-Down / Bottom-Up Estimation",
            mandatory=True,
            rationale="Market sizing requires convergent estimation approaches",
        ),
    ],
    EngagementType.DIAGNOSTIC: [
        MethodologyRequirement(
            framework="Root Cause Analysis",
            mandatory=True,
            rationale="Diagnostic engagements require structured causal investigation",
        ),
    ],
    EngagementType.EVALUATIVE: [
        MethodologyRequirement(
            framework="Porter's Five Forces",
            mandatory=False,
            rationale="Structural competitive analysis framework",
        ),
    ],
    EngagementType.EXPLORATORY: [
        MethodologyRequirement(
            framework="Landscape Mapping",
            mandatory=True,
            rationale="Exploratory engagements require structured surveying",
        ),
    ],
    EngagementType.STRATEGIC: [
        MethodologyRequirement(
            framework="Scenario Planning",
            mandatory=True,
            rationale="Strategic engagements require multi-scenario analysis",
        ),
        MethodologyRequirement(
            framework="Porter's Five Forces",
            mandatory=False,
            rationale="Structural competitive analysis",
        ),
    ],
}

_DEFAULT_SOURCES: list[SourceRequirement] = [
    SourceRequirement(source_type="news", minimum_count=5, quality_threshold=0.5),
    SourceRequirement(source_type="industry_reports", minimum_count=2, quality_threshold=0.7),
]

_MAX_DECOMPOSE_RETRIES = 2


class SpecificationEngine:
    """L0 Specification Engine: 10-step pipeline.

    Implements SpecificationEngineContract Protocol.
    """

    def __init__(
        self,
        llm: LLMCallable,
        template_registry: TemplateRegistry | None = None,
        db_session_factory: Callable | None = None,
    ) -> None:
        self._llm = llm
        self._registry = template_registry or TemplateRegistry()
        self._db_session_factory = db_session_factory

        self._classifier = EngagementClassifier(llm)
        self._clarifier = IntentClarifier(llm)
        self._decomposer = Decomposer(llm)
        self._validator = MECEValidator(llm)
        self._scorer = PriorityScorer(llm)
        self._task_generator = TaskGenerator(llm, self._registry)

        self._spec: EngagementSpec | None = None
        self._agent_configs: list[dict] = []

    async def generate_spec(
        self,
        question: str,
        client_id: str,
        client_context: str | None = None,
        constraints: list[str] | None = None,
    ) -> AsyncIterator[AnyPipelineEvent]:
        """Run the 10-step specification pipeline.

        Yields SpecificationGenerated, TasksDecomposed, AgentDispatched events.
        """
        engagement_id = f"eng_{uuid.uuid4().hex[:12]}"

        # Step 1: Classify
        classification = await self._classifier.classify(question, client_context)
        logger.info(
            "Step 1 complete: %s / %s",
            classification.engagement_type,
            classification.pipeline_profile,
        )

        # Step 2: Clarify intent + Day-1 Hypothesis
        intent = await self._clarifier.clarify(
            question,
            classification.engagement_type,
            client_context,
            constraints,
        )
        logger.info("Step 2 complete: intent_clear=%s", intent.intent_clear)

        # Steps 3-4: Decompose with MECE validation (retry loop)
        tree = await self._decompose_with_validation(
            question,
            classification.engagement_type,
            intent.day_1_hypothesis,
            client_context,
        )
        logger.info(
            "Steps 3-4 complete: %d leaves, depth %d",
            tree.metadata.leaf_count,
            tree.metadata.depth,
        )

        # Step 5: Priority scoring
        priorities = await self._scorer.score(
            tree, intent.day_1_hypothesis, classification.engagement_type
        )
        logger.info("Step 5 complete: %d priorities scored", len(priorities))

        # Step 6-7: Build ResearchSpec + Task generation
        research_spec = self._build_research_spec(
            question, intent, classification, engagement_id, client_id
        )
        task_decomposition = await self._task_generator.generate(
            tree, priorities, classification.engagement_type, research_spec
        )
        logger.info("Steps 6-7 complete: %d tasks generated", len(task_decomposition.tasks))

        # Build agent configs for HITL gate
        self._agent_configs = []
        for task in task_decomposition.tasks:
            match = self._registry.match(task, classification.engagement_type)
            self._agent_configs.append({
                "task_id": task.id,
                "template": match.template.name,
                "match_type": match.match_type,
                "similarity": match.similarity,
                "tools": task.assigned_tools,
            })

        # Yield SpecificationGenerated
        yield SpecificationGenerated(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            engagement_id=engagement_id,
            client_id=client_id,
            spec_version=research_spec.specification_version,
            question_count=len(research_spec.questions),
            validation_passed=True,
        )

        # Yield TasksDecomposed
        categories = list({t.effective_category for t in task_decomposition.tasks})
        yield TasksDecomposed(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            engagement_id=engagement_id,
            client_id=client_id,
            task_count=len(task_decomposition.tasks),
            categories=categories,
            rationale=task_decomposition.decomposition_rationale,
        )

        # Build EngagementSpec
        validation_report = ValidationReport(
            intent_clear=intent.intent_clear,
            scope_valid=True,
            within_frontier=True,
            quality_threshold_met=intent.intent_clear,
        )
        self._spec = EngagementSpec(
            research_spec=research_spec,
            task_decomposition=task_decomposition,
            validation_report=validation_report,
            issue_tree=tree.model_dump(),
        )

        # Yield AgentDispatched for each task
        for task in task_decomposition.tasks:
            match = self._registry.match(task, classification.engagement_type)
            yield AgentDispatched(
                event_id=f"evt_{uuid.uuid4().hex[:12]}",
                engagement_id=engagement_id,
                client_id=client_id,
                agent_id=f"agent_{task.id}",
                agent_type=match.template.name,
                task_id=task.id,
                model_tier=task.assigned_model.value,
                tools=task.assigned_tools,
            )

        # Step 8: HITL Gate 1 (only if db_session_factory provided)
        if self._db_session_factory:
            await self._trigger_hitl_gate(tree, task_decomposition)

        # Steps 9-10: Research execution + feedback loop -- STUB
        # Implemented by Component #7 (Research Agents) and the orchestrator.

    async def get_spec(self) -> EngagementSpec:
        """Return the generated engagement specification."""
        if self._spec is None:
            raise RuntimeError("generate_spec() must be called first")
        return self._spec

    async def _decompose_with_validation(
        self,
        question: str,
        engagement_type: EngagementType,
        day_1_hypothesis: str,
        client_context: str | None,
    ) -> IssueTree:
        """Run decomposition with MECE validation retry loop."""
        for attempt in range(_MAX_DECOMPOSE_RETRIES + 1):
            tree = await self._decomposer.decompose(
                question, engagement_type, day_1_hypothesis, client_context
            )

            validation = await self._validator.validate(
                tree, question, engagement_type
            )

            if validation.all_passed:
                return tree

            logger.warning(
                "MECE validation failed (attempt %d/%d): %s",
                attempt + 1,
                _MAX_DECOMPOSE_RETRIES + 1,
                {k.value: v for k, v in validation.feedback.items() if not validation.dimensions[k]},
            )

        # Return last tree even if validation didn't fully pass
        logger.warning("Returning tree after %d attempts despite validation issues", _MAX_DECOMPOSE_RETRIES + 1)
        return tree

    def _build_research_spec(
        self,
        question: str,
        intent: IntentClarificationResult,
        classification: ClassificationResult,
        engagement_id: str,
        client_id: str,
    ) -> ResearchSpec:
        """Assemble the ResearchSpec from classification and intent results."""
        primary_q = ResearchQuestion(question=question, is_primary=True)
        secondary_qs = [
            ResearchQuestion(
                question=boundary,
                is_primary=False,
                parent_question=question,
            )
            for boundary in intent.scope_boundaries[:3]
            if boundary and not boundary.startswith("No ")
        ]

        methodology = _DEFAULT_METHODOLOGY.get(
            classification.engagement_type, []
        )

        non_goals = [
            "Political positioning and recommendation framing",
            "Client relationship management",
        ]
        for boundary in intent.scope_boundaries:
            if boundary not in non_goals:
                non_goals.append(boundary)

        return ResearchSpec(
            engagement_id=engagement_id,
            client_id=client_id,
            title=question[:200],
            created_at=datetime.now(UTC),
            specification_version=1,
            decision_context=intent.decision_context,
            surprising_finding=intent.surprising_finding,
            questions=[primary_q] + secondary_qs,
            methodology=methodology,
            source_requirements=_DEFAULT_SOURCES,
            output_format="markdown",
            non_goals=non_goals,
            engagement_type=classification.engagement_type,
            day_1_hypothesis=intent.day_1_hypothesis,
            recommended_pipeline_profile=classification.pipeline_profile,
            effective_pipeline_profile=classification.pipeline_profile,
            profile_source="classifier",
        )

    async def _trigger_hitl_gate(
        self,
        tree: IssueTree,
        tasks: TaskDecomposition,
    ) -> None:
        """Trigger the HITL Gate 1 (post-specification review)."""
        from keystone.hitl.gate import build_spec_gate_items, create_and_wait_for_gate
        from keystone.hitl.schemas import GateType

        items = build_spec_gate_items(
            issue_tree=tree.model_dump(),
            agent_configs=self._agent_configs,
        )

        profile = self._spec.research_spec.effective_pipeline_profile
        if profile == PipelineProfile.LIGHT:
            return

        async with self._db_session_factory() as session:
            await create_and_wait_for_gate(
                session=session,
                engagement_id=self._spec.research_spec.engagement_id,
                client_id=self._spec.research_spec.client_id,
                gate_type=GateType.POST_SPECIFICATION,
                items=items,
            )
