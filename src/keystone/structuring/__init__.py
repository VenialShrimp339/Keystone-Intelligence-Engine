"""Pipeline-L2 Content Structuring.

Transforms a ConfidenceMap + list[StructuredFinding] into:

1. a `StructuredOutline` that the renderer traverses in consulting order
2. per-task section text that the L4 Evaluator scores
3. per-task `SprintContract`s negotiated for the L4 rubric

L2 sits between L1.5 (Deliberation) and L4 (Evaluator). It is pure Python
plus one LLM call per task (for sprint contract generation, delegated to
`SprintContractGenerator`). No other external I/O.
"""

from keystone.structuring.content_structuring import (
    ContentStructurer,
    filter_outline_by_passed_tasks,
)
from keystone.structuring.framework_selector import (
    frameworks_for_engagement,
    primary_framework,
)

__all__ = [
    "ContentStructurer",
    "filter_outline_by_passed_tasks",
    "frameworks_for_engagement",
    "primary_framework",
]
