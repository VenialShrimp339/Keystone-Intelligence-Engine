"""Unit tests for JSON Schema validation (Component #1).

Validates sample RESEARCH.md and research-tasks.json files against
their respective JSON Schemas.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMAS_DIR = PROJECT_ROOT / "schemas"
SAMPLES_DIR = PROJECT_ROOT / "samples"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _validate(instance: dict, schema_path: Path) -> None:
    schema = _load_json(schema_path)
    jsonschema.validate(instance, schema)


# ---------------------------------------------------------------------------
# Schema loading
# ---------------------------------------------------------------------------


class TestSchemaLoading:
    def test_research_md_schema_loads(self):
        schema = _load_json(SCHEMAS_DIR / "research_md.schema.json")
        assert schema["$schema"]
        assert "properties" in schema

    def test_research_tasks_schema_loads(self):
        schema = _load_json(SCHEMAS_DIR / "research_tasks.schema.json")
        assert schema["$schema"]
        assert "properties" in schema


# ---------------------------------------------------------------------------
# Sample RESEARCH.md files validate against schema
# ---------------------------------------------------------------------------


class TestSampleResearchMdValidation:
    @pytest.fixture(params=["luminar_lidar", "auto_body_chain", "specialty_chemicals_ma"])
    def sample_research_md(self, request) -> dict:
        path = SAMPLES_DIR / request.param / "RESEARCH.md.json"
        return _load_json(path)

    def test_sample_validates(self, sample_research_md):
        _validate(sample_research_md, SCHEMAS_DIR / "research_md.schema.json")


# ---------------------------------------------------------------------------
# Sample research-tasks.json files validate against schema
# ---------------------------------------------------------------------------


class TestSampleResearchTasksValidation:
    @pytest.fixture(params=["luminar_lidar", "auto_body_chain", "specialty_chemicals_ma"])
    def sample_tasks(self, request) -> dict:
        path = SAMPLES_DIR / request.param / "research-tasks.json"
        return _load_json(path)

    def test_sample_validates(self, sample_tasks):
        _validate(sample_tasks, SCHEMAS_DIR / "research_tasks.schema.json")


# ---------------------------------------------------------------------------
# Schema rejects invalid RESEARCH.md
# ---------------------------------------------------------------------------


class TestResearchMdSchemaRejection:
    def _minimal_valid_spec(self) -> dict:
        return {
            "engagement_id": "eng_001",
            "client_id": "client_001",
            "title": "Test",
            "created_at": "2026-04-05T00:00:00Z",
            "specification_version": 1,
            "engagement_type": "evaluative",
            "decision_context": "Some decision",
            "surprising_finding": "Something surprising",
            "questions": [
                {"question": "Primary question?", "is_primary": True}
            ],
            "output_format": "markdown",
            "non_goals": ["Political positioning"],
        }

    def test_rejects_missing_decision_context(self):
        spec = self._minimal_valid_spec()
        del spec["decision_context"]
        with pytest.raises(jsonschema.ValidationError):
            _validate(spec, SCHEMAS_DIR / "research_md.schema.json")

    def test_rejects_empty_decision_context(self):
        spec = self._minimal_valid_spec()
        spec["decision_context"] = ""
        with pytest.raises(jsonschema.ValidationError):
            _validate(spec, SCHEMAS_DIR / "research_md.schema.json")

    def test_rejects_no_questions(self):
        spec = self._minimal_valid_spec()
        spec["questions"] = []
        with pytest.raises(jsonschema.ValidationError):
            _validate(spec, SCHEMAS_DIR / "research_md.schema.json")

    def test_rejects_empty_non_goals(self):
        spec = self._minimal_valid_spec()
        spec["non_goals"] = []
        with pytest.raises(jsonschema.ValidationError):
            _validate(spec, SCHEMAS_DIR / "research_md.schema.json")

    def test_rejects_invalid_engagement_type(self):
        spec = self._minimal_valid_spec()
        spec["engagement_type"] = "invalid_type"
        with pytest.raises(jsonschema.ValidationError):
            _validate(spec, SCHEMAS_DIR / "research_md.schema.json")

    def test_rejects_missing_engagement_type(self):
        spec = self._minimal_valid_spec()
        del spec["engagement_type"]
        with pytest.raises(jsonschema.ValidationError):
            _validate(spec, SCHEMAS_DIR / "research_md.schema.json")


# ---------------------------------------------------------------------------
# Schema rejects invalid research-tasks.json
# ---------------------------------------------------------------------------


class TestResearchTasksSchemaRejection:
    def _minimal_valid_task(self) -> dict:
        return {
            "id": "task_001",
            "engagement_id": "eng_001",
            "client_id": "client_001",
            "category": "market_sizing",
            "type": "estimative",
            "target_decision_usefulness": 3,
            "description": "Estimate TAM",
            "acceptance_criteria": ["Criteria 1"],
            "deliverable_destination": "Section 2",
            "priority": 1,
            "anti_confirmatory_framing": "Evaluate the market size",
            "assigned_tools": ["tool_a", "tool_b", "tool_c"],
            "end_product": "Market size table",
            "dependencies": [],
        }

    def _minimal_valid_decomposition(self) -> dict:
        return {
            "project": "Test",
            "engagement_id": "eng_001",
            "client_id": "client_001",
            "research_md_path": "RESEARCH.md",
            "specification_version": 1,
            "decomposition_rationale": "Standard decomposition",
            "tasks": [self._minimal_valid_task()],
        }

    def test_rejects_missing_anti_confirmatory_framing(self):
        decomp = self._minimal_valid_decomposition()
        del decomp["tasks"][0]["anti_confirmatory_framing"]
        with pytest.raises(jsonschema.ValidationError):
            _validate(decomp, SCHEMAS_DIR / "research_tasks.schema.json")

    def test_rejects_too_few_tools(self):
        decomp = self._minimal_valid_decomposition()
        decomp["tasks"][0]["assigned_tools"] = ["a", "b"]
        with pytest.raises(jsonschema.ValidationError):
            _validate(decomp, SCHEMAS_DIR / "research_tasks.schema.json")

    def test_rejects_too_many_tools(self):
        decomp = self._minimal_valid_decomposition()
        decomp["tasks"][0]["assigned_tools"] = ["a", "b", "c", "d", "e", "f"]
        with pytest.raises(jsonschema.ValidationError):
            _validate(decomp, SCHEMAS_DIR / "research_tasks.schema.json")

    def test_passes_defaults_to_false(self):
        decomp = self._minimal_valid_decomposition()
        # passes not specified should be valid (schema default)
        _validate(decomp, SCHEMAS_DIR / "research_tasks.schema.json")

    def test_rejects_missing_end_product(self):
        decomp = self._minimal_valid_decomposition()
        del decomp["tasks"][0]["end_product"]
        with pytest.raises(jsonschema.ValidationError):
            _validate(decomp, SCHEMAS_DIR / "research_tasks.schema.json")

    def test_rejects_missing_dependencies(self):
        decomp = self._minimal_valid_decomposition()
        del decomp["tasks"][0]["dependencies"]
        with pytest.raises(jsonschema.ValidationError):
            _validate(decomp, SCHEMAS_DIR / "research_tasks.schema.json")
