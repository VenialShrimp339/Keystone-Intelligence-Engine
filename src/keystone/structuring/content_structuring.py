"""Pipeline-L2 ContentStructurer: confidence map + findings -> StructuredOutline.

Satisfies ContentStructuringContract. Deterministic structuring plus one
LLM call per task for sprint contract negotiation (delegated to
`SprintContractGenerator`). Everything else is pure Python.

The structurer produces three artifacts:

1. `StructuredOutline` — outline for the renderer to traverse. Sections
   ordered per consulting brief conventions: executive summary ->
   framework analysis -> branch findings -> moderate / weak / contested
   uncertainty -> gaps -> absence.
2. Per-task section text — analytical narrative the Evaluator scores.
   Lede, evidence chain, analytical significance, absence report.
3. Per-task `SprintContract` — quality criteria for the L4 rubric.
"""

from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from typing import TYPE_CHECKING

from keystone.events import (
    OutlineGenerated,
    SectionDrafted,
    SprintContractProposed,
)
from keystone.models.evaluation import SprintContract
from keystone.models.structuring import (
    AnalyticalFramework,
    FrameworkHint,
    OutlineItem,
    OutlineItemType,
    OutlineSectionType,
    StructuredOutline,
    StructuredSection,
)
from keystone.structuring.framework_selector import (
    frameworks_for_engagement,
    primary_framework,
)
from keystone.structuring.section_text import render_task_section_text

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from typing import Any

    from keystone.evaluator.sprint_contract import SprintContractGenerator
    from keystone.events import AnyPipelineEvent
    from keystone.models.confidence import ConfidenceMap
    from keystone.models.research import EngagementSpec, StructuredFinding
    from keystone.models.tasks import ResearchTask

logger = logging.getLogger(__name__)


