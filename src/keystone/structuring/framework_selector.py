"""Engagement-type -> analytical framework selection for L2 structuring.

Maps the five EngagementType values to consulting analytical frameworks.
The selection is deterministic: the classifier in L0 has already chosen
the engagement type, so L2 just honors that choice. An LLM-driven
alternative lives outside scope; this layer's job is consistency.
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
}


def frameworks_for_engagement(
    engagement_type: EngagementType,
) -> list[FrameworkHint]:
    """Return the ordered framework hints for an engagement type."""
    return list(_FRAMEWORK_MAP.get(engagement_type, []))


def primary_framework(
    engagement_type: EngagementType,
) -> AnalyticalFramework | None:
    """Return the mandatory (primary) framework for the engagement type."""
    hints = _FRAMEWORK_MAP.get(engagement_type, [])
    for hint in hints:
        if hint.mandatory:
            return hint.framework
    return hints[0].framework if hints else None
