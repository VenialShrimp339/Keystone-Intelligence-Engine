"""Research Agent Pipeline for the Keystone Intelligence Engine.

Component #7: L1 parallel research agents. Takes tasks from the
Specification Engine, executes iterative research via MCP tools,
and produces StructuredFindings for the CitationProcessor.
"""

from keystone.research.agent_pool import AgentPool, AgentResult
from keystone.research.context_loader import ContextLoader
from keystone.research.error_recovery import (
    ErrorCategory,
    ErrorRecovery,
    classify_error,
)
from keystone.research.evidence_context import (
    EvidenceContextProvider,
    TaskFilter,
    evidence_to_citation,
    infer_source_type,
)
from keystone.research.finding_writer import FindingValidationError, FindingWriter
from keystone.research.isolation import AgentWorkspace, IsolationManager
from keystone.research.research_agent import ResearchAgent
from keystone.research.task_claimer import TaskClaimError, TaskClaimer

__all__ = [
    "AgentPool",
    "AgentResult",
    "AgentWorkspace",
    "ContextLoader",
    "ErrorCategory",
    "ErrorRecovery",
    "EvidenceContextProvider",
    "FindingValidationError",
    "FindingWriter",
    "IsolationManager",
    "ResearchAgent",
    "TaskClaimError",
    "TaskClaimer",
    "TaskFilter",
    "classify_error",
    "evidence_to_citation",
    "infer_source_type",
]
