"""Sprint contract generation for per-section quality criteria.

Phase 1: Evaluator proposes criteria unilaterally. The data structure
supports Phase 2 bidirectional negotiation without rework (Section 5.13).
"""

from __future__ import annotations

import logging
from pathlib import Path

from keystone.evaluator.retry import LLMCallable, retry_llm_call
from keystone.llm.parsing import ParseError, safe_llm_json
from keystone.models.evaluation import RubricDimension, SprintContract
from keystone.models.research import EngagementSpec
from keystone.models.tasks import ResearchTask

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def _strip_frontmatter(text: str) -> str:
    """Strip YAML frontmatter (---...---) from a prompt template if present."""
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[end + 5 :]
    return text


class SprintContractGenerator:
    """Generates sprint contracts for research sections.

    Phase 1: unilateral proposal. Phase 2: adds Generator review +
    single negotiation round for infeasible criteria.
    """

    def __init__(self, llm: LLMCallable) -> None:
        self._llm = llm

    async def generate(self, task: ResearchTask, spec: EngagementSpec) -> SprintContract:
        template = (_PROMPTS_DIR / "sprint_contract_generation.md").read_text()
        prompt = (
            template.replace("{{task_id}}", task.id)
            .replace("{{task_category}}", task.effective_category)
            .replace("{{task_description}}", task.description)
            .replace("{{end_product}}", task.end_product)
            .replace("{{task_acceptance_criteria}}", "; ".join(task.acceptance_criteria))
            .replace("{{anti_confirmatory_framing}}", task.anti_confirmatory_framing)
            .replace("{{engagement_type}}", spec.research_spec.engagement_type.value)
            .replace("{{decision_context}}", spec.research_spec.decision_context)
            .replace("{{quality_bar}}", spec.research_spec.quality_bar)
        )

        raw = await retry_llm_call(self._llm, prompt, description="sprint_contract_generation")
        try:
            parsed = safe_llm_json(raw)
        except ParseError as exc:
            msg = (
                f"Failed to parse sprint contract JSON for task {task.id}; "
                "cannot continue with a bare contract."
            )
            logger.warning(msg)
            raise RuntimeError(msg) from exc

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
