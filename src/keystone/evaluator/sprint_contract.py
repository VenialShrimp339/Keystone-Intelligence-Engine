"""Sprint contract generation for per-section quality criteria.

Phase 1: Evaluator proposes criteria unilaterally. The data structure
supports Phase 2 bidirectional negotiation without rework (Section 5.13).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from keystone.evaluator.retry import LLMCallable, retry_llm_call
from keystone.models.evaluation import RubricDimension, SprintContract
from keystone.models.research import EngagementSpec
from keystone.models.tasks import ResearchTask

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).parent / "prompts"


class SprintContractGenerator:
    """Generates sprint contracts for research sections.

    Phase 1: unilateral proposal. Phase 2: adds Generator review +
    single negotiation round for infeasible criteria.
    """

    def __init__(self, llm: LLMCallable) -> None:
        self._llm = llm

    async def generate(
        self, task: ResearchTask, spec: EngagementSpec
    ) -> SprintContract:
        template = (_PROMPTS_DIR / "sprint_contract_generation.md").read_text()
        prompt = (
            template
            .replace("{{task_id}}", task.id)
            .replace("{{task_category}}", task.effective_category)
            .replace("{{task_description}}", task.description)
            .replace("{{end_product}}", task.end_product)
            .replace("{{task_acceptance_criteria}}", "; ".join(task.acceptance_criteria))
            .replace("{{anti_confirmatory_framing}}", task.anti_confirmatory_framing)
            .replace("{{engagement_type}}", spec.research_spec.engagement_type.value)
            .replace("{{decision_context}}", spec.research_spec.decision_context)
            .replace("{{quality_bar}}", spec.research_spec.quality_bar)
        )

        raw = await retry_llm_call(
            self._llm, prompt, description="sprint_contract_generation"
        )
        parsed = _parse_contract_json(raw)

        dimension_emphasis: dict[RubricDimension, float] = {}
        for dim_str, weight in parsed.get("dimension_emphasis", {}).items():
            try:
                dimension_emphasis[RubricDimension(dim_str)] = float(weight)
            except (ValueError, KeyError):
                logger.warning("Ignoring unknown dimension in emphasis: %s", dim_str)

        return SprintContract(
            section_id=f"section_{task.id}",
            engagement_id=task.engagement_id,
            client_id=task.client_id,
            task_id=task.id,
            section_title=task.deliverable_destination,
            acceptance_criteria=parsed.get("acceptance_criteria", task.acceptance_criteria),
            dimension_emphasis=dimension_emphasis,
            mandatory_elements=parsed.get("mandatory_elements", []),
            anti_patterns=parsed.get("anti_patterns", []),
        )


def _parse_contract_json(raw: str) -> dict:
    text = raw.strip()
    if "```" in text:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start : end + 1]
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        logger.warning("Failed to parse sprint contract JSON")
    return {}
