"""Step 5: Heuristic priority scoring for issue tree branches.

Phase 1 uses a simplified formula:
    priority_score = decision_relevance x uncertainty_reduction

Phase 2 adds: / estimated_cost (full VOI formula per Directive 13).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from keystone.evaluator.retry import LLMCallable, retry_llm_call
from keystone.models.research import EngagementType
from keystone.specification._prompts import extract_json, load_prompt
from keystone.specification.decomposer import IssueTree, IssueTreeNode


class PriorityScore(BaseModel):
    """Priority score for a single issue tree leaf node."""

    branch_id: str
    decision_relevance: float = Field(ge=0.0, le=1.0)
    uncertainty_reduction: float = Field(ge=0.0, le=1.0)
    priority_score: float = Field(ge=0.0, le=1.0)
    reasoning: str


def _collect_leaves(node: IssueTreeNode) -> list[IssueTreeNode]:
    """Collect all leaf nodes from a tree."""
    if not node.children:
        return [node]
    leaves: list[IssueTreeNode] = []
    for child in node.children:
        leaves.extend(_collect_leaves(child))
    return leaves


class PriorityScorer:
    """Score issue tree leaf nodes by decision relevance and uncertainty reduction.

    Phase 1 formula: priority_score = decision_relevance x uncertainty_reduction
    """

    def __init__(self, llm: LLMCallable) -> None:
        self._llm = llm

    async def score(
        self,
        tree: IssueTree,
        day_1_hypothesis: str,
        engagement_type: EngagementType,
    ) -> list[PriorityScore]:
        """Score each leaf node of the issue tree."""
        import json

        leaves = _collect_leaves(tree.root)
        leaves_json = json.dumps(
            [{"id": l.id, "name": l.name, "description": l.description} for l in leaves],
            indent=2,
        )

        prompt = load_prompt(
            "priority_scoring",
            day_1_hypothesis=day_1_hypothesis,
            engagement_type=engagement_type.value,
            leaves=leaves_json,
        )

        raw = await retry_llm_call(
            self._llm, prompt, description="priority_scoring"
        )
        data = extract_json(raw)

        scores_raw = data.get("scores", data if isinstance(data, list) else [])
        if isinstance(scores_raw, dict):
            scores_raw = scores_raw.get("scores", [])

        scores: list[PriorityScore] = []
        for entry in scores_raw:
            dr = float(entry["decision_relevance"])
            ur = float(entry["uncertainty_reduction"])
            scores.append(
                PriorityScore(
                    branch_id=entry["branch_id"],
                    decision_relevance=dr,
                    uncertainty_reduction=ur,
                    priority_score=round(dr * ur, 4),
                    reasoning=entry.get("reasoning", ""),
                )
            )

        return scores
