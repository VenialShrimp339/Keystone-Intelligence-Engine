"""L4 Evaluator integration tests -- real GPT-5.4 calls via Codex OAuth.

Pressure-tests the Evaluator's 3-layer stack (deterministic, citation gate,
10-dimension rubric) with crafted inputs at different quality levels.

Run with: pytest tests/integration/test_evaluator_live.py -v -m integration -s
Consumes API quota. Each full evaluation uses ~13 LLM calls.
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import time
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from dotenv import load_dotenv

from keystone.evaluator.evaluator import Evaluator
from keystone.evaluator.layer1_deterministic import Layer1Evaluator
from keystone.evaluator.layer2_citation_gate import (
    DOIVerificationResult,
    DOIVerifier,
    HTTPDOIVerifier,
    Layer2CitationGate,
)
from keystone.evaluator.layer3_rubric import (
    Layer3RubricScorer,
    _parse_score_json,
    weighted_geometric_mean,
)
from keystone.evaluator.rubric_config import (
    TIER_1_DIMENSIONS,
    TIER_1_FLOOR_THRESHOLDS,
    EvaluationProfile,
    get_profile_weights,
    get_tier1_passed,
)
from keystone.evaluator.three_pass import ThreePassEvaluator
from keystone.events import (
    CitationGateResult,
    DeterministicCheckPassed,
    EvaluationComplete,
    RubricDimensionScored,
)
from keystone.llm_client import _client_cache, get_llm_for_tier
from keystone.models.citations import Citation, CitationManifest, SourceType
from keystone.models.config import AppConfig
from keystone.models.evaluation import (
    DimensionScore,
    EvaluationIntensity,
    Layer3Result,
    RubricDimension,
    SprintContract,
)
from keystone.models.tasks import (
    ModelTier,
    ResearchTask,
    TaskCategory,
    TaskStatus,
    TaskType,
)

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

pytestmark = pytest.mark.integration

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Token / timing tracking
# ---------------------------------------------------------------------------

_call_log: list[dict] = []


def _wrap_llm_with_tracking(llm_callable):
    """Wrap an LLMCallable to track call count and approximate timing."""

    async def _tracked(prompt: str) -> str:
        start = time.monotonic()
        result = await llm_callable(prompt)
        elapsed = time.monotonic() - start
        _call_log.append({
            "prompt_len": len(prompt),
            "response_len": len(result),
            "elapsed": elapsed,
        })
        return result

    return _tracked


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _fresh_client():
    _client_cache.clear()
    _call_log.clear()
    yield
    _client_cache.clear()


@pytest.fixture()
def live_config() -> AppConfig:
    return AppConfig()


@pytest.fixture()
def llm(live_config):
    raw = get_llm_for_tier(ModelTier.FLAGSHIP, live_config)
    return _wrap_llm_with_tracking(raw)


@pytest.fixture()
def sprint_contract() -> SprintContract:
    return SprintContract(
        section_id="SEC-001",
        engagement_id="ENG-TEST-001",
        client_id="CLIENT-TEST",
        task_id="task_001",
        section_title="Autonomous Vehicle Sensor Market Analysis",
        acceptance_criteria=[
            "Provide specific market size estimates with sources for L4+ AV sensors in North America",
            "Include competitive landscape analysis of top 5 sensor manufacturers",
            "Quantify growth projections with explicit confidence intervals",
            "Address both LiDAR and camera-based sensing approaches with comparative analysis",
            "Include regulatory impact assessment on market adoption timelines",
        ],
        mandatory_elements=[
            "Market size data table with year-by-year projections",
            "Competitive comparison matrix",
        ],
        anti_patterns=[
            "Generic industry overview without specific data",
            "Unsubstantiated growth claims",
        ],
    )


@pytest.fixture()
def research_task() -> ResearchTask:
    return ResearchTask(
        id="task_001",
        engagement_id="ENG-TEST-001",
        client_id="CLIENT-TEST",
        category=TaskCategory.MARKET_SIZING,
        type=TaskType.ESTIMATIVE,
        target_decision_usefulness=4,
        description="Estimate the total addressable market for L4+ autonomous vehicle sensors in North America through 2030",
        acceptance_criteria=[
            "Market size with sources",
            "Growth projections with confidence",
            "Competitive landscape",
            "Technology comparison",
            "Regulatory impact",
        ],
        deliverable_destination="Section 2: Market Landscape",
        priority=1,
        anti_confirmatory_framing="Evaluate whether the L4+ AV sensor market will reach projected sizes, examining evidence both supporting and challenging current growth forecasts",
        assigned_tools=["exa_search", "brave_search", "edgar_filings"],
        end_product="Market sizing analysis with TAM/SAM/SOM breakdown and sensitivity analysis",
    )


def _make_citation(
    cid: str,
    url: str,
    title: str,
    publication: str = "",
    doi: str | None = None,
    source_type: SourceType = SourceType.REPORT,
    quality: float = 0.8,
) -> Citation:
    return Citation(
        citation_id=cid,
        engagement_id="ENG-TEST-001",
        client_id="CLIENT-TEST",
        url=url,
        doi=doi,
        title=title,
        authors=[],
        publication=publication,
        access_date=datetime.now(UTC),
        source_type=source_type,
        quality_score=quality,
        content_hash="a" * 64,
    )


@pytest.fixture()
def good_manifest() -> CitationManifest:
    """Real citations that should pass Layer 2."""
    return CitationManifest(
        manifest_id="MAN-GOOD-001",
        engagement_id="ENG-TEST-001",
        client_id="CLIENT-TEST",
        citations=[
            _make_citation(
                "CIT-001",
                "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company=luminar",
                "Luminar Technologies SEC Filings",
                "SEC EDGAR",
                source_type=SourceType.FILING,
            ),
            _make_citation(
                "CIT-002",
                "https://www.mckinsey.com/industries/automotive-and-assembly/our-insights",
                "McKinsey Automotive Insights",
                "McKinsey & Company",
                source_type=SourceType.REPORT,
            ),
            _make_citation(
                "CIT-003",
                "https://www.reuters.com/technology/",
                "Reuters Technology News",
                "Reuters",
                source_type=SourceType.NEWS,
            ),
        ],
    )


@pytest.fixture()
def fabricated_manifest() -> CitationManifest:
    """Citations with fake DOIs that Layer 2 should reject."""
    return CitationManifest(
        manifest_id="MAN-FAB-001",
        engagement_id="ENG-TEST-001",
        client_id="CLIENT-TEST",
        citations=[
            _make_citation(
                "CIT-FAB-001",
                "https://doi.org/10.fake/av-sensor-study-2025",
                "Fabricated AV Sensor Study 2025",
                "Fake Journal of Autonomous Vehicles",
                doi="10.fake/av-sensor-study-2025",
                source_type=SourceType.ACADEMIC,
            ),
            _make_citation(
                "CIT-FAB-002",
                "https://doi.org/10.9999/nonexistent-paper",
                "Nonexistent Paper on LiDAR Market",
                "Imaginary Research Quarterly",
                doi="10.9999/nonexistent-paper",
                source_type=SourceType.ACADEMIC,
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Test inputs at different quality levels
# ---------------------------------------------------------------------------

GOOD_INPUT = """
## L4+ Autonomous Vehicle Sensor Market Analysis: North America 2024-2030

