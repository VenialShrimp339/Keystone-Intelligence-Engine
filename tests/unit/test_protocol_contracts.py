"""Protocol contract isinstance verification tests.

Catches signature drift: if a component's method signature doesn't
match its Protocol contract, isinstance() returns False.

Skipped contracts:
- GenerationContract: not implemented (Phase 2)
- ObservationLibraryContract: not implemented (Phase 2)
- HITLGateContract: no wrapping class yet (hitl/ provides functions, not a class)
"""

from __future__ import annotations

import json

import pytest

from keystone.contracts import (
    CitationProcessorContract,
    ContentStructuringContract,
    DeliberationContract,
    EvaluatorContract,
    ResearchAgentContract,
    SpecificationEngineContract,
)


def _mock_llm():
    async def llm(prompt: str) -> str:
        return json.dumps({"score": 0.7})

    return llm


class TestSpecificationEngineContract:
    def test_isinstance(self) -> None:
        from keystone.specification.spec_engine import SpecificationEngine

        engine = SpecificationEngine(llm=_mock_llm())
        assert isinstance(engine, SpecificationEngineContract)


class TestResearchAgentContract:
    def test_isinstance(self) -> None:
        from keystone.gateway import (
            AuditLogger,
            InMemoryRateLimiter,
            MCPGateway,
            MockMCPClient,
            ToolAuthorizer,
            ToolRegistry,
        )
        from keystone.gateway.servers import register_all_tools
        from keystone.research.research_agent import ResearchAgent

        registry = ToolRegistry()
        register_all_tools(registry)
        gateway = MCPGateway(
            registry=registry,
            authorizer=ToolAuthorizer(registry),
            rate_limiter=InMemoryRateLimiter({}),
            audit_logger=AuditLogger(),
            client=MockMCPClient(),
        )
        agent = ResearchAgent(llm=_mock_llm(), gateway=gateway)
        assert isinstance(agent, ResearchAgentContract)


class TestCitationProcessorContract:
    def test_isinstance(self) -> None:
        from keystone.citation.processor import CitationProcessor

        processor = CitationProcessor()
        assert isinstance(processor, CitationProcessorContract)


class TestDeliberationContract:
    def test_isinstance(self) -> None:
        from keystone.deliberation.deliberation import Deliberation

        delib = Deliberation(analyst_llm=_mock_llm())
        assert isinstance(delib, DeliberationContract)


class TestEvaluatorContract:
    def test_isinstance(self) -> None:
        from keystone.evaluator.evaluator import Evaluator

        evaluator = Evaluator(llm=_mock_llm())
        assert isinstance(evaluator, EvaluatorContract)


class TestContentStructuringContract:
    def test_isinstance(self) -> None:
        from keystone.structuring import ContentStructurer

        structurer = ContentStructurer()
        assert isinstance(structurer, ContentStructuringContract)