class ContentStructurer:
    """L2 Content Structuring.

    Usage::

        structurer = ContentStructurer(sprint_contract_generator=scg)
        async for event in structurer.structure(
            confidence_map, findings, spec, tasks, eid, client_id
        ):
            yield event
        outline = await structurer.get_outline()
        text = await structurer.get_task_section_text(task.id)
        contract = await structurer.get_sprint_contract(task.id)
    """

    def __init__(
        self,
        sprint_contract_generator: SprintContractGenerator | None = None,
        frameworks_override: list[FrameworkHint] | None = None,
    ) -> None:
        self._sprint_contract_generator = sprint_contract_generator
        self._frameworks_override = frameworks_override
        self._outline: StructuredOutline | None = None
        self._section_texts: dict[str, str] = {}
        self._sprint_contracts: dict[str, SprintContract] = {}
        # Task IDs whose sprint contract came from the fallback path rather
        # than a successful generator call. The orchestrator reads this set
        # after ``structure()`` to emit a ``sprint_contract_fallback``
        # governance flag per task — silent fallback was the audit finding.
        self._fallback_task_ids: set[str] = set()

    async def structure(
        self,
        confidence_map: ConfidenceMap,
        findings: list[StructuredFinding],
        spec: EngagementSpec,
        tasks: list[ResearchTask],
        engagement_id: str,
        client_id: str,
    ) -> AsyncIterator[AnyPipelineEvent]:
        """Build the outline, draft per-task section text, negotiate contracts.

        Yields:
            SectionDrafted: one per renderable task.
            SprintContractProposed: one per renderable task (after the
                generator returns; skipped if no generator is wired in).
            OutlineGenerated: one at the end, after all tasks processed.
        """
        frameworks = frameworks_for_engagement(
            spec.research_spec.engagement_type,
            override=self._frameworks_override,
        )
        framework = primary_framework(
            spec.research_spec.engagement_type,
            override=self._frameworks_override,
        )
        finding_by_task = {finding.task_id: finding for finding in findings}

        for task in tasks:
            finding = finding_by_task.get(task.id)
            section_text = render_task_section_text(
                task=task,
                finding=finding,
                framework=framework,
                engagement_type_label=spec.research_spec.engagement_type.value,
                confidence_map=confidence_map,
            )
            self._section_texts[task.id] = section_text

            claim_count = len(finding.claims) if finding else 0
            yield SectionDrafted(
                event_id=_uid(),
                engagement_id=engagement_id,
                client_id=client_id,
                section_id=f"section_{task.id}",
                section_title=task.deliverable_destination,
                claim_count=claim_count,
            )

            if self._sprint_contract_generator is not None:
                contract = await self._negotiate_contract(task, spec)
                self._sprint_contracts[task.id] = contract
                yield SprintContractProposed(
                    event_id=_uid(),
                    engagement_id=engagement_id,
                    client_id=client_id,
                    section_id=contract.section_id,
                    criteria_count=len(contract.acceptance_criteria),
                )

        outline = self._build_outline(
            confidence_map=confidence_map,
            findings=findings,
            spec=spec,
            tasks=tasks,
            frameworks=frameworks,
            framework=framework,
        )
        self._outline = outline

        yield OutlineGenerated(
            event_id=_uid(),
            engagement_id=engagement_id,
            client_id=client_id,
            section_count=len(outline.sections),
        )

    async def get_outline(self) -> StructuredOutline:
        """Return the built outline. Raises if structure() has not completed."""
        if self._outline is None:
            raise RuntimeError("structure() must complete before get_outline()")
        return self._outline

    async def get_task_section_text(self, task_id: str) -> str:
        """Return the per-task section text. Empty string if task was skipped."""
        return self._section_texts.get(task_id, "")

    async def get_sprint_contract(self, task_id: str) -> SprintContract | None:
        """Return the negotiated contract for a task, or None if not negotiated."""
        return self._sprint_contracts.get(task_id)

    async def get_sprint_contracts(self) -> list[SprintContract]:
        """Return all negotiated contracts. Protocol conformance."""
        return list(self._sprint_contracts.values())

    # ------------------------------------------------------------------
    # Internal: sprint-contract negotiation
    # ------------------------------------------------------------------

    async def _negotiate_contract(self, task: ResearchTask, spec: EngagementSpec) -> SprintContract:
        """Delegate to the wired SprintContractGenerator.

        On generator failure, fall back to a task-derived contract so L2 never
        blocks L4 on an LLM mishap. The fallback contract is functionally
        equivalent to what `SprintContractGenerator.generate` produces when
        the LLM returns an unrecognized JSON shape. The task ID is recorded
        in ``self._fallback_task_ids`` so the orchestrator can emit a WARN
        governance flag for operators — silent fallback was the audit
        finding.
        """
        assert self._sprint_contract_generator is not None
        try:
            return await self._sprint_contract_generator.generate(task, spec)
        except Exception as exc:
            logger.warning(
                "Sprint contract generation failed for task %s: %s. "
                "Falling back to task-derived contract.",
                task.id,
                exc,
            )
            self._fallback_task_ids.add(task.id)
            return SprintContract(
                section_id=f"section_{task.id}",
                engagement_id=task.engagement_id,
                client_id=task.client_id,
                task_id=task.id,
                section_title=task.deliverable_destination,
                acceptance_criteria=list(task.acceptance_criteria),
                dimension_emphasis={},
                mandatory_elements=[],
                anti_patterns=[],
            )

    def get_fallback_task_ids(self) -> set[str]:
        """Return task IDs whose sprint contract came from the fallback path.

        Orchestrator reads this after ``structure()`` to emit per-task
        governance flags. Empty set is the happy path.
        """
        return set(self._fallback_task_ids)

    # ------------------------------------------------------------------
    # Internal: outline construction
    # ------------------------------------------------------------------

    def _build_outline(
        self,
        *,
        confidence_map: ConfidenceMap,
        findings: list[StructuredFinding],
        spec: EngagementSpec,
        tasks: list[ResearchTask],
        frameworks: list[FrameworkHint],
        framework: AnalyticalFramework | None,
    ) -> StructuredOutline:
        task_by_id = {task.id: task for task in tasks}
        branch_titles = _collect_leaf_titles(spec.issue_tree)
        citation_ids_by_task = _citation_ids_by_task(findings)

        sections: list[StructuredSection] = []

        exec_section = _executive_summary_section(confidence_map, task_by_id, citation_ids_by_task)
        if exec_section is not None:
            sections.append(exec_section)

        framework_section = _framework_analysis_section(frameworks, framework)
        if framework_section is not None:
            sections.append(framework_section)

        sections.extend(_branch_sections(findings, task_by_id, branch_titles, framework))

        moderate_section = _moderate_section(confidence_map, task_by_id, citation_ids_by_task)
        if moderate_section is not None:
            sections.append(moderate_section)

        weak_section = _weak_section(confidence_map, task_by_id, citation_ids_by_task)
        if weak_section is not None:
            sections.append(weak_section)

        contested_section = _contested_section(confidence_map, task_by_id, citation_ids_by_task)
        if contested_section is not None:
            sections.append(contested_section)

        gap_section = _gap_section(confidence_map, task_by_id)
        if gap_section is not None:
            sections.append(gap_section)

        insufficient_section = _insufficient_section(
            confidence_map, task_by_id, citation_ids_by_task
        )
        if insufficient_section is not None:
            sections.append(insufficient_section)

        absence_section = _absence_section(findings, task_by_id)
        if absence_section is not None:
            sections.append(absence_section)

        known_branch_ids = {
            task.issue_tree_branch_id for task in tasks if task.issue_tree_branch_id
        }
        covered_branch_ids = {
            section.issue_tree_branch_id
            for section in sections
            if section.section_type == OutlineSectionType.BRANCH and section.issue_tree_branch_id
        }
        uncovered_branch_ids = sorted((set(branch_titles) | known_branch_ids) - covered_branch_ids)

        rendered_task_ids = sorted({f.task_id for f in findings})

        return StructuredOutline(
            engagement_id=spec.research_spec.engagement_id,
            client_id=spec.research_spec.client_id,
            engagement_type=spec.research_spec.engagement_type.value,
            frameworks=list(frameworks),
            sections=sections,
            rendered_task_ids=rendered_task_ids,
            uncovered_branch_ids=uncovered_branch_ids,
        )