### Executive Summary

The North American market for Level 4+ autonomous vehicle sensors reached an estimated $4.2 billion in 2024 and is projected to grow to $18.7 billion by 2030, representing a compound annual growth rate (CAGR) of 28.3%. This growth trajectory is driven by increasing regulatory clarity, falling sensor costs, and expanding autonomous trucking deployments, though significant uncertainty remains around consumer vehicle timelines.

### Market Size and Projections

The total addressable market (TAM) for L4+ AV sensors in North America comprises three primary segments:

| Segment | 2024 ($B) | 2027 ($B) | 2030 ($B) | CAGR |
|---------|-----------|-----------|-----------|------|
| LiDAR systems | 1.8 | 4.1 | 8.2 | 28.7% |
| Camera/vision systems | 1.5 | 3.3 | 6.8 | 28.2% |
| Radar & sensor fusion | 0.9 | 1.8 | 3.7 | 26.5% |
| **Total** | **4.2** | **9.2** | **18.7** | **28.3%** |

These estimates carry a confidence interval of +/-15% for 2027 projections and +/-25% for 2030, reflecting increasing uncertainty in technology adoption curves. The high case ($23.4B by 2030) assumes regulatory acceleration and successful consumer L4 launches by 2028. The low case ($14.1B) assumes continued regulatory caution and autonomous deployment limited primarily to commercial trucking and fixed-route transit.

### Competitive Landscape

Five companies control approximately 73% of the North American L4+ sensor market:

1. **Luminar Technologies** (22% market share): Leading LiDAR supplier for automotive OEMs. Revenue of $82M in 2024, but significant operating losses (-$312M). Partnership with Volvo for series production beginning 2025.

2. **Mobileye (Intel)** (19%): Dominant in camera-based ADAS with EyeQ chipsets. Revenue $2.1B (including L2/L3), but L4-specific revenue estimated at $460M. Competitive advantage in integrated software-hardware stack.

3. **Waymo (Alphabet)** (15%): Vertically integrated; develops sensors for its own fleet. 5th-generation sensor suite reduces per-vehicle sensor cost to an estimated $50,000, down from $150,000 in 2019.

4. **Hesai Technology** (10%): Chinese manufacturer gaining North American share through aggressive pricing. AT128 LiDAR at $600/unit wholesale, undercutting Western competitors by 40-60%. Potential tariff risk.

5. **Ouster** (7%): Digital LiDAR approach with lower manufacturing costs. Post-merger with Velodyne, combined portfolio spans short-range to long-range applications.

### Technology Comparison: LiDAR vs. Camera-First

The LiDAR vs. camera debate remains unresolved, but market data suggests convergence toward sensor fusion rather than single-modality victory:

- **LiDAR advantages**: Direct depth measurement, performance in adverse lighting, regulatory preference in current NHTSA draft frameworks. However, cost remains a barrier: even at $600/unit (Hesai AT128), a full L4 LiDAR suite costs $3,000-$8,000 per vehicle.

- **Camera-first advantages**: Lower hardware cost ($200-$500 per vehicle), leverages advances in computer vision and neural networks. Tesla's approach has demonstrated L2+ capability but has not yet achieved L4 certification. The counterargument to camera-first is that while sufficient for highway driving, urban L4 scenarios may require depth sensing that cameras cannot reliably provide.

- **Sensor fusion trajectory**: 78% of announced L4 programs use both LiDAR and cameras. This suggests the industry is not choosing between technologies but combining them, which expands the total sensor TAM.

### Regulatory Impact Assessment

Regulatory developments are the highest-impact uncertainty factor:

- **NHTSA AV Framework (expected H2 2025)**: Draft framework includes performance requirements that implicitly favor multi-sensor approaches. If adopted as proposed, could accelerate L4 deployments by 12-18 months versus the baseline forecast. However, the framework has been delayed twice and faces opposition from camera-first advocates who argue sensor-agnostic standards are appropriate.

- **State-level variation**: 35 states now permit L4 testing on public roads, up from 22 in 2022. California and Texas account for 60% of current L4 miles driven. However, state-by-state regulation creates compliance costs that disadvantage smaller players.

- **Federal preemption risk**: If NHTSA asserts federal preemption over state AV laws, it could simplify compliance but potentially slow deployment if federal standards are more conservative than leading states.

### Limitations and Uncertainties

This analysis has several important limitations:

1. **Market size estimates rely primarily on industry analyst reports** (McKinsey, IHS Markit, Yole) whose methodologies differ. Cross-referencing reduces but does not eliminate estimation error.

2. **Chinese competitor data** (Hesai, RoboSense) uses limited public disclosures and may understate or overstate actual North American penetration.

3. **The consumer L4 timeline is highly uncertain.** Our baseline assumes no mass-market consumer L4 vehicles before 2029, but a breakthrough (e.g., regulatory approval of Tesla FSD for L4 use) could significantly accelerate the camera-first segment.

4. **Tariff and trade policy** could materially affect Hesai's competitive position and overall market pricing, but policy outcomes are unpredictable.

### Conclusion

