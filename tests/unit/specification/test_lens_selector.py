from __future__ import annotations

from keystone.models.research import EngagementType
from keystone.specification.lens_selector import LensSelector


def test_business_request_selects_business_relevant_lenses():
    selection = LensSelector().select(
        question="Evaluate a public company's competitive landscape, acquirer, and financials",
        engagement_type=EngagementType.STRATEGIC,
        domain="business_strategy",
        decision_context="Prepare a consulting pitch deck for the CFO.",
        output_target="slide deck",
    )

    lens_ids = {lens.lens_id for lens in selection.lenses}
    assert "market_competitive" in lens_ids
    assert "financial" in lens_ids
    assert 2 <= len(selection.lenses) <= 5


def test_technical_request_selects_architecture_and_risk_lenses():
    selection = LensSelector().select(
        question="Evaluate a secure plugin runtime architecture for browser automation",
        engagement_type=EngagementType.DESIGN,
        domain="technical_architecture",
        decision_context="Decide the implementation architecture for an internal tool.",
        output_target="architecture memo",
    )

    lens_ids = {lens.lens_id for lens in selection.lenses}
    assert "technical_architecture" in lens_ids
    assert "risk_security" in lens_ids
    assert lens_ids != {"financial", "operational", "market"}


def test_scientific_request_selects_evidence_review_lens():
    selection = LensSelector().select(
        question="Synthesize the academic literature on GLP-1 cardiovascular outcomes",
        engagement_type=EngagementType.SYNTHESIS,
        domain="scientific_literature",
        decision_context="Decide whether the evidence base supports deeper diligence.",
        output_target="evidence memo",
    )

    lens_ids = {lens.lens_id for lens in selection.lenses}
    assert "scientific_evidence_review" in lens_ids
    assert "causal_driver_tree" in lens_ids


def test_ambiguous_request_requires_approval_and_clarification():
    selection = LensSelector().select(question="Research this", output_target=None)

    assert selection.approval_required is True
    assert selection.clarifying_questions
    assert 2 <= len(selection.lenses) <= 5
