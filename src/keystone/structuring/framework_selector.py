"""Engagement-type -> analytical framework selection for L2 structuring.

Maps EngagementType values to analytical frameworks, with domain-aware
overrides. The selection is deterministic: the classifier in L0 has
already chosen the engagement type and domain, so L2 honors those choices.

Callers can supply an ``override`` list of FrameworkHint to bypass the
default mapping for novel engagements that don't fit the predefined
types (per Jack's architectural directive #1: predefined types are
templates, not constraints).
"""

from __future__ import annotations

from keystone.models.research import EngagementType
from keystone.models.structuring import AnalyticalFramework, FrameworkHint

_FRAMEWORK_MAP: dict[EngagementType, list[FrameworkHint]] = {
    EngagementType.SIZING: [
        FrameworkHint(
            framework=AnalyticalFramework.ESTIMATION,
            rationale=(
                "Sizing engagements require top-down and bottom-up estimates with "
                "explicit range and sensitivity to drivers."
            ),
            mandatory=True,
        ),
    ],
    EngagementType.DIAGNOSTIC: [
        FrameworkHint(
            framework=AnalyticalFramework.ROOT_CAUSE,
            rationale=(
                "Diagnostic engagements trace observed symptoms to candidate root "
                "causes; evidence must discriminate between causal hypotheses."
            ),
            mandatory=True,
        ),
    ],
    EngagementType.EVALUATIVE: [
        FrameworkHint(
            framework=AnalyticalFramework.PORTERS_FIVE_FORCES,
            rationale=(
                "Evaluative engagements assess attractiveness and positioning; "
                "Porter's Five Forces is the canonical lens for industry structure."
            ),
            mandatory=True,
        ),
        FrameworkHint(
            framework=AnalyticalFramework.VALUE_CHAIN,
            rationale=(
                "Value chain analysis augments five-forces with where margin sits "
                "and where differentiation is defensible."
            ),
            mandatory=False,
        ),
    ],
    EngagementType.EXPLORATORY: [
        FrameworkHint(
            framework=AnalyticalFramework.LANDSCAPE_MAPPING,
            rationale=(
                "Exploratory engagements aim to map the terrain before narrowing; "
                "landscape mapping makes the whitespace and clusters visible."
            ),
            mandatory=True,
        ),
    ],
    EngagementType.STRATEGIC: [
        FrameworkHint(
            framework=AnalyticalFramework.SCENARIO_PLANNING,
            rationale=(
                "Strategic engagements need decision options under uncertainty; "
                "scenario planning surfaces the axes that matter."
            ),
            mandatory=True,
        ),
        FrameworkHint(
            framework=AnalyticalFramework.SWOT,
            rationale=(
                "SWOT grounds scenarios in the client's current position so "
                "recommendations are actionable, not abstract."
            ),
            mandatory=False,
        ),
    ],
    EngagementType.DESIGN: [
        FrameworkHint(
            framework=AnalyticalFramework.TRADE_OFF_ANALYSIS,
            rationale=(
                "Design engagements require structured evaluation of competing "
                "requirements and architectural trade-offs."
            ),
            mandatory=True,
        ),
    ],
    EngagementType.SYNTHESIS: [
        FrameworkHint(
            framework=AnalyticalFramework.SYSTEMATIC_REVIEW,
            rationale=(
                "Synthesis engagements aggregate prior findings; a systematic "
                "review ensures coverage and reduces selection bias."
            ),
            mandatory=True,
        ),
    ],
}

_TECHNICAL_DOMAIN_KEYWORDS = frozenset(
    {"technical", "technology", "architecture", "engineering", "software", "system"}
)

_TECHNICAL_FRAMEWORK_OVERRIDES: dict[EngagementType, list[FrameworkHint]] = {
    EngagementType.EVALUATIVE: [
        FrameworkHint(
            framework=AnalyticalFramework.TRADE_OFF_ANALYSIS,
            rationale=(
                "Technical evaluations require structured trade-off analysis "
                "across dimensions rather than industry-structure frameworks."
            ),
            mandatory=True,
        ),
    ],
    EngagementType.STRATEGIC: [
        FrameworkHint(
            framework=AnalyticalFramework.TRADE_OFF_ANALYSIS,
            rationale=(
                "Technical strategy benefits from structured trade-off analysis "
                "to surface architectural decision points."
            ),
            mandatory=True,
        ),
        FrameworkHint(
            framework=AnalyticalFramework.LANDSCAPE_MAPPING,
            rationale=(
                "Mapping the technical landscape provides context for "
                "strategic architectural decisions."
            ),
            mandatory=False,
        ),
    ],
}


def _is_technical_domain(domain: str | None) -> bool:
    if domain is None:
        return False
    lower = domain.lower()
    return any(kw in lower for kw in _TECHNICAL_DOMAIN_KEYWORDS)


def frameworks_for_engagement(
    engagement_type: EngagementType,
    override: list[FrameworkHint] | None = None,
    *,
    domain: str | None = None,
) -> list[FrameworkHint]:
    """Return the ordered framework hints for an engagement type.

    When ``override`` is non-None it replaces the default mapping entirely,
    including the empty-list case — an explicit empty override yields an
    empty framework list (the caller has decided no framework applies).

    When ``domain`` indicates a technical subject area, domain-specific
    framework overrides take precedence over the business defaults for
    the applicable engagement types.
    """
    if override is not None:
        return list(override)
    if _is_technical_domain(domain) and engagement_type in _TECHNICAL_FRAMEWORK_OVERRIDES:
        return list(_TECHNICAL_FRAMEWORK_OVERRIDES[engagement_type])
    return list(_FRAMEWORK_MAP.get(engagement_type, []))


def primary_framework(
    engagement_type: EngagementType,
    override: list[FrameworkHint] | None = None,
    *,
    domain: str | None = None,
) -> AnalyticalFramework | None:
    """Return the mandatory (primary) framework for the engagement type.

    When ``override`` is non-None it is the selection source, using the
    same mandatory-first / first-listed fallback as the default mapping.
    """
    hints = frameworks_for_engagement(engagement_type, override, domain=domain)
    for hint in hints:
        if hint.mandatory:
            return hint.framework
    return hints[0].framework if hints else None
