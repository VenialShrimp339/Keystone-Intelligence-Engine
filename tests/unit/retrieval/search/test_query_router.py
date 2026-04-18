"""Unit tests for the rule-based query router."""

from __future__ import annotations

import pytest

from keystone.retrieval.search.models import QueryClassification
from keystone.retrieval.search.query_router import RuleBasedQueryRouter


@pytest.fixture
def router() -> RuleBasedQueryRouter:
    return RuleBasedQueryRouter()


class TestRuleBasedQueryRouter:
    async def test_quantitative_currency(self, router: RuleBasedQueryRouter) -> None:
        route = await router.classify("What was Apple's revenue in $383B FY2023?")
        assert route.classification is QueryClassification.QUANTITATIVE
        assert "currency" in route.signals or "metric_term" in route.signals
        assert route.confidence >= 0.6

    async def test_quantitative_percent(self, router: RuleBasedQueryRouter) -> None:
        route = await router.classify("Gross margin 38% growth YoY")
        assert route.classification is QueryClassification.QUANTITATIVE

    async def test_qualitative_explanatory(self, router: RuleBasedQueryRouter) -> None:
        route = await router.classify("Why is Apple's brand loyalty strong?")
        assert route.classification is QueryClassification.QUALITATIVE
        assert "explanatory" in route.signals

    async def test_hybrid_when_both(self, router: RuleBasedQueryRouter) -> None:
        route = await router.classify(
            "Explain why Apple's revenue grew 10% in FY2023 and describe the strategy"
        )
        assert route.classification is QueryClassification.HYBRID
        assert route.confidence == 0.9

    async def test_default_is_qualitative(self, router: RuleBasedQueryRouter) -> None:
        route = await router.classify("Some random unclassifiable string")
        assert route.classification is QueryClassification.QUALITATIVE
        assert route.confidence == 0.5

    async def test_confidence_scaling(self, router: RuleBasedQueryRouter) -> None:
        # One signal (explanatory) -> 0.6
        single = await router.classify("How did they respond?")
        # Two signals (explanatory + qualitative_term) -> 0.9
        multi = await router.classify("Analyze the company's moat and competitive advantage.")
        assert single.confidence == 0.6
        assert multi.confidence == 0.9

    async def test_ticker_pattern(self, router: RuleBasedQueryRouter) -> None:
        route = await router.classify("What is $MSFT's current price?")
        assert route.classification is QueryClassification.QUANTITATIVE
        assert "stock_ticker" in route.signals

    async def test_fiscal_year_only(self, router: RuleBasedQueryRouter) -> None:
        route = await router.classify("FY2024 Q3 performance summary")
        assert route.classification is QueryClassification.QUANTITATIVE

    async def test_empty_query_raises(self, router: RuleBasedQueryRouter) -> None:
        with pytest.raises(ValueError):
            await router.classify("   ")

    async def test_metric_term(self, router: RuleBasedQueryRouter) -> None:
        route = await router.classify("EPS and net income last quarter")
        assert route.classification is QueryClassification.QUANTITATIVE
        assert "metric_term" in route.signals

    async def test_signals_deduplicated(self, router: RuleBasedQueryRouter) -> None:
        route = await router.classify("How did revenue grow?")
        assert len(route.signals) == len(set(route.signals))
