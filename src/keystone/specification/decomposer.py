"""Step 3: MECE issue tree decomposition with dynamic analytical lenses.

The core intellectual engine of the Specification Engine. Standard-tier
agents independently construct issue trees from selected analytical
perspectives, then a flagship-tier meta-agent synthesizes them into a unified
tree.

Implements Directive 2 (MECE Issue Tree Decomposition) and
Directive 12 (Principles Over Example Libraries).
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from keystone.evaluator.retry import LLMCallable, retry_llm_call
from keystone.specification._prompts import extract_json, load_prompt
from keystone.specification.lens_selector import LensDefinition, LensSelector

if TYPE_CHECKING:
    from keystone.models.research import EngagementType

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
    lenses_used: list[str] = Field(description="Analytical lenses used in construction")
    synthesis_rationale: str = Field(description="Why the synthesis chose this structure")


class IssueTree(BaseModel):
    """Complete MECE issue tree with metadata."""

    root: IssueTreeNode
    metadata: IssueTreeMetadata


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
    1. Select 2-5 request-appropriate lenses and spawn parallel STANDARD-tier
       agents. Lens decompositions benefit from parallelism more than raw
       reasoning depth.
    2. Each produces an independent shallow tree (2-3 levels)
    3. FLAGSHIP meta-agent synthesizes into unified tree. The synthesis step
       is the real reasoning work and keeps the strongest model.

    Callers may pass ``lens_llm`` and ``synth_llm`` as distinct callables
    to honor the tier split. Legacy single-LLM callers pass ``llm`` and
    both phases use it.
    """

    def __init__(
        self,
        llm: LLMCallable | None = None,
        *,
        lens_llm: LLMCallable | None = None,
        synth_llm: LLMCallable | None = None,
        lens_selector: LensSelector | None = None,
    ) -> None:
        if lens_llm is None and synth_llm is None and llm is None:
            raise ValueError(
                "Decomposer requires at least one LLM (pass 'llm', or both "
                "'lens_llm' and 'synth_llm')."
            )
        resolved_lens = lens_llm if lens_llm is not None else llm
        resolved_synth = synth_llm if synth_llm is not None else llm
        if resolved_lens is None or resolved_synth is None:
            raise ValueError(
                "Decomposer requires both lens and synthesis LLMs; fall back "
                "to the legacy 'llm' kwarg to share one callable across both."
            )
        self._lens_llm = resolved_lens
        self._synth_llm = resolved_synth
        self._lens_selector = lens_selector or LensSelector()

    async def decompose(
        self,
        question: str,
        engagement_type: EngagementType,
        day_1_hypothesis: str,
        client_context: str | None = None,
        *,
        domain: str | None = None,
        decision_context: str | None = None,
        output_target: str | None = None,
    ) -> IssueTree:
        """Produce a unified MECE issue tree from selected lens perspectives."""
        selection = self._lens_selector.select(
            question=question,
            engagement_type=engagement_type,
            domain=domain,
            decision_context=decision_context,
            output_target=output_target,
            client_context=client_context,
        )

        # Phase 1: Parallel lens decompositions
        raw_lens_trees = await asyncio.gather(
            *[
                self._run_lens(lens, question, engagement_type, day_1_hypothesis, client_context)
                for lens in selection.lenses
            ]
        )
        lens_trees = list(zip(selection.lenses, raw_lens_trees, strict=True))

        # Phase 2: Synthesis
        return await self._synthesize(question, engagement_type, day_1_hypothesis, lens_trees)

    async def _run_lens(
        self,
        lens: LensDefinition,
        question: str,
        engagement_type: EngagementType,
        day_1_hypothesis: str,
        client_context: str | None,
    ) -> dict:
        """Run a single lens decomposition and return raw JSON."""
        context = _lens_context(lens, client_context)
        prompt = load_prompt(
            f"decompose_{lens.prompt_family}_lens",
            question=question,
            engagement_type=engagement_type.value,
            day_1_hypothesis=day_1_hypothesis,
            client_context=context,
        )

        raw = await retry_llm_call(
            self._lens_llm,
            prompt,
            description=f"decompose_{lens.lens_id}_lens",
        )
        return extract_json(raw)

    async def _synthesize(
        self,
        question: str,
        engagement_type: EngagementType,
        day_1_hypothesis: str,
        lens_trees: list[tuple[LensDefinition, dict]],
    ) -> IssueTree:
        """Synthesize selected lens trees into one unified tree."""
        lens_payloads = [
            {
                "lens_id": lens.lens_id,
                "label": lens.label,
                "prompt_family": lens.prompt_family,
                "rationale": lens.rationale,
                "tree": tree,
            }
            for lens, tree in lens_trees
        ]
        prompt = load_prompt(
            "decompose_synthesis",
            question=question,
            engagement_type=engagement_type.value,
            day_1_hypothesis=day_1_hypothesis,
            lens_trees=json.dumps(lens_payloads, indent=2),
            lenses_used=", ".join(lens.label for lens, _tree in lens_trees),
        )

        raw = await retry_llm_call(self._synth_llm, prompt, description="decompose_synthesis")
        data = extract_json(raw)

        root_data = data.get("root", data.get("tree", data))
        root = _parse_tree_nodes(root_data)

        leaf_count = _count_leaves(root)
        depth = _max_depth(root)

        metadata = IssueTreeMetadata(
            depth=depth,
            leaf_count=leaf_count,
            lenses_used=[lens.lens_id for lens, _tree in lens_trees],
            synthesis_rationale=data.get(
                "synthesis_rationale",
                "Unified tree synthesized from selected dynamic lenses.",
            ),
        )

        return IssueTree(root=root, metadata=metadata)


def _lens_context(lens: LensDefinition, client_context: str | None) -> str:
    base_context = client_context or "No additional context provided."
    return (
        "Dynamic lens directive:\n"
        f"- Selected lens id: {lens.lens_id}\n"
        f"- Selected lens label: {lens.label}\n"
        f"- Lens description: {lens.description}\n"
        f"- Selection rationale: {lens.rationale}\n"
        "- Adapt the host prompt to this selected lens. Keep the output schema unchanged.\n\n"
        f"Client context:\n{base_context}"
    )
