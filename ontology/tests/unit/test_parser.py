"""Parser tests — WorkLog → WorkDirective → Event pipeline (T0-4)."""

from __future__ import annotations

from datetime import datetime

import pytest

from ontology.models.core import WorkLog
from ontology.models.enums import Intent
from ontology.parser import (
    IntentMatch,
    WorkLogParser,
    action_to_event,
    directive_to_action,
    worklog_to_directive,
    ParsingError,
)


@pytest.mark.unit
class TestIntentExtraction:
    """Test intent extraction from unstructured text."""

    @pytest.fixture
    def parser(self) -> WorkLogParser:
        return WorkLogParser()

    def test_create_task_intent(self, parser: WorkLogParser) -> None:
        text = "Created new task for API implementation. Task ID: 01ARZ3NDEKTSV4RRFFQ69G5FA2"
        match = parser.extract_intent(text)
        assert match.intent == Intent.CREATE_TASK
        assert match.confidence > 0.7

    def test_update_status_intent(self, parser: WorkLogParser) -> None:
        text = "Updated status of task to in_progress after code review"
        match = parser.extract_intent(text)
        assert match.intent == Intent.UPDATE_STATUS
        assert match.confidence > 0.7

    def test_log_work_intent(self, parser: WorkLogParser) -> None:
        text = "Logged 4.5 hours of work on authentication module"
        match = parser.extract_intent(text)
        assert match.intent == Intent.LOG_WORK
        assert match.confidence > 0.7

    def test_raise_blocker_intent(self, parser: WorkLogParser) -> None:
        text = "Task 01ARZ3NDEKTSV4RRFFQ69G5FA2 is blocked by missing API docs"
        match = parser.extract_intent(text)
        assert match.intent == Intent.RAISE_BLOCKER
        assert match.confidence > 0.7

    def test_no_intent_raises(self, parser: WorkLogParser) -> None:
        text = "Just some random notes about the weather"
        with pytest.raises(ParsingError, match="No intent detected"):
            parser.extract_intent(text)


@pytest.mark.unit
class TestEntityExtraction:
    """Test entity recognition from text."""

    @pytest.fixture
    def parser(self) -> WorkLogParser:
        return WorkLogParser()

    def test_extract_ulid_entities(self, parser: WorkLogParser) -> None:
        text = "Task 01ARZ3NDEKTSV4RRFFQ69G5FA2 assigned to person 01ARZ3NDEKTSV4RRFFQ69G5FA1"
        entities = parser.extract_entities(text)
        assert len(entities) == 2
        assert all(e.entity_id in text for e in entities)

    def test_no_entities_returns_empty(self, parser: WorkLogParser) -> None:
        text = "General progress update with no specific entity references"
        entities = parser.extract_entities(text)
        assert entities == []

    def test_entity_type_inference(self, parser: WorkLogParser) -> None:
        text = "Task 01ARZ3NDEKTSV4RRFFQ69G5FA2 completed"
        entities = parser.extract_entities(text)
        assert len(entities) == 1
        assert entities[0].entity_type == "task"


@pytest.mark.unit
class TestDueDateInference:
    """Test due date extraction and inference."""

    @pytest.fixture
    def parser(self) -> WorkLogParser:
        return WorkLogParser()

    def test_iso_date_pattern(self, parser: WorkLogParser) -> None:
        text = "Due by 2026-05-15 for deliverable"
        due_date = parser.infer_due_date(text)
        assert due_date == "2026-05-15"

    def test_relative_days_pattern(self, parser: WorkLogParser) -> None:
        text = "Need to complete this in 3 days"
        base = datetime(2026, 4, 22)
        due_date = parser.infer_due_date(text, base_date=base)
        assert due_date == "2026-04-25"

    def test_default_due_date_is_7_days(self, parser: WorkLogParser) -> None:
        text = "Just some work without due date"
        base = datetime(2026, 4, 22)
        due_date = parser.infer_due_date(text, base_date=base)
        assert due_date == "2026-04-29"