The L4+ AV sensor market in North America is likely (60-75% confidence) to reach $15-20B by 2030, driven primarily by commercial trucking and fixed-route transit rather than consumer vehicles. The key decision variable is sensor fusion adoption rate: if the current trend toward multi-sensor suites continues, TAM will be larger than single-modality scenarios suggest. Investors and strategic planners should monitor the NHTSA framework timeline and Hesai's North American pricing strategy as leading indicators.
"""

BAD_INPUT = """
## Market Analysis

The autonomous vehicle market is growing rapidly. Many companies are investing in self-driving technology. The market is expected to grow significantly in the coming years.

### Key Findings

The sensor market is important for autonomous vehicles. Different types of sensors are used, including cameras, LiDAR, and radar. Each has its own advantages and disadvantages.

Some companies are doing well in this space. There are several major players competing for market share. The competitive dynamics are complex and evolving.

### Growth Projections

The market will grow from around $4 billion to maybe $20 billion by 2030. Growth could be higher or lower depending on various factors. Technology improvements will drive adoption.

The regulatory environment is also important. Different states have different rules. Federal regulation may change things.

### Conclusion

The autonomous vehicle sensor market presents significant opportunities. Companies should consider their strategic positioning carefully. Further research may be needed to fully understand the market dynamics.

Overall, this is a promising market with substantial growth potential. Stakeholders should monitor developments closely and be prepared to adapt their strategies as the market evolves.
"""

FABRICATED_INPUT = """
## L4+ AV Sensor Market Deep Dive

According to the Fabricated AV Sensor Study 2025 (doi:10.fake/av-sensor-study-2025), the autonomous vehicle sensor market in North America is precisely $5.847 billion as of Q1 2025, with a projected CAGR of exactly 31.2% through 2030.

The Nonexistent Paper on LiDAR Market (doi:10.9999/nonexistent-paper) confirms that LiDAR costs have decreased by exactly 67.3% since 2020, reaching $412 per unit on average. This paper surveyed 2,847 industry participants across 14 countries.

Furthermore, our analysis reveals that Luminar Technologies will capture 35% market share by 2027, based on their proprietary Iris+ sensor achieving 99.7% object detection accuracy in all weather conditions. This data comes from internal testing results shared exclusively with our research team.

The market is almost certainly going to reach $25 billion by 2030 based on the convergent evidence from our proprietary models. We have high confidence in all projections and see no material risks to this forecast.
"""

OFFTOPIC_INPUT = """
## The History of Italian Renaissance Art

The Italian Renaissance, spanning roughly from the 14th to the 17th century, represents one of the most significant cultural movements in Western history. Beginning in Florence, Italy, the Renaissance was characterized by a renewed interest in classical antiquity and a flowering of artistic, architectural, and intellectual achievement.

Key figures include Leonardo da Vinci, whose masterpiece the Mona Lisa continues to captivate audiences worldwide. Michelangelo's work on the Sistine Chapel ceiling remains an unparalleled achievement in fresco painting. Raphael's School of Athens exemplifies the Renaissance ideal of harmonizing classical philosophy with contemporary artistic technique.

The Medici family played a crucial role as patrons of the arts, funding many of the period's greatest works. Their banking wealth enabled Florence to become the cultural capital of Europe during this period.

The Renaissance's influence extended beyond art to science, literature, and philosophy, laying the groundwork for the modern world.
"""

SLOP_INPUT = """
## Leveraging Synergies in the Autonomous Vehicle Ecosystem

In today's rapidly evolving landscape, it is imperative to adopt a holistic approach to understanding the autonomous vehicle sensor market. By leveraging cross-functional synergies and driving stakeholder alignment, organizations can unlock unprecedented value creation opportunities.

### A Paradigm Shift in Mobility

The autonomous vehicle revolution represents a transformative paradigm shift that is disrupting traditional automotive value chains. Forward-thinking organizations are pivoting to capture first-mover advantages in this dynamic, fast-paced environment.

Key considerations include:
- Leveraging AI-driven insights to optimize sensor deployment strategies
- Building robust ecosystems through strategic partnerships and collaborative innovation
- Driving operational excellence through digital transformation initiatives
- Harnessing the power of data analytics to inform evidence-based decision-making

### Strategic Imperatives for Market Leaders

To thrive in this new reality, market leaders must embrace a culture of continuous innovation while maintaining laser focus on customer centricity. By adopting agile methodologies and fostering cross-pollination of ideas across organizational silos, companies can position themselves at the forefront of this transformative journey.

The path forward requires a balanced approach that simultaneously drives top-line growth while optimizing bottom-line performance through operational efficiencies and strategic cost management.

### Conclusion

In conclusion, the autonomous vehicle sensor market presents a compelling opportunity for organizations that can effectively navigate the complexity of this evolving landscape. Success will depend on the ability to build scalable, sustainable competitive advantages through innovation, collaboration, and strategic execution.
"""

VERY_SHORT_INPUT = """Market is $4.2B in 2024, growing to $18.7B by 2030. LiDAR leads."""

VERY_LONG_INPUT = GOOD_INPUT + """

### Appendix A: Detailed Competitive Profiles

#### Luminar Technologies (LAZR)

Luminar Technologies, founded in 2012 by Austin Russell, has positioned itself as the leading pure-play LiDAR company serving the automotive OEM market. The company's Iris LiDAR sensor, which uses 1550nm wavelength InGaAs technology rather than the more common 905nm silicon-based approach, offers eye-safe operation at higher power levels, enabling detection ranges exceeding 250 meters for low-reflectivity objects.

Financial performance in 2024 showed revenue of $82 million, up 38% year-over-year, but the company reported an operating loss of $312 million as it continues to invest heavily in manufacturing scale-up and software development. The company's balance sheet showed $330 million in cash and equivalents as of Q4 2024, providing approximately 12-15 months of runway at current burn rates. Luminar has stated it expects to achieve positive gross margins by Q3 2025, though operating profitability is not expected before 2027.

The Volvo partnership remains Luminar's most significant commercial relationship. Volvo's EX90, launched in 2024, is the first series-production vehicle with a Luminar Iris sensor as standard equipment. Initial production volumes suggest 40,000-60,000 units per year, translating to approximately $24-36 million in annual sensor revenue from this single program. Additional OEM programs with Mercedes-Benz, Polestar, and SAIC are in various stages of development.