# ----------------------------------------------------------------------
# Post-evaluation filtering (for the orchestrator render path)
# ----------------------------------------------------------------------


def filter_outline_by_passed_tasks(
    outline: StructuredOutline,
    passed_task_ids: set[str],
) -> StructuredOutline:
    """Drop outline items whose task_ids do not intersect passed_task_ids.

    Items with empty task_ids (framework notes, synthesized gaps without
    provenance) are kept: they carry no task-specific failure risk.
    Sections that end up empty after filtering are dropped.
    """
    filtered_sections: list[StructuredSection] = []
    for section in outline.sections:
        kept_items: list[OutlineItem] = []
        for item in section.items:
            if not item.task_ids:
                kept_items.append(item)
                continue
            if passed_task_ids.intersection(item.task_ids):
                surviving = [tid for tid in item.task_ids if tid in passed_task_ids]
                kept_items.append(item.model_copy(update={"task_ids": surviving}))

        if not kept_items:
            continue

        filtered_sections.append(_rebuild_section_aggregates(section, kept_items))

    rendered_task_ids = sorted(set(outline.rendered_task_ids).intersection(passed_task_ids))

    return StructuredOutline(
        engagement_id=outline.engagement_id,
        client_id=outline.client_id,
        engagement_type=outline.engagement_type,
        frameworks=list(outline.frameworks),
        sections=filtered_sections,
        rendered_task_ids=rendered_task_ids,
        uncovered_branch_ids=list(outline.uncovered_branch_ids),
    )


def _rebuild_section_aggregates(
    section: StructuredSection,
    items: list[OutlineItem],
) -> StructuredSection:
    task_ids = sorted({tid for item in items for tid in item.task_ids})
    claim_ids = sorted({item.item_id for item in items if item.item_id})
    citation_ids = sorted({cid for item in items for cid in item.citation_ids})
    return section.model_copy(
        update={
            "items": items,
            "task_ids": task_ids,
            "claim_ids": claim_ids,
            "citation_ids": citation_ids,
        }
    )


# ----------------------------------------------------------------------
# Section builders
# ----------------------------------------------------------------------


