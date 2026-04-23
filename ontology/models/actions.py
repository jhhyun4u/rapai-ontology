"""Action models for work intent execution.

Canonical action types define work intent execution (10 types).
Every WorkDirective carries one Action Intent.
Source: ontology/schemas/actions.json (Draft 2020-12, v0.1.0)
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ontology.models.enums import Intent


class Action(BaseModel):
    """Base Action model for work intent execution.

    Wraps Intent enum with metadata and validators for intent fulfillment tracking.
    """

    model_config = ConfigDict(extra="forbid")

    action_id: str | None = Field(
        None,
        pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$",
        description="ULID for this action (auto-generated if not provided)",
    )
    intent: Intent = Field(..., description="Work intent type")
    actor_id: str | None = Field(
        None,
        pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$",
        description="Person or Agent executing the action",
    )
    actor_type: str | None = Field(None, description="Type of actor: person, agent, or system")
    target_entity_id: str | None = Field(
        None,
        pattern=r"^[0-9A-HJKMNP-TV-Zabcdef\-]{26,36}$",
        description="Primary entity affected by this action",
    )
    target_entity_type: str | None = Field(
        None, description="Type of entity: task, blocker, decision, gate, etc."
    )
    metadata: dict | None = Field(None, description="Action-specific metadata")
    status: str | None = Field(None, description="Execution status: pending, in_progress, completed, failed")
    result: str | None = Field(None, description="Result or outcome of the action")
    triggered_by_rule_id: str | None = Field(None, description="Rule ID that triggered this action")
    created_at: str | None = None
    completed_at: str | None = None
    updated_at: str | None = None

    @model_validator(mode="after")
    def validate_actor_type_consistency(self) -> Action:
        """If actor_id is present, actor_type should be specified."""
        if self.actor_id and not self.actor_type:
            raise ValueError(
                "actor_type must be specified when actor_id is present "
                "(valid types: person, agent, system)"
            )
        return self

    @model_validator(mode="after")
    def validate_completion_consistency(self) -> Action:
        """If completed_at is set, status should be completed or failed."""
        if self.completed_at and self.status not in ("completed", "failed"):
            raise ValueError(
                f"completed_at is set, but status is '{self.status}' "
                f"(must be 'completed' or 'failed')"
            )
        return self

    @model_validator(mode="after")
    def validate_target_entity_consistency(self) -> Action:
        """If target_entity_id is present, target_entity_type should be specified."""
        if self.target_entity_id and not self.target_entity_type:
            raise ValueError(
                "target_entity_type must be specified when target_entity_id is present"
            )
        return self


# Specialized Action subclasses for intent-specific validation

class CreateTaskAction(Action):
    """Action for creating a new Task."""

    intent: Intent = Field(default=Intent.CREATE_TASK, pattern="^create_task$")


class UpdateStatusAction(Action):
    """Action for updating Task status."""

    intent: Intent = Field(default=Intent.UPDATE_STATUS, pattern="^update_status$")
    metadata: dict | None = Field(
        None, description="Should contain from_status and to_status"
    )


class LogWorkAction(Action):
    """Action for logging work (hours, progress notes)."""

    intent: Intent = Field(default=Intent.LOG_WORK, pattern="^log_work$")


class AssignPersonAction(Action):
    """Action for assigning Person to Task/Role."""

    intent: Intent = Field(default=Intent.ASSIGN_PERSON, pattern="^assign_person$")
    metadata: dict | None = Field(None, description="Should contain role assignment details")


class RaiseBlockerAction(Action):
    """Action for raising a Blocker on Task."""

    intent: Intent = Field(default=Intent.RAISE_BLOCKER, pattern="^raise_blocker$")


class ResolveBlockerAction(Action):
    """Action for resolving/closing a Blocker."""

    intent: Intent = Field(default=Intent.RESOLVE_BLOCKER, pattern="^resolve_blocker$")
    result: str | None = Field(None, description="Resolution details or outcome")


class RecordDecisionAction(Action):
    """Action for recording a Decision with options and rationale."""

    intent: Intent = Field(default=Intent.RECORD_DECISION, pattern="^record_decision$")


class SubmitGateAction(Action):
    """Action for submitting/signing off on a Gate review."""

    intent: Intent = Field(default=Intent.SUBMIT_GATE, pattern="^submit_gate$")
    result: str | None = Field(None, description="Gate outcome: passed, failed, waived")


class MeasureKPIAction(Action):
    """Action for recording KPI measurement."""

    intent: Intent = Field(default=Intent.MEASURE_KPI, pattern="^measure_kpi$")
    metadata: dict | None = Field(
        None, description="Should contain measured_value and unit"
    )


class ProduceArtifactAction(Action):
    """Action for producing/uploading an Artifact."""

    intent: Intent = Field(default=Intent.PRODUCE_ARTIFACT, pattern="^produce_artifact$")
    metadata: dict | None = Field(
        None, description="Should contain artifact URI and type"
    )


class ValidateLevelUpAction(Action):
    """Action for validating TRL/CRL level-up criteria (Phase III W2-W3)."""

    intent: Intent = Field(
        default=Intent.VALIDATE_LEVEL_UP_CRITERIA,
        pattern="^validate_level_up_criteria$",
    )
    metadata: dict | None = Field(
        None, description="Should contain level_type (TRL or CRL) and target_level"
    )


# Action registry for intent mapping
ACTION_MODELS = {
    "create_task": CreateTaskAction,
    "update_status": UpdateStatusAction,
    "log_work": LogWorkAction,
    "assign_person": AssignPersonAction,
    "raise_blocker": RaiseBlockerAction,
    "resolve_blocker": ResolveBlockerAction,
    "record_decision": RecordDecisionAction,
    "submit_gate": SubmitGateAction,
    "measure_kpi": MeasureKPIAction,
    "produce_artifact": ProduceArtifactAction,
    "validate_level_up_criteria": ValidateLevelUpAction,
}


def get_action_model(intent: str):
    """Get the appropriate Action model class for a given intent."""
    return ACTION_MODELS.get(intent, Action)
