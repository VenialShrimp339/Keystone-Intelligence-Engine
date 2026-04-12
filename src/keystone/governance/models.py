"""Governance runtime models for Wave 2B enforcement."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

from keystone.models.research import PipelineProfile
from keystone.models.tasks import TaskImportance


class EnforcementAction(StrEnum):
    HALT = "halt"
    ESCALATE = "escalate"
    DEGRADE = "degrade"
    WARN = "warn"


class EnforcementScope(StrEnum):
    TASK = "task"
    PIPELINE = "pipeline"


class ResearchStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED_NO_OUTPUT = "failed_no_output"
    NOT_RUN = "not_run"


class QualityFlag(BaseModel):
    gate: str
    action: EnforcementAction
    scope: EnforcementScope
    severity: Literal["info", "warn", "error", "critical"]
    message: str
    task_id: str | None = None


class TaskOutcome(BaseModel):
    task_id: str
    importance: TaskImportance
    research_status: ResearchStatus
    evaluation_status: Literal["passed", "failed", "not_evaluated"]
    renderable: bool
    flags: list[QualityFlag] = Field(default_factory=list)


class GovernanceState(BaseModel):
    profile: PipelineProfile
    degraded: bool = False
    halted: bool = False
    flags: list[QualityFlag] = Field(default_factory=list)
    task_outcomes: dict[str, TaskOutcome] = Field(default_factory=dict)
