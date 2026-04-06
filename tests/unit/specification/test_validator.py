"""Tests for the MECE validator (Step 4)."""

from __future__ import annotations

import json

from keystone.models.research import EngagementType
from keystone.specification.decomposer import IssueTree, IssueTreeMetadata, IssueTreeNode
from keystone.specification.validator import (
    MECEValidationResult,
    MECEValidator,
    ValidationDimension,
)


def _make_tree(leaf_count: int = 12, depth: int = 2) -> IssueTree:
    """Create a test tree with the given parameters."""
    children = []
    leaves_per_branch = max(1, leaf_count // 3)
    for i in range(1, 4):
        branch_children = []
        for j in range(1, leaves_per_branch + 1):
            branch_children.append(
                IssueTreeNode(
                    id=f"branch_{i}.{j}",
                    name=f"Sub-topic {i}.{j}",
                    description=f"Investigate sub-topic {i}.{j}",
                )
            )
        children.append(
            IssueTreeNode(
                id=f"branch_{i}",
                name=f"Major Branch {i}",
                description=f"Top-level branch {i}",
                children=branch_children,
            )
        )
    return IssueTree(
        root=IssueTreeNode(
            id="root",
            name="Root",
            description="Root node",
            children=children,
        ),
        metadata=IssueTreeMetadata(
            depth=depth,
            leaf_count=leaf_count,
            lenses_used=["financial", "operational", "market"],
            synthesis_rationale="Test synthesis.",
        ),
    )


def _make_llm(all_pass: bool = True, fail_dimensions: list[str] | None = None):
    fail_dims = fail_dimensions or []

    async def llm(prompt: str) -> str:
        dimensions = {}
        feedback = {}
        for dim in ValidationDimension:
            if all_pass and dim.value not in fail_dims:
                dimensions[dim.value] = True
                feedback[dim.value] = "Passes."
            elif dim.value in fail_dims:
                dimensions[dim.value] = False
                feedback[dim.value] = f"Failed: {dim.value} issue detected."
            else:
                dimensions[dim.value] = True
                feedback[dim.value] = "Passes."
        return json.dumps({"dimensions": dimensions, "feedback": feedback})

    return llm


class TestMECEValidator:

    async def test_valid_tree_passes_all(self):
        llm = _make_llm(all_pass=True)
        validator = MECEValidator(llm)
        tree = _make_tree()
        result = await validator.validate(tree, "Test question", EngagementType.EVALUATIVE)
        assert result.all_passed is True
        assert result.regeneration_needed is False
        assert isinstance(result, MECEValidationResult)

    async def test_overlapping_branches_fail_me(self):
        llm = _make_llm(fail_dimensions=["mutual_exclusivity"])
        validator = MECEValidator(llm)
        tree = _make_tree()
        result = await validator.validate(tree, "Test question", EngagementType.EVALUATIVE)
        assert result.dimensions[ValidationDimension.MUTUAL_EXCLUSIVITY] is False
        assert result.all_passed is False
        assert result.regeneration_needed is True

    async def test_overdecomposed_tree_fails_depth(self):
        llm = _make_llm(fail_dimensions=["depth_appropriateness"])
        validator = MECEValidator(llm)
        tree = _make_tree(leaf_count=40, depth=4)
        result = await validator.validate(tree, "Test question", EngagementType.SIZING)
        assert result.dimensions[ValidationDimension.DEPTH_APPROPRIATENESS] is False
        assert result.regeneration_needed is True

    async def test_empty_tree_fails_ce(self):
        llm = _make_llm(fail_dimensions=["collective_exhaustiveness"])
        validator = MECEValidator(llm)
        tree = _make_tree(leaf_count=2, depth=1)
        result = await validator.validate(tree, "Test question", EngagementType.DIAGNOSTIC)
        assert result.dimensions[ValidationDimension.COLLECTIVE_EXHAUSTIVENESS] is False

    async def test_all_dimensions_present(self):
        llm = _make_llm(all_pass=True)
        validator = MECEValidator(llm)
        tree = _make_tree()
        result = await validator.validate(tree, "Test question", EngagementType.STRATEGIC)
        for dim in ValidationDimension:
            assert dim in result.dimensions
            assert dim in result.feedback

    async def test_multiple_failures(self):
        llm = _make_llm(fail_dimensions=["tailoring", "actionability"])
        validator = MECEValidator(llm)
        tree = _make_tree()
        result = await validator.validate(tree, "Test question", EngagementType.EXPLORATORY)
        assert result.dimensions[ValidationDimension.TAILORING] is False
        assert result.dimensions[ValidationDimension.ACTIONABILITY] is False
        assert result.all_passed is False