def _executive_summary_section(
    confidence_map: ConfidenceMap,
    task_by_id: dict[str, ResearchTask],
    citation_ids_by_task: dict[str, set[str]],
) -> StructuredSection | None:
    claims = confidence_map.high_confidence_above_80pct
    if not claims:
        return None

    items: list[OutlineItem] = []
    for claim in claims:
        task_ids = _claim_task_ids(
            claim.aggregated_claim_id,
            list(claim.task_ids),
            confidence_map.provenance_index,
        )
        items.append(
            OutlineItem(
                item_id=claim.aggregated_claim_id,
                item_type=OutlineItemType.CLAIM,
                text=claim.claim,
                task_ids=task_ids,
                citation_ids=_supporting_citation_ids(task_ids, citation_ids_by_task),
                issue_tree_branch_id=_single_branch_id(task_ids, task_by_id),
                note=(f"Robustness: {claim.robustness} | Curmudgeon: {claim.curmudgeon_challenge}"),
            )
        )

    return _make_section(
        section_id="executive_summary",
        section_type=OutlineSectionType.EXECUTIVE_SUMMARY,
        title="Executive Summary",
        items=items,
    )


def _framework_analysis_section(
    frameworks: list[FrameworkHint],
    primary: AnalyticalFramework | None,
) -> StructuredSection | None:
    if not frameworks:
        return None

    items: list[OutlineItem] = []
    for hint in frameworks:
        label = hint.framework.value.replace("_", " ").title()
        marker = "primary" if hint.mandatory else "augmenting"
        items.append(
            OutlineItem(
                item_id=f"framework_{hint.framework.value}",
                item_type=OutlineItemType.FRAMEWORK_NOTE,
                text=f"{label} ({marker}): {hint.rationale}",
            )
        )

    return StructuredSection(
        section_id="framework_analysis",
        section_type=OutlineSectionType.FRAMEWORK_ANALYSIS,
        title="Analytical Framework",
        framework=primary,
        task_ids=[],
        claim_ids=[],
        citation_ids=[],
        items=items,
    )


def _branch_sections(
    findings: list[StructuredFinding],
    task_by_id: dict[str, ResearchTask],
    branch_titles: dict[str, str],
    framework: AnalyticalFramework | None,
) -> list[StructuredSection]:
    branch_items: dict[str | None, list[OutlineItem]] = defaultdict(list)
    for finding in findings:
        task = task_by_id.get(finding.task_id)
        branch_id = task.issue_tree_branch_id if task else None
        for claim in finding.claims:
            citation_ids = claim.citation_ids or [
                citation.citation_id for citation in claim.citations
            ]
            branch_items[branch_id].append(
                OutlineItem(
                    item_id=claim.claim_id,
                    item_type=OutlineItemType.CLAIM,
                    text=claim.text,
                    task_ids=[finding.task_id],
                    citation_ids=citation_ids,
                    issue_tree_branch_id=branch_id,
                    confidence=claim.confidence,
                    confidence_tier=claim.confidence_tier,
                    evidence=claim.evidence,
                    caveats=list(claim.caveats),
                )
            )

    sections: list[StructuredSection] = []
    for branch_id, items in sorted(branch_items.items(), key=lambda entry: entry[0] or ""):
        if not items:
            continue
        if branch_id and branch_id in branch_titles:
            title = branch_titles[branch_id]
        else:
            title = branch_id or "Key Findings"
        section_id = f"branch_{branch_id or 'general'}"
        section = _make_section(
            section_id=section_id,
            section_type=OutlineSectionType.BRANCH,
            title=title,
            items=items,
            issue_tree_branch_id=branch_id,
        )
        sections.append(section.model_copy(update={"framework": framework}))
    return sections


def _moderate_section(
    confidence_map: ConfidenceMap,
    task_by_id: dict[str, ResearchTask],
    citation_ids_by_task: dict[str, set[str]],
) -> StructuredSection | None:
    claims = confidence_map.moderate_confidence_60_80pct
    if not claims:
        return None

    items: list[OutlineItem] = []
    for claim in claims:
        task_ids = _claim_task_ids(
            claim.aggregated_claim_id,
            list(claim.task_ids),
            confidence_map.provenance_index,
        )
        items.append(
            OutlineItem(
                item_id=claim.aggregated_claim_id,
                item_type=OutlineItemType.CLAIM,
                text=claim.claim,
                task_ids=task_ids,
                citation_ids=_supporting_citation_ids(task_ids, citation_ids_by_task),
                issue_tree_branch_id=_single_branch_id(task_ids, task_by_id),
                note=(f"Dissent: {claim.dissent} | Sensitivity: {claim.sensitivity}"),
            )
        )

    return _make_section(
        section_id="moderate_confidence",
        section_type=OutlineSectionType.MODERATE,
        title="Moderate Confidence Findings (60-80%)",
        items=items,
    )


