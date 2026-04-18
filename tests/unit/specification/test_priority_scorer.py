"""Tests for the priority scorer (Step 5)."""

from __future__ import annotations

import json

import pytest

from keystone.models.research import EngagementType
from keystone.specification.decomposer import IssueTree, IssueTreeMetadata, IssueTreeNode
from keystone.specification.priority_scorer import PriorityScore, PriorityScorer


def _make_tree() -> IssueTree:
    return IssueTree(
        root=IssueTreeNode(
            id="root",
            name="Root",
            description="Root",
            children=[
                IssueTreeNode(
                    id="branch_1",
                    name="Market Size",
                    description="Estimate TAM",
                    children=[
                        IssueTreeNode(id="branch_1.1", name="L2+ market", description="L2+ TAM"),
                        IssueTreeNode(id="branch_1.2", name="L4+ market", description="L4+ TAM"),
                    ],
                ),
                IssueTreeNode(
                    id="branch_2",
                    name="Competition",
                    description="Competitive landscape",
                    children=[
                        IssueTreeNode(
                            id="branch_2.1",
                            name="Chinese competitors",
                            description="Hesai, RoboSense",
                        ),
                        IssueTreeNode(
                            id="branch_2.2", name="Western competitors", description="Innoviz, Aeva"
                        ),
                    ],
                ),
            ],
        ),
        metadata=IssueTreeMetadata(
            depth=2,
            leaf_count=4,
            lenses_used=["financial", "operational", "market"],
            synthesis_rationale="Test tree.",
        ),
    )


def _make_llm(scores: list[dict] | None = None):
    default_scores = [
        {
            "branch_id": "branch_1.1",
            "decision_relevance": 0.9,
            "uncertainty_reduction": 0.8,
            "reasoning": "Core to TAM estimate.",
        },
        {
            "branch_id": "branch_1.2",
            "decision_relevance": 0.7,
            "uncertainty_reduction": 0.9,
            "reasoning": "High uncertainty in L4+ timeline.",
        },
        {
            "branch_id": "branch_2.1",
            "decision_relevance": 0.8,
            "uncertainty_reduction": 0.7,
            "reasoning": "Chinese competition is key risk.",
        },
        {
            "branch_id": "branch_2.2",
            "decision_relevance": 0.6,
            "uncertainty_reduction": 0.5,
            "reasoning": "Western competitors less threatening.",
        },
    ]

    async def llm(prompt: str) -> str:
        return json.dumps({"scores": scores or default_scores})

    return llm


class TestPriorityScorer:
    async def test_returns_scores_for_all_leaves(self):
        llm = _make_llm()
        scorer = PriorityScorer(llm)
        tree = _make_tree()
        scores = await scorer.score(tree, "Test hypothesis", EngagementType.EVALUATIVE)
        assert len(scores) == 4

    async def test_scores_between_0_and_1(self):
        llm = _make_llm()
        scorer = PriorityScorer(llm)
        tree = _make_tree()
        scores = await scorer.score(tree, "Test hypothesis", EngagementType.SIZING)
        for s in scores:
            assert 0.0 <= s.decision_relevance <= 1.0
            assert 0.0 <= s.uncertainty_reduction <= 1.0
            assert 0.0 <= s.priority_score <= 1.0

    async def test_priority_score_formula(self):
        llm = _make_llm()
        scorer = PriorityScorer(llm)
        tree = _make_tree()
        scores = await scorer.score(tree, "Test hypothesis", EngagementType.STRATEGIC)
        for s in scores:
            expected = round(s.decision_relevance * s.uncertainty_reduction, 4)
            assert s.priority_score == pytest.approx(expected, abs=0.001)

    async def test_result_type(self):
        llm = _make_llm()
        scorer = PriorityScorer(llm)
        tree = _make_tree()
        scores = await scorer.score(tree, "Test hypothesis", EngagementType.DIAGNOSTIC)
        for s in scores:
            assert isinstance(s, PriorityScore)
            assert len(s.branch_id) > 0
