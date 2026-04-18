"""Structural checks on the JSON Schemas themselves.

These tests catch drift early \u2014 e.g. a new Pydantic field without a schema
counterpart, or mismatched enum members between ``enums.json`` and
``models/enums.py``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from ontology.models.enums import (
    ContractModality,
    DailyReportTag,
    FundingSource,
    GateLevel,
    GateStatus,
    Intent,
    KPITier,
    ProjectStatus,
    ProjectTypeCode,
    ScaleTier,
    SecurityTier,
    TaskStatus,
)

SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "schemas"


@pytest.mark.unit
def test_every_schema_is_valid_draft_2020_12() -> None:
    """Each schema file must itself be a valid Draft 2020-12 metaschema."""
    for path in SCHEMAS_DIR.glob("*.json"):
        doc = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(doc)


@pytest.mark.unit
def test_every_schema_declares_ontology_metadata(enums_schema: dict[str, Any]) -> None:
    """Each schema must advertise ``x-ontology-version``."""
    for path in SCHEMAS_DIR.glob("*.json"):
        doc = json.loads(path.read_text(encoding="utf-8"))
        assert "x-ontology-version" in doc, f"{path.name} missing x-ontology-version"


@pytest.mark.unit
@pytest.mark.parametrize(
    ("enum_cls", "def_name"),
    [
        (ProjectTypeCode, "ProjectTypeCode"),
        (ContractModality, "ContractModality"),
        (FundingSource, "FundingSource"),
        (SecurityTier, "SecurityTier"),
        (ScaleTier, "ScaleTier"),
        (GateLevel, "GateLevel"),
        (GateStatus, "GateStatus"),
        (KPITier, "KPITier"),
        (DailyReportTag, "DailyReportTag"),
        (TaskStatus, "TaskStatus"),
        (ProjectStatus, "ProjectStatus"),
        (Intent, "Intent"),
    ],
)
def test_python_enum_matches_json_schema_enum(
    enums_schema: dict[str, Any], enum_cls: type, def_name: str
) -> None:
    """Python enum members must exactly equal the JSON Schema ``enum`` list."""
    schema_values: list[str] = enums_schema["$defs"][def_name]["enum"]
    python_values: list[str] = [member.value for member in enum_cls]  # type: ignore[attr-defined]
    assert sorted(schema_values) == sorted(python_values), (
        f"{def_name}: JSON={schema_values} vs Python={python_values}"
    )
