"""WorkLog → WorkDirective → Event Parser (T0-4 TIER 0).

Transforms unstructured WorkLog entries into structured WorkDirective + Event records.
Provides intent extraction, entity recognition, and audit trail logging.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from typing import Any

from ontology.models.actions import Action, get_action_model
from ontology.models.core import Event, WorkLog
from ontology.models.enums import Intent
from ontology.models.extended import WorkDirective
from pydantic import BaseModel, Field, field_validator


class ParsingError(Exception):
    """Raised when WorkLog parsing fails."""

    pass


class IntentMatch(BaseModel):
    """Result of intent extraction from text."""

    intent: Intent
    confidence: float = Field(..., ge=0.0, le=1.0)
    matched_keywords: list[str]


class EntityReference(BaseModel):
    """Extracted entity from text."""

    entity_type: str  # task, person, blocker, decision, gate, artifact
    entity_id: str
    role: str | None = None
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


class ParsedWorkDirective(BaseModel):
    """Intermediate parsed result before WorkDirective instantiation."""

    intent: Intent
    due_date: str  # ISO 8601 date
    entities: list[EntityReference]
    source_text: str
    source_worklog_id: str | None = None
    source_rule_ids: list[str] = Field(default_factory=list)


class WorkLogParser:
    """Parse WorkLog entries into WorkDirective + Event records.

    Keywords-based intent extraction with heuristic entity recognition.
    Targets natural language work logs from daily standups, notes, emails.
    """

    # Intent keyword mappings (priority-ordered)
    INTENT_KEYWORDS: dict[Intent, dict[str, Any]] = {
        Intent.CREATE_TASK: {
            "keywords": ["create task", "new task", "open task", "add task"],
            "patterns": [r"task:?\s+([^,\n]+)", r"create.*task.*?\b(\w+)"],
            "priority": 90,
        },
        Intent.UPDATE_STATUS: {
            "keywords": ["mark", "status", "set to", "moved to", "updated"],
            "patterns": [r"(?:mark|set)\s+(?:as\s+)?(\w+)", r"status.*?(\w+)"],
            "priority": 85,
        },
        Intent.LOG_WORK: {
            "keywords": ["logged", "spent", "worked", "hours"],
            "patterns": [r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|h)"],
            "priority": 80,
        },
        Intent.ASSIGN_PERSON: {
            "keywords": ["assign", "assigned to", "owner", "responsible"],
            "patterns": [r"assigned?\s+(?:to\s+)?(@?\w+)", r"owner:?\s+(@?\w+)"],
            "priority": 75,
        },
        Intent.RAISE_BLOCKER: {
            "keywords": ["blocked", "blocker", "impediment", "waiting"],
            "patterns": [r"blocked?\s+(?:by\s+)?([^,\n]+)"],
            "priority": 80,
        },
        Intent.RESOLVE_BLOCKER: {
            "keywords": ["resolved", "unblocked", "cleared", "fixed"],
            "patterns": [r"resolved\s+(\w+)", r"unblocked"],
            "priority": 70,
        },
        Intent.RECORD_DECISION: {
            "keywords": ["decided", "decision", "chose", "selected"],
            "patterns": [r"decided.*?(\w+)", r"decision:?\s+([^,\n]+)"],
            "priority": 75,
        },
        Intent.SUBMIT_GATE: {
            "keywords": ["gate", "review", "approved", "passed"],
            "patterns": [r"(?:passed|approved)\s+(\w+)(?:\s+gate)?"],
            "priority": 70,
        },
        Intent.MEASURE_KPI: {
            "keywords": ["kpi", "metric", "measurement", "score"],
            "patterns": [r"(?:kpi|metric).*?(\d+(?:\.\d+)?)", r"score.*?(\d+)"],
            "priority": 65,
        },
        Intent.PRODUCE_ARTIFACT: {
            "keywords": ["artifact", "deliverable", "doc", "report", "upload"],
            "patterns": [r"(?:artifact|doc|report):?\s+(\S+)"],
            "priority": 70,
        },
    }

    # Entity type keywords
    ENTITY_KEYWORDS: dict[str, list[str]] = {
        "task": ["task", "ticket", "item", "story"],
        "person": ["@", "person", "owner", "assignee"],
        "blocker": ["blocker", "blocker", "impediment"],
        "decision": ["decision", "choice"],
        "gate": ["gate", "review", "milestone"],
        "artifact": ["artifact", "doc", "report", "deliverable"],
    }

    def __init__(self):
        """Initialize parser with intent priority ranking."""
        self.intent_priority = {
            intent: data["priority"]
            for intent, data in self.INTENT_KEYWORDS.items()
        }

    def extract_intent(self, text: str) -> IntentMatch:
        """Extract primary intent from WorkLog text using keywords + patterns.

        Returns intent with confidence score based on keyword density + pattern matches.
        """
        text_lower = text.lower()
        matches: dict[Intent, tuple[float, list[str]]] = {}

        for intent, intent_data in self.INTENT_KEYWORDS.items():
            keyword_hits = sum(
                1
                for kw in intent_data["keywords"]
                if kw in text_lower
            )
            pattern_hits = sum(
                1 for pattern in intent_data["patterns"]
                if re.search(pattern, text_lower, re.IGNORECASE)
            )
            total_hits = keyword_hits + pattern_hits

            if total_hits > 0:
                priority_boost = self.intent_priority[intent] / 100.0
                confidence = min(
                    (total_hits * 0.3 + priority_boost) / 1.3, 1.0
                )
                matched_kw = [
                    kw for kw in intent_data["keywords"]
                    if kw in text_lower
                ]
                matches[intent] = (confidence, matched_kw)

        if not matches:
            raise ParsingError(f"No intent detected in: {text[:100]}")

        best_intent = max(matches.items(), key=lambda x: x[1][0])
        return IntentMatch(
            intent=best_intent[0],
            confidence=best_intent[1][0],
            matched_keywords=best_intent[1][1],
        )

    def extract_entities(self, text: str) -> list[EntityReference]:
        """Extract referenced entities (tasks, persons, blockers, etc.)."""
        entities: list[EntityReference] = []

        # ULID pattern
        ulid_pattern = r"[0-9A-HJKMNP-TV-Z]{26}"

        # Extract all ULID-like IDs
        for match in re.finditer(ulid_pattern, text):
            entity_id = match.group()
            # Infer entity type from context (preceding words)
            preceding_text = text[max(0, match.start() - 30):match.start()].lower()

            entity_type = "task"  # default
            for ent_type, keywords in self.ENTITY_KEYWORDS.items():
                if any(kw in preceding_text for kw in keywords):
                    entity_type = ent_type
                    break

            entities.append(
                EntityReference(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    confidence=0.9,
                )
            )

        return entities

    def infer_due_date(self, text: str, base_date: datetime | None = None) -> str:
        """Infer due date from text or use default (7 days out)."""
        if base_date is None:
            base_date = datetime.now(UTC)

        # Patterns: "by Friday", "due next Monday", "due 2026-05-15", etc.
        patterns = [
            (r"by\s+(\d{4}-\d{2}-\d{2})", "iso"),
            (r"due\s+(\d{4}-\d{2}-\d{2})", "iso"),
            (r"(?:in\s+)?(\d+)\s+days?", "relative_days"),
        ]

        for pattern, pattern_type in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if pattern_type == "iso":
                    return match.group(1)
                elif pattern_type == "relative_days":
                    days_offset = int(match.group(1))
                    due = base_date + timedelta(days=days_offset)
                    return due.date().isoformat()

        # Default: 7 days from now
        due = base_date + timedelta(days=7)
        return due.date().isoformat()

    def parse(
        self,
        worklog: WorkLog,
        parent_id: str | None = None,
    ) -> ParsedWorkDirective:
        """Parse WorkLog into structured WorkDirective.

        Args:
            worklog: WorkLog instance with text content
            parent_id: Optional parent directive for nested work

        Returns:
            ParsedWorkDirective with extracted intent, entities, due_date
        """
        if not worklog.content or len(worklog.content) == 0:
            raise ParsingError("WorkLog content is empty")

        # Extract intent
        intent_match = self.extract_intent(worklog.content)

        # Extract entities
        entities = self.extract_entities(worklog.content)

        # Infer due date
        due_date = self.infer_due_date(
            worklog.content,
            base_date=worklog.created_at
            if worklog.created_at
            else datetime.utcnow(),
        )

        return ParsedWorkDirective(
            intent=intent_match.intent,
            due_date=due_date,
            entities=entities,
            source_text=worklog.content[:500],  # Truncate for storage
            source_worklog_id=worklog.log_id,
            source_rule_ids=getattr(worklog, "rule_ids", []),
        )


def worklog_to_directive(
    worklog: WorkLog, parser: WorkLogParser | None = None
) -> WorkDirective:
    """Convert WorkLog to WorkDirective using parser."""
    import uuid

    if parser is None:
        parser = WorkLogParser()

    parsed = parser.parse(worklog)

    # Build entity list for WorkDirective
    directive_entities = [
        {
            "entity_type": e.entity_type,
            "entity_id": e.entity_id,
            "role": e.role,
        }
        for e in parsed.entities
    ]

    # Generate directive_id (ULID-like, using UUID for simplicity)
    directive_id = str(uuid.uuid4().hex[:26]).upper()

    directive = WorkDirective.model_validate(
        {
            "directive_id": directive_id,
            "intent": parsed.intent.value,
            "entities": directive_entities,
            "due_date": parsed.due_date,
            "status": "created",
            "source_worklog_id": parsed.source_worklog_id,
            "source_rule_ids": parsed.source_rule_ids,
            "source_document": f"Parsed from WorkLog on {datetime.now(UTC).isoformat()}",
        }
    )

    return directive


def directive_to_action(directive: WorkDirective) -> Action:
    """Convert WorkDirective to Action for intent execution."""
    action_model = get_action_model(directive.intent.value)

    action = action_model.model_validate(
        {
            "intent": directive.intent.value,
            "target_entity_id": directive.entities[0]["entity_id"]
            if directive.entities
            else None,
            "target_entity_type": directive.entities[0]["entity_type"]
            if directive.entities
            else "task",
            "status": "pending",
            "triggered_by_rule_id": directive.source_rule_ids[0]
            if directive.source_rule_ids
            else None,
        }
    )

    return action


def action_to_event(
    action: Action,
    project_id: str,
    actor_id: str | None = None,
) -> Event:
    """Log Action as CloudEvents 1.0 Event for audit trail."""
    # Extract intent value (handle both enum and string)
    intent_value = (
        action.intent.value
        if isinstance(action.intent, Intent)
        else action.intent
    )

    event = Event.model_validate(
        {
            "specversion": "1.0",
            "type": f"ontology.action.v1",  # CloudEvents type pattern: ^[a-z][a-z0-9._-]*\.v[0-9]+$
            "source": "urn:rapai:parser:worklog",
            "id": action.action_id or "auto-generated",
            "time": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "datacontenttype": "application/json",
            "subject": f"action/{intent_value}/{action.target_entity_id}",
            "actor_agent_id": actor_id or action.actor_id or "AG-PARSER",
            "data": {
                "action_intent": intent_value,
                "action_status": action.status,
                "action_result": action.result,
                "project_id": project_id,
            },
        }
    )

    return event
