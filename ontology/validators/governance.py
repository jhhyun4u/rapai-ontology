"""Governance validator \u2014 SemVer + Append-only enforcement.

Source of policy: ``mindvault/ontology/06-ontology-design-charter.md``.

What this module does
---------------------
Given two snapshots of the same schema (``old`` and ``new``), it detects:
    1. Removal of a field from ``properties``      \u2192 breaking  (MAJOR)
    2. Removal of an element from an ``enum`` list \u2192 breaking  (MAJOR)
    3. Narrowing of a constraint                   \u2192 breaking  (MAJOR)
       (e.g. ``maxLength`` decreased, ``minLength`` increased, ``pattern`` tightened)
    4. A field added to ``required``                \u2192 breaking  (MAJOR)
    5. ``additionalProperties: true \u2192 false``       \u2192 breaking  (MAJOR)
    6. Addition of new optional fields               \u2192 non-breaking (MINOR)
    7. Addition of a new enum value                  \u2192 non-breaking (MINOR)
    8. Documentation / title / description changes   \u2192 patch       (PATCH)

Use it to gate Pull Requests: a breaking change MUST accompany a major
``x-ontology-version`` bump.

The Append-only law mirrors Neo4j ``GATE_DECISION`` semantics: deletions of
prior-approved fields are considered unsafe unless the version number leaps
and a migration script is shipped alongside.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any


class GovernanceViolation(Exception):
    """Raised when a schema diff violates the governance policy."""


class BreakingChangeError(GovernanceViolation):
    """Raised when a change is breaking but the version did not bump MAJOR."""


@dataclass(frozen=True)
class Diff:
    """Structured comparison result between two schema snapshots."""

    breaking: list[str] = field(default_factory=list)
    minor: list[str] = field(default_factory=list)
    patch: list[str] = field(default_factory=list)

    @property
    def severity(self) -> str:
        if self.breaking:
            return "major"
        if self.minor:
            return "minor"
        if self.patch:
            return "patch"
        return "none"


# ── Public API ───────────────────────────────────────────────────────────
def compare_schemas(old: dict[str, Any], new: dict[str, Any], *, path: str = "") -> Diff:
    """Recursively diff two JSON Schema documents.

    Returns a :class:`Diff` whose ``severity`` drives the required SemVer bump.
    Only a subset of JSON Schema is inspected \u2014 enough to catch the common
    breaking patterns the charter cares about.
    """
    breaking: list[str] = []
    minor: list[str] = []
    patch: list[str] = []

    # 1. additionalProperties tightening.
    old_ap = old.get("additionalProperties", True)
    new_ap = new.get("additionalProperties", True)
    if old_ap is True and new_ap is False:
        breaking.append(f"{path or '<root>'}: additionalProperties tightened true \u2192 false")

    # 2. required set expansion.
    old_required = set(old.get("required") or [])
    new_required = set(new.get("required") or [])
    for added in sorted(new_required - old_required):
        breaking.append(f"{path or '<root>'}: required field added '{added}'")

    # 3. properties diff.
    old_props = old.get("properties") or {}
    new_props = new.get("properties") or {}

    for removed in sorted(set(old_props) - set(new_props)):
        breaking.append(f"{path}/properties/{removed}: removed")
    for added in sorted(set(new_props) - set(old_props)):
        minor.append(f"{path}/properties/{added}: added")
    for common in sorted(set(old_props) & set(new_props)):
        sub_diff = _compare_property(old_props[common], new_props[common], f"{path}/properties/{common}")
        breaking.extend(sub_diff.breaking)
        minor.extend(sub_diff.minor)
        patch.extend(sub_diff.patch)

    # 4. $defs diff (recurse).
    old_defs = old.get("$defs") or {}
    new_defs = new.get("$defs") or {}
    for removed in sorted(set(old_defs) - set(new_defs)):
        breaking.append(f"{path}/$defs/{removed}: removed")
    for added in sorted(set(new_defs) - set(old_defs)):
        minor.append(f"{path}/$defs/{added}: added")
    for common in sorted(set(old_defs) & set(new_defs)):
        sub_diff = compare_schemas(old_defs[common], new_defs[common], path=f"{path}/$defs/{common}")
        breaking.extend(sub_diff.breaking)
        minor.extend(sub_diff.minor)
        patch.extend(sub_diff.patch)

    # 5. Documentation-level changes roll up as patch.
    for doc_key in ("title", "description"):
        if old.get(doc_key) != new.get(doc_key):
            patch.append(f"{path or '<root>'}/{doc_key}: changed")

    return Diff(breaking=breaking, minor=minor, patch=patch)


def compare_enum_definitions(
    old_values: Iterable[str], new_values: Iterable[str], *, name: str = "enum"
) -> Diff:
    """Specialised enum diff \u2014 addition minor, removal major."""
    old_set, new_set = set(old_values), set(new_values)
    breaking = [f"{name}: value removed '{v}'" for v in sorted(old_set - new_set)]
    minor = [f"{name}: value added '{v}'" for v in sorted(new_set - old_set)]
    return Diff(breaking=breaking, minor=minor)


def validate_semver_bump(old_version: str, new_version: str, diff: Diff) -> None:
    """Raise :class:`BreakingChangeError` when the bump is insufficient."""

    def _parse(s: str) -> tuple[int, int, int]:
        try:
            major, minor, patch = (int(p) for p in s.strip().split("."))
        except Exception as exc:  # pragma: no cover
            raise GovernanceViolation(f"Malformed SemVer '{s}'") from exc
        return major, minor, patch

    old_mmp = _parse(old_version)
    new_mmp = _parse(new_version)

    if new_mmp <= old_mmp:
        raise GovernanceViolation(
            f"Ontology version must monotonically increase: {old_version} \u2192 {new_version}"
        )

    required = diff.severity
    if required == "major" and new_mmp[0] == old_mmp[0]:
        raise BreakingChangeError(
            "Breaking changes detected but MAJOR not bumped:\n  - "
            + "\n  - ".join(diff.breaking)
        )
    if required == "minor" and new_mmp[:2] == old_mmp[:2] and new_mmp[2] > old_mmp[2]:
        # Minor-only change was shipped as a patch bump \u2014 downgrade severity is wrong.
        raise GovernanceViolation(
            "Additive changes require at least a MINOR bump.\n  - "
            + "\n  - ".join(diff.minor)
        )


# ── Internal helpers ─────────────────────────────────────────────────────
_NARROW_NUM_KEYS: tuple[str, ...] = ("maxLength", "maximum", "exclusiveMaximum", "maxItems")
_WIDEN_NUM_KEYS: tuple[str, ...] = ("minLength", "minimum", "exclusiveMinimum", "minItems")


def _compare_property(old: dict[str, Any], new: dict[str, Any], path: str) -> Diff:
    """Diff a single property entry."""
    breaking: list[str] = []
    minor: list[str] = []
    patch: list[str] = []

    # Type change is always breaking.
    if old.get("type") != new.get("type"):
        breaking.append(f"{path}/type: {old.get('type')!r} \u2192 {new.get('type')!r}")

    # Enum narrowing = breaking, widening = minor.
    if "enum" in old or "enum" in new:
        sub = compare_enum_definitions(old.get("enum") or [], new.get("enum") or [], name=f"{path}/enum")
        breaking.extend(sub.breaking)
        minor.extend(sub.minor)

    # Numeric bounds narrowing = breaking.
    for key in _NARROW_NUM_KEYS:
        if key in old and key in new and new[key] < old[key]:
            breaking.append(f"{path}/{key}: narrowed {old[key]} \u2192 {new[key]}")
    for key in _WIDEN_NUM_KEYS:
        if key in old and key in new and new[key] > old[key]:
            breaking.append(f"{path}/{key}: narrowed {old[key]} \u2192 {new[key]}")

    # Pattern tightening is a breaking change by default (regex equivalence is hard).
    if old.get("pattern") != new.get("pattern") and old.get("pattern") is not None:
        breaking.append(f"{path}/pattern: changed")

    # $ref swaps are breaking unless identical.
    if old.get("$ref") != new.get("$ref"):
        breaking.append(f"{path}/$ref: {old.get('$ref')!r} \u2192 {new.get('$ref')!r}")

    # Nested object schemas.
    if old.get("type") == "object" and new.get("type") == "object":
        nested = compare_schemas(old, new, path=path)
        breaking.extend(nested.breaking)
        minor.extend(nested.minor)
        patch.extend(nested.patch)

    return Diff(breaking=breaking, minor=minor, patch=patch)
