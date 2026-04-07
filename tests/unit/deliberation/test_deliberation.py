"""End-to-end tests for the Deliberation orchestrator.

Validates: event ordering, contract compliance, HITL gate skip,
HITL gate positive path, confidence map production, and engagement
context propagation.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from keystone.contracts import DeliberationContract
from keystone.deliberation.deliberation import Deliberation
from keystone.events import (
    AggregationComplete,
    AnalystSpawned,
    ConfidenceMapProduced,
    IndependentAnalysisComplete,
)
from keystone.hitl.models import Base
from keystone.hitl.schemas import GateResponse, GateStatus, GateType
from keystone.models.agents import DeliberationAnalystType
from keystone.models.citations import (
    Citation,
    CitationManifest,
    ConfidenceTier,
    SourceType,
)
from keystone.models.confidence import ConfidenceMap
from keystone.models.research import FindingClaim, StructuredFinding


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _cit(cid: str = "CIT-001") -> Citation:
    return Citation(
        citation_id=cid,
        engagement_id="ENG-001",
        client_id="CLT-001",
        url=f"https://example.com/{cid}",
        title=f"Source {cid}",
        source_type=SourceType.REPORT,
        quality_score=0.8,
        access_date=datetime.now(UTC),
    )


def _manifest() -> CitationManifest:
    return CitationManifest(
        manifest_id="MAN-001",
        engagement_id="ENG-001",
        client_id="CLT-001",
        citations=[_cit("CIT-001"), _cit("CIT-002")],
    )


def _finding(
    agent_id: str,
    claims: list[FindingClaim],
    absences: list[str] | None = None,
) -> StructuredFinding:
    return StructuredFinding(
        task_id="TASK-001",
        agent_id=agent_id,
        engagement_id="ENG-001",
        client_id="CLT-001",
        agent_type="quantitative",
        claims=claims,
        absence_report=absences or [],
        sources_consulted=5,
        tokens_consumed=1000,
    )


def _fc(text: str, confidence: float = 0.8) -> FindingClaim:
    return FindingClaim(
        text=text,
        evidence="Supporting evidence",
        citations=[_cit()],
        confidence=confidence,
        confidence_tier=ConfidenceTier.HIGH,
    )


def _mock_llm():
    """Mock LLM that handles all deliberation prompts."""

    async def llm(prompt: str) -> str:
        lower = prompt.lower()
        if "evaluate each claim" in lower:
            return json.dumps([
                {"index": 0, "confidence": 0.85, "source_count": 3, "reasoning": "Strong evidence"},
                {"index": 1, "confidence": 0.45, "source_count": 1, "reasoning": "Weak evidence"},
                {"index": 2, "confidence": 0.70, "source_count": 2, "reasoning": "Moderate support"},
            ])
        if "select the analyst" in lower:
            return json.dumps({"selected_analyst": "ach", "reasoning": "Best evidence"})
        if "contradict" in lower:
            return json.dumps({"contradictions": []})
        if "assumptions" in lower:
            return json.dumps({"assumptions": ["Market stability", "No disruption"]})
        return json.dumps({"score": 0.7})

    return llm


async def _collect_events(delib, manifest, findings, eid="ENG-001", cid="CLT-001"):
    events = []
    async for event in delib.deliberate(manifest, findings, eid, cid):
        events.append(event)
    return events


# ---------------------------------------------------------------------------
# End-to-end pipeline tests
# ---------------------------------------------------------------------------


class TestEndToEnd:
    @pytest.mark.asyncio
    async def test_full_pipeline(self) -> None:
        """Full deliberation produces a valid confidence map."""
        findings = [
            _finding("agent-1", [
                _fc("Market is $50B", 0.85),
                _fc("Growth declining", 0.45),
                _fc("Strong incumbents", 0.7),
            ]),
        ]
        delib = Deliberation(analyst_llm=_mock_llm())
        events = await _collect_events(delib, _manifest(), findings)
        cm = await delib.get_confidence_map()

        assert isinstance(cm, ConfidenceMap)
        assert cm.total_claims == 3
        assert cm.engagement_id == "ENG-001"
        assert cm.client_id == "CLT-001"

    @pytest.mark.asyncio
    async def test_events_in_correct_order(self) -> None:
        """Events: AnalystSpawned* -> IndependentAnalysisComplete* -> AggregationComplete -> ConfidenceMapProduced."""
        findings = [_finding("agent-1", [_fc("Claim", 0.8)])]
        delib = Deliberation(analyst_llm=_mock_llm())
        events = await _collect_events(delib, _manifest(), findings)
        types = [type(e) for e in events]

        # All AnalystSpawned before any IndependentAnalysisComplete
        last_spawned = max(i for i, t in enumerate(types) if t is AnalystSpawned)
        first_complete = min(
            i for i, t in enumerate(types) if t is IndependentAnalysisComplete
        )
        assert last_spawned < first_complete

        # All IndependentAnalysisComplete before AggregationComplete
        last_analysis = max(
            i for i, t in enumerate(types) if t is IndependentAnalysisComplete
        )
        agg_idx = types.index(AggregationComplete)
        assert last_analysis < agg_idx

        # AggregationComplete before ConfidenceMapProduced
        cm_idx = types.index(ConfidenceMapProduced)
        assert agg_idx < cm_idx

    @pytest.mark.asyncio
    async def test_four_analysts_spawned_by_default(self) -> None:
        findings = [_finding("agent-1", [_fc("Claim", 0.8)])]
        delib = Deliberation(analyst_llm=_mock_llm())
        events = await _collect_events(delib, _manifest(), findings)

        spawned = [e for e in events if isinstance(e, AnalystSpawned)]
        assert len(spawned) == 4
        analyst_types = {e.analyst_type for e in spawned}
        assert analyst_types == {"ach", "quantitative", "adversarial", "historical_analogy"}

    @pytest.mark.asyncio
    async def test_custom_analyst_types(self) -> None:
        findings = [_finding("agent-1", [_fc("Claim", 0.8)])]
        delib = Deliberation(
            analyst_llm=_mock_llm(),
            analyst_types=[
                DeliberationAnalystType.ACH,
                DeliberationAnalystType.SCENARIO_PLANNING,
            ],
        )
        events = await _collect_events(delib, _manifest(), findings)

        spawned = [e for e in events if isinstance(e, AnalystSpawned)]
        assert len(spawned) == 2

    @pytest.mark.asyncio
    async def test_confidence_map_produced_event(self) -> None:
        findings = [_finding("agent-1", [_fc("A", 0.8), _fc("B", 0.4)])]
        delib = Deliberation(analyst_llm=_mock_llm())
        events = await _collect_events(delib, _manifest(), findings)

        cm_events = [e for e in events if isinstance(e, ConfidenceMapProduced)]
        assert len(cm_events) == 1
        assert cm_events[0].total_claims == 2
        assert cm_events[0].tiers_populated >= 1


# ---------------------------------------------------------------------------
# HITL Gate tests
# ---------------------------------------------------------------------------


class TestHITLGate:
    @pytest.mark.asyncio
    async def test_gate_skipped_when_no_db(self) -> None:
        """Pipeline completes without HITL gate when db_session_factory=None."""
        findings = [_finding("agent-1", [_fc("Claim", 0.8)])]
        delib = Deliberation(analyst_llm=_mock_llm(), db_session_factory=None)
        events = await _collect_events(delib, _manifest(), findings)

        assert any(isinstance(e, ConfidenceMapProduced) for e in events)

    @pytest.mark.asyncio
    async def test_gate_triggered_with_db_session_factory(self) -> None:
        """HITL Gate 2 fires when db_session_factory is provided (positive path)."""
        # Real in-memory SQLite database
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        # Mock create_and_wait_for_gate to auto-approve
        mock_gate_response = GateResponse(
            id="gate-001",
            engagement_id="ENG-001",
            client_id="CLT-001",
            gate_type=GateType.POST_DELIBERATION,
            status=GateStatus.APPROVED,
            created_at=datetime.now(UTC),
        )
        mock_create_gate = AsyncMock(return_value=mock_gate_response)

        findings = [_finding("agent-1", [_fc("Claim", 0.8)])]
        delib = Deliberation(
            analyst_llm=_mock_llm(),
            db_session_factory=session_factory,
        )

        with patch(
            "keystone.hitl.gate.create_and_wait_for_gate", mock_create_gate
        ):
            events = await _collect_events(delib, _manifest(), findings)

        # Gate was called with correct gate_type
        mock_create_gate.assert_awaited_once()
        assert mock_create_gate.call_args.kwargs["gate_type"] == GateType.POST_DELIBERATION

        # Pipeline still completed normally
        assert any(isinstance(e, ConfidenceMapProduced) for e in events)
        cm = await delib.get_confidence_map()
        assert isinstance(cm, ConfidenceMap)

        await engine.dispose()


# ---------------------------------------------------------------------------
# Contract compliance tests
# ---------------------------------------------------------------------------


class TestContractCompliance:
    def test_satisfies_deliberation_contract(self) -> None:
        delib = Deliberation(analyst_llm=_mock_llm())
        assert isinstance(delib, DeliberationContract)

    @pytest.mark.asyncio
    async def test_get_confidence_map_before_deliberate_raises(self) -> None:
        delib = Deliberation(analyst_llm=_mock_llm())
        with pytest.raises(RuntimeError, match="deliberate.*must be called"):
            await delib.get_confidence_map()


# ---------------------------------------------------------------------------
# Event metadata tests
# ---------------------------------------------------------------------------


class TestEventMetadata:
    @pytest.mark.asyncio
    async def test_events_carry_engagement_context(self) -> None:
        findings = [_finding("agent-1", [_fc("Claim", 0.8)])]
        delib = Deliberation(analyst_llm=_mock_llm())
        events = await _collect_events(
            delib, _manifest(), findings, "ENG-X", "CLT-Y"
        )

        for event in events:
            assert event.engagement_id == "ENG-X"
            assert event.client_id == "CLT-Y"

    @pytest.mark.asyncio
    async def test_analyst_spawned_has_model_tier(self) -> None:
        findings = [_finding("agent-1", [_fc("Claim", 0.8)])]
        delib = Deliberation(analyst_llm=_mock_llm())
        events = await _collect_events(delib, _manifest(), findings)

        spawned = [e for e in events if isinstance(e, AnalystSpawned)]
        for s in spawned:
            assert s.model_tier == "standard"


# ---------------------------------------------------------------------------
# Empty input tests
# ---------------------------------------------------------------------------


class TestEmptyInput:
    @pytest.mark.asyncio
    async def test_empty_findings(self) -> None:
        delib = Deliberation(analyst_llm=_mock_llm())
        events = await _collect_events(delib, _manifest(), [])
        cm = await delib.get_confidence_map()

        assert cm.total_claims == 0
        assert any(isinstance(e, ConfidenceMapProduced) for e in events)

    @pytest.mark.asyncio
    async def test_findings_with_no_claims(self) -> None:
        findings = [_finding("agent-1", [])]
        delib = Deliberation(analyst_llm=_mock_llm())
        events = await _collect_events(delib, _manifest(), findings)
        cm = await delib.get_confidence_map()

        assert cm.total_claims == 0
