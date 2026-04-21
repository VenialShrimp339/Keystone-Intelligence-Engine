"""Layer 4: Process trajectory evaluation (Section 5.11).

Layers 1-3 evaluate the OUTPUT TEXT. They cannot see a lazy or narrow
research process that happened to produce plausible-sounding prose.
Layer 4 evaluates the PROCESS: which sources were consulted, which
tools were used, how many synthesis rounds ran, and whether the agent
honored the task's anti-confirmatory framing.

Runs one LLM call per evaluation plus deterministic metric extraction
from the agent's pipeline event trail.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from keystone.evaluator.retry import LLMCallable, retry_llm_call
from keystone.events import (
    AnyPipelineEvent,
    FindingSynthesized,
    ResearchComplete,
    SearchCompleted,
    SourceFound,
)
from keystone.llm.parsing import ParseError, safe_llm_json
from keystone.models.agents import AgentInstance
from keystone.models.citations import CitationManifest
from keystone.models.evaluation import Layer4Result, ProcessFlag
from keystone.models.tasks import ResearchTask

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).parent / "prompts"
_PROMPT_FILE = "process_trajectory.md"


def _strip_frontmatter(text: str) -> str:
    """Strip YAML frontmatter (---...---) from a prompt template if present."""
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[end + 5 :]
    return text


# Quality banding thresholds for Citation.quality_score (0-1 scale)
_HIGH_QUALITY_THRESHOLD = 0.75
_MEDIUM_QUALITY_THRESHOLD = 0.5

# Deterministic flag thresholds
_LOW_SOURCE_COUNT_MAX = 4
_LOW_DOMAIN_DIVERSITY_MAX = 2
_LOW_TOOL_UTILIZATION_MAX = 0.34
_MAX_SOURCE_SAMPLE = 12

# Deterministic score penalties applied before blending with the LLM score
_CRITICAL_FLAG_PENALTY = 15.0
_WARNING_FLAG_PENALTY = 5.0
_CRITICAL_FLAGS: frozenset[ProcessFlag] = frozenset(
    {
        ProcessFlag.SINGLE_DOMAIN,
        ProcessFlag.LOW_TOOL_DIVERSITY,
        ProcessFlag.NO_HIGH_CONFIDENCE_CITATIONS,
    }
)

# Synthetic source type label for internal-corpus retrieval hits. The
# retrieval bridge does not emit SourceFound events (those are from
# external MCP tool results), so when SearchCompleted events are
# present we fold a distinct label into the source-type diversity set
# so agents that exercised the internal corpus register as having
# broadened their source base.
_INTERNAL_CORPUS_SOURCE_TYPE = "internal_corpus"


@dataclass(frozen=True)
class ProcessContext:
    """Inputs Layer 4 needs to evaluate the research process of one task.

    The orchestrator builds this by filtering pipeline events to the
    agent that handled the task, then bundling the agent, task, and
    engagement-level issue tree alongside the filtered event list.

    Layer 4 never mutates this context.
    """

    agent_id: str
    task: ResearchTask
    agent: AgentInstance
    events: list[AnyPipelineEvent] = field(default_factory=list)
    issue_tree: dict[str, Any] | None = None


class Layer4Evaluator:
    """Process trajectory evaluator.

    Usage:
        layer4 = Layer4Evaluator(llm=llm_client)
        result = await layer4.evaluate(process_context, citation_manifest)
    """

    def __init__(self, llm: LLMCallable) -> None:
        self._llm = llm

    async def evaluate(
        self,
        context: ProcessContext,
        manifest: CitationManifest,
    ) -> Layer4Result:
        metrics = _compute_deterministic_metrics(context, manifest)
        deterministic_flags = _compute_deterministic_flags(metrics, context)

        llm_assessment = await self._run_llm_assessment(context, metrics, deterministic_flags)

        combined_flags = _merge_flags(deterministic_flags, llm_assessment.flags)
        qualitative = llm_assessment.score
        process_quality_score = _compute_process_quality_score(qualitative, combined_flags)

        return Layer4Result(
            source_count=metrics["source_count"],
            unique_domains=metrics["unique_domains"],
            source_type_diversity=metrics["source_type_diversity"],
            assigned_tools=list(metrics["assigned_tools"]),
            tools_used=list(metrics["tools_used"]),
            tool_utilization=metrics["tool_utilization"],
            round_count=metrics["round_count"],
            issue_tree_branches_covered=list(metrics["branches_covered"]),
            issue_tree_branches_missed=list(metrics["branches_missed"]),
            citation_quality_distribution=dict(metrics["citation_quality"]),
            qualitative_score=qualitative,
            rationale=llm_assessment.rationale,
            missed_inquiries=list(llm_assessment.missed_inquiries),
            skepticism_assessment=llm_assessment.skepticism_assessment,
            process_quality_score=process_quality_score,
            process_flags=[flag.value for flag in combined_flags],
        )

    async def _run_llm_assessment(
        self,
        context: ProcessContext,
        metrics: dict[str, Any],
        deterministic_flags: list[ProcessFlag],
    ) -> _LLMAssessment:
        template = _strip_frontmatter((_PROMPTS_DIR / _PROMPT_FILE).read_text())
        prompt = _fill_prompt(template, context, metrics, deterministic_flags)

        try:
            raw = await retry_llm_call(self._llm, prompt, description="process_trajectory")
        except RuntimeError as exc:
            logger.warning(
                "Layer 4 LLM assessment failed for task %s: %s. Using degraded assessment.",
                context.task.id,
                exc,
            )
            return _LLMAssessment(
                score=50.0,
                rationale="LLM assessment unavailable; relying on deterministic metrics.",
                missed_inquiries=[],
                skepticism_assessment="Unknown — LLM assessment could not be completed.",
                flags=[],
            )

        try:
            parsed_any = safe_llm_json(raw, required_keys=("qualitative_score",))
        except ParseError:
            logger.warning(
                "Layer 4 assessment JSON for task %s was not parseable: %.120s...",
                context.task.id,
                raw[:120],
            )
            return _LLMAssessment(
                score=50.0,
                rationale="LLM assessment returned unparseable output.",
                missed_inquiries=[],
                skepticism_assessment="Unknown — LLM output was not valid JSON.",
                flags=[],
            )

        if not isinstance(parsed_any, dict):
            logger.warning(
                "Layer 4 assessment for task %s was a list, expected object.",
                context.task.id,
            )
            return _LLMAssessment(
                score=50.0,
                rationale="LLM assessment returned an array; expected an object.",
                missed_inquiries=[],
                skepticism_assessment="Unknown — LLM output shape was invalid.",
                flags=[],
            )
        parsed: dict[str, Any] = parsed_any

        score = _clamp(float(parsed.get("qualitative_score", 50)), 0.0, 100.0)
        rationale = str(parsed.get("rationale", "")).strip() or "No rationale provided."
        skepticism = str(parsed.get("skepticism_assessment", "")).strip() or (
            "No skepticism assessment provided."
        )
        missed_raw = parsed.get("missed_inquiries", [])
        missed = [str(item).strip() for item in missed_raw if str(item).strip()]

        flag_strings = parsed.get("additional_flags", []) or []
        llm_flags: list[ProcessFlag] = []
        for raw_flag in flag_strings:
            try:
                llm_flags.append(ProcessFlag(str(raw_flag).strip()))
            except ValueError:
                logger.debug("Ignoring unrecognized Layer 4 flag from LLM: %r", raw_flag)

        return _LLMAssessment(
            score=score,
            rationale=rationale,
            missed_inquiries=missed,
            skepticism_assessment=skepticism,
            flags=llm_flags,
        )


@dataclass(frozen=True)
class _LLMAssessment:
    score: float
    rationale: str
    missed_inquiries: list[str]
    skepticism_assessment: str
    flags: list[ProcessFlag]


# ---------------------------------------------------------------------------
# Deterministic metric extraction
# ---------------------------------------------------------------------------


def _compute_deterministic_metrics(
    context: ProcessContext,
    manifest: CitationManifest,
) -> dict[str, Any]:
    events = context.events
    assigned_tools = list(context.task.assigned_tools)

    source_events = [e for e in events if isinstance(e, SourceFound)]
    synthesis_events = [e for e in events if isinstance(e, FindingSynthesized)]
    complete_events = [e for e in events if isinstance(e, ResearchComplete)]
    search_events = [e for e in events if isinstance(e, SearchCompleted)]

    # source_count: prefer ResearchComplete's authoritative count, fall back
    # to the SourceFound event count. The ResearchComplete count includes
    # non-URL sources (raw tool results) that SourceFound also emits for.
    if complete_events:
        source_count = max(e.sources_consulted for e in complete_events)
    else:
        source_count = len(source_events)

    unique_domains = len({_extract_domain(e.url) for e in source_events if e.url})

    source_types = {e.source_type for e in source_events if e.source_type}
    # A SearchCompleted event represents a successful retrieval against
    # the internal corpus. Count it as a distinct source type so agents
    # that exercised internal retrieval register as having broader
    # source diversity than agents that only used external MCP tools.
    retrieval_tools_used = {e.tool_name for e in search_events}
    if retrieval_tools_used:
        source_types = source_types | {_INTERNAL_CORPUS_SOURCE_TYPE}
    source_type_diversity = len(source_types)

    tools_used_set: set[str] = set()
    for e in source_events:
        stype = e.source_type
        if not stype:
            continue
        if stype in assigned_tools:
            tools_used_set.add(stype)
            continue
        # Shallow-mode URLs carry the tool name in their scheme
        # (tool://<tool_name>/round_N).
        if e.url.startswith("tool://"):
            parsed = urlparse(e.url)
            host = parsed.netloc or parsed.path.lstrip("/").split("/", 1)[0]
            if host in assigned_tools:
                tools_used_set.add(host)

    # Internal retrieval is a system-owned capability available to every
    # agent (not surfaced through assigned_tools). When an agent emits a
    # SearchCompleted event it has used one of the retrieval tools; fold
    # those into both numerator and denominator so tool_utilization
    # reflects the broadened capability surface without exceeding 1.0.
    utilization_assigned = list(assigned_tools) + sorted(retrieval_tools_used)
    utilization_used = sorted(tools_used_set | retrieval_tools_used)
    tool_utilization = (
        len(utilization_used) / len(utilization_assigned) if utilization_assigned else 0.0
    )
    tools_used = sorted(tools_used_set)

    round_count = len(synthesis_events)

    branches_covered, branches_missed = _compute_branch_coverage(context)

    citation_quality = _bucket_citation_quality(manifest)

    return {
        "source_count": source_count,
        "unique_domains": unique_domains,
        "source_type_diversity": source_type_diversity,
        "source_types": sorted(source_types),
        "assigned_tools": assigned_tools,
        "tools_used": tools_used,
        "tool_utilization": tool_utilization,
        "round_count": round_count,
        "branches_covered": branches_covered,
        "branches_missed": branches_missed,
        "citation_quality": citation_quality,
        "source_events": source_events,
        "retrieval_calls": len(search_events),
        "retrieval_tools_used": sorted(retrieval_tools_used),
    }


def _extract_domain(url: str) -> str:
    """Return a normalized host segment for diversity counting.

    `tool://<tool>/round_N` URLs (shallow mode placeholder scheme) return
    the tool name so they do not inflate domain diversity beyond the
    distinct tools actually exercised.
    """
    if not url:
        return ""
    parsed = urlparse(url)
    host = parsed.netloc or parsed.path.lstrip("/").split("/", 1)[0]
    return host.lower().removeprefix("www.")


def _bucket_citation_quality(manifest: CitationManifest) -> dict[str, int]:
    buckets = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for cit in manifest.citations:
        score = cit.quality_score
        if score >= _HIGH_QUALITY_THRESHOLD:
            buckets["HIGH"] += 1
        elif score >= _MEDIUM_QUALITY_THRESHOLD:
            buckets["MEDIUM"] += 1
        else:
            buckets["LOW"] += 1
    return buckets


def _compute_branch_coverage(context: ProcessContext) -> tuple[list[str], list[str]]:
    branch_id = context.task.issue_tree_branch_id
    covered: list[str] = [branch_id] if branch_id else []
    missed: list[str] = []

    if not branch_id or not context.issue_tree:
        return covered, missed

    siblings = _find_sibling_branch_ids(context.issue_tree, branch_id)
    missed = [sid for sid in siblings if sid != branch_id]
    return covered, missed


def _find_sibling_branch_ids(tree: dict[str, Any], branch_id: str) -> list[str]:
    """Return sibling branch IDs of the given branch, if the tree contains it."""
    root = tree.get("root") if "root" in tree else tree
    return _search_siblings(root, branch_id, parent_children=None)


def _search_siblings(
    node: dict[str, Any] | None,
    target_id: str,
    parent_children: list[dict[str, Any]] | None,
) -> list[str]:
    if node is None or not isinstance(node, dict):
        return []

    if node.get("id") == target_id and parent_children is not None:
        return [c.get("id", "") for c in parent_children if c.get("id")]

    for child in node.get("children", []) or []:
        result = _search_siblings(child, target_id, node.get("children") or [])
        if result:
            return result
    return []


# ---------------------------------------------------------------------------
# Flag computation
# ---------------------------------------------------------------------------


def _compute_deterministic_flags(
    metrics: dict[str, Any],
    context: ProcessContext,
) -> list[ProcessFlag]:
    flags: list[ProcessFlag] = []

    if metrics["source_count"] > 0 and metrics["source_type_diversity"] <= 1:
        flags.append(ProcessFlag.SINGLE_SOURCE_TYPE)

    if metrics["source_count"] > 0 and metrics["unique_domains"] == 1:
        flags.append(ProcessFlag.SINGLE_DOMAIN)
    elif metrics["source_count"] >= 3 and metrics["unique_domains"] <= _LOW_DOMAIN_DIVERSITY_MAX:
        flags.append(ProcessFlag.LOW_DOMAIN_DIVERSITY)

    if metrics["round_count"] <= 1:
        flags.append(ProcessFlag.NO_MULTI_ROUND)

    if metrics["assigned_tools"] and metrics["tool_utilization"] <= _LOW_TOOL_UTILIZATION_MAX:
        flags.append(ProcessFlag.LOW_TOOL_DIVERSITY)

    if metrics["source_count"] <= _LOW_SOURCE_COUNT_MAX:
        flags.append(ProcessFlag.LOW_SOURCE_COUNT)

    citation_quality = metrics["citation_quality"]
    if sum(citation_quality.values()) > 0 and citation_quality["HIGH"] == 0:
        flags.append(ProcessFlag.NO_HIGH_CONFIDENCE_CITATIONS)

    branch_id = context.task.issue_tree_branch_id
    if not branch_id:
        flags.append(ProcessFlag.COVERAGE_GAP)

    return flags


def _merge_flags(
    deterministic: list[ProcessFlag],
    llm: list[ProcessFlag],
) -> list[ProcessFlag]:
    seen: set[ProcessFlag] = set()
    merged: list[ProcessFlag] = []
    for flag in list(deterministic) + list(llm):
        if flag in seen:
            continue
        seen.add(flag)
        merged.append(flag)
    return merged


def _compute_process_quality_score(
    qualitative: float,
    flags: Iterable[ProcessFlag],
) -> float:
    penalty = 0.0
    for flag in flags:
        penalty += _CRITICAL_FLAG_PENALTY if flag in _CRITICAL_FLAGS else _WARNING_FLAG_PENALTY
    deterministic_score = _clamp(100.0 - penalty, 0.0, 100.0)
    blended = 0.5 * deterministic_score + 0.5 * qualitative
    return round(_clamp(blended, 0.0, 100.0), 2)


# ---------------------------------------------------------------------------
# Prompt rendering
# ---------------------------------------------------------------------------


def _fill_prompt(
    template: str,
    context: ProcessContext,
    metrics: dict[str, Any],
    deterministic_flags: list[ProcessFlag],
) -> str:
    task = context.task
    assigned_tools = ", ".join(metrics["assigned_tools"]) or "(none)"
    tools_used = ", ".join(metrics["tools_used"]) or "(none)"
    citation_quality = _format_quality_dict(metrics["citation_quality"])
    source_sample = _format_source_sample(metrics["source_events"])
    acceptance = "\n".join(f"- {c}" for c in task.acceptance_criteria) or "- (none specified)"
    flag_list = "\n".join(f"- {f.value}" for f in deterministic_flags) or "(none)"
    missed_branches = ", ".join(metrics["branches_missed"]) or "(none identified)"
    assigned_branch = task.issue_tree_branch_id or "(unassigned)"

    tool_utilization_pct = round(metrics["tool_utilization"] * 100)

    return (
        template.replace("{{task_description}}", task.description)
        .replace("{{anti_confirmatory_framing}}", task.anti_confirmatory_framing)
        .replace("{{acceptance_criteria}}", acceptance)
        .replace("{{assigned_tools}}", assigned_tools)
        .replace("{{tools_used}}", tools_used)
        .replace("{{source_count}}", str(metrics["source_count"]))
        .replace("{{unique_domains}}", str(metrics["unique_domains"]))
        .replace("{{source_type_diversity}}", str(metrics["source_type_diversity"]))
        .replace("{{round_count}}", str(metrics["round_count"]))
        .replace("{{tool_utilization_pct}}", str(tool_utilization_pct))
        .replace("{{citation_quality}}", citation_quality)
        .replace("{{source_sample}}", source_sample)
        .replace("{{assigned_branch}}", assigned_branch)
        .replace("{{missed_branches}}", missed_branches)
        .replace("{{deterministic_flags}}", flag_list)
    )


def _format_quality_dict(buckets: dict[str, int]) -> str:
    parts = [f"{tier}: {buckets.get(tier, 0)}" for tier in ("HIGH", "MEDIUM", "LOW")]
    return ", ".join(parts)


def _format_source_sample(events: list[SourceFound]) -> str:
    if not events:
        return "(no SourceFound events were emitted by this agent.)"
    lines: list[str] = []
    for e in events[:_MAX_SOURCE_SAMPLE]:
        domain = _extract_domain(e.url) or "(no domain)"
        lines.append(f"- {e.source_type or 'unknown'} | {domain} | quality={e.quality_score:.2f}")
    if len(events) > _MAX_SOURCE_SAMPLE:
        lines.append(f"- ... ({len(events) - _MAX_SOURCE_SAMPLE} more sources omitted)")
    return "\n".join(lines)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