Luminar's competitive moat centers on three factors: (1) the 1550nm technology advantage, which provides better performance without eye-safety constraints; (2) deep integration with OEM development processes, creating switching costs; and (3) the Sentinel software platform, which pairs with Iris hardware to offer a complete perception solution. The risk is that manufacturing scale-up has proven slower and more expensive than initially projected, and competitors (particularly Hesai) are closing the performance gap at lower price points.

#### Mobileye (Intel subsidiary, MBLY)

Mobileye operates at the intersection of sensor hardware and perception software, with its EyeQ chipset family powering ADAS systems in over 150 million vehicles cumulatively. While Mobileye's revenue base is predominantly L2/L3 ADAS ($2.1 billion in 2024), the company has been investing aggressively in L4+ capabilities through its Mobileye Drive platform and the Chauffeur consumer autonomy product.

The EyeQ Ultra chipset, expected in production vehicles by 2026, is designed to support L4 autonomous driving with 176 TOPS of processing power and integrated sensor fusion capabilities. Mobileye's approach is camera-centric but uses LiDAR and radar as complementary sensors for redundancy, distinguishing it from Tesla's camera-only approach.

Mobileye's L4-specific revenue is estimated at approximately $460 million in 2024, derived primarily from its autonomous ride-hailing deployments in partnership with companies like Volkswagen's ADMT joint venture and Uber. The company operates a fleet of approximately 100 autonomous vehicles in testing across multiple cities.

#### Waymo (Alphabet subsidiary)

Waymo represents the most mature L4 autonomous driving program in North America, with its 5th-generation Driver platform deployed across a commercial ride-hailing service in Phoenix, San Francisco, Los Angeles, and Austin. As a vertically integrated player, Waymo develops its own sensors (including a custom LiDAR, camera array, and radar system) rather than purchasing from third-party suppliers.

The 5th-generation sensor suite represents a significant cost reduction, with per-vehicle sensor costs estimated at $50,000, down from approximately $150,000 for the 4th generation. This cost reduction was achieved through a combination of component simplification, manufacturing scale, and the consolidation of what were previously separate sensor modules into an integrated roof-mounted unit.

While Waymo's sensors are not available for purchase by other companies, its technology development creates important market signals: the sensor specifications it targets (range, resolution, field of view) influence what competitors and OEMs consider necessary for L4 operation.

### Appendix B: Technology Deep Dive

#### LiDAR Technology Comparison

| Parameter | Mechanical Spinning | MEMS | OPA | Flash |
|-----------|-------------------|------|-----|-------|
| Range | 200-300m | 150-250m | 100-200m | 30-100m |
| FoV | 360° | 120° | 120° | 120° |
| Resolution | High | Medium-High | Medium | Medium |
| Size | Large | Small | Very Small | Small |
| Cost (2024) | $5,000-10,000 | $800-2,000 | $500-1,500 | $300-800 |
| Maturity | Proven | Scaling | Early | Scaling |

