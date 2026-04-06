"""Step 6: Seed AgentDefinition template registry.

Contains 5+ seed templates for common research agent configurations.
The registry matches tasks to templates by analyzing the task's category,
required sources, and engagement type.

Tighten-only invariant: Custom configs generated from templates can only
RESTRICT capabilities, never expand beyond the parent template.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from keystone.models.agents import AgentDefinition, AgentRole, ResearchAgentType
from keystone.models.research import EngagementType
from keystone.models.tasks import ModelTier, ResearchTask, TaskCategory
from keystone.tool_names import ToolName


class TemplateMatch(BaseModel):
    """Result of matching a task to an agent template."""

    template: AgentDefinition
    similarity: float = Field(ge=0.0, le=1.0)
    match_type: str = Field(description="exact | interpolated | custom")


# ---------------------------------------------------------------------------
# Seed templates
# ---------------------------------------------------------------------------

_QUANTITATIVE_ANALYST = AgentDefinition(
    name="quantitative_analyst",
    description="Financial data analysis, SEC filings, economic indicators, and quantitative modeling",
    role=AgentRole.RESEARCH,
    model=ModelTier.STANDARD,
    tools=[ToolName.EDGAR_FILINGS, ToolName.FINNHUB_MARKET, ToolName.EXA_SEARCH, ToolName.BRAVE_SEARCH, ToolName.FRED_DATA],
    system_prompt=(
        "You are a quantitative research analyst. Your methodology is data-driven: "
        "start with financial filings and economic data, build quantitative models, "
        "and validate with independent data sources. Always provide numerical ranges "
        "with explicit assumptions. Flag when data quality is insufficient for "
        "quantitative conclusions."
    ),
    source="builtin",
    research_type=ResearchAgentType.QUANTITATIVE,
)

_MARKET_RESEARCHER = AgentDefinition(
    name="market_researcher",
    description="Competitive analysis, market sizing, industry trends, and strategic positioning",
    role=AgentRole.RESEARCH,
    model=ModelTier.STANDARD,
    # news_search and industry_reports removed: no MCP servers registered yet.
    # Add back when dedicated news/industry-report MCP servers are available.
    tools=[ToolName.EXA_SEARCH, ToolName.BRAVE_SEARCH, ToolName.EDGAR_FILINGS, ToolName.FINNHUB_MARKET, ToolName.PAPER_SEARCH],
    system_prompt=(
        "You are a market research analyst. Your methodology focuses on competitive "
        "dynamics, market structure, and strategic positioning. Map the competitive "
        "landscape before diving into individual players. Always assess both the "
        "bull and bear case for market positions. Use multiple independent sources "
        "to triangulate market size estimates."
    ),
    source="builtin",
    research_type=ResearchAgentType.QUALITATIVE,
)

_ACADEMIC_RESEARCHER = AgentDefinition(
    name="academic_researcher",
    description="Academic literature, patent analysis, technology assessment, and expert consensus",
    role=AgentRole.RESEARCH,
    model=ModelTier.STANDARD,
    # patent_search removed: no MCP server registered yet.
    tools=[ToolName.PAPER_SEARCH, ToolName.DOI_VERIFY, ToolName.EXA_SEARCH, ToolName.BRAVE_SEARCH, ToolName.EDGAR_FILINGS],
    system_prompt=(
        "You are an academic research analyst. Your methodology prioritizes "
        "peer-reviewed sources, patent filings, and established expert consensus. "
        "Distinguish between preliminary findings and replicated results. Flag "
        "when academic consensus conflicts with industry practice. Assess "
        "technology readiness levels rigorously."
    ),
    source="builtin",
    research_type=ResearchAgentType.QUANTITATIVE,
)

_REGULATORY_ANALYST = AgentDefinition(
    name="regulatory_analyst",
    description="Regulatory landscape, compliance requirements, government policy, and legal frameworks",
    role=AgentRole.RESEARCH,
    model=ModelTier.STANDARD,
    # government_search and news_search removed: no MCP servers registered yet.
    tools=[ToolName.EDGAR_FILINGS, ToolName.EXA_SEARCH, ToolName.BRAVE_SEARCH, ToolName.PAPER_SEARCH, ToolName.FRED_DATA],
    system_prompt=(
        "You are a regulatory research analyst. Your methodology focuses on "
        "current and pending regulations, compliance requirements, and government "
        "policy direction. Distinguish between enacted law, proposed rules, and "
        "industry speculation. Map the regulatory timeline and identify key "
        "decision points. Assess regulatory risk by jurisdiction."
    ),
    source="builtin",
    research_type=ResearchAgentType.QUALITATIVE,
)

_GENERALIST = AgentDefinition(
    name="generalist_researcher",
    description="Broad research across multiple domains, trend analysis, and cross-cutting themes",
    role=AgentRole.RESEARCH,
    model=ModelTier.STANDARD,
    tools=[ToolName.EXA_SEARCH, ToolName.BRAVE_SEARCH, ToolName.PAPER_SEARCH, ToolName.EDGAR_FILINGS, ToolName.FINNHUB_MARKET],
    system_prompt=(
        "You are a generalist research analyst. Your methodology is breadth-first: "
        "survey the landscape before going deep. Identify cross-cutting themes "
        "and unexpected connections between domains. Flag when specialized "
        "expertise would improve the analysis. Prioritize recency and relevance."
    ),
    source="builtin",
    research_type=ResearchAgentType.QUALITATIVE,
)

_CONTRARIAN_ANALYST = AgentDefinition(
    name="contrarian_analyst",
    description="Devil's advocate analysis, assumption challenging, and risk identification",
    role=AgentRole.RESEARCH,
    model=ModelTier.STANDARD,
    tools=[ToolName.EXA_SEARCH, ToolName.BRAVE_SEARCH, ToolName.PAPER_SEARCH, ToolName.EDGAR_FILINGS, ToolName.FINNHUB_MARKET],
    system_prompt=(
        "You are a contrarian research analyst. Your methodology specifically "
        "seeks evidence that challenges prevailing assumptions and consensus views. "
        "For every strong claim, find the strongest counterargument. Identify "
        "base rate neglect, survivorship bias, and confirmation bias in existing "
        "analyses. Your value is in preventing groupthink."
    ),
    source="builtin",
    research_type=ResearchAgentType.CONTRARIAN,
)

_HISTORICAL_ANALYST = AgentDefinition(
    name="historical_analyst",
    description="Historical analogy analysis, pattern matching across industries and time periods",
    role=AgentRole.RESEARCH,
    model=ModelTier.STANDARD,
    tools=[ToolName.PAPER_SEARCH, ToolName.EXA_SEARCH, ToolName.BRAVE_SEARCH, ToolName.FINNHUB_MARKET, ToolName.EDGAR_FILINGS],
    system_prompt=(
        "You are a historical analogy analyst. Your methodology identifies "
        "structural parallels between the current situation and historical "
        "precedents. For each analogy, explicitly map what's similar, what's "
        "different, and where the analogy breaks down. Extract actionable "
        "lessons while acknowledging the limits of historical comparison."
    ),
    source="builtin",
    research_type=ResearchAgentType.HISTORICAL_ANALOGY,
)

_SEED_TEMPLATES: list[AgentDefinition] = [
    _QUANTITATIVE_ANALYST,
    _MARKET_RESEARCHER,
    _ACADEMIC_RESEARCHER,
    _REGULATORY_ANALYST,
    _GENERALIST,
    _CONTRARIAN_ANALYST,
    _HISTORICAL_ANALYST,
]

# Category -> preferred template name mapping
_CATEGORY_TEMPLATE_MAP: dict[TaskCategory, str] = {
    TaskCategory.MARKET_SIZING: "market_researcher",
    TaskCategory.COMPETITIVE_LANDSCAPE: "market_researcher",
    TaskCategory.FINANCIAL_ANALYSIS: "quantitative_analyst",
    TaskCategory.TECHNOLOGY_ASSESSMENT: "academic_researcher",
    TaskCategory.REGULATORY: "regulatory_analyst",
    TaskCategory.STRATEGIC_POSITIONING: "generalist_researcher",
}

# Source type -> template affinity
_SOURCE_TEMPLATE_AFFINITY: dict[str, str] = {
    "financial_filings": "quantitative_analyst",
    "financial_data": "quantitative_analyst",
    "sec_filings": "quantitative_analyst",
    "academic": "academic_researcher",
    "patents": "academic_researcher",
    "patent_data": "academic_researcher",
    "government": "regulatory_analyst",
    "industry_reports": "market_researcher",
    "news": "market_researcher",
    "company_filings": "quantitative_analyst",
}


class TemplateRegistry:
    """Registry of seed AgentDefinition templates.

    Matches tasks to templates using category, required sources, and
    engagement type signals. Above 0.85 similarity: use template with
    task-specific interpolation. Below 0.85: flag for custom generation.
    """

    def __init__(self) -> None:
        self._templates = {t.name: t for t in _SEED_TEMPLATES}

    def get_seed_templates(self) -> list[AgentDefinition]:
        """Return all seed templates."""
        return list(self._templates.values())

    def match(
        self,
        task: ResearchTask,
        engagement_type: EngagementType,
    ) -> TemplateMatch:
        """Find best-matching template for a task.

        Scoring:
        1. Category match: 0.4 weight
        2. Source affinity: 0.3 weight (average across required_sources)
        3. Engagement type fit: 0.3 weight
        """
        best_score = 0.0
        best_template = self._templates["generalist_researcher"]

        for template in self._templates.values():
            score = self._score_match(task, engagement_type, template)
            if score > best_score:
                best_score = score
                best_template = template

        if best_score >= 0.85:
            match_type = "exact"
        elif best_score >= 0.5:
            match_type = "interpolated"
        else:
            match_type = "custom"

        return TemplateMatch(
            template=best_template,
            similarity=round(best_score, 3),
            match_type=match_type,
        )

    def _score_match(
        self,
        task: ResearchTask,
        engagement_type: EngagementType,
        template: AgentDefinition,
    ) -> float:
        """Score how well a template matches a task."""
        # 1. Category match (0.4 weight)
        preferred = _CATEGORY_TEMPLATE_MAP.get(task.category)
        category_score = 1.0 if preferred == template.name else 0.0

        # 2. Source affinity (0.3 weight)
        if task.required_sources:
            source_scores = []
            for src in task.required_sources:
                affine_template = _SOURCE_TEMPLATE_AFFINITY.get(src)
                source_scores.append(1.0 if affine_template == template.name else 0.0)
            source_score = sum(source_scores) / len(source_scores)
        else:
            source_score = 0.3  # neutral

        # 3. Engagement type fit (0.3 weight)
        type_score = self._engagement_type_fit(engagement_type, template)

        return 0.4 * category_score + 0.3 * source_score + 0.3 * type_score

    def _engagement_type_fit(
        self, engagement_type: EngagementType, template: AgentDefinition
    ) -> float:
        """How well does this template fit the engagement type?"""
        fits: dict[EngagementType, dict[str, float]] = {
            EngagementType.SIZING: {
                "quantitative_analyst": 1.0,
                "market_researcher": 0.8,
                "academic_researcher": 0.4,
                "regulatory_analyst": 0.2,
                "generalist_researcher": 0.5,
                "contrarian_analyst": 0.3,
                "historical_analyst": 0.3,
            },
            EngagementType.DIAGNOSTIC: {
                "quantitative_analyst": 0.7,
                "market_researcher": 0.5,
                "academic_researcher": 0.6,
                "regulatory_analyst": 0.4,
                "generalist_researcher": 0.6,
                "contrarian_analyst": 0.7,
                "historical_analyst": 0.5,
            },
            EngagementType.EVALUATIVE: {
                "quantitative_analyst": 0.7,
                "market_researcher": 1.0,
                "academic_researcher": 0.6,
                "regulatory_analyst": 0.5,
                "generalist_researcher": 0.6,
                "contrarian_analyst": 0.8,
                "historical_analyst": 0.6,
            },
            EngagementType.EXPLORATORY: {
                "quantitative_analyst": 0.3,
                "market_researcher": 0.7,
                "academic_researcher": 0.6,
                "regulatory_analyst": 0.3,
                "generalist_researcher": 1.0,
                "contrarian_analyst": 0.4,
                "historical_analyst": 0.5,
            },
            EngagementType.STRATEGIC: {
                "quantitative_analyst": 0.6,
                "market_researcher": 0.8,
                "academic_researcher": 0.5,
                "regulatory_analyst": 0.5,
                "generalist_researcher": 0.7,
                "contrarian_analyst": 0.8,
                "historical_analyst": 0.9,
            },
        }
        return fits.get(engagement_type, {}).get(template.name, 0.3)
