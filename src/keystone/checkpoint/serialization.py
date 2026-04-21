"""Checkpoint serialization and deserialization helpers.

Each checkpoint stage has a pair of functions:
  - ``serialize_<stage>(...)`` → ``dict[str, Any]`` (JSON-safe payload)
  - ``deserialize_<stage>(payload)`` → named tuple of restored variables

Event envelopes follow the same ``event.__class__.__name__`` +
``model_dump(mode="json")`` pattern used by ``run_store.py``.
"""

from __future__ import annotations

import logging
from typing import Any, NamedTuple

from keystone.events import (
    # L0
    AgentDispatched,
    AggregationComplete,
    AnalystSpawned,
    AnyPipelineEvent,
    # Retrieval
    ChunkIngested,
    # CitationProcessor
    CitationDeduped,
    CitationExtracted,
    CitationFormatted,
    CitationGateResult,
    ConfidenceMapProduced,
    ConstraintEncoded,
    CorroborationScored,
    DeliverableAssembled,
    DeterministicCheckPassed,
    DissenterVetoTriggered,
    DraftGenerated,
    EnsembleEvaluationComplete,
    EnsembleJudgeScored,
    EvaluationComplete,
    FindingSynthesized,
    # L1.5
    IndependentAnalysisComplete,
    ManifestProduced,
    ObservationRecorded,
    # L2
    OutlineGenerated,
    PatternPromoted,
    ProcessTrajectoryScored,
    ResearchComplete,
    # L1
    ResearchStarted,
    # HITL
    ReviewDecisionSubmitted,
    ReviewGateApproved,
    ReviewGateCreated,
    ReviewGateModified,
    ReviewGateRejected,
    RubricDimensionScored,
    SearchCompleted,
    SectionDrafted,
    SourceFound,
    SpecificationGenerated,
    SprintContractProposed,
    # L3
    TasksDecomposed,
    URLVerified,
)
from keystone.governance.models import GovernanceState
from keystone.models.agents import AgentInstance
from keystone.models.citations import CitationManifest
from keystone.models.confidence import ConfidenceMap
from keystone.models.evaluation import EvaluationResult, SprintContract
from keystone.models.research import EngagementSpec, StructuredFinding
from keystone.models.structuring import StructuredOutline
from keystone.models.tasks import ResearchTask

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------
# Event class registry for deserialization
# -----------------------------------------------------------------------

_ALL_EVENT_CLASSES: list[type[AnyPipelineEvent]] = [
    SpecificationGenerated,
    TasksDecomposed,
    AgentDispatched,
    ResearchStarted,
    SourceFound,
    CitationExtracted,
    FindingSynthesized,
    ResearchComplete,
    CitationDeduped,
    CorroborationScored,
    URLVerified,
    ManifestProduced,
    ChunkIngested,
    SearchCompleted,
    AnalystSpawned,
    IndependentAnalysisComplete,
    AggregationComplete,
    ConfidenceMapProduced,
    OutlineGenerated,
    SectionDrafted,
    SprintContractProposed,
    DraftGenerated,
    CitationFormatted,
    DeliverableAssembled,
    DeterministicCheckPassed,
    CitationGateResult,
    RubricDimensionScored,
    ProcessTrajectoryScored,
    EvaluationComplete,
    EnsembleJudgeScored,
    DissenterVetoTriggered,
    EnsembleEvaluationComplete,
    ObservationRecorded,
    PatternPromoted,
    ConstraintEncoded,
    ReviewGateCreated,
    ReviewDecisionSubmitted,
    ReviewGateApproved,
    ReviewGateModified,
    ReviewGateRejected,
]

_CLASS_ALIASES: dict[str, type] = {}

_CLASS_BY_NAME: dict[str, type] = {cls.__name__: cls for cls in _ALL_EVENT_CLASSES} | _CLASS_ALIASES


# -----------------------------------------------------------------------
# Event serialization
# -----------------------------------------------------------------------


def serialize_events_by_agent(
    events_by_agent: dict[str, list[AnyPipelineEvent]],
) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for agent_id, events in events_by_agent.items():
        serialized: list[dict[str, Any]] = []
        for event in events:
            data = event.model_dump(mode="json")
            data["event_type"] = event.__class__.__name__
            serialized.append(data)
        result[agent_id] = serialized
    return result


def deserialize_events_by_agent(
    data: dict[str, list[dict[str, Any]]],
) -> dict[str, list[AnyPipelineEvent]]:
    result: dict[str, list[AnyPipelineEvent]] = {}
    for agent_id, event_dicts in data.items():
        events: list[AnyPipelineEvent] = []
        for ed in event_dicts:
            event_type = ed.pop("event_type", None)
            if event_type is None:
                logger.warning("Skipping event without event_type for agent %s", agent_id)
                continue
            cls = _CLASS_BY_NAME.get(event_type)
            if cls is None:
                logger.warning("Skipping unknown event type %s for agent %s", event_type, agent_id)
                continue
            try:
                events.append(cls.model_validate(ed))
            except Exception:
                logger.warning(
                    "Failed to deserialize %s event for agent %s",
                    event_type,
                    agent_id,
                    exc_info=True,
                )
        result[agent_id] = events
    return result


# -----------------------------------------------------------------------
# POST_SPEC
# -----------------------------------------------------------------------


