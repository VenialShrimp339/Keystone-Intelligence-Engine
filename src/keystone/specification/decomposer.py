"""Step 3: MECE issue tree decomposition with heterogeneous consulting lenses.

The core intellectual engine of the Specification Engine. Three Sonnet-tier
agents independently construct issue trees from different analytical
perspectives (financial, operational, market/competitive), then an Opus-tier
meta-agent synthesizes them into a unified tree.

Implements Directive 2 (MECE Issue Tree Decomposition) and
Directive 12 (Principles Over Example Libraries).
"""

from __future__ import annotations

import asyncio
import json
import logging

from pydantic import BaseModel, Field

from keystone.evaluator.retry import LLMCallable, retry_llm_call
from keystone.models.research import EngagementType
from keystone.specification._prompts import extract_json, load_prompt

logger = logging.getLogger(__name__)


class IssueTreeNode(BaseModel):
    """A single node in the MECE issue tree."""

    id: str
    name: str
    description: str
    children: list[IssueTreeNode] = Field(default_factory=list)
    lens_annotations: dict[str, str] = Field(
        default_factory=dict,
        description="Which lens contributed what insight to this node",
    )


class IssueTreeMetadata(BaseModel):
    """Metadata about the constructed issue tree."""

    depth: int = Field(description="Maximum tree depth (target: 2-3)")
    leaf_count: int = Field(description="Number of leaf nodes (target: 8-20)")
    lenses_used: list[str] = Field(
        description="Analytical lenses used in construction"
    )
    synthesis_rationale: str = Field(
        description="Why the synthesis chose this structure"
    )


class IssueTree(BaseModel):
    """Complete MECE issue tree with metadata."""

    root: IssueTreeNode
    metadata: IssueTreeMetadata


_LENSES = ["financial", "operational", "market"]


def _count_leaves(node: IssueTreeNode) -> int:
    """Count leaf nodes in the tree."""
    if not node.children:
        return 1
    return sum(_count_leaves(c) for c in node.children)


def _max_depth(node: IssueTreeNode, current: int = 0) -> int:
    """Compute maximum depth of the tree."""
    if not node.children:
        return current
    return max(_max_depth(c, current + 1) for c in node.children)


def _parse_tree_nodes(data: dict | list) -> IssueTreeNode:
    """Parse an LLM-produced tree structure into IssueTreeNode."""
    if isinstance(data, list):
        # Wrap a list of branches under a synthetic root
        children = [_parse_tree_nodes(item) for item in data]
        return IssueTreeNode(
            id="root",
            name="Root",
            description="Synthesized root",
            children=children,
        )

    return IssueTreeNode(
        id=data.get("id", "node"),
        name=data.get("name", ""),
        description=data.get("description", ""),
        children=[_parse_tree_nodes(c) for c in data.get("children", [])],
        lens_annotations=data.get("lens_annotations", {}),
    )


class Decomposer:
    """Construct a MECE issue tree using heterogeneous consulting lenses.

    Three-phase decomposition:
    1. Spawn 3 parallel agents (financial, operational, market/competitive)
    2. Each produces an independent shallow tree (2-3 levels)
    3. Opus meta-agent synthesizes into unified tree
    """

    def __init__(self, llm: LLMCallable) -> None:
        self._llm = llm

    async def decompose(
        self,
        question: str,
        engagement_type: EngagementType,
        day_1_hypothesis: str,
        client_context: str | None = None,
    ) -> IssueTree:
        """Produce a unified MECE issue tree from 3 lens perspectives."""
        # Phase 1: Parallel lens decompositions
        lens_trees = await asyncio.gather(
            *[
                self._run_lens(lens, question, engagement_type, day_1_hypothesis, client_context)
                for lens in _LENSES
            ]
        )

        # Phase 2: Synthesis
        return await self._synthesize(
            question, engagement_type, day_1_hypothesis, lens_trees
        )

    async def _run_lens(
        self,
        lens: str,
        question: str,
        engagement_type: EngagementType,
        day_1_hypothesis: str,
        client_context: str | None,
    ) -> dict:
        """Run a single lens decomposition and return raw JSON."""
        prompt = load_prompt(
            f"decompose_{lens}_lens",
            question=question,
            engagement_type=engagement_type.value,
            day_1_hypothesis=day_1_hypothesis,
            client_context=client_context or "No additional context provided.",
        )

        raw = await retry_llm_call(
            self._llm, prompt, description=f"decompose_{lens}_lens"
        )
        return extract_json(raw)

    async def _synthesize(
        self,
        question: str,
        engagement_type: EngagementType,
        day_1_hypothesis: str,
        lens_trees: list[dict],
    ) -> IssueTree:
        """Synthesize 3 lens trees into one unified tree."""
        prompt = load_prompt(
            "decompose_synthesis",
            question=question,
            engagement_type=engagement_type.value,
            day_1_hypothesis=day_1_hypothesis,
            financial_tree=json.dumps(lens_trees[0], indent=2),
            operational_tree=json.dumps(lens_trees[1], indent=2),
            market_tree=json.dumps(lens_trees[2], indent=2),
        )

        raw = await retry_llm_call(
            self._llm, prompt, description="decompose_synthesis"
        )
        data = extract_json(raw)

        root_data = data.get("root", data.get("tree", data))
        root = _parse_tree_nodes(root_data)

        leaf_count = _count_leaves(root)
        depth = _max_depth(root)

        metadata = IssueTreeMetadata(
            depth=depth,
            leaf_count=leaf_count,
            lenses_used=_LENSES.copy(),
            synthesis_rationale=data.get(
                "synthesis_rationale",
                "Unified tree synthesized from financial, operational, and market lenses.",
            ),
        )

        return IssueTree(root=root, metadata=metadata)
