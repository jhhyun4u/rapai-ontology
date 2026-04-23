"""Pytest fixtures shared across ontology tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

SCHEMAS_DIR = Path(__file__).resolve().parents[1] / "schemas"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture(scope="session")
def schemas_dir() -> Path:
    """Directory containing canonical JSON Schemas (SSOT)."""
    return SCHEMAS_DIR


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Directory containing sample fixture data."""
    return FIXTURES_DIR


@pytest.fixture(scope="session")
def enums_schema(schemas_dir: Path) -> dict[str, Any]:
    return _load_json(schemas_dir / "enums.json")


@pytest.fixture(scope="session")
def project_schema(schemas_dir: Path) -> dict[str, Any]:
    return _load_json(schemas_dir / "project.json")


@pytest.fixture(scope="session")
def task_schema(schemas_dir: Path) -> dict[str, Any]:
    return _load_json(schemas_dir / "task.json")


@pytest.fixture(scope="session")
def worklog_schema(schemas_dir: Path) -> dict[str, Any]:
    return _load_json(schemas_dir / "worklog.json")


@pytest.fixture(scope="session")
def person_schema(schemas_dir: Path) -> dict[str, Any]:
    return _load_json(schemas_dir / "person.json")


@pytest.fixture(scope="session")
def event_schema(schemas_dir: Path) -> dict[str, Any]:
    return _load_json(schemas_dir / "event.json")


@pytest.fixture(scope="session")
def links_schema(schemas_dir: Path) -> dict[str, Any]:
    return _load_json(schemas_dir / "links.json")


@pytest.fixture(scope="session")
def actions_schema(schemas_dir: Path) -> dict[str, Any]:
    return _load_json(schemas_dir / "actions.json")
