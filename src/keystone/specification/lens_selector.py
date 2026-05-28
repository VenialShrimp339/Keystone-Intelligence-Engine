"""Dynamic analytical lens selection for L0 issue-tree planning."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from keystone.models.research import EngagementType


class LensDefinition(BaseModel):
    """A selected lens plus the existing prompt family used to execute it."""

    model_config = ConfigDict(frozen=True)

    lens_id: str
    label: str
    prompt_family: str = Field(
        description="One of the existing prompt hosts: financial, operational, market."
    )
    description: str
    rationale: str


class LensSelection(BaseModel):
    """Human-reviewable lens plan for one decomposition request."""

    lenses: list[LensDefinition]
    clarifying_questions: list[str] = Field(default_factory=list)
    approval_required: bool = False
    rationale: str


@dataclass(frozen=True)
class _LensCandidate:
    lens_id: str
    label: str
    prompt_family: str
    description: str
    keywords: frozenset[str]


_CATALOG: tuple[_LensCandidate, ...] = (
    _LensCandidate(
        "market_competitive",
        "Market and Competitive",
        "market",
        (
            "External market structure, customer demand, competitors, substitutes, "
            "and industry trends."
        ),
        frozenset(
            {
                "market",
                "industry",
                "competitor",
                "competitive",
                "landscape",
                "customer",
                "segment",
                "share",
                "pricing",
                "growth",
            }
        ),
    ),
    _LensCandidate(
        "financial",
        "Financial",
        "financial",
        "Revenue, costs, margins, cash flow, capital intensity, valuation, and financing risk.",
        frozenset(
            {
                "financial",
                "finance",
                "10-k",
                "filing",
                "margin",
                "revenue",
                "cost",
                "cash",
                "valuation",
                "dcf",
                "model",
                "spreadsheet",
                "ebitda",
            }
        ),
    ),
    _LensCandidate(
        "operational_capability",
        "Operational Capability",
        "operational",
        "Capabilities, workflows, execution capacity, process maturity, and delivery constraints.",
        frozenset(
            {
                "operations",
                "operational",
                "process",
                "workflow",
                "capacity",
                "supply",
                "manufacturing",
                "delivery",
                "implementation",
                "execution",
            }
        ),
    ),
    _LensCandidate(
        "regulatory_legal",
        "Regulatory and Legal",
        "market",
        "Regulatory constraints, legal exposure, compliance requirements, and policy change.",
        frozenset(
            {
                "regulatory",
                "regulation",
                "legal",
                "compliance",
                "policy",
                "law",
                "approval",
                "privacy",
                "antitrust",
            }
        ),
    ),
    _LensCandidate(
        "technical_architecture",
        "Technical Architecture",
        "operational",
        (
            "System design, engineering trade-offs, integration paths, scalability, "
            "and maintainability."
        ),
        frozenset(
            {
                "technical",
                "technology",
                "architecture",
                "software",
                "engineering",
                "system",
                "api",
                "database",
                "model",
                "pipeline",
                "runtime",
                "code",
            }
        ),
    ),
    _LensCandidate(
        "scientific_evidence_review",
        "Scientific Evidence Review",
        "market",
        "Study quality, evidence hierarchy, reproducibility, mechanisms, and unresolved findings.",
        frozenset(
            {
                "scientific",
                "science",
                "literature",
                "academic",
                "study",
                "evidence",
                "trial",
                "clinical",
                "paper",
                "research",
                "meta-analysis",
            }
        ),
    ),
    _LensCandidate(
        "customer_user",
        "Customer and User",
        "market",
        "User needs, adoption behavior, switching costs, willingness to pay, and workflow fit.",
        frozenset(
            {
                "user",
                "customer",
                "buyer",
                "adoption",
                "usage",
                "workflow",
                "retention",
                "churn",
                "satisfaction",
            }
        ),
    ),
    _LensCandidate(
        "risk_security",
        "Risk and Security",
        "operational",
        "Failure modes, operational risk, security exposure, resilience, and downside scenarios.",
        frozenset(
            {
                "risk",
                "security",
                "confidential",
                "privacy",
                "threat",
                "failure",
                "resilience",
                "safety",
                "downside",
                "exposure",
            }
        ),
    ),
    _LensCandidate(
        "temporal_trend",
        "Temporal and Trend",
        "market",
        "How facts, incentives, and constraints change over time across scenarios.",
        frozenset(
            {
                "trend",
                "future",
                "forecast",
                "history",
                "trajectory",
                "outlook",
                "through",
                "by",
                "since",
                "consolidation",
            }
        ),
    ),
    _LensCandidate(
        "stakeholder_incentive",
        "Stakeholder and Incentive",
        "market",
        "Decision-makers, incentives, constraints, bargaining power, and likely reactions.",
        frozenset(
            {
                "stakeholder",
                "partner",
                "supplier",
                "incentive",
                "decision",
                "cfo",
                "buyer",
                "acquirer",
                "management",
                "investor",
            }
        ),
    ),
    _LensCandidate(
        "causal_driver_tree",
        "Causal Driver Tree",
        "operational",
        "Root causes, causal mechanisms, drivers, bottlenecks, and counterfactual explanations.",
        frozenset(
            {
                "why",
                "driver",
                "cause",
                "causal",
                "root",
                "bottleneck",
                "explain",
                "diagnose",
                "factor",
            }
        ),
    ),
    _LensCandidate(
        "comparative_benchmark",
        "Comparative Benchmark",
        "market",
        "Peer comparison, alternative approaches, benchmarks, analogues, and relative performance.",
        frozenset(
            {
                "compare",
                "comparison",
                "benchmark",
                "peer",
                "alternative",
                "versus",
                "vs",
                "relative",
                "best",
                "position",
                "evaluate",
            }
        ),
    ),
)

_DOMAIN_PRIORS: dict[str, dict[str, int]] = {
    "business": {
        "market_competitive": 5,
        "financial": 4,
        "operational_capability": 4,
        "stakeholder_incentive": 2,
        "regulatory_legal": 1,
    },
    "technical": {
        "technical_architecture": 6,
        "risk_security": 4,
        "comparative_benchmark": 3,
        "operational_capability": 2,
    },
    "scientific": {
        "scientific_evidence_review": 6,
        "causal_driver_tree": 4,
        "comparative_benchmark": 3,
        "risk_security": 2,
    },
}

_ENGAGEMENT_PRIORS: dict[EngagementType, dict[str, int]] = {
    EngagementType.SIZING: {"financial": 5, "market_competitive": 4, "comparative_benchmark": 2},
    EngagementType.DIAGNOSTIC: {
        "causal_driver_tree": 5,
        "operational_capability": 3,
        "risk_security": 2,
    },
    EngagementType.EVALUATIVE: {
        "comparative_benchmark": 4,
        "market_competitive": 2,
        "risk_security": 2,
    },
    EngagementType.EXPLORATORY: {
        "market_competitive": 3,
        "comparative_benchmark": 3,
        "temporal_trend": 2,
    },
    EngagementType.STRATEGIC: {
        "market_competitive": 4,
        "stakeholder_incentive": 3,
        "temporal_trend": 3,
        "financial": 2,
    },
    EngagementType.DESIGN: {
        "technical_architecture": 3,
        "customer_user": 3,
        "risk_security": 2,
        "operational_capability": 2,
    },
    EngagementType.SYNTHESIS: {
        "scientific_evidence_review": 3,
        "comparative_benchmark": 3,
        "causal_driver_tree": 2,
    },
}


class LensSelector:
    """Deterministic planner that selects 2-5 lenses from request context."""

    def __init__(self, *, min_lenses: int = 2, max_lenses: int = 3) -> None:
        if min_lenses < 1 or max_lenses < min_lenses or max_lenses > 5:
            raise ValueError("LensSelector requires 1 <= min_lenses <= max_lenses <= 5")
        self._min_lenses = min_lenses
        self._max_lenses = max_lenses

    def select(
        self,
        *,
        question: str,
        engagement_type: EngagementType | None = None,
        domain: str | None = None,
        decision_context: str | None = None,
        output_target: str | None = None,
        client_context: str | None = None,
    ) -> LensSelection:
        text = " ".join(
            part
            for part in [question, domain, decision_context, output_target, client_context]
            if part
        )
        tokens = set(_tokens(text))
        domain_group = _domain_group(domain, text)
        scores = {candidate.lens_id: 0 for candidate in _CATALOG}

        for candidate in _CATALOG:
            scores[candidate.lens_id] += len(tokens & candidate.keywords)

        for lens_id, weight in _DOMAIN_PRIORS.get(domain_group, {}).items():
            scores[lens_id] += weight

        if engagement_type is not None:
            for lens_id, weight in _ENGAGEMENT_PRIORS.get(engagement_type, {}).items():
                scores[lens_id] += weight

        if output_target and re.search(
            r"\b(xlsx|excel|spreadsheet|model|dcf)\b",
            output_target,
            re.I,
        ):
            scores["financial"] += 4
        if output_target and re.search(
            r"\b(deck|slides|presentation|brief|memo)\b",
            output_target,
            re.I,
        ):
            scores["stakeholder_incentive"] += 1
            scores["market_competitive"] += 1

        ambiguous = _is_ambiguous(question, domain, decision_context)
        if ambiguous:
            scores["causal_driver_tree"] += 2
            scores["comparative_benchmark"] += 2

        selected_ids = _ranked_lens_ids(scores, self._max_lenses)
        if len(selected_ids) < self._min_lenses:
            for fallback in ("causal_driver_tree", "comparative_benchmark", "market_competitive"):
                if fallback not in selected_ids:
                    selected_ids.append(fallback)
                if len(selected_ids) >= self._min_lenses:
                    break

        candidates_by_id = {candidate.lens_id: candidate for candidate in _CATALOG}
        lenses = [
            LensDefinition(
                lens_id=lens_id,
                label=candidates_by_id[lens_id].label,
                prompt_family=candidates_by_id[lens_id].prompt_family,
                description=candidates_by_id[lens_id].description,
                rationale=_rationale(lens_id, scores[lens_id], domain_group, engagement_type),
            )
            for lens_id in selected_ids
        ]
        clarifying_questions = _clarifying_questions(
            question,
            domain,
            decision_context,
            output_target,
        )
        approval_required = bool(clarifying_questions) or ambiguous
        labels = ", ".join(lens.label for lens in lenses)
        return LensSelection(
            lenses=lenses,
            clarifying_questions=clarifying_questions,
            approval_required=approval_required,
            rationale=(
                f"Selected {len(lenses)} lenses from request/domain/engagement "
                f"signals: {labels}."
            ),
        )


def _ranked_lens_ids(scores: dict[str, int], max_lenses: int) -> list[str]:
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    positive = [lens_id for lens_id, score in ranked if score > 0]
    return positive[:max_lenses]


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9][a-z0-9_-]*", text.lower())


def _domain_group(domain: str | None, text: str) -> str:
    lower = f"{domain or ''} {text}".lower()
    if re.search(r"\b(technical|technology|architecture|engineering|software|api|code)\b", lower):
        return "technical"
    if re.search(r"\b(scientific|science|literature|academic|clinical|study|paper)\b", lower):
        return "scientific"
    if re.search(
        r"\b(business|financial|market|m&a|acquirer|competitor|operations|industry|company)\b",
        lower,
    ):
        return "business"
    return "unknown"


def _is_ambiguous(
    question: str,
    domain: str | None,
    decision_context: str | None,
) -> bool:
    token_count = len(_tokens(question))
    vague_refs = re.search(r"\b(this|that|it|thing|topic|stuff|project)\b", question.lower())
    return token_count < 6 or (bool(vague_refs) and not domain and not decision_context)


def _clarifying_questions(
    question: str,
    domain: str | None,
    decision_context: str | None,
    output_target: str | None,
) -> list[str]:
    questions: list[str] = []
    if not decision_context and len(_tokens(question)) < 14:
        questions.append("What decision will this research inform, and who is the audience?")
    if not domain and not re.search(
        r"\b(company|industry|technical|scientific|market|financial)\b",
        question,
        re.I,
    ):
        questions.append(
            "What domain or problem category should govern source selection and lenses?"
        )
    if not output_target:
        questions.append(
            "What output format should the system optimize for: memo, deck, "
            "spreadsheet, or evidence bundle?"
        )
    return questions[:3]


def _rationale(
    lens_id: str,
    score: int,
    domain_group: str,
    engagement_type: EngagementType | None,
) -> str:
    details: list[str] = []
    if score > 0:
        details.append(f"score={score}")
    if domain_group != "unknown":
        details.append(f"domain={domain_group}")
    if engagement_type is not None:
        details.append(f"engagement={engagement_type.value}")
    suffix = "; ".join(details) if details else "fallback coverage"
    return f"{lens_id} selected from {suffix}."


def catalog() -> list[dict[str, Any]]:
    """Expose lens catalog for docs/tests without leaking internal dataclasses."""
    return [
        {
            "lens_id": candidate.lens_id,
            "label": candidate.label,
            "prompt_family": candidate.prompt_family,
            "description": candidate.description,
            "keywords": sorted(candidate.keywords),
        }
        for candidate in _CATALOG
    ]