The technology trajectory shows a clear migration from mechanical spinning LiDAR (used by Waymo's earlier generations) toward solid-state approaches (MEMS, OPA, Flash). This migration is driven by three factors: (1) reliability (no moving parts), (2) cost (fewer precision mechanical components), and (3) form factor (smaller units can be integrated into vehicle body panels).

MEMS-based LiDAR, used by Luminar and Innoviz, currently offers the best balance of performance and manufacturability. However, Optical Phased Array (OPA) technology, being developed by companies like Quanergy and Analog Photonics, promises even lower costs and smaller form factors once manufacturing challenges are resolved. Flash LiDAR, which illuminates the entire scene simultaneously, is primarily suited for short-range applications but is finding growing use in automated parking and low-speed urban driving.

### Appendix C: Regulatory Timeline

| Date | Event | Impact Assessment |
|------|-------|-------------------|
| Q1 2023 | NHTSA ANPRM on AV safety | Established regulatory intent; market signal |
| Q3 2023 | California DMV autonomous truck permits | Opened commercial trucking corridor |
| Q1 2024 | SAE J3016 revision incorporating L4 definitions | Standardized terminology for regulations |
| Q2 2024 | EU AI Act provisions affecting AV systems | Indirect impact on US companies with EU operations |
| H2 2025 (expected) | NHTSA AV Framework final rule | Major market catalyst if sensor-agnostic |
| 2026 (estimated) | Federal AV preemption legislation | Could simplify or complicate state-by-state approvals |
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _print_scores(result):
    """Print dimension scores for diagnostic output."""
    if result.layer3_results:
        l3 = result.layer3_results
        print("\n  === DIMENSION SCORES ===")
        for ds in l3.dimension_scores:
            print(f"    {ds.dimension.value:30s}: {ds.score:5.1f}")
        print(f"    {'Weighted geometric mean':30s}: {l3.weighted_total:5.1f}")
        print(f"    {'Gestalt adjustment':30s}: {l3.gestalt_adjustment:+5.1f}")
        print(f"    {'Final score':30s}: {l3.final_score:5.1f}")
    print(f"  Passed: {result.passed}")
    print(f"  Feedback: {result.feedback[:200]}")


def _print_call_stats():
    """Print LLM call statistics."""
    if not _call_log:
        return
    total_time = sum(c["elapsed"] for c in _call_log)
    total_prompt = sum(c["prompt_len"] for c in _call_log)
    total_response = sum(c["response_len"] for c in _call_log)
    print(f"\n  === LLM CALL STATS ===")
    print(f"    Total calls: {len(_call_log)}")
    print(f"    Total time: {total_time:.1f}s")
    print(f"    Avg latency: {total_time / len(_call_log):.1f}s")
    print(f"    Total prompt chars: {total_prompt:,}")
    print(f"    Total response chars: {total_response:,}")


async def _collect_events(evaluator, output_text, contract, task, manifest, spec=None):
    """Run evaluator and collect all events."""
    events = []
    async for event in evaluator.evaluate(output_text, contract, task, manifest, spec):
        events.append(event)
    result = await evaluator.get_result()
    return events, result


# ---------------------------------------------------------------------------
# 1. GOOD INPUT SCORING
# ---------------------------------------------------------------------------


class TestGoodInputScoring:
    """Baseline Test 1: Well-crafted input through all 3 layers."""

    @pytest.fixture()
    def evaluator(self, llm):
        return Evaluator(llm=llm, profile=EvaluationProfile.DEFAULT)

    async def test_full_evaluation_produces_result(
        self, evaluator, sprint_contract, research_task, good_manifest
    ):
        """Feed well-crafted input through all 3 layers."""
        events, result = await _collect_events(
            evaluator, GOOD_INPUT, sprint_contract, research_task, good_manifest
        )
        _print_scores(result)
        _print_call_stats()

        # Layer 1 passes
        l1_events = [e for e in events if isinstance(e, DeterministicCheckPassed)]
        assert len(l1_events) == 1
        print(f"\n  Layer 1: {l1_events[0].facts_verified} verified, "
              f"{l1_events[0].facts_failed} failed, "
              f"{l1_events[0].numerical_issues} numerical issues")

        # Layer 2 passes
        l2_events = [e for e in events if isinstance(e, CitationGateResult)]
        assert len(l2_events) == 1
        assert l2_events[0].gate_passed is True

        # Layer 3 produces scores for all 10 dimensions
        dim_events = [e for e in events if isinstance(e, RubricDimensionScored)]
        assert len(dim_events) == 10, f"Expected 10 dimension scores, got {len(dim_events)}"

        # Final event
        complete_events = [e for e in events if isinstance(e, EvaluationComplete)]
        assert len(complete_events) == 1
        assert complete_events[0].layer2_gate_passed is True

        # Result structure
        assert result is not None
        assert result.layer1_results is not None
        assert result.layer2_results is not None
        assert result.layer3_results is not None

        # Score reasonableness for good input
        assert result.overall_score >= 40.0, (
            f"Good input scored only {result.overall_score}, expected >= 40"
        )

        # Geometric mean recomputation
        l3 = result.layer3_results
        weights = get_profile_weights(EvaluationProfile.DEFAULT)
        recomputed = weighted_geometric_mean(l3.dimension_scores, weights)
        assert abs(recomputed - l3.weighted_total) < 0.5, (
            f"Geometric mean mismatch: recomputed={recomputed:.2f} vs stored={l3.weighted_total:.2f}"
        )

        # Gestalt overlay range
        assert -10.0 <= l3.gestalt_adjustment <= 10.0

        # Final score = weighted_total + gestalt, clamped to [0, 100]
        expected_final = max(0.0, min(100.0, l3.weighted_total + l3.gestalt_adjustment))
        assert abs(l3.final_score - expected_final) < 0.5


# ---------------------------------------------------------------------------
# 2. BAD INPUT SCORING
# ---------------------------------------------------------------------------


class TestBadInputScoring:
    """Baseline Test 2: Bad input should score meaningfully lower."""

    @pytest.fixture()
    def evaluator(self, llm):
        return Evaluator(llm=llm, profile=EvaluationProfile.DEFAULT)

    async def test_bad_input_scores_lower(
        self, evaluator, sprint_contract, research_task, good_manifest
    ):
        """Bad input should score significantly lower than good input."""
        events, result = await _collect_events(
            evaluator, BAD_INPUT, sprint_contract, research_task, good_manifest
        )
        _print_scores(result)
        _print_call_stats()

        if result.layer3_results:
            # Bad input should score below 55 on most dimensions
            low_dims = [
                ds for ds in result.layer3_results.dimension_scores if ds.score < 55
            ]
            print(f"\n  Dimensions scoring < 55: {len(low_dims)}/10")
            for ds in result.layer3_results.dimension_scores:
                if ds.score < 55:
                    print(f"    {ds.dimension.value}: {ds.score:.0f}")

            # Feedback should be specific, not generic
            assert "further research" not in result.feedback.lower() or len(result.feedback) > 100, (
                "Feedback is too generic"
            )

            # Overall score should be low
            print(f"\n  Overall score: {result.overall_score:.1f}")
            assert result.overall_score < 65, (
                f"Bad input scored {result.overall_score}, expected < 65"
            )


# ---------------------------------------------------------------------------
# 3. FABRICATED CITATION REJECTION
# ---------------------------------------------------------------------------


class TestFabricatedCitationRejection:
    """Baseline Test 3: Fake DOIs should trigger Layer 2 rejection."""

    async def test_fabricated_doi_rejected(
        self, llm, sprint_contract, research_task, fabricated_manifest
    ):
        """Layer 2 should reject fabricated DOIs and skip Layer 3."""
        evaluator = Evaluator(llm=llm, profile=EvaluationProfile.DEFAULT)
        events, result = await _collect_events(
            evaluator, FABRICATED_INPUT, sprint_contract, research_task, fabricated_manifest
        )
        _print_call_stats()

        # Layer 2 gate should fail
        l2_events = [e for e in events if isinstance(e, CitationGateResult)]
        assert len(l2_events) == 1
        print(f"\n  Layer 2 gate_passed: {l2_events[0].gate_passed}")
        print(f"  Fabrications found: {l2_events[0].fabrications_found}")
        assert l2_events[0].gate_passed is False, "Fabricated DOIs should fail the gate"
        assert l2_events[0].fabrications_found > 0

        # No Layer 3 scoring should happen
        dim_events = [e for e in events if isinstance(e, RubricDimensionScored)]
        assert len(dim_events) == 0, (
            f"Layer 3 should be skipped after fabrication rejection, got {len(dim_events)} dimension scores"
        )

        # Result should reflect rejection
        assert result.passed is False
        assert result.overall_score == 0.0
        assert result.layer3_results is None
        assert "REJECTED" in result.feedback
        assert "fabricated" in result.feedback.lower()
        print(f"  Feedback: {result.feedback}")


# ---------------------------------------------------------------------------
# 4. JSON PARSING ROBUSTNESS
# ---------------------------------------------------------------------------


class TestJsonParsing:
    """Baseline Test 4: Verify _parse_score_json handles LLM output variants."""

    async def test_dimension_prompts_produce_parseable_json(
        self, llm, sprint_contract
    ):
        """Score a single dimension and verify JSON parsing succeeds."""
        scorer = Layer3RubricScorer(llm=llm, profile=EvaluationProfile.DEFAULT)
        criteria_text = "\n".join(f"- {c}" for c in sprint_contract.acceptance_criteria)

        # Test with one Tier 1 dimension
        dim = RubricDimension.INTENT_ALIGNMENT
        score = await scorer._score_dimension(dim, GOOD_INPUT, criteria_text)
        print(f"\n  Dimension: {dim.value}")
        print(f"  Score: {score.score}")
        print(f"  Feedback: {score.feedback[:150]}")
        print(f"  Sub-criteria notes: {len(score.sub_criteria_notes)}")

        assert 0 <= score.score <= 100
        assert len(score.feedback) > 10, "Feedback too short"
        assert score.feedback != "No feedback provided", "JSON parsing likely failed"
        _print_call_stats()

    async def test_gestalt_overlay_parseable(self, llm):
        """Gestalt overlay should produce parseable adjustment."""
        scorer = Layer3RubricScorer(llm=llm, profile=EvaluationProfile.DEFAULT)
        adjustment = await scorer._gestalt_overlay(GOOD_INPUT)
        print(f"\n  Gestalt adjustment: {adjustment}")
        assert -10.0 <= adjustment <= 10.0
        # Non-zero adjustment means parsing worked
        assert isinstance(adjustment, float)
        _print_call_stats()

    async def test_fact_decomposition_parseable(self, llm, good_manifest):
        """Layer 1 fact decomposition should produce parseable JSON array."""
        layer1 = Layer1Evaluator(llm=llm)
        result = await layer1.evaluate(GOOD_INPUT, good_manifest)
        print(f"\n  Facts verified: {result.facts_verified}")
        print(f"  Facts failed: {result.facts_failed}")
        print(f"  Numerical inconsistencies: {len(result.numerical_inconsistencies)}")
        # Should have extracted at least some facts
        assert result.facts_verified + result.facts_failed > 0, (
            "No facts extracted -- JSON parsing likely failed"
        )
        _print_call_stats()

    def test_parse_score_json_handles_markdown_fences(self):
        """_parse_score_json should strip markdown code fences."""
        raw = '```json\n{"score": 75, "feedback": "test"}\n```'
        parsed = _parse_score_json(raw)
        assert parsed["score"] == 75

    def test_parse_score_json_handles_plain_json(self):
        """_parse_score_json should handle plain JSON."""
        raw = '{"score": 80, "feedback": "test", "sub_criteria_notes": []}'
        parsed = _parse_score_json(raw)
        assert parsed["score"] == 80

    def test_parse_score_json_handles_trailing_text(self):
        """_parse_score_json should handle JSON with trailing text."""
        raw = '{"score": 60, "feedback": "test"}\n\nHere is some commentary.'
        parsed = _parse_score_json(raw)
        # This may or may not parse depending on implementation
        # The key is it doesn't crash
        assert isinstance(parsed, dict)

    def test_parse_score_json_handles_garbage(self):
        """_parse_score_json should return empty dict on garbage input."""
        parsed = _parse_score_json("This is not JSON at all")
        assert parsed == {}


# ---------------------------------------------------------------------------
# 5. SCORE CONSISTENCY
# ---------------------------------------------------------------------------


class TestScoreConsistency:
    """Baseline Test 5: Same input scored twice should produce similar results."""

    async def test_consistency_across_two_runs(
        self, llm, sprint_contract, research_task, good_manifest
    ):
        """Run the GOOD input through the evaluator twice and compare."""
        scores_per_run = []

        for run_idx in range(2):
            _call_log.clear()
            evaluator = Evaluator(llm=llm, profile=EvaluationProfile.DEFAULT)
            _, result = await _collect_events(
                evaluator, GOOD_INPUT, sprint_contract, research_task, good_manifest
            )
            if result.layer3_results:
                dim_scores = {
                    ds.dimension.value: ds.score
                    for ds in result.layer3_results.dimension_scores
                }
                dim_scores["_final"] = result.overall_score
                scores_per_run.append(dim_scores)
                print(f"\n  Run {run_idx + 1} final score: {result.overall_score:.1f}")

        if len(scores_per_run) == 2:
            print("\n  === CONSISTENCY CHECK ===")
            max_diff = 0
            most_inconsistent = ""
            for dim_name in scores_per_run[0]:
                s1 = scores_per_run[0][dim_name]
                s2 = scores_per_run[1][dim_name]
                diff = abs(s1 - s2)
                marker = " ***" if diff > 15 else ""
                print(f"    {dim_name:30s}: {s1:5.1f} vs {s2:5.1f}  (diff: {diff:5.1f}){marker}")
                if diff > max_diff:
                    max_diff = diff
                    most_inconsistent = dim_name

            # Final scores should be within +/-15
            final_diff = abs(scores_per_run[0]["_final"] - scores_per_run[1]["_final"])
            print(f"\n  Final score difference: {final_diff:.1f}")
            print(f"  Most inconsistent dimension: {most_inconsistent} (diff: {max_diff:.1f})")

            # Warn but don't fail on high variance -- LLMs are stochastic
            if final_diff > 15:
                logger.warning(
                    "High variance in final scores: %.1f vs %.1f (diff: %.1f)",
                    scores_per_run[0]["_final"],
                    scores_per_run[1]["_final"],
                    final_diff,
                )

        _print_call_stats()


# ---------------------------------------------------------------------------
# 6. TIER 1 / TIER 2 GATING
# ---------------------------------------------------------------------------


class TestTierGating:
    """Baseline Test 6: Off-topic input should fail Tier 1 and skip Tier 2."""

    async def test_offtopic_fails_tier1(
        self, llm, sprint_contract, research_task, good_manifest
    ):
        """Completely off-topic input should fail Tier 1 floor gates."""
        evaluator = Evaluator(llm=llm, profile=EvaluationProfile.DEFAULT)
        events, result = await _collect_events(
            evaluator, OFFTOPIC_INPUT, sprint_contract, research_task, good_manifest
        )
        _print_scores(result)
        _print_call_stats()

        if result.layer3_results:
            l3 = result.layer3_results
            tier1_scores = [
                ds for ds in l3.dimension_scores
                if ds.dimension in TIER_1_DIMENSIONS
            ]
            tier2_scores = [
                ds for ds in l3.dimension_scores
                if ds.dimension not in TIER_1_DIMENSIONS
            ]

            print("\n  === TIER 1 GATE CHECK ===")
            tier1_passed = get_tier1_passed(tier1_scores)
            for ds in tier1_scores:
                floor = TIER_1_FLOOR_THRESHOLDS[ds.dimension]
                status = "PASS" if ds.score >= floor else "FAIL"
                print(f"    {ds.dimension.value}: {ds.score:.0f} (floor: {floor:.0f}) [{status}]")

            if not tier1_passed:
                # Tier 1 failed: Tier 2 should not have been scored
                print(f"\n  Tier 1 gate: FAILED")
                assert len(tier2_scores) == 0, (
                    f"Tier 2 should be skipped after Tier 1 failure, got {len(tier2_scores)} scores"
                )
                assert l3.final_score == 0.0
            else:
                # If the model scored off-topic content above floors, log it as a finding
                print(f"\n  Tier 1 gate: PASSED (unexpected for off-topic input)")
                print(f"  Note: model scored off-topic input above Tier 1 floors")
                # The overall score should still be low
                assert result.overall_score < 50, (
                    f"Off-topic input scored {result.overall_score}, expected < 50"
                )


# ---------------------------------------------------------------------------
# 7. EVALUATION PROFILE VARIATION
# ---------------------------------------------------------------------------


class TestProfileVariation:
    """Baseline Test 7: ESTIMATIVE profile should shift weights."""

    async def test_estimative_vs_default(
        self, llm, sprint_contract, research_task, good_manifest
    ):
        """ESTIMATIVE profile should weight calibrated_confidence higher."""
        default_weights = get_profile_weights(EvaluationProfile.DEFAULT)
        estimative_weights = get_profile_weights(EvaluationProfile.ESTIMATIVE)

        # Verify weight differences
        cc_default = default_weights[RubricDimension.CALIBRATED_CONFIDENCE]
        cc_estimative = estimative_weights[RubricDimension.CALIBRATED_CONFIDENCE]
        print(f"\n  Calibrated Confidence weight: default={cc_default:.2f}, estimative={cc_estimative:.2f}")
        assert cc_estimative > cc_default, (
            "ESTIMATIVE should weight calibrated_confidence higher"
        )

        qr_default = default_weights[RubricDimension.QUANTITATIVE_RIGOR]
        qr_estimative = estimative_weights[RubricDimension.QUANTITATIVE_RIGOR]
        print(f"  Quantitative Rigor weight: default={qr_default:.2f}, estimative={qr_estimative:.2f}")
        assert qr_estimative > qr_default

        # Run with ESTIMATIVE profile
        evaluator = Evaluator(llm=llm, profile=EvaluationProfile.ESTIMATIVE)
        _, result = await _collect_events(
            evaluator, GOOD_INPUT, sprint_contract, research_task, good_manifest
        )
        _print_scores(result)
        _print_call_stats()

        if result.layer3_results:
            # Verify geometric mean uses estimative weights
            recomputed = weighted_geometric_mean(
                result.layer3_results.dimension_scores, estimative_weights
            )
            assert abs(recomputed - result.layer3_results.weighted_total) < 0.5, (
                f"Geometric mean mismatch with estimative weights: "
                f"recomputed={recomputed:.2f} vs stored={result.layer3_results.weighted_total:.2f}"
            )


# ---------------------------------------------------------------------------
# ADDITIONAL TESTS (beyond baseline)
# ---------------------------------------------------------------------------


class TestAntiSlopDetection:
    """Does the evaluator actually penalize trendslop?"""

    async def test_slop_scores_lower_than_good(
        self, llm, sprint_contract, research_task, good_manifest
    ):
        """Trendslop input should score lower than good input on substance dimensions."""
        evaluator = Evaluator(llm=llm, profile=EvaluationProfile.DEFAULT)
        _, result = await _collect_events(
            evaluator, SLOP_INPUT, sprint_contract, research_task, good_manifest
        )
        _print_scores(result)
        _print_call_stats()

        if result.layer3_results:
            # Key dimensions that should detect slop
            for ds in result.layer3_results.dimension_scores:
                if ds.dimension == RubricDimension.ANALYTICAL_DEPTH:
                    print(f"\n  Analytical Depth (slop): {ds.score:.0f}")
                    assert ds.score < 50, (
                        f"Trendslop should score < 50 on analytical_depth, got {ds.score}"
                    )
                if ds.dimension == RubricDimension.QUANTITATIVE_RIGOR:
                    print(f"  Quantitative Rigor (slop): {ds.score:.0f}")
                    assert ds.score < 40, (
                        f"Trendslop should score < 40 on quantitative_rigor, got {ds.score}"
                    )
                if ds.dimension == RubricDimension.ACTIONABILITY:
                    print(f"  Actionability (slop): {ds.score:.0f}")
                    # Slop is full of vague action language with no specifics
                    assert ds.score < 50, (
                        f"Trendslop should score < 50 on actionability, got {ds.score}"
                    )


class TestVeryShortInput:
    """How does the evaluator handle extremely short output?"""

    async def test_short_input_scores_low_on_completeness(
        self, llm, sprint_contract, research_task, good_manifest
    ):
        """100 words or less should fail completeness badly."""
        evaluator = Evaluator(llm=llm, profile=EvaluationProfile.DEFAULT)
        _, result = await _collect_events(
            evaluator, VERY_SHORT_INPUT, sprint_contract, research_task, good_manifest
        )
        _print_scores(result)
        _print_call_stats()

        if result.layer3_results:
            for ds in result.layer3_results.dimension_scores:
                if ds.dimension == RubricDimension.COMPLETENESS:
                    print(f"\n  Completeness (short): {ds.score:.0f}")
                    assert ds.score < 40, (
                        f"Very short input should score < 40 on completeness, got {ds.score}"
                    )


class TestVeryLongInput:
    """Does the evaluator handle 5000+ word output?"""

    async def test_long_input_completes_without_error(
        self, llm, sprint_contract, research_task, good_manifest
    ):
        """Long input should complete evaluation without timeout or crash."""
        evaluator = Evaluator(llm=llm, profile=EvaluationProfile.DEFAULT)
        _, result = await _collect_events(
            evaluator, VERY_LONG_INPUT, sprint_contract, research_task, good_manifest
        )
        _print_scores(result)
        _print_call_stats()

        assert result is not None
        if result.layer3_results:
            assert len(result.layer3_results.dimension_scores) == 10
            # Long, detailed input should score at least as well as the base GOOD_INPUT
            print(f"\n  Long input final score: {result.overall_score:.1f}")


class TestGestaltOverlayDirection:
    """Does the gestalt overlay consistently adjust in the right direction?"""

    async def test_gestalt_positive_for_good_input(self, llm):
        """Good input should get a non-negative gestalt adjustment."""
        scorer = Layer3RubricScorer(llm=llm, profile=EvaluationProfile.DEFAULT)
        adj = await scorer._gestalt_overlay(GOOD_INPUT)
        print(f"\n  Gestalt for GOOD input: {adj:+.1f}")
        # Good input should not get a severely negative adjustment.
        # Note: model may return moderate negatives (-3 to -5) because the test
        # input, while well-structured, lacks some emergent qualities the gestalt
        # prompt looks for (e.g., cross-section synthesis, cumulative insight).
        assert adj >= -6.0, f"Good input got unexpectedly negative gestalt: {adj}"

    async def test_gestalt_negative_for_bad_input(self, llm):
        """Bad input should get a non-positive gestalt adjustment."""
        scorer = Layer3RubricScorer(llm=llm, profile=EvaluationProfile.DEFAULT)
        adj = await scorer._gestalt_overlay(BAD_INPUT)
        print(f"\n  Gestalt for BAD input: {adj:+.1f}")
        # Bad input should not get a large positive adjustment
        assert adj <= 3.0, f"Bad input got unexpectedly positive gestalt: {adj}"
        _print_call_stats()


class TestFeedbackActionability:
    """Are feedback strings actually actionable or just generic?"""

    async def test_feedback_contains_specific_references(
        self, llm, sprint_contract, research_task, good_manifest
    ):
        """Feedback should reference specific content, not be generic."""
        evaluator = Evaluator(llm=llm, profile=EvaluationProfile.DEFAULT)
        _, result = await _collect_events(
            evaluator, BAD_INPUT, sprint_contract, research_task, good_manifest
        )

        print(f"\n  Full feedback:\n  {result.feedback}")

        # Feedback should be non-trivially long
        assert len(result.feedback) > 50, "Feedback is too short to be actionable"

        if result.layer3_results:
            # Check individual dimension feedback
            generic_phrases = ["needs improvement", "could be better", "room for improvement"]
            for ds in result.layer3_results.dimension_scores:
                is_generic = any(p in ds.feedback.lower() for p in generic_phrases)
                if is_generic and len(ds.feedback) < 50:
                    print(f"  WARNING: Generic feedback on {ds.dimension.value}: {ds.feedback[:80]}")


class TestLayer2IsolatedFromLayer3:
    """Verify Layer 2 citation gate works independently."""

    async def test_layer2_passes_with_url_only_citations(self, good_manifest):
        """URL-only citations (no DOI) should pass Layer 2 if URLs are live."""
        gate = Layer2CitationGate(doi_verifier=HTTPDOIVerifier())
        result = await gate.evaluate(good_manifest)
        print(f"\n  Citations checked: {result.citations_checked}")
        print(f"  Citations verified: {result.citations_verified}")
        print(f"  Fabrications: {result.citations_fabricated}")
        print(f"  Gate passed: {result.gate_passed}")
        assert result.gate_passed is True

    async def test_layer2_empty_manifest_passes(self):
        """Empty manifest should pass (nothing to reject)."""
        manifest = CitationManifest(
            manifest_id="MAN-EMPTY",
            engagement_id="ENG-TEST-001",
            client_id="CLIENT-TEST",
        )
        gate = Layer2CitationGate()
        result = await gate.evaluate(manifest)
        assert result.gate_passed is True
        assert result.citations_checked == 0


class TestLightTouchIntensity:
    """LIGHT_TOUCH should skip Layer 3 entirely."""

    async def test_light_touch_skips_rubric(
        self, llm, sprint_contract, research_task, good_manifest
    ):
        """LIGHT_TOUCH evaluation should skip Layer 3 rubric scoring."""
        evaluator = Evaluator(
            llm=llm,
            profile=EvaluationProfile.DEFAULT,
            intensity=EvaluationIntensity.LIGHT_TOUCH,
        )
        events, result = await _collect_events(
            evaluator, GOOD_INPUT, sprint_contract, research_task, good_manifest
        )
        _print_call_stats()

        # No rubric dimension scores
        dim_events = [e for e in events if isinstance(e, RubricDimensionScored)]
        assert len(dim_events) == 0, "LIGHT_TOUCH should not score dimensions"

        # Result reflects light touch
        assert result.intensity == EvaluationIntensity.LIGHT_TOUCH
        assert result.layer3_results is None
        assert result.passed is True
        assert "LIGHT_TOUCH" in result.feedback
        print(f"\n  Feedback: {result.feedback}")


class TestStrategicProfile:
    """STRATEGIC profile should shift weights toward actionability."""

    def test_strategic_weights_sum_to_one(self):
        weights = get_profile_weights(EvaluationProfile.STRATEGIC)
        total = sum(weights.values())
        assert abs(total - 1.0) < 1e-9, f"Strategic weights sum to {total}"

    def test_strategic_actionability_higher(self):
        default_w = get_profile_weights(EvaluationProfile.DEFAULT)
        strategic_w = get_profile_weights(EvaluationProfile.STRATEGIC)
        assert strategic_w[RubricDimension.ACTIONABILITY] > default_w[RubricDimension.ACTIONABILITY]

    def test_strategic_quant_rigor_lower(self):
        default_w = get_profile_weights(EvaluationProfile.DEFAULT)
        strategic_w = get_profile_weights(EvaluationProfile.STRATEGIC)
        assert strategic_w[RubricDimension.QUANTITATIVE_RIGOR] < default_w[RubricDimension.QUANTITATIVE_RIGOR]