@pytest.mark.unit
class TestWorkLogParsing:
    """Test full WorkLog → WorkDirective parsing."""

    @pytest.fixture
    def parser(self) -> WorkLogParser:
        return WorkLogParser()

    @pytest.fixture
    def sample_worklog(self) -> WorkLog:
        return WorkLog.model_validate(
            {
                "log_id": "01ARZ3NDEKTSV4RRFFQ69G5FA3",
                "task_id": "01ARZ3NDEKTSV4RRFFQ69G5FA2",
                "author_person_id": "01ARZ3NDEKTSV4RRFFQ69G5FA1",
                "date": "2026-04-22",
                "content": "Created task 01ARZ3NDEKTSV4RRFFQ69G5FA2 for backend implementation. Logged 3 hours. Due 2026-05-15.",
                "tags": ["DONE"],
                "created_at": "2026-04-22T09:00:00Z",
            }
        )

    def test_parse_creates_parsed_directive(
        self, parser: WorkLogParser, sample_worklog: WorkLog
    ) -> None:
        parsed = parser.parse(sample_worklog)
        assert parsed.intent == Intent.CREATE_TASK
        assert parsed.due_date == "2026-05-15"
        assert len(parsed.entities) >= 1

    def test_parse_empty_content_raises(self, parser: WorkLogParser) -> None:
        with pytest.raises(Exception):  # Pydantic validation will fail on empty content
            WorkLog.model_validate(
                {
                    "log_id": "01ARZ3NDEKTSV4RRFFQ69G5FA4",
                    "task_id": "01ARZ3NDEKTSV4RRFFQ69G5FA2",
                    "author_person_id": "01ARZ3NDEKTSV4RRFFQ69G5FA1",
                    "date": "2026-04-22",
                    "content": "",  # Empty content violates min_length=1
                    "tags": ["development"],
                    "created_at": "2026-04-22T09:00:00Z",
                }
            )


@pytest.mark.unit
class TestPipelineIntegration:
    """Test full WorkLog → Directive → Action → Event pipeline."""

    @pytest.fixture
    def sample_worklog(self) -> WorkLog:
        return WorkLog.model_validate(
            {
                "log_id": "01ARZ3NDEKTSV4RRFFQ69G5FA3",
                "task_id": "01ARZ3NDEKTSV4RRFFQ69G5FA2",
                "author_person_id": "01ARZ3NDEKTSV4RRFFQ69G5FA1",
                "date": "2026-04-22",
                "content": "Created task 01ARZ3NDEKTSV4RRFFQ69G5FA2 for backend API. Logged 4 hours work.",
                "tags": ["DONE"],
                "created_at": "2026-04-22T09:00:00Z",
            }
        )

    def test_worklog_to_directive(self, sample_worklog: WorkLog) -> None:
        directive = worklog_to_directive(sample_worklog)
        assert directive.intent == Intent.CREATE_TASK
        assert directive.due_date  # Has inferred due date
        assert directive.source_worklog_id == sample_worklog.log_id

    def test_directive_to_action(self, sample_worklog: WorkLog) -> None:
        directive = worklog_to_directive(sample_worklog)
        action = directive_to_action(directive)
        assert action.intent == Intent.CREATE_TASK
        assert action.status == "pending"

    def test_action_to_event(self, sample_worklog: WorkLog) -> None:
        directive = worklog_to_directive(sample_worklog)
        action = directive_to_action(directive)
        event = action_to_event(
            action,
            project_id="01ARZ3NDEKTSV4RRFFQ69G5FA0",
            actor_id="01ARZ3NDEKTSV4RRFFQ69G5FA1",
        )
        assert event.type == "ontology.action.v1"  # CloudEvents type pattern
        assert event.data["project_id"] == "01ARZ3NDEKTSV4RRFFQ69G5FA0"
        assert event.specversion == "1.0"
        assert event.data["action_intent"] == "create_task"
