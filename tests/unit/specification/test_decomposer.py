"""Tests for the decomposer (Step 3)."""

from __future__ import annotations

import json

from keystone.models.research import EngagementType
from keystone.specification.decomposer import (
    Decomposer,
    IssueTree,
    IssueTreeNode,
    _count_leaves,
    _max_depth,
)


def _make_lens_tree(prefix: str, leaf_count: int = 4) -> dict:
    """Create a mock lens tree with the given prefix and leaf count."""
    children = []
    for i in range(1, leaf_count + 1):
        children.append(
            {
                "id": f"{prefix}_{i}",
                "name": f"{prefix.title()} Branch {i}",
                "description": f"Investigate {prefix} aspect {i}",
                "children": [],
            }
        )
    return {
        "id": f"{prefix}_root",
        "name": f"{prefix.title()} Analysis",
        "description": f"{prefix.title()} lens decomposition",
        "children": children,
    }


def _make_synthesized_tree(leaf_count: int = 12) -> dict:
    """Create a mock synthesized tree."""
    branches = []
    leaves_per_branch = max(1, leaf_count // 3)
    for i in range(1, 4):
        children = []
        for j in range(1, leaves_per_branch + 1):
            children.append(
                {
                    "id": f"branch_{i}.{j}",
                    "name": f"Sub-topic {i}.{j}",
                    "description": f"Investigate sub-topic {i}.{j}",
                    "lens_annotations": {"financial": "Financial aspect"} if j == 1 else {},
                    "children": [],
                }
            )
        branches.append(
            {
                "id": f"branch_{i}",
                "name": f"Major Branch {i}",
                "description": f"Top-level branch {i}",
                "lens_annotations": {"financial": "Revenue", "market": "Competition"},
                "children": children,
            }
        )
    return {
        "root": {
            "id": "root",
            "name": "Research question decomposition",
            "description": "Unified MECE tree",
            "children": branches,
        },
        "synthesis_rationale": (
            "Merged financial and market perspectives, added operational insights."
        ),
    }


class TestDecomposer:
    async def test_produces_valid_tree(self):
        call_count = 0

        async def llm(prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            # First 3 calls are lens trees, 4th is synthesis
            if call_count <= 3:
                prefix = ["fin", "ops", "mkt"][call_count - 1]
                return json.dumps(_make_lens_tree(prefix))
            return json.dumps(_make_synthesized_tree())

        decomposer = Decomposer(llm)
        tree = await decomposer.decompose(
            "Evaluate Luminar's competitive position",
            EngagementType.EVALUATIVE,
            "Luminar's technology lead is sustainable through 2028",
        )

        assert isinstance(tree, IssueTree)
        assert tree.root.id == "root"
        assert len(tree.root.children) == 3

    async def test_tree_depth_2_to_3(self):
        call_count = 0

        async def llm(prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                return json.dumps(_make_lens_tree(f"lens_{call_count}"))
            return json.dumps(_make_synthesized_tree())

        decomposer = Decomposer(llm)
        tree = await decomposer.decompose(
            "Test question",
            EngagementType.SIZING,
            "Test hypothesis",
        )

        assert 2 <= tree.metadata.depth <= 3

    async def test_leaf_count_8_to_20(self):
        call_count = 0

        async def llm(prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                return json.dumps(_make_lens_tree(f"lens_{call_count}"))
            return json.dumps(_make_synthesized_tree(leaf_count=12))

        decomposer = Decomposer(llm)
        tree = await decomposer.decompose(
            "Test question",
            EngagementType.EVALUATIVE,
            "Test hypothesis",
        )

        assert 8 <= tree.metadata.leaf_count <= 20

    async def test_selected_lenses_recorded(self):
        call_count = 0

        async def llm(prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                return json.dumps(_make_lens_tree(f"lens_{call_count}"))
            return json.dumps(_make_synthesized_tree())

        decomposer = Decomposer(llm)
        tree = await decomposer.decompose(
            "Test question",
            EngagementType.STRATEGIC,
            "Test hypothesis",
        )

        assert 2 <= len(tree.metadata.lenses_used) <= 5
        assert tree.metadata.lenses_used != ["financial", "operational", "market"]

    async def test_dynamic_lenses_handle_technical_domain(self):
        call_count = 0

        async def llm(prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            if "Dynamic lens directive:" in prompt:
                return json.dumps(_make_lens_tree(f"lens_{call_count}"))
            return json.dumps(_make_synthesized_tree())

        decomposer = Decomposer(llm)
        tree = await decomposer.decompose(
            "Evaluate a secure plugin runtime architecture for browser automation",
            EngagementType.DESIGN,
            "A plugin runtime can be made secure without losing automation capability",
            domain="technical_architecture",
            decision_context="Choose an internal tool architecture",
            output_target="architecture memo",
        )

        assert "technical_architecture" in tree.metadata.lenses_used
        assert "risk_security" in tree.metadata.lenses_used
        assert tree.metadata.lenses_used != ["financial", "operational", "market"]

    async def test_tree_validates_as_json(self):
        call_count = 0

        async def llm(prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                return json.dumps(_make_lens_tree(f"lens_{call_count}"))
            return json.dumps(_make_synthesized_tree())

        decomposer = Decomposer(llm)
        tree = await decomposer.decompose(
            "Test question",
            EngagementType.EVALUATIVE,
            "Test hypothesis",
        )

        # Should serialize to valid JSON via Pydantic
        tree_dict = tree.model_dump()
        assert "root" in tree_dict
        assert "metadata" in tree_dict
        json.dumps(tree_dict)  # Should not raise


class TestTreeHelpers:
    def test_count_leaves_simple(self):
        node = IssueTreeNode(
            id="root",
            name="Root",
            description="Root",
            children=[
                IssueTreeNode(id="a", name="A", description="A"),
                IssueTreeNode(id="b", name="B", description="B"),
            ],
        )
        assert _count_leaves(node) == 2

    def test_count_leaves_nested(self):
        node = IssueTreeNode(
            id="root",
            name="Root",
            description="Root",
            children=[
                IssueTreeNode(
                    id="a",
                    name="A",
                    description="A",
                    children=[
                        IssueTreeNode(id="a1", name="A1", description="A1"),
                        IssueTreeNode(id="a2", name="A2", description="A2"),
                    ],
                ),
                IssueTreeNode(id="b", name="B", description="B"),
            ],
        )
        assert _count_leaves(node) == 3

    def test_max_depth_flat(self):
        node = IssueTreeNode(
            id="root",
            name="Root",
            description="Root",
            children=[
                IssueTreeNode(id="a", name="A", description="A"),
            ],
        )
        assert _max_depth(node) == 1

    def test_max_depth_nested(self):
        node = IssueTreeNode(
            id="root",
            name="Root",
            description="Root",
            children=[
                IssueTreeNode(
                    id="a",
                    name="A",
                    description="A",
                    children=[
                        IssueTreeNode(id="a1", name="A1", description="A1"),
                    ],
                ),
            ],
        )
        assert _max_depth(node) == 2

    def test_single_leaf(self):
        node = IssueTreeNode(id="leaf", name="Leaf", description="Leaf")
        assert _count_leaves(node) == 1
        assert _max_depth(node) == 0