def _weak_section(
    confidence_map: ConfidenceMap,
    task_by_id: dict[str, ResearchTask],
    citation_ids_by_task: dict[str, set[str]],
) -> StructuredSection | None:
    claims = confidence_map.weak_confidence_50_60pct
    if not claims:
        return None

    items: list[OutlineItem] = []
    for claim in claims:
        task_ids = _claim_task_ids(
            claim.aggregated_claim_id,
            list(claim.task_ids),
            confidence_map.provenance_index,
        )
        items.append(
            OutlineItem(
                item_id=claim.aggregated_claim_id,
                item_type=OutlineItemType.CLAIM,
                text=claim.claim,
                task_ids=task_ids,
                citation_ids=_supporting_citation_ids(task_ids, citation_ids_by_task),
                issue_tree_branch_id=_single_branch_id(task_ids, task_by_id),
                note=(f"Key issue: {claim.key_issue} | Recommendation: {claim.recommendation}"),
            )
        )

    return _make_section(
        section_id="weak_confidence",
        section_type=OutlineSectionType.WEAK,
        title="Weak Confidence (50-60%)",
        items=items,
    )


def _contested_section(
    confidence_map: ConfidenceMap,
    task_by_id: dict[str, ResearchTask],
    citation_ids_by_task: dict[str, set[str]],
) -> StructuredSection | None:
    claims = confidence_map.contested_below_50pct
    if not claims:
        return None

    items: list[OutlineItem] = []
    for claim in claims:
        task_ids = _claim_task_ids(
            claim.aggregated_claim_id,
            list(claim.task_ids),
            confidence_map.provenance_index,
        )
        items.append(
            OutlineItem(
                item_id=claim.aggregated_claim_id,
                item_type=OutlineItemType.CLAIM,
                text=claim.claim,
                task_ids=task_ids,
                citation_ids=_supporting_citation_ids(task_ids, citation_ids_by_task),
                issue_tree_branch_id=_single_branch_id(task_ids, task_by_id),
                note=(
                    f"Key disagreement: {claim.key_disagreement} | "
                    f"Steelmanned opposing view: {claim.steelmanned_opposing_view}"
                ),
            )
        )

    return _make_section(
        section_id="contested_claims",
        section_type=OutlineSectionType.CONTESTED,
        title="Contested Claims (<50%)",
        items=items,
    )


def _gap_section(
    confidence_map: ConfidenceMap,
    task_by_id: dict[str, ResearchTask],
) -> StructuredSection | None:
    if not confidence_map.gaps_identified:
        return None

    items: list[OutlineItem] = []
    for index, gap in enumerate(confidence_map.gaps_identified, start=1):
        task_ids = list(confidence_map.gap_provenance.get(gap, []))
        items.append(
            OutlineItem(
                item_id=f"gap_{index}",
                item_type=OutlineItemType.GAP,
                text=gap,
                task_ids=task_ids,
                citation_ids=[],
                issue_tree_branch_id=_single_branch_id(task_ids, task_by_id),
            )
        )

    return _make_section(
        section_id="research_gaps",
        section_type=OutlineSectionType.GAPS,
        title="Identified Gaps",
        items=items,
    )


def _insufficient_section(
    confidence_map: ConfidenceMap,
    task_by_id: dict[str, ResearchTask],
    citation_ids_by_task: dict[str, set[str]],
) -> StructuredSection | None:
    claims = confidence_map.insufficient_evidence
    if not claims:
        return None

    items: list[OutlineItem] = []
    for claim in claims:
        task_ids = _claim_task_ids(
            claim.aggregated_claim_id,
            list(claim.task_ids),
            confidence_map.provenance_index,
        )
        items.append(
            OutlineItem(
                item_id=claim.aggregated_claim_id,
                item_type=OutlineItemType.INSUFFICIENT,
                text=claim.claim,
                task_ids=task_ids,
                citation_ids=_supporting_citation_ids(task_ids, citation_ids_by_task),
                issue_tree_branch_id=_single_branch_id(task_ids, task_by_id),
                note=f"Reason: {claim.reason} | Priority: {claim.priority}",
            )
        )

    return _make_section(
        section_id="insufficient_evidence",
        section_type=OutlineSectionType.INSUFFICIENT,
        title="Insufficient Evidence",
        items=items,
    )