def serialize_post_spec(
    spec: EngagementSpec,
    governance: GovernanceState,
) -> dict[str, Any]:
    return {
        "spec": spec.model_dump(mode="json"),
        "governance": governance.model_dump(mode="json"),
    }


class PostSpecData(NamedTuple):
    spec: EngagementSpec
    governance: GovernanceState


def deserialize_post_spec(payload: dict[str, Any]) -> PostSpecData:
    return PostSpecData(
        spec=EngagementSpec.model_validate(payload["spec"]),
        governance=GovernanceState.model_validate(payload["governance"]),
    )


# -----------------------------------------------------------------------
# POST_L1_CITPROC
# -----------------------------------------------------------------------


def serialize_post_l1_citproc(
    findings: list[StructuredFinding],
    manifest: CitationManifest,
    events_by_agent: dict[str, list[AnyPipelineEvent]],
    agent_by_task: dict[str, AgentInstance],
    governance: GovernanceState,
) -> dict[str, Any]:
    return {
        "findings": [f.model_dump(mode="json") for f in findings],
        "manifest": manifest.model_dump(mode="json"),
        "events_by_agent": serialize_events_by_agent(events_by_agent),
        "agent_by_task": {tid: a.model_dump(mode="json") for tid, a in agent_by_task.items()},
        "governance": governance.model_dump(mode="json"),
    }


class PostL1CitprocData(NamedTuple):
    findings: list[StructuredFinding]
    manifest: CitationManifest
    events_by_agent: dict[str, list[AnyPipelineEvent]]
    agent_by_task: dict[str, AgentInstance]
    governance: GovernanceState


def deserialize_post_l1_citproc(payload: dict[str, Any]) -> PostL1CitprocData:
    return PostL1CitprocData(
        findings=[StructuredFinding.model_validate(f) for f in payload["findings"]],
        manifest=CitationManifest.model_validate(payload["manifest"]),
        events_by_agent=deserialize_events_by_agent(payload["events_by_agent"]),
        agent_by_task={
            tid: AgentInstance.model_validate(a) for tid, a in payload["agent_by_task"].items()
        },
        governance=GovernanceState.model_validate(payload["governance"]),
    )


# -----------------------------------------------------------------------
# POST_DELIBERATION
# -----------------------------------------------------------------------


def serialize_post_deliberation(
    confidence_map: ConfidenceMap,
    governance: GovernanceState,
) -> dict[str, Any]:
    return {
        "confidence_map": confidence_map.model_dump(mode="json"),
        "governance": governance.model_dump(mode="json"),
    }


class PostDeliberationData(NamedTuple):
    confidence_map: ConfidenceMap
    governance: GovernanceState


def deserialize_post_deliberation(payload: dict[str, Any]) -> PostDeliberationData:
    return PostDeliberationData(
        confidence_map=ConfidenceMap.model_validate(payload["confidence_map"]),
        governance=GovernanceState.model_validate(payload["governance"]),
    )


# -----------------------------------------------------------------------
# POST_STRUCTURING
# -----------------------------------------------------------------------


def serialize_post_structuring(
    outline: StructuredOutline,
    eval_tasks: list[ResearchTask],
    section_texts: dict[str, str],
    sprint_contracts: dict[str, SprintContract],
    fallback_task_ids: set[str],
    governance: GovernanceState,
) -> dict[str, Any]:
    return {
        "outline": outline.model_dump(mode="json"),
        "eval_tasks": [t.model_dump(mode="json") for t in eval_tasks],
        "section_texts": section_texts,
        "sprint_contracts": {tid: c.model_dump(mode="json") for tid, c in sprint_contracts.items()},
        "fallback_task_ids": sorted(fallback_task_ids),
        "governance": governance.model_dump(mode="json"),
    }


class PostStructuringData(NamedTuple):
    outline: StructuredOutline
    eval_tasks: list[ResearchTask]
    section_texts: dict[str, str]
    sprint_contracts: dict[str, SprintContract]
    fallback_task_ids: set[str]
    governance: GovernanceState


def deserialize_post_structuring(payload: dict[str, Any]) -> PostStructuringData:
    return PostStructuringData(
        outline=StructuredOutline.model_validate(payload["outline"]),
        eval_tasks=[ResearchTask.model_validate(t) for t in payload["eval_tasks"]],
        section_texts=payload["section_texts"],
        sprint_contracts={
            tid: SprintContract.model_validate(c) for tid, c in payload["sprint_contracts"].items()
        },
        fallback_task_ids=set(payload["fallback_task_ids"]),
        governance=GovernanceState.model_validate(payload["governance"]),
    )


# -----------------------------------------------------------------------
# POST_EVALUATION
# -----------------------------------------------------------------------


def serialize_post_evaluation(
    evaluation_results: list[EvaluationResult],
    governance: GovernanceState,
) -> dict[str, Any]:
    return {
        "evaluation_results": [r.model_dump(mode="json") for r in evaluation_results],
        "governance": governance.model_dump(mode="json"),
    }


class PostEvaluationData(NamedTuple):
    evaluation_results: list[EvaluationResult]
    governance: GovernanceState


def deserialize_post_evaluation(payload: dict[str, Any]) -> PostEvaluationData:
    return PostEvaluationData(
        evaluation_results=[
            EvaluationResult.model_validate(r) for r in payload["evaluation_results"]
        ],
        governance=GovernanceState.model_validate(payload["governance"]),
    )
