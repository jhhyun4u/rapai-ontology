"""Roundtrip tests — the SSOT enforcement mechanism.

For each Core Object:
    1. Load the fixture JSON.
    2. Validate it against the canonical JSON Schema (jsonschema).
    3. Parse it into the Pydantic model.
    4. Serialize back to JSON.
    5. Assert the output re-validates against the schema and is semantically equal.

This guarantees the Pydantic model is faithful to the JSON Schema SSOT
(ADR-001 R5). A drift causes CI to fail.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, RefResolver

from ontology.models.core import Event, Person, Project, Task, WorkLog

SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "schemas"


def _resolver(schema: dict[str, Any]) -> RefResolver:
    """Build a RefResolver that finds sibling schemas by $id."""
    store: dict[str, dict[str, Any]] = {}
    for path in SCHEMAS_DIR.glob("*.json"):
        with path.open(encoding="utf-8") as fh:
            doc = json.load(fh)
        if "$id" in doc:
            store[doc["$id"]] = doc
        # Also register by local filename for relative ref resolution.
        store[path.name] = doc
    return RefResolver.from_schema(schema, store=store)


def _validate(schema: dict[str, Any], instance: Any) -> None:
    validator = Draft202012Validator(schema, resolver=_resolver(schema))
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path))
    if errors:
        joined = "\n".join(f"  - {e.message} at /{'/'.join(str(p) for p in e.absolute_path)}" for e in errors)
        raise AssertionError(f"Schema validation failed:\n{joined}")


@pytest.mark.unit
class TestProjectRoundtrip:
    def test_contract_research_project(
        self, project_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_project.json").read_text(encoding="utf-8"))
        _validate(project_schema, payload)
        model = Project.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(project_schema, serialized)
        # Structural equality: fixture is canonical.
        assert serialized["project_id"] == payload["project_id"]
        assert serialized["cross_cutting"]["contract_modality"] == "contract_research"
        assert model.cross_cutting.is_contract_research is True

    def test_developmental_project_requires_trl(
        self, project_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads(
            (fixtures_dir / "sample_project_developmental.json").read_text(encoding="utf-8")
        )
        _validate(project_schema, payload)
        model = Project.model_validate(payload)
        assert model.trl_target == 7

    def test_type_b_without_trl_fails(self, fixtures_dir: Path) -> None:
        payload = json.loads(
            (fixtures_dir / "sample_project_developmental.json").read_text(encoding="utf-8")
        )
        payload.pop("trl_target")
        with pytest.raises(ValueError, match="requires 'trl_target'"):
            Project.model_validate(payload)


@pytest.mark.unit
class TestTaskRoundtrip:
    def test_task_roundtrip(
        self, task_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_task.json").read_text(encoding="utf-8"))
        _validate(task_schema, payload)
        model = Task.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(task_schema, serialized)
        assert set(serialized.keys()) >= {"task_id", "project_id", "wbs_code", "title", "status"}

    def test_task_self_depends_rejected(self, fixtures_dir: Path) -> None:
        payload = json.loads((fixtures_dir / "sample_task.json").read_text(encoding="utf-8"))
        payload["depends_on_task_ids"] = [payload["task_id"]]
        with pytest.raises(ValueError, match="depend on itself"):
            Task.model_validate(payload)

    def test_invalid_wbs_code_rejected(self, fixtures_dir: Path) -> None:
        payload = json.loads((fixtures_dir / "sample_task.json").read_text(encoding="utf-8"))
        payload["wbs_code"] = "1-2-3"  # wrong separator
        with pytest.raises(ValueError):
            Task.model_validate(payload)


@pytest.mark.unit
class TestWorkLogRoundtrip:
    def test_worklog_roundtrip(
        self, worklog_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_worklog.json").read_text(encoding="utf-8"))
        _validate(worklog_schema, payload)
        model = WorkLog.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(worklog_schema, serialized)
        assert "DONE" in serialized["tags"]

    def test_empty_tags_rejected(self, fixtures_dir: Path) -> None:
        payload = json.loads((fixtures_dir / "sample_worklog.json").read_text(encoding="utf-8"))
        payload["tags"] = []
        with pytest.raises(ValueError):
            WorkLog.model_validate(payload)

    def test_duplicate_tags_rejected(self, fixtures_dir: Path) -> None:
        payload = json.loads((fixtures_dir / "sample_worklog.json").read_text(encoding="utf-8"))
        payload["tags"] = ["DONE", "DONE"]
        with pytest.raises(ValueError, match="unique"):
            WorkLog.model_validate(payload)


@pytest.mark.unit
class TestPersonRoundtrip:
    def test_person_roundtrip(
        self, person_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_person.json").read_text(encoding="utf-8"))
        _validate(person_schema, payload)
        model = Person.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(person_schema, serialized)
        assert model.security_clearance.rank == 2  # CONFIDENTIAL


@pytest.mark.unit
class TestEventRoundtrip:
    def test_cloudevent_with_model_id(
        self, event_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_event.json").read_text(encoding="utf-8"))
        _validate(event_schema, payload)
        model = Event.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(event_schema, serialized)
        assert serialized["specversion"] == "1.0"

    def test_llm_event_without_model_id_fails(self, fixtures_dir: Path) -> None:
        payload = json.loads((fixtures_dir / "sample_event.json").read_text(encoding="utf-8"))
        payload.pop("model_id")
        with pytest.raises(ValueError, match="model_id is required"):
            Event.model_validate(payload)

    def test_invalid_type_pattern_rejected(self, fixtures_dir: Path) -> None:
        payload = json.loads((fixtures_dir / "sample_event.json").read_text(encoding="utf-8"))
        payload["type"] = "NotReverseDNS"  # must end in .v<int>
        with pytest.raises(ValueError):
            Event.model_validate(payload)