def _absence_section(
    findings: list[StructuredFinding],
    task_by_id: dict[str, ResearchTask],
) -> StructuredSection | None:
    items: list[OutlineItem] = []
    for finding in findings:
        task = task_by_id.get(finding.task_id)
        branch_id = task.issue_tree_branch_id if task else None
        for index, text in enumerate(finding.absence_report, start=1):
            items.append(
                OutlineItem(
                    item_id=f"absence_{finding.task_id}_{index}",
                    item_type=OutlineItemType.ABSENCE,
                    text=text,
                    task_ids=[finding.task_id],
                    citation_ids=[],
                    issue_tree_branch_id=branch_id,
                )
            )
    if not items:
        return None
    return _make_section(
        section_id="absence_reports",
        section_type=OutlineSectionType.ABSENCE,
        title="Absence Reports",
        items=items,
    )


# ----------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------


def _make_section(
    *,
    section_id: str,
    section_type: OutlineSectionType,
    title: str,
    items: list[OutlineItem],
    issue_tree_branch_id: str | None = None,
) -> StructuredSection:
    task_ids = sorted({tid for item in items for tid in item.task_ids})
    claim_ids = sorted({item.item_id for item in items if item.item_id})
    citation_ids = sorted({cid for item in items for cid in item.citation_ids})
    return StructuredSection(
        section_id=section_id,
        section_type=section_type,
        title=title,
        issue_tree_branch_id=issue_tree_branch_id,
        task_ids=task_ids,
        claim_ids=claim_ids,
        citation_ids=citation_ids,
        items=items,
    )


def _citation_ids_by_task(
    findings: list[StructuredFinding],
) -> dict[str, set[str]]:
    result: dict[str, set[str]] = defaultdict(set)
    for finding in findings:
        for claim in finding.claims:
            citation_ids = claim.citation_ids or [
                citation.citation_id for citation in claim.citations
            ]
            result[finding.task_id].update(citation_ids)
    return result


def _supporting_citation_ids(
    task_ids: list[str],
    citation_ids_by_task: dict[str, set[str]],
) -> list[str]:
    return sorted(
        {
            citation_id
            for task_id in task_ids
            for citation_id in citation_ids_by_task.get(task_id, set())
        }
    )


def _single_branch_id(
    task_ids: list[str],
    task_by_id: dict[str, ResearchTask],
) -> str | None:
    branch_ids = {
        task_by_id[tid].issue_tree_branch_id
        for tid in task_ids
        if tid in task_by_id and task_by_id[tid].issue_tree_branch_id
    }
    if len(branch_ids) == 1:
        return next(iter(branch_ids))
    return None


def _claim_task_ids(
    aggregated_claim_id: str | None,
    task_ids: list[str],
    provenance_index: dict[str, list[str]],
) -> list[str]:
    if task_ids:
        return list(task_ids)
    if aggregated_claim_id and aggregated_claim_id in provenance_index:
        return list(provenance_index[aggregated_claim_id])
    return []


def _collect_leaf_titles(issue_tree: dict[str, Any] | None) -> dict[str, str]:
    """Collect leaf branch IDs -> titles from the MECE issue tree."""
    if not issue_tree:
        return {}

    roots: list[dict[str, Any]] = []
    if isinstance(issue_tree, dict):
        if "root" in issue_tree and isinstance(issue_tree["root"], dict):
            roots = [issue_tree["root"]]
        else:
            roots = [issue_tree]

    leaves: dict[str, str] = {}

    def _walk(node: dict[str, Any]) -> None:
        node_id = node.get("id")
        node_name = node.get("name") or node.get("label") or node_id
        children = node.get("children") or []
        if node_id and not children:
            leaves[node_id] = str(node_name)
            return
        for child in children:
            if isinstance(child, dict):
                _walk(child)

    for root in roots:
        _walk(root)
    return leaves


def _uid() -> str:
    return str(uuid.uuid4())
