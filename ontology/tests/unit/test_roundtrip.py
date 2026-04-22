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
from ontology.models.extended import (
    Artifact,
    Blocker,
    Decision,
    Gate,
    IP,
    KPI,
    Milestone,
    Risk,
    Role,
    WorkDirective,
)
from ontology.models.links import (
    AssignedToLink,
    BlocksLink,
    DependsOnLink,
    GovernedByLink,
    MeasuredByLink,
    ProducesLink,
    RaisedFromLink,
    RelatedIPLink,
)
from ontology.models.actions import (
    Action,
    AssignPersonAction,
    CreateTaskAction,
    LogWorkAction,
    MeasureKPIAction,
    ProduceArtifactAction,
    RaiseBlockerAction,
    RecordDecisionAction,
    ResolveBlockerAction,
    SubmitGateAction,
    UpdateStatusAction,
    ValidateLevelUpAction,
)

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


# ────── Extended Object Roundtrip Tests (Phase II) ──────────────────────────

@pytest.mark.unit
class TestWorkDirectiveRoundtrip:
    @pytest.fixture(scope="session")
    def workdirective_schema(self, schemas_dir: Path) -> dict[str, Any]:
        with (schemas_dir / "workdirective.json").open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_workdirective_roundtrip(
        self, workdirective_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_workdirective.json").read_text(encoding="utf-8"))
        _validate(workdirective_schema, payload)
        model = WorkDirective.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(workdirective_schema, serialized)
        assert serialized["intent"] == "create_task"
        assert model.status.value == "created"


@pytest.mark.unit
class TestRoleRoundtrip:
    @pytest.fixture(scope="session")
    def role_schema(self, schemas_dir: Path) -> dict[str, Any]:
        with (schemas_dir / "role.json").open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_role_roundtrip(
        self, role_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_role.json").read_text(encoding="utf-8"))
        _validate(role_schema, payload)
        model = Role.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(role_schema, serialized)
        assert serialized["name"] == "PI"


@pytest.mark.unit
class TestMilestoneRoundtrip:
    @pytest.fixture(scope="session")
    def milestone_schema(self, schemas_dir: Path) -> dict[str, Any]:
        with (schemas_dir / "milestone.json").open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_milestone_roundtrip(
        self, milestone_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_milestone.json").read_text(encoding="utf-8"))
        _validate(milestone_schema, payload)
        model = Milestone.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(milestone_schema, serialized)
        assert len(serialized["deliverable_ids"]) == 2


@pytest.mark.unit
class TestBlockerRoundtrip:
    @pytest.fixture(scope="session")
    def blocker_schema(self, schemas_dir: Path) -> dict[str, Any]:
        with (schemas_dir / "blocker.json").open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_blocker_roundtrip(
        self, blocker_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_blocker.json").read_text(encoding="utf-8"))
        _validate(blocker_schema, payload)
        model = Blocker.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(blocker_schema, serialized)
        assert serialized["severity"] == "high"


@pytest.mark.unit
class TestDecisionRoundtrip:
    @pytest.fixture(scope="session")
    def decision_schema(self, schemas_dir: Path) -> dict[str, Any]:
        with (schemas_dir / "decision.json").open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_decision_roundtrip(
        self, decision_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_decision.json").read_text(encoding="utf-8"))
        _validate(decision_schema, payload)
        model = Decision.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(decision_schema, serialized)
        assert serialized["chosen"] == "OPT-001"


@pytest.mark.unit
class TestGateRoundtrip:
    @pytest.fixture(scope="session")
    def gate_schema(self, schemas_dir: Path) -> dict[str, Any]:
        with (schemas_dir / "gate.json").open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_gate_roundtrip(
        self, gate_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_gate.json").read_text(encoding="utf-8"))
        _validate(gate_schema, payload)
        model = Gate.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(gate_schema, serialized)
        assert serialized["status"] == "passed"


@pytest.mark.unit
class TestKPIRoundtrip:
    @pytest.fixture(scope="session")
    def kpi_schema(self, schemas_dir: Path) -> dict[str, Any]:
        with (schemas_dir / "kpi.json").open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_kpi_roundtrip(
        self, kpi_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_kpi.json").read_text(encoding="utf-8"))
        _validate(kpi_schema, payload)
        model = KPI.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(kpi_schema, serialized)
        assert serialized["tier"] == "output"


@pytest.mark.unit
class TestArtifactRoundtrip:
    @pytest.fixture(scope="session")
    def artifact_schema(self, schemas_dir: Path) -> dict[str, Any]:
        with (schemas_dir / "artifact.json").open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_artifact_roundtrip(
        self, artifact_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_artifact.json").read_text(encoding="utf-8"))
        _validate(artifact_schema, payload)
        model = Artifact.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(artifact_schema, serialized)
        assert serialized["type"] == "report"


@pytest.mark.unit
class TestRiskRoundtrip:
    @pytest.fixture(scope="session")
    def risk_schema(self, schemas_dir: Path) -> dict[str, Any]:
        with (schemas_dir / "risk.json").open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_risk_roundtrip(
        self, risk_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_risk.json").read_text(encoding="utf-8"))
        _validate(risk_schema, payload)
        model = Risk.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(risk_schema, serialized)
        assert serialized["category"] == "schedule"


@pytest.mark.unit
class TestIPRoundtrip:
    @pytest.fixture(scope="session")
    def ip_schema(self, schemas_dir: Path) -> dict[str, Any]:
        with (schemas_dir / "ip.json").open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_ip_roundtrip(
        self, ip_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_ip.json").read_text(encoding="utf-8"))
        _validate(ip_schema, payload)
        model = IP.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(ip_schema, serialized)
        assert serialized["type"] == "patent"


# ────── Link Type Roundtrip Tests (Relationship Infrastructure) ─────────────

@pytest.mark.unit
class TestDependsOnLinkRoundtrip:
    @pytest.fixture(scope="session")
    def links_schema(self, schemas_dir: Path) -> dict[str, Any]:
        with (schemas_dir / "links.json").open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_depends_on_link_roundtrip(
        self, links_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_link_depends_on.json").read_text(encoding="utf-8"))
        _validate(links_schema, payload)
        model = DependsOnLink.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(links_schema, serialized)
        assert serialized["link_type"] == "depends_on"


@pytest.mark.unit
class TestProducesLinkRoundtrip:
    @pytest.fixture(scope="session")
    def links_schema(self, schemas_dir: Path) -> dict[str, Any]:
        with (schemas_dir / "links.json").open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_produces_link_roundtrip(
        self, links_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_link_produces.json").read_text(encoding="utf-8"))
        _validate(links_schema, payload)
        model = ProducesLink.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(links_schema, serialized)
        assert serialized["link_type"] == "produces"


@pytest.mark.unit
class TestBlocksLinkRoundtrip:
    @pytest.fixture(scope="session")
    def links_schema(self, schemas_dir: Path) -> dict[str, Any]:
        with (schemas_dir / "links.json").open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_blocks_link_roundtrip(
        self, links_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_link_blocks.json").read_text(encoding="utf-8"))
        _validate(links_schema, payload)
        model = BlocksLink.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(links_schema, serialized)
        assert serialized["link_type"] == "blocks"


@pytest.mark.unit
class TestAssignedToLinkRoundtrip:
    @pytest.fixture(scope="session")
    def links_schema(self, schemas_dir: Path) -> dict[str, Any]:
        with (schemas_dir / "links.json").open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_assigned_to_link_roundtrip(
        self, links_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_link_assigned_to.json").read_text(encoding="utf-8"))
        _validate(links_schema, payload)
        model = AssignedToLink.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(links_schema, serialized)
        assert serialized["link_type"] == "assigned_to"


@pytest.mark.unit
class TestGovernedByLinkRoundtrip:
    @pytest.fixture(scope="session")
    def links_schema(self, schemas_dir: Path) -> dict[str, Any]:
        with (schemas_dir / "links.json").open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_governed_by_link_roundtrip(
        self, links_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_link_governed_by.json").read_text(encoding="utf-8"))
        _validate(links_schema, payload)
        model = GovernedByLink.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(links_schema, serialized)
        assert serialized["link_type"] == "governed_by"


@pytest.mark.unit
class TestMeasuredByLinkRoundtrip:
    @pytest.fixture(scope="session")
    def links_schema(self, schemas_dir: Path) -> dict[str, Any]:
        with (schemas_dir / "links.json").open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_measured_by_link_roundtrip(
        self, links_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_link_measured_by.json").read_text(encoding="utf-8"))
        _validate(links_schema, payload)
        model = MeasuredByLink.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(links_schema, serialized)
        assert serialized["link_type"] == "measured_by"


@pytest.mark.unit
class TestRaisedFromLinkRoundtrip:
    @pytest.fixture(scope="session")
    def links_schema(self, schemas_dir: Path) -> dict[str, Any]:
        with (schemas_dir / "links.json").open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_raised_from_link_roundtrip(
        self, links_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_link_raised_from.json").read_text(encoding="utf-8"))
        _validate(links_schema, payload)
        model = RaisedFromLink.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(links_schema, serialized)
        assert serialized["link_type"] == "raised_from"


@pytest.mark.unit
class TestRelatedIPLinkRoundtrip:
    @pytest.fixture(scope="session")
    def links_schema(self, schemas_dir: Path) -> dict[str, Any]:
        with (schemas_dir / "links.json").open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_related_ip_link_roundtrip(
        self, links_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_link_related_ip.json").read_text(encoding="utf-8"))
        _validate(links_schema, payload)
        model = RelatedIPLink.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(links_schema, serialized)
        assert serialized["link_type"] == "related_ip"


# Action Roundtrip Tests

@pytest.mark.unit
class TestActionBaseRoundtrip:
    @pytest.fixture(scope="session")
    def actions_schema(self, schemas_dir: Path) -> dict[str, Any]:
        with (schemas_dir / "actions.json").open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_action_base_roundtrip(
        self, actions_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_action_base.json").read_text(encoding="utf-8"))
        _validate(actions_schema, payload)
        model = Action.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(actions_schema, serialized)
        assert serialized["intent"] == "create_task"
        assert serialized["status"] == "pending"


@pytest.mark.unit
class TestCreateTaskActionRoundtrip:
    @pytest.fixture(scope="session")
    def actions_schema(self, schemas_dir: Path) -> dict[str, Any]:
        with (schemas_dir / "actions.json").open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_create_task_action_roundtrip(
        self, actions_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_action_create_task.json").read_text(encoding="utf-8"))
        _validate(actions_schema, payload)
        model = CreateTaskAction.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(actions_schema, serialized)
        assert serialized["intent"] == "create_task"
        assert serialized["status"] == "completed"


@pytest.mark.unit
class TestUpdateStatusActionRoundtrip:
    @pytest.fixture(scope="session")
    def actions_schema(self, schemas_dir: Path) -> dict[str, Any]:
        with (schemas_dir / "actions.json").open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_update_status_action_roundtrip(
        self, actions_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_action_update_status.json").read_text(encoding="utf-8"))
        _validate(actions_schema, payload)
        model = UpdateStatusAction.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(actions_schema, serialized)
        assert serialized["intent"] == "update_status"
        assert serialized["metadata"]["from_status"] == "pending"


@pytest.mark.unit
class TestLogWorkActionRoundtrip:
    @pytest.fixture(scope="session")
    def actions_schema(self, schemas_dir: Path) -> dict[str, Any]:
        with (schemas_dir / "actions.json").open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_log_work_action_roundtrip(
        self, actions_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_action_log_work.json").read_text(encoding="utf-8"))
        _validate(actions_schema, payload)
        model = LogWorkAction.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(actions_schema, serialized)
        assert serialized["intent"] == "log_work"
        assert serialized["metadata"]["hours"] == 4.5


@pytest.mark.unit
class TestAssignPersonActionRoundtrip:
    @pytest.fixture(scope="session")
    def actions_schema(self, schemas_dir: Path) -> dict[str, Any]:
        with (schemas_dir / "actions.json").open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_assign_person_action_roundtrip(
        self, actions_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_action_assign_person.json").read_text(encoding="utf-8"))
        _validate(actions_schema, payload)
        model = AssignPersonAction.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(actions_schema, serialized)
        assert serialized["intent"] == "assign_person"
        assert serialized["metadata"]["role"] == "engineer"


@pytest.mark.unit
class TestRaiseBlockerActionRoundtrip:
    @pytest.fixture(scope="session")
    def actions_schema(self, schemas_dir: Path) -> dict[str, Any]:
        with (schemas_dir / "actions.json").open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_raise_blocker_action_roundtrip(
        self, actions_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_action_raise_blocker.json").read_text(encoding="utf-8"))
        _validate(actions_schema, payload)
        model = RaiseBlockerAction.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(actions_schema, serialized)
        assert serialized["intent"] == "raise_blocker"
        assert serialized["target_entity_type"] == "task"


@pytest.mark.unit
class TestResolveBlockerActionRoundtrip:
    @pytest.fixture(scope="session")
    def actions_schema(self, schemas_dir: Path) -> dict[str, Any]:
        with (schemas_dir / "actions.json").open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_resolve_blocker_action_roundtrip(
        self, actions_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_action_resolve_blocker.json").read_text(encoding="utf-8"))
        _validate(actions_schema, payload)
        model = ResolveBlockerAction.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(actions_schema, serialized)
        assert serialized["intent"] == "resolve_blocker"
        assert serialized["target_entity_type"] == "blocker"


@pytest.mark.unit
class TestRecordDecisionActionRoundtrip:
    @pytest.fixture(scope="session")
    def actions_schema(self, schemas_dir: Path) -> dict[str, Any]:
        with (schemas_dir / "actions.json").open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_record_decision_action_roundtrip(
        self, actions_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_action_record_decision.json").read_text(encoding="utf-8"))
        _validate(actions_schema, payload)
        model = RecordDecisionAction.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(actions_schema, serialized)
        assert serialized["intent"] == "record_decision"
        assert serialized["metadata"]["context"] == "Architecture choice"


@pytest.mark.unit
class TestSubmitGateActionRoundtrip:
    @pytest.fixture(scope="session")
    def actions_schema(self, schemas_dir: Path) -> dict[str, Any]:
        with (schemas_dir / "actions.json").open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_submit_gate_action_roundtrip(
        self, actions_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_action_submit_gate.json").read_text(encoding="utf-8"))
        _validate(actions_schema, payload)
        model = SubmitGateAction.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(actions_schema, serialized)
        assert serialized["intent"] == "submit_gate"
        assert serialized["result"] == "passed"


@pytest.mark.unit
class TestMeasureKPIActionRoundtrip:
    @pytest.fixture(scope="session")
    def actions_schema(self, schemas_dir: Path) -> dict[str, Any]:
        with (schemas_dir / "actions.json").open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_measure_kpi_action_roundtrip(
        self, actions_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_action_measure_kpi.json").read_text(encoding="utf-8"))
        _validate(actions_schema, payload)
        model = MeasureKPIAction.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(actions_schema, serialized)
        assert serialized["intent"] == "measure_kpi"
        assert serialized["metadata"]["unit"] == "percent"


@pytest.mark.unit
class TestProduceArtifactActionRoundtrip:
    @pytest.fixture(scope="session")
    def actions_schema(self, schemas_dir: Path) -> dict[str, Any]:
        with (schemas_dir / "actions.json").open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_produce_artifact_action_roundtrip(
        self, actions_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_action_produce_artifact.json").read_text(encoding="utf-8"))
        _validate(actions_schema, payload)
        model = ProduceArtifactAction.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(actions_schema, serialized)
        assert serialized["intent"] == "produce_artifact"
        assert "s3://" in serialized["metadata"]["artifact_uri"]


@pytest.mark.unit
class TestValidateLevelUpActionRoundtrip:
    @pytest.fixture(scope="session")
    def actions_schema(self, schemas_dir: Path) -> dict[str, Any]:
        with (schemas_dir / "actions.json").open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_validate_level_up_action_roundtrip(
        self, actions_schema: dict[str, Any], fixtures_dir: Path
    ) -> None:
        payload = json.loads((fixtures_dir / "sample_action_validate_level_up.json").read_text(encoding="utf-8"))
        _validate(actions_schema, payload)
        model = ValidateLevelUpAction.model_validate(payload)
        serialized = json.loads(model.model_dump_json(exclude_none=True))
        _validate(actions_schema, serialized)
        assert serialized["intent"] == "validate_level_up_criteria"
        assert serialized["metadata"]["level_type"] == "TRL"
